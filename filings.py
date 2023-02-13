import requests, zipfile, io
import xml.etree.ElementTree as ET
import os
from utils import *


class Filing:
    """
    All relevant filing information for a PTR
    """
    def __init__(self, prefix, last_name, first_name, suffix, filing_type, state_dst, year, filing_date, doc_ID, form_type):
        self.prefix = prefix
        self.last_name = last_name
        self.first_name = first_name
        self.suffix = suffix
        self.filing_type = filing_type
        self.state_dst = state_dst
        self.year = year
        self.filing_date = filing_date
        self.doc_ID = doc_ID
        self.form_type = form_type


def download_overviews() -> None:
    """

    :return: None. Downloads filing information overview files as XMLs for all reported years
    """
    for year in REPORTED_YEARS:
        url = f"https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.ZIP"
        r = requests.get(url)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(f"Overviews/{year}")


# Parse overview XML files into Filing objects. If no year specified, goes through all available years
def extract_overviews(year: str = "") -> list[Filing]:
    """

    :param year: year to parse XML overview file for. If no year specified, goes through all available years
    :return: list of Filing information for each PTR in the given year(s)
    """
    # Download filing overviews if they don't exist
    if not os.path.exists("Overviews"):
        download_overviews()

    years = REPORTED_YEARS if year is "" else [year]

    filings = []
    for year in years:
        overview = ET.parse(f'Overviews/{year}/{year}FD.xml')
        root = overview.getroot()

        # Confirm tag order
        filing_tags = []
        for child in root[0]:
            filing_tags.append(child.tag)
        if filing_tags != OVERVIEW_TAG_ORDER:
            raise Exception("filings.py: Overview tags order has changed")

        # filings in the XML are tagged Member
        for member in root.findall('Member'):
            doc_ID = member[8].text
            form_type = "Online PTR" if doc_ID[0] == '2' else ""
            filings.append(
                Filing(member[0].text, member[1].text, member[2].text, member[3].text, member[4].text, member[5].text,
                       member[6].text, member[7].text, doc_ID, form_type))

    return filings
