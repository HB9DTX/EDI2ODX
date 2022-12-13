#!/usr/bin/env python3
# Written by Yves OESCH / HB9DTX / http://www.yvesoesch.ch
# Project hosted on https://github.com/HB9DTX/EDI2ODX
# Documentation in README.md
#
# 2022-12-09 de G1OGY: Add MGM mode.
# 2022-12-11 de G1OGY: add FM mode and translate mixed-mode codes into the SENT-mode (codes mandatory for IARU entry)
# 2022-12-09 de G1OGY: trap and translate CALL/P
# 2022-12-11 de G1OGY: amend QSO time derivation within `pandas` to provide midnight-crossing capability
# 2022-12-12 de G1OGY: amend provision for and advice to produce "Excel" DXlog output
# 2022-12-12 de G1OGY: Tucnak users - see line no. 132 of this file


import pandas as pd  # sudo apt-get install python3-pandas or `sudo pip install pandas` to reduce 500MB apt(8) download
import logging
import os

import maiden       # in local folder

# following imports are only needed for statistics and mapping
import numpy as np
import matplotlib.pyplot as plt
import math
import geotiler     # as `pip` package, usage: https://wrobell.dcmod.org/geotiler/usage.html

#################################################################################################
# This section contains settings as global variables that might be altered by the user if needed

SORTBYQRB = False               # If True: Sorts the ODX from longest QRB to smallest. False= chronological
                                # DUBUS recommendation: False
EXCELOUTPUT = False             # In case excel DXlog is needed, edit False to True
                                # REQUIRES, minimum, `pip install openpyxl` (290kB)
STATSMAP = True                 # if True compute the azimuth/elevation stats and plot a map with all contacted stations

MAP_BBOX = (-10.0, 40.0, 30.0, 58.0)  # Map limits; lower left, upper right, (long, lat) # central europe

# ODX dictionary sets the distance limits in km to select the interesting QSO's (per band)
# band identifier according to EDI format spec for PBand argument.
# it can be edited if the min QSO distance to report are to be changed
# it can be extended it other bands are of interest
ODX = {'50 MHz': 1000,
       '144 MHz': 800,
       '432 MHz': 600,
       '1,3 GHz': 400,
       '2,3 GHz': 300,
       '3,4 GHz': 200,
       '5,7 GHz': 150,
       '10 GHz': 100,
       '24 GHz': 50}
# WAVELENGTHS is used because the first line in the output txt file must contain the band not the QRG
WAVELENGTHS = {'50 MHz': '6 m',
               '144 MHz': '2 m',
               '432 MHz': '70 cm',
               '1,3 GHz': '23 cm',
               '2,3 GHz': '13 cm',
               '3,4 GHz': '9 cm',
               '5,7 GHz': '6 cm',
               '10 GHz': '3 cm',
               '24 GHz': '12 mm'}
#################################################################################################
# Unfortunately 432 or 435 MHz exist both as band definition (Wintest versus N1MM!)
# OK1KKW and DARC definition of PBand also differ...therefore the entries are copied in the dictionaries
# it might be necessary to do the same for other bands if needed (not tested yet ...)
#
# 2022-12-09 de G1OGY: IARU R1 designate band 2 Metres as 145 MHz and 70cm as 435 MHz (as above)
ODX['145 MHz'] = ODX['144 MHz']
WAVELENGTHS['145 MHz'] = WAVELENGTHS['144 MHz']
ODX['435 MHz'] = ODX['432 MHz']
WAVELENGTHS['435 MHz'] = WAVELENGTHS['432 MHz']

logging.basicConfig(level=logging.INFO)


class Contest:
    # Objects of this class contain all the information for a given contest log
    def __init__(self):
        self.start = None               # contest start time
        self.locator = None             # locator of the contest station
        self.call = None                # callsign of the contest station
        self.bandEDI = None             # contest operating band in EDI format
        self.bandFileName = None        # operating band without underscores
        self.outputFilePrefix = None    # common prefix of the output files
        self.qsoList = None             # contains the whole contest log with all columns
        self.qsoDx = None               # best DXs only, with limited columns for DUBUS report


