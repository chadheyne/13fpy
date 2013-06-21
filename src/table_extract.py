#!/usr/bin/env python

import glob
import os
import sys
import csv
import re
import platform
import itertools
from collections import OrderedDict, defaultdict
from table_templates import tab_file, csv_file, reg_file

__author__ = "Chad Heyne"
__email__ = "chadheyne@smeal.psu.edu"

########################################################################################################
#                                                                                                      #
#                                                                                                      #
#                                                                                                      #
#                                                                                                      #
#                                                                                                      #
#                                                                                                      #
#                                                                                                      #
########################################################################################################

def directories():

    if "Linux" in platform.system():
        repo = "/home/chad/Code/Repos/Python/13fpy"
        tables = "/home/chad/Documents/13F/tables_banks"
        rawdata = "/home/chad/Documents/13F/rawdata_banks"
        broken = "/home/chad/Documents/13F/broken_banks"
        unprocessed = "/home/chad/Documents/13F/unprocessed_banks"
        remain = "/home/chad/Documents/13F/remainder_banks"
    else:
        repo = r"C:/Users/czh156/Repos/Python/13fpy"
        tables = r"C:/Users/czh156/Desktop/tables_banks"
        rawdata = r"C:/Users/czh156/Desktop/rawdata_banks"
        broken = r"C:/Users/czh156/Desktop/broken_banks"
        unprocessed = r"C:/Users/czh156/Desktop/unprocessed_banks"
        remain = r"C:/Users/czh156/Desktop/remainder_banks"
    return repo, tables, rawdata, broken, unprocessed, remain


def validate_cusip(cusip, cusips):
    """ Check if CUSIP is in the dictionary of all possible CUSIPs """
    return cusip in cusips


def validate_entry(entry, pattern):
    return pattern.search(entry)


def validate_row(row, patterns):
    hits = 1
    for pattern in patterns:
        for item in row:
            if validate_entry(item, pattern):
                hits += 1
                break
    return hits >= len(row)


def find_eligible_rows(cik, date, data, cusips, patterns, unprocessed_output, remainder_output):
    """
        Loop through all files looking for anything similar to a CUSIP and write to intermediate file
    """

    keep_rows = []
    bad_rows = []

    keep_going = False

    filename = os.path.splitext(os.path.split(unprocessed_output)[-1])[0]
    for row_no, row in enumerate(data):

        if patterns["SkipL"].search(row):
            row_data = {}
            bad_rows.append(row)
            keep_going = False
            continue

        row = row.replace("-", "")
        matches = patterns["CUSIP"].findall(row)
        row_data = {}

        if patterns["UseL"].search(row):
            keep_going = True
        if patterns["StopL"].search(row):
            keep_going = False

        for match in sorted(matches, key=len, reverse=True):
            match = match.upper()
            if validate_cusip(match, cusips) or validate_cusip(match[:6], cusips):
                cusip = match
                row_data = {"CUSIP": cusip, "Line": row.rstrip("\n"), "Shprn": ""}
                shrpn = patterns["Shprn"].findall(row.split(cusip)[-1])
                for hit in shrpn:
                    if validate_entry(hit, patterns["Shprn"]):
                        row_data["Shprn"] = hit
                        break

                keep_rows.append(row_data)
                break

        if not row_data:
            bad_rows.append(row)

    if keep_rows:
        maxlen = max([len(row) for row in keep_rows])
        minlen = min([len(row) for row in keep_rows])

        for item in sorted(list(keep_rows), key=len):
            if len(item) > minlen + 20:  # < > ?
                keep_rows.remove(item)
                bad_rows.append(item["Line"])

        f_out = open(unprocessed_output, "w", newline="", encoding="utf-8")
        csv_f = csv.writer(f_out, csv.QUOTE_ALL)
        csv_f.writerow(["CUSIP", "Shprn", "Line"])
        for row in keep_rows:
            csv_f.writerow([row["CUSIP"], row["Shprn"], row["Line"].lstrip(" ")])
            if patterns["Anyopt"].search(row["Line"]):
                print("File: {0} --- Data: {1}".format(filename, row["Line"]))
        f_out.close()

    if bad_rows:
        f_out = open(remainder_output, "w", newline="", encoding="utf-8")
        for row in bad_rows:
            f_out.write(row + "\n")
        f_out.close()

    return keep_rows


