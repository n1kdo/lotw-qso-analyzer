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

import calendar
import datetime
import logging
import re
import time
import urllib
import urllib2
import sys
import matplotlib
from matplotlib.dates import DateFormatter, YearLocator, MonthLocator
from matplotlib.ticker import FormatStrFormatter
matplotlib.use('Agg')
# Module import not at top of file.  Sorry, folks, that's how Matplotlib works.
import matplotlib.pyplot as plt
import matplotlib.backends.backend_agg as agg

plt.ioff()

__author__ = 'Jeffrey B. Otterson, N1KDO'
__copyright__ = 'Copyright 2017 Jeffrey B. Otterson'
__license__ = 'Simplified BSD'
__version__ = '0.01'

logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.WARN)
logging.Formatter.converter = time.gmtime

BANDS = ['160M', '80M', '60M', '40M', '30M', '20M', '17M', '15M', '12M', '10M', '6M', '2M', '70CM']


def call_lotw(**params):
    logging.debug('Calling LoTW')
    qsos = []
    qso = {}
    first_line = True
    if params.get('url'):
        url = params.pop('url')
    else:
        url = 'https://lotw.arrl.org/lotwuser/lotwreport.adi'

    if params.get('filename'):
        adif_file_name = params.pop('filename')
        adif_file = open(adif_file_name, 'w')
    else:
        adif_file_name = None
        adif_file = None

    data = urllib.urlencode(params)
    req = urllib2.Request(url + '?' + data)
    response = urllib2.urlopen(req)
    for line in response:
        line = line.strip()
        if first_line:
            if 'ARRL Logbook of the World' not in line:
                print line
                raise Exception('ADIF download failed: ' + line)
            first_line = False
        if adif_file is not None:
            adif_file.write(line + '\n')
        item_name, item_value = adif_field(line)
        if item_value is None:  # header field.
            if item_name is not None:
                if item_name == 'eor':
                    qsos.append(qso)
                    qso = {}
                if item_name == 'eoh':
                    qsos = []
                    qso = {}
        else:
            qso[item_name] = item_value
    if adif_file is not None:
        adif_file.close()
    logging.debug('Fetched %d QSL records' % len(qsos))
    return qsos


def get_lotw_adif(username, password, filename=None):
    return call_lotw(login=username,
                     password=password,
                     filename=filename,
                     qso_query='1',
                     qso_qsl='no',
                     qso_owncall=username,
                     qso_qsldetail='yes',
                     )


def get_qsl_cards(username, password, filename=None):
    return call_lotw(url='https://lotw.arrl.org/lotwuser/logbook/qslcards.php',
                     filename=filename,
                     login=username,
                     password=password,
                     ac_acct='1')


def adif_field(s):
    if '<' in s:
        match = re.search(r'^<(.*)>(.*)$', s)
        if match.group(2):
            payload = match.group(2)
            title = match.group(1)
            match = re.search(r'^(.*?):.*$', title)
            if match is not None:
                fn = str(match.group(1)).lower()
                return fn, payload
            else:
                print title
        else:
            return str(match.group(1)).lower(), None
    return None, None


def read_adif_file(adif_file_name):
    f = open(adif_file_name)
    qso = {}
    qsos = []
    for line in iter(f):
        item_name, item_value = adif_field(line.strip())
        if item_value is None:  # header field.
            if item_name is not None:
                if item_name == 'eor':
                    qsos.append(qso)
                    qso = {}
                if item_name == 'eoh':
                    qsos = []
                    qso = {}
        else:
            qso[item_name] = item_value
    return qsos


def date_range(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)


def convert_qso_date(d):
    return datetime.datetime.strptime(d, '%Y%m%d').date()


