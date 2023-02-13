import re
from filings import *

TRANSACTION_DOLLAR_RANGES = ['$1,001 - $15,000',
                             '$1,5,001 - $50,000',
                             '$50,001 - $100,000',
                             '$100,001 - $250,000',
                             '$250,001 - $500,000',
                             '$500,001 - 1,000,000',
                             '$1,000,001 - $5,000,000',
                             '$5,000,001 - $25,000,000',
                             '$25,000,001 - $50,000,000',
                             'Over $50,000,000',
                             'Transaction in a Spouse or Dependent Child Asset over $1,000,000']

OVERVIEW_TAG_ORDER = ['Prefix', 'Last', 'First', 'Suffix', 'FilingType', 'StateDst', 'Year', 'FilingDate', 'DocID']

REPORTED_YEARS = ['2008', '2009', '2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019',
                  '2020',
                  '2021',
                  '2022']

EXTRA_TRANSACTION_HEADERS = ["FILING STATUS", "SUBHOLDING OF", "DESCRIPTION", "LOCATION", "F S", "S O"]


def url_to_filing(url):
    pattern = re.compile('/(\d+)/(\d+)\.pdf')
    match = pattern.search(url)
    if not match: raise Exception("utils.py url_to_filing: couldn't find year or docID")
    date, doc_id = match.group(1), match.group(2)
    return Filing("", "", "", "", "", "", date, "", doc_id, "")


# Coalesces multiple whitespaces into one, strips whitespaces
def remove_excess_whitespace(text):
    return ' '.join(text.strip().split())

