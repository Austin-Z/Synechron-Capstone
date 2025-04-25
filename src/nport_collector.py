import pandas as pd
import openpyxl
from edgar import *
import requests
import os
from dotenv import load_dotenv



# Set SEC API identity ("Name Email")
set_identity("yuz7@andrew.cmu.edu")
    
# OpenFIGI API Key (Register at OpenFIGI and get one)
API_KEY = os.getenv('FIGI_API_KEY', "01bd02bb-2846-4f48-8a42-e313b8f0c37c")

# Function to lookup Tickers using Cusips
def cusip_to_ticker(cusip_list):
    url = "https://api.openfigi.com/v3/mapping"
    headers = {"Content-Type": "application/json", "X-OPENFIGI-APIKEY": API_KEY}

    payload = [{"idType": "ID_CUSIP", "idValue": cusip} for cusip in cusip_list]
    
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        
        # Print the response to inspect its structure
        print("Response JSON:", data)
        
        results = {}
        for i, item in enumerate(data):
            if item and "data" in item and item["data"]:
                results[cusip_list[i]] = item["data"][0].get("ticker", "Not Found")
            else:
                results[cusip_list[i]] = "Not Found"
        
        return results
    else:
        print("Error:", response.status_code, response.text)
        return None

# Specify list of fund of funds
tickers = ["MDIZX", "TSVPX", "PFDOX"]

def retrieve_nport_filings(tickers):
    
    for ticker in tickers:
        # Retrieve the investments_table for the ticker
        investments_table = find(ticker).filings.filter(form="NPORT-P")[0].obj().investments_table
    
        # Extract column headers
        columns = [column.header for column in investments_table.columns]
    
        # Extract column data from _cells and transpose it to create rows
        rows = list(zip(*[column._cells for column in investments_table.columns]))
    
        # Convert to pandas DataFrame and assign it to a variable dynamically
        globals()[ticker] = pd.DataFrame(rows, columns=columns)
    
        # Ensure 'Value' column is a string, then remove unwanted characters
        globals()[ticker]['Value'] = globals()[ticker]['Value'].astype(str).str.replace("$", "", regex=False).str.replace(",", "", regex=False)
    
        # Convert to numeric
        globals()[ticker]['Value'] = pd.to_numeric(globals()[ticker]['Value'], errors='coerce')  # Use 'coerce' to handle any unexpected format
    
        globals()[ticker]['Pct'] = pd.to_numeric(globals()[ticker]['Pct'], errors='coerce')  # Convert percentage column safely
    
        # Write each ticker's DataFrame to a CSV file
        csv_filename = f"{ticker}.csv"
        globals()[ticker].to_csv(csv_filename, index=False)
        print(f"Data written to {csv_filename}")
        
        fof_tickers = list(cusip_to_ticker(globals()[ticker]['Cusip']).values())
        fof_tickers = filter(lambda x: x != "Not Found", fof_tickers)
        
        for ticker in fof_tickers:
            try:
            # Retrieve the investments_table for the ticker
                investments_table = find(ticker).filings.filter(form="NPORT-P")[0].obj().investments_table
                
                # Extract column headers
                columns = [column.header for column in investments_table.columns]
                
                # Extract column data from _cells and transpose it to create rows
                rows = list(zip(*[column._cells for column in investments_table.columns]))
                
                # Convert to pandas DataFrame and assign it to a variable dynamically
                globals()[ticker] = pd.DataFrame(rows, columns=columns)
                
                # Ensure 'Value' column is a string, then remove unwanted characters
                globals()[ticker]['Value'] = globals()[ticker]['Value'].astype(str).str.replace("$", "", regex=False).str.replace(",", "", regex=False)
                
                # Convert to numeric
                globals()[ticker]['Value'] = pd.to_numeric(globals()[ticker]['Value'], errors='coerce')  # Use 'coerce' to handle any unexpected format
                
                globals()[ticker]['Pct'] = pd.to_numeric(globals()[ticker]['Pct'], errors='coerce')  # Convert percentage column safely
                
                # Write each ticker's DataFrame to a CSV file
                csv_filename = f"{ticker}.csv"
                globals()[ticker].to_csv(csv_filename, index=False)
                print(f"Data written to {csv_filename}")
            except:
                print(f"NPort Filing Not Available for {ticker}")
                continue


retrieve_nport_filings(tickers)