def read_edi_file(filename, contest):
    # Read one EDI file and fills all the attributes of the contest object

    contest.start = 'YYYYMMDD'  # Just in case those arguments would be empty in the EDI file
    contest.call = 'CALLSIGN'
    contest.bandEDI = 'BAND'
    contest.bandFileName = 'BAND'
    contest.locator = 'LOCATOR'

    with open(filename, 'r', encoding="utf-8", errors="ignore") as ediFile:
        # start by parsing the header ([REG1TEST;1] section of the file to extract start date, call and band
        # https://stackoverflow.com/questions/63596329/python-pandas-read-csv-with-commented-header-line
        for line in ediFile:
            if line.startswith('TDate='):
                contest.start = line[6:14]
                logging.info('contest start time found: %s', contest.start)

            if line.startswith('PCall='):
                logging.debug('call found')
                logging.debug(line)
                contest.call = line[6:-1]
                portable = {47: 45}
                contest.call = contest.call.translate(portable)
                # Converts '/' into '-' to avoid messing-up the filename
                logging.info('The station call sign is: %s', contest.call)

            if line.startswith('PWWLo='):
                logging.debug('locator found')
                logging.debug(line)
                contest.locator = line[6:-1]
                logging.info('The station locator is: %s', contest.locator)

            if line.startswith('PBand='):
                logging.debug('Band found')
                logging.debug(line)
                traffic_band = line[6:-1]
                contest.bandEDI = traffic_band  # To be used for selecting the ODX distance in dictionary
                band_file_name = traffic_band.replace(' ', '')  # To be used in the filenames (no space, no comma)
                band_file_name = band_file_name.replace(',', '_')
                contest.bandFileName = band_file_name
                logging.info('The operating band is: %s', contest.bandEDI)

            if line.startswith('[QSORecords'):
                logging.debug('QSO log starts here')
                break
        # real log of QSO's starts here. The rest of the file is processed as a dataframe using pandas
        #OGY: Tucnak users should replace the following line with the commented \
        #     line below it so to ignore the last line IDENT in a Tucnak EDI file \
        #     (or manually delete the IDENT line before processing).
        qsos_list = pd.read_csv(ediFile, delimiter=";", skiprows=1)
        #qsos_list = pd.read_csv(ediFile, delimiter=";", skiprows=1, skipfooter=1, engine='python')
        qsos_list.columns = ['DATE', 'TIME', 'CALL', 'MODE', 'SENT_RST', 'SENT_NR',
                             'RECEIVED_RST', 'RECEIVED_NUMBER',
                             'EXCHANGE', 'LOCATOR', 'QRB',
                             'N_EXCH', 'N_LOCATOR', 'N_DXCC', 'DUPE']
        # Column names matching EDI file format specification

    contest.qsoList = qsos_list
    contest.outputFilePrefix = current_contest.start + '_' + current_contest.call + '_'\
        + current_contest.locator + '__' + current_contest.bandFileName
    # contest start date, callsign and band are used to create "unique" filenames
    ediFile.close()
    return contest


def select_odx_only(contest, distance_limit):
    # Fills the contest attribute .qsoDX containing only the interesting QSO's of a given log file
    # i.e. the ones with distance exceeding a value given as parameter
    # keeps only the columns of interest for the DUBUS report, removes the others

    qsos_dx = contest.qsoList[contest.qsoList['QRB'] >= distance_limit].copy()
    # .copy needed to avoid SettingWithCopyWarning
    logging.debug(qsos_dx)

    # removes unuseful columns, keeps DATE, TIME, CALL, MODE, LOCATOR and QRB only
    qsos_dx.drop(columns=['SENT_NR', 'SENT_RST', 'RECEIVED_RST', 'RECEIVED_NUMBER',
                          'EXCHANGE', 'N_EXCH', 'N_LOCATOR', 'N_DXCC', 'DUPE'], inplace=True)

    qsos_dx['DATE'] = pd.to_datetime(qsos_dx['DATE'], format='%y%m%d')
    qsos_dx['DATE'] = qsos_dx['DATE'].dt.strftime('%Y-%m-%d')
    # DATE conversion to format expected by DUBUS

    #qsos_dx['TIME'] = pd.to_datetime(qsos_dx['TIME'], format='%H%M')   #Buggous with QSO right after midnight
    qsos_dx['TIME'] = pd.to_datetime(qsos_dx['TIME'], infer_datetime_format=True)
    qsos_dx['TIME'] = qsos_dx['TIME'].dt.strftime('%H:%M')
    # TIME conversion to format expected by DUBUS

    qsos_dx['QRB'] = qsos_dx['QRB'].astype(str) + ' km'
    # add the km unit to match DUBUS publication

    qsos_dx['MOD'] = ['m' if x == 7 else 'f' if x == 6 else 'c' if x == 2 else 'c' if x == 4 else 's' if x == 1 else 's' if x == 3 else '' for x in qsos_dx['MODE']]
    logging.debug(qsos_dx['MOD'])
    qsos_dx.drop(columns=['MODE'], inplace=True)
    # Replace the MODE column which contains integers by a new column MOD
    # which contains a single letter indicating FM, MGM, CW or SSB (sent mode)

    if SORTBYQRB:
        qsos_dx.sort_values(by=['QRB', 'DATE', 'TIME'], ascending=[False, True, True], inplace=True)
        # Optional sorting by descending QSO distances
        # Date and time sorting as 2nd/3rd priority, otherwise log order would be random for QSO with same QRB

    nr_qso_dx = qsos_dx.shape[0]
    logging.info('%s QSOs with distance over %s km:', nr_qso_dx, distance_limit)
    logging.debug(qsos_dx)
    contest.qsoDx = qsos_dx
    return contest


