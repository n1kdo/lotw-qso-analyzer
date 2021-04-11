import logging
import re
import urllib.error
import urllib.parse
import urllib.request

"""
adif.py -- read/write/fetch from LoTW  and adif files on disk.
adif data is stored with each qso as a dict,
  the key name is the adif field name, and
  the value is the field value.
There are no special checks for correctness.
field length and type data is ignored on read,
and no type data is emitted when new adif is created.

you probably should not use this.  "it works for me."
"""

"""
list of DXCC countries.
key is DXCC number
value is tuple (name, deleted)
"""
dxcc_countries = {
    '0': ('None', False),
    '1': ('Canada', False),
    '2': ('Abu Ail Is.', True),
    '3': ('Afghanistan', False),
    '4': ('Agalega & St. Brandon', False),
    '5': ('Aland Is.', False),
    '6': ('Alaska', False),
    '7': ('Albania', False),
    '8': ('Aldabra', True),
    '9': ('American Samoa', False),
    '10': ('Amsterdam & St Paul Is.', False),
    '11': ('Andaman & Nicobar Is.', False),
    '12': ('Anguilla', False),
    '13': ('Antarctica', False),
    '14': ('Armenia', False),
    '15': ('Asiatic Russia', False),
    '16': ('New Zealand Subantarctic Islands', False),
    '17': ('Aves Island', False),
    '18': ('Azerbaijan', False),
    '19': ('Bajo Nuevo', True),
    '20': ('Baker & Howland Is.', False),
    '21': ('Balearic Is.', False),
    '22': ('Palau', False),
    '23': ('Blenheim Reef', True),
    '24': ('Bouvet', False),
    '25': ('British North Borneo', True),
    '26': ('British Somaliland', True),
    '27': ('Belarus', False),
    '28': ('Canal Zone', True),
    '29': ('Canary Is.', False),
    '30': ('Celebe & Molucca Is.', True),
    '31': ('C. Kiribati (British Phoenx Is.)', False),
    '32': ('Ceuta & Melilla', False),
    '33': ('Chagos Is.', False),
    '34': ('Chatham Is.', False),
    '35': ('Christmas I.', False),
    '36': ('Clipperton I.', False),
    '37': ('Cocos I.', False),
    '38': ('Cocos (Keeling) Is.', False),
    '39': ('Comoros', True),
    '40': ('Crete', False),
    '41': ('Crozet I.', False),
    '42': ('Damao, Diu', True),
    '43': ('Desecheo I.', False),
    '44': ('Desroches', True),
    '45': ('Dodecanese', False),
    '46': ('East Malaysia', False),
    '47': ('Easter I.', False),
    '48': ('E. Kiribati (Line Is.)', False),
    '49': ('Equatorial Guinea', False),
    '50': ('Mexico', False),
    '51': ('Eritrea', False),
    '52': ('Estonia', False),
    '53': ('Ethiopia', False),
    '54': ('European Russia', False),
    '55': ('Farquhar', True),
    '56': ('Fernando De Noronha', False),
    '57': ('French Equatorial Africa', True),
    '58': ('French Indo-China', True),
    '59': ('French West Africa', True),
    '60': ('Bahamas', False),
    '61': ('Franz Josef Land', False),
    '62': ('Barbados', False),
    '63': ('French Guiana', False),
    '64': ('Bermuda', False),
    '65': ('British Virgin Is.', False),
    '66': ('Belize', False),
    '67': ('French India', True),
    '68': ('Kuwait/Saudi Arabia Neutral Zone', True),
    '69': ('Cayman Is.', False),
    '70': ('Cuba', False),
    '71': ('Galapagos Is.', False),
    '72': ('Dominican Republic', False),
    '74': ('El Salvador', False),
    '75': ('Georgia', False),
    '76': ('Guatemala', False),
    '77': ('Grenada', False),
    '78': ('Haiti', False),
    '79': ('Guadeloupe', False),
    '80': ('Honduras', False),
    '81': ('Germany', True),
    '82': ('Jamaica', False),
    '84': ('Martinique', False),
    '85': ('Bonaire, Curacao', True),
    '86': ('Nicaragua', False),
    '88': ('Panama', False),
    '89': ('Turks & Caicos Is.', False),
    '90': ('Trinidad & Tobago', False),
    '91': ('Aruba', False),
    '93': ('Geyser Reef', True),
    '94': ('Antigua & Barbuda', False),
    '95': ('Dominica', False),
    '96': ('Montserrat', False),
    '97': ('St. Lucia', False),
    '98': ('St. Vincent', False),
    '99': ('Glorioso Is.', False),
    '100': ('Argentina', False),
    '101': ('Goa', True),
    '102': ('Gold Coast, Togoland', True),
    '103': ('Guam', False),
    '104': ('Bolivia', False),
    '105': ('Guantanamo Bay', False),
    '106': ('Guernsey', False),
    '107': ('Guinea', False),
    '108': ('Brazil', False),
    '109': ('Guinea-Bissau', False),
    '110': ('Hawaii', False),
    '111': ('Heard I.', False),
    '112': ('Chile', False),
    '113': ('Ifni', True),
    '114': ('Isle Of Man', False),
    '115': ('Italian Somaliland', True),
    '116': ('Colombia', False),
    '117': ('Itu Hq', False),
    '118': ('Jan Mayen', False),
    '119': ('Java', True),
    '120': ('Ecuador', False),
    '122': ('Jersey', False),
    '123': ('Johnston I.', False),
    '124': ('Juan De Nova, Europa', False),
    '125': ('Juan Fernandez Is.', False),
    '126': ('Kaliningrad', False),
    '127': ('Kamaran Is.', True),
    '128': ('Karelo-Finnish Republic', True),
    '129': ('Guyana', False),
    '130': ('Kazakhstan', False),
    '131': ('Kerguelen Is.', False),
    '132': ('Paraguay', False),
    '133': ('Kermadec', False),
    '134': ('Kingman Reef', True),
    '135': ('Kyrgyzstan', False),
    '136': ('Peru', False),
    '137': ('Republic Of Korea', False),
    '138': ('Kure I.', False),
    '139': ('Kuria Muria I.', True),
    '140': ('Suriname', False),
    '141': ('Falkland Is.', False),
    '142': ('Lakshadweep Is.', False),
    '143': ('Laos', False),
    '144': ('Uruguay', False),
    '145': ('Latvia', False),
    '146': ('Lithuania', False),
    '147': ('Lord Howe I.', False),
    '148': ('Venezuela', False),
    '149': ('Azores', False),
    '150': ('Australia', False),
    '151': ('Malyj Vysotskij I.', True),
    '152': ('Macao', False),
    '153': ('Macquarie I,', False),
    '154': ('Yemen Arab Republic', True),
    '155': ('Malaya', True),
    '157': ('Nauru', False),
    '158': ('Vanuatu', False),
    '159': ('Maldives', False),
    '160': ('Tonga', False),
    '161': ('Malpelo I.', False),
    '162': ('New Caledonia', False),
    '163': ('Papua New Guinea', False),
    '164': ('Manchuria', True),
    '165': ('Mauritius Is', False),
    '166': ('Mariana Is.', False),
    '167': ('Market Reef', False),
    '168': ('Marshall Is.', False),
    '169': ('Mayotte', False),
    '170': ('New Zealand', False),
    '171': ('Mellish Reef', False),
    '172': ('Pitcairn I.', False),
    '173': ('Micronesia', False),
    '174': ('Midway I.', False),
    '175': ('French Polynesia', False),
    '176': ('Fiji', False),
    '177': ('Minami Torishima', False),
    '178': ('Minerva Reef', True),
    '179': ('Moldova', False),
    '180': ('Mount Athos', False),
    '181': ('Mozambique', False),
    '182': ('Navassa I.', False),
    '183': ('Netherlands Borneo', True),
    '184': ('Netherlands New Guinea', True),
    '185': ('Solomon Islands', False),
    '186': ('Newfoundland, Labrador', True),
    '187': ('Niger', False),
    '188': ('Niue', False),
    '189': ('Norfolk I.', False),
    '190': ('Samoa', False),
    '191': ('North Cook Is.', False),
    '192': ('Ogasawara', False),
    '193': ('Okinawa (Ryukyu Is.)', True),
    '194': ('Okino Tori-Shima', True),
    '195': ('Annobon I.', False),
    '196': ('Palestine', True),
    '197': ('Palmyra & Jarvis Is.', False),
    '198': ('Papua Territory', True),
    '199': ('Peter 1 I.', False),
    '200': ('Portuguese Timor', True),
    '201': ('Prince Edward & Marion Is.', False),
    '202': ('Puerto Rico', False),
    '203': ('Andorra', False),
    '204': ('Revillagigedo', False),
    '205': ('Ascension I.', False),
    '206': ('Austria', False),
    '207': ('Rodriguez I.', False),
    '208': ('Ruanda-Urundi', True),
    '209': ('Belgium', False),
    '210': ('Saar', True),
    '211': ('Sable I.', False),
    '212': ('Bulgaria', False),
    '213': ('Saint Martin', False),
    '214': ('Corsica', False),
    '215': ('Cyprus', False),
    '216': ('San Andres & Providencia', False),
    '217': ('San Felix & San Ambrosio', False),
    '218': ('Czechoslovakia', True),
    '219': ('Sao Tome & Principe', False),
    '220': ('Sarawak', True),
    '221': ('Denmark', False),
    '222': ('Faroe Is.', False),
    '223': ('England', False),
    '224': ('Finland', False),
    '225': ('Sardinia', False),
    '226': ('Saudi/Iraq Neutral Zone', True),
    '227': ('France', False),
    '228': ('Serrana Bank & Roncador Cay', True),
    '229': ('German Democratic Republic', True),
    '230': ('Federal Republic Of Germany', False),
    '231': ('Sikkim', True),
    '232': ('Somalia', False),
    '233': ('Gibraltar', False),
    '234': ('S Cook Is.', False),
    '235': ('South Georgia I.', False),
    '236': ('Greece', False),
    '237': ('Greenland', False),
    '238': ('South Orkney Is.', False),
    '239': ('Hungary', False),
    '240': ('South Sandwich Is.', False),
    '241': ('South Shetland Is.', False),
    '242': ('Iceland', False),
    '243': ("People's Democratic Republic Of Yemen", True),
    '244': ('Southern Sudan', True),
    '245': ('Ireland', False),
    '246': ('Sovereign Military Order Of Malta', False),
    '247': ('Spratly Is.', False),
    '248': ('Italy', False),
    '249': ('St. Kitts & Nevis', False),
    '250': ('St. Helena', False),
    '251': ('Liechtenstein', False),
    '252': ('St Paul Island', False),
    '253': ('St. Peter & St. Paul Rocks', False),
    '254': ('Luxembourg', False),
    '255': ('St. Maarten, Saba, St. Eustatius', True),
    '256': ('Madeira Is.', False),
    '257': ('Malta', False),
    '258': ('Sumatra', True),
    '259': ('Svalbard', False),
    '260': ('Monaco', False),
    '261': ('Swan Is.', True),
    '262': ('Tajikistan', False),
    '263': ('Netherlands', False),
    '264': ('Tangier', True),
    '265': ('Northern Ireland', False),
    '266': ('Norway', False),
    '267': ('Territory of New Guinea', True),
    '268': ('Tibet', True),
    '269': ('Poland', False),
    '270': ('Tokelau Is.', False),
    '271': ('Trieste', True),
    '272': ('Portugal', False),
    '273': ('Trindade & Martin Vaz Is.', False),
    '274': ('Tristan Da Cunha & Gough I.', False),
    '275': ('Romania', False),
    '276': ('Tromelin I.', False),
    '277': ('St. Pierre & Miquelon', False),
    '278': ('San Marino', False),
    '279': ('Scotland', False),
    '280': ('Turkmenistan', False),
    '281': ('Spain', False),
    '282': ('Tuvalu', False),
    '283': ('UK Sovereighn Base Areas on Cyprus', False),
    '284': ('Sweden', False),
    '285': ('Virgin Is.', False),
    '286': ('Uganda', False),
    '287': ('Switzerland', False),
    '288': ('Ukraine', False),
    '289': ('United Nations Hq', False),
    '291': ('United States of America', False),
    '292': ('Uzbekistan', False),
    '293': ('Viet Nam', False),
    '294': ('Wales', False),
    '295': ('Vatican', False),
    '296': ('Serbia', False),
    '297': ('Wake I.', False),
    '298': ('Wallis & Futuna Is.', False),
    '299': ('West Malaysia', False),
    '301': ('W. Kiribati (Gilbert Is.)', False),
    '302': ('Western Sahara', False),
    '303': ('Willis I.', False),
    '304': ('Bahrain', False),
    '305': ('Bangladesh', False),
    '306': ('Bhutan', False),
    '307': ('Zanzibar', True),
    '308': ('Costa Rica', False),
    '309': ('Myanmar', False),
    '312': ('Cambodia', False),
    '315': ('Sri Lanka', False),
    '318': ('China', False),
    '321': ('Hong Kong', False),
    '324': ('India', False),
    '327': ('Indonesia', False),
    '330': ('Iran', False),
    '333': ('Iraq', False),
    '336': ('Israel', False),
    '339': ('Japan', False),
    '342': ('Jordan', False),
    '344': ("Democratic People's Rep. Of Korea", False),
    '345': ('Brunei Darussalam', False),
    '348': ('Kuwait', False),
    '354': ('Lebanon', False),
    '363': ('Mongolia', False),
    '369': ('Nepal', False),
    '370': ('Oman', False),
    '372': ('Pakistan', False),
    '375': ('Philippines', False),
    '376': ('Qatar', False),
    '378': ('Saudi Arabia', False),
    '379': ('Seychelles', False),
    '381': ('Singapore', False),
    '382': ('Djibouti', False),
    '384': ('Syria', False),
    '386': ('Taiwan', False),
    '387': ('Thailand', False),
    '390': ('Turkey', False),
    '391': ('United Arab Emirates', False),
    '400': ('Algeria', False),
    '401': ('Angola', False),
    '402': ('Botswana', False),
    '404': ('Burundi', False),
    '406': ('Cameroon', False),
    '408': ('Central Africa', False),
    '409': ('Cape Verde', False),
    '410': ('Chad', False),
    '411': ('Comoros', False),
    '412': ('Republic Of The Congo', False),
    '414': ('Democratic Republic Of The Congo', False),
    '416': ('Benin', False),
    '420': ('Gabon', False),
    '422': ('The Gambia', False),
    '424': ('Ghana', False),
    '428': ("Cote D'Ivoire", False),
    '430': ('Kenya', False),
    '432': ('Lesotho', False),
    '434': ('Liberia', False),
    '436': ('Libya', False),
    '438': ('Madagascar', False),
    '440': ('Malawi', False),
    '442': ('Mali', False),
    '444': ('Mauritania', False),
    '446': ('Morocco', False),
    '450': ('Nigeria', False),
    '452': ('Zimbabwe', False),
    '453': ('Reunion I.', False),
    '454': ('Rwanda', False),
    '456': ('Senegal', False),
    '458': ('Sierra Leone', False),
    '460': ('Rotuma I.', False),
    '462': ('South Africa', False),
    '464': ('Namibia', False),
    '466': ('Sudan', False),
    '468': ('Swaziland', False),
    '470': ('Tanzania', False),
    '474': ('Tunisia', False),
    '478': ('Egypt', False),
    '480': ('Burkina Faso', False),
    '482': ('Zambia', False),
    '483': ('Togo', False),
    '488': ('Walvis Bay', True),
    '489': ('Conway Reef', False),
    '490': ('Banaba I. (Ocean I.)', False),
    '492': ('Yemen', False),
    '493': ('Penguin Is.', True),
    '497': ('Croatia', False),
    '499': ('Slovenia', False),
    '501': ('Bosnia-Herzegovina', False),
    '502': ('Macedonia', False),
    '503': ('Czech Republic', False),
    '504': ('Slovak Republic', False),
    '505': ('Pratas I.', False),
    '506': ('Scarborough Reef', False),
    '507': ('Temotu Province', False),
    '508': ('Austral I.', False),
    '509': ('Marquesas Is.', False),
    '510': ('Palestine', False),
    '511': ('Timor-Leste', False),
    '512': ('Chesterfield Is.', False),
    '513': ('Ducie I.', False),
    '514': ('Montenegro', False),
    '515': ('Swains I.', False),
    '516': ('Saint Barthelemy', False),
    '517': ('Curacao', False),
    '518': ('St Maarten', False),
    '519': ('Saba & St. Eustatius', False),
    '520': ('Bonaire', False),
    '521': ('South Sudan (Republic of)', False),
    '522': ('Republic of Kosovo', False),
}

