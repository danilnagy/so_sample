/** Minimal RIFF/WAVE reading (integer and float PCM) and PCM16 writing. */

export interface WavData {
  sampleRate: number;
  /** One normalized Float64Array per channel, samples in [-1, 1]. */
  channels: Float64Array[];
  bitsPerSample: number;
  format: 'pcm' | 'float';
}

export function parseWav(bytes: Uint8Array): WavData {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const tag = (offset: number): string => String.fromCharCode(...bytes.subarray(offset, offset + 4));
  if (bytes.length < 12 || tag(0) !== 'RIFF' || tag(8) !== 'WAVE') throw new Error('Not a RIFF/WAVE file');
  let offset = 12;
  let formatCode = 0;
  let channelCount = 0;
  let sampleRate = 0;
  let bitsPerSample = 0;
  let data: Uint8Array | null = null;
  while (offset + 8 <= bytes.length) {
    const id = tag(offset);
    const size = view.getUint32(offset + 4, true);
    const body = offset + 8;
    if (id === 'fmt ') {
      formatCode = view.getUint16(body, true);
      channelCount = view.getUint16(body + 2, true);
      sampleRate = view.getUint32(body + 4, true);
      bitsPerSample = view.getUint16(body + 14, true);
      if (formatCode === 0xfffe && size >= 26) formatCode = view.getUint16(body + 24, true);
    } else if (id === 'data') {
      data = bytes.subarray(body, Math.min(body + size, bytes.length));
    }
    offset = body + size + (size & 1);
  }
  if (!data || !channelCount || !sampleRate) throw new Error('WAV is missing fmt or data chunks');
  const format = formatCode === 3 ? 'float' : formatCode === 1 ? 'pcm' : null;
  if (!format) throw new Error(`Unsupported WAV format code ${formatCode}`);
  const bytesPerSample = bitsPerSample / 8;
  if (![1, 2, 3, 4, 8].includes(bytesPerSample) || (format === 'float' && bytesPerSample !== 4 && bytesPerSample !== 8)) {
    throw new Error(`Unsupported WAV sample size ${bitsPerSample} bits`);
  }
  const frames = Math.floor(data.length / (bytesPerSample * channelCount));
  const channels = Array.from({ length: channelCount }, () => new Float64Array(frames));
  const dv = new DataView(data.buffer, data.byteOffset, data.byteLength);
  let pos = 0;
  for (let i = 0; i < frames; i++) {
    for (let c = 0; c < channelCount; c++) {
      let value: number;
      if (format === 'float') {
        value = bytesPerSample === 4 ? dv.getFloat32(pos, true) : dv.getFloat64(pos, true);
      } else if (bytesPerSample === 1) {
        value = (dv.getUint8(pos) - 128) / 128;
      } else if (bytesPerSample === 2) {
        value = dv.getInt16(pos, true) / 32768;
      } else if (bytesPerSample === 3) {
        value = (((dv.getUint8(pos) | (dv.getUint8(pos + 1) << 8) | (dv.getUint8(pos + 2) << 16)) << 8) >> 8) / 8388608;
      } else {
        value = dv.getInt32(pos, true) / 2147483648;
      }
      channels[c][i] = value;
      pos += bytesPerSample;
    }
  }
  return { sampleRate, channels, bitsPerSample, format };
}

/**
 * Float sample to PCM16 as libsndfile wrote the accepted restores: the scaled value plus
 * 2^-17 is floored, then clipped (measured; see the pcm16 fixture).
 */
export function floatToPcm16(value: number): number {
  const scaled = Math.floor(value * 32768 + 2 ** -17);
  return scaled > 32767 ? 32767 : scaled < -32768 ? -32768 : scaled;
}

/** A 16-bit PCM WAV from interleaved samples. */
export function wavFromPcm16(interleaved: Int16Array, channelCount: number, sampleRate: number): Uint8Array {
  const dataBytes = interleaved.length * 2;
  const out = new Uint8Array(44 + dataBytes);
  const view = new DataView(out.buffer);
  const ascii = (offset: number, text: string): void => {
    for (let i = 0; i < text.length; i++) out[offset + i] = text.charCodeAt(i);
  };
  ascii(0, 'RIFF');
  view.setUint32(4, 36 + dataBytes, true);
  ascii(8, 'WAVE');
  ascii(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, channelCount, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * channelCount * 2, true);
  view.setUint16(32, channelCount * 2, true);
  view.setUint16(34, 16, true);
  ascii(36, 'data');
  view.setUint32(40, dataBytes, true);
  new Int16Array(out.buffer, 44, interleaved.length).set(interleaved);
  return out;
}

/** A mono float WAV, used for sample downloads and previews. */
export function wavFromFloat(samples: Float64Array, sampleRate: number): Uint8Array {
  const pcm = new Int16Array(samples.length);
  for (let i = 0; i < samples.length; i++) pcm[i] = floatToPcm16(Math.max(-1, Math.min(1, samples[i])));
  return wavFromPcm16(pcm, 1, sampleRate);
}
