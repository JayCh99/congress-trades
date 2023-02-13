from filings import *
from utils import *
from textwrap import dedent
import re
import urllib.request as urllib2
import pdfplumber


class Transaction:
    """
    Represents a single asset transaction in a Periodic Transaction Report (PTR)
    """
    def __init__(self, asset_name: str, transaction_type: str, transaction_date: str, report_date: str,
                 dollar_range: str, cgo200: bool, asset_code: str, ownership: str, ticker: str):
        """ Headers correspond to PTR columns """
        self.asset_name = asset_name
        self.transaction_type = transaction_type
        self.transaction_date = transaction_date
        self.report_date = report_date
        self.dollar_range = dollar_range
        self.cgo200 = cgo200
        self.asset_code = asset_code
        self.ownership = ownership
        self.ticker = ticker

    def __str__(self):
        return dedent(f"""
        Asset Name: {self.asset_name}
        Transaction Type: {self.transaction_type} 
        Transaction Date: {self.transaction_date}
        Report Date: {self.report_date}
        Dollar Range: {self.dollar_range}
        Capital Gains Over $200?: {self.cgo200}
        Asset Code: {self.asset_code} 
        Ownership: {self.ownership} 
        Stock Ticker: {self.ticker}""")

    def num_missing_req_vars(self):
        """

        :return: number of missing required PTR values for the Transaction
        """
        c = 0
        req_vars = [self.asset_name, self.transaction_type, self.transaction_date, self.report_date, self.dollar_range,
                    self.cgo200]
        for var in req_vars:
            if var is "":
                c += 1
        return c


def download_ptr(filing: Filing) -> None:
    """

    :param filing: Filing information for a Periodic Transaction Report (PTR)
    :return: None. Downloads PTR
    """
    url = f"https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{filing.year}/{filing.doc_ID}.pdf"
    response = urllib2.urlopen(url).read()
    file = open(f"Reports/{filing.year}/{filing.doc_ID}.pdf", 'wb')
    file.write(response)
    file.close()


def extract_text_ptr(filing: Filing) -> str:
    """

    :param filing: Filing information for a PTR
    :return: multi-line text scraped from PTR

    Checks for the pdf in the local folders, downloads if not found
    """
    # Download and open file
    if not os.path.exists(f"Reports/{filing.year}/{filing.doc_ID}.pdf"):
        download_ptr(filing)
    pdfFileObj = open(f"Reports/{filing.year}/{filing.doc_ID}.pdf", 'rb')

    # Coalesces the pages together
    with pdfplumber.open(pdfFileObj) as pdf:
        text = ""
        for i in range(len(pdf.pages)):
            text += pdf.pages[i].extract_text() + '\n'

    # Make sure the file is a PTR
    ptr_pattern = re.compile("P.*T.*R.*")
    ptr_match = ptr_pattern.search(text.splitlines()[1].upper())
    if not ptr_match: raise Exception(f"Report expected to be PTR is not a PTR, DocID: {filing.doc_ID}")

    return text


def remove_headers_ptr(text: str) -> str:
    """

    :param text: uppercase PTR text
    :return: text without unnecessary information
    """
    end_beginning_ptr = "\n* FOR THE COMPLETE LIST OF ASSET TYPE ABBREVIATIONS, PLEASE VISIT"
    header_end_ptr = "\nTRANSACTIONS"
    table_headers_ptr = "ID OWNER ASSET TRANSACTION DATE NOTIFICATION AMOUNT CAP.\nTYPE DATE GAINS >\n$200?\n"
    text = text.replace(table_headers_ptr, "")
    return text[text.find(header_end_ptr) + len(header_end_ptr):text.find(end_beginning_ptr)]


