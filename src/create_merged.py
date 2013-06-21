#!/usr/bin/env python

import csv
import glob
import platform
import os
import re

def directories():
    if "Linux" in platform.system():
        repo_dir = "/home/chad/Code/Repos/Python/13fpy"
        tables_dir = "/home/chad/Documents/13F/tables_banks"
    else:
        repo_dir = r"C:/Users/czh156/Repos/Python/13fpy"
        tables_dir = r"C:/Users/czh156/Desktop/tables_banks"
    return repo_dir, tables_dir


def file_list(dir_table):
    return glob.glob(dir_table + "/*/*.txt")


def main():
    repo_dir, tables_dir = directories()
    textfiles = file_list(tables_dir)

    opt_file = open(os.path.join(repo_dir, "Data", "OptionFile.csv"), "w", newline="")
    sto_file = open(os.path.join(repo_dir, "Data", "StockFile.csv"), "w", newline="")
    def_file = open(os.path.join(repo_dir, "Data", "OptionDef.csv"), "w", newline="")

    csv_opt = csv.DictWriter(opt_file, ["Filename", "CIK", "Date", "Poss_hit", "Name", "Type", "CUSIP", "Value", "Shares", "Opt", "Extra", "FlagR"])
    csv_sto = csv.DictWriter(sto_file, ["Filename", "CIK", "Date", "Poss_hit", "Name", "Type", "CUSIP", "Value", "Shares", "Opt", "Extra", "FlagR"])
    csv_def = csv.DictWriter(def_file, ["Filename", "CIK", "Date", "Poss_hit", "Name", "Type", "CUSIP", "Value", "Shares", "Opt", "Extra", "FlagR"])

    csv_opt.writeheader()
    csv_sto.writeheader()
    csv_def.writeheader()
    bad_strings = ["CLA", "PU", "CL A", "CL"]
    for textfile in textfiles:
        with open(textfile, newline="") as f:
            text_dict = csv.DictReader(f)
            cik, date, ext = os.path.split(textfile)[-1].split("_")
            for line in text_dict:

                line["FlagR"] = None
                line["Filename"] = os.path.splitext(os.path.basename(textfile))[0]
                line["CIK"] = cik
                line["Date"] = date

                if line["Poss_hit"] == "True":
                    if line["Type"] == "-999999" or line["Shares"] == "-999999":
                        continue

                    if len(line["Name"]) > 35:
                        line["FlagR"] = "Likely bad observation"
                    elif not line["Value"] or not line["Shares"]:
                        line["FlagR"] = "Missing shares or value"
                    elif line["CUSIP"] == line["Value"] or line["CUSIP"] == line["Shares"]:
                        line["FlagR"] = "Possible invalid CUSIP, same as shares or value"
                    elif line["Opt"].upper() in bad_strings or re.search(r"[^0-9A-Za-z]", line["Opt"]):
                        line["FlagR"] = "Likely false positive"

                    else:
                        line["FlagR"] = "Likely true positive"

                    csv_opt.writerow(line)

                if line["Opt"].upper() == "CALL" or line["Opt"].upper() == "PUT":
                    csv_def.writerow(line)

                csv_sto.writerow(line)


    opt_file.close()
    sto_file.close()

if __name__ == "__main__":
    main()