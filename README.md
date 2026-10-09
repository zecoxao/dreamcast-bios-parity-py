# dreamcast-bios-parity-py

Fixes the HOLLY parity check of a Dreamcast/NAOMI SH-4 BIOS ROM.

This is a Python port of [mathieulh/Dreamcast_BIOS_Parity_Fixed](https://github.com/mathieulh/Dreamcast_BIOS_Parity_Fixed)
(originally a PowerShell script, `Fix-BiosParity.ps1`).

The tool reads a BIOS file, checks the parity of the total XOR, and, if the
parity is odd, flips the least-significant bit of the first byte of the trailing
zero-padding (any single-bit flip in the padding works). The modified file will
then pass the HOLLY parity check.

This restores the even-parity condition that the GPU expects, allowing the G1
bus to unlock and the BIOS to run.

## Usage

```
python fix_bios_parity.py -i dc_boot.bin -o dc_boot_fixed.bin
```

Requires Python 3.7+ and no third-party dependencies.

## What the script does

1. Reads the entire ROM into a byte array.
2. Computes the XOR of all bytes (`xorAll`).
3. Determines the parity of that XOR (even = 0, odd = 1) by repeatedly folding
   the byte onto itself.
4. If the parity is odd, it locates the first byte of the trailing zero-padding
   (the area that is never executed) and flips its least-significant bit.
   Flipping a single bit toggles the overall XOR parity, turning an odd parity
   into an even one.
5. Writes the (possibly) modified image to the output file.

Because the modification is confined to the padding region, the SH-4 will fetch
and execute exactly the same instructions as before, but the BIOS will now
satisfy the HOLLY parity check and the G1 bus will be unlocked.

## In-depth technical explanation

The validation algorithm used by the HOLLY GPU (on Dreamcast/NAOMI) is a parity
check over 4-byte blocks. It computes the XOR of each 4-byte block (treating the
block as four independent bytes) and then reduces that value to a single parity
bit (XOR of all its bits). The hardware expects the XOR of the parity bits of
all blocks to be 0 (i.e., an even number of blocks with odd parity).

Mathematically, this is equivalent to:

Let `B[0..N-1]` be the byte array of the BIOS (length `N`, a multiple of 4).
Define for each block `i` (starting at offset `4i`):

```
x_i = B[4i] ^ B[4i+1] ^ B[4i+2] ^ B[4i+3]
```

Then compute the parity of `x_i`:

```
p_i = parity(x_i) = (xor of all bits of x_i) in {0, 1}
```

The BIOS is valid iff:

```
p_0 ^ p_1 ^ ... ^ p_(N/4-1) = 0
```

which simplifies to the parity of the XOR of the entire BIOS:

```
parity( B[0] ^ B[1] ^ ... ^ B[N-1] ) = 0
```

In other words, the XOR of all bytes in the BIOS must contain an even number of
1 bits. For the supplied `dc_boot.bin` the XOR of all bytes is `0x3C` (binary
`00111100`), which has four 1 bits - even parity - so the check passes. Altering
any single byte flips the parity of exactly one block, toggling the overall
parity and causing the validation error observed.

This matches the description of a "parity in 4-byte blocks over an 8-bit bus":
the SH-4 reads the BIOS byte-by-byte (8-bit bus), forms 4-byte blocks
implicitly, and the GPU checks the global parity condition.

Target check value: the hardware expects the final parity bit to be 0 (even
parity). No rotation is needed; the relation is a simple parity-over-XOR
condition.

## Credits

Original PowerShell implementation and research by
[mathieulh](https://github.com/mathieulh). Python port in this repository.

## License

GPL-2.0, matching the original project. See [LICENSE](LICENSE).
