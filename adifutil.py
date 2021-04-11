#!/usr/bin/python

import datetime
import adif


def convert_qso_date(d):
    return datetime.datetime.strptime(d, '%Y%m%d%H%M%S')


def safe_get(d, k):
    result = d.get(k)
    if result is None:
        return ""
    return result


def main():
    fn = 'w1cum.adif'
    start_of_contest = datetime.datetime.strptime("20190622180000", '%Y%m%d%H%M%S')
    end_of_contest = datetime.datetime.strptime("20190623180000", '%Y%m%d%H%M%S')
    qsos = adif.read_adif_file(fn)
    band_totals = {}

    num_qsos = 0
    for qso in qsos:
        dt = safe_get(qso, 'qso_date')
        tm = safe_get(qso, 'time_on')
        d = convert_qso_date(dt+tm)
        if (d >= start_of_contest) and (d < end_of_contest):
            num_qsos += 1
            band = safe_get(qso, 'band')
            if band_totals.get(band) is None:
                band_totals[band] = 0
            band_totals[band] += 1
    print('%d qsos' % num_qsos)
    bands = ['80m', '40m', '20m', '15m', '10m', '6m']
    for band in bands:
        bt = band_totals.get(band)
        if bt is None:
            bt = 0
        print("%4s : %5d " % (band, bt))


if __name__ == '__main__':
    main()
