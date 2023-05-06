import datetime
import logging
import numpy as np
import matplotlib
from matplotlib.dates import DateFormatter, YearLocator, MonthLocator, DayLocator, HourLocator
from matplotlib.ticker import FormatStrFormatter

import matplotlib.pyplot as plt
import matplotlib.backends.backend_agg as agg

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import shapely.geometry as sgeom

import adif

WIDTH_INCHES = 16
HEIGHT_INCHES = 9
FG = 'k'
BG = 'w'


class BinnedQSOData:

    def __init__(self, first_datetime, last_datetime):
        self.offset = int(first_datetime.timestamp())
        days = (last_datetime - first_datetime)
        self.num_days = days.days + 1

        if self.num_days <= 7:  # a week
            self.bin_size = 3600  # 1 hour
            self.num_bins = self.num_days * 24 + 1
            self.bin_size = 60 * 30  # 1/2 hour
            self.num_bins = self.num_days * 24 * 2 + 1
        elif self.num_days <= 28:  # a month
            self.bin_size = 3600 * 12  # 12 hours
            self.num_bins = self.num_days * 2 + 1
        elif self.num_days <= 365:  # 1 year
            self.bin_size = 86400  # 1 day
            self.num_bins = self.num_days + 1
        elif self.num_days <= 3653:  # 10 years
            self.bin_size = 86400 * 7  # 7 days
            self.num_bins = self.num_days // 7 + 1
        elif self.num_days <= 7305:  # 20 years
            self.bin_size = 86400 * 7  # 7 days
            self.num_bins = self.num_days // 7 + 1
        else:  # > 20 years
            self.bin_size = 86400 * 28  # 4 weeks
            self.num_bins = self.num_days // 28 + 1

        self.data = [{}] * self.num_bins
        for i in range(0, self.num_bins):
            ts = self.offset + i * self.bin_size
            dt = datetime.datetime.utcfromtimestamp(ts)
            self.data[i] = {'datetime': dt}
        logging.info(f'num_days = {self.num_days}')
        logging.info(f'num_bins = {self.num_bins}')
        logging.info(f'offset = {self.offset}')
        logging.info(f'bin_size = {self.bin_size}')

    def get_bin(self, data_datetime):
        ts = int(data_datetime.timestamp())
        ts = ts - self.offset
        bin_num = ts // self.bin_size
        return bin_num


def auto_scale(val):
    factor = 1
    t = val
    while t > 10:
        factor = factor * 10
        t = int(t/10)
    return (t+1) * factor


def no_zero(n):
    if n == 0:
        return None
    return n