def get_yes_no(prompt, default=None):
    while True:
        yn = raw_input(prompt)
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

    print
    print '%5d total lotw QSOs' % len(qso_list)
    qso_list.sort(key=lambda q: q['qso_date'])

    dxcc_confirmed = {}
    date_records = {}  # key is qso date.  value is [worked, confirmed]
    unique_calls = {}
    first_date = None
    last_date = None
    n_worked = 0
    n_confirmed = 0
    n_challenge = 0

    for qso in qso_list:
        qso_dxcc = qso.get('dxcc')
        qso_date = qso.get('qso_date')
        qsl_rcvd = qso.get('qsl_rcvd')
        qso_band = qso.get('band')
        # credit_granted = qso.get('app_lotw_credit_granted')
        confirmed = 0
        new_dxcc = 0
        challenge = 0
        n_worked += 1

        if qso_dxcc is not None:
            if qsl_rcvd is not None and qsl_rcvd.lower() == 'y':
                confirmed = 1
                mode = qso.get('app_lotw_modegroup')
                country = qso.get('country')
                if (qso_dxcc not in dxcc_confirmed):
                    new_dxcc = 1
                    dxcc_confirmed[qso_dxcc] = {'COUNTRY': country,
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
                counts['worked'] += 1
                counts['confirmed'] += confirmed
                counts['new_dxcc'] += new_dxcc
                counts['challenge'] += challenge
                counts[qso_band] += challenge
            else:
                counts = {'qdate': qdate, 'worked': 1, 'confirmed': confirmed, 'new_dxcc': new_dxcc, 'challenge': challenge}
                for band in BANDS:
                    counts[band] = 0
                counts[qso_band] += challenge

            date_records[qdate] = counts
            if last_date is None or qdate > last_date:
                last_date = qdate
            if first_date is None or qdate < first_date:
                first_date = qdate
        else:
            print 'DANGER WILL ROBINSON!'

        call = qso['call']
        if call not in unique_calls:
            unique_calls[call] = [qso]
        else:
            unique_calls[call].append(qso)

    print '%5d dxcc entities confirmed' % len(dxcc_confirmed)
    print '%5d days worked' % len(date_records)
    print '%5d counted confirmed' % n_confirmed
    print '%5d counted challenge' % n_challenge
    print '%5d counted worked' % n_worked
    print 'first date: ' + first_date.strftime('%Y-%m-%d')
    print 'last date: ' + last_date.strftime('%Y-%m-%d')

    # now calculate running totals by date
    total_worked = 0
    total_confirmed = 0
    total_new_dxcc = 0
    total_new_challenge = 0
    band_totals = {}
#    for band in BANDS:
#        band_totals[band] = 0

    for qdate in sorted(date_records.iterkeys()):
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
        date_records[qdate] = counts  # I think this is redundant.
        if False:
            print("%s  %5d  %5d  %5d  %5d  %5d  %5d  %5d  %5d") % (qdate.strftime('%Y-%m-%d'),
                                                                   counts['worked'],
                                                                   counts['confirmed'],
                                                                   counts['total_worked'],
                                                                   counts['total_confirmed'],
                                                                   counts['new_dxcc'],
                                                                   counts['total_new_dxcc'],
                                                                   counts['challenge'],
                                                                   counts['total_challenge'])

    # top 20 most productive days
    number_of_top_days = 20
    print
    print 'Top %d days' % number_of_top_days
    print
    most_productive = sorted(date_records.values(), key=lambda counts: counts['worked'], reverse=True)
    for i in range(0, number_of_top_days):
        print '%2d  %12s %5d' % (i+1, str(most_productive[i]['qdate']), most_productive[i]['worked'])

    plot_cumulative_qsos(date_records, callsign + ' Cumulative QSOs', callsign + '_cumulative_qsos.png')
    plot_dxcc_qsos(date_records, callsign + ' DXCC QSOs', callsign + '_dxcc_qsos.png')
    plot_qsos_rate(date_records, callsign + ' QSO Rate', callsign + '_qsos_rate.png')
    plot_qsos_band_rate(date_records, callsign + ' New DXCC Rate', callsign + '_band_rate.png')
    plot_qsos_band_counts(date_records, callsign + ' Confirmed Band Slots', callsign + '_slots.png')

    calls_by_qso = []
    for call, qso_list in unique_calls.iteritems():
        calls_by_qso.append((call, len(qso_list)))
    calls_by_qso = sorted(calls_by_qso, key=lambda count: count[1], reverse=True)

    # show top calls
    number_of_top_calls = 40
    print
    print 'Top %d calls' % number_of_top_calls
    print
    for i in range(0, number_of_top_calls):
        print "%2d %10s %3d" % (i+1, calls_by_qso[i][0], calls_by_qso[i][1])


def compare_lists(qso_list, cards_list):
    qsos = {}
    for qso in qso_list:
        key = qso['call'] + '.' + qso['qso_date'] + '.' + qso['band'] + '.' + qso['app_lotw_modegroup']
        qsos[key] = qso

    for qso in cards_list:
        key = qso['call'] + '.' + qso['qso_date'] + '.' + qso['band'] + '.' + qso.get('app_lotw_modegroup')
        if not key in qsos:
            print 'cant find a match for '
            print qso
            print


def plot_cumulative_qsos(date_records, title, filename):
    """
    make the chart
    """
    data = [[], [], [], [], []]
    for qdate in sorted(date_records.iterkeys()):
        counts = date_records[qdate]
        worked = counts['total_worked']
        confirmed = counts['total_confirmed']
        challenge = counts['total_challenge']
        new_dxcc = counts['total_new_dxcc']
        data[0].append(qdate)
        data[1].append(new_dxcc)
        data[2].append(challenge - new_dxcc)
        data[3].append(confirmed - challenge)
        data[4].append(worked - confirmed)

    logging.debug('make_plot(...,...,%s)', title)
    WIDTH_INCHES = 12
    HEIGHT_INCHES = 9
    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100, tight_layout={'pad': 0.10}, facecolor='blue')

    if matplotlib.__version__[0] == '1':
        ax = fig.add_subplot(111, axis_bgcolor='white')
    else:
        ax = fig.add_subplot(111, facecolor='white')

    ax.set_title(title, color='k', size=48, weight='bold')

    dates = matplotlib.dates.date2num(data[0])
    colors = ['#ffff00', '#ff9933', '#cc6600', '#660000']
    labels = ['dxcc', 'challenge', 'confirmed', 'worked']
    start_date = dates[0]
    end_date = dates[-1]
    ax.set_xlim(start_date, end_date)

    ax.stackplot(dates, data[1], data[2], data[3], data[4], labels=labels, colors=colors, linewidth=0.2)
    ax.grid(True)

    ax.spines['left'].set_color('k')
    ax.spines['right'].set_color('k')
    ax.spines['bottom'].set_color('k')
    ax.tick_params(axis='y', colors='k', which='both', direction='out')
    ax.tick_params(axis='x', colors='k', which='both', direction='out', top='off')
    ax.set_ylabel('QSOS', color='k', size='x-large', weight='bold')
    ax.set_xlabel('Year', color='k', size='x-large', weight='bold')

    ax.xaxis.set_major_locator(YearLocator())
    ax.xaxis.set_minor_locator(MonthLocator())
    ax.xaxis.set_major_formatter(DateFormatter('%y'))
    legend = ax.legend(loc='upper left')

    canvas = agg.FigureCanvasAgg(fig)
    canvas.draw()
    fig.savefig(filename)
    plt.close(fig)
    return


