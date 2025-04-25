import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from collectors.edgar_collector import EdgarCollector
from models.database import Fund

class TestEdgarCollector(unittest.TestCase):
    def setUp(self):
        self.collector = EdgarCollector()
    
    @patch('requests.get')
    def test_get_fund_info(self, mock_get):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'name': 'Test Fund', 'cik': '0001234567'}
        mock_get.return_value = mock_response
        
        result = self.collector.get_fund_info('1234567')
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'Test Fund')
    
    @patch('requests.get')
    def test_get_fund_info_error(self, mock_get):
        # Mock failed response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = self.collector.get_fund_info('1234567')
        self.assertIsNone(result)

    @patch('requests.post')
    def test_cusip_to_ticker(self, mock_post):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"data": [{"ticker": "AAPL"}]},
            {"data": [{"ticker": "MSFT"}]}
        ]
        mock_post.return_value = mock_response
        
        result = self.collector.cusip_to_ticker(['037833100', '594918104'])
        self.assertEqual(result['037833100'], 'AAPL')
        self.assertEqual(result['594918104'], 'MSFT')

    @patch('requests.post')
    def test_cusip_to_ticker_error(self, mock_post):
        # Mock failed response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_post.return_value = mock_response
        
        result = self.collector.cusip_to_ticker(['037833100'])
        self.assertIsNone(result)

    def test_process_investments_table(self):
        # Create mock investments table
        mock_table = MagicMock()
        mock_table.columns = [
            MagicMock(header='Name'),
            MagicMock(header='Value'),
            MagicMock(header='Pct')
        ]
        mock_table.columns[0]._cells = ['Stock A', 'Stock B']
        mock_table.columns[1]._cells = ['$1,000', '$2,000']
        mock_table.columns[2]._cells = ['0.5', '1.0']
        
        result = self.collector.process_investments_table(mock_table)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertEqual(result['Value'].iloc[0], 1000)
        self.assertEqual(result['Pct'].iloc[1], 1.0)

    @patch('edgar.find')
    def test_get_nport_holdings(self, mock_find):
        # Create mock filing object
        mock_filing = MagicMock()
        mock_investments_table = MagicMock()
        mock_investments_table.columns = [
            MagicMock(header='Name'),
            MagicMock(header='Value'),
            MagicMock(header='Pct')
        ]
        mock_investments_table.columns[0]._cells = ['Stock A', 'Stock B']
        mock_investments_table.columns[1]._cells = ['$1,000', '$2,000']
        mock_investments_table.columns[2]._cells = ['0.5', '1.0']
        
        mock_filing.investments_table = mock_investments_table
        mock_find.return_value.filings.filter.return_value = [mock_filing]
        
        result = self.collector.get_nport_holdings('TESTFUND')
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertEqual(result['Value'].iloc[0], 1000)

    @patch('collectors.edgar_collector.EdgarCollector.get_nport_holdings')
    @patch('collectors.edgar_collector.EdgarCollector.cusip_to_ticker')
    def test_collect_fof_holdings(self, mock_cusip_to_ticker, mock_get_nport):
        # Mock the holdings data
        mock_holdings = pd.DataFrame({
            'Name': ['Fund A', 'Fund B'],
            'Cusip': ['123456789', '987654321'],
            'Value': [1000, 2000],
            'Pct': [0.5, 1.0]
        })
        
        mock_get_nport.return_value = mock_holdings
        mock_cusip_to_ticker.return_value = {
            '123456789': 'FUNDA',
            '987654321': 'FUNDB'
        }
        
        result = self.collector.collect_fof_holdings(['TESTFUND'])
        self.assertIn('TESTFUND', result)
        self.assertEqual(len(result), 1)
        self.assertTrue(isinstance(result['TESTFUND'], pd.DataFrame))

    @patch('edgar.find')
    @patch('collectors.edgar_collector.EdgarCollector.cusip_to_ticker')
    def test_retrieve_nport_filings(self, mock_cusip_to_ticker, mock_find):
        # Create mock filing object
        mock_filing = MagicMock()
        mock_investments_table = MagicMock()
        mock_investments_table.columns = [
            MagicMock(header='Name'),
            MagicMock(header='Value'),
            MagicMock(header='Pct'),
            MagicMock(header='Cusip')
        ]
        mock_investments_table.columns[0]._cells = ['Fund A', 'Fund B']
        mock_investments_table.columns[1]._cells = ['$1,000', '$2,000']
        mock_investments_table.columns[2]._cells = ['0.5', '1.0']
        mock_investments_table.columns[3]._cells = ['123456789', '987654321']
        
        mock_filing.investments_table = mock_investments_table
        mock_find.return_value.filings.filter.return_value = [mock_filing]
        
        mock_cusip_to_ticker.return_value = {
            '123456789': 'FUNDA',
            '987654321': 'FUNDB'
        }
        
        # Test with a temporary file
        import tempfile
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            os.chdir(tmpdir)
            try:
                self.collector.retrieve_nport_filings(['TESTFUND'])
                # Check if global variables were created
                self.assertTrue('TESTFUND' in globals())
                self.assertIsInstance(globals()['TESTFUND'], pd.DataFrame)
                # Check if CSV was created
                self.assertTrue(os.path.exists('TESTFUND.csv'))
            finally:
                os.chdir(original_dir)

if __name__ == '__main__':
    unittest.main() 