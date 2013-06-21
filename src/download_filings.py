#!/usr/bin/env python

import itertools
import os
import platform
import sys
import re
import csv
from collections import defaultdict
from ftplib import FTP

"""
 Set CIKS to None if there are no specific companies that are of particular interest. This will download
 the filings for all CIKS for the filing types specified in FILING_TYPE. If FILING_TYPE is also None, This
 will attempt to download the entirety of Edgar. You should restrict at least one of CIKS or FILING_TYPE
 to a subset of Edgar filings.

"""

#CIKS = []
CIKS = None

FILING_TYPE = ["13F-HR", "13F-HR/A", "13F-NT", "13F-NT/A"]
#FILING_TYPE = None

YEAR_RANGE = [str(year) for year in range(1999, 2013)] # Range of beginning year to end year + 1
QTR_RANGE = [str(qtr) for qtr in [1, 2, 3 4]] # If you want all quarters use 1-4, if a quarter does not exist,
                                               # you should run the program twice, once with all full years,
                                               # and again with all partial years.

TIME_PERIODS = [(year, "QTR" + qtr) for year, qtr in itertools.product(YEAR_RANGE, QTR_RANGE)]


if "Linux" in platform.system():
    RAWDATA_DIR = "/home/chad/Documents/Edgar/"
    INDEX_DIR = "/home/chad/Documents/Edgar/Indices"
else:
    RAWDATA_DIR = r"C:/Users/czh156/Desktop/Edgar/"
    INDEX_DIR = r"C:/Users/czh156/Desktop/Edgar/Indices"


def edgar_login():
    ftp = FTP(host="ftp.sec.gov", user="anonymous", passwd="anon@anon")
    return ftp


def index_reader(index):
    with open(index + ".csv", "r", encoding="utf-8") as index_file:
        index_csv = csv.DictReader(index_file)
        file_type = defaultdict(list)
        file_name = defaultdict(list)
        file_list = []
        for line in index_csv:
            file_list.append(dict(line))
            file_type[line["Form Type"]].append(dict(line))
            file_name[line["CIK"]].append(dict(line))
        return file_list, file_type, file_name


def download_filing(filing, year, quarter, edgar):

    url = filing["Filename"]
    directory = os.path.join(RAWDATA_DIR, "_".join(["rawdata", year, quarter]))

    try:
        os.makedirs(directory)
    except OSError:
        pass

    ftp_extension = url.split("-")[-1].strip(".txt").lstrip("0")
    cik = filing["CIK"].lstrip("0")
    date = filing["Date Filed"]
    with open(os.path.join(directory, "_".join([cik, date, ftp_extension])) + ".txt", "wb") as local_file:
        edgar.retrbinary("RETR {0}".format(url), local_file.write)


def main():

    if not RAWDATA_DIR:
        sys.exit("Please input the name of the directory that you would like files saved to.")

    edgar = edgar_login()

    for period in TIME_PERIODS:

        year, quarter = period
        index_list, type_list, cik_list = index_reader(os.path.join(INDEX_DIR, "_".join(period) + ".csv"))

        if CIKS is not None:
            for cik in CIKS:
                downloads = cik_list[cik]
                for download in downloads:
                    if FILING_TYPE is None:
                        download_filing(download, year, quarter, edgar)
                    elif download["Form Type"] in FILING_TYPE:
                        download_filing(download, year, quarter, edgar)
                    else:
                        continue

        elif FILING_TYPE is not None:
            for filing_type in FILING_TYPE:
                downloads = type_list[filing_type]
                for download in downloads:
                    if CIKS is None:
                        download_filing(download, year, quarter, edgar)
                    elif download["CIK"] in CIKS:
                        download_filing(download, year, quarter, edgar)
                    else:
                        continue

        elif CIKS is None and FILING_TYPE is None:
            for filing in index_list:
                download_filing(filing, year, quarter, edgar)



if __name__ == "__main__":
    main()
