#!/usr/bin/env python
from ftplib import FTP
import itertools
import os
import tempfile
import csv
import platform


YEAR_RANGE = [str(year) for year in range(1993, 2013)] # Range of beginning year to end year + 1
QTR_RANGE  = [str(qtr) for qtr in [1, 2, 3, 4]]      # If you want all quarters use 1-4, if a quarter does not exist,
                                               # you should run the program twice, once with all full years,
                                               # and again with all partial years.

TIME_PERIODS = [(year, "QTR" + qtr) for year, qtr in itertools.product(YEAR_RANGE, QTR_RANGE)]


if "Linux" in platform.system():
    INDEX_DIR = "/home/chad/Documents/Edgar/Indices"

else:
    INDEX_DIR = r"C:/Users/czh156/Desktop/Edgar/Indices"

try:
    os.makedirs(INDEX_DIR)
except OSError:
    pass

def edgar_login():
    ftp = FTP(host="ftp.sec.gov", user="anonymous", passwd="anon@anon")
    return ftp


def write_csv(fh, local_file):

    local_file = open(local_file, "w", newline="")
    csv_local = csv.writer(local_file)

    for line in fh:
        if line.count(b"|") < 4:
            continue
        datalines = [data.decode("utf-8", "ignore").strip() for data in line.split(b"|")]
        csv_local.writerow(datalines)


def download_index(period, edgar):

    year, quarter = period
    url = '/edgar/full-index/{0}/{1}'.format(year, quarter)

    fh = tempfile.TemporaryFile()
    edgar.cwd(url)
    edgar.retrbinary("RETR master.idx", fh.write)

    return fh


def main():

    edgar = edgar_login()

    for period in TIME_PERIODS:
        tempidx = download_index(period, edgar)
        tempidx.seek(0)
        local_file = os.path.join(INDEX_DIR, "_".join(period) + ".csv")
        write_csv(tempidx, local_file)


if __name__ == "__main__":
    main()
