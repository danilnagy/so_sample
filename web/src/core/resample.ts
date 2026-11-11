/**
 * Polyphase resampling, following scipy.signal.resample_poly with its default
 * Kaiser (beta 5) low-pass design, so imports match the Python reference closely.
 * 48000 -> 23437.5 Hz is up 125 / down 256; 44100 -> 23437.5 Hz is up 625 / down 1176.
 */

/** Device rate 23437.5 Hz = 46875 / 2; the ratio to any integer source rate is rational. */
export function nativeRatio(inputRate: number): [number, number] {
  if (!Number.isInteger(inputRate) || inputRate < 8000 || inputRate > 384000) {
    throw new Error(`Unsupported input sample rate ${inputRate}`);
  }
  let a = 46875;
  let b = 2 * inputRate;
  while (b) [a, b] = [b, a % b];
  return [46875 / a, (2 * inputRate) / a];
}

export function besselI0(x: number): number {
  const q = (x * x) / 4;
  let sum = 1;
  let term = 1;
  for (let k = 1; k < 500; k++) {
    term *= q / (k * k);
    sum += term;
    if (term < sum * 1e-17) break;
  }
  return sum;
}

export function kaiserWindow(length: number, beta: number): Float64Array {
  const out = new Float64Array(length);
  if (length === 1) {
    out[0] = 1;
    return out;
  }
  const alpha = (length - 1) / 2;
  const denominator = besselI0(beta);
  for (let n = 0; n < length; n++) {
    const r = (n - alpha) / alpha;
    out[n] = besselI0(beta * Math.sqrt(Math.max(0, 1 - r * r))) / denominator;
  }
  return out;
}

function sinc(x: number): number {
  if (x === 0) return 1;
  const px = Math.PI * x;
  return Math.sin(px) / px;
}

/** Linear-phase low-pass FIR, cutoff relative to Nyquist, scaled to unit DC gain. */
export function firwinLowpass(numtaps: number, cutoff: number, beta = 5): Float64Array {
  const window = kaiserWindow(numtaps, beta);
  const alpha = 0.5 * (numtaps - 1);
  const h = new Float64Array(numtaps);
  let sum = 0;
  for (let n = 0; n < numtaps; n++) {
    h[n] = cutoff * sinc(cutoff * (n - alpha)) * window[n];
    sum += h[n];
  }
  for (let n = 0; n < numtaps; n++) h[n] /= sum;
  return h;
}

function outputLength(filterLength: number, inputLength: number, up: number, down: number): number {
  return Math.floor(((inputLength - 1) * up + filterLength - 1) / down) + 1;
}

/** y[k] = sum_m x[m] h[k*down - m*up] (zero-padded x), as scipy.signal.upfirdn. */
export function upfirdn(h: Float64Array, x: ArrayLike<number>, up: number, down: number): Float64Array {
  const n = outputLength(h.length, x.length, up, down);
  const y = new Float64Array(n);
  for (let k = 0; k < n; k++) {
    const t = k * down;
    const mMax = Math.min(x.length - 1, Math.floor(t / up));
    const mMin = Math.max(0, Math.ceil((t - h.length + 1) / up));
    let acc = 0;
    for (let m = mMin; m <= mMax; m++) acc += h[t - m * up] * x[m];
    y[k] = acc;
  }
  return y;
}

export function resamplePoly(x: ArrayLike<number>, up: number, down: number): Float64Array {
  if (up === down) return Float64Array.from(x);
  const maxRate = Math.max(up, down);
  const halfLen = 10 * maxRate;
  const h = firwinLowpass(2 * halfLen + 1, 1 / maxRate);
  for (let i = 0; i < h.length; i++) h[i] *= up;
  const nIn = x.length;
  const nOut = Math.floor((nIn * up) / down) + ((nIn * up) % down ? 1 : 0);
  const nPrePad = down - (halfLen % down);
  const nPreRemove = Math.floor((halfLen + nPrePad) / down);
  let nPostPad = 0;
  while (outputLength(h.length + nPrePad + nPostPad, nIn, up, down) < nOut + nPreRemove) nPostPad++;
  const padded = new Float64Array(nPrePad + h.length + nPostPad);
  padded.set(h, nPrePad);
  const y = upfirdn(padded, x, up, down);
  return y.slice(nPreRemove, nPreRemove + nOut);
}

/** Resample from a supported input rate to the device rate. */
export function toNativeRate(x: ArrayLike<number>, inputRate: number): Float64Array {
  const [up, down] = nativeRatio(inputRate);
  return resamplePoly(x, up, down);
}

/** Native frame count a source of `frames` frames at `inputRate` converts to. */
export function nativeFrameCount(frames: number, inputRate: number): number {
  const [up, down] = nativeRatio(inputRate);
  return Math.ceil((frames * up) / down);
}
