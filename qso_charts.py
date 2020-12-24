import datetime
import logging
import numpy as np
import matplotlib
from matplotlib.dates import DateFormatter, YearLocator, MonthLocator
from matplotlib.ticker import FormatStrFormatter

import matplotlib.pyplot as plt
import matplotlib.backends.backend_agg as agg

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import shapely.geometry as sgeom

WIDTH_INCHES = 16
HEIGHT_INCHES = 9
FG = 'k'
BG = 'w'


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


# JEFF this should use a python generator
def next_bin_date(d, size):
    if size == 7:
        return d + datetime.timedelta(days=7)
    else:
        month = d.month + 1
        if month > 12:
            month = 1
            year = d.year + 1
        else:
            year = d.year
        return datetime.date(year, month, 1)


def make_bins(dates, data):
    logging.debug('make_bins called with %d items' % len(dates))
    days = (dates[-1] - dates[0]).days
    if days <= 731:  # 2 years or less -- don't bin! leave as daily data
        return dates, data
    if days <= 3650:  # 10 years or less -- bin into weeks
        bin_start_date = dates[0]
        bin_size = 7
        bin_end_date = next_bin_date(bin_start_date, bin_size)
    else:  # bin into months
        bin_start_date = datetime.date(dates[0].year, dates[0].month, 1)
        bin_size = 31
        bin_end_date = next_bin_date(bin_start_date, bin_size)

    binned_dates = []
    binned_data = []

    for i in range(len(data)):
        binned_data.append([])
    bin_total = [0]*len(data)

    for i in range(0, len(dates)):
        d = dates[i]
        while d > bin_end_date:
            binned_dates.append(bin_start_date)
            for j in range(len(data)):
                binned_data[j].append(bin_total[j])
                bin_total[j] = 0
            bin_start_date = bin_end_date
            bin_end_date = next_bin_date(bin_start_date, bin_size)

        for j in range(len(data)):
            bin_total[j] += data[j][i]

    binned_dates.append(bin_start_date)
    for j in range(len(data)):
        binned_data[j].append(bin_total[j])
        bin_total[j] = 0

    logging.debug('make_bins returning %d items' % len(binned_dates))
    return binned_dates, binned_data


def plot_qsos_by_date(date_records, title, filename=None, start_date=None, end_date=None):
    """
    make the chart
    """
    logging.debug('plot_qsos_by_date(...,%s, %s)' % (title, filename))
    dates = []
    data = [[], [], [], []]
    biggest = 0
    for counts in date_records:
        qdate = counts['qdate']
        worked = counts['total_worked']
        confirmed = counts['total_confirmed']
        challenge = counts['total_challenge']
        new_dxcc = counts['total_new_dxcc']
        dates.append(qdate)
        data[0].append(new_dxcc)
        data[1].append(challenge - new_dxcc)
        data[2].append(confirmed - challenge)
        data[3].append(worked - confirmed)
        if worked > biggest:
            biggest = worked

    # {'pad': 0.10}
    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100, tight_layout=True)

    ax = fig.add_subplot(111, facecolor=BG)

    ax.set_title(title, color=FG, size='xx-large', weight='bold')

    dates = matplotlib.dates.date2num(dates)
    colors = ['#ffff00', '#ff9933', '#cc6600', '#660000']
    labels = ['dxcc', 'challenge', 'confirmed', 'worked']
    if start_date is None:
        start_date = dates[0]
    if end_date is None:
        end_date = dates[-1]
    ax.set_xlim(start_date, end_date)

    ax.set_ylim(bottom=0, top=auto_scale(biggest))

    ax.stackplot(dates, data[0], data[1], data[2], data[3], labels=labels, colors=colors, linewidth=0.2)
    ax.grid(True)

    ax.spines['left'].set_color(FG)
    ax.spines['right'].set_color(FG)
    ax.spines['bottom'].set_color(FG)
    ax.spines['top'].set_color(FG)
    ax.tick_params(axis='y', colors=FG, which='both', direction='out', left=True, right=True)
    ax.tick_params(axis='x', colors=FG, which='both', direction='out', top=False)
    ax.set_ylabel('QSOS', color=FG, size='x-large', weight='bold')
    ax.set_xlabel('Year', color=FG, size='x-large', weight='bold')

    ax.xaxis.set_major_locator(YearLocator())
    ax.xaxis.set_minor_locator(MonthLocator())
    ax.xaxis.set_major_formatter(DateFormatter('%y'))

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


