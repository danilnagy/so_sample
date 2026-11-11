/** CRC-16/CCITT (polynomial 0x1021, no reflection), as Python's binascii.crc_hqx. */

export const CRC_INITIAL_STATE = 0x1d0f;

export function crcUpdate(state: number, byte: number): number {
  let crc = (state ^ (byte << 8)) & 0xffff;
  for (let i = 0; i < 8; i++) {
    crc = crc & 0x8000 ? ((crc << 1) ^ 0x1021) & 0xffff : (crc << 1) & 0xffff;
  }
  return crc;
}