# Turns a multi-line string containing many transactions into a list of strings where each string contains one
# transaction. Transactions consistently have a FILING STATUS (or F S) header at the end of them and inconsistently
# have other extra headers at the end, which is used to distinguish consecutive transactions
def separate_transactions(text: str) -> list[str]:
    """

    :param text: multi-line string containing many transactions
    :return: list of strings where each string contains one transaction

    Uses FILING STATUS (or F S) header at the end of and (inconsistent) extra headers at the beginning of transactions
    to distinguish consecutive transactions
    """
    transactions = []
    cur_text = ""
    prev_found_extra_header = False

    for line in text.splitlines():
        line = line.strip()

        found_extra_header = False
        for heading in EXTRA_TRANSACTION_HEADERS: found_extra_header = found_extra_header or heading in line

        if prev_found_extra_header and not found_extra_header:
            # We have found a new transaction starting with 'line'
            print(cur_text)
            transactions.append(cur_text)
            cur_text = ""

        cur_text += " " + line
        prev_found_extra_header = found_extra_header

    transactions.append(cur_text)
    return transactions


def parse_transaction(text: str) -> Transaction:
    """

    :param text: string representation of a transaction
    :return: Transaction with corresponding information
    """
    # SET 1
    # Parse ticker if exists, shave off parentheses
    ticker_pattern = re.compile('\([^\W\d_]{1,5}\)')
    ticker_match = ticker_pattern.search(text)
    ticker = ticker_match.group()[1:len(ticker_match.group()) - 1] if ticker_match else ""
    text = text.replace(ticker_match.group(), "") if ticker_match else text

    # Parse asset code if exists, shave off brackets
    asset_code_pattern = re.compile('\[[^\W\d_][^\W\d_]]')
    asset_code_match = asset_code_pattern.search(text)
    asset_code = asset_code_match.group()[1:len(asset_code_match.group()) - 1] if asset_code_match else ""
    text = text.replace(asset_code_match.group(), "") if asset_code_match else text

    # Parse ownership status if exists
    ownership_pattern = re.compile('JT|SP|DC')
    ownership_match = ownership_pattern.search(text)
    ownership = ownership_match.group() if ownership_match else ""
    text = text.replace(ownership, "")

    # Parse cgo200 if it can be identified (form uses a checkbox).
    # Empty check boxes are usually represented as "GFEDC" and checked check boxes as "GFEDCB"
    cgo200 = ""
    cgo200_text = ""
    if "GFEDCB" in text:
        cgo200 = True
        cgo200_text = "GFEDCB"
    elif "GFEDC" in text:
        cgo200 = False
        cgo200_text = "GFEDC"
    text = text.replace(cgo200_text, "")

    # There may be excess white space if SET 1 features were in the middle of SET 2 features
    text = remove_excess_whitespace(text)

    # SET 2
    # Parse transaction and reporting dates
    dates_pattern = re.compile('(\d\d/\d\d/\d\d\d\d) (\d\d/\d\d/\d\d\d\d)')
    dates_match = dates_pattern.search(text)
    transaction_date, report_date = dates_match.group(1), dates_match.group(2)
    dates_start_i, dates_end_i = dates_match.start(), dates_match.end()

    # Parse type of transaction, which is written before the dates
    transaction_type_start_i = max(text.rfind(" S (PARTIAL) ", 0, dates_start_i),
                                   text.rfind(" S ", 0, dates_start_i),
                                   text.rfind(" P ", 0, dates_start_i))
    transaction_type = text[transaction_type_start_i:dates_start_i].strip()

    # Parse asset name, which is written before the type of transaction
    asset_name = text[:transaction_type_start_i].strip()

    # Attempt to identify transaction dollar range; mostly likely to be in an unexpected format
    dollar_range = ""
    for rng in TRANSACTION_DOLLAR_RANGES:
        if rng in text:
            dollar_range = rng
            break

    return Transaction(asset_name, transaction_type, transaction_date, report_date, dollar_range, cgo200, asset_code,
                       ownership, ticker)


def ptr_to_transactions(filing: Filing) -> list[Transaction]:
    """

    :param filing: Filing information for a PTR
    :return: all transactions found in the PTR as Transactions
    """
    raw_text = extract_text_ptr(filing)
    text = remove_headers_ptr(raw_text.upper())
    text_transactions = separate_transactions(text)

    processed_transactions = []
    for text_txn in text_transactions:
        processed_transactions.append(parse_transaction(text_txn))

    return processed_transactions
