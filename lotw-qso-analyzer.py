#!/usr/bin/python
"""
lotw-qso-analyzer.py -- get statistics from LoTW QSO ADIF.
data can come from ADIF file downloaded from Logbook of The World, or this
script can collect the data from LoTW for you, optionally saving the ADIF.

LICENSE:

Copyright (c) 2018, Jeffrey B. Otterson, N1KDO
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
import time
import sys

import adif
import qso_charts

__author__ = 'Jeffrey B. Otterson, N1KDO'
__copyright__ = 'Copyright 2017 Jeffrey B. Otterson'
__license__ = 'Simplified BSD'
__version__ = '0.02'

logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)
logging.Formatter.converter = time.gmtime

BANDS = ['160M', '80M', '60M', '40M', '30M', '20M', '17M', '15M', '12M', '10M', '6M', '2M', '70CM']


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


def crunch_data(callsign, qso_list):
    #    print_csv_data = get_yes_no('Show CSV data for Excel [y/N] : ', False)
    logging.debug('crunch_data')
    logging.info('%5d total LoTW QSOs' % len(qso_list))
    # sort list of QSOs into ascending range by qso_date
    qso_list.sort(key=lambda q: q['qso_date'])

    dxcc_confirmed = {}
    date_records = {}  # key is qso date.  value is dict, first record is summary data.
    total_counts = {'qdate': 'total', 'worked': 0, 'confirmed': 0, 'new_dxcc': 0, 'challenge': 0}
    for band in BANDS:
        total_counts[band] = 0
        total_counts['challenge_' + band] = 0

    #    unique_calls = {}
    first_date = None
    last_date = None
    n_worked = 0
    n_confirmed = 0
    n_challenge = 0

    for qso in qso_list:
        qso_date = qso.get('qso_date')
        if qso_date is not None:
            confirmed = 0
            new_dxcc = 0
            challenge = 0
            n_worked += 1

            qso_dxcc = qso.get('dxcc')
            qsl_rcvd = qso.get('qsl_rcvd')
            qso_band = qso.get('band')
            if qso_dxcc is not None:
                if qsl_rcvd is not None and qsl_rcvd.lower() == 'y':
                    confirmed = 1
                    mode = qso.get('app_lotw_modegroup')
                    if qso_dxcc not in dxcc_confirmed:
                        new_dxcc = 1
                        dxcc_confirmed[qso_dxcc] = {'COUNTRY': qso.get('country'),
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

            n_confirmed += confirmed
            n_challenge += challenge

            if qso_date is not None:
                qdate = convert_qso_date(qso_date)
                if qdate in date_records:
                    counts = date_records[qdate]
                else:
                    counts = {'qdate': qdate, 'worked': 0, 'confirmed': 0,
                              'new_dxcc': 0, 'challenge': 0}
                    for band in BANDS:
                        counts[band] = 0
                        counts['challenge_' + band] = 0
                        date_records[qdate] = counts

                if counts['qdate'] != qdate:
                    logging.error('ow ow ow!')  # this is bad bad
                counts['worked'] += 1
                counts['confirmed'] += confirmed
                counts['new_dxcc'] += new_dxcc
                counts['challenge'] += challenge
                counts['challenge_' + qso_band] += challenge
                counts[qso_band] += 1
                total_counts['worked'] += 1
                total_counts['confirmed'] += confirmed
                total_counts['new_dxcc'] += new_dxcc
                total_counts['challenge'] += challenge
                total_counts['challenge_' + qso_band] += challenge
                total_counts[qso_band] += 1

                if last_date is None or qdate > last_date:
                    last_date = qdate
                if first_date is None or qdate < first_date:
                    first_date = qdate
            else:
                logging.warning("Invalid QSO record has no date ", qso)

#            call = qso['call']
#            if call not in unique_calls:
#                unique_calls[call] = [qso]
#            else:
#                unique_calls[call].append(qso)

    print('%5d counted worked' % n_worked)
    print('%5d confirmed' % n_confirmed)
    print('%5d challenge' % n_challenge)
    print('%5d total dxcc' % len(dxcc_confirmed))
    print()
    print('%5d unique log dates' % len(date_records))
    print('first QSO date: ' + first_date.strftime('%Y-%m-%d'))
    print('last QSO date: ' + last_date.strftime('%Y-%m-%d'))

    # now calculate running totals by date
    total_worked = 0
    total_confirmed = 0
    total_new_dxcc = 0
    total_new_challenge = 0
    band_totals = {}
    #    for band in BANDS:
    #        band_totals[band] = 0

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
        #date_records[qdate] = counts  # I think this is redundant.
    #        print(("%s  %5d  %5d  %5d  %5d  %5d  %5d  %5d  %5d") % (qdate.strftime('%Y-%m-%d'),
    #                                                               counts['worked'],
    #                                                               counts['confirmed'],
    #                                                               counts['total_worked'],
    #                                                               counts['total_confirmed'],
    #                                                               counts['new_dxcc'],
    #                                                               counts['total_new_dxcc'],
    #                                                               counts['challenge'],
    #                                                               counts['total_challenge']))


    if False: # show summary data, not needed for charting, but possibly interesting.
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
        number_of_top_calls = 40
        print()
        print('Top %d calls' % number_of_top_calls)
        print()
        for i in range(0, number_of_top_calls):
            print('%2d %10s %3d' % (i + 1, calls_by_qso[i][0], calls_by_qso[i][1]))

    # don't want to sort this more than once.
    # the result is a list of counts dicts
    results = []
    for key in sorted(date_records.keys()):
        # if key >= start_date and key <= end_date:
        results.append(date_records[key])
    logging.debug('crunched data for %d log days' % len(results))
    return results


def draw_charts(date_records, callsign, start_date=None, end_date=None):
    logging.debug('draw_charts')
    #start_date = datetime.datetime.strptime('20070101', '%Y%m%d').date()
    #start_date = datetime.datetime.strptime('20140101', '%Y%m%d').date()
    #end_date   = datetime.datetime.strptime('20181231', '%Y%m%d').date()

    callsign = callsign.upper()

    # now draw the charts
    qso_charts.plot_qsos_by_date(date_records, callsign + ' QSOs',
                                 callsign + '_qsos_by_date.png',
                                 start_date=start_date,
                                 end_date=end_date)
    qso_charts.plot_dxcc_qsos(date_records, callsign + ' DXCC QSOs',
                              callsign + '_dxcc_qsos.png', start_date=start_date,
                              end_date=end_date)
    qso_charts.plot_qsos_rate(date_records, callsign + ' QSO Rate',
                              callsign + '_qso_rate.png', start_date=start_date,
                              end_date=end_date)
    qso_charts.plot_qsos_band_rate(date_records, callsign + ' QSO by Band',
                                   callsign + '_qsos_band_rate.png',
                                   start_date=start_date, end_date=end_date)
    qso_charts.plot_challenge_bands_by_date(date_records, callsign + ' Challenge Band Slots',
                                            callsign + '_challenge_bands_by_date.png', start_date=start_date, end_date=end_date)


def compare_lists(qso_list, cards_list):
    qsos = {}
    for qso in qso_list:
        key = qso['call'] + '.' + qso['qso_date'] + '.' + qso['band'] + '.' + qso['app_lotw_modegroup']
        qsos[key] = qso

    for qso in cards_list:
        key = qso['call'] + '.' + qso['qso_date'] + '.' + qso['band'] + '.' + qso.get('app_lotw_modegroup')
        if not key in qsos:
            print("can't find a match for ")
            print(qso)
            print()


def combine_qsos(qso_list, qsl_cards):
    logging.debug('combining dxcc qsl card info')
    # this is brute-force right now.  it could be made faster.
    updated_qsls = []
    added_qsls = []
    for card in qsl_cards:
        found = False
        for qso in qso_list:
            if qso['call'] == card['call'] and qso['qso_date'] == card['qso_date'] and qso['band'] == card['band']:
                found = True
                if qso.get('dxcc') == None:
                    # print('QSO to QSL: %s %s %s %s' % (card['call'], card['band'], card['qso_date'], card['country']))
                    qso['dxcc'] = card['dxcc']
                    qso['country'] = card['country']
                    qso['credit_granted'] = card['credit_granted']
                    qso['app_lotw_deleted_entity'] = card['app_lotw_deleted_entity']
                    qso['app_lotw_credit_granted'] = card['app_lotw_credit_granted']
                    qso['qsl_rcvd'] = 'y'
                    qso['app_n1kdo_qso_combined'] = 'qslcards detail added'
                    updated_qsls.append(qso);
        if not found:
            # print('QSL added from card: %s %s %s %s' % (card['call'], card['band'], card['qso_date'], card['country']))
            card['app_n1kdo_qso_combined'] = 'qslcards QSL added'
            card['qsl_rcvd'] = 'y'
            added_qsls.append(card);
            qso_list.append(card)
    logging.info('updated %d QSL from cards, added %d QSLs from cards' % ( len(updated_qsls), len(added_qsls)))
    return qso_list


def main():
    print('N1KDO\'s LoTW ADIF analyzer version %s' % __version__)
    qso_list = None
    qsl_cards = None

    # uncomment these next ~8 lines to test
    if True:
        callsign = 'n1kdo'
        lotw_filename = callsign + '.adif'
        cards_filename = callsign + '-cards.adif'
        qso_list = adif.read_adif_file(lotw_filename)
        qsl_cards = adif.read_adif_file(cards_filename)

    while qso_list is None:
        print('If you already have a downloaded ADIF data file from LoTW, that can be used,')
        print('otherwise, this program will get the data from LoTW for you, and can optionally')
        print('create an ADIF data file for subsequent analysis.')
        print()
        have_adif = get_yes_no('Do you have a LoTW ADIF file? [y/n] : ')
        if have_adif:
            adif_file_name = ''
            try:
                callsign = input1('Please enter your LoTW callsign   : ')
                if callsign == '':
                    continue
                qso_list = adif.read_adif_file(callsign + '.adif')
                qsl_cards = adif.read_adif_file(callsign + '-cards.adif')
            except:
                print('Problem reading ADIF file %s' % adif_file_name)
                print()
            else:
                break
        else:
            callsign = input1('Please enter your LoTW callsign : ')
            password = input1('Please enter your LoTW password : ')
            try:
                print('Please wait while your data is fetched from Logbook of The World.')
                print('This could take several minutes.')
                qso_list = adif.get_lotw_adif(callsign, password, callsign + '.adif')
                # JEFF creation of filename from unchecked callsign is dangerous. fix this by sanitizing the callsign.
                print('Fetching DXCC confirmations...')
                qsl_cards = adif.get_qsl_cards(callsign, password, callsign + '-cards.adif')
                print('Please wait while your data is crunched.')
            except Exception as ex:
                e = sys.exc_info()[0]
                print('Problem downloading from LoTW...' + e)
                print()
            else:
                break

    qso_list = combine_qsos(qso_list, qsl_cards)
    adif.write_adif_file(qso_list, callsign + '-combined.adif')

    date_records = crunch_data('N1KDO', qso_list)
    draw_charts(date_records, callsign);

    logging.info('done.')


if __name__ == '__main__':
    main()