def plot_qsos_by_date(bin_data, title, filename=None, start_date=None, end_date=None):
    """
    make the chart
    """
    logging.debug('plot_qsos_by_date(...,%s, %s)' % (title, filename))
    dates = []
    data = [[], [], [], []]
    biggest = 0
    for bin_dict in bin_data.data:
        qdate = bin_dict['datetime']
        worked = bin_dict['total_worked']
        confirmed = bin_dict['total_confirmed']
        challenge = bin_dict['total_challenge']
        dxcc = bin_dict['total_dxcc']
        dates.append(qdate)
        data[0].append(dxcc)
        data[1].append(challenge - dxcc)
        data[2].append(confirmed - challenge)
        data[3].append(worked - confirmed)
        if worked > biggest:
            biggest = worked

    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100, tight_layout=True)
    dts = datetime.datetime.now().strftime('%Y-%m-%d')
    fig.text(1.0, 0.0, dts, fontsize=12, color='black', ha='right', va='bottom', transform=fig.transFigure)

    ax = fig.add_subplot(111, facecolor=BG)

    ax.set_title(title, color=FG, size='xx-large', weight='bold')

    dates = matplotlib.dates.date2num(dates)
    colors = ['#ffff00', '#ff9933', '#cc6600', '#660000']
    labels = [f'{dxcc} dxcc', f'{challenge} challenge', f'{confirmed} confirmed', f'{worked} logged']
    if start_date is None:
        start_date = dates[0]
    if end_date is None:
        end_date = dates[-1]
    ax.set_xlim(start_date, end_date)

    scale_factor = 1000
    upper = (biggest // scale_factor + 1) * scale_factor

    ax.set_ylim(bottom=0, top=upper)  # auto_scale(biggest))

    ax.stackplot(dates, data[0], data[1], data[2], data[3], labels=labels, colors=colors, linewidth=0.2)
    ax.grid(True)

    ax.spines['left'].set_color(FG)
    ax.spines['right'].set_color(FG)
    ax.spines['bottom'].set_color(FG)
    ax.spines['top'].set_color(FG)
    ax.tick_params(axis='y', colors=FG, which='both', direction='out', left=True, right=True)
    ax.tick_params(axis='x', colors=FG, which='both', direction='out', top=False)
    ax.set_ylabel('QSOs', color=FG, size='x-large', weight='bold')

    if bin_data.num_days <= 28:
        ax.xaxis.set_major_locator(DayLocator())
        ax.xaxis.set_minor_locator(HourLocator())
        ax.xaxis.set_major_formatter(DateFormatter('%m-%d'))
        ax.set_xlabel('Date', color=FG, size='x-large', weight='bold')
    else:
        ax.xaxis.set_major_locator(YearLocator())
        ax.xaxis.set_minor_locator(MonthLocator())
        ax.xaxis.set_major_formatter(DateFormatter('%y'))
        ax.set_xlabel('Year', color=FG, size='x-large', weight='bold')

    legend = ax.legend(loc='upper left', facecolor=BG, edgecolor=FG)
    for text in legend.get_texts():
        text.set_color(FG)

    if filename is not None:
        canvas = agg.FigureCanvasAgg(fig)
        canvas.draw()
        fig.savefig(filename, facecolor=BG)
    else:
        plt.show()
    plt.close(fig)
    logging.debug('plot_qsos_by_date(...,%s, %s) done' % (title, filename))
    return


def plot_dxcc_qsos(bin_data, title, filename=None, start_date=None, end_date=None):
    """
    make the chart
    """
    logging.debug('plot_dxcc_qsos(...,%s, %s)' % (title, filename))
    dates = []
    total_dxcc_data = []
    total_challenge_data = []

    for bin_dict in bin_data.data:
        qso_date = bin_dict['datetime']
        dates.append(qso_date)
        total_dxcc_data.append(bin_dict['total_dxcc'])
        total_challenge_data.append(bin_dict['total_challenge'])

    number_dxcc = bin_data.data[-1]['total_dxcc']
    number_challenge = bin_data.data[-1]['total_challenge']

    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100, tight_layout=True)

    dts = datetime.datetime.now().strftime('%Y-%m-%d')
    fig.text(1.0, 0.0, dts, fontsize=12, color='black', ha='right', va='bottom', transform=fig.transFigure)

    ax = fig.add_subplot(111, facecolor=BG)

    axb = ax.twinx()
    ax.set_title(title, color=FG, size='xx-large', weight='bold')

    dates = matplotlib.dates.date2num(dates)
    if start_date is None:
        start_date = dates[0]
    if end_date is None:
        end_date = dates[-1]
    ax.set_xlim(start_date, end_date)
    ax.set_ylim(0, 350)
    axb.set_ylim(0, 3500)

    lns1 = ax.plot_date(dates, total_dxcc_data,
                        fmt='r-',
                        mew=0, markersize=5, label='DXCC ({:d})'.format(number_dxcc))
    lns2 = axb.plot_date(dates, total_challenge_data,
                         fmt='g:',
                         mew=0, markersize=5, label='Challenge ({:d})'.format(number_challenge))
    ax.grid(True)

    yticks = [0, 50, 100, 150, 200, 250, 300, 350]
    ax.set_yticks(yticks)
    if False:
        minor_ticks = [340, total_dxcc_data[-1]]
        ax.set_yticks(minor_ticks, minor=True)  # current number of dxcc entities
        ax.tick_params(axis='y', which='minor', direction='in', right=False, labelcolor='r', pad=-24)
        ax.yaxis.set_minor_formatter(FormatStrFormatter('%d'))

    ax.tick_params(axis='y', colors=FG, which='major', direction='out', right=False, labelcolor='r')
    ax.tick_params(axis='x', colors=FG, which='both', direction='out', top=False)
    ax.set_ylabel('DXCCs', color='r', size='x-large', weight='bold')
    axb.set_ylabel('Challenge', color='g', size='x-large', weight='bold')
    challenge_ticks = [500, 1000, 1500, 2000, 2500, 3000, 3500]
    axb.tick_params(axis='y', colors=FG, which='major', direction='out', left=False, labelcolor='g')
    axb.set_yticks(challenge_ticks)
    if False:
        current_challenge_label_distance = total_challenge_data[-1] % 500
        #print(current_challenge_label_distance)
        if current_challenge_label_distance > 20 and current_challenge_label_distance < 480:
            axb.set_yticks([total_challenge_data[-1]], minor=True)
            axb.yaxis.set_minor_formatter(FormatStrFormatter('%d'))
    axb.tick_params(axis='y', colors=FG, which='minor', direction='out', left=False, labelcolor='g', pad=-72)

    if bin_data.num_days <= 28:
        ax.xaxis.set_major_locator(DayLocator())
        ax.xaxis.set_minor_locator(HourLocator())
        ax.xaxis.set_major_formatter(DateFormatter('%m-%d'))
        ax.set_xlabel('Date', color=FG, size='x-large', weight='bold')
    else:
        ax.xaxis.set_major_locator(YearLocator())
        ax.xaxis.set_minor_locator(MonthLocator())
        ax.xaxis.set_major_formatter(DateFormatter('%y'))
        ax.set_xlabel('Year', color=FG, size='x-large', weight='bold')

    lns = lns1 + lns2
    labs = [l.get_label() for l in lns]

    # legend = ax.legend(lns, labs, loc='upper left', numpoints=1, facecolor=BG, edgecolor=FG)
    legend = ax.legend(lns, labs, loc='lower right', numpoints=1, facecolor=BG, edgecolor=FG)
    for text in legend.get_texts():
        text.set_color(FG)

    ax.spines['left'].set_color(FG)
    ax.spines['right'].set_color(FG)
    ax.spines['top'].set_color(FG)
    ax.spines['bottom'].set_color(FG)

    axb.spines['left'].set_color(FG)
    axb.spines['right'].set_color(FG)
    axb.spines['top'].set_color(FG)
    axb.spines['bottom'].set_color(FG)

    if filename is not None:
        canvas = agg.FigureCanvasAgg(fig)
        canvas.draw()
        fig.savefig(filename, facecolor=BG)
    else:
        plt.show()
    plt.close(fig)
    logging.debug('plot_dxcc_qsos(...,%s, %s) done' % (title, filename))
    return


