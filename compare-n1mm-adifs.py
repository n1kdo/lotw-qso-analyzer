"""
compare N# N1MM+ adif files.

This script provides a n-way compare of ADIF files.
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
    qso_date = qso.get('qso_date', 'missing')
    qso_time = qso.get('time_on', '000000')
    qso_call = qso.get('call')
    qso_band = qso.get('band', 'missing')
    # ClubLog throws seconds away, so this will too.
    qso_time = qso_time[0:4]
    return qso_date + '~' + qso_time + '~' + qso_call + '~' + qso_band


def n1mm_qso_key(qso):
    n1mm_id = qso.get('app_n1mm_id', 'missing')
    return n1mm_id


def main():

    parser = argparse.ArgumentParser(description='Compare ADIF files')
    parser.add_argument('--start_date', help='start date')
    parser.add_argument('--end_date', help='end date')
    parser.add_argument('--debug', action='store_true', help='show logging informational output')
    parser.add_argument('--info', action='store_true', help='show informational diagnostic output')
    parser.add_argument('filename', nargs='*', type=str, help='names of ADIF files')
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
    if len(args.filename) < 2:
        logging.error('wrong number of files, must be at least two')
        exit(1)

    qsos_dict = {}
    first = True

    for filename in args.filename:
        header, qsos = read_adif_file(filename)
        if start_date is not None and end_date is not None:
            qsos = adif_date_range(qsos, start_date, end_date)
            logging.info(f'{len(qsos)} qsos narrowed from {filename}')

        file_qsos_dict = {}
        for qso in qsos:
            key = n1mm_qso_key(qso)
            file_qsos_dict[key] = qso
            if first:
                qsos_dict[key] = qso
            else:
                if qsos_dict.get(key) is None:
                    logging.info(f'QSO {qso_string(qso)} was not seen in any previous log.')
                    qsos_dict[key] = qso
        if not first:
            qsos_keys = list(qsos_dict.keys())
            for key in qsos_keys:
                if file_qsos_dict.get(key) is None:
                    logging.info(f'QSO {qso_string(qsos_dict.get(key))} was seen in a previous log, but is not in this file.')

        first = False
        logging.info(f'{len(qsos_dict)} QSOs so far...')
    print('done')


if __name__ == '__main__':
    main()
