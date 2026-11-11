/**
 * The recording path without a browser: worklet blocks are assembled into the stereo
 * recording the decoder needs, and a one-channel input is refused with a clear message
 * instead of being duplicated into a checksum failure.
 */

import { describe, expect, it } from 'vitest';

import { base64ToBytes } from '../../core/bytes';
import { labelsForBody } from '../../core/labels';
import { decodeCapture, recoverFrame } from '../../core/modem/decode';
import { encodeRestoreWav } from '../../core/modem/encode';
import { type Packet, encodePackets, packetsEqual } from '../../core/packets';
import { parseWav } from '../../core/wav';
import { MonoInputError, assembleRecording, describeRecording, monoInputMessage, recordingWavBytes, requireDistinctChannels } from '../device';
import golden from '../../core/__fixtures__/golden-web-template-001.json';

const BLOCK = 128;
const packets: Packet[] = golden.frame.packets.map((p) => ({ tag: p.tag, payload: base64ToBytes(p.payload) }));

/** The restore as the worklet would deliver it: 128-frame blocks of Float32 per channel. */
function blocksOf(channels: Float64Array[]): Float32Array[][] {
  const blocks: Float32Array[][] = [];
  for (let offset = 0; offset < channels[0].length; offset += BLOCK) {
    blocks.push(channels.map((c) => Float32Array.from(c.subarray(offset, offset + BLOCK))));
  }
  return blocks;
}

describe('recording assembly', () => {
  const wav = parseWav(encodeRestoreWav(labelsForBody(encodePackets(packets))));
  const frames = wav.channels[0].length;

  it('assembles stereo blocks into a recording the decoder reads back to the verified packets', () => {
    const recording = assembleRecording(blocksOf(wav.channels), 2, frames, wav.sampleRate, 'Line In');
    expect(recording.channels.length).toBe(2);
    expect(recording.channels[0].length).toBe(frames);
    const { frame, attempts } = recoverFrame(recording, 0.02);
    expect(attempts[0]).toEqual({ method: 'crossing', passed: true });
    expect(packetsEqual(frame.packets, packets)).toBe(true);
  });

  it('refuses a one-channel input by name instead of duplicating it', () => {
    const mono = blocksOf([wav.channels[0]]);
    expect(() => assembleRecording(mono, 1, frames, wav.sampleRate, 'MacBook Pro Microphone')).toThrow(MonoInputError);
    expect(() => assembleRecording(mono, 1, frames, wav.sampleRate, 'MacBook Pro Microphone')).toThrow(
      'MacBook Pro Microphone is mono. A backup needs both channels: choose a stereo line input.',
    );
    expect(monoInputMessage('')).toContain('This input is mono');
  });

  it('would otherwise fail as a checksum error, which is what a duplicated mono channel produces', () => {
    const duplicated = { ...wav, channels: [wav.channels[0], wav.channels[0]] };
    expect(() => recoverFrame(duplicated, 0.02)).toThrow(/Packet checksum differs/);
  });

  it('refuses two channels that carry one signal, as a mono jack reported as stereo delivers', () => {
    // Seen on 2026-11-06: a USB headset adapter, "stereo, 2 channels", recorded the PO-33's
    // left channel twice. The decoder then fails with the same checksum tags for any transfer.
    const duplicated = blocksOf([wav.channels[0], wav.channels[0]]);
    expect(() => assembleRecording(duplicated, 2, frames, wav.sampleRate, 'Microphone In')).toThrow(
      /Microphone In delivered the same signal on both channels/,
    );
    const nearly = { ...wav, channels: [wav.channels[0], wav.channels[0].map((v) => v * 0.98)] };
    expect(() => requireDistinctChannels(nearly, 'Line In')).toThrow(MonoInputError);
    expect(() => requireDistinctChannels(wav, 'Line In')).not.toThrow();
    expect(() => requireDistinctChannels({ ...wav, channels: [wav.channels[1], wav.channels[0]] })).not.toThrow();
  });

  it('saves a recording as a WAV the decoder reads back unchanged', () => {
    const recording = assembleRecording(blocksOf(wav.channels), 2, frames, wav.sampleRate);
    const saved = parseWav(recordingWavBytes(recording));
    expect(saved.sampleRate).toBe(wav.sampleRate);
    expect(saved.channels[0].length).toBe(frames);
    expect(packetsEqual(recoverFrame(saved, 0.02).frame.packets, packets)).toBe(true);
    expect(describeRecording(recording)).toMatch(/^\d+\.\d s at 44100 Hz, peak left 50\.0%, right 50\.0%$/);
  });

  it('rejects a one-channel recording file before decoding', () => {
    const monoFile = { ...wav, channels: [wav.channels[0]] };
    expect(() => decodeCapture(monoFile, 0.02)).toThrow('Expected a stereo recording, found 1 channels');
  });
});
