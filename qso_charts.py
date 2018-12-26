import logging
import numpy as np
import matplotlib
from matplotlib.dates import DateFormatter, YearLocator, MonthLocator
from matplotlib.ticker import FormatStrFormatter

matplotlib.use('Agg')
# Module import not at top of file.  Sorry, folks, that's how Matplotlib works.
import matplotlib.pyplot as plt
import matplotlib.backends.backend_agg as agg

WIDTH_INCHES = 12
HEIGHT_INCHES = 9
FG = 'k'
BG = 'w'

plt.ioff()

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


def plot_qsos_by_date(date_records, title, filename, start_date=None, end_date=None):
    """
    make the chart
    """
    data = [[], [], [], [], []]
    biggest = 0
    for t in date_records:
        qdate = t[0]
        counts = t[1]
        worked = counts['total_worked']
        confirmed = counts['total_confirmed']
        challenge = counts['total_challenge']
        new_dxcc = counts['total_new_dxcc']
        data[0].append(qdate)
        data[1].append(new_dxcc)
        data[2].append(challenge - new_dxcc)
        data[3].append(confirmed - challenge)
        data[4].append(worked - confirmed)
        if worked > biggest:
            biggest = worked

    logging.debug('make_plot(...,...,%s)', title)
    # {'pad': 0.10}
    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100, tight_layout=True)

    if matplotlib.__version__[0] == '1':
        ax = fig.add_subplot(111, axis_bgcolor=BG)
    else:
        ax = fig.add_subplot(111, facecolor=BG)

    ax.set_title(title, color=FG, size=48, weight='bold')

    dates = matplotlib.dates.date2num(data[0])
    colors = ['#ffff00', '#ff9933', '#cc6600', '#660000']
    labels = ['dxcc', 'challenge', 'confirmed', 'worked']
    if start_date is None:
        start_date = dates[0]
    if end_date is None:
        end_date = dates[-1]
    ax.set_xlim(start_date, end_date)

    ax.set_ylim(bottom=0, top=auto_scale(biggest))

    ax.stackplot(dates, data[1], data[2], data[3], data[4], labels=labels, colors=colors, linewidth=0.2)
    ax.grid(True)

    ax.spines['left'].set_color(FG)
    ax.spines['right'].set_color(FG)
    ax.spines['bottom'].set_color(FG)
    ax.spines['top'].set_color(FG)
    ax.tick_params(axis='y', colors=FG, which='both', direction='out')
    ax.tick_params(axis='x', colors=FG, which='both', direction='out', top=False)
    ax.set_ylabel('QSOS', color=FG, size='x-large', weight='bold')
    ax.set_xlabel('Year', color=FG, size='x-large', weight='bold')

    ax.xaxis.set_major_locator(YearLocator())
    ax.xaxis.set_minor_locator(MonthLocator())
    ax.xaxis.set_major_formatter(DateFormatter('%y'))

    legend = ax.legend(loc='upper left', facecolor=BG, edgecolor=FG)
    for text in legend.get_texts():
        text.set_color(FG)

    canvas = agg.FigureCanvasAgg(fig)
    canvas.draw()
    fig.savefig(filename, facecolor=BG)
    plt.close(fig)
    return


