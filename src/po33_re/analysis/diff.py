def compare_bytes(a: bytes, b: bytes) -> dict:
    overlap = min(len(a), len(b))
    changed = bits = 0
    ranges = []
    start = None
    for i in range(overlap):
        xor = a[i] ^ b[i]
        if xor:
            changed += 1
            bits += xor.bit_count()
            if start is None:
                start = i
        elif start is not None:
            ranges.append([start, i])
            start = None
    if start is not None:
        ranges.append([start, overlap])
    return {
        "length_a": len(a),
        "length_b": len(b),
        "overlap_bytes": overlap,
        "changed_overlap_bytes": changed,
        "changed_overlap_bits": bits,
        "changed_overlap_percent": 100.0 * changed / overlap if overlap else None,
        "tail_bytes": abs(len(a) - len(b)),
        "changed_ranges": ranges,
        "identical": a == b,
    }
