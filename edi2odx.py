import pandas as pd  # sudo apt-get install python3-pandas
import logging


# This dictionary sets the distance limits in km to select the interesting QSO's (per band)
# band identifier according to EDI format spec for PBand argument.
ODX = {'144 MHz': 700, '432 MHz': 500, '1,3 GHz': 300}

# Unfortunately 432 or 435 MHz exist as band definition (Wintest versus N1MM!)
# OK1KKW and DARC definition of PBAND differ...
# therefore entry is copied in the dictionary
ODX['435 MHz'] = ODX['432 MHz']


def read_edi_file(filename):
    # with open('HB9XC_432.edi', 'r') as ediFile:
    with open(filename, 'r', encoding="utf-8", errors="ignore") as ediFile:
        # https://stackoverflow.com/questions/63596329/python-pandas-read-csv-with-commented-header-line
        for line in ediFile:
            if line.startswith('PCall='):
                logging.debug('call found')
                logging.debug(line)
                call_sign = line[6:-1]
                logging.info('The station call sign is: %s', call_sign)

            if line.startswith('PBand='):
                logging.debug('Band found')
                logging.debug(line)
                band = line[6:-1]
                band_edi = band  # To be used for selecting the ODX distance in dictionary
                band_file_name = band.replace(' ', '')  # To be used in the filenames (no space, no comma)
                band_file_name = band_file_name.replace(',', '_')
                logging.info('The operating band is: %s', band_edi)

            else:
                if line.startswith('[QSORecords'):
                    logging.debug('QSO log starts here')
                    break
        qsos_list = pd.read_csv(ediFile, delimiter=";", skiprows=1)
        qsos_list.columns = ['DATE', 'TIME', 'CALL', 'MODE', 'SENT_RST', 'SENT_NR',
                             'RECEIVED_RST', 'RECEIVED_NUMBER',
                             'EXCHANGE', 'LOCATOR', 'QRB',
                             'N_EXCH', 'N_LOCATOR', 'N_DXCC', 'DUPE']
        # Column names matching EDI file format specification

    ediFile.close()
    return qsos_list, call_sign, band_edi, band_file_name


def select_odx_only(qsos, distance_limit):
    qsos_dx = qsos[qsos['QRB'] > distance_limit].copy()  # .copy needed to avoid SettingWithCopyWarning
    logging.debug(qsos_dx)

    qsos_dx.drop(columns=['MODE', 'SENT_RST', 'SENT_NR', 'RECEIVED_RST', 'RECEIVED_NUMBER',
                          'EXCHANGE', 'N_EXCH', 'N_LOCATOR', 'N_DXCC', 'DUPE'], inplace=True)

    qsos_dx['DATE'] = pd.to_datetime(qsos_dx['DATE'], format='%y%m%d')
    qsos_dx['DATE'] = qsos_dx['DATE'].dt.strftime('%Y-%m-%d')

    qsos_dx['TIME'] = pd.to_datetime(qsos_dx['TIME'], format='%H%M')
    qsos_dx['TIME'] = qsos_dx['TIME'].dt.strftime('%H:%M')

    nr_qso_dx = qsos_dx.shape[0]
    logging.debug(nr_qso_dx)

    logging.info('%s QSOs with distance over %s km:', nr_qso_dx, distance_limit)
    logging.info(qsos_dx)
    return qsos_dx


def generate_xlsx_csv_files(qsos_dx, call_sign, band):
    output_file_name = call_sign + '__' + band

    csv_filename = output_file_name + '.txt'
    logging.debug(csv_filename)
    qsos_dx.to_csv(csv_filename, index=False, sep='\t')

    excel_file_name = output_file_name + '.xlsx'
    logging.debug(excel_file_name)
    qsos_dx.to_excel(excel_file_name, index=False)  # maybe requires installing XlsxWriter package?
    return


logging.basicConfig(level=logging.DEBUG)
logging.info('Program START')
logging.info('Distance limits to select the QSOs, per band: %s', ODX)

# [QSOs, call, bandEDI, bandFileName] = read_edi_file('HB9XC_1240.edi')

[QSOs, call, bandEDI, bandFileName] = read_edi_file('HELVETIA-2022_UHF@HB9N.435_MHz.EDI')

logging.debug(QSOs)
QSOs_DX = select_odx_only(QSOs, ODX[bandEDI])
logging.debug(QSOs_DX)
generate_xlsx_csv_files(QSOs_DX, call, bandFileName)

logging.info('Program END')
# logging.debug(QSOs['CALL'])
