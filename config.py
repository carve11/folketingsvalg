# config.py
import os

URL_GEO = "https://api.dataforsyningen.dk"
INDEX_TEMPLATE = 'index_template.html'
INDEX_FNAME = 'index.html'
ROOT_DIR = os.path.dirname(__file__)
TITLE = 'Folketingsvalg 2022'
DATA_DIR = 'data'
MAP_WIDTH = 600
MAP_HEIGHT = 500
MAP_FONT_SIZE = '13px'
MAP_FONT = 'system-ui'

ELECTION_URL = {
    2019: 'https://www.dst.dk/valg/Valg1684447/xml/fintal.xml',
    2022: 'https://www.dst.dk/valg/Valg1968094/xml/fintal.xml',
}
DISTRICT_ATTRIB = {
    'Land': [],
    'Landsdel': ['landsdel_id'],
    'Storkreds': ['storkreds_id', 'landsdel_id'],
    'Opstillingskreds': ['opstillingskreds_id', 'storkreds_id'],
}
VOTE_ATTRIB = {
    'Stemmeberettigede': 'nochildren',
    'ValgDato': 'nochildren',
    'Stemmer': 'children'
}

PARTY_RENAME = {
    'K. KD - Kristendemokraterne': 'K. Kristendemokraterne'
}

DISTRICT_MAPPING = {
    'Landsdele': 'valglandsdelsnavn',
    'Regioner': 'regionsnavn',
    'Storkredse': 'storkredsnavn'
}