adif_mode_to_lotw_modegroup_map = {
    'AM': 'PHONE',
    'CW': 'CW',
    'FM': 'PHONE',
    'FT8': 'DIGITAL',
    'MFSK': 'DIGITAL',
    'JT65': 'DIGITAL',
    'JT9': 'DIGITAL',
    'PSK': 'DIGITAL',
    'RTTY': 'DIGITAL',
    'SSB': 'PHONE',
    'SSTV': 'DIGITAL',  # REALLY? FIXME
}

merge_key_parts = ['qso_date', 'app_lotw_modegroup', 'call', 'band']
qso_key_parts = ['qso_date', 'time_on', 'call', 'band']

def adif_mode_to_lotw_modegroup(adif_mode):
    lotw_modegroup = adif_mode_to_lotw_modegroup_map.get(adif_mode.upper())
    if lotw_modegroup is None:
        logging.warning('cannot find lotw mode group for adif mode {}, guessing this is DATA'.format(adif_mode))
        lotw_modegroup = 'DATA'
    return lotw_modegroup


def get_adif_country_name(dxcc):
    country_tuple = dxcc_countries.get(dxcc) or ('None', False)
    return country_tuple[0]


def call_lotw(**params):
    logging.debug('Calling LoTW')
    qsos = []
    qso = {}
    header = {}
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
    try:
        response = urllib.request.urlopen(req)
    except urllib.error.HTTPError as q:
        print('problem with request ' + req.full_url)
        print(q.reason)
        for line in q:
            print(line)
        return None, None

    for line in response:
        try:
            line = line.decode('iso-8859-1')
        except Exception as inst:
            print()
            print('...problem')
            print(line)
            print(inst)
            print('Problem downloading from LoTW...')
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
        if item_value is None or len(item_value) == 0:  # header field.
            if item_name is not None:
                if item_name == 'eor':
                    qsos.append(qso)
                    qso = {}
                if item_name == 'eoh':
                    header = qso
                    qsos = []
                    qso = {}
        else:
            qso[item_name] = item_value
        print('QSOs loaded: {}'.format(len(qsos)), end='\r')
    print()
    if adif_file is not None:
        adif_file.close()
    logging.debug('Retrieved %d records from LoTW.' % len(qsos))
    return header, sorted(qsos, key=lambda qso: qso_key(qso))


