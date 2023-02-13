from transactions import *

# Test ptr using a url
def test_ptr_scraping(url):
    filing = url_to_filing(url)
    transactions = ptr_to_transactions(filing)
    for t in transactions:
        print(t)

if __name__=="__main__":
    # Find more urls at https://disclosures-clerk.house.gov/PublicDisclosure/FinancialDisclosure --> Search Reports
    url = 'https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2022/20020154.pdf'
    test_ptr_scraping(url)