def plot_dxcc_qsos(date_records, title, filename):
    """
    make the chart
    """
    dates_data = []
    total_dxcc_data = []
    total_challenge_data = []

    for qdate in sorted(date_records.iterkeys()):
        counts = date_records[qdate]
        dates_data.append(qdate)
        total_dxcc_data.append(counts['total_new_dxcc'])
        total_challenge_data.append(counts['total_challenge'])

    logging.debug('make_plot(...,...,%s)', title)
    WIDTH_INCHES = 12
    HEIGHT_INCHES = 9
    FG = 'black'
    BG = 'white'

    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100, tight_layout={'pad': 0.10}, facecolor='blue')

    if matplotlib.__version__[0] == '1':
        ax = fig.add_subplot(111, axis_bgcolor='white')
    else:
        ax = fig.add_subplot(111, facecolor='white')

    axb = ax.twinx()
    ax.set_title(title, color='k', size=48, weight='bold')

    dates = matplotlib.dates.date2num(dates_data)
    start_date = dates[0]
    end_date = dates[-1]
    ax.set_xlim(start_date, end_date)
    ax.set_ylim(0, 350)
    axb.set_ylim(0, 3500)

    lns1 = ax.plot_date(dates, total_dxcc_data, color='r',
                 linestyle='-',
                 marker='None',
                 mew=0, markersize=5, label='DXCC')
    lns2 = axb.plot_date(dates, total_challenge_data, color='g',
                 linestyle=':',
                 marker='None',
                 mew=0, markersize=5, label='Challenge')
    ax.grid(True)

    ax.set_yticks([0,50,100,150,200,250,300,350])
    ax.set_yticks([339], minor=True)
    ax.yaxis.set_minor_formatter(FormatStrFormatter('%d'))

    ax.tick_params(axis='y', colors=FG, which='both', direction='out', right='off', labelcolor='r')
    ax.tick_params(axis='x', colors=FG, which='both', direction='out', top='off')
    ax.set_ylabel('DXCCs', color='r', size='x-large', weight='bold')
    axb.set_ylabel('Challenge', color='g', size='x-large', weight='bold')
    axb.tick_params(axis='y', colors=FG, which='both', direction='out', left='off', labelcolor='g')
    ax.set_xlabel('Date', color=FG, size='x-large', weight='bold')

    ax.xaxis.set_major_locator(YearLocator())
    ax.xaxis.set_minor_locator(MonthLocator())
    ax.xaxis.set_major_formatter(DateFormatter('%Y'))
    lns = lns1+lns2
    labs = [l.get_label() for l in lns]
    legend = ax.legend(lns, labs, loc='upper left', numpoints=1)
    legend.get_frame().set_edgecolor(FG)

    ax.spines['left'].set_color(FG)
    ax.spines['right'].set_color(FG)
    ax.spines['top'].set_color(FG)
    ax.spines['bottom'].set_color(FG)

    axb.spines['left'].set_color(FG)
    axb.spines['right'].set_color(FG)
    axb.spines['top'].set_color(FG)
    axb.spines['bottom'].set_color(FG)

    canvas = agg.FigureCanvasAgg(fig)
    canvas.draw()
    fig.savefig(filename)
    plt.close(fig)
    return