def get_lotw_adif(username, password, filename=None, qso_qsorxsince=None):
    if qso_qsorxsince == None:
        qso_qsorxsince = '1900-01-01'
    return call_lotw(login=username,
                     password=password,
                     filename=filename,
                     qso_query='1',
                     qso_qsl='no',
                     qso_owncall=username,
                     qso_qsldetail='yes',
                     qso_qsorxsince=qso_qsorxsince,
                     )


def get_qsl_cards(username, password, filename=None):
    qsl_cards_header, qsl_cards = call_lotw(url='https://lotw.arrl.org/lotwuser/logbook/qslcards.php',
                     filename=filename,
                     login=username,
                     password=password,
                     ac_acct='1')
    # add 'qsl_rcvd'='y' to be consistent with LoTW.
    for qsl_card in qsl_cards:
        qsl_card['qsl_rcvd'] = 'y'
    return qsl_cards_header, qsl_cards


def adif_field_naive(s):
    if '<' in s:
        match = re.search(r'^<(.*)>(.*)$', s)
        if match is None:
            return None, None
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


def adif_field(s):
    state = 0
    element_name = ''
    element_size = 0
    element_type = ''
    element_value = ''
    bytes_to_copy = 0
    for c in s:
        if state == 0:  # initial, look for <
            if c == '<':
                element_name = ''
                state = 1
        elif state == 1:  # copying name
            if c == ':':  # end of name, start of size
                element_name = element_name.lower()
                element_size = ''
                state = 2
            elif c == '>':  # end of name, no size, not data, must be header
                state = 0
            else:  # keep copying the name.
                element_name += c
        elif state == 2:  # copying size
            if c == ':':  # end of size, start of type
                element_type = ''
                bytes_to_copy = int(element_size.strip())
                state = 3
            elif c == '>':
                element_value = ''
                bytes_to_copy = int(element_size.strip())
                state = 4
            else:
                element_size += c
        elif state == 3:  # copying type
            if c == '>':
                element_value = ''
                state = 4
            else:
                element_type += c
        elif state == 4:  # copying value.
            if bytes_to_copy > 0:
                element_value += c
                bytes_to_copy -= 1
            if bytes_to_copy == 0:
                state = 0  # start new adif value.
    return element_name, element_value