def plot_qsos_rate(bin_data, title, filename=None, start_date=None, end_date=None):
    """
    make the chart
    """
    logging.debug('plot_qsos_rate(...,%s, %s)' % (title, filename))

    dates = []
    data = [[], [], [], []]
    maxy = 0
    for bin_dict in bin_data.data:
        qdate = bin_dict['datetime']
        if (start_date is None or qdate >= start_date) and (end_date is None or qdate <= end_date):
            # compute stacked bar sizes
            new_dxcc = bin_dict['new_dxcc']
            challenge = bin_dict['challenge'] - bin_dict['new_dxcc']
            confirmed = bin_dict['confirmed'] - bin_dict['challenge']
            worked = bin_dict['worked'] - bin_dict['confirmed']
            dates.append(qdate)
            data[0].append(new_dxcc)
            data[1].append(challenge)
            data[2].append(confirmed)
            data[3].append(worked)

    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100, tight_layout=True)

    dts = datetime.datetime.now().strftime('%Y-%m-%d')
    fig.text(1.0, 0.0, dts, fontsize=12, color='black', ha='right', va='bottom', transform=fig.transFigure)

    ax = fig.add_subplot(111, facecolor=BG)
    ax.set_title(title, color=FG, size='xx-large', weight='bold')

    for i in range(0, len(data[0])):
        total = data[0][i] + data[1][i] + data[2][i] + data[3][i]
        if total > maxy:
            maxy = total

    dates = matplotlib.dates.date2num(dates)
    if start_date is None:
        start_date = dates[0]
    if end_date is None:
        end_date = dates[-1]
    ax.set_xlim(start_date, end_date)
    ax.set_ylim(0, auto_scale(maxy))

    offsets = np.zeros((len(dates)), np.int32)
    colors = ['#ff3333', '#cccc00', '#009900', '#000099']
    labels = ['Logged', 'Confirmed', 'Challenge', 'DXCC Entity']

    width = bin_data.num_bins / 100
    logging.debug(f'width {width}')
    logging.debug(f'num_bins {bin_data.num_bins}')

    d = np.array(data[0])
    ax.bar(dates, d, width, bottom=offsets, color=colors[0], label=labels[3])
    offsets += d
    d = np.array(data[1])
    ax.bar(dates, d, width, bottom=offsets, color=colors[1], label=labels[2])
    offsets += d
    d = np.array(data[2])
    ax.bar(dates, d, width, bottom=offsets, color=colors[2], label=labels[1])
    offsets += d
    d = np.array(data[3])
    ax.bar(dates, d, width, bottom=offsets, color=colors[3], label=labels[0])
    ax.grid(True)

    ax.tick_params(axis='y', colors=FG, which='both', direction='out')
    ax.tick_params(axis='x', colors=FG, which='both', direction='out', top=False)
    ax.set_ylabel('QSOs', color=FG, size='x-large', weight='bold')
    ax.set_ylim(0, auto_scale(maxy))

    ax.spines['left'].set_color(FG)
    ax.spines['right'].set_color(FG)
    ax.spines['top'].set_color(FG)
    ax.spines['bottom'].set_color(FG)

    if bin_data.num_days <= 28:
        ax.xaxis.set_major_locator(DayLocator())
        ax.xaxis.set_minor_locator(HourLocator())
        ax.xaxis.set_major_formatter(DateFormatter('%m-%d'))
        ax.set_xlabel('Date', color=FG, size='x-large', weight='bold')
    else:
        ax.xaxis.set_major_locator(YearLocator())
        ax.xaxis.set_minor_locator(MonthLocator())
        ax.xaxis.set_major_formatter(DateFormatter('%y'))
        ax.set_xlabel('Year', color=FG, size='x-large', weight='bold')

    legend = ax.legend(loc='upper left', numpoints=1, facecolor=BG, edgecolor=FG)
    for text in legend.get_texts():
        text.set_color(FG)

    if filename is not None:
        canvas = agg.FigureCanvasAgg(fig)
        canvas.draw()
        fig.savefig(filename, facecolor=BG)
    else:
        plt.show()
    plt.close(fig)
    logging.debug('plot_qsos_rate(...,%s, %s) done' % (title, filename))
    return


