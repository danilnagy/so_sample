/**
 * The empty device state every export starts from: a backup taken after a factory reset
 * with all sounds and patterns deleted (experiments/empty-001-a). The compile step
 * overwrites what the project describes and leaves the rest as the device wrote it.
 */

import { base64ToBytes } from './bytes';
import type { Packet } from './packets';
import { type DeviceState, cloneState, parseFrame } from './state';
import template from './__fixtures__/template-empty.json';

export const TEMPLATE_CAPTURE_SHA256: string = template.capture_sha256;

const packets: Packet[] = template.packets.map((p) => ({ tag: p.tag, payload: base64ToBytes(p.payload) }));
const state = parseFrame({ packets, endByte: 0, encodedBody: new Uint8Array(0) });

export function emptyTemplateState(): DeviceState {
  return cloneState(state);
}
