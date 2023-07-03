#!/usr/bin/python
"""
adif_log_analyzer.py -- get statistics from LoTW QSO ADIF.
data can come from ADIF file downloaded from Logbook of The World, or this
script can collect the data from LoTW for you, optionally saving the ADIF.

LICENSE:

Copyright (c) 2017 - 2021, Jeffrey B. Otterson, N1KDO
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

import datetime
import logging
import os
import sys
import time

import adif
import qso_charts

__author__ = 'Jeffrey B. Otterson, N1KDO'
__copyright__ = 'Copyright 2017 - 2023 Jeffrey B. Otterson'
__license__ = 'Simplified BSD'
__version__ = '0.10.0'

FFMA_GRIDS = ['CM79', 'CM86', 'CM87', 'CM88', 'CM89', 'CM93', 'CM94', 'CM95', 'CM96', 'CM97', 'CM98', 'CM99',
              'CN70', 'CN71', 'CN72', 'CN73', 'CN74', 'CN75', 'CN76', 'CN77', 'CN78', 'CN80', 'CN81', 'CN82',
              'CN83', 'CN84', 'CN85', 'CN86', 'CN87', 'CN88', 'CN90', 'CN91', 'CN92', 'CN93', 'CN94', 'CN95',
              'CN96', 'CN97', 'CN98', 'DL79', 'DL88', 'DL89', 'DL98', 'DL99', 'DM02', 'DM03', 'DM04', 'DM05',
              'DM06', 'DM07', 'DM08', 'DM09', 'DM12', 'DM13', 'DM14', 'DM15', 'DM16', 'DM17', 'DM18', 'DM19',
              'DM22', 'DM23', 'DM24', 'DM25', 'DM26', 'DM27', 'DM28', 'DM29', 'DM31', 'DM32', 'DM33', 'DM34',
              'DM35', 'DM36', 'DM37', 'DM38', 'DM39', 'DM41', 'DM42', 'DM43', 'DM44', 'DM45', 'DM46', 'DM47',
              'DM48', 'DM49', 'DM51', 'DM52', 'DM53', 'DM54', 'DM55', 'DM56', 'DM57', 'DM58', 'DM59', 'DM61',
              'DM62', 'DM63', 'DM64', 'DM65', 'DM66', 'DM67', 'DM68', 'DM69', 'DM70', 'DM71', 'DM72', 'DM73',
              'DM74', 'DM75', 'DM76', 'DM77', 'DM78', 'DM79', 'DM80', 'DM81', 'DM82', 'DM83', 'DM84', 'DM85',
              'DM86', 'DM87', 'DM88', 'DM89', 'DM90', 'DM91', 'DM92', 'DM93', 'DM94', 'DM95', 'DM96', 'DM97',
              'DM98', 'DM99', 'DN00', 'DN01', 'DN02', 'DN03', 'DN04', 'DN05', 'DN06', 'DN07', 'DN08', 'DN10',
              'DN11', 'DN12', 'DN13', 'DN14', 'DN15', 'DN16', 'DN17', 'DN18', 'DN20', 'DN21', 'DN22', 'DN23',
              'DN24', 'DN25', 'DN26', 'DN27', 'DN28', 'DN30', 'DN31', 'DN32', 'DN33', 'DN34', 'DN35', 'DN36',
              'DN37', 'DN38', 'DN40', 'DN41', 'DN42', 'DN43', 'DN44', 'DN45', 'DN46', 'DN47', 'DN48', 'DN50',
              'DN51', 'DN52', 'DN53', 'DN54', 'DN55', 'DN56', 'DN57', 'DN58', 'DN60', 'DN61', 'DN62', 'DN63',
              'DN64', 'DN65', 'DN66', 'DN67', 'DN68', 'DN70', 'DN71', 'DN72', 'DN73', 'DN74', 'DN75', 'DN76',
              'DN77', 'DN78', 'DN80', 'DN81', 'DN82', 'DN83', 'DN84', 'DN85', 'DN86', 'DN87', 'DN88', 'DN90',
              'DN91', 'DN92', 'DN93', 'DN94', 'DN95', 'DN96', 'DN97', 'DN98', 'EL06', 'EL07', 'EL08', 'EL09',
              'EL15', 'EL16', 'EL17', 'EL18', 'EL19', 'EL28', 'EL29', 'EL39', 'EL49', 'EL58', 'EL59', 'EL79',
              'EL84', 'EL86', 'EL87', 'EL88', 'EL89', 'EL94', 'EL95', 'EL96', 'EL97', 'EL98', 'EL99', 'EM00',
              'EM01', 'EM02', 'EM03', 'EM04', 'EM05', 'EM06', 'EM07', 'EM08', 'EM09', 'EM10', 'EM11', 'EM12',
              'EM13', 'EM14', 'EM15', 'EM16', 'EM17', 'EM18', 'EM19', 'EM20', 'EM21', 'EM22', 'EM23', 'EM24',
              'EM25', 'EM26', 'EM27', 'EM28', 'EM29', 'EM30', 'EM31', 'EM32', 'EM33', 'EM34', 'EM35', 'EM36',
              'EM37', 'EM38', 'EM39', 'EM40', 'EM41', 'EM42', 'EM43', 'EM44', 'EM45', 'EM46', 'EM47', 'EM48',
              'EM49', 'EM50', 'EM51', 'EM52', 'EM53', 'EM54', 'EM55', 'EM56', 'EM57', 'EM58', 'EM59', 'EM60',
              'EM61', 'EM62', 'EM63', 'EM64', 'EM65', 'EM66', 'EM67', 'EM68', 'EM69', 'EM70', 'EM71', 'EM72',
              'EM73', 'EM74', 'EM75', 'EM76', 'EM77', 'EM78', 'EM79', 'EM80', 'EM81', 'EM82', 'EM83', 'EM84',
              'EM85', 'EM86', 'EM87', 'EM88', 'EM89', 'EM90', 'EM91', 'EM92', 'EM93', 'EM94', 'EM95', 'EM96',
              'EM97', 'EM98', 'EM99', 'EN00', 'EN01', 'EN02', 'EN03', 'EN04', 'EN05', 'EN06', 'EN07', 'EN08',
              'EN10', 'EN11', 'EN12', 'EN13', 'EN14', 'EN15', 'EN16', 'EN17', 'EN18', 'EN20', 'EN21', 'EN22',
              'EN23', 'EN24', 'EN25', 'EN26', 'EN27', 'EN28', 'EN29', 'EN30', 'EN31', 'EN32', 'EN33', 'EN34',
              'EN35', 'EN36', 'EN37', 'EN38', 'EN40', 'EN41', 'EN42', 'EN43', 'EN44', 'EN45', 'EN46', 'EN47',
              'EN48', 'EN50', 'EN51', 'EN52', 'EN53', 'EN54', 'EN55', 'EN56', 'EN57', 'EN58', 'EN60', 'EN61',
              'EN62', 'EN63', 'EN64', 'EN65', 'EN66', 'EN67', 'EN70', 'EN71', 'EN72', 'EN73', 'EN74', 'EN75',
              'EN76', 'EN80', 'EN81', 'EN82', 'EN83', 'EN84', 'EN85', 'EN86', 'EN90', 'EN91', 'EN92', 'FM02',
              'FM03', 'FM04', 'FM05', 'FM06', 'FM07', 'FM08', 'FM09', 'FM13', 'FM14', 'FM15', 'FM16', 'FM17',
              'FM18', 'FM19', 'FM25', 'FM26', 'FM27', 'FM28', 'FM29', 'FN00', 'FN01', 'FN02', 'FN03', 'FN10',
              'FN11', 'FN12', 'FN13', 'FN14', 'FN20', 'FN21', 'FN22', 'FN23', 'FN24', 'FN25', 'FN30', 'FN31',
              'FN32', 'FN33', 'FN34', 'FN35', 'FN41', 'FN42', 'FN43', 'FN44', 'FN45', 'FN46', 'FN51', 'FN53',
              'FN54', 'FN55', 'FN56', 'FN57', 'FN64', 'FN65', 'FN66', 'FN67']

logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)
logging.Formatter.converter = time.gmtime
charts_dir = 'charts/'


def date_range(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)


def convert_qso_date(d):
    return datetime.datetime.strptime(d, '%Y%m%d').date()


def input1(prompt):
    print(prompt)
    s = input()
    # s = sys.stdin.readline()
    return s


def get_yes_no(prompt, default=None):
    while True:
        yn = input1(prompt)
        if len(yn):
            if yn[0] == 'y' or yn[0] == 'Y':
                return True
            if yn[0] == 'n' or yn[0] == 'N':
                return False
        else:
            if default is not None:
                return default


def crunch_data(qso_list):
    #    print_csv_data = get_yes_no('Show CSV data for Excel [y/N] : ', False)
    logging.debug('crunch_data')
    logging.info('%5d total LoTW QSOs' % len(qso_list))
    # sort list of QSOs into ascending range by qso_date
    # qso_list.sort(key=lambda q: q['qso_date'])
    for qso in qso_list:
        app_lotw_qso_timestamp = qso.get('app_lotw_qso_timestamp')
        if app_lotw_qso_timestamp is None:
            logging.warning('app_lotw_qso_timestamp is None')
            qso_date = qso.get('qso_date')
            qso_time = qso.get('time_on') or ''
            if len(qso_time) != 6:
                qso_time = '120000'  # if no date, make mid-day
            qso_iso_date = qso_date[0:4] + '-' + qso_date[4:6] + '-' + qso_date[6:8]
            qso_iso_date += 'T' + qso_time[0:2] + ':' + qso_time[2:4] + ':' + qso_time[4:6] + '+00:00'
            dt = datetime.datetime.fromisoformat(qso_iso_date)
            qso['app_lotw_qso_timestamp'] = dt
            # could/should create this here if missing
        else:
            if isinstance(app_lotw_qso_timestamp, str):
                app_lotw_qso_timestamp = app_lotw_qso_timestamp.replace('Z', '+00:00')
                qso['app_lotw_qso_timestamp'] = datetime.datetime.fromisoformat(app_lotw_qso_timestamp)
            elif not isinstance(app_lotw_qso_timestamp, datetime.datetime):
                logging.error(f'app_lotw_qso_timestamp is of type {type(app_lotw_qso_timestamp)}')

    qso_list.sort(key=lambda q: q['app_lotw_qso_timestamp'])

    # now this can be binned.
    first_datetime = qso_list[0]['app_lotw_qso_timestamp']
    last_datetime = qso_list[-1]['app_lotw_qso_timestamp']

    # always start on a day boundary
    first_datetime = first_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
    last_datetime = last_datetime.replace(hour=23, minute=59, second=59, microsecond=999999)

    bin_data = qso_charts.BinnedQSOData(first_datetime, last_datetime)

    dxcc_confirmed = {}
    grids = {}
    total_counts = {'date': 'total', 'worked': 0, 'confirmed': 0, 'new_dxcc': 0, 'challenge': 0, 'ffma': 0, 'vucc': 0}
    for band in adif.BANDS:
        total_counts[band] = 0
        total_counts['challenge_' + band] = 0
        for mode in adif.MODES:
            total_counts[f'{band}_{mode}'] = 0
    for mode in adif.MODES:
        total_counts[mode] = 0

    unique_calls = {}
    first_date = None
    last_date = None
    n_worked = 0
    n_confirmed = 0
    n_verified = 0
    n_challenge = 0
    check_cards = []

    date_records = {}  # key is qso date.  value is dict, first record is summary data.
    # initialize data
    key_names = ['challenge', 'confirmed', 'new_dxcc', 'worked', 'ffma', 'vucc']
    for band in adif.BANDS:
        key_names.append(band)
        key_names.append('challenge_' + band)
    for mode in adif.MODES:
        key_names.append(mode)
    for i in range(0, bin_data.num_bins):
        for key_name in key_names:
            bin_data.data[i][key_name] = 0

    for qso in qso_list:
        app_lotw_qso_timestamp = qso.get('app_lotw_qso_timestamp')
        bin_num = bin_data.get_bin(app_lotw_qso_timestamp)
        bin_dict = bin_data.data[bin_num]
        qso_date = qso.get('qso_date')
        qso_band = (qso.get('band') or '').upper()
        if qso_band == '':
            logging.warning('empty band data in qso:' + str(qso))
            continue

        if qso_date is not None:
            if False:  # check sanity of qsl date
                processed_date = qso.get('app_lotw_dxcc_processed_dtg')
                if processed_date is not None:
                    processed_date = processed_date[0:4] + processed_date[5:7] + processed_date[8:10]
                    d = int(processed_date) - int(qso_date)
                    if d / 10000 > 10:
                        print('{}:{}:{}'.format(qso_date, processed_date, d))

            confirmed = 0
            verified = 0
            new_dxcc = 0
            new_deleted = 0
            challenge = 0
            vucc = 0
            ffma = 0
            n_worked += 1

            qso_dxcc = qso.get('dxcc') or '0'
            lotw_qsl_rcvd = (qso.get('lotw_qsl_rcvd') or 'N').lower()
            if lotw_qsl_rcvd == 'y':
                confirmed = 1
            elif lotw_qsl_rcvd == 'v':
                confirmed = 1
                verified = 1
            qsl_rcvd = (qso.get('qsl_rcvd') or 'N').lower()
            if qsl_rcvd == 'y':
                if True:
                    confirmed = 1
                else:
                    if qso.get('app_lotw_2xqsl') is not None or qso.get('app_lotw_credit_granted') is not None:
                        confirmed = 1
                    elif qso.get('qslrdate') is not None:
                        confirmed = 1
                    elif confirmed == 0:
                        check_cards.append(qso)
                        print(qso)

            elif qsl_rcvd == 'v':
                confirmed = 1
                verified = 1

            dxcc_lookup_tuple = adif.dxcc_countries.get(qso_dxcc) or ('None', False)
            dxcc_name = dxcc_lookup_tuple[0]
            deleted = dxcc_lookup_tuple[1]
            mode = qso.get('app_lotw_modegroup')
            if mode is None:
                mode = adif.adif_mode_to_lotw_modegroup(qso.get('mode'))

            if mode not in adif.MODES:
                logging.warning('unknown mode {} in qso:'.format(mode) + str(qso))

            if qso_dxcc is not None and qso_dxcc != '0' and deleted is False:
                if confirmed == 1:
                    if qso_dxcc not in dxcc_confirmed:
                        dxcc_country = adif.dxcc_countries.get(qso_dxcc) or ('error', True)
                        deleted = dxcc_country[1]
                        if deleted:
                            new_deleted = 1
                        else:
                            new_dxcc = 1
                        dxcc_confirmed[qso_dxcc] = {
                            'COUNTRY': dxcc_name,
                            'DXCC': qso_dxcc,
                            'MIXED': 0,
                            'CW': 0,
                            'PHONE': 0,
                            'DATA': 0,
                            '160M': 0,
                            '80M': 0,
                            '40M': 0,
                            '30M': 0,
                            '20M': 0,
                            '17M': 0,
                            '15M': 0,
                            '12M': 0,
                            '10M': 0,
                            '6M': 0
                        }
                    dxcc_counts = dxcc_confirmed[qso_dxcc]
                    dxcc_counts['MIXED'] = dxcc_counts['MIXED'] + 1
                    if mode in dxcc_counts:
                        dxcc_counts[mode] = dxcc_counts[mode] + 1
                    if qso_band in dxcc_counts:
                        if dxcc_counts[qso_band] == 0:
                            challenge = 1
                        dxcc_counts[qso_band] = dxcc_counts[qso_band] + 1

            if qso_band == '6M':
                qso_grids = []
                vucc_grids = qso.get('vucc_grids')
                if vucc_grids is not None:
                    vucc_grids = vucc_grids.split(',')
                    for vucc_grid in vucc_grids:
                        qso_grids.append(vucc_grid[0:4])
                if len(qso_grids) == 0:
                    gridsquare = qso.get('gridsquare')
                    if gridsquare is not None:
                        qso_grids.append(gridsquare[0:4])
                for qso_grid in qso_grids:
                    grid_count = grids.get(qso_grid)
                    if grid_count is None:
                        grid_count = 1
                        vucc += 1
                        if qso_grid in FFMA_GRIDS:
                            ffma += 1
                    else:
                        grid_count += 1
                    grids[qso_grid] = grid_count

            n_confirmed += confirmed
            n_verified += verified
            n_challenge += challenge

            if qso_date is not None:
                qdate = convert_qso_date(qso_date)
                if qdate in date_records:
                    counts = date_records[qdate]
                else:
                    counts = {'qdate': qdate, 'worked': 0, 'confirmed': 0,
                              'new_dxcc': 0, 'challenge': 0, 'ffma': 0, 'vucc': 0}
                    for band in adif.BANDS:
                        counts[band] = 0
                        counts['challenge_' + band] = 0
                    for mode_name in adif.MODES:
                        counts[mode_name] = 0
                    date_records[qdate] = counts

                if counts['qdate'] != qdate:
                    logging.error('ow ow ow!')  # this is bad bad
                counts['worked'] += 1
                counts['confirmed'] += confirmed
                counts['new_dxcc'] += new_dxcc
                counts['challenge'] += challenge
                counts['ffma'] += ffma
                counts['vucc'] += vucc
                counts[mode] += 1

                bin_dict['worked'] += 1
                bin_dict['confirmed'] += confirmed
                bin_dict['new_dxcc'] += new_dxcc
                bin_dict['challenge'] += challenge
                bin_dict['ffma'] += ffma
                bin_dict['vucc'] += vucc
                bin_dict[qso_band] += 1
                bin_dict[mode] += 1
                bin_dict['challenge_' + qso_band] += challenge

                total_counts['worked'] += 1
                total_counts['confirmed'] += confirmed
                total_counts['new_dxcc'] += new_dxcc
                total_counts['challenge'] += challenge
                total_counts['ffma'] += ffma
                total_counts['vucc'] += vucc

                if qso_band != '':
                    counts['challenge_' + qso_band] += challenge
                    counts[qso_band] += 1
                    total_counts['challenge_' + qso_band] += challenge
                    total_counts[qso_band] += 1
                    total_counts[f'{qso_band}_{mode}'] += 1
                total_counts[mode] += 1

                if last_date is None or qdate > last_date:
                    last_date = qdate
                if first_date is None or qdate < first_date:
                    first_date = qdate

                call = qso['call']
                if call not in unique_calls:
                    unique_calls[call] = [qso]
                else:
                    unique_calls[call].append(qso)
            else:
                logging.warning("Invalid QSO record has no date ", qso)

    print('%5d counted worked' % n_worked)
    print(f'{len(unique_calls):5d} unique calls')
    print('%5d confirmed' % n_confirmed)
    print('%5d verified' % n_verified)
    print('%5d challenge' % n_challenge)
    for band in adif.BANDS:
        c = int(total_counts['challenge_' + band])
        if c > 0:
            print('{:5d} {}'.format(c, band))
    print('%5d total dxcc' % len(dxcc_confirmed))
    print()
    print('             QSOs band/mode')
    print('  BAND     CW   DATA  IMAGE  PHONE  TOTAL')
    for band in adif.BANDS:
        c = int(total_counts[band])
        if c > 0:
            cw = total_counts[f'{band}_CW']
            data = total_counts[f'{band}_DATA']
            image = total_counts[f'{band}_IMAGE']
            phone = total_counts[f'{band}_PHONE']
            print(f'{band:>6s}  {cw:5d}  {data:5d}  {image:5d}  {phone:5d}  {c:5d}')

    cw = total_counts[f'CW']
    data = total_counts[f'DATA']
    image = total_counts[f'IMAGE']
    phone = total_counts[f'PHONE']
    c = cw + data + image + phone
    print(f' TOTAL  {cw:5d}  {data:5d}  {image:5d}  {phone:5d}  {c:5d}')

    print()
    print('%5d unique log dates' % len(date_records))
    print('first QSO date: ' + first_date.strftime('%Y-%m-%d'))
    print('last QSO date: ' + last_date.strftime('%Y-%m-%d'))

    # now calculate running totals by date
    total_worked = 0
    total_confirmed = 0
    total_new_dxcc = 0
    total_new_challenge = 0

    for qdate in sorted(date_records.keys()):
        counts = date_records[qdate]
        total_worked += counts['worked']
        total_confirmed += counts['confirmed']
        total_new_dxcc += counts['new_dxcc']
        total_new_challenge += counts['challenge']
        #        for band in BANDS:
        #            band_totals[band] += counts[band]
        #            counts['total_' + band] = band_totals[band]
        counts['total_worked'] = total_worked
        counts['total_confirmed'] = total_confirmed
        counts['total_new_dxcc'] = total_new_dxcc
        counts['total_challenge'] = total_new_challenge

    total_worked = 0
    total_confirmed = 0
    total_dxcc = 0
    total_challenge = 0
    total_vucc = 0
    total_ffma = 0
    for bin_num in range(0, bin_data.num_bins):
        bin_dict = bin_data.data[bin_num]
        total_worked += bin_dict['worked']
        total_confirmed += bin_dict['confirmed']
        total_dxcc += bin_dict['new_dxcc']
        total_challenge += bin_dict['challenge']
        total_vucc += bin_dict['vucc']
        total_ffma += bin_dict['ffma']
        bin_dict['total_worked'] = total_worked
        bin_dict['total_confirmed'] = total_confirmed
        bin_dict['total_dxcc'] = total_dxcc
        bin_dict['total_challenge'] = total_challenge
        bin_dict['total_vucc'] = total_vucc
        bin_dict['total_ffma'] = total_ffma

    #        print(("%s  %5d  %5d  %5d  %5d  %5d  %5d  %5d  %5d") % (qdate.strftime('%Y-%m-%d'),
    #                                                               counts['worked'],
    #                                                               counts['confirmed'],
    #                                                               counts['total_worked'],
    #                                                               counts['total_confirmed'],
    #                                                               counts['new_dxcc'],
    #                                                               counts['total_new_dxcc'],
    #                                                               counts['challenge'],
    #                                                               counts['total_challenge']))

    if True:  # show summary data, not needed for charting, but possibly interesting.
        # top 20 most productive days
        number_of_top_days = 20
        if len(date_records) < number_of_top_days:
            number_of_top_days = len(date_records)
        print()
        print('Top %d days' % number_of_top_days)
        print()
        most_productive = sorted(list(date_records.values()), key=lambda counts: counts['worked'], reverse=True)
        for i in range(0, number_of_top_days):
            print('%2d  %12s %5d' % (i + 1, str(most_productive[i]['qdate']), most_productive[i]['worked']))

        calls_by_qso = []
        for call, qso_list in unique_calls.items():
            calls_by_qso.append((call, len(qso_list)))
        calls_by_qso = sorted(calls_by_qso, key=lambda count: count[1], reverse=True)

        # show top calls
        number_of_top_calls = 50
        print()
        print('Top %d calls' % number_of_top_calls)
        print()
        for i in range(0, number_of_top_calls):
            print('%2d %10s %3d' % (i + 1, calls_by_qso[i][0], calls_by_qso[i][1]))

    # dump the dxcc_counts data
    dxcc_records = dxcc_confirmed.values()
    dxcc_records = sorted(dxcc_records, key=lambda dxcc: int(dxcc['DXCC']))
    print(
        'DXCC Name                                 MIXED    CW PHONE  DATA 160M  80M  40M  30M  20M  17M  15M  12M  10M   6M')
    for rec in dxcc_records:
        print(
            ' {:3d} {:36s}  {:4d}  {:4d}  {:4d}  {:4d} {:4d} {:4d} {:4d} {:4d} {:4d} {:4d} {:4d} {:4d} {:4d} {:4d}'.format(
                int(rec['DXCC']), rec['COUNTRY'],
                rec['MIXED'], rec['CW'], rec['PHONE'], rec['DATA'],
                rec['160M'], rec['80M'], rec['40M'], rec['30M'],
                rec['20M'], rec['17M'], rec['15M'], rec['12M'],
                rec['10M'], rec['6M']))

    # don't want to sort this more than once.
    # the result is a list of counts dicts
    results = []
    for key in sorted(date_records.keys()):
        # if key >= start_date and key <= end_date:
        results.append(date_records[key])
    logging.debug('crunched data for %d log days' % len(results))
    return bin_data


def draw_charts(qso_list, callsign, start_date=None, end_date=None):
    logging.debug('draw_charts')
    callsign = callsign.upper()
    file_callsign = charts_dir + callsign.replace('/', '-')
    logging.info('crunching QSO data')
    bin_data = crunch_data(qso_list)

    # now draw the charts
    logging.info('drawing QSOs chart')
    qso_charts.plot_qsos_by_date(bin_data,
                                 callsign + ' QSOs',
                                 file_callsign + '_qsos_by_date.png',
                                 start_date=start_date,
                                 end_date=end_date)
    logging.info('drawing DXCC and Challenge QSLs chart')
    qso_charts.plot_dxcc_qsos(bin_data,
                              callsign + ' DXCC and Challenge QSLs',
                              file_callsign + '_dxcc_qsos.png',
                              start_date=start_date,
                              end_date=end_date)
    logging.info('drawing VUCC and FFMA QSLs chart')
    qso_charts.plot_vucc_qsos(bin_data,
                              callsign + ' VUCC and FFMA QSLs',
                              file_callsign + '_vucc_qsos.png',
                              start_date=start_date,
                              end_date=end_date)
    logging.info('drawing QSO Rate chart')
    qso_charts.plot_qsos_rate(bin_data,
                              callsign + ' QSO Rate',
                              file_callsign + '_qso_rate.png',
                              start_date=start_date,
                              end_date=end_date)
    logging.info('drawing QSO Rate by Band chart')
    qso_charts.plot_qsos_band_rate(bin_data,
                                   callsign + ' QSO Rate by Band',
                                   file_callsign + '_qsos_band_rate.png',
                                   start_date=start_date,
                                   end_date=end_date)
    logging.info('drawing QSO Rate by Mode chart')
    qso_charts.plot_qsos_mode_rate(bin_data,
                                   callsign + ' QSO Rate by Mode',
                                   file_callsign + '_qsos_mode_rate.png',
                                   start_date=start_date,
                                   end_date=end_date)
    logging.info('drawing Challenge Band Slots chart')
    qso_charts.plot_challenge_bands_by_date(bin_data, callsign + ' Challenge Band Slots',
                                            file_callsign + '_challenge_bands_by_date.png', start_date=start_date,
                                            end_date=end_date)
    logging.info('drawing Grid Squares Confirmed map')
    qso_charts.plot_map(qso_list,
                        callsign + ' Grid Squares Confirmed',
                        file_callsign + '_grids_map.png',
                        start_date=start_date,
                        end_date=end_date)


def main():
    print('N1KDO\'s ADIF analyzer version %s' % __version__)
    if len(sys.argv) == 3:
        callsign = sys.argv[1]
        filename = sys.argv[2]
    else:
        callsign = ''
        filename = ''

    while len(callsign) < 3:
        callsign = input('enter callsign: ')

    while len(filename) < 4:
        filename = input('Enter adif file name: ')

    filename = 'data/' + filename
    if not os.path.exists(filename):
        filename = ''

    adif_header, qso_list = adif.read_adif_file(filename)
    logging.info('read {} qsls from {}'.format(len(qso_list), filename))

    if qso_list is not None:
        start_date = None
        end_date = None
        # start_date = datetime.datetime.strptime('20070101', '%Y%m%d').date()
        # start_date = datetime.datetime.strptime('20180101', '%Y%m%d').date()
        # end_date   = datetime.datetime.strptime('20181231', '%Y%m%d').date()
        draw_charts(qso_list, callsign, start_date=start_date, end_date=end_date)

    logging.info('done.')


if __name__ == '__main__':
    main()