def chars_from_file(filename, chunksize=8192):
    with open(filename, 'rb') as f:
        while True:
            chunk = f.read(chunksize)
            if chunk:
                for b in chunk:
                    yield chr(b)
            else:
                break


def read_adif_file(adif_file_name):
    """
    adif file reader/parser.
    :param adif_file_name:  the name of the file to read.
    :return:
    """
    logging.debug('reading adif file {}'.format(adif_file_name))
    qsos = []
    header = {}
    qso = {}
    # parse adif, bytewise.  state machine:
    # 0 / clear  not copying
    # 1 / name
    # 2 / size
    # 3 / type
    # 4 / value
    element_name = ''
    element_size = ''
    element_value = ''
    element_type = ''
    state = 0
    bytes_to_copy = 0

    try:
        for c in chars_from_file(adif_file_name):
            if state == 0:  # not parsing adif data from file.
                if c == '<':
                    element_name = ''
                    state = 1
            elif state == 1:  # copying name
                if c == ':':  # end of name, start of size
                    element_name = element_name.lower()
                    element_size = ''
                    state = 2
                elif c == '>':  # end of name, no size, not data, must be header
                    element_name = element_name.lower()
                    if element_name == 'eoh':
                        header = qso
                        qso = {}
                    elif element_name == 'eor':
                        qsos.append(qso)
                        qso = {}
                    state = 0
                else:  # keep copying the name.
                    element_name += c
            elif state == 2:  # copying size
                if c == ':':  # end of size, start of type
                    element_type = ''
                    bytes_to_copy = int(element_size.strip())
                    state = 3
                elif c == '>':
                    element_value = ''
                    bytes_to_copy = int(element_size.strip())
                    state = 4
                else:
                    element_size += c
            elif state == 3:  # copying type
                if c == '>':
                    element_value = ''
                    state = 4
                else:
                    element_type += c
            elif state == 4:  # copying value.
                if bytes_to_copy > 0:
                    element_value += c
                    bytes_to_copy -= 1
                if bytes_to_copy == 0:
                    qso[element_name.lower()] = element_value
                    state = 0  # start new adif value.
    except FileNotFoundError:
        logging.warning('could not read file {}'.format(adif_file_name))
        pass
    logging.debug('read {} QSOs from {}'.format(len(qsos), adif_file_name))
    return header, sorted(qsos, key=lambda qso: qso_key(qso))