def plot_qsos_band_rate(bin_data, title, filename=None, start_date=None, end_date=None):
    """
    make the chart
    """
    logging.debug('plot_qsos_band_rate(...,%s, %s)' % (title, filename))

    challenge_bands = ['160M', '80M', '40M', '30M', '20M', '17M', '15M', '12M', '10M', '6M']
    colors = ['violet', 'g', 'b', 'c', 'r', '#ffff00', '#ff6600', '#00ff00', '#663300', '#00ffff']

    data = [[], [], [], [], [], [], [], [], [], []]
    dates = []

    for bin_dict in bin_data.data:
        qdate = bin_dict['datetime']
        if (start_date is None or qdate >= start_date) and (end_date is None or qdate <= end_date):
            dates.append(qdate)
            sum = 0
            for i in range(0, len(challenge_bands)):
                band_count = bin_dict[challenge_bands[i]]
                sum += band_count
                data[i].append(band_count)

    maxy = 0
    for i in range(0, len(data[0])):
        total = 0
        for j in range(0, len(challenge_bands)):
            total += data[j][i]
        if total > maxy:
            maxy = total

    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100, tight_layout=True)

    dts = datetime.datetime.now().strftime('%Y-%m-%d')
    fig.text(1.0, 0.0, dts, fontsize=12, color='black', ha='right', va='bottom', transform=fig.transFigure)

    ax = fig.add_subplot(111, facecolor=BG)
    ax.set_title(title, color=FG, size='xx-large', weight='bold')

    dates = matplotlib.dates.date2num(dates)
    if start_date is None:
        start_date = dates[0]
    if end_date is None:
        end_date = dates[-1]
    ax.set_xlim(start_date, end_date)
    ax.set_ylim(0, auto_scale(maxy))

    width = bin_data.num_bins / 100
    logging.debug(f'num_bins={bin_data.num_bins}')
    logging.debug(f'width={width}')

    offset = np.zeros((len(dates)), dtype=np.int32)
    for i in range(0, len(challenge_bands)):
        ta = np.array(data[i])
        ax.bar(dates, ta, width=width, bottom=offset, color=colors[i], label=challenge_bands[i])
        # ax.bar(dates, ta, bottom=offset, color=colors[i], label=challenge_bands[i])
        offset += ta

    ax.grid(True)

    ax.tick_params(axis='y', colors=FG, which='both', direction='out')
    ax.tick_params(axis='x', colors=FG, which='both', direction='out', top=False)
    ax.set_ylabel('QSOs', color=FG, size='x-large', weight='bold')
    ax.set_xlabel('Date', color=FG, size='x-large', weight='bold')

    ax.spines['left'].set_color(FG)
    ax.spines['right'].set_color(FG)
    ax.spines['top'].set_color(FG)
    ax.spines['bottom'].set_color(FG)

    if bin_data.num_days <= 28:
        ax.xaxis.set_major_locator(DayLocator())
        ax.xaxis.set_minor_locator(HourLocator())
        ax.xaxis.set_major_formatter(DateFormatter('%m-%d'))
    else:
        ax.xaxis.set_major_locator(YearLocator())
        ax.xaxis.set_minor_locator(MonthLocator())
        ax.xaxis.set_major_formatter(DateFormatter('%y'))

    legend = ax.legend(loc='upper left', numpoints=1, facecolor=BG, edgecolor=FG)
    for text in legend.get_texts():
        text.set_color(FG)

    if filename is not None:
        canvas = agg.FigureCanvasAgg(fig)
        canvas.draw()
        fig.savefig(filename, facecolor=BG)
    else:
        plt.show()
    plt.close(fig)
    logging.debug('plot_qsos_band_rate(...,%s, %s) done' % (title, filename))
    return