def parse_file(cik, date, data, cusips, patterns, output_table, broken_output):
    """
        Master parser. Split lines on CUSIP and ship off to one of three parsers: csv, tab, regular
        based on file contents.
    """

    cusip_hits = []
    before_cusip, after_cusip = [], []

    use_tab = use_csv = garbage = 0
    use_html = False

    for line in data:
        cusip = line["CUSIP"]

        if line["Line"].strip().startswith(cusip) and len(line["Line"].strip()) > len(cusip) + 15:
            cusip_first = True
        elif line["Line"].strip().startswith(cusip) and len(line["Line"].strip()) < len(cusip) + 5:
            garbage += 1

        try:
            before, after = line["Line"].split(cusip, 1)
        except ValueError:
            continue

        if "\t" in line["Line"]:
            use_tab += 1

        if "<HTML>" in line["Line"].upper():
            use_html = True

        if line["Line"].count(",") > line["Line"].count(" "):
            use_csv += 1

        before_cusip.append(before.rstrip(",\t"))
        after_cusip.append(after.lstrip(",\t"))

        cusip_hits.append(cusip)

    datalines = {"CPS": cusip_hits, "BFR": before_cusip, "AFR": after_cusip, "DTA": data}

    if use_tab > len(data)//2:
        print("File: {0}, CIK: {1}, Date: {2} using Tabs".format(output_table, cik, date))
        tab_file(cik, date, datalines, cusips, patterns, output_table, broken_output)
    elif use_csv > len(data)//2:
        print("File: {0}, CIK: {1}, Date: {2} using csv".format(output_table, cik, date))
        csv_file(cik, date, datalines, cusips, patterns, output_table, broken_output)
    elif use_html:
        print("File: {0}, CIK: {1}, Date: {2} using HTML".format(output_table, cik, date))
    elif garbage > len(data)//2:
        print("File: {0}, CIK: {1}, Date: {2} looks like garbage".format(output_table, cik, date))
    else:
        print("File: {0}, CIK: {1}, Date: {2} using sieve".format(output_table, cik, date))
        reg_file(cik, date, datalines, cusips, patterns, output_table, broken_output)

    return datalines


def load_files(rawdata_dir):
    """ Change to point to data directory with rawdata from Edgar"""
    return sorted(glob.glob(rawdata_dir + "/*/*.txt"))


def load_cusips(repo_dir):
    """
        Use data from WRDS on CUSIPs to create a dictionary of any possible CUSIP.
        1) From CUSIP database. 6, 8, and 9 digit cusips with and without leading zeros.
        2) From CRSP database, 8 digit cusips and ncusips with and without leading zeros.
        3) From CRSP headers database, 8 digit cusips with and without leading zeros.
    """

    cusips = {}
    with open(os.path.join(repo_dir, "Data", "CUSIPs.csv"), "r", encoding="utf-8", newline="") as c_file:
        cusip_dict = csv.DictReader(c_file)
        for line in cusip_dict:
            cusips[line["CUSIP8"] + line["ISSUE_CHECK"]] = 1
            cusips[line["ISSUER_NUM"]] = 1
            cusips[line["ISSUER_NUM"].lstrip("0")] = 1
            cusips[line["CUSIP8"].lstrip("0")] = 1
            cusips[line["CUSIP8"].lstrip("0") + line["ISSUE_CHECK"]] = 1

    with open(os.path.join(repo_dir, "Data", "crsp_cusip.csv"), "r", encoding="utf-8", newline="") as crsp_file:
        crsp_dict = csv.DictReader(crsp_file)
        for line in crsp_dict:
            cusips[line["CUSIP"]] = 1
            cusips[line["CUSIP"].lstrip("0")] = 1
            cusips[line["NCUSIP"]] = 1
            cusips[line["NCUSIP"].lstrip("0")] = 1

    with open (os.path.join(repo_dir, "Data", "wrds_cusip.csv"), "r", encoding="utf-8", newline="") as wrds_file:
        wrds_dict = csv.DictReader(wrds_file)
        for line in wrds_dict:
            cusips[line["CUSIP"]] = 1
            cusips[line["CUSIP"].lstrip("0")] = 1

    return cusips