def compare_qsos(qso1, qso2):
    fields = ['call', 'band', 'mode', 'qso_date']
    for field in fields:
        if qso1.get(field) != qso2.get(field):
            return False
    return True


def qso_key(qso):
    return get_key(qso, qso_key_parts)


def merge_key(qso):
    return get_key(qso, merge_key_parts)


def get_key(qso, key_parts):
    key = ''
    for key_part in key_parts:
        if len(key) > 0:
            key += '.'
        key += qso.get(key_part) or 'missing'
    return key


def merge(header, qsos, new_header, new_qsos):
    qso_dict = {}
    added_count = 0
    updated_count = 0
    for qso in qsos:
        key = qso_key(qso)
        qso_dict[key] = qso
    for new_qso in new_qsos:
        updated = False
        added = False
        key = qso_key(new_qso)
        found_qso = qso_dict.get(key)
        if found_qso is None:
            qso_dict[key] = new_qso
            qsos.append(new_qso)
            added = True
            added_count += 1
            logging.debug('added qso: ' + str(new_qso))
        else:
            for key in new_qso:
                if key not in qso_key_parts:
                    if found_qso.get(key) != new_qso.get(key):
                        updated = True
                        found_qso[key] = new_qso.get(key)
                        logging.debug('updating {} with {}'.format(key, new_qso.get(key)))
            if updated:
                updated_count += 1
                logging.debug('updated QSO: ' + str(found_qso))
            else:
                logging.debug('found existing QSO ' + str(found_qso))
        if not added and not updated:
            logging.debug('ignoring QSO: ' + str(new_qso))

    header['app_lotw_numrec'] = str(len(qsos))
    logging.info('Added {}, updated {} QSOs'.format(added_count, updated_count))
    return header, sorted(qsos, key=lambda qso: qso_key(qso))


