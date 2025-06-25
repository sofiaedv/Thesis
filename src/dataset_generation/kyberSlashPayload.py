# -*- coding: utf-8 -*-
"""
Created on Mon Apr 14 13:15:39 2025

@author: sofia.edvardsson
"""

import sys
import random

# Kyber512 Parameters
KYBER_Q = 3329
KYBER512_K = 2
KYBER512_N = 256
KYBER512_POLY_COEFFICIENTS = 256
KYBER512_DU = 10 # Bits per coefficient for u vector compression
KYBER512_DV = 4  # Bits per coefficient for v polynomial compression

# Calculated sizes
KYBER512_U_BYTES = KYBER512_K * KYBER512_N * KYBER512_DU // 8 # 640
KYBER512_V_BYTES = KYBER512_N * KYBER512_DV // 8             # 128
KYBER512_CT_BYTES = KYBER512_U_BYTES + KYBER512_V_BYTES      # 768

slow_values = [2276, 2654, 1420, 1050, 1731]
C_slow = random.choice(slow_values)


def poly_compress_coeff(c, d, q):
    val = (float(c) * (1 << d)) / float(q)
    compressed = round(val)
    return int(compressed) % (1 << d)


def pack_poly_v(v_coeffs):
    if len(v_coeffs) != KYBER512_N:
        raise ValueError(f"Input must have {KYBER512_N} coefficients")

    packed_v = bytearray(KYBER512_V_BYTES)
    idx_byte = 0
    for i in range(0, KYBER512_N, 2): # Process coefficients in pairs
        coeff0 = v_coeffs[i]
        coeff1 = v_coeffs[i+1]

        c_comp0 = poly_compress_coeff(coeff0, KYBER512_DV, KYBER_Q)
        c_comp1 = poly_compress_coeff(coeff1, KYBER512_DV, KYBER_Q)

        packed_byte = c_comp0 | (c_comp1 << 4)
        packed_v[idx_byte] = packed_byte
        idx_byte += 1

    return packed_v


def generate_fixed_ciphertext(const_c):
    v_poly_coeffs = [const_c] * KYBER512_N

    packed_u = bytearray(KYBER512_U_BYTES)

    packed_v = pack_poly_v(v_poly_coeffs)

    ct = packed_u + packed_v

    if len(ct) != KYBER512_CT_BYTES:
         print(f"Error: Generated ciphertext has wrong length {len(ct)}", file=sys.stderr)
         return None

    return ct


ct_slow = generate_fixed_ciphertext(C_slow)
