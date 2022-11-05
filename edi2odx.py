#!/usr/bin/env python3
# Written by Yves OESCH / HB9DTX / http://www.yvesoesch.ch
# Project hosted on https://github.com/HB9DTX/EDI2ODX
# Documentation in README.md

import pandas as pd  # sudo apt-get install python3-pandas
import logging
import os

import maiden       # in local folder

# following imports are only needed for statistics and mapping
import numpy as np
import matplotlib.pyplot as plt
import math
import geotiler     # as package, usage: https://wrobell.dcmod.org/geotiler/usage.html


#################################################################################################
# This section contains setting that might be altered by the user if needed

SORTBYQRB = False               # If True: Sorts the ODX from longest QRB to smallest. False= chronological
                                #DUBUS recommendation: False

STATSMAP = True                 # if True compute the azimuth/elevation stats and plot a map with all contacted stations

MAP_BBOX = (-10.0, 40.0, 30.0, 58.0)  # Map limits; lower left, upper right, (long, lat) #central europe

# ODX dictionary sets the distance limits in km to select the interesting QSO's (per band)
# band identifier according to EDI format spec for PBand argument.
# it can be edited if the min QSO distance to report are to be changed
# it can be extended it other bands are of interest
ODX = {'50 MHz': 1000,
       '144 MHz': 800,
       '432 MHz': 600,
       '1,3 GHz': 400,
       '2,3 GHz': 300}

# WAVELENGTHS is used because the first line in the output txt file must contain the band not the QRG
WAVELENGTHS = {'50 MHz': '6 m',
               '144 MHz': '2 m',
               '432 MHz': '70 cm',
               '1,3 GHz': '23 cm',
               '2,3 GHz': '13 cm'}
#################################################################################################
# Unfortunately 432 or 435 MHz exist both as band definition (Wintest versus N1MM!)
# OK1KKW and DARC definition of PBand also differ...therefore the entries are copied in the dictionaries
# it might be necessary to do the same for other bands if needed (not tested yet ...)
ODX['435 MHz'] = ODX['432 MHz']
WAVELENGTHS['435 MHz'] = WAVELENGTHS['432 MHz']

logging.basicConfig(level=logging.INFO)


def read_edi_file(filename):
    # Read one EDI file and returns:
    # qsos_list: dataframe containing all the QSO of the EDI file
    # contest_start: String describing the contest start date YYYYMMDD
    # call_sign: station callsign
    # band_edi: operating band, according to EDI specification
    # band_file_name: operating band, with space and comma replaced by underscore, for usage as file name
    contest_start = 'YYYYMMDD'  # Just in case those arguments would be empty in the EDI file
    call_sign = 'CALLSIGN'
    band_edi = 'BAND'
    band_file_name = 'BAND'
    wwlocator = 'LOCATOR'

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

            if line.startswith('PWWLo='):
                logging.debug('locator found')
                logging.debug(line)
                wwlocator = line[6:-1]
                logging.info('The station locator is: %s', wwlocator)

            if line.startswith('PBand='):
                logging.debug('Band found')
                logging.debug(line)
                traffic_band = line[6:-1]
                band_edi = traffic_band  # To be used for selecting the ODX distance in dictionary
                band_file_name = traffic_band.replace(' ', '')  # To be used in the filenames (no space, no comma)
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
    return qsos_list, contest_start, call_sign, wwlocator, band_edi, band_file_name