def load_patterns(repo_dir):
    """Set of regular expressions to filter text"""

    pattern_file = open(os.path.join(repo_dir, "src", "patterns.csv"), "r", encoding="utf-8", newline="")
    pattern_dict = csv.DictReader(pattern_file)
    patterns = OrderedDict()
    for line in pattern_dict:
        patterns[line["Type"]] = re.compile(line["Pattern"], re.IGNORECASE)
    return patterns


def make_dirs(dirs_to):
    for item in dirs_to:
        try:
            os.makedirs(item)
        except OSError:
            pass


def clean_run(repo_dir, unprocessed_dir):
    del_files = glob.glob(os.path.join(repo_dir, "Data") + "/logdata*.txt")
    for f in del_files:
        os.remove(f)
    unproc_files = glob.glob(unprocessed_dir + "/*/*.txt")
    for f in unproc_files:
        os.remove(f)


def main():

    repo_dir, tables_dir, rawdata_dir, broken_dir, unprocessed_dir, remain_dir = directories()
    cusips = load_cusips(repo_dir)
    patterns = load_patterns(repo_dir)
    file_list = load_files(rawdata_dir)

    if len(glob.glob(unprocessed_dir + "/*/*.txt")) <= len(file_list):
        clean_run(repo_dir, unprocessed_dir)

    log = open(os.path.join(repo_dir, "Data", "log.txt"), "w")

    sys.stdout = log
    for f in file_list:
        raw_dir, input_table = os.path.split(f)
        dir_tables = os.path.join(tables_dir, os.path.basename(raw_dir).replace("rawdata", "tables"))
        dir_broken = os.path.join(broken_dir, os.path.basename(raw_dir).replace("rawdata", "broken"))
        dir_unproc = os.path.join(unprocessed_dir, os.path.basename(raw_dir).replace("rawdata", "unprocessed"))
        dir_remain = os.path.join(remain_dir, os.path.basename(raw_dir).replace("rawdata", "remainder"))
        make_dirs([dir_tables, dir_broken, dir_unproc, dir_remain])

        with open(f) as data_file:
            data = [line.rstrip() for line in data_file.readlines()]

        cik, date, _ = input_table.split("_")
        log_data = os.path.join(repo_dir, "Data", "logdata" + date.split("-")[0] + ".txt")
        table_output = os.path.join(dir_tables, input_table)
        broken_output = os.path.join(dir_broken, input_table)

        unprocessed_output = os.path.join(dir_unproc, input_table)
        remainder_output = os.path.join(dir_remain, input_table)

        if not os.path.exists(unprocessed_output):
            logdata = open(log_data, "a")
            sys.stdout = logdata
            line_data = find_eligible_rows(cik, date, data, cusips, patterns, unprocessed_output, remainder_output)
            logdata.flush()
            os.fsync(logdata.fileno())
            sys.stdout = log

        else:
            with open(unprocessed_output) as line_file:
                csv_lines = csv.DictReader(line_file)
                line_data = [line for line in csv_lines]

        parse_file(cik, date, line_data, cusips, patterns, table_output, broken_output)

        log.flush()
        os.fsync(log.fileno())

    log.close()
    logdata.close()
    sys.stdout = sys.__stdout__

if __name__ == "__main__":
    main()