def generate_xlsx_csv_files(contest):
    # generate output files in text files for the best DX QSO's of the contest provided as argument
    csv_filename = contest.outputFilePrefix + '_DXs.txt'
    outfile = open(csv_filename, 'w')
    outfile.write(contest.call + ' (' + contest.locator + ') wkd ' + WAVELENGTHS[contest.bandEDI] + ':\n')
    outfile.write('DATE\tTIME\tCALL\tLOCATOR\tQRB/MOD\n')   # no time between QSB and MOD ==> manual header write
    outfile.close()
    logging.debug(csv_filename)
    contest.qsoDx.to_csv(csv_filename, index=False, header=False, sep='\t', mode='a')

    if EXCELOUTPUT:
        excel_file_name = contest.outputFilePrefix + '_DXs.xlsx'
        logging.debug(excel_file_name)
        contest.qsoDx.to_excel(excel_file_name, index=False)
    return


def compute_dist_az(contest):
    # Computes distance and azimuth from contest station to all stations in the log.
    # Creates additional columns in contest.qsoList dataframe
    mhl = maiden.Maiden()
    mylatlong = mhl.maiden2latlon(contest.locator)
    distances = np.zeros(contest.qsoList.shape[0])
    azimuths = np.zeros(contest.qsoList.shape[0])
    latitudes = np.zeros(contest.qsoList.shape[0])
    longitudes = np.zeros(contest.qsoList.shape[0])
    for index, contents in contest.qsoList.iterrows():
        # OGY: logging.debug(index, contents['LOCATOR'])      # This log directive causes '--- Logging error ---' print
        stationlatlong = mhl.maiden2latlon(contents['LOCATOR'])
        if stationlatlong[0] is not None:  # avoids error if locator is not valid
            (distances[index], azimuths[index]) = mhl.dist_az(mylatlong, stationlatlong)
            latitudes[index] = stationlatlong[0]
            longitudes[index] = stationlatlong[1]
        else:  # fake / fill-in data
            logging.debug(type(stationlatlong[0]))
            (distances[index], azimuths[index]) = (0, 0)
            latitudes[index] = mylatlong[0]
            longitudes[index] = mylatlong[1]
    contest.qsoList['DISTANCE2'] = distances
    contest.qsoList['AZIMUTH'] = azimuths
    contest.qsoList['LATITUDE'] = latitudes
    contest.qsoList['LONGITUDE'] = longitudes
    logging.debug(contest.qsoList[['CALL', 'AZIMUTH', 'QRB', 'DISTANCE2']])
    return contest


