import datetime
import logging
import numpy as np
import matplotlib
from matplotlib.dates import DateFormatter, YearLocator, MonthLocator, DayLocator, HourLocator

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


class QsoChart:

    def __init__(self, title='untitled', filename=None, tight_layout=True):
        self.title = title
        self.filename = filename
        self.bin_data = None
        self.fig = None
        self.ax = None
        self.WIDTH_INCHES = 16
        self.HEIGHT_INCHES = 9
        self.FG = 'k'
        self.BG = 'w'

        if tight_layout:
            self.fig = plt.Figure(figsize=(self.WIDTH_INCHES, self.HEIGHT_INCHES), dpi=100, tight_layout=True)
        else:
            self.fig = plt.Figure(figsize=(self.WIDTH_INCHES, self.HEIGHT_INCHES), dpi=100)
        dts = datetime.datetime.now().strftime('%Y-%m-%d')
        self.fig.text(1.0, 0.0, dts, fontsize=12, color='black',
                      ha='right', va='bottom', transform=self.fig.transFigure)
        return

    def get_figure(self):
        return self.fig

    def save_chart(self):
        if self.filename is not None:
            logging.info(f'writing image file {self.filename}')
            canvas = agg.FigureCanvasAgg(self.fig)
            canvas.draw()
            self.fig.savefig(self.filename, facecolor=BG)
        else:
            plt.show()
        plt.close(self.fig)


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

        self.data = []
        for i in range(self.num_bins):
            ts = self.offset + i * self.bin_size
            dt = datetime.datetime.utcfromtimestamp(ts)
            self.data.append({'datetime': dt})
        logging.info(f'num_days = {self.num_days}')
        logging.info(f'num_bins = {self.num_bins}')
        logging.info(f'offset = {self.offset}')
        logging.info(f'bin_size = {self.bin_size}')

    def get_bin(self, data_datetime):
        ts = int(data_datetime.timestamp())
        ts = ts - self.offset
        bin_num = ts // self.bin_size
        return bin_num

    def get_bin_size(self):
        return datetime.timedelta(seconds=self.bin_size)


class BinnedQSOChart(QsoChart):
    def __init__(self, bin_data, title, filename=None, start_date=None, end_date=None, max_y=0):
        super().__init__(title, filename, True)
        self.bin_data = bin_data
        self.start_date = start_date
        self.end_date = end_date
        self.maxy = max_y

        if start_date is None:
            bins_start_date = self.bin_data.data[0].get('datetime')
            if bins_start_date is not None:
                start_date = bins_start_date.date()
        if end_date is None:
            bins_end_date = self.bin_data.data[-1].get('datetime')
            if bins_end_date is not None:
                end_date = bins_end_date.date() + datetime.timedelta(days=1)  # get one more day

        self.ax = self.fig.add_subplot(111, facecolor=self.BG)
        self.ax.set_title(self.title, color=self.FG, size='xx-large', weight='bold')

        self.ax.set_xlim(start_date, end_date)
        if max_y != 0:
            self.ax.set_ylim(0, max_y)
        self.ax.grid(True)

        self.ax.tick_params(axis='y', colors=FG, which='both', direction='out')
        self.ax.tick_params(axis='x', colors=FG, which='both', direction='out', top=False)
        self.ax.set_ylabel('QSOs', color=FG, size='x-large', weight='bold')

        self.ax.spines['left'].set_color(FG)
        self.ax.spines['right'].set_color(FG)
        self.ax.spines['top'].set_color(FG)
        self.ax.spines['bottom'].set_color(FG)

        if self.bin_data.num_days <= 31:  # month or less
            self.ax.xaxis.set_major_locator(DayLocator())
            self.ax.xaxis.set_minor_locator(HourLocator())
            self.ax.xaxis.set_major_formatter(DateFormatter('%m-%d'))
        elif bin_data.num_bins <= 366:  # a year or less
            self.ax.xaxis.set_major_locator(MonthLocator())
            self.ax.xaxis.set_major_formatter(DateFormatter('%b %y'))
        else:
            self.ax.xaxis.set_major_locator(YearLocator())
            self.ax.xaxis.set_minor_locator(MonthLocator())
            self.ax.xaxis.set_major_formatter(DateFormatter('%Y'))
        self.ax.set_xlabel('Date', color=FG, size='x-large', weight='bold')

    def get_axis(self):
        return self.ax