def plot_qsos_mode_rate(bin_data, title, filename=None, start_date=None, end_date=None):
    """
    make the chart
    """
    logging.debug('plot_qsos_mode_rate(...,%s, %s)' % (title, filename))

    colors = ['r', 'g', 'c', 'b']
    data = [[], [], [], []]
    dates = []

    for bin_dict in bin_data.data:
        qdate = bin_dict['datetime']
        if (start_date is None or qdate >= start_date) and (end_date is None or qdate <= end_date):
            dates.append(qdate)
            sum = 0
            for i in range(0, len(adif.MODES)):
                mode_count = bin_dict[adif.MODES[i]]
                sum += mode_count
                data[i].append(mode_count)

    # dates, data = make_bins(dates, data)
    maxy = 0
    for i in range(0, len(data[0])):
        total = 0
        for j in range(0, len(adif.MODES)):
            total += data[j][i]
        if total > maxy:
            maxy = total

    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100, tight_layout=True)

    dts = datetime.datetime.now().strftime('%Y-%m-%d')
    fig.text(1.0, 0.0, dts, fontsize=12, color='black', ha='right', va='bottom', transform=fig.transFigure)

    ax = fig.add_subplot(111, facecolor=BG)
    ax.set_title(title, color=FG, size='xx-large', weight='bold')

    dates = matplotlib.dates.date2num(dates)
    if start_date is None:
        start_date = dates[0]
    if end_date is None:
        end_date = dates[-1]
    ax.set_xlim(start_date, end_date)
    ax.set_ylim(0, auto_scale(maxy))

    width = bin_data.num_bins / 100
    logging.debug(f'num_bins={bin_data.num_bins}')
    logging.debug(f'width={width}')

    offset = np.zeros((len(dates)), dtype=np.int32)
    for i in range(0, len(adif.MODES)):
        ta = np.array(data[i])
        ax.bar(dates, ta, width, bottom=offset, color=colors[i], label=adif.MODES[i])
        offset += ta

    ax.grid(True)

    ax.tick_params(axis='y', colors=FG, which='both', direction='out')
    ax.tick_params(axis='x', colors=FG, which='both', direction='out', top=False)
    ax.set_ylabel('QSOs', color=FG, size='x-large', weight='bold')
    ax.set_xlabel('Date', color=FG, size='x-large', weight='bold')

    ax.spines['left'].set_color(FG)
    ax.spines['right'].set_color(FG)
    ax.spines['top'].set_color(FG)
    ax.spines['bottom'].set_color(FG)

    if bin_data.num_days <= 28:
        ax.xaxis.set_major_locator(DayLocator())
        ax.xaxis.set_minor_locator(HourLocator())
        ax.xaxis.set_major_formatter(DateFormatter('%m-%d'))
    else:
        ax.xaxis.set_major_locator(YearLocator())
        ax.xaxis.set_minor_locator(MonthLocator())
        ax.xaxis.set_major_formatter(DateFormatter('%y'))

    # ax.xaxis.set_minor_formatter(DateFormatter('%m'))
    legend = ax.legend(loc='upper left', numpoints=1, facecolor=BG, edgecolor=FG)
    for text in legend.get_texts():
        text.set_color(FG)

    if filename is not None:
        canvas = agg.FigureCanvasAgg(fig)
        canvas.draw()
        fig.savefig(filename, facecolor=BG)
    else:
        plt.show()
    plt.close(fig)
    logging.debug('plot_qsos_mode_rate(...,%s, %s) done' % (title, filename))
    return