def no_zero(n):
    if n == 0:
        return None
    return n


def plot_qsos_rate(date_records, title, filename):
    """
    make the chart
    """
    data = [[], [], [], [], []]
    for qdate in sorted(date_records.iterkeys()):
        counts = date_records[qdate]
#        data[0].append(qdate)
#        data[1].append(no_zero(counts['new_dxcc']))
#        data[2].append(no_zero(counts['challenge']))
#        data[3].append(no_zero(counts['confirmed']))
#        data[4].append(no_zero(counts['worked']))

        worked = counts['worked']
        confirmed = counts['confirmed']
        challenge = counts['challenge']
        new_dxcc = counts['new_dxcc']
        data[0].append(qdate)
        data[1].append(no_zero(new_dxcc))
        data[2].append(no_zero(challenge) if new_dxcc != challenge else None)
        data[3].append(no_zero(confirmed) if confirmed != new_dxcc and confirmed !=  - challenge else None)
        data[4].append(no_zero(worked) if worked != confirmed and worked != challenge and worked != new_dxcc else None)

    logging.debug('make_plot(...,...,%s)', title)
    WIDTH_INCHES = 12
    HEIGHT_INCHES = 9
    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100, tight_layout={'pad': 0.10}, facecolor='blue')

    if matplotlib.__version__[0] == '1':
        ax = fig.add_subplot(111, axis_bgcolor='white')
    else:
        ax = fig.add_subplot(111, facecolor='white')

    ax.set_title(title, color='k', size=48, weight='bold')

    dates = matplotlib.dates.date2num(data[0])
    start_date = dates[0]
    end_date = dates[-1]
    ax.set_xlim(start_date, end_date)

    colors = ['#ffff00', '#ff9933', '#cc6600', '#660000']
    labels = ['dxcc', 'challenge', 'confirmed', 'worked']

    ax.plot_date(dates, data[4], markerfacecolor='#660000', marker='s', markersize=4, mew=0, label='worked')
    ax.plot_date(dates, data[3], markerfacecolor='#cc6600', marker='o', markersize=4, mew=0, label='confirmed')
    ax.plot_date(dates, data[2], markerfacecolor='#cccc00', marker='d', markersize=4, mew=0, label='challenge')
    ax.plot_date(dates, data[1], markerfacecolor='#9966ff', marker='^', markersize=4, mew=0, label='new dxcc')
    ax.grid(True)

    ax.tick_params(axis='y', colors='k', which='both', direction='out')
    ax.tick_params(axis='x', colors='k', which='both', direction='out', top='off')
    ax.set_ylabel('QSOs', color='k', size='x-large', weight='bold')
    ax.set_xlabel('Date', color='k', size='x-large', weight='bold')
    # ax.set_ylim(0,100)

    ax.xaxis.set_major_locator(YearLocator())
    ax.xaxis.set_minor_locator(MonthLocator())
    ax.xaxis.set_major_formatter(DateFormatter('%Y'))
    legend = ax.legend(loc='upper left', numpoints=1)

    canvas = agg.FigureCanvasAgg(fig)
    canvas.draw()
    fig.savefig(filename)
    plt.close(fig)
    return