def plot_dxcc_qsos(date_records, title, filename, start_date=None, end_date=None):
    """
    make the chart
    """
    dates_data = []
    total_dxcc_data = []
    total_challenge_data = []

    for t in date_records:
        qso_date = t[0]
        counts = t[1]
        dates_data.append(qso_date)
        total_dxcc_data.append(counts['total_new_dxcc'])
        total_challenge_data.append(counts['total_challenge'])

    logging.debug('make_plot(...,...,%s)', title)
    # {'pad': 0.10}
    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100, tight_layout=True)

    if matplotlib.__version__[0] == '1':
        ax = fig.add_subplot(111, axis_bgcolor=BG)
    else:
        ax = fig.add_subplot(111, facecolor=BG)

    axb = ax.twinx()
    ax.set_title(title, color=FG, size=48, weight='bold')

    dates = matplotlib.dates.date2num(dates_data)
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
                        mew=0, markersize=5, label='DXCC')
    lns2 = axb.plot_date(dates, total_challenge_data, color='g',
                         linestyle=':',
                         marker='None',
                         mew=0, markersize=5, label='Challenge')
    ax.grid(True)

    ax.set_yticks([0, 50, 100, 150, 200, 250, 300, 350])
    ax.set_yticks([339], minor=True)
    ax.yaxis.set_minor_formatter(FormatStrFormatter('%d'))

    ax.tick_params(axis='y', colors=FG, which='both', direction='out', right=False, labelcolor='r')
    ax.tick_params(axis='x', colors=FG, which='both', direction='out', top=False)
    ax.set_ylabel('DXCCs', color='r', size='x-large', weight='bold')
    axb.set_ylabel('Challenge', color='g', size='x-large', weight='bold')
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

    canvas = agg.FigureCanvasAgg(fig)
    canvas.draw()
    fig.savefig(filename, facecolor=BG)
    plt.close(fig)
    return


def plot_qsos_rate(date_records, title, filename, start_date=None, end_date=None):
    """
    make the chart
    """
    dates = []
    data = [[], [], [], []]
    maxy = 0
    for t in date_records:
        qdate = t[0]
        if (start_date is None or t[0] >= start_date) and (end_date is None or t[0] <= end_date):
            # compute stacked bar sizes
            counts = t[1]
            new_dxcc = counts['new_dxcc']
            challenge = counts['challenge'] - counts['new_dxcc']
            confirmed = counts['confirmed'] - counts['challenge']
            worked = counts['worked'] - counts['confirmed']
            dates.append(qdate)
            data[0].append(new_dxcc)
            data[1].append(challenge)
            data[2].append(confirmed)
            data[3].append(worked)
            total = worked + confirmed + challenge + new_dxcc
            if total > maxy:
                maxy = total
    logging.debug('make_plot(...,...,%s)', title)
    # {'pad': 0.10}
    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100, tight_layout=True, facecolor='blue')

    if matplotlib.__version__[0] == '1':
        ax = fig.add_subplot(111, axis_bgcolor=BG)
    else:
        ax = fig.add_subplot(111, facecolor=BG)

    ax.set_title(title, color=FG, size=48, weight='bold')

    dates = matplotlib.dates.date2num(dates)
    if start_date is None:
        start_date = dates[0]
    if end_date is None:
        end_date = dates[-1]
    ax.set_xlim(start_date, end_date)
    ax.set_ylim(0, auto_scale(maxy))

    offsets = np.zeros((len(dates)), np.int32)
    colors = ['#ff0000', '#ffff00', '#00ff00', '#0000ff']
    labels = ['DXCC Entity', 'Challenge', 'Confirmed', 'Worked']
    width = 1
    d = np.array(data[0])
    ax.bar(dates, d, width, bottom=offsets, color=colors[0], label=labels[0])
    offsets += d
    d = np.array(data[1])
    ax.bar(dates, d, width, bottom=offsets, color=colors[1], label=labels[1])
    offsets += d
    d = np.array(data[2])
    ax.bar(dates, d, width, bottom=offsets, color=colors[2], label=labels[2])
    offsets += d
    d = np.array(data[3])
    ax.bar(dates, d, width, bottom=offsets, color=colors[3], label=labels[3])
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
    #ax.xaxis.set_minor_formatter(DateFormatter('%M'))

    legend = ax.legend(loc='upper left', numpoints=1, facecolor=BG, edgecolor=FG)
    for text in legend.get_texts():
        text.set_color(FG)

    canvas = agg.FigureCanvasAgg(fig)
    canvas.draw()
    fig.savefig(filename, facecolor=BG)
    plt.close(fig)
    return


