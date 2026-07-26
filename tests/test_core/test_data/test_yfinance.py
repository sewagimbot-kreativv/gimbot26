
import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import MagicMock, patch

from pulse.core.data.yfinance import YFinanceFetcher
from pulse.core.models import StockData, FundamentalData, OHLCV

@pytest.fixture
def fetcher():
    return YFinanceFetcher(suffix=".JK")

@pytest.fixture
def mock_yf_ticker():
    with patch('yfinance.Ticker') as mock:
        yield mock

@pytest.fixture
def mock_stock_data(mock_yf_ticker):
    # Mock history data
    dates = pd.date_range(start='2023-01-01', periods=5, freq='D')
    history_data = {
        'Open': [1000, 1010, 1005, 1020, 1015],
        'High': [1020, 1025, 1015, 1030, 1025],
        'Low': [990, 1000, 995, 1010, 1005],
        'Close': [1010, 1005, 1020, 1015, 1025],
        'Volume': [10000, 12000, 11000, 13000, 15000]
    }
    hist_df = pd.DataFrame(history_data, index=dates)
    
    # Mock info data
    info_data = {
        'longName': 'Bank Central Asia Tbk',
        'shortName': 'BBCA',
        'sector': 'Financial Services',
        'industry': 'Banks - Regional',
        'averageVolume': 12000,
        'marketCap': 1000000000000,
        'sharesOutstanding': 1000000000,
        'trailingPE': 20.5,
        'priceToBook': 4.2,
        'dividendYield': 2.5
    }
    
    mock_ticker_instance = mock_yf_ticker.return_value
    mock_ticker_instance.history.return_value = hist_df
    mock_ticker_instance.info = info_data
    
    return mock_ticker_instance

class TestYFinanceFetcher:

    def test_init(self):
        fetcher = YFinanceFetcher()
        assert fetcher.suffix == ".JK"
        
        fetcher_custom = YFinanceFetcher(suffix=".ID")
        assert fetcher_custom.suffix == ".ID"

    def test_format_ticker(self, fetcher):
        assert fetcher._format_ticker("BBCA") == "BBCA.JK"
        assert fetcher._format_ticker("bbca") == "BBCA.JK"
        assert fetcher._format_ticker("BBCA.JK") == "BBCA.JK"
        
        # Test index
        assert fetcher._format_ticker("IHSG") == "^JKSE"
        assert fetcher._format_ticker("^JKSE") == "^JKSE"

    def test_clean_ticker(self, fetcher):
        assert fetcher._clean_ticker("BBCA.JK") == "BBCA"
        assert fetcher._clean_ticker("BBCA") == "BBCA"

    @pytest.mark.asyncio
    async def test_fetch_stock_success(self, fetcher, mock_stock_data):
        ticker = "BBCA"
        data = await fetcher.fetch_stock(ticker)
        
        assert data is not None
        assert isinstance(data, StockData)
        assert data.ticker == "BBCA"
        assert data.name == "Bank Central Asia Tbk"
        assert data.current_price == 1025.0
        assert data.previous_close == 1015.0
        assert data.change == 10.0
        assert data.change_percent == pytest.approx(0.985, abs=0.001)
        assert len(data.history) == 5
        
    @pytest.mark.asyncio
    async def test_fetch_stock_no_data(self, fetcher, mock_yf_ticker):
        mock_ticker_instance = mock_yf_ticker.return_value
        mock_ticker_instance.history.return_value = pd.DataFrame()
        
        data = await fetcher.fetch_stock("UNKNOWN")
        assert data is None

    @pytest.mark.asyncio
    async def test_fetch_stock_error(self, fetcher, mock_yf_ticker):
        mock_yf_ticker.side_effect = Exception("Connection error")
        
        data = await fetcher.fetch_stock("BBCA")
        assert data is None

    @pytest.mark.asyncio
    async def test_fetch_fundamentals_success(self, fetcher, mock_stock_data):
        ticker = "BBCA"
        data = await fetcher.fetch_fundamentals(ticker)
        
        assert data is not None
        assert isinstance(data, FundamentalData)
        assert data.ticker == "BBCA"
        assert data.pe_ratio == 20.5
        assert data.pb_ratio == 4.2
        assert data.dividend_yield == pytest.approx(2.5)

    @pytest.mark.asyncio
    async def test_fetch_fundamentals_no_data(self, fetcher, mock_yf_ticker):
        mock_ticker_instance = mock_yf_ticker.return_value
        mock_ticker_instance.info = {}
        
        data = await fetcher.fetch_fundamentals("UNKNOWN")
        assert data is None

    @pytest.mark.asyncio
    async def test_fetch_multiple(self, fetcher, mock_stock_data):
        tickers = ["BBCA", "BMRI"]
        data = await fetcher.fetch_multiple(tickers)
        
        assert len(data) == 2
        assert all(isinstance(d, StockData) for d in data)

    @pytest.mark.asyncio
    async def test_fetch_index_success(self, fetcher, mock_stock_data):
        index = "IHSG"
        
        # Mock index info
        mock_stock_data.info = {
            'shortName': 'IDX Composite',
            'averageVolume': 1000000
        }
        
        data = await fetcher.fetch_index(index)
        
        assert data is not None
        assert isinstance(data, StockData)
        assert data.ticker == "IHSG"
        assert data.name == "IDX Composite"
        assert data.sector == "Index"
        assert data.current_price == 1025.0
