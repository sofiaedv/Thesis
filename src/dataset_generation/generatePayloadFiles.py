#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 27 13:12:36 2025

@author: sofiaedvardsson
"""

import time
import generatePayloads as payloads
import generateKyberSlashPayloads as ksPayloads

sample_sizes = [100000]
no_data_sets = 25
output_directory = "./payloads/KyberSlash1_2/"
safe_mode = True
payload_generation_file = "./pqc_payloads/keysAndCiphertext"
start_collection = 225

for sample_size in sample_sizes:
    prefix = str(sample_size)[:-3]+"k" if sample_size >= 1000 else str(sample_size)
    for i in range(start_collection, start_collection + no_data_sets):
        start_time = time.perf_counter()
        collection_name = prefix + "_" + str(i)
        if "KyberSlash" in output_directory:
            ksPayloads.generatePayloadFile(sample_size, collection_name, 
                                         output_directory, 
                                         payload_generation_file, 
                                         safe_mode
                                         )
        else:
            payloads.generatePayloadFile(sample_size, collection_name, 
                                         output_directory, 
                                         payload_generation_file, 
                                         safe_mode
                                         )
        end_time = time.perf_counter()
        print("Number:", i ,"Time elapsed: ", round(end_time - start_time, 3), "seconds")