def plot_challenge_bands_by_date(bin_data, title, filename=None, start_date=None, end_date=None):
    """
    make the chart
    """
    logging.debug('plot_challenge_bands_by_date(...,%s, %s)' % (title, filename))

    challenge_bands = ['160M', '80M', '40M', '30M', '20M', '17M', '15M', '12M', '10M', '6M']
    colors = ['r', 'g', 'b', 'c', 'r', '#990099', '#ff6600', '#00ff00', '#663300', '#00ff99']
    line_styles = [':', '--', '--', '-', '--', ':', '--', ':', '--', '--']

    data = [[], [], [], [], [], [], [], [], [], [], []]
    totals = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    biggest = 0
    for bin_dict in bin_data.data:
        qdate = bin_dict['datetime']
        data[0].append(qdate)
        for i in range(0, len(challenge_bands)):
            totals[i] += bin_dict['challenge_' + challenge_bands[i]]
            if totals[i] > biggest:
                biggest = totals[i]
            data[i + 1].append(totals[i])

    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100, tight_layout=True)

    dts = datetime.datetime.now().strftime('%Y-%m-%d')
    fig.text(1.0, 0.0, dts, fontsize=12, color='black', ha='right', va='bottom', transform=fig.transFigure)

    ax = fig.add_subplot(111, facecolor=BG)

    axb = ax.twinx()
    ax.set_title(title, color=FG, size='xx-large', weight='bold')

    dates = matplotlib.dates.date2num(data[0])
    if start_date is None:
        start_date = dates[0]
    if end_date is None:
        end_date = dates[-1]
    ax.set_xlim(start_date, end_date)

    y_end = (int(biggest / 50) + 1) * 50
    ax.set_ylim(0, y_end)

    for i in range(0, len(challenge_bands)):
        ax.plot_date(dates, data[i + 1],
                     color=colors[i],
                     fmt=line_styles[i],
                     mew=0, markersize=5, label='{:s} ({:d})'.format(challenge_bands[i], totals[i]))
    ax.grid(True)

    ax.tick_params(axis='y', colors=FG, which='both', direction='out', right=False)
    ax.tick_params(axis='x', colors=FG, which='both', direction='out', top=False)
    ax.set_ylabel('DXCCs', color=FG, size='x-large', weight='bold')
    ax.set_xlabel('Date', color=FG, size='x-large', weight='bold')

    if bin_data.num_days <= 28:
        ax.xaxis.set_major_locator(DayLocator())
        ax.xaxis.set_minor_locator(HourLocator())
        ax.xaxis.set_major_formatter(DateFormatter('%m-%d'))
    else:
        ax.xaxis.set_major_locator(YearLocator())
        ax.xaxis.set_minor_locator(MonthLocator())
        ax.xaxis.set_major_formatter(DateFormatter('%y'))

    legend = ax.legend(loc='upper left', numpoints=1, facecolor=BG, edgecolor=FG)
    for text in legend.get_texts():
        text.set_color(FG)

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

    if filename is not None:
        canvas = agg.FigureCanvasAgg(fig)
        canvas.draw()
        fig.savefig(filename, facecolor=BG)
    else:
        plt.show()
    plt.close(fig)
    logging.debug('plot_challenge_bands_by_date(...,%s, %s) done' % (title, filename))
    return