def select_odx_only(qsos, distance_limit):
    # returns a dataframe containing only the interesting QSO's of a given log file
    # i.e. the ones with distance exceeding a value given as parameter
    # filters out the columns of interest for the DUBUS report, removes the others
    qsos_dx = qsos[qsos['QRB'] >= distance_limit].copy()  # .copy needed to avoid SettingWithCopyWarning
    logging.debug(qsos_dx)

    # removes unusefull columns, keeps DATE, TIME, CALL, MODE, LOCATOR and QRB only
    qsos_dx.drop(columns=['SENT_NR', 'SENT_RST', 'RECEIVED_RST', 'RECEIVED_NUMBER',
                          'EXCHANGE', 'N_EXCH', 'N_LOCATOR', 'N_DXCC', 'DUPE'], inplace=True)

    qsos_dx['DATE'] = pd.to_datetime(qsos_dx['DATE'], format='%y%m%d')
    qsos_dx['DATE'] = qsos_dx['DATE'].dt.strftime('%Y-%m-%d')
    # DATE conversion to format expected by DUBUS

    qsos_dx['TIME'] = pd.to_datetime(qsos_dx['TIME'], format='%H%M')
    qsos_dx['TIME'] = qsos_dx['TIME'].dt.strftime('%H:%M')
    # TIME conversion to format expected by DUBUS

    qsos_dx['QRB'] = qsos_dx['QRB'].astype(str) + ' km'
    # to match DUBUS publication

    qsos_dx['MOD'] = ['c' if x == 2 else 's' if x == 1 else '' for x in qsos_dx['MODE']]
    logging.debug(qsos_dx['MOD'])
    qsos_dx.drop(columns=['MODE'], inplace=True)

    if SORTBYQRB:
        qsos_dx.sort_values(by=['QRB', 'DATE', 'TIME'], ascending=[False, True, True], inplace=True)
        # Date and time sorting as 2nd/3rd priority, otherwise log order is random for QSO with same QRB

    nr_qso_dx = qsos_dx.shape[0]
    logging.debug(nr_qso_dx)
    logging.info('%s QSOs with distance over %s km:', nr_qso_dx, distance_limit)
    logging.debug(qsos_dx)
    return qsos_dx


def generate_xlsx_csv_files(qsos_dx, out_file_suffix):
    # generate output files in xlsx and text files for the QSO's given as input
    # contest start date, callsign and band are used to create "unique" filenames
    out_file_suffix = out_file_suffix + '_DXs'
    # double underscore recommended for readability because one might appear in the band as decimal point (1_3GHz)
    # if INCLUDEMODECOLUMN:
    #   out_file_suffix = out_file_suffix + '_with_mode'

    csv_filename = out_file_suffix + '.txt'
    outfile = open(csv_filename, 'w')
    outfile.write(call + ' (' + locator + ') wkd ' + WAVELENGTHS[bandEDI] + ':\n')
    outfile.write('DATE\tTIME\tCALL\tLOCATOR\tQRB/MOD\n')   # no time between QSB and MOD ==> manual header write
    outfile.close()
    logging.debug(csv_filename)
    qsos_dx.to_csv(csv_filename, index=False, header=False, sep='\t', mode='a')

    # In case excel log is needed, uncomment the lines below
    # excel_file_name = out_file_suffix + '.xlsx'
    # logging.debug(excel_file_name)
    # qsos_dx.to_excel(excel_file_name, index=False)  # maybe requires installing XlsxWriter package?
    return


def compute_dist_az(df, mylocator):
    mhl = maiden.Maiden()
    mylatlong = mhl.maiden2latlon(mylocator)
    distances = np.zeros(df.shape[0])
    azimuths = np.zeros(df.shape[0])
    latitudes = np.zeros(df.shape[0])
    longitudes = np.zeros(df.shape[0])
    for index, contents in df.iterrows():
        logging.debug(index, contents['LOCATOR'])
        stationlatlong = mhl.maiden2latlon(contents['LOCATOR'])
        if stationlatlong[0] is not None:  # a voids error if locator is not valid
            (distances[index], azimuths[index]) = mhl.dist_az(mylatlong, stationlatlong)
            latitudes[index] = stationlatlong[0]
            longitudes[index] = stationlatlong[1]
        else:  # fake / fill-in data
            logging.debug(type(stationlatlong[0]))
            (distances[index], azimuths[index]) = (0, 0)
            latitudes[index] = mylatlong[0]
            longitudes[index] = mylatlong[1]
    df['DISTANCE2'] = distances
    df['AZIMUTH'] = azimuths
    df['LATITUDE'] = latitudes
    df['LONGITUDE'] = longitudes
    logging.debug(df[['CALL', 'AZIMUTH', 'QRB', 'DISTANCE2']])
    # print(type(df['Pts'][1]))
    # print(type(df['Distance2'][1]))
    return df


