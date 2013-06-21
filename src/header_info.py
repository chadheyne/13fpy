#!/usr/bin/env python

import glob
import os
import csv
import re
import platform


if 'Linux' in platform.system():
    prefix = '/home/chad/Code/Repos/Python/13fpy'
    data_dir = '/home/chad/Documents/13F/rawdata_banks'
else:
    prefix = r'C:/Users/czh156/Repos/Python/13fpy'
    data_dir = r'C:/Users/czh156/Desktop/rawdata_banks'


def parse_header(file_name, header, dollar_match, entry_match, number_match):
    f = open(file_name)
    lines = f.readlines()
    in_table = False

    subset = ['Number of Other Included Managers',
              'Form 13F Information Table Entry Total',
              'Form 13F Information Table Value Total']

    for line in lines:
        if line.startswith('<SEC-HEADER>'):
            in_table = True
        elif line.startswith('</SEC-HEADER>'):
            in_table = False

        if in_table:
            for key in header.keys():
                if line.strip().startswith(key+':'):
                    header[key] = line.split(':')[-1].strip()

        for key in subset:
            if key.lower() in line.lower() and header[key] == '':

                if key == 'Form 13F Information Table Value Total':
                    results = dollar_match.search(line.lower())
                    header[key] = results.group(1)
                elif key == 'Form 13F Information Table Entry Total':
                    results = entry_match.search(line.lower())
                    header[key] = results.group(1)
                elif key == 'Number of Other Included Managers':
                    results = number_match.search(line.lower())
                    header[key] = results.group(1)

        if header['Form 13F Information Table Value Total']:
            break
    return header


def main():

    file_list = glob.glob(os.path.join(data_dir, '*/*.txt'))
    headers = open(os.path.join(prefix, 'Data/headerinfo.csv'), 'w', encoding='utf-8', newline='')
    headers_csv = csv.DictWriter(headers, ['File', 'CIK', 'date', 'URL', 'ACCESSION NUMBER', 'CONFORMED SUBMISSION TYPE',
                                           'PUBLIC DOCUMENT COUNT', 'EFFECTIVENESS DATE', 'CONFORMED PERIOD OF REPORT',
                                           'FILED AS OF DATE', 'COMPANY CONFORMED NAME', 'CENTRAL INDEX KEY', 'IRS NUMBER',
                                           'FISCAL YEAR END', 'FORM TYPE', 'SEC FILE NUMBER', 'FILM NUMBER',
                                           'STREET 1', 'STREET 2', 'CITY', 'STATE', 'ZIP', 'BUSINESS PHONE',
                                           'Number of Other Included Managers',
                                           'Form 13F Information Table Entry Total',
                                           'Form 13F Information Table Value Total'], csv.QUOTE_ALL)
    headers_csv.writeheader()
    dollar_match = re.compile(r"\s*{0}:?\s*\$?_*(\s?\d*,?\d*,?\d*\.?\d*).*$".format('form 13f information table value total'))
    entry_match = re.compile(r"\s*{0}:?\s*_*(\d*,?\d*,?\d*).*$".format('form 13f information table entry total'))
    number_match = re.compile(r"\s*{0}:?\s*_*(\d*).*?".format('number of other included managers'))

    for f in file_list:

        name = os.path.splitext(os.path.basename(f))[0]
        cik, date, ext = name.split('_')
        comp_header = {'CIK': cik,
                       'date': date,
                       'ACCESSION NUMBER': '',
                       'CONFORMED SUBMISSION TYPE': '',
                       'EFFECTIVENESS DATE': '',
                       'PUBLIC DOCUMENT COUNT': '',
                       'CONFORMED PERIOD OF REPORT': '',
                       'FILED AS OF DATE': '',
                       'COMPANY CONFORMED NAME': '',
                       'CENTRAL INDEX KEY': '',
                       'IRS NUMBER': '',
                       'FISCAL YEAR END': '',
                       'FORM TYPE': '',
                       'SEC FILE NUMBER': '',
                       'FILM NUMBER': '',
                       'STREET 1': '',
                       'STREET 2': '',
                       'CITY': '',
                       'STATE': '',
                       'ZIP': '',
                       'BUSINESS PHONE': '',
                       'Number of Other Included Managers': '',
                       'Form 13F Information Table Entry Total': '',
                       'Form 13F Information Table Value Total': '',
                       }
        header = parse_header(f, comp_header, dollar_match, entry_match, number_match)
        header['URL'] = 'ftp://ftp.sec.gov/edgar/data/' + header['ACCESSION NUMBER'] + '.txt'
        header['File'] = name
        headers_csv.writerow(header)
    headers.close()

if __name__ == "__main__":
    main()