def plot_qsos_band_rate(date_records, title, filename):
    """
    make the chart
    """
    CHALLENGE_BANDS = ['160M', '80M', '40M', '30M', '20M',     '17M',     '15M',     '12M',     '10M',      '6M']
    colors =          [   'r',   'g',   'b',   'c',   'r', '#ffff00', '#ff6600', '#00ff00', '#663300', '#00ff99']
    markers =         [   '*',   '^',   'd',   '*',   'o',       'h',       's',       'p',       's',       'd']

    data       = [[],   [],     [],    [],    [],     [],    [],    [],    [],    [],    []]

    for qdate in sorted(date_records.iterkeys()):
        counts = date_records[qdate]
        data[0].append(qdate)
        for i in range(0, len(CHALLENGE_BANDS)):
            data[i+1].append(no_zero(counts[CHALLENGE_BANDS[i]]))

    logging.debug('make_plot(...,...,%s)', title)
    WIDTH_INCHES = 12
    HEIGHT_INCHES = 9
    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100, tight_layout={'pad': 0.10}, facecolor='blue')

    if matplotlib.__version__[0] == '1':
        ax = fig.add_subplot(111, axis_bgcolor='white')
    else:
        ax = fig.add_subplot(111, facecolor='white')

    ax.set_title(title, color='k', size=48, weight='bold')

    dates = matplotlib.dates.date2num(data[0])
    labels = ['dxcc', 'challenge', 'confirmed', 'worked']
    start_date = dates[0]
    end_date = dates[-1]
    ax.set_xlim(start_date, end_date)
    #ax.set_ylim(0, 100)

    for i in range(0, len(CHALLENGE_BANDS)):
        ax.plot_date(dates, data[i+1], markerfacecolor=colors[i], marker=markers[i], mew=0, markersize=5, label=CHALLENGE_BANDS[i])
    ax.grid(True)

    ax.tick_params(axis='y', colors='k', which='both', direction='out')
    ax.tick_params(axis='x', colors='k', which='both', direction='out', top='off')
    ax.set_ylabel('QSOs', color='k', size='x-large', weight='bold')
    ax.set_xlabel('Date', color='k', size='x-large', weight='bold')

    ax.xaxis.set_major_locator(YearLocator())
    ax.xaxis.set_minor_locator(MonthLocator())
    ax.xaxis.set_major_formatter(DateFormatter('%Y'))
    legend = ax.legend(loc='upper left', numpoints=1)

    canvas = agg.FigureCanvasAgg(fig)
    canvas.draw()
    fig.savefig(filename)
    plt.close(fig)
    return


