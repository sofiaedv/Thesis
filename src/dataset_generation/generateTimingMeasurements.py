#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  5 09:20:44 2025

@author: sofiaedvardsson
"""

import subprocess
import pathlib
import time
import numpy as np
import pandas as pd
import gzip
import struct
#import matplotlib.pyplot as plt


##############################
## PARAMETERS

collection_name = "100k_25"
input_directory = "./../Exjobb/src/dataset_generation/payloads/" + collection_name
output_directory = "./../Exjobb/data/timing_measurements/"
safe_mode = False
file_for_time_collection = "./sc-test-kyberk2so"


##############################
## FUNCTIONS

go_libraries = ["circl-0", "circl-2", 
                "crystals-go-0", "crystals-go-2", "crystals-go-12", 
                "kyber-k2so-0", "kyber-k2so-2", "kyber-k2so-12"]

def createCSV(classes, time_measurements, collection_name, input_directory, output_directory, library):
    library = "_" + library if not library == "" else ""
    d = {"Class": classes, "Time": time_measurements}
    df = pd.DataFrame(data=d)
    
    output_directory_index = pathlib.Path(output_directory) / "index"
    output_directory_no_index = pathlib.Path(output_directory) / "no_index"
    
    output_directory_index.mkdir(parents=True, exist_ok=True)
    output_directory_no_index.mkdir(parents=True, exist_ok=True)
    
    csv_file_index = output_directory_index / (collection_name + "_index" + library + "_timing_measurements.csv")
    csv_file_no_index = output_directory_no_index / (collection_name + "_no_index" + library + "_timing_measurements.csv")
    
    df.to_csv(csv_file_index, sep=";", header=False, index=True)
    df.to_csv(csv_file_no_index, sep=";", header=False, index=False)


def getTimingMeasurementTest(payload, file_for_time_collection):
    process = subprocess.run(
        ["sudo", "perf", "record", "-e", "cycles:u", "-g", "-o", "./perf.data", "--", file_for_time_collection],
        input = payload,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        text = False
        )
        
    if process.returncode != 0:
        print("Error running perf record")
        
    process = subprocess.run(
        ["sudo", "perf", "report", "-i", "./perf.data", "--stdio"],
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        )
        
    if process.returncode != 0:
        print("Error generating perf report")
    
    #print(process.stdout.decode())
    
    for line in process.stdout.decode().splitlines():
        if "Decapsulate" in line:
            print(line)
            #execution_time = line.split("cycles")

    return 0 #execution_time
    
# sudo perf probe -x ./pqc_implementations/circl-0/circl-0 "github.com/cloudflare/circl/kem/kyber/kyber512.(*scheme).Decapsulate"
def getTimingMeasurementNope(payload, file_for_time_collection):
    process = subprocess.run(
        ["sudo", "perf", "stat", "-e", "probe_circl:github,cycles", file_for_time_collection],
        input = payload,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        text = False
        )
        
    stat_output = process.stderr.decode()
    
    #for line in process.stderr.decode():
    print(stat_output)
        #if "cycles" in line:
            #execution_time = line.split("cycles")

    return 0 #execution_time


def getTimingMeasurementOld(payload, file_for_time_collection):
    process = subprocess.Popen(
        [file_for_time_collection],
        stdin = subprocess.PIPE,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        )

    start_time = time.perf_counter_ns()
    process.stdin.write(payload)
    stdout, stderr = process.communicate()
    end_time = time.perf_counter_ns()
    
    execution_time = end_time - start_time
    return execution_time
    
    
def getTimingMeasurementGo(payload, file_for_time_collection):
    process = subprocess.Popen(
        [file_for_time_collection],
        stdin = subprocess.PIPE,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        text = False,
        )

    process.stdin.write(payload)
    stdout, stderr = process.communicate()
    
    execution_time = struct.unpack("<Q", stdout)[0]
    return execution_time
    
    
def getTimingMeasurement(payload, file_for_time_collection):
    process = subprocess.run(
        [file_for_time_collection],
        input = payload,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        text = False,
        )
    
    execution_time = int(process.stdout.decode())
    return execution_time


def collectTimingMeasurements(collection_name, input_directory, output_directory, file_for_time_collection, safe_mode=True, library=""):
    
    output_directory = pathlib.Path(output_directory) / collection_name
    
    if not pathlib.Path(input_directory).exists():
        print("Invalid colection")
        return
    elif safe_mode and output_directory.exists():
        if not input("Do you want to overwrite the existing directory: y/N\n").strip().lower() == "y":
            return
        
    
    output_directory.mkdir(parents=True, exist_ok=True)
    
    payload_file = input_directory + "/" + collection_name + "_payloads"
    classes_file = input_directory + "/" + collection_name + "_classes"
    
    with open(classes_file, "r", encoding="utf-8") as file:
        classes = file.read()
        
    classes = np.array(list(classes), dtype=str)
        
    times = np.empty(len(classes), dtype=np.int32)
    
    i = 0
    
    if "KyberSlash" in payload_file:
        with gzip.open(payload_file, "rb") as f:
        
            # Warm up
            for j in range(min(50, int(len(classes)/2))):
                payload = f.read(2400)
                if library in go_libraries:
                    getTimingMeasurementGo(payload, file_for_time_collection)
                else:
                    getTimingMeasurement(payload, file_for_time_collection)
            
            # Reset file read
            f.seek(0)
            
            while payload := f.read(2400):
                if library in go_libraries:
                    execution_time = getTimingMeasurementGo(payload, file_for_time_collection)
                else:
                    execution_time = getTimingMeasurement(payload, file_for_time_collection)
                #execution_time = getTimingMeasurement(payload, file_for_time_collection)
                if execution_time == None:
                    return
                
                times[i] = execution_time
                
                i += 1
    else:
        with gzip.open(payload_file, "rb") as f:
            
            dk = f.read(1632)
            
            # Warm up
            for j in range(min(50, int(len(classes)/2))):
                c = f.read(768)
                getTimingMeasurement(dk + c, file_for_time_collection)
            
            # Reset file read
            f.seek(1632)
            
            while c := f.read(768):
                execution_time = getTimingMeasurement(dk + c, file_for_time_collection)
                if execution_time == None:
                    return
                
                times[i] = execution_time
                
                i += 1

    createCSV(classes, times, collection_name, input_directory, output_directory, library)

if __name__ == "__main__":
    start_time = time.perf_counter()
    collectTimingMeasurements(collection_name, input_directory, output_directory, file_for_time_collection, safe_mode)
    end_time = time.perf_counter()
    print("Time elapsed: ", round(end_time - start_time, 3), "seconds")
    