def plotstations(contest):
    # Plot contest statistics:
    # - histogram of azimuths
    # - histogram of distances to other stations
    # - map al all contest stations in log

    # Azimuths probability density plot
    fig1, ax1 = plt.subplots()
    ax1.set_title('Azimuth density probability computed from ' + contest.locator +
                  '\nContest ' + contest.start + '; Call ' + contest.call + '; Band ' + contest.bandEDI)
    ax1.hist(contest.qsoList['AZIMUTH'], bins=int(math.sqrt(contest.qsoList.shape[0])))
    ax1.set_xlabel('Azimuth')
    ax1.set_ylabel('Number of QSO')
    ax1.set_xlim([0, 360])
    annotation = 'Total number of QSO in log: ' + str(contest.qsoList.shape[0])
    ax1.text(0.5, 0.95, annotation, transform=ax1.transAxes, ha='center', va='top',
             bbox=dict(boxstyle='square', facecolor='None'))
    annotation = 'Plot: EDI2ODX by HB9DTX'
    ax1.text(0.05, 0.0, annotation, transform=fig1.transFigure, fontsize='xx-small', color='black', ha='left',
             va='bottom')  # transform=ax1.transAxes, =fig1.transFigure
    plt.savefig(contest.outputFilePrefix + '_Azimuth' + '.png')
    # plt.show()
    plt.close()

    # Histogram of Points (Distances)
    fig2, ax2 = plt.subplots()
    ax2.set_title('Distances density probability computed from ' + contest.locator +
                  '\nContest ' + contest.start + '; Call ' + contest.call + '; Band ' + contest.bandEDI)
    ax2.hist(contest.qsoList['AZIMUTH'], bins=int(math.sqrt(contest.qsoList.shape[0])),
             weights=contest.qsoList['DISTANCE2'])
    ax2.set_xlabel('Azimuth')
    ax2.set_ylabel('Number of points (km)')
    ax2.set_xlim([0, 360])
    annotation = 'Total number of QSO in log: ' + str(contest.qsoList.shape[0]) + '\nTotal km: '\
                 + str(round(contest.qsoList['QRB'].sum()))
    ax2.text(0.5, 0.95, annotation, transform=ax2.transAxes, ha='center', va='top',
             bbox=dict(boxstyle='square', facecolor='None'))
    annotation = 'Plot: EDI2ODX by HB9DTX'
    ax2.text(0.05, 0, annotation, fontsize='xx-small', color='black', transform=fig1.transFigure, ha='left',
             va='bottom')
    plt.savefig(contest.outputFilePrefix + '_Points' + '.png')
    # plt.show()
    plt.close()

    # Geographical map of stations
    mm = geotiler.Map(extent=MAP_BBOX, zoom=5)
    img = geotiler.render_map(mm)

    points = list(zip(contest.qsoList['LONGITUDE'], contest.qsoList['LATITUDE']))
    x, y = zip(*(mm.rev_geocode(p) for p in points))

    mhl = maiden.Maiden()
    mylatlong = mhl.maiden2latlon(contest.locator)
    mylatlong = (mylatlong[1], mylatlong[0])
    mx, my = mm.rev_geocode(mylatlong)

    fig3, ax3 = plt.subplots(tight_layout=True)
    ax3.imshow(img)
    ax3.scatter(x, y, c='purple', edgecolor='none', s=10, alpha=0.9, label='all stations')
    ax3.scatter(mx, my, c='red', edgecolor='none', s=50, alpha=0.9, label='My station')
    ax3.set_title('Stations positions for contest ' + contest.start +
                  '\nCall ' + contest.call + '; Band ' + contest.bandEDI)
    plt.axis('off')
    annotation = 'Total number of stations in log: ' + str(contest.qsoList.shape[0])
    ax3.text(1, 0, annotation, transform=ax3.transAxes, ha='right', va='bottom',
             bbox=dict(boxstyle='square', facecolor='white'))
    annotation = 'Plot: EDI2ODX by HB9DTX\nMap data: OpenStreetMap.'
    ax3.text(0, 0, annotation, fontsize='xx-small', color='blue', transform=ax3.transAxes, ha='left', va='bottom')
    # bbox=dict(boxstyle='square', facecolor='white'))
    plt.savefig(contest.outputFilePrefix + '_Map' + '.png', bbox_inches='tight')
    # plt.show()
    plt.close()


##############################################################################################
# Main program starts here
##############################################################################################
logging.info('Program START')
logging.info('Distance limits to select the QSOs, per band: %s', ODX)

file_list = []                                      # list all EDI files in the local folder
for file in os.listdir():
    if file.endswith(".edi") or file.endswith(".EDI"):  # list only EDI files
        file_list.append(file)
logging.info('EDI files to process: %s', file_list)

for file in file_list:
    logging.info('-' * 80)
    logging.info('Processing %s', file)
    current_contest = Contest()
    read_edi_file(file, current_contest)                                # read one EDI file
    logging.debug(current_contest)
    logging.debug(current_contest.start)
    logging.debug(current_contest.locator)
    logging.debug(current_contest.qsoList)

    select_odx_only(current_contest, ODX[current_contest.bandEDI])      # select best DX's
    logging.debug(current_contest.qsoDx)

    generate_xlsx_csv_files(current_contest)                            # generate the txt (and optional xls)

    if STATSMAP:                                                        # generates contest statistics and map
        compute_dist_az(current_contest)
        plotstations(current_contest)
    del current_contest                 # deletes current_contest object after processing

logging.info('Program END')
