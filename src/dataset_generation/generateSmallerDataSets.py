#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 18 18:07:57 2025

@author: sofiaedvardsson
"""

import pandas as pd
import pathlib

sample_size = 10000
no_sample_files = 250
input_directory = "./../../data/timing_measurements/new_timing_measurements/KyberSlash1_2/c_programs/"

library_versions = ["pq-crystals-kyber-0", "pq-crystals-kyber-2", "pq-crystals-kyber-12"]

for i in range(no_sample_files):
    for library in library_versions:
        df = pd.read_csv(input_directory + f"100k_{i}/index/100k_{i}_index_{library}_timing_measurements.csv",
                         sep=";",
                         header=None,
                         index_col=0)
        
        df_sample = df.groupby(1).sample(n=sample_size, random_state=sample_size+i)
        df_sample = df_sample.sample(frac=1, random_state=sample_size+i)
        sample_string = str(sample_size)[:-3]
        
        pathlib.Path(input_directory + f"{sample_string}k_{i}/index/").mkdir(parents=True, exist_ok=True)
        pathlib.Path(input_directory + f"{sample_string}k_{i}/no_index/").mkdir(parents=True, exist_ok=True)
        df_sample.to_csv(input_directory + f"{sample_string}k_{i}/index/{sample_string}k_{i}_index_{library}_timing_measurements.csv",
                         sep=";",
                         header=False,
                         index=True)
        df_sample.to_csv(input_directory + f"{sample_string}k_{i}/no_index/{sample_string}k_{i}_no_index_{library}_timing_measurements.csv",
                         sep=";",
                         header=False,
                         index=False)