def grid_square_box(grid):
    grid = grid.upper()
    ord_A = ord('A')
    ord_0 = ord('0')
    lon = (ord(grid[0]) - ord_A) * 20
    lon += (ord(grid[2]) - ord_0) * 2
    lat = (ord(grid[1]) - ord_A) * 10
    lat += (ord(grid[3]) - ord_0)
    lon -= 180
    lat -= 90
    return sgeom.box(lon, lat, lon+2, lat+1)


def plot_map(qsos, title, filename=None, start_date=None, end_date=None, confirmed_only=True):
    """
    make the chart
    """
    logging.debug('plot_map(...,%s, %s)' % (title, filename))
    grids = {}
    most = 0
    for qso in qsos:
        qsl_rcvd = (qso.get('qsl_rcvd') or 'N').lower()
        if not confirmed_only or qsl_rcvd != 'n':
            grid = qso.get('gridsquare')
            if grid is not None:
                if qsl_rcvd == 'n':
                    logging.info('QSO has grid but is not confirmed.')
                grid = grid[0:4].upper()
                if grid not in grids:
                    grids[grid] = 0
                grids[grid] += 1
                if grids[grid] > most:
                    most = grids[grid]

    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100)

    dts = datetime.datetime.now().strftime('%Y-%m-%d')
    fig.text(1.0, 0.0, dts, fontsize=12, color='black', ha='right', va='bottom', transform=fig.transFigure)

    projection = ccrs.PlateCarree(central_longitude=-110)
    ax = fig.add_axes([0, 0, 1, 1], projection=projection)

    # ax.stock_img()
    ax.add_feature(cfeature.LAND, color='white')
    ax.add_feature(cfeature.OCEAN, color='#afdfef')
    ax.add_feature(cfeature.LAKES, color='#afdfef')
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)

    # geographic lines: add international date line, equator, etc.
    map_lines = cfeature.NaturalEarthFeature(
        category='physical',
        name='geographic_lines',
        scale='110m',
        facecolor='none',
        edgecolor='black',
        linewidth=0.5
        )
    ax.add_feature(map_lines)

    ax.set_title(title, color=FG, size='xx-large', weight='bold')

    color_palette = ['#0b0089', '#4100a0', '#6500aa', '#8500aa', '#a4109c', '#c03486',
                     '#cf4875', '#e3615f', '#f28047', '#fb9b30', '#ffb804', '#fbdc00', '#f0fb00',
                     ]
    num_colors = len(color_palette)
    scale = most / num_colors
    scale = max(scale, 1)

    for grid in grids.keys():
        if len(grid) >= 4:
            box = grid_square_box(grid)
            count = grids[grid]
            index = int(count / scale)
            index = min(index, num_colors - 1)
            clr = color_palette[index]
            ax.add_geometries([box], ccrs.PlateCarree(), alpha=0.5, facecolor=clr, edgecolor=clr, linewidth=0)

    if filename is not None:
        canvas = agg.FigureCanvasAgg(fig)
        canvas.draw()
        fig.savefig(filename, facecolor=BG)
    else:
        plt.show()
    plt.close(fig)
    logging.debug('plot_map(...,%s, %s) done' % (title, filename))
    return