def plot_dxcc_qsos(date_records, title, filename=None, start_date=None, end_date=None):
    """
    make the chart
    """
    logging.debug('plot_dxcc_qsos(...,%s, %s)' % (title, filename))
    dates = []
    total_dxcc_data = []
    total_challenge_data = []

    for counts in date_records:
        qso_date = counts['qdate']
        dates.append(qso_date)
        total_dxcc_data.append(counts['total_new_dxcc'])
        total_challenge_data.append(counts['total_challenge'])

    number_dxcc = date_records[-1]['total_new_dxcc']
    number_challenge = date_records[-1]['total_challenge']

    # {'pad': 0.10}
    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100, tight_layout=True)

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

    lns1 = ax.plot_date(dates, total_dxcc_data, color='r',
                        linestyle='-',
                        marker='None',
                        mew=0, markersize=5, label='DXCC ({:d})'.format(number_dxcc))
    lns2 = axb.plot_date(dates, total_challenge_data, color='g',
                         linestyle=':',
                         marker='None',
                         mew=0, markersize=5, label='Challenge ({:d})'.format(number_challenge))
    ax.grid(True)

    yticks = [0, 50, 100, 150, 200, 250, 300, 350]
    # yticks.append(total_dxcc_data[-1])
    ax.set_yticks(yticks)
    minor_ticks = [340, total_dxcc_data[-1]]
    ax.set_yticks(minor_ticks, minor=True)  # current number of dxcc entities
    ax.yaxis.set_minor_formatter(FormatStrFormatter('%d'))

    ax.tick_params(axis='y', colors=FG, which='both', direction='out', right=False, labelcolor='r')
    ax.tick_params(axis='x', colors=FG, which='both', direction='out', top=False)
    ax.set_ylabel('DXCCs', color='r', size='x-large', weight='bold')
    axb.set_ylabel('Challenge', color='g', size='x-large', weight='bold')
    challenge_ticks = [1000, 1500, 2000, 2500, 3000, 3500]
    axb.set_yticks(challenge_ticks)
    axb.set_yticks([total_challenge_data[-1]], minor=True)
    axb.yaxis.set_minor_formatter(FormatStrFormatter('%d'))
    axb.tick_params(axis='y', colors=FG, which='both', direction='out', left=False, labelcolor='g')
    ax.set_xlabel('Date', color=FG, size='x-large', weight='bold')

    ax.xaxis.set_major_locator(YearLocator())
    ax.xaxis.set_minor_locator(MonthLocator())
    ax.xaxis.set_major_formatter(DateFormatter('%Y'))
    lns = lns1 + lns2
    labs = [l.get_label() for l in lns]

    legend = ax.legend(lns, labs, loc='upper left', numpoints=1, facecolor=BG, edgecolor=FG)
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


def plot_qsos_rate(date_records, title, filename=None, start_date=None, end_date=None):
    """
    make the chart
    """
    logging.debug('plot_qsos_rate(...,%s, %s)' % (title, filename))

    dates = []
    data = [[], [], [], []]
    maxy = 0
    for counts in date_records:
        qdate = counts['qdate']
        if (start_date is None or qdate >= start_date) and (end_date is None or qdate <= end_date):
            # compute stacked bar sizes
            new_dxcc = counts['new_dxcc']
            challenge = counts['challenge'] - counts['new_dxcc']
            confirmed = counts['confirmed'] - counts['challenge']
            worked = counts['worked'] - counts['confirmed']
            dates.append(qdate)
            data[0].append(new_dxcc)
            data[1].append(challenge)
            data[2].append(confirmed)
            data[3].append(worked)

    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100, tight_layout=True)
    ax = fig.add_subplot(111, facecolor=BG)
    ax.set_title(title, color=FG, size='xx-large', weight='bold')

    dates, data = make_bins(dates, data)

    for i in range(0, len(data[0])):
        total = data[0][i] + data[1][i] + data[2][i] + data[3][i]
        if total > maxy:
            maxy = total
    delta = (dates[-1] - dates[0]).days

    dates = matplotlib.dates.date2num(dates)
    if start_date is None:
        start_date = dates[0]
    if end_date is None:
        end_date = dates[-1]
    ax.set_xlim(start_date, end_date)
    ax.set_ylim(0, auto_scale(maxy))

    offsets = np.zeros((len(dates)), np.int32)
    colors = ['#ff0000', '#ff6600', '#00ff00', '#0000ff']
    labels = ['DXCC Entity', 'Challenge', 'Confirmed', 'Worked']
    width = delta / 365  # guess
    d = np.array(data[3])
    ax.bar(dates, d, width, bottom=offsets, color=colors[3], label=labels[3])
    offsets += d
    d = np.array(data[2])
    ax.bar(dates, d, width, bottom=offsets, color=colors[2], label=labels[2])
    offsets += d
    d = np.array(data[1])
    ax.bar(dates, d, width, bottom=offsets, color=colors[1], label=labels[1])
    offsets += d
    d = np.array(data[0])
    ax.bar(dates, d, width, bottom=offsets, color=colors[0], label=labels[0])
    ax.grid(True)

    ax.tick_params(axis='y', colors=FG, which='both', direction='out')
    ax.tick_params(axis='x', colors=FG, which='both', direction='out', top=False)
    ax.set_ylabel('QSOs', color=FG, size='x-large', weight='bold')
    ax.set_xlabel('Date', color=FG, size='x-large', weight='bold')

    ax.set_ylim(0, auto_scale(maxy))

    ax.spines['left'].set_color(FG)
    ax.spines['right'].set_color(FG)
    ax.spines['top'].set_color(FG)
    ax.spines['bottom'].set_color(FG)

    ax.xaxis.set_major_locator(YearLocator())
    ax.xaxis.set_minor_locator(MonthLocator())
    ax.xaxis.set_major_formatter(DateFormatter('%Y'))
    # ax.xaxis.set_minor_formatter(DateFormatter('%M'))

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


