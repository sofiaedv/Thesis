#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  5 09:15:08 2025

@author: sofiaedvardsson
"""

import random
import subprocess
import pathlib
import time
import gzip

##############################
## PARAMETERS

sample_size = 10000
collection_name = "tmp1"
output_directory = "./payloads/"
safe_mode = False
payload_generation_file = "./pqc_payloads/keysAndCiphertext"


##############################
## FUNCTIONS

def generatePayload(payload_generation_file):
    result = subprocess.run([payload_generation_file], capture_output=True)
    result_parts = result.stdout
    return result_parts[:1632], result_parts[1632:]


def generatePayloadFile(sample_size, collection_name, output_directory, payload_generation_file, safe_mode=True):
    output_directory = pathlib.Path(output_directory) / collection_name

    if safe_mode and output_directory.exists():
        if not input("Do you want to overwrite the existing directory: y/N\n").strip().lower() == "y":
            return

    dk, classX_c = generatePayload(payload_generation_file)

    payload_classes = ["X"]*sample_size + ["Y"]*sample_size
    random.shuffle(payload_classes)

    payloads = bytearray()

    for label in payload_classes:
        if label == "X":
            payloads.extend(classX_c)
        else:
            _, classY_c = generatePayload(payload_generation_file)
            payloads.extend(classY_c)

    with gzip.open(output_directory / f"{collection_name}_payloads", "wb") as file:
        file.write(dk)
        file.write(payloads)

    with open(output_directory / f"{collection_name}_classes", "w", encoding="utf-8") as f:
        f.write("".join(payload_classes))


if __name__ == "__main__":
    start_time = time.perf_counter()
    generatePayloadFile(sample_size, collection_name, output_directory, payload_generation_file, safe_mode)
    end_time = time.perf_counter()
    print("Time elapsed: ", round(end_time - start_time, 3), "seconds")