def plotstations(df, contest_start, mylocator, band, out_file_suffix):
    # Histogram of azimuths
    fig1, ax1 = plt.subplots()
    ax1.set_title('Azimuth density probability computed from ' + mylocator +
                  '\nContest ' + contest_start + '; Call ' + call + '; Band ' + band)
    ax1.hist(df['AZIMUTH'], bins=int(math.sqrt(df.shape[0])))
    ax1.set_xlabel('Azimuth')
    ax1.set_ylabel('Number of QSO')
    ax1.set_xlim([0, 360])

    annotation = 'Total number of QSO in log: ' + str(df.shape[0])
    ax1.text(0.5, 0.95, annotation, transform=ax1.transAxes, ha='center', va='top',
             bbox=dict(boxstyle='square', facecolor='None'))
    annotation = 'Plot: EDI2ODX by HB9DTX'
    ax1.text(0.05, 0.0, annotation, transform=fig1.transFigure, fontsize='xx-small', color='black', ha='left',
             va='bottom')  # transform=ax1.transAxes, =fig1.transFigure
    plt.savefig(out_file_suffix + '_Azimuth' + '.png')
    # plt.show()
    plt.close()

    # Histogram of Points (Distances)
    fig2, ax2 = plt.subplots()
    ax2.set_title('Distances density probability computed from ' + mylocator +
                  '\nContest ' + contest_start + '; Call ' + call + '; Band ' + band)
    ax2.hist(df['AZIMUTH'], bins=int(math.sqrt(df.shape[0])), weights=df['DISTANCE2'])
    ax2.set_xlabel('Azimuth')
    ax2.set_ylabel('Number of points (km)')
    ax2.set_xlim([0, 360])
    annotation = 'Total number of QSO in log: ' + str(df.shape[0]) + '\nTotal km: '+str(round(df['QRB'].sum()))
    ax2.text(0.5, 0.95, annotation, transform=ax2.transAxes, ha='center', va='top',
             bbox=dict(boxstyle='square', facecolor='None'))

    annotation = 'Plot: EDI2ODX by HB9DTX'
    ax2.text(0.05, 0, annotation, fontsize='xx-small', color='black', transform=fig1.transFigure, ha='left',
             va='bottom')
    plt.savefig(out_file_suffix + '_Points' + '.png')
    # plt.show()
    plt.close()

    # Geographical map of stations
    mm = geotiler.Map(extent=MAP_BBOX, zoom=5)
    img = geotiler.render_map(mm)

    points = list(zip(df['LONGITUDE'], df['LATITUDE']))
    x, y = zip(*(mm.rev_geocode(p) for p in points))

    mhl = maiden.Maiden()
    mylatlong = mhl.maiden2latlon(mylocator)
    mylatlong = (mylatlong[1], mylatlong[0])
    mx, my = mm.rev_geocode(mylatlong)

    fig3, ax3 = plt.subplots(tight_layout=True)
    ax3.imshow(img)
    ax3.scatter(x, y, c='purple', edgecolor='none', s=10, alpha=0.9, label='all stations')
    ax3.scatter(mx, my, c='red', edgecolor='none', s=50, alpha=0.9, label='My station')
    ax3.set_title('Stations positions for contest ' + contest_start +
                  '\nCall ' + call + '; Band ' + band)
    plt.axis('off')

    annotation = 'Total number of stations in log: ' + str(df.shape[0])
    ax3.text(1, 0, annotation, transform=ax3.transAxes, ha='right', va='bottom',
             bbox=dict(boxstyle='square', facecolor='white'))

    annotation = 'Plot: EDI2ODX by HB9DTX\nMap data: OpenStreetMap.'
    ax3.text(0, 0, annotation, fontsize='xx-small', color='blue', transform=ax3.transAxes, ha='left', va='bottom')
    # bbox=dict(boxstyle='square', facecolor='white'))
    plt.savefig(out_file_suffix + '_Map' + '.png', bbox_inches='tight')
    # plt.show()
    plt.close()


##############################################################################################
# Main program starts here
##############################################################################################
logging.info('Program START')
logging.info('Distance limits to select the QSOs, per band: %s', ODX)
# logging.info('MOD column added: %s', INCLUDEMODECOLUMN)

file_list = []                                      # list all EDI files in the local folder
for file in os.listdir():
    if file.endswith(".edi") or file.endswith(".EDI"):  # list only EDI files
        file_list.append(file)
logging.info('EDI files to process: %s', file_list)


for file in file_list:
    logging.info('Processing %s', file)
    [QSOs, start, call, locator, bandEDI, bandFileName] = read_edi_file(file)    # read one EDI file
    output_file_name_prefix = start + '_' + call + '_' + locator + '__' + bandFileName
    logging.debug(QSOs)
    QSOs_DX = select_odx_only(QSOs, ODX[bandEDI])                       # select best DX's
    logging.debug(QSOs_DX)
    generate_xlsx_csv_files(QSOs_DX, output_file_name_prefix)         # generate output files
    if STATSMAP:
        QSOs = compute_dist_az(QSOs, locator)
        plotstations(QSOs, start, locator, bandEDI, output_file_name_prefix)

logging.info('Program END')
