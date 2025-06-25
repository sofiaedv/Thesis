#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  7 15:22:52 2025

@author: sofiaedvardsson
"""

import subprocess
import os
import numpy as np
import pandas as pd

language = "c"
payload_datasets = 10

def run_mona_timing_report(input_file):
    input_file = os.path.abspath(input_file)
    cwd = os.path.abspath("./../../mona-timing-report")

    process = subprocess.run(["java", "-jar", "ReportingTool.jar",
                              "--inputFile", input_file,
                              "--name", "Report"],
                             capture_output=True,
                             text=True,
                             cwd=cwd)

    output = process.stdout + process.stderr

    if "no significant different result found" in output:
        return False
    else:
        return True

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
            mona_verdict = run_mona_timing_report(f"./../data/timing_measurements/isolated/KyberSlash1_2/c_programs/new/100k_{i}/index/100k_{i}_index_{library_version}_timing_measurements.csv")
            verdicts[i][j] = mona_verdict

    df = pd.DataFrame(verdicts)
    print(df.sum(axis=0))
