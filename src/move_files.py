#!/usr/bin/env python
import os
import shutil
import csv
import platform

################################
# Make csv of downloaded files #
################################

if 'Linux' in platform.system():
    prefix = '/home/chad/Code/Repos/Python/13fpy'
    rawpath = '/home/chad/Documents/13F'
    old = 'rawdata'
    replace = 'rawdata_banks'
else:
    prefix = r"C:/Users/czh156/Repos/Python/13FPy/"
    rawpath = r"\\smeal.psu.edu\data\Users\Grads\czh156\Desktop\13F"
    old = r"\\smeal.psu.edu\data\Users\Grads\czh156\Desktop\13F\rawdata"
    replace = r"C:/Users/czh156/Desktop/rawdata_banks"

# Get list of bank CIKs from Michelle's co-author

bank_list = open(os.path.join(prefix, 'Data', 'ad50_R_22May2013b.csv'), 'r')
banks = csv.DictReader(bank_list)
ciks = []
for b in banks:
    if b['ReportedCIK'] not in ciks:
        ciks.append(b['ReportedCIK'])
    if b['WRDS_CIK'] not in ciks:
        ciks.append(b['WRDS_CIK'])
    if b['CIK_May16'] not in ciks:
        ciks.append(b['CIK_May16'])

banks = [c.lstrip('0') for c in ciks]
bank_list.close()

#Make a new file to store information about downloaded files for banks
download_banks = open(os.path.join(prefix, 'Data', 'downloaded_banks.csv'), "w", newline='')
csv_banks = csv.writer(download_banks)
csv_banks.writerow(['CIK', 'Year', 'Qtr', 'Path', 'Size', 'Filename'])

#Make a new file to store information about downloaded files for all funds
download_all = open(os.path.join(prefix, 'Data', 'downloaded_all.csv'), "w", newline='')
csv_all = csv.writer(download_all)
csv_all.writerow(['CIK', 'Year', 'Qtr', 'Path', 'Size', 'Filename'])

#Walk the directory, skip anything that isn't a text file
for root, dirs, files in os.walk(os.path.join(rawpath, 'rawdata')):
    for f in files:
        if not f.endswith('.txt'):
            continue

        cik = f.split('_')[0]
        location = os.path.dirname(os.path.join(root, f))
        fullname = os.path.abspath(os.path.join(root, f))
        size = os.path.getsize(fullname)
        _, year, qtr = location.split('\\')[-1].split('_')

        #Only write to bank file if it's in the list of banks
        if cik in banks:
            csv_banks.writerow([cik, year, qtr, location, size, f])

        #Always write to all file, even if it's also in bank file
        csv_all.writerow([cik, year, qtr, location, size, f])

        #Write the file on every iteration
        download_banks.flush()
        download_all.flush()
        os.fsync(download_banks.fileno())
        os.fsync(download_all.fileno())

download_banks.close()
download_all.close()


#Move downloaded files from 'rawdata' to 'bank only' files
file_list = open(os.path.join(prefix, 'Data', 'downloaded_banks.csv'), 'r')
files = csv.DictReader(file_list)

for f in files:
    newdir = f['Path'].replace(old, replace, 1)

    if not os.path.exists(newdir):
        os.mkdir(newdir)
    if not os.path.exists(os.path.join(newdir, f['Filename'])):
        oldfile = os.path.join(f['Path'], f['Filename'])
        newfile = os.path.join(newdir, f['Filename'])
        shutil.copy2(oldfile, newdir, follow_symlinks=False)
    else:
        print(f['Filename'])
