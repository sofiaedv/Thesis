#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 18 14:47:54 2025

@author: sofiaedvardsson
"""
import numpy as np
import pandas as pd
import pathlib

from runMona import run_mona_timing_report
from runDudect import run_dudect
from runWelch import run_Welch

sample_size = "30k"
input_directory = "./../data/timing_measurements/new_timing_measurements/KyberSlash1_2/"
output_directory = "./../data/verdicts/new_timing_measurements/KyberSlash1_2/"
payload_datasets = 250
no_tools = 3

library_versions = ["pq-crystals-kyber-0", "pq-crystals-kyber-2", "pq-crystals-kyber-12"]
input_directory += "c_programs/"
output_directory += "c_programs/"

verdicts = np.zeros((payload_datasets*len(library_versions), no_tools+1), int)

for i in range(payload_datasets):
    for j in range(len(library_versions)):
        library_version = library_versions[j]
        verdicts[3*i +j][0] = 0 if "0" in library_version else 1
        mona_verdict = run_mona_timing_report(input_directory + f"{sample_size}_{i}/index/{sample_size}_{i}_index_{library_version}_timing_measurements.csv")
        welch_verdict = run_Welch(input_directory + f"{sample_size}_{i}/no_index/{sample_size}_{i}_no_index_{library_version}_timing_measurements.csv")
        dudect_verdict = run_dudect(input_directory + f"{sample_size}_{i}/no_index/{sample_size}_{i}_no_index_{library_version}_timing_measurements.csv")
        if mona_verdict == None or welch_verdict == None or dudect_verdict == None:
            print("Problematic file:", input_directory + f"{sample_size}_{i}/index/{sample_size}_{i}_index_{library_version}_timing_measurements.csv")
            continue
        verdicts[3*i +j][1] = mona_verdict
        verdicts[3*i +j][2] = welch_verdict
        verdicts[3*i +j][3] = dudect_verdict

df = pd.DataFrame(verdicts)
df.rename(columns={0: "Ground truth", 1: "Mona", 2: "Welch", 3: "dudect"}, inplace=True)

pathlib.Path(output_directory).mkdir(parents=True, exist_ok=True)
df.to_csv(output_directory + f"{sample_size}_verdicts.csv", sep=";", index=True, header=True)