def write_adif_field(key, item):
    if item is not None:
        ss = str(item)
        return '<{0}:{1}>{2}\n'.format(key, len(ss), ss)
    else:
        return '<{0}>\n'.format(key)


def write_adif_file(header, qsos, adif_file_name, abridge_results=True):
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
                 'submode',
                 'time_on',
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
                   'app_lotw_owncall',
                   'app_lotw_gridsquare_invalid',
                   'app_lotw_ituz_inferred',
                   'app_lotw_ituz_invalid',
                   'app_lotw_qslmode',
                   'app_lotw_qso_timestamp',
                   'app_lotw_rxqsl',
                   'app_lotw_rxqso',
                   'band_rx',
                   'cnty',
                   'cqz',
                   'credit_granted',
                   'freq',
                   'freq_rx',
                   'iota',
                   'ituz',
                   'pfx',
                   'qslrdate',
                   'station_callsign',
                   'state',
                   ]
    with open(adif_file_name, 'w') as f:
        f.write('n1kdo lotw-qso-analyzer adif compatible file\n\n')
        header['programid'] = 'n1kdo log analyzer'
        for k in header:
            f.write(write_adif_field(k, header[k]))
        f.write('<eoh>\n\n')
        for qso in qsos:
            for key, value in qso.items():
                if abridge_results:
                    if key in save_keys:
                        f.write(write_adif_field(key, value))
                    else:
                        if key not in ignore_keys:
                            logging.warning('not saving %s %s' % (key, value))
                else:
                    f.write(write_adif_field(key, value))
            f.write('<eor>\n\n')
    logging.debug('wrote_adif_file %s' % adif_file_name)