def no_zero(n):
    if n == 0:
        return None
    return n


class QSOsByDateChart(BinnedQSOChart):
    def __init__(self, bin_data, title, filename=None, start_date=None, end_date=None):
        logging.info(f'drawing QSOsByDateChart "{title}" to {filename}.')
        # calculate some data before setting up the chart...
        qso_dates = []
        data = [[], [], [], []]
        biggest = 0
        worked = 0
        confirmed = 0
        challenge = 0
        dxcc = 0
        for bin_dict in bin_data.data:
            bin_date = bin_dict['datetime']
            worked = bin_dict['total_worked']
            confirmed = bin_dict['total_confirmed']
            challenge = bin_dict['total_challenge']
            dxcc = bin_dict['total_dxcc']
            qso_dates.append(bin_date)
            data[0].append(dxcc)
            data[1].append(challenge - dxcc)
            data[2].append(confirmed - challenge)
            data[3].append(worked - confirmed)
            if worked > biggest:
                biggest = worked

        scale_factor = 1000
        upper = (biggest // scale_factor + 1) * scale_factor

        super().__init__(bin_data, title, filename, start_date, end_date, upper)

        plot_dates = matplotlib.dates.date2num(qso_dates)
        colors = ['#ffff00', '#ff9933', '#cc6600', '#660000']
        labels = [f'{dxcc} dxcc', f'{challenge} challenge', f'{confirmed} confirmed', f'{worked} logged']

        self.ax.stackplot(plot_dates, data[0], data[1], data[2], data[3], labels=labels, colors=colors, linewidth=0.2)

        self.ax.set_ylabel('QSOs', color=FG, size='x-large', weight='bold')

        legend = self.ax.legend(loc='upper left', facecolor=BG, edgecolor=FG)
        for text in legend.get_texts():
            text.set_color(FG)

        self.save_chart()


class DXCCQSOsChart(BinnedQSOChart):
    def __init__(self, bin_data, title, filename=None, start_date=None, end_date=None):
        logging.info(f'drawing DXCCQSOsChart "{title}" to {filename}.')
        # calculate some data before setting up the chart...
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
        plot_dates = matplotlib.dates.date2num(dates)

        super().__init__(bin_data, title, filename, start_date, end_date, 0)

        axb = self.ax.twinx()
        self.ax.set_ylim(0, 350)
        axb.set_ylim(0, 3500)

        lines1 = self.ax.plot_date(plot_dates, total_dxcc_data,
                                   fmt='r-',
                                   mew=0, markersize=5, label='Current DXCCs ({:d})'.format(number_dxcc))
        lines2 = axb.plot_date(plot_dates, total_challenge_data,
                               fmt='g:',
                               mew=0, markersize=5, label='Challenge ({:d})'.format(number_challenge))

        self.ax.set_ylabel('DXCCs', color='r', size='x-large', weight='bold')
        yticks = [0, 50, 100, 150, 200, 250, 300, 331, 340, 350]
        labels = ['0', '50', '100', '150', '200', '250', '300', 'Honor Roll', '340', '350']
        self.ax.set_yticks(yticks, labels)
        self.ax.tick_params(axis='y', colors=FG, which='major', direction='out', right=False, labelcolor='r')
        self.ax.tick_params(axis='x', colors=FG, which='both', direction='out', top=False)

        axb.set_ylabel('Challenge', color='g', size='x-large', weight='bold')
        challenge_ticks = [500, 1000, 1500, 2000, 2500, 3000, 3500]
        axb.set_yticks(challenge_ticks)
        axb.tick_params(axis='y', colors=FG, which='major', direction='out', left=False, labelcolor='g')
        axb.tick_params(axis='y', colors=FG, which='minor', direction='out', left=False, labelcolor='g', pad=-72)

        lines = lines1 + lines2
        labels = [str(line.get_label()) for line in lines]

        legend = self.ax.legend(lines, labels, loc='upper left', numpoints=1, facecolor=BG, edgecolor=FG)
        for text in legend.get_texts():
            text.set_color(FG)

        self.save_chart()


class VuccFfmaQSOsChart(BinnedQSOChart):
    def __init__(self, bin_data, title, filename=None, start_date=None, end_date=None):
        logging.info(f'drawing VuccFfmaQSOsChart "{title}" to {filename}.')
        # calculate some data before setting up the chart...
        dates = []
        total_vucc_data = []
        total_ffma_data = []

        for bin_dict in bin_data.data:
            qso_date = bin_dict['datetime']
            dates.append(qso_date)
            total_vucc_data.append(bin_dict['total_vucc'])
            total_ffma_data.append(bin_dict['total_ffma'])

        number_vucc = bin_data.data[-1]['total_vucc']
        number_ffma = bin_data.data[-1]['total_ffma']

        plot_dates = matplotlib.dates.date2num(dates)

        limit_factor = 500
        limit = (int(number_vucc / limit_factor) + 1) * limit_factor

        super().__init__(bin_data, title, filename, start_date, end_date, limit)

        self.ax.set_ylim(0, limit)
        axb = self.ax.twinx()
        axb.set_ylim(0, 500)  # 488 FFMA grids

        lines1 = self.ax.plot_date(plot_dates, total_vucc_data,
                                   fmt='r-',
                                   mew=0, markersize=5, label='Confirmed VUCC QSOs ({:d})'.format(number_vucc))
        lines2 = axb.plot_date(plot_dates, total_ffma_data,
                               fmt='g:',
                               mew=0, markersize=5, label='Confirmed FFMA QSOs({:d})'.format(number_ffma))

        self.ax.tick_params(axis='y', colors=FG, which='major', direction='out', right=False, labelcolor='r')
        step = 50 if limit < 1000 else 100
        yticks = [i for i in range(0, limit + 1, step)]
        self.ax.set_yticks(yticks)

        self.ax.set_ylabel('Confirmed VUCC QSOs', color='r', size='x-large', weight='bold')
        axb.set_ylabel('Confirmed FFMA QSOs', color='g', size='x-large', weight='bold')
        ffma_ticks = [0, 50, 100, 150, 200, 250, 300, 350, 400, 450, 488]
        ffma_tick_labels = ['0', '50', '100', '150', '200', '250', '300', '350', '400', '450', 'FFMA 488']
        axb.tick_params(axis='y', colors=FG, which='major', direction='out', left=False, labelcolor='g')
        axb.set_yticks(ffma_ticks, ffma_tick_labels)
        axb.tick_params(axis='y', colors=FG, which='minor', direction='out', left=False, labelcolor='g', pad=-72)

        lines = lines1 + lines2
        labels = [str(line.get_label()) for line in lines]

        legend = self.ax.legend(lines, labels, loc='upper left', numpoints=1, facecolor=BG, edgecolor=FG)
        for text in legend.get_texts():
            text.set_color(FG)

        self.save_chart()


class ChallengeBandsByDateChart(BinnedQSOChart):
    def __init__(self, bin_data, title, filename=None, start_date=None, end_date=None):
        logging.info(f'drawing ChallengeBandsByDateChart "{title}" to {filename}.')
        # calculate some data before setting up the chart...
        challenge_bands = ['160M', '80M', '40M', '30M', '20M', '17M', '15M', '12M', '10M', '6M']
        colors = ['r', 'g', 'b', 'c', 'r', '#990099', '#ff6600', '#00ff00', '#663300', '#00ff99']
        line_styles = [':', '--', '--', '-', '--', ':', '--', ':', '--', '--']

        data = [[], [], [], [], [], [], [], [], [], [], []]
        totals = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        biggest = 0
        for bin_dict in bin_data.data:
            bin_date = bin_dict['datetime']
            data[0].append(bin_date)
            for i in range(0, len(challenge_bands)):
                totals[i] += bin_dict['challenge_' + challenge_bands[i]]
                if totals[i] > biggest:
                    biggest = totals[i]
                data[i + 1].append(totals[i])

        scale_factor = 50
        y_end = (int(biggest / scale_factor) + 1) * scale_factor
        plot_dates = matplotlib.dates.date2num(data[0])

        super().__init__(bin_data, title, filename, start_date, end_date, 0)

        self.ax.set_ylim(0, y_end)

        step = scale_factor  # 50 if y_end < 1000 else 100
        yticks = [i for i in range(0, y_end + 1, step)]
        self.ax.set_yticks(yticks)

        for i in range(0, len(challenge_bands)):
            self.ax.plot_date(plot_dates, data[i + 1],
                              color=colors[i],
                              fmt=line_styles[i],
                              mew=0, markersize=5, label='{:s} ({:d})'.format(challenge_bands[i], totals[i]))

        legend = self.ax.legend(loc='upper left', numpoints=1, facecolor=BG, edgecolor=FG)
        for text in legend.get_texts():
            text.set_color(FG)

        self.save_chart()


class QSOsRateChart(BinnedQSOChart):
    def __init__(self, bin_data, title, filename=None, start_date=None, end_date=None):
        logging.info(f'drawing QSOsRateChart "{title}" to {filename}.')
        # calculate some data before setting up the chart...
        plot_dates = []
        data = [[], [], [], []]
        plot_widths = []
        maxy = 0
        for bin_dict in bin_data.data:
            bin_date = bin_dict['datetime'].date()
            if (start_date is None or bin_date >= start_date) and (end_date is None or bin_date <= end_date):
                # compute stacked bar sizes
                new_dxcc = bin_dict['new_dxcc']
                challenge = bin_dict['challenge'] - bin_dict['new_dxcc']
                confirmed = bin_dict['confirmed'] - bin_dict['challenge']
                worked = bin_dict['worked'] - bin_dict['confirmed']
                plot_dates.append(np.datetime64(bin_date))
                data[0].append(new_dxcc)
                data[1].append(challenge)
                data[2].append(confirmed)
                data[3].append(worked)
                plot_widths = np.timedelta64(bin_data.bin_size, 's')

        for i in range(0, len(data[0])):
            total = data[0][i] + data[1][i] + data[2][i] + data[3][i]
            if total > maxy:
                maxy = total

        super().__init__(bin_data, title, filename, start_date, end_date, 0)

        offsets = np.zeros((len(plot_dates)), np.int32)
        colors = ['#ff3333', '#cccc00', '#009900', '#000099']
        labels = ['Logged', 'Confirmed', 'Challenge', 'DXCC Entity']

        d = np.array(data[0])
        self.ax.bar(plot_dates, d, plot_widths, bottom=offsets, color=colors[0], label=labels[3])
        offsets += d
        d = np.array(data[1])
        self.ax.bar(plot_dates, d, plot_widths, bottom=offsets, color=colors[1], label=labels[2])
        offsets += d
        d = np.array(data[2])
        self.ax.bar(plot_dates, d, plot_widths, bottom=offsets, color=colors[2], label=labels[1])
        offsets += d
        d = np.array(data[3])
        self.ax.bar(plot_dates, d, plot_widths, bottom=offsets, color=colors[3], label=labels[0])

        legend = self.ax.legend(loc='upper left', numpoints=1, facecolor=BG, edgecolor=FG)
        for text in legend.get_texts():
            text.set_color(FG)

        self.save_chart()


class QSOsByBandRateChart(BinnedQSOChart):
    def __init__(self, bin_data, title, filename=None, start_date=None, end_date=None):
        logging.info(f'drawing QSOsByBandRateChart "{title}" to {filename}.')
        # calculate some data before setting up the chart...
        challenge_bands = ['160M', '80M', '40M', '30M', '20M', '17M', '15M', '12M', '10M', '6M']
        colors = ['violet', 'g', 'b', 'c', 'r', '#ffff00', '#ff6600', '#00ff00', '#663300', '#00ffff']

        data = [[], [], [], [], [], [], [], [], [], []]
        plot_dates = []
        plot_widths = []

        for bin_dict in bin_data.data:
            bin_date = bin_dict['datetime'].date()
            if (start_date is None or bin_date >= start_date) and (end_date is None or bin_date <= end_date):
                plot_dates.append(np.datetime64(bin_date))
                plot_widths.append(np.timedelta64(bin_data.bin_size, 's'))
                for i in range(0, len(challenge_bands)):
                    band_count = bin_dict[challenge_bands[i]]
                    data[i].append(band_count)

        maxy = 0
        for i in range(0, len(data[0])):
            total = 0
            for j in range(0, len(challenge_bands)):
                total += data[j][i]
            if total > maxy:
                maxy = total

        super().__init__(bin_data, title, filename, start_date, end_date, maxy)

        offset = np.zeros((len(plot_dates)), dtype=np.int32)
        for i in range(0, len(challenge_bands)):
            ta = np.array(data[i])
            self.ax.bar(plot_dates, ta, width=plot_widths, bottom=offset, color=colors[i], label=challenge_bands[i])
            # ax.bar(dates, ta, bottom=offset, color=colors[i], label=challenge_bands[i])
            offset += ta

        legend = self.ax.legend(loc='upper left', numpoints=1, facecolor=BG, edgecolor=FG)
        for text in legend.get_texts():
            text.set_color(FG)

        self.save_chart()


class QSOsByModeRateChart(BinnedQSOChart):
    def __init__(self, bin_data, title, filename=None, start_date=None, end_date=None):
        logging.info(f'drawing QSOsByModeRateChart "{title}" to {filename}.')
        # calculate some data before setting up the chart...
        colors = ['r', 'g', 'c', 'b']
        data = [[], [], [], []]
        plot_dates = []
        plot_widths = []

        for bin_dict in bin_data.data:
            bin_date = bin_dict['datetime'].date()
            if (start_date is None or bin_date >= start_date) and (end_date is None or bin_date <= end_date):
                plot_dates.append(np.datetime64(bin_date))
                plot_widths.append(np.timedelta64(bin_data.bin_size, 's'))
                for i in range(0, len(adif.MODES)):
                    mode_count = bin_dict[adif.MODES[i]]
                    data[i].append(mode_count)

        maxy = 0
        for i in range(0, len(data[0])):
            total = 0
            for j in range(0, len(adif.MODES)):
                total += data[j][i]
            if total > maxy:
                maxy = total

        super().__init__(bin_data, title, filename, start_date, end_date, maxy)

        offset = np.zeros((len(plot_dates)), dtype=np.int32)
        for i in range(0, len(adif.MODES)):
            ta = np.array(data[i])
            self.ax.bar(plot_dates, ta, plot_widths, bottom=offset, color=colors[i], label=adif.MODES[i])
            offset += ta

        legend = self.ax.legend(loc='upper left', numpoints=1, facecolor=BG, edgecolor=FG)
        for text in legend.get_texts():
            text.set_color(FG)

        self.save_chart()


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
    return sgeom.box(lon, lat, lon + 2, lat + 1)


class QSOsMap(QsoChart):
    def __init__(self, qsos, title, filename=None, start_date=None, end_date=None, confirmed_only=True):
        logging.info(f'drawing QSOsMap "{title}" to {filename}.')
        super().__init__(title, filename, tight_layout=False)
        grids = {}
        most = 0
        for qso in qsos:
            if start_date is not None:
                qso_date_string = qso.get('qso_date')
                qso_date = datetime.datetime.strptime(qso_date_string, '%Y%m%d').date()
                if qso_date < start_date or qso_date >= end_date:
                    continue
            qsl_received = (qso.get('qsl_rcvd') or 'N').lower()
            if not confirmed_only or qsl_received != 'n':
                grid = qso.get('gridsquare')
                if grid is not None:
                    if qsl_received == 'n':
                        logging.info('QSO has grid but is not confirmed.')
                    grid = grid[0:4].upper()
                    if grid not in grids:
                        grids[grid] = 0
                    grids[grid] += 1
                    if grids[grid] > most:
                        most = grids[grid]

        projection = ccrs.PlateCarree(central_longitude=-110)
        # noinspection PyTypeChecker
        ax = self.fig.add_axes((0, 0, 1, 1), projection=projection)
        ax.set_title(title, color=self.FG, size='xx-large', weight='bold')

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

        self.save_chart()
