#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 10 13:25:44 2025

@author: sofiaedvardsson
"""

import subprocess
import numpy as np
import pandas as pd
import pathlib

language = "c"
sample_size = "10k"
input_directory = "./../data/timing_measurements/new_timing_measurements/KyberSlash1_2/"
output_directory = "./../data/verdicts/new_timing_measurements/dudect/KyberSlash1_2/"
payload_datasets = 250

def run_dudect(input_file):
    csv_lines = 2 * 1000 * int(input_file.split("no_index/")[1].split("k")[0])
    process = subprocess.run(["./../../dudect/src/dudect", 
                              "-f", input_file, 
                              "-n", str(csv_lines)],
                             capture_output=True,
                             text=True,
                             check=False)
    
    result = process.returncode
    
    if result == 11:
        return True
    elif result == 10:
        return False
    else:
        print(input_file)
        print(process.stdout + process.stderr)
        return None

if __name__ == "__main__":
    if language == "go":
        library_versions = ["circl-0", "circl-2",
                            "crystals-go-0", "crystals-go-2", "crystals-go-12",
                            "kyber-k2so-0", "kyber-k2so-2", "kyber-k2so-0"]
    else:
        library_versions = ["pq-crystals-kyber-0", "pq-crystals-kyber-2", "pq-crystals-kyber-12"]
    
    verdicts = np.zeros((payload_datasets, len(library_versions)), int)
    
    for i in range(payload_datasets):
        for j in range(len(library_versions)):
            library_version = library_versions[j]
            dudect_verdict = run_dudect(input_directory + f"/{language}_programs/{sample_size}_{i}/no_index/{sample_size}_{i}_no_index_{library_version}_timing_measurements.csv")
            verdicts[i][j] = dudect_verdict
            
    df = pd.DataFrame(verdicts)
    print(df.sum(axis=0))
    dudect_flat = df.to_numpy().flatten()
    dudect_single_column = pd.DataFrame(dudect_flat, columns=["dudect"])
    pathlib.Path(output_directory).mkdir(parents=True, exist_ok=True)
    dudect_single_column.to_csv(output_directory + f"{sample_size}_0-{payload_datasets-1}.csv", sep=";", header=True, index=True)
