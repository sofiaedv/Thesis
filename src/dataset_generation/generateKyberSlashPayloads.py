#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  8 22:25:35 2025

@author: sofiaedvardsson
"""

import random
import subprocess
import pathlib
import time
import gzip

from kyberSlashPayload import generate_fixed_ciphertext

##############################
## PARAMETERS

sample_size = 10
collection_name = "tmp1"
output_directory = "./payloads/KyberSlash/"
safe_mode = False
payload_generation_file = "./pqc_payloads/keysAndCiphertext"


##############################
## FUNCTIONS

KYBER_Q = 3329

def generatePayload(payload_generation_file):
    result = subprocess.run([payload_generation_file], capture_output=True)
    result_parts = result.stdout

    return result_parts[:1632], result_parts[1632:]


def compress(coefficient):
    val = (float(coefficient) * (1 << 4)) / float(KYBER_Q)
    compressed = round(val)
    return int(compressed) % (1 << 4)


def generateSlowPayloadOld():
    slow_values = [103, 2858, 893, 1294, 3253]
    slow_value = random.choice(slow_values)

    c_compressed = compress(slow_value)
    packed_byte = (c_compressed << 4) | c_compressed

    c = bytes([0]) * 640 + bytes([packed_byte]) * 128

    return c


def generateSlowPayload():

    c = generate_fixed_ciphertext(3204)

    return bytes(c)


def generatePayloadFile(sample_size, collection_name, output_directory, payload_generation_file, safe_mode=True):
    output_directory = pathlib.Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    output_directory = output_directory / collection_name

    if safe_mode and output_directory.exists():
        if not input("Do you want to overwrite the existing directory: y/N\n").strip().lower() == "y":
            return

    output_directory.mkdir(parents=True, exist_ok=True)

    X_dk, _ = generatePayload(payload_generation_file)
    classX_c = generateSlowPayload()

    payload_classes = ["X"]*sample_size + ["Y"]*sample_size
    random.shuffle(payload_classes)

    payloads = bytearray()

    for label in payload_classes:
        if label == "X":
            payloads.extend(X_dk + classX_c)
        else:
            Y_dk, classY_c = generatePayload(payload_generation_file)
            payloads.extend(Y_dk + classY_c)

    with gzip.open(output_directory / f"{collection_name}_payloads", "wb") as file:
        file.write(payloads)

    with open(output_directory / f"{collection_name}_classes", "w", encoding="utf-8") as f:
        f.write("".join(payload_classes))


if __name__ == "__main__":
    start_time = time.perf_counter()
    generatePayloadFile(sample_size, collection_name, output_directory, payload_generation_file, safe_mode)
    end_time = time.perf_counter()
    print("Time elapsed: ", round(end_time - start_time, 3), "seconds")