def plot_qsos_band_rate(date_records, title, filename, start_date=None, end_date=None):
    """
    make the chart
    """
    challenge_bands = ['160M', '80M', '40M', '30M', '20M', '17M', '15M', '12M', '10M', '6M']
    colors = ['violet', 'g', 'b', 'c', 'r', '#ffff00', '#ff6600', '#00ff00', '#663300', '#00ffff']

    data = [[], [], [], [], [], [], [], [], [], []]
    dates = []
    biggest = 0

    for t in date_records:
        qdate = t[0]
        if (start_date is None or qdate >= start_date) and (end_date is None or qdate <= end_date):
            counts = t[1]
            dates.append(qdate)
            sum = 0
            for i in range(0, len(challenge_bands)):
                band_count = counts[challenge_bands[i]]
                sum += band_count
                data[i].append(band_count)
            if sum > biggest:
                biggest = sum


    logging.debug('make_plot(...,...,%s)', title)
    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100, tight_layout=True)

    if matplotlib.__version__[0] == '1':
        ax = fig.add_subplot(111, axis_bgcolor=BG)
    else:
        ax = fig.add_subplot(111, facecolor=BG)

    ax.set_title(title, color=FG, size=48, weight='bold')

    dates = matplotlib.dates.date2num(dates)
    if start_date is None:
        start_date = dates[0]
    if end_date is None:
        end_date = dates[-1]
    ax.set_xlim(start_date, end_date)
    ax.set_ylim(0, auto_scale(biggest))

    width = 1

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
    #ax.xaxis.set_minor_formatter(DateFormatter('%m'))
    legend = ax.legend(loc='upper left', numpoints=1, facecolor=BG, edgecolor=FG)
    for text in legend.get_texts():
        text.set_color(FG)

    canvas = agg.FigureCanvasAgg(fig)
    canvas.draw()
    fig.savefig(filename, facecolor=BG)
    plt.close(fig)
    return


def plot_challenge_bands_by_date(date_records, title, filename, start_date=None, end_date=None):
    """
    make the chart
    """

    challenge_bands = ['160M', '80M', '40M', '30M', '20M', '17M', '15M', '12M', '10M', '6M']
    colors = ['r', 'g', 'b', 'c', 'r', '#990099', '#ff6600', '#00ff00', '#663300', '#00ff99']
    line_styles = ['-', '-', '-', '-', '--', '-', ':', ':', ':', '--']

    data = [[], [], [], [], [], [], [], [], [], [], []]
    totals = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    for t in date_records:
        qdate = t[0]
        counts = t[1]
        data[0].append(qdate)
        for i in range(0, len(challenge_bands)):
            totals[i] += counts['challenge_' + challenge_bands[i]]
            data[i + 1].append(totals[i])

    logging.debug('make_plot(...,...,%s)', title)
    # {'pad': 0.10}
    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100, tight_layout=True)

    if matplotlib.__version__[0] == '1':
        ax = fig.add_subplot(111, axis_bgcolor=BG)
    else:
        ax = fig.add_subplot(111, facecolor=BG)

    axb = ax.twinx()
    ax.set_title(title, color=FG, size=48, weight='bold')

    dates = matplotlib.dates.date2num(data[0])
    if start_date is None:
        start_date = dates[0]
    if end_date is None:
        end_date = dates[-1]
    ax.set_xlim(start_date, end_date)
    ax.set_ylim(0, 200)

    for i in range(0, len(challenge_bands)):
        ax.plot_date(dates, data[i + 1], color=colors[i],
                     linestyle=line_styles[i],
                     marker='None',
                     mew=0, markersize=5, label=challenge_bands[i])
    ax.grid(True)

    ax.tick_params(axis='y', colors=FG, which='both', direction='out', right=False)
    ax.tick_params(axis='x', colors=FG, which='both', direction='out', top=False)
    ax.set_ylabel('QSOs', color=FG, size='x-large', weight='bold')
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

    canvas = agg.FigureCanvasAgg(fig)
    canvas.draw()
    fig.savefig(filename, facecolor=BG)
    plt.close(fig)
    return


