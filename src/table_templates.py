import glob
import os
import sys
import csv
import re
import platform
import itertools
from collections import OrderedDict, defaultdict

__author__ = "Chad Heyne"
__email__ = "chadheyne@smeal.psu.edu"

########################################################################################################
#                                                                                                      #
#             Helper functions for extracting data from SEC Edgar 13F holdings files                   #
#             1) tab delimited files                                                                   #
#             2) csv delimited files                                                                   #
#             3) pseudo fixed width files                                                              #
#             4) html tables---None in this dataset                                                    #
#                                                                                                      #
########################################################################################################

def tab_file(cik, date, datalines, cusips, patterns, output_table, broken_output):

    filename = os.path.splitext(os.path.split(output_table)[-1])[0]
    output_file = open(output_table, "w", newline="", encoding="utf-8")

    output_csv = csv.writer(output_file, csv.QUOTE_ALL)
    output_csv.writerow(["Poss_hit", "Name", "Type", "CUSIP", "Value", "Shares", "Opt", "Extra"])

    cusip_hits   = datalines["CPS"]
    before_cusip = datalines["BFR"]
    after_cusip  = datalines["AFR"]
    data         = datalines["DTA"]


    pre_dict = defaultdict(int)
    for line in before_cusip:
        match = re.search(r"\t\w", line)
        if match:
            pre_dict[match.start()] += 1
    try:
        com_pre = max(pre_dict, key=pre_dict.get)
    except ValueError:
        com_pre = 30

    pre_split = [k for k, v in pre_dict.items() if v > len(before_cusip)//10]

    post_dict = defaultdict(int)
    for line in after_cusip:
        matchval = re.search(r"(\d+)\t+(\d+)", line)
        if matchval:
            pre_dict[matchval.start()] += 1

    post_split = [k for k, v in post_dict.items() if v > len(after_cusip)//10]

    beg_splits = sorted([c for c in pre_split if c+1 not in pre_split])
    end_splits = sorted([c for c in post_split if c-1 not in post_split])

    for cusip, before, after, data in zip(cusip_hits, before_cusip, after_cusip, data):

        if patterns["Anyopt"].search(before + after):
            poss_opt = True
        else:
            poss_opt = False

        try:
            name, co_type = before.split(r"\t", 1)
        except ValueError:
            try:
                name, co_type = before[:com_pre], before[com_pre:]
            except IndexError:
                name, co_type = before, "-999999"

        row_data = [name, co_type, cusip]

        val_shr = re.search(r"(\d+)\t+(\d+)", after)
        if val_shr:
            try:
                value, shares = val_shr.groups()
            except ValueError:
                value, shares = after.split("\t")[0:1]
        else:
            try:
                value, shares = after.split("\t")[0:1]
            except ValueError:
                value, shares = after, "-999999"
        row_data += value, shares

        if poss_opt:
            if patterns["Anyopt"].search(after):
                option = patterns["Anyopt"].search(after).group()
            else:
                option = patterns["Anyopt"].search(before + after).group()
        else:
            option = "Unlikely"
        row_data += [option]
        remainder = re.sub(r"[^\s\tA-Za-z]", "", after)
        row_data += [remainder]

        data_want = ["Poss_hit", "Name", "Type", "CUSIP", "Value", "Shares", "Opt", "Extra"]
        row_data = [str(i).strip() for i in row_data]
        row_data.insert(0, poss_opt)
        if poss_opt:
            print("File: {0} --- Data: {1}".format(filename, row_data))
        use_this = list(itertools.zip_longest(data_want, row_data, fillvalue="Other"))
        output_csv.writerow([a[1] for a in use_this])
    output_file.close()


def csv_file(cik, date, datalines, cusips, patterns, output_table, broken_output):
    """
        Simple case of csv delimited files
    """

    filename = os.path.splitext(os.path.split(output_table)[-1])[0]
    output_file = open(output_table, "w", newline="", encoding="utf-8")
    output_csv = csv.writer(output_file, csv.QUOTE_ALL)
    data_want = ["Poss_hit", "Name", "Type", "CUSIP", "Value", "Shares", "Opt", "Extra"]
    output_csv.writerow(data_want)

    line_data = csv.reader([line["Line"] for line in datalines["DTA"]])

    for line in line_data:

        if len(line) > 5:
            name, cusip, value, shares, *extra = line
        else:
            continue

        if patterns["Anyopt"].search(name + " ".join(extra)):
            poss_opt = True
        else:
            poss_opt = False

        row_data = [poss_opt, name, "N/A", cusip, value, shares, "N/A", " ".join(extra)]

        if poss_opt:
            print("File: {0} --- Data: {1}".format(filename, row_data))

        use_this = list(itertools.zip_longest(data_want, row_data, fillvalue="Other"))
        output_csv.writerow([a[1] for a in use_this])
    output_file.close()


def reg_file(cik, date, datalines, cusips, patterns, output_table, broken_output):
    """
        Pseudo fixed width file. Split lines on CUSIP and index the most common occurrence of
        multiple spaces separating fields. Attempt multiple splits of the data in decreasing
        confidence of the results
    """

    filename = os.path.splitext(os.path.split(output_table)[-1])[0]
    output_file = open(output_table, "w", newline="", encoding="utf-8")
    output_csv = csv.writer(output_file, csv.QUOTE_ALL)
    output_csv.writerow(["Poss_hit", "Name", "Type", "CUSIP", "Value", "Shares", "Opt", "Extra"])

    cusip_hits = datalines["CPS"]
    before_cusip  = [re.sub(r"[-\t\.,$]", "", row) for row in datalines["BFR"]]
    after_cusip   = [re.sub(r"[-\t\.,$]", "", row) for row in datalines["AFR"]]
    data          = datalines["DTA"]
    pre_split, post_split = [], []
    beg_splits, end_splits = [], []
    split_lines = []

    pre_dict = defaultdict(int)
    for line in before_cusip:
        if re.search(r"\s{2}\w", line):
            pre_dict[re.search(r"\s{2}\w", line).start()] += 1
    try:
        com_pre = max(pre_dict, key=pre_dict.get)
    except ValueError:
        com_pre = 30

    pre_split = [k for k, v in pre_dict.items() if v > len(before_cusip)//10]

    post_dict = defaultdict(int)
    for line in after_cusip:
        if re.search(r"\d\s{2,}\d", line):
            post_dict[re.search(r"\d\s{2,}\d", line).start() + 1] += 1
    try:
        com_post = max(post_dict, key=post_dict.get)
    except ValueError:
        com_post = -1

    post_split = [k for k, v in post_dict.items() if v > len(after_cusip)//10]

    beg_splits = sorted([c for c in pre_split if c+1 not in pre_split])
    end_splits = sorted([c for c in post_split if c-1 not in post_split])

    print("Parsing CIK: {0} - Date: {1}".format(cik, date))
    print("Line matches: BEG - {0} --- END - {1}".format(beg_splits, end_splits))

    for cusip, before, after, data in zip(cusip_hits, before_cusip, after_cusip, data):

        if patterns["Anyopt"].search(before + after):
            poss_opt = True
        else:
            poss_opt = False

        if re.search(r"\s{2}\w", before):
            try:
                name_co = re.search(r"\s{2,}\w", before)
                name, co_type = before[:name_co.start() + 1], before[name_co.end() - 2:]
            except ValueError:
                name, co_type = before, "-999999"
        else:
            try:
                name, co_type = before[:com_pre], before[com_pre:]
            except IndexError:
                name, co_type = before, "-999999"

        row_data = [name, co_type, cusip]

        val_shr = re.search(r"(\d+)\s{2,}(\d+)", after)

        if val_shr:
            try:
                value, shares = val_shr.groups()
            except ValueError:
                value, shares = after[:val_shr.start() + 1], after[val_shr.end() - 2:].split(" ", 1)[0]
        elif re.search(r"(\d+)\s(\d+)", after):
            try:
                value, shares = re.search(r"(\d+)\s(\d+)", after).groups()
            except ValueError:
                value, shares = after[:re.search(r"\d\s\d", after).start() + 1], after[re.search(r"\d\s\d", after).end() - 2].split(" ", 1)[0]
        elif com_post > 0:
            value, shares = after[:com_post], after[com_post:]
        else:
            value, shares = after, "-999999"
        row_data += value, shares

        if poss_opt:
            if patterns["Anyopt"].search(after):
                option = patterns["Anyopt"].search(after).group()
            else:
                option = patterns["Anyopt"].search(before + after).group()
        else:
            option = "Unlikely"
        remainder = re.sub(r"[^\sA-Za-z]", "", after)
        row_data += [option]
        row_data += [remainder]

        data_want = ["Poss_hit", "Name", "Type", "CUSIP", "Value", "Shares", "Opt", "Extra"]
        row_data = [str(i).strip() for i in row_data]
        row_data.insert(0, poss_opt)
        if poss_opt:
            print("File: {0} --- Data: {1}".format(filename, row_data))
        use_this = list(itertools.zip_longest(data_want, row_data, fillvalue="Other"))
        output_csv.writerow([a[1] for a in use_this])
    output_file.close()

def main():
    pass

if __name__ == "__main__":
    main()
