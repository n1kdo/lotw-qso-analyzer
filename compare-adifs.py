"""
compare two adif files
"""
import argparse
import datetime
import logging
import time
from adif import read_adif_file, qso_string

__version__ = '0.0.1'

def adif_date_range(qsos, start_date, end_date):
    narrowed_qsos = []
    for qso in qsos:
        qso_date_string = qso.get('qso_date')
        if qso_date_string is not None:
            qso_date = datetime.datetime.strptime(qso_date_string, '%Y%m%d').date()
            if start_date <= qso_date < end_date:
                narrowed_qsos.append(qso)
    return narrowed_qsos


def qso_key(qso):
    qso_date = qso.get('qso_date') or 'missing'
    qso_time = qso.get('time_on') or '000000'
    qso_call = qso.get('call') or 'missing'
    qso_band = qso.get('band') or 'missing'
    # ClubLog throws seconds away, so this will too.
    qso_time = qso_time[0:4]
    return qso_date + '~' + qso_time + '~' + qso_call + '~' + qso_band


def main():

    parser = argparse.ArgumentParser(description='Compare ADIF files')

    parser.add_argument('--start_date', help='start date')
    parser.add_argument('--end_date', help='end date')
    parser.add_argument('--debug', action='store_true', help='show logging informational output')
    parser.add_argument('--info', action='store_true', help='show informational diagnostic output')
    parser.add_argument('filename', nargs=2, type=str, help='name of ADIF file')
    args = parser.parse_args()

    log_format = '%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s'
    log_date_format = '%Y-%m-%d %H:%M:%S'
    if args.debug:
        logging.basicConfig(format=log_format, datefmt=log_date_format, level=logging.DEBUG)
    elif args.info:
        logging.basicConfig(format=log_format, datefmt=log_date_format, level=logging.INFO)
    else:
        logging.basicConfig(format=log_format, datefmt=log_date_format, level=logging.WARNING)

    logging.Formatter.converter = time.gmtime

    if args.start_date is not None:
        start_date = datetime.datetime.strptime(args.start_date, '%Y%m%d').date()
    else:
        start_date = None
    if args.end_date is not None:
        end_date = datetime.datetime.strptime(args.end_date, '%Y%m%d').date()
    else:
        end_date = None
    if len(args.filename) != 2:
        logging.error('wrong number of files, must be two')
        exit(1)

    left_file = args.filename[0]
    right_file = args.filename[1]

    # read the two adif files
    header1, left_qsos = read_adif_file(left_file)
    logging.info(f'{len(left_qsos)} qsos read from {left_file}')
    header2, right_qsos = read_adif_file(right_file)
    logging.info(f'{len(right_qsos)} qsos read from {right_file}')

    # narrow to date range
    if start_date is not None and end_date is not None:
        left_qsos = adif_date_range(left_qsos, start_date, end_date)
        logging.info(f'{len(left_qsos)} qsos narrowed from {left_file}')
        right_qsos = adif_date_range(right_qsos, start_date, end_date)
        logging.info(f'{len(right_qsos)} qsos narrowed from {right_file}')

    # build keys
    left_keys = []
    for qso in left_qsos:
        left_keys.append(qso_key(qso))
    right_keys = []
    for qso in right_qsos:
        right_keys.append(qso_key(qso))

    # now start comparing.
    # first make sure that every key in list 1 is in list 2.
    print(f'looking for QSOs in {left_file} that are not in {right_file}')
    left_missing = 0
    for qk in left_keys:
        if qk not in right_keys:
            left_missing += 1
            print(f'did not find qso {qk} in {right_file}')

    print()
    # next make sure that every key in list 1 is in list 2.
    print(f'looking for QSOs in {right_file} that are not in {left_file}')
    right_missing = 0
    for qk in right_keys:
        if qk not in left_keys:
            right_missing += 1
            print(f'did not find qso {qk} in {left_file}')

    print(f'{left_missing} qsos not found in {right_file}')
    print(f'{right_missing} qsos not found in {left_file}')

    print('done')


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)
    logging.Formatter.converter = time.gmtime
    main()