def compare_lists(qso_list, cards_list):
    qsos = {}
    for qso in qso_list:
        key = qso['call'] + '.' + qso['qso_date'] + '.' + qso['band'] + '.' + qso['app_lotw_modegroup']
        qsos[key] = qso

    for qso in cards_list:
        key = qso['call'] + '.' + qso['qso_date'] + '.' + qso['band'] + '.' + qso.get('app_lotw_modegroup')
        if key not in qsos:
            print("can't find a match for ")
            print(qso)
            print()


def combine_qsos(qso_list, qsl_cards):
    logging.debug('combining dxcc qsl card info')
    # build index of qsos

    # this is brute-force right now.  it could be made faster.
    updated_qsls = []
    added_qsls = []
    for card in qsl_cards:
        card_merge_key = get_key(card, merge_key_parts)
        found = False
        for qso in qso_list:
            if card_merge_key == merge_key(qso):
                qsl_rcvd = (qso.get('qsl_rcvd') or 'n').lower()
                if qsl_rcvd != 'y':
                    break
                    #logging.warning('foo! {}'.format(card_merge_key))
                if found:  # have already seen this qsl
                    logging.warning('already seen {} {} {} '.format(card_merge_key, str(qso), str(card)))
                found = True
                for k in card:
                    if k not in merge_key_parts:
                        qso[k] = card[k]

                #if qso.get('dxcc') is None:
                #    # print('QSO to QSL: %s %s %s %s' % (card['call'], card['band'], card['qso_date'], card['country']))
                ##    qso['dxcc'] = card['dxcc']
                 #   qso['country'] = card['country']
                 #   copy_qso_data(card, qso, 'credit_granted')
                 #   copy_qso_data(card, qso, 'app_lotw_deleted_entity')
                 ##   copy_qso_data(card, qso, 'app_lotw_credit_granted')
                  #  qso['qsl_rcvd'] = 'y'
                  #  qso['app_n1kdo_qso_combined'] = 'qslcards detail added'
                updated_qsls.append(qso)
        if not found:
            # print('QSL added from card: %s %s %s %s' % (card['call'], card['band'], card['qso_date'], card['country']))
            card['app_n1kdo_qso_combined'] = 'qslcards QSL added'
            card['qsl_rcvd'] = 'y'
            added_qsls.append(card)
            qso_list.append(card)
    logging.info('updated %d QSL from cards, added %d QSLs from cards' % (len(updated_qsls), len(added_qsls)))
    return qso_list


def copy_qso_data(qso_from, qso_to, key):
    data = qso_from.get(key)
    if data is not None:
        qso_to[key] = data
    else:
        print('no key {} in {}'.format(key, qso_from))


