#!/usr/bin/env python3
"""Fix the HOLLY parity check of a Dreamcast/NAOMI SH-4 BIOS ROM.

The HOLLY GPU on Dreamcast/NAOMI validates the BIOS by checking the overall
parity of the byte-wise XOR of the entire ROM: the BIOS is accepted only when
the XOR of all its bytes contains an even number of set bits.

This tool restores that even-parity condition when it is broken. It leaves the
executable code untouched by only modifying the trailing zero-padding area:
flipping a single bit there toggles the overall XOR parity while the SH-4 still
fetches and executes exactly the same instructions as before.

Python port of Fix-BiosParity.ps1
(https://github.com/mathieulh/Dreamcast_BIOS_Parity_Fixed).

Example:
    python fix_bios_parity.py -i dc_boot.bin -o dc_boot_fixed.bin
"""

from __future__ import annotations

import argparse
import sys


def get_parity(value: int) -> int:
    """Return the parity of a byte (0 = even number of 1-bits, 1 = odd)."""
    p = value & 0xFF
    p ^= p >> 4
    p ^= p >> 2
    p ^= p >> 1
    return p & 1


def fix_bios_parity(data: bytearray) -> tuple[bool, int, int | None]:
    """Fix the parity of ``data`` in place if needed.

    Returns a tuple ``(changed, xor_all, pad_start)`` where ``changed`` says
    whether a bit was flipped, ``xor_all`` is the XOR of every byte, and
    ``pad_start`` is the offset of the flipped padding byte (or ``None`` when
    no change was required).
    """
    # XOR of all bytes.
    xor_all = 0
    for b in data:
        xor_all ^= b

    # If parity is already even, nothing to do.
    if get_parity(xor_all) == 0:
        return False, xor_all, None

    # Parity is odd: flip one bit in the trailing zero-padding area.
    # Find the last non-zero byte so we can locate the start of the padding.
    last_non_zero = -1
    for i in range(len(data) - 1, -1, -1):
        if data[i] != 0:
            last_non_zero = i
            break

    if last_non_zero < 0:
        raise ValueError("The file appears to be all zero - nothing to fix.")

    pad_start = last_non_zero + 1  # first byte after the last non-zero byte
    if pad_start >= len(data):
        raise ValueError("No padding found - the file ends with non-zero data.")

    # Flip the least-significant bit of the first padding byte.
    data[pad_start] ^= 0x01
    return True, xor_all, pad_start


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fix the HOLLY parity check of a Dreamcast/NAOMI SH-4 BIOS ROM."
    )
    parser.add_argument(
        "-i",
        "--input-file",
        required=True,
        help="Path to the original BIOS image (e.g. dc_boot.bin).",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        required=True,
        help="Path where the fixed image will be written.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    with open(args.input_file, "rb") as fh:
        data = bytearray(fh.read())

    changed, xor_all, pad_start = fix_bios_parity(data)

    if changed:
        assert pad_start is not None
        original = data[pad_start] ^ 0x01
        print(
            f"Parity is odd (XOR = 0x{xor_all:02X}) - fixing by flipping a bit "
            f"in the padding."
        )
        print(
            f"Flipped bit 0 of byte at offset 0x{pad_start:08X} "
            f"(was {original:02X}, now {data[pad_start]:02X})"
        )
    else:
        print(f"Parity is already even (XOR = 0x{xor_all:02X}) - no change needed.")

    with open(args.output_file, "wb") as fh:
        fh.write(data)
    print(f"Written fixed image to '{args.output_file}'")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