def plot_qsos_band_rate(date_records, title, filename=None, start_date=None, end_date=None):
    """
    make the chart
    """
    logging.debug('plot_qsos_band_rate(...,%s, %s)' % (title, filename))

    challenge_bands = ['160M', '80M', '40M', '30M', '20M', '17M', '15M', '12M', '10M', '6M']
    colors = ['violet', 'g', 'b', 'c', 'r', '#ffff00', '#ff6600', '#00ff00', '#663300', '#00ffff']

    data = [[], [], [], [], [], [], [], [], [], []]
    dates = []

    for counts in date_records:
        qdate = counts['qdate']
        if (start_date is None or qdate >= start_date) and (end_date is None or qdate <= end_date):
            dates.append(qdate)
            sum = 0
            for i in range(0, len(challenge_bands)):
                band_count = counts[challenge_bands[i]]
                sum += band_count
                data[i].append(band_count)

    dates, data = make_bins(dates, data)
    maxy = 0
    for i in range(0, len(data[0])):
        total = 0
        for j in range(0, len(challenge_bands)):
            total += data[j][i]
        if total > maxy:
            maxy = total
    delta = (dates[-1] - dates[0]).days

    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100, tight_layout=True)
    ax = fig.add_subplot(111, facecolor=BG)
    ax.set_title(title, color=FG, size='xx-large', weight='bold')

    dates = matplotlib.dates.date2num(dates)
    if start_date is None:
        start_date = dates[0]
    if end_date is None:
        end_date = dates[-1]
    ax.set_xlim(start_date, end_date)
    ax.set_ylim(0, auto_scale(maxy))

    width = delta / 365

    offset = np.zeros((len(dates)), dtype=np.int32)
    for i in range(0, len(challenge_bands)):
        ta = np.array(data[i])
        ax.bar(dates, ta, width, bottom=offset, color=colors[i], label=challenge_bands[i])
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

    ax.xaxis.set_major_locator(YearLocator())
    ax.xaxis.set_minor_locator(MonthLocator())
    ax.xaxis.set_major_formatter(DateFormatter('%Y'))
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
    logging.debug('plot_qsos_band_rate(...,%s, %s) done' % (title, filename))
    return


def plot_challenge_bands_by_date(date_records, title, filename=None, start_date=None, end_date=None):
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
    for counts in date_records:
        qdate = counts['qdate']
        data[0].append(qdate)
        for i in range(0, len(challenge_bands)):
            totals[i] += counts['challenge_' + challenge_bands[i]]
            if totals[i] > biggest:
                biggest = totals[i]
            data[i + 1].append(totals[i])

    # {'pad': 0.10}
    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100, tight_layout=True)

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
        ax.plot_date(dates, data[i + 1], color=colors[i],
                     linestyle=line_styles[i],
                     marker='None',
                     mew=0, markersize=5, label='{:s} ({:d})'.format(challenge_bands[i], totals[i]))
    ax.grid(True)

    ax.tick_params(axis='y', colors=FG, which='both', direction='out', right=False)
    ax.tick_params(axis='x', colors=FG, which='both', direction='out', top=False)
    ax.set_ylabel('DXCCs', color=FG, size='x-large', weight='bold')
    ax.set_xlabel('Date', color=FG, size='x-large', weight='bold')

    ax.xaxis.set_major_locator(YearLocator())
    ax.xaxis.set_minor_locator(MonthLocator())
    ax.xaxis.set_major_formatter(DateFormatter('%Y'))
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


def plot_map(qsos, title, filename=None, start_date=None, end_date=None):
    """
    make the chart
    """
    logging.debug('plot_map(...,%s, %s)' % (title, filename))
    grids = {}
    most = 0
    for qso in qsos:
        grid = qso.get('gridsquare')
        if grid is not None:
            grid = grid[0:4].upper()
            if grid not in grids:
                grids[grid] = 0
            grids[grid] += 1
            if grids[grid] > most:
                most = grids[grid]

    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100)
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
