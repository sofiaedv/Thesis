#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  8 09:40:20 2025

@author: sofiaedvardsson
"""

import numpy as np
import pandas as pd
from scipy import stats

language = "c"
payload_datasets = 250
t_values = []

def run_Welch(input_file):
    df = pd.read_csv(input_file, sep=";", header=None)
    test_result = stats.ttest_ind(df[df[0] == "X"][1], df[df[0] == "Y"][1], equal_var=False)
    t_statistic = test_result.statistic
    t_values.append(abs(t_statistic))
    
    return abs(t_statistic) > 4.5


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
            welch_verdict = run_Welch(f"./../data/timing_measurements/isolated/KyberSlash1_2/{language}_programs/100k_{i}/no_index/100k_{i}_no_index_{library_version}_timing_measurements.csv")
            verdicts[i][j] = welch_verdict
            
    df = pd.DataFrame(verdicts)
    df.rename(columns={0: library_versions[0], 1: library_versions[1], 2: library_versions[2]}, inplace=True)
    print(df.sum(axis=0))
    print(max(t_values))
