#!/usr/bin/env python3
# Written by Yves OESCH / HB9DTX
# Hosted on https://github.com/HB9DTX/EDI2ODX
import pandas as pd  # sudo apt-get install python3-pandas
import logging
import os
logging.basicConfig(level=logging.INFO)

#################################################################################################
# This dictionary sets the distance limits in km to select the interesting QSO's (per band)
# band identifier according to EDI format spec for PBand argument.
ODX = {'50 MHz': 1000,
       '144 MHz': 800,
       '432 MHz': 600,
       '1,3 GHz': 400,
       '2,3 GHz': 300}
#################################################################################################

# Unfortunately 432 or 435 MHz exist as band definition (Wintest versus N1MM!)
# OK1KKW and DARC definition of PBand differ...
# therefore entry is copied in the dictionary
ODX['435 MHz'] = ODX['432 MHz']

start = 'YYYYMMDD'       # Just in case those arguments would be empty in the EDI file
band = 'BAND'
call = 'CALLSIGN'


def read_edi_file(filename):
    # Read one EDI file and returns
    # qsos_list: dataframe containing all the QSO of the EDI file
    # contest_start: String describing the contest start date YYYYMMDD
    # call_sign: station callsign
    # band_edi: operating band, according to EDI specification
    # band_file_name: operating band, with space and comma replaced by underscore, for usage as file name

    with open(filename, 'r', encoding="utf-8", errors="ignore") as ediFile:
        # start by parsing the header ([REG1TEST;1] section of the file to extract start date, call and band
        # https://stackoverflow.com/questions/63596329/python-pandas-read-csv-with-commented-header-line
        for line in ediFile:
            if line.startswith('TDate='):
                logging.debug('contest start time found')
                contest_start = line[6:14]

            if line.startswith('PCall='):
                logging.debug('call found')
                logging.debug(line)
                call_sign = line[6:-1]
                logging.info('The station call sign is: %s', call_sign)

            if line.startswith('PBand='):
                logging.debug('Band found')
                logging.debug(line)
                traffic_band = line[6:-1]
                band_edi = traffic_band  # To be used for selecting the ODX distance in dictionary
                band_file_name = band.replace(' ', '')  # To be used in the filenames (no space, no comma)
                band_file_name = band_file_name.replace(',', '_')
                logging.info('The operating band is: %s', band_edi)

            if line.startswith('[QSORecords'):
                logging.debug('QSO log starts here')
                break
        # real log of QSO's starts here. The rest of the file is processed as a dataframe using pandas
        qsos_list = pd.read_csv(ediFile, delimiter=";", skiprows=1)
        qsos_list.columns = ['DATE', 'TIME', 'CALL', 'MODE', 'SENT_RST', 'SENT_NR',
                             'RECEIVED_RST', 'RECEIVED_NUMBER',
                             'EXCHANGE', 'LOCATOR', 'QRB',
                             'N_EXCH', 'N_LOCATOR', 'N_DXCC', 'DUPE']
        # Column names matching EDI file format specification

    ediFile.close()
    return qsos_list, contest_start, call_sign, band_edi, band_file_name


def select_odx_only(qsos, distance_limit):
    # returns a dataframe containing only the interesting QSO's of a given log file
    # i.e. the ones with distance exceeding a value given as parameter
    qsos_dx = qsos[qsos['QRB'] > distance_limit].copy()  # .copy needed to avoid SettingWithCopyWarning
    logging.debug(qsos_dx)

    qsos_dx.drop(columns=['MODE', 'SENT_RST', 'SENT_NR', 'RECEIVED_RST', 'RECEIVED_NUMBER',
                          'EXCHANGE', 'N_EXCH', 'N_LOCATOR', 'N_DXCC', 'DUPE'], inplace=True)
    # removes unusefull columns

    qsos_dx['DATE'] = pd.to_datetime(qsos_dx['DATE'], format='%y%m%d')
    qsos_dx['DATE'] = qsos_dx['DATE'].dt.strftime('%Y-%m-%d')
    # conversion to format expected by DUBUS

    qsos_dx['TIME'] = pd.to_datetime(qsos_dx['TIME'], format='%H%M')
    qsos_dx['TIME'] = qsos_dx['TIME'].dt.strftime('%H:%M')
    # conversion to format expected by DUBUS

    nr_qso_dx = qsos_dx.shape[0]
    logging.debug(nr_qso_dx)

    logging.info('%s QSOs with distance over %s km:', nr_qso_dx, distance_limit)
    logging.debug(qsos_dx)
    return qsos_dx


def generate_xlsx_csv_files(qsos_dx, contest_start, call_sign, traffic_band):
    # generate output files in xlsx and text files for the QSO's given as input
    # contest start date, callsign and band are used to create "unique" filenames
    output_file_name = contest_start + '_' + call_sign + '__' + traffic_band + '_DXs'
    # double underscore recommended for readability because one might appear in the band as decimal point (1_3GHz)

    csv_filename = output_file_name + '.txt'
    logging.debug(csv_filename)
    qsos_dx.to_csv(csv_filename, index=False, sep='\t')

    excel_file_name = output_file_name + '.xlsx'
    logging.debug(excel_file_name)
    qsos_dx.to_excel(excel_file_name, index=False)  # maybe requires installing XlsxWriter package?
    return


##############################################################################################
# Main program starts here
##############################################################################################
logging.info('Program START')
logging.info('Distance limits to select the QSOs, per band: %s', ODX)

file_list = []                                      # list all EDI files in the local folder
for file in os.listdir():                           # list only EDI files
    if file.endswith(".edi") or file.endswith(".EDI"):
        file_list.append(file)
logging.info('EDI files to process: %s', file_list)


for file in file_list:
    logging.info('Processing %s', file)
    [QSOs, start, call, bandEDI, bandFileName] = read_edi_file(file)    # read one EDI file
    logging.debug(QSOs)
    QSOs_DX = select_odx_only(QSOs, ODX[bandEDI])                       # select best DX's
    logging.debug(QSOs_DX)
    generate_xlsx_csv_files(QSOs_DX, start, call, bandFileName)         # generate output files

logging.info('Program END')
