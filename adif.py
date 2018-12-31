import logging
import re
import sys
import urllib.request, urllib.parse, urllib.error

"""
adif.py -- read/write/fetch from LoTW 
adif data is stored with each qso as a dict, 
  the key name is the adif field name, and
  the value is the field value.
There are no special checks for correctness.
field length and type data is ignored on read, 
and no type data is emitted when new adif is created.

you probably should not use this.  "it works for me."
"""


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
        adif_file = None

    data = urllib.parse.urlencode(params)
    req = urllib.request.Request(url + '?' + data)
    response = urllib.request.urlopen(req)
    for line in response:
        try:
            line = line.decode('iso-8859-1')
        except Exception as inst:
            print()
            print('...problem')
            print(line)
            e = sys.exc_info()[0]
            print('Problem downloading from LoTW...' + e)
            pass

        line = line.strip()
        if first_line:
            if 'ARRL Logbook of the World' not in line:
                print(line)
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
                print(title)
        else:
            return str(match.group(1)).lower(), None
    return None, None


def read_adif_file(adif_file_name):
    logging.debug('read_adif_file %s' % adif_file_name)
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
    logging.debug('read %d records from %s' % (len(qsos), adif_file_name))
    return qsos


def write_adif_field(key, item):
    if item is not None:
        ss = str(item)
        return '<{0}:{1}>{2}\n'.format(key, len(ss), ss)
    else:
        return '<{0}>\n'.format(key)


def write_adif_file(qsos, adif_file_name):
    logging.debug('write_adif_file %s' % adif_file_name)
    save_keys = ['app_lotw_mode',
                 'app_lotw_modegroup',
                 'app_n1kdo_qso_combined',
                 'band',
                 'call',
                 'country',
                 'dxcc',
                 'gridsquare',
                 'mode',
                 'qso_date',
                 'qsl_rcvd',
                 ]
    ignore_keys = ['app_lotw_2xqsl',
                   'app_lotw_dxcc_application_nr',
                   'app_lotw_cqz_inferred',
                   'app_lotw_cqz_invalid',
                   'app_lotw_credit_granted',
                   'app_lotw_deleted_entity',
                   'app_lotw_dxcc_entity_status',
                   'app_lotw_dxcc_processed_dtg',
                   'app_lotw_npsunit',
                   'app_lotw_gridsquare_invalid',
                   'app_lotw_ituz_inferred',
                   'app_lotw_ituz_invalid',
                   'app_lotw_qslmode',
                   'band_rx',
                   'cqz', 'credit_granted',
                   'cnty',
                   'freq',
                   'freq_rx',
                   'iota',
                   'ituz',
                   'state',
                   'pfx',
                   'qslrdate',
                   'time_on',
                   ]
    with open(adif_file_name, 'w') as f:
        f.write('n1kdo lotw-qso-analyzer adif (?) compatible file\n\n')
        f.write(write_adif_field('programid', 'n1kdo log analyzer'))
        f.write('<eoh>\n\n')
        for qso in qsos:
            for key, value in qso.items():
                if key in save_keys:
                    f.write(write_adif_field(key, value))
                else:
                    if key not in ignore_keys:
                        logging.warning('not saving %s %s' % (key, value))
            f.write('<eor>\n\n')
    logging.debug('wrote_adif_file %s' % adif_file_name)
