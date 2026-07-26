"""yfinance data fetcher for Indonesian stocks."""


import pandas as pd
import yfinance as yf

from pulse.core.models import OHLCV, FundamentalData, StockData
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class YFinanceFetcher:
    """Fetch stock data from yfinance for IDX stocks."""

    # Indonesian market indices mapping
    INDEX_MAPPING = {
        "IHSG": ("^JKSE", "IDX Composite"),
        "LQ45": ("^JKLQ45", "IDX LQ45"),
        "IDX30": ("^JKIDX30", "IDX30"),
        "JII": ("^JKII", "Jakarta Islamic Index"),
        "KOMPAS100": ("^JKSE", "Kompas 100"),  # fallback to IHSG
    }

    def __init__(self, suffix: str = ".JK"):
        """
        Initialize yfinance fetcher.
        
        Args:
            suffix: Ticker suffix for IDX (default: .JK)
        """
        self.suffix = suffix

    def _format_ticker(self, ticker: str) -> str:
        """Format ticker with IDX suffix."""
        ticker = ticker.upper().strip()

        # Check if it's an index
        if ticker in self.INDEX_MAPPING:
            return self.INDEX_MAPPING[ticker][0]

        # Don't add suffix to indices starting with ^
        if ticker.startswith("^"):
            return ticker

        if not ticker.endswith(self.suffix):
            return f"{ticker}{self.suffix}"
        return ticker

    def _clean_ticker(self, ticker: str) -> str:
        """Remove suffix from ticker."""
        if ticker.endswith(self.suffix):
            return ticker[:-len(self.suffix)]
        return ticker

    async def fetch_stock(
        self,
        ticker: str,
        period: str = "3mo",
    ) -> StockData | None:
        """
        Fetch stock data for a ticker.
        
        Args:
            ticker: Stock ticker (e.g., "BBCA")
            period: Historical data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            
        Returns:
            StockData object or None if failed
        """
        formatted_ticker = self._format_ticker(ticker)
        clean_ticker = self._clean_ticker(ticker)

        try:
            log.debug(f"Fetching {formatted_ticker} from yfinance...")

            stock = yf.Ticker(formatted_ticker)

            # Get historical data
            hist = stock.history(period=period)

            if hist.empty:
                log.warning(f"No data found for {ticker}")
                return None

            # Get stock info
            info = stock.info or {}

            # Convert history to OHLCV list
            history: list[OHLCV] = []
            for date, row in hist.iterrows():
                history.append(OHLCV(
                    date=date.to_pydatetime(),
                    open=float(row.get("Open", 0)),
                    high=float(row.get("High", 0)),
                    low=float(row.get("Low", 0)),
                    close=float(row.get("Close", 0)),
                    volume=int(row.get("Volume", 0)),
                ))

            # Get latest data
            latest = history[-1] if history else None
            prev = history[-2] if len(history) > 1 else None

            current_price = latest.close if latest else 0.0
            previous_close = prev.close if prev else current_price
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0.0

            # Calculate 52-week high/low
            week_52_data = hist.tail(252) if len(hist) >= 252 else hist
            week_52_high = float(week_52_data["High"].max()) if not week_52_data.empty else 0.0
            week_52_low = float(week_52_data["Low"].min()) if not week_52_data.empty else 0.0

            return StockData(
                ticker=clean_ticker,
                name=info.get("longName") or info.get("shortName"),
                sector=info.get("sector"),
                industry=info.get("industry"),
                current_price=current_price,
                previous_close=previous_close,
                change=change,
                change_percent=change_percent,
                volume=latest.volume if latest else 0,
                avg_volume=int(info.get("averageVolume", 0)),
                day_low=latest.low if latest else 0.0,
                day_high=latest.high if latest else 0.0,
                week_52_low=week_52_low,
                week_52_high=week_52_high,
                market_cap=info.get("marketCap"),
                shares_outstanding=info.get("sharesOutstanding"),
                history=history,
            )

        except Exception as e:
            log.error(f"Error fetching {ticker}: {e}")
            return None

    async def fetch_fundamentals(self, ticker: str) -> FundamentalData | None:
        """
        Fetch fundamental data for a ticker.
        
        Args:
            ticker: Stock ticker
            
        Returns:
            FundamentalData object or None if failed
        """
        formatted_ticker = self._format_ticker(ticker)
        clean_ticker = self._clean_ticker(ticker)

        try:
            stock = yf.Ticker(formatted_ticker)
            info = stock.info or {}

            if not info:
                return None

            # Dynamic USD/IDR exchange rate
            usdidr_rate = 16000.0
            try:
                fx_ticker = yf.Ticker("USDIDR=X")
                fx_hist = fx_ticker.history(period="1d")
                if not fx_hist.empty:
                    val = float(fx_hist["Close"].iloc[-1])
                    if val > 10000:
                        usdidr_rate = val
            except Exception:
                pass

            pb_ratio = info.get("priceToBook")
            bvps = info.get("bookValue")
            if pb_ratio is not None and pb_ratio > 100:
                pb_ratio = pb_ratio / usdidr_rate
                if bvps is not None:
                    bvps = bvps * usdidr_rate

            raw_de = info.get("debtToEquity")
            debt_to_equity = (raw_de / 100.0) if raw_de is not None else None

            return FundamentalData(
                ticker=clean_ticker,
                pe_ratio=info.get("trailingPE") or info.get("forwardPE"),
                pb_ratio=pb_ratio,
                ps_ratio=info.get("priceToSalesTrailing12Months"),
                peg_ratio=info.get("pegRatio"),
                ev_ebitda=info.get("enterpriseToEbitda"),
                roe=info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else None,
                roa=info.get("returnOnAssets", 0) * 100 if info.get("returnOnAssets") else None,
                npm=info.get("profitMargins", 0) * 100 if info.get("profitMargins") else None,
                opm=info.get("operatingMargins", 0) * 100 if info.get("operatingMargins") else None,
                gpm=info.get("grossMargins", 0) * 100 if info.get("grossMargins") else None,
                eps=info.get("trailingEps"),
                bvps=bvps,
                dps=info.get("dividendRate"),
                revenue_growth=info.get("revenueGrowth", 0) * 100 if info.get("revenueGrowth") else None,
                earnings_growth=info.get("earningsGrowth", 0) * 100 if info.get("earningsGrowth") else None,
                debt_to_equity=debt_to_equity,
                current_ratio=info.get("currentRatio"),
                quick_ratio=info.get("quickRatio"),
                dividend_yield=info.get("dividendYield") if info.get("dividendYield") is not None else None,
                payout_ratio=info.get("payoutRatio", 0) * 100 if info.get("payoutRatio") else None,
                market_cap=info.get("marketCap"),
                enterprise_value=info.get("enterpriseValue"),
            )

        except Exception as e:
            log.error(f"Error fetching fundamentals for {ticker}: {e}")
            return None

    async def fetch_multiple(
        self,
        tickers: list[str],
        period: str = "3mo",
    ) -> list[StockData]:
        """
        Fetch data for multiple tickers.
        
        Args:
            tickers: List of stock tickers
            period: Historical data period
            
        Returns:
            List of StockData objects
        """
        results = []

        for ticker in tickers:
            data = await self.fetch_stock(ticker, period)
            if data:
                results.append(data)

        return results

    async def fetch_history(
        self,
        ticker: str,
        period: str = "3mo",
    ) -> pd.DataFrame | None:
        """
        Fetch historical data as DataFrame (async wrapper).
        
        Args:
            ticker: Stock ticker
            period: Historical data period
            
        Returns:
            DataFrame with OHLCV data
        """
        return self.get_history_df(ticker, period)

    def get_history_df(self, ticker: str, period: str = "1y") -> pd.DataFrame | None:
        """
        Get historical data as pandas DataFrame (for technical analysis).
        
        Args:
            ticker: Stock ticker
            period: Historical data period
            
        Returns:
            DataFrame with OHLCV data
        """
        formatted_ticker = self._format_ticker(ticker)

        try:
            stock = yf.Ticker(formatted_ticker)
            hist = stock.history(period=period)

            if hist.empty:
                return None

            # Ensure column names are lowercase for ta library
            hist.columns = hist.columns.str.lower()

            return hist

        except Exception as e:
            log.error(f"Error fetching history for {ticker}: {e}")
            return None

    async def fetch_index(
        self,
        index_name: str,
        period: str = "3mo",
    ) -> StockData | None:
        """
        Fetch market index data (IHSG, LQ45, IDX30, etc).
        
        Args:
            index_name: Index name (IHSG, LQ45, IDX30, JII)
            period: Historical data period
            
        Returns:
            StockData object with index data, or None if failed
        """
        index_name = index_name.upper().strip()

        # Map index name to yfinance ticker
        if index_name in self.INDEX_MAPPING:
            yf_ticker, display_name = self.INDEX_MAPPING[index_name]
        elif index_name.startswith("^"):
            yf_ticker = index_name
            display_name = index_name
        else:
            log.warning(f"Unknown index: {index_name}")
            return None

        try:
            log.debug(f"Fetching index {yf_ticker} from yfinance...")

            stock = yf.Ticker(yf_ticker)

            # Get historical data
            hist = stock.history(period=period)

            if hist.empty:
                log.warning(f"No data found for index {index_name}")
                return None

            # Get index info
            info = stock.info or {}

            # Convert history to OHLCV list
            history: list[OHLCV] = []
            for date, row in hist.iterrows():
                history.append(OHLCV(
                    date=date.to_pydatetime(),
                    open=float(row.get("Open", 0)),
                    high=float(row.get("High", 0)),
                    low=float(row.get("Low", 0)),
                    close=float(row.get("Close", 0)),
                    volume=int(row.get("Volume", 0)),
                ))

            # Get latest data
            latest = history[-1] if history else None
            prev = history[-2] if len(history) > 1 else None

            current_price = latest.close if latest else 0.0
            previous_close = prev.close if prev else current_price
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0.0

            # Calculate 52-week high/low
            week_52_data = hist.tail(252) if len(hist) >= 252 else hist
            week_52_high = float(week_52_data["High"].max()) if not week_52_data.empty else 0.0
            week_52_low = float(week_52_data["Low"].min()) if not week_52_data.empty else 0.0

            return StockData(
                ticker=index_name,
                name=display_name,
                sector="Index",
                industry="Market Index",
                current_price=current_price,
                previous_close=previous_close,
                change=change,
                change_percent=change_percent,
                volume=latest.volume if latest else 0,
                avg_volume=int(info.get("averageVolume", 0)),
                day_low=latest.low if latest else 0.0,
                day_high=latest.high if latest else 0.0,
                week_52_low=week_52_low,
                week_52_high=week_52_high,
                market_cap=None,
                shares_outstanding=None,
                history=history,
            )

        except Exception as e:
            log.error(f"Error fetching index {index_name}: {e}")
            return None
