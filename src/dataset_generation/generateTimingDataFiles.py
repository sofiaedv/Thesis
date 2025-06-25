#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 27 13:20:44 2025

@author: sofiaedvardsson
"""

import generateTimingMeasurements as times

sample_size = "100k"
no_data_sets = 250
start_collection = 0
output_directory = "./../../data/timing_measurements/new_measurements/"
safe_mode = False

library_versions = ["pq-crystals-kyber-0", "pq-crystals-kyber-2", "pq-crystals-kyber-12"]

input_directories = ["./payloads/", "./payloads/KyberSlash1_2/"]

for input_directory in input_directories:
    out_directory = output_directory

    if "KyberSlash1_2" in input_directory:
        out_directory += "KyberSlash1_2/"
    
    out_directory += "c_programs/"

    for i in range(start_collection, start_collection + no_data_sets):
        collection_name = sample_size + "_" + str(i)
        for library in library_versions:
            times.collectTimingMeasurements(collection_name, 
                                            input_directory + sample_size + "/" + collection_name,
                                            out_directory,
                                            f"./pqc_implementations/{library}/{library}",
                                            safe_mode,
                                            library
                                            )
