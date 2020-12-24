#!/usr/binenv python3
"""
Get ADIF data files from LoTW.

Functionality factored out of the adif-log-analyzer,
it is not appropriate for that application to fetch data,
only to analyze it.
"""

__author__ = 'Jeffrey B. Otterson, N1KDO'
__copyright__ = 'Copyright 2020 Jeffrey B. Otterson'
__license__ = 'Simplified BSD'
__version__ = '0.01'

import adif
import getpass
import logging
import os.path
import time

logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)
logging.Formatter.converter = time.gmtime


def get_file_date_size(filename):
    if os.path.exists(filename):
        file_timestamp = os.path.getmtime(filename)
        file_size = os.path.getsize(filename)
        return file_timestamp, file_size
    else:
        return None, None


def show_file_info(filename):
    file_timestamp, file_size = get_file_date_size(filename)
    if filename is None:
        print('{} does not exist.'.format(filename))
    else:
        print('{} created {}, {} bytes'.format(filename, time.ctime(file_timestamp), file_size))


def menu():
    valid_choices = '012345'
    while True:
        print('1. Download complete LoTW ADIF')
        print('2. Download updates to existing LoTW ADIF')
        print('3. Download DXCC QSL cards ADIF')
        print('4. Save current LoTW ADIF')
        print('5. Merge LoTW and DXCC QSLs into combined ADIF')
        print('0. Exit this program')
        print()
        choice = input('Your Choice? ')
        if len(choice) == 1 and choice in valid_choices:
            return choice
        print('bad choice.')


def get_password(password):
    if password is not None and len(password) >=6:
        return password
    while True:
        password = getpass.getpass()
        if password is not None and len(password) > 0:
            return password


def main():
    #callsign = 'n1kdo'
    callsign = ''
    password = None
    working_dir = ''
    while len(callsign) < 3:
        #print('Please enter your callsign: ', end=None)
        callsign = input('Please enter your callsign: ')
        #print()

    lotw_adif_file_name = '{}{}-lotw.adif'.format(working_dir, callsign)
    lotw_adif_new_qsos_file_name = '{}{}-lotw-new-qsos.adif'.format(working_dir, callsign)
    lotw_adif_new_qsls_file_name = '{}{}-lotw-new-qsls.adif'.format(working_dir, callsign)
    dxcc_qsls_file_name = '{}{}-cards.adif'.format(working_dir, callsign)

    lotw_header = None
    lotw_qsos = None

    if os.path.exists(lotw_adif_file_name):
        lotw_header, lotw_qsos = adif.read_adif_file(lotw_adif_file_name)
        if lotw_header.get('app_lotw_lastqsl') is None:
            lotw_header['app_lotw_lastqsl'] = lotw_header.get('app_lotw_lastqsorx')
    if os.path.exists(dxcc_qsls_file_name):
        dxcc_qsls_header, dxcc_qsl_cards = adif.read_adif_file(dxcc_qsls_file_name)

    while True:
        print('---------------------------------------')
        show_file_info(lotw_adif_file_name)
        last_qso_date = None
        if lotw_header is not None:
            print('{} QSOs'.format(len(lotw_qsos)))
            last_qso_date = lotw_header.get('app_lotw_lastqsorx')
            if last_qso_date is not None:
                print('Last QSO Received {}'.format(last_qso_date))
            last_qsl_date = lotw_header.get(('app_lotw_lastqsl'))
            if last_qsl_date is not None:
                print('Last QSL Received {}'.format(last_qsl_date))
        print('---------------------------------------')
        show_file_info(dxcc_qsls_file_name)
        if dxcc_qsls_header is not None:
            dxcc_record_updated = dxcc_qsls_header.get('app_lotw_dxccrecord_updated')
            if dxcc_record_updated is not None:
                print('DXCC Record Updated {}'.format(dxcc_record_updated))
            #print(dxcc_qsls_header)
            print('{} DXCC QSL Cards'.format(len(dxcc_qsl_cards)))
        print('---------------------------------------')
        choice = menu()
        if choice == '0':
            exit()
        elif choice == '1':
            password = get_password(password)
            lotw_header, lotw_qsos = adif.get_lotw_adif(callsign, password, filename=lotw_adif_file_name)
        elif choice == '2':
            if last_qso_date is None:
                print('Cannot update, no base, download first.')
            else:
                password = get_password(password)
                logging.info('fetching new QSOs')
                new_lotw_qsos_header, new_lotw_qsos = adif.get_lotw_adif(callsign,
                                                                        password,
                                                                        filename=lotw_adif_new_qsos_file_name,
                                                                        qso_qsorxsince=last_qso_date)
                new_last_qso_date = lotw_header.get('app_lotw_lastqsorx')
                logging.info('New last QSO Received {}, {} QSO records'.format(new_last_qso_date, len(new_lotw_qsos)))
                logging.info('fetching new QSOs')
                lotw_header, lotw_qsos = adif.merge(lotw_header, lotw_qsos, new_lotw_qsos_header, new_lotw_qsos)
                if new_lotw_qsos_header.get('app_lotw_lastqsorx') is not None:
                    lotw_header['app_lotw_lastqsorx'] = new_lotw_qsos_header.get('app_lotw_lastqsorx')

                new_lotw_qsls_header, new_lotw_qsls = adif.call_lotw(login=callsign,
                                                                     password=password,
                                                                     filename=lotw_adif_new_qsls_file_name,
                                                                     qso_owncall=callsign,
                                                                     qso_qsl='yes',
                                                                     qso_qsldetail='yes',
                                                                     qso_qslsince=last_qsl_date,
                                                                     qso_query='1'
                                                                     )
                lotw_header, lotw_qsos = adif.merge(lotw_header, lotw_qsos, new_lotw_qsls_header, new_lotw_qsls)
                if new_lotw_qsls_header.get('app_lotw_lastqsl') is not None:
                    lotw_header['app_lotw_lastqsl'] = new_lotw_qsls_header.get('app_lotw_lastqsl')

        elif choice == '3':
            password = get_password(password)
            dxcc_qsls_header, dxcc_qsl_cards = adif.get_qsl_cards(callsign, password, dxcc_qsls_file_name)
        elif choice == '4':  # save lotw qsos data
            adif.write_adif_file(lotw_header, lotw_qsos, lotw_adif_file_name, abridge_results=False)
        elif choice == '5':
            if lotw_header is None or dxcc_qsls_header is None:
                print('need both lotw qsos and dxcc cards in order to merge.  sorry.')
            else:
                combined_qsos = adif.combine_qsos(lotw_qsos, dxcc_qsl_cards)


if __name__ == '__main__':
    main()