def plot_qsos_band_counts(date_records, title, filename):
    """
    make the chart
    """
    WIDTH_INCHES = 12
    HEIGHT_INCHES = 9
    FG = 'black'
    BG = 'white'

    CHALLENGE_BANDS = ['160M', '80M', '40M', '30M', '20M',     '17M',     '15M',     '12M',     '10M',      '6M']
    colors =          [   'r',   'g',   'b',   'c',   'r', '#990099', '#ff6600', '#00ff00', '#663300', '#00ff99']
    linestyle =       [   '-',   '-',   '-',   '-',  '--',       '-',       ':',       ':',       ':',      '--']

    data       = [[],   [],     [],    [],    [],     [],    [],    [],    [],    [],    []]
    totals     = [ 0,    0,      0,     0,     0,      0,     0,     0,     0,     0,     0]

    for qdate in sorted(date_records.iterkeys()):
        counts = date_records[qdate]
        data[0].append(qdate)
        for i in range(0, len(CHALLENGE_BANDS)):
            totals[i] += counts[CHALLENGE_BANDS[i]]
            data[i+1].append(totals[i])

    logging.debug('make_plot(...,...,%s)', title)
    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100, tight_layout={'pad': 0.10}, facecolor=BG)

    if matplotlib.__version__[0] == '1':
        ax = fig.add_subplot(111, axis_bgcolor=BG)
    else:
        ax = fig.add_subplot(111, facecolor=BG)

    axb = ax.twinx()
    ax.set_title(title, color=FG, size=48, weight='bold')

    dates = matplotlib.dates.date2num(data[0])
    start_date = dates[0]
    end_date = dates[-1]
    ax.set_xlim(start_date, end_date)
    ax.set_ylim(0, 200)

    for i in range(0, len(CHALLENGE_BANDS)):
        ax.plot_date(dates, data[i+1], color=colors[i],
                     linestyle=linestyle[i],
                     marker='None',
                     mew=0, markersize=5, label=CHALLENGE_BANDS[i])
    ax.grid(True)

    ax.tick_params(axis='y', colors=FG, which='both', direction='out', right='off')
    ax.tick_params(axis='x', colors=FG, which='both', direction='out', top='off')
    ax.set_ylabel('QSOs', color=FG, size='x-large', weight='bold')
    ax.set_xlabel('Date', color=FG, size='x-large', weight='bold')

    ax.xaxis.set_major_locator(YearLocator())
    ax.xaxis.set_minor_locator(MonthLocator())
    ax.xaxis.set_major_formatter(DateFormatter('%Y'))
    legend = ax.legend(loc='upper left', numpoints=1)
    #legend.get_frame().set_color((0, 0, 0, 0))
    #legend.get_frame().set_edgecolor(FG)
    for text in legend.get_texts():
        plt.setp(text, color=FG)
    ax.spines['left'].set_color(FG)
    ax.spines['right'].set_color(FG)
    ax.spines['top'].set_color(FG)
    ax.spines['bottom'].set_color(FG)

    axb.spines['left'].set_color(FG)
    axb.spines['right'].set_color(FG)
    axb.spines['top'].set_color(FG)
    axb.spines['bottom'].set_color(FG)

    axb.set_ylim(ax.get_ylim())
    axb.tick_params(axis='y', colors=FG, which='both', direction='out')

    canvas = agg.FigureCanvasAgg(fig)
    canvas.draw()
    fig.savefig(filename, facecolor=BG)
    plt.close(fig)
    return


def main():
    print 'N1KDO\'s LoTWADIF analyzer version %s' % __version__
    print
    qso_list = None
    # qso_list = read_adif_file('n1kdo.adif')
    while qso_list is None:
        print 'If you already have a downloaded ADIF data file from LoTW, that can be used,'
        print 'otherwise, this program will get the data from LoTW for you, and can optionally'
        print 'create an ADIF data file for subsequent analysis.'
        print
        have_adif = get_yes_no('Do you have a LoTW ADIF file? [y/n] : ')
        if (have_adif):
            adif_file_name = ''
            try:
                adif_file_name = raw_input('Enter the name of the ADIF file to use : ')
                if adif_file_name == '':
                    continue
                qso_list = read_adif_file(adif_file_name)
            except:
                print 'Problem reading ADIF file %s' % adif_file_name
                print
            else:
                break
        else:
            mycall = raw_input('Please enter your LoTW callsign   : ')
            password = raw_input('Please enter your LoTW password : ')
            filename = raw_input('If you want to save this data for future analysis, enter the filename now : ')
            if filename == '':
                filename = None
            try:
                print 'please wait while your data is fetched from Logbook of The World.  This could take several minutes.'
                qso_list = get_lotw_adif(mycall, password, filename)
                print 'please wait while your data is crunched.'
            except:
                e = sys.exc_info()[0]
                print 'Problem downloading from LoTW...' + e
                print
            else:
                break

    print 'Crunching data...'
    crunch_data('N1KDO', qso_list)
    print 'done.'

if __name__ == '__main__':
    main()
