import pandas as pd  # sudo apt-get install python3-pandas
import logging
import datetime

ODX = 400

logging.basicConfig(level=logging.INFO)


#with open('HB9XC_432.edi', 'r') as ediFile:
with open('HB9XC_1240.edi', 'r') as ediFile:
#https://stackoverflow.com/questions/63596329/python-pandas-read-csv-with-commented-header-line
    for line in ediFile:
        if line.startswith('PCall='):
            logging.debug('call found')
            logging.debug(line)
            call = line[6:-1]
            logging.info('The station call is: %s', call)

        if line.startswith('PBand='):
            logging.debug('Band found')
            logging.debug(line)
            band = line[6:-1]
            band = band.replace(' ','')    # Band cleanup to allow using the string in a filename
            band = band.replace(',','_')
            logging.info('The operating band is: %s', band)

        else:
            if line.startswith('[QSORecords'):
                logging.debug('QSO log starts here')
                logging.debug(line)
                break
    QSOs = pd.read_csv(ediFile, delimiter=";", skiprows=1)
    QSOs.columns = ['DATE', 'TIME', 'CALL', 'MODE', 'SENT_RST', 'SENT_NR', \
                    'RECEIVED_RST', 'RECEIVED_NUMBER', \
                    'EXCHANGE', 'LOCATOR', 'QRB', \
                    'N_EXCH', 'N_LOCATOR', 'N_DXCC', 'DUPE']
    #EDI file format

ediFile.close()

logging.debug(QSOs)
#logging.debug(QSOs['CALL'])

QSOs_DX = QSOs[QSOs['QRB'] > ODX].copy()        #.copy needed to avoid SettingWithCopyWarning

logging.debug(QSOs_DX)

QSOs_DX.drop(columns=['MODE', 'SENT_RST', 'SENT_NR', 'RECEIVED_RST', 'RECEIVED_NUMBER', \
                    'EXCHANGE', 'N_EXCH', 'N_LOCATOR', 'N_DXCC', 'DUPE'], inplace=True)


#QSO_DX['newDate'] = pd.to_datetime(QSO_DX.checkin).dt.strftime("%m/%d/%Y")

QSOs_DX['DATE'] = pd.to_datetime(QSOs_DX['DATE'], format='%y%m%d')
QSOs_DX['DATE'] =  QSOs_DX['DATE'].dt.strftime('%Y-%m-%d')

QSOs_DX['TIME'] = pd.to_datetime(QSOs_DX['TIME'], format='%H%M')
QSOs_DX['TIME'] =  QSOs_DX['TIME'].dt.strftime('%H:%M')

#QSOs_DX['DATE'] = '20' + QSOs_DX['DATE'].astype('string')
#QSOs_DX['DATE'] = QSOs_DX['DATE'].apply(lambda x: x.strftime('%Y-%m-%d'))
#QSOs_DX['DATE'] = QSOs_DX['DATE']

#QSOs_DX['DATE'] = QSOs_DX['DATE'].to_datetime(QSOs_DX['DATE'], format='%Y%m%d')

logging.info('QSOs with distance over %s km:', ODX)
logging.info(QSOs_DX)




OutputFileName = call + '__' + band

csvOutputFilename = OutputFileName +'.txt'
logging.debug(csvOutputFilename)
QSOs_DX.to_csv(csvOutputFilename, index=False, sep='\t')



excelOutputFileName = OutputFileName + '.xlsx'
logging.debug(excelOutputFileName)
QSOs_DX.to_excel(excelOutputFileName, index = False)      #requires intalling XlsxWriter package?
