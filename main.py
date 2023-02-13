from transactions import *
from filings import *

if __name__ == "__main__" :
    print("Running")
    # Specify year here
    filings = extract_overviews()
    transactions = []
    ptr_urls = []
    for filing in filings:
        if filing.form_type == "Online PTR":
            transactions += ptr_to_transactions(filing)

    for txn in transactions:
        print(txn)


