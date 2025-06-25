#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  7 22:38:48 2025

@author: sofiaedvardsson
"""

import subprocess
import os
import numpy as np
import pandas as pd
import pathlib

language = "c"
sample_size = "100k"
start = 0
end = 250
input_directory = "./../data/timing_measurements/new_timing_measurements/"
output_directory = "./../data/verdicts/new_timing_measurements/RTLF_parts/"
payload_datasets = 250

sample_sizes = ["100k"]
locations = ["isolated/KyberSlash1_2", "isolated", "new_timing_measurements"]
part_ranges = [range(200, end, 25), range(25, end, 25), range(start, end, 25)]

def run_RTLF(input_file):
    input_file = os.path.abspath(input_file)
    
    process = subprocess.run(["/usr/local/bin/Rscript", "./../../RTLF/rtlf.R", 
                              "-i", input_file, 
                              #"-o", "result.json",
                              "-q"],
                             capture_output=True,
                             text=True)
    
    result = process.returncode
    
    if result == 11:
        return True
    elif result == 10:
        return False
    else:
        return None
    
if language == "go":
    library_versions = ["circl-0", "circl-2",
                        "crystals-go-0", "crystals-go-2", "crystals-go-12",
                        "kyber-k2so-0", "kyber-k2so-2", "kyber-k2so-0"]
else:
    library_versions = ["pq-crystals-kyber-0", "pq-crystals-kyber-2", "pq-crystals-kyber-12"]

for sample_size in sample_sizes:
    z = 0
    for location in locations:
        input_directory = f"./../data/timing_measurements/{location}/"
        output_directory = f"./../data/verdicts/{location}/RTLF_parts/"
        
        for k in part_ranges[z]:
        
            verdicts = np.zeros((payload_datasets, len(library_versions)), int)
            
            for i in range(k, k+25):
                for j in range(len(library_versions)):
                    library_version = library_versions[j]
                    RTLF_verdict = run_RTLF(input_directory + f"{language}_programs/{sample_size}_{i}/no_index/{sample_size}_{i}_no_index_{library_version}_timing_measurements.csv")
                    verdicts[i][j] = RTLF_verdict
                    
            df = pd.DataFrame(verdicts)
            print(df.head())
            print(df.sum(axis=0))
            rtlf_flat = df.to_numpy().flatten()
            rtlf_single_column = pd.DataFrame(rtlf_flat, columns=["RTLF"])
            pathlib.Path(output_directory).mkdir(parents=True, exist_ok=True)
            rtlf_single_column.to_csv(output_directory + f"{sample_size}_{k}-{k+25-1}.csv", sep=";", header=True, index=True)
        
        z += 1
        
