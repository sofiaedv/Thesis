# -*- coding: utf-8 -*-
"""
Created on Fri Apr 18 20:42:09 2025

@author: sofia.edvardsson
"""

import numpy as np
import pandas as pd
import pathlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from sklearn.metrics import matthews_corrcoef

def matthew(df):
    mcc = []
    columns = df.columns
    
    for col in columns[1:]:
        mcc.append(matthews_corrcoef(df[columns[0]], df[col]))
    
    return mcc

def result(df):
    columns = df.columns
    df_True = df[df[columns[0]] == 1]
    df_False = df[df[columns[0]] == 0]
    
    TP = df_True[columns[1:]].sum(axis=0)
    FN = len(df_True) - TP
    
    FP = df_False[columns[1:]].sum(axis=0)
    TN = len(df_False) - FP
    
    mcc = matthew(df)
    
    df_result = pd.DataFrame({"TP": TP,
                              "FN": FN,
                              "TN": TN,
                              "FP": FP,
                              "Type-I": FP/len(df_False),
                              "Type-II": FN/len(df_True),
                              "Accuracy": (TP + TN)/len(df),
                              "MCC": mcc})
    
    return df_result

def plot_attribute(dfs, attribute, title, subtitle, sizes, save_plot=False, output_file=""):
    full_toolnames = {"Mona": "Mona Timing Report",
                      "dudect": "dudect",
                      "Welch": "Welch t-test",
                      "RTLF": "RTLF"}
    plt.figure()
    tools = dfs[0].index
    
    plt.grid(axis="y", linewidth=0.5)
    
    if attribute == "MCC":
        plt.plot(sizes, [0.5]*len(sizes), f"C{len(tools)}--", label="MCC threshold")
    
    for tool in tools:
        tool_result = []
        for df in dfs:
            if tool in df.index:
                tool_result.append(df.loc[tool][attribute])
        if len(tool_result) > 0:
            plt.plot(sizes[:len(tool_result)], tool_result, label=full_toolnames[tool])
        
    if attribute == "MCC":
        plt.ylim(-0.65, 0.65)
    elif attribute == "Accuracy":
        plt.ylim(-0.05, 0.75)
    else:
        plt.ylim(-0.05, 1.05)
    
    if not attribute == "MCC":
        plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1))
    plt.xlabel("Samples per class")
    y_label = attribute if not "Type" in attribute else attribute + " error"
    plt.ylabel(y_label)
    plt.suptitle(title, size="x-large")
    plt.title(subtitle)
    plt.legend()
    
    if save_plot:
        plt.savefig(output_file)
    
    plt.show()
    
    
def plot_attributes(dfs, attributes, title, subtitles, sizes):
    full_toolnames = {"Mona": "Mona Timing Report",
                      "dudect": "dudect",
                      "Welch": "Welch t-test",
                      "RTLF": "RTLF"}
    tools = dfs[0].index
    
    fig, axs = plt.subplots(ncols=2, figsize=(2*6.4, 4.8))
    
    for i in range(len(attributes)):
        attribute = attributes[i]
        
        axs[i].grid(axis="y", linewidth=0.5)
    
        if attribute == "MCC":
            axs[i].plot(sizes, [0.5]*len(sizes), f"C{len(tools)}--", label="MCC threshold")
        
        for tool in tools:
            tool_result = []
            for df in dfs:
                tool_result.append(df.loc[tool][attribute])
            axs[i].plot(sizes, tool_result, label=full_toolnames[tool])
            
        if attribute == "MCC":
            axs[i].ylim(-0.65, 0.65)
        else:
            axs[i].set_ylim(-0.05, 1.05)
            axs[i].yaxis.set_major_formatter(mtick.PercentFormatter(1))
        axs[i].set_xlabel("Samples per class")
        y_label = attribute if not "Type" in attribute else attribute + " error"
        axs[i].set_ylabel(y_label)
        axs[i].set_title(subtitles[i])
        #axs[i].legend()
    fig.legend(list(full_toolnames.values())[:3], loc="outside lower center", bbox_to_anchor=(0.5,-0.075), ncol=len(list(full_toolnames.values())[:3]), bbox_transform=fig.transFigure)
    plt.suptitle(title, size="x-large")
    plt.show()
    

if __name__ == "__main__":
    input_directories = [
        "./../data/verdicts/isolated/KyberSlash1_2/c_programs/",
        "./../data/verdicts/isolated/c_programs/",
        "./../data/verdicts/c_programs/",
        "./../data/verdicts/KyberSlash1_2/c_programs/"
        ]
    titles = [
        "Vulnerability specific payloads - Low noise",
        "Naive payloads - Low noise",
        "Naive payloads - High noise",
        "Vulnerability specific payloads - High noise"
        ]
    
    mcc_sums = []
    mcc_sums_high = []
    mcc_sums_low = []
    for j in range(len(input_directories)):
        neg_count = []
        
        input_directory = input_directories[j]
        title = titles[j]
        
        print("########  " + title + "  ########")
        
        sizes = ["10k", "30k", "50k", "100k"]
        dfs = []
        for size in sizes:
            df = pd.read_csv(input_directory + f"{size}_verdicts.csv",
                             sep=";",
                             header=0,
                             index_col=0)
            if pathlib.Path(input_directory + f"{size}_verdicts_RTLF.csv").exists():
                df_RTLF = pd.read_csv(input_directory + f"{size}_verdicts_RTLF.csv",
                                 sep=";",
                                 header=0,
                                 index_col=0)
                df["RTLF"] = df_RTLF["RTLF"]
            df_result = result(df)
            dfs.append(df_result)
            print("Class size:", size)
            print(df_result)
            
            neg_count.append(df_result["FN"].sum(axis=0) + df_result["TN"].sum(axis=0))
            
            if j == 0 or j == 3:
                mcc_sums.append(df_result["MCC"].sum(axis=0))
                #mcc_sums.append(df_result["TP"].sum(axis=0))
                if j == 0:
                    mcc_sums_low.append(df_result["Accuracy"].sum(axis=0))
                else:
                    mcc_sums_high.append(df_result["Accuracy"].sum(axis=0))
            print()
        
        payload_type = "Naive" if "Naive" in title else "KyberSlash"
        setup_type = "LowNoise" if "Low" in title else "HighNoise"
        
        save = False
        
        plot_attribute(dfs, "Accuracy", title, "Tool accuracy rates", sizes, save, f"./../../Thesis/Figures/Accuracy_{payload_type}_{setup_type}.png")
        plot_attribute(dfs, "MCC", title, "Tool MCC values", sizes, save, f"./../../Thesis/Figures/MCC_{payload_type}_{setup_type}.png")
        plot_attribute(dfs, "Type-I", title, "Tool Type-I error rates", sizes, save, f"./../../Thesis/Figures/Type-I_{payload_type}_{setup_type}.png")
        plot_attribute(dfs, "Type-II", title, "Tool Type-II error rates", sizes, save, f"./../../Thesis/Figures/Type-II_{payload_type}_{setup_type}.png")
        #plot_attributes(dfs, ["Type-I", "Type-II"], title, ["Tool Type-I error rates", "Tool Type-II error rates"], sizes)
        
        print("Average n.o. negatives: ", sum(neg_count)/16)
        print()
        
    print("##### STATS #####")
    print("Total: ", sum(mcc_sums)/32)
    print("Low noise: ", sum(mcc_sums_low)/12)
    print("High noise: ", sum(mcc_sums_high)/12)
    print()
        