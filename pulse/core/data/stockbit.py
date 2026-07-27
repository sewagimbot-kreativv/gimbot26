"""Stockbit API client for broker flow data."""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from pulse.core.config import settings
from pulse.core.models import (
    AccDistType,
    BandarDetector,
    BrokerSummary,
    BrokerTransaction,
    BrokerType,
)
from pulse.utils.constants import BROKER_CODES, BROKER_TYPES
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class StockbitClient:
    """Client for Stockbit API to fetch broker summary data."""

    def __init__(
        self,
        secrets_file: Path | None = None,
        auth_state_file: Path | None = None,
    ):
        """
        Initialize Stockbit client.

        Args:
            secrets_file: Path to secrets.json with access token
            auth_state_file: Path to auth_state.json with cookies
        """
        self.base_url = settings.stockbit.api_base_url
        self.secrets_file = secrets_file or (settings.base_dir / settings.stockbit.secrets_file)
        self.auth_state_file = auth_state_file or (
            settings.base_dir / settings.stockbit.auth_state_file
        )
        self._token: str | None = None
        self._token_loaded_at: float | None = None

    def _load_token(self) -> str | None:
        """Load access token from environment variable or secrets file.

        Priority:
        1. STOCKBIT_TOKEN environment variable (recommended)
        2. secrets.json file
        """
        # Priority 1: Environment variable
        env_token = os.getenv("STOCKBIT_TOKEN")
        if env_token:
            log.debug("Using token from STOCKBIT_TOKEN environment variable")
            self._token = env_token
            self._token_loaded_at = time.time()
            return self._token

        # Priority 2: Secrets file
        if not self.secrets_file.exists():
            log.warning(f"No token found. Set STOCKBIT_TOKEN env var or create {self.secrets_file}")
            return None

        try:
            with open(self.secrets_file) as f:
                data = json.load(f)
                self._token = data.get("access_token")
                self._token_loaded_at = data.get("updated_at")
                log.debug(f"Using token from {self.secrets_file}")
                return self._token
        except Exception as e:
            log.error(f"Error loading token: {e}")
            return None

    def _save_token(self, token: str) -> None:
        """Save access token to secrets file."""
        self.secrets_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.secrets_file, "w") as f:
            json.dump({"access_token": token, "updated_at": time.time()}, f)

        self._token = token
        self._token_loaded_at = time.time()
        log.info(f"Token saved to {self.secrets_file}")

    def set_token(self, token: str, save: bool = True) -> bool:
        """Set access token manually.

        Args:
            token: JWT access token from Stockbit
            save: Whether to save to secrets file (default True)

        Returns:
            True if token is valid and set successfully
        """
        # Validate token format
        if not token or not token.startswith("eyJ"):
            log.error("Invalid token format. Token should be a JWT starting with 'eyJ'")
            return False

        # Check token expiry
        expiry = self.get_token_expiry(token)
        if expiry and expiry < datetime.now():
            log.error(f"Token is expired (expired at {expiry})")
            return False

        self._token = token
        self._token_loaded_at = time.time()

        if save:
            self._save_token(token)

        if expiry:
            hours_left = (expiry - datetime.now()).total_seconds() / 3600
            log.info(f"Token set successfully. Valid for {hours_left:.1f} hours")
        else:
            log.info("Token set successfully")

        return True

    def get_token_expiry(self, token: str = None) -> datetime | None:
        """Get token expiry datetime.

        Args:
            token: JWT token to check (uses current token if None)

        Returns:
            Expiry datetime or None if cannot parse
        """
        import base64

        token = token or self._token
        if not token:
            return None

        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None

            payload = parts[1]
            # Add padding if needed
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += "=" * padding

            decoded = base64.b64decode(payload)
            claims = json.loads(decoded)

            exp = claims.get("exp")
            if exp:
                return datetime.fromtimestamp(exp)
            return None
        except Exception:
            return None

    def get_token_status(self) -> dict:
        """Get current token status.

        Returns:
            Dict with token status info
        """
        if not self.token:
            return {
                "has_token": False,
                "source": None,
                "is_valid": False,
                "expires_at": None,
                "hours_remaining": None,
            }

        # Determine source
        env_token = os.getenv("STOCKBIT_TOKEN")
        source = "environment" if env_token and env_token == self._token else "file"

        expiry = self.get_token_expiry()
        is_valid = expiry is None or expiry > datetime.now()
        hours_remaining = None
        if expiry:
            hours_remaining = (expiry - datetime.now()).total_seconds() / 3600

        return {
            "has_token": True,
            "source": source,
            "is_valid": is_valid,
            "expires_at": expiry,
            "hours_remaining": hours_remaining,
        }

    @property
    def token(self) -> str | None:
        """Get current access token."""
        if not self._token:
            self._load_token()
        return self._token

    @property
    def is_authenticated(self) -> bool:
        """Check if we have a valid token."""
        return self.token is not None

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authorization."""
        return {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Origin": "https://stockbit.com",
            "Referer": "https://stockbit.com/",
        }

    def _parse_accdist(self, value: str) -> AccDistType:
        """Parse accumulation/distribution string."""
        value_lower = value.lower() if value else ""

        if "small acc" in value_lower:
            return AccDistType.SMALL_ACC
        elif "small dist" in value_lower:
            return AccDistType.SMALL_DIST
        elif "acc" in value_lower:
            return AccDistType.ACCUMULATION
        elif "dist" in value_lower:
            return AccDistType.DISTRIBUTION
        else:
            return AccDistType.NEUTRAL

    def _parse_broker_type(self, broker_code: str, raw_type: str | None = None) -> BrokerType:
        """Determine broker type."""
        if raw_type:
            if "asing" in raw_type.lower():
                return BrokerType.ASING
            elif "lokal" in raw_type.lower():
                return BrokerType.LOKAL

        return BrokerType(BROKER_TYPES.get(broker_code, "Unknown"))

    def _clean_number(self, value: Any) -> float:
        """Clean and convert number from API response."""
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return 0.0
        return 0.0

    def _parse_broker_transaction(
        self, data: dict[str, Any], is_buyer: bool = True
    ) -> BrokerTransaction:
        """Parse broker transaction data."""
        broker_code = data.get("netbs_broker_code", "")
        raw_type = data.get("type")

        if is_buyer:
            buy_lot = int(self._clean_number(data.get("blot", 0)))
            buy_value = self._clean_number(data.get("bval", 0))
            sell_lot = 0
            sell_value = 0.0
        else:
            buy_lot = 0
            buy_value = 0.0
            sell_lot = abs(int(self._clean_number(data.get("slot", 0))))
            sell_value = abs(self._clean_number(data.get("sval", 0)))

        net_lot = buy_lot - sell_lot
        net_value = buy_value - sell_value

        return BrokerTransaction(
            broker_code=broker_code,
            broker_name=BROKER_CODES.get(broker_code),
            broker_type=self._parse_broker_type(broker_code, raw_type),
            buy_lot=buy_lot,
            buy_value=buy_value,
            buy_avg_price=self._clean_number(data.get("netbs_buy_avg_price", 0)),
            sell_lot=sell_lot,
            sell_value=sell_value,
            sell_avg_price=self._clean_number(data.get("netbs_sell_avg_price", 0)),
            net_lot=net_lot,
            net_value=net_value,
        )

    async def fetch_broker_summary(
        self,
        ticker: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> BrokerSummary | None:
        """
        Fetch broker summary for a ticker.

        Args:
            ticker: Stock ticker (e.g., "BBCA")
            start_date: Start date (YYYY-MM-DD), defaults to today
            end_date: End date (YYYY-MM-DD), defaults to today

        Returns:
            BrokerSummary object or None if failed
        """
        if not self.is_authenticated:
            log.error("Not authenticated. Run authentication first.")
            return None

        ticker = ticker.upper().strip()
        today = datetime.now().strftime("%Y-%m-%d")
        start_date = start_date or today
        end_date = end_date or today

        url = f"{self.base_url}/marketdetectors/{ticker}"
        params = {
            "from": start_date,
            "to": end_date,
            "transaction_type": "TRANSACTION_TYPE_NET",
            "market_board": "MARKET_BOARD_REGULER",
            "investor_type": "INVESTOR_TYPE_ALL",
            "limit": 100,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                )

                if response.status_code == 401:
                    log.error("Token expired! Please run authentication again.")
                    return None

                if response.status_code != 200:
                    log.error(f"Failed to fetch {ticker}: {response.status_code}")
                    return None

                data = response.json()
                return self._parse_broker_summary(ticker, data)

        except Exception as e:
            log.error(f"Error fetching broker summary for {ticker}: {e}")
            return None

    def _parse_broker_summary(self, ticker: str, data: dict[str, Any]) -> BrokerSummary | None:
        """Parse raw API response into BrokerSummary."""
        try:
            api_data = data.get("data", {})

            # Parse broker transactions
            broker_summary = api_data.get("broker_summary", {})
            top_buyers = [
                self._parse_broker_transaction(b, is_buyer=True)
                for b in broker_summary.get("brokers_buy", [])[:10]
            ]
            top_sellers = [
                self._parse_broker_transaction(b, is_buyer=False)
                for b in broker_summary.get("brokers_sell", [])[:10]
            ]

            # Parse bandar detector
            bandar_data = api_data.get("bandar_detector", {})
            bandar = None

            if bandar_data:
                top1 = bandar_data.get("top1", {})
                top5 = bandar_data.get("top5", {})

                bandar = BandarDetector(
                    average=self._clean_number(bandar_data.get("average", 0)),
                    broker_accdist=self._parse_accdist(bandar_data.get("broker_accdist", "")),
                    top1_accdist=self._parse_accdist(top1.get("accdist", "")) if top1 else None,
                    top1_amount=self._clean_number(top1.get("amount", 0)),
                    top1_percent=self._clean_number(top1.get("percent", 0)),
                    top5_accdist=self._parse_accdist(top5.get("accdist", "")) if top5 else None,
                    top5_amount=self._clean_number(top5.get("amount", 0)),
                    top5_percent=self._clean_number(top5.get("percent", 0)),
                    total_buyer=int(self._clean_number(bandar_data.get("total_buyer", 0))),
                    total_seller=int(self._clean_number(bandar_data.get("total_seller", 0))),
                )

            # Calculate foreign flow
            foreign_net_buy = sum(
                b.net_value for b in top_buyers if b.broker_type == BrokerType.ASING
            ) - sum(b.net_value for b in top_sellers if b.broker_type == BrokerType.ASING)

            foreign_net_lot = sum(
                b.net_lot for b in top_buyers if b.broker_type == BrokerType.ASING
            ) - sum(abs(b.net_lot) for b in top_sellers if b.broker_type == BrokerType.ASING)

            # Calculate totals
            total_buy = sum(b.buy_value for b in top_buyers)
            total_sell = sum(b.sell_value for b in top_sellers)

            return BrokerSummary(
                ticker=ticker,
                date=datetime.now(),
                top_buyers=top_buyers,
                top_sellers=top_sellers,
                bandar=bandar,
                foreign_net_buy=foreign_net_buy,
                foreign_net_lot=foreign_net_lot,
                total_buy_value=total_buy,
                total_sell_value=total_sell,
                net_value=total_buy - total_sell,
                raw_data=data,
            )

        except Exception as e:
            log.error(f"Error parsing broker summary: {e}")
            return None

    async def fetch_multiple(
        self,
        tickers: list[str],
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[BrokerSummary]:
        """
        Fetch broker summaries for multiple tickers.

        Args:
            tickers: List of stock tickers
            start_date: Start date
            end_date: End date

        Returns:
            List of BrokerSummary objects
        """
        results = []

        for ticker in tickers:
            summary = await self.fetch_broker_summary(ticker, start_date, end_date)
            if summary:
                results.append(summary)

            # Rate limiting
            await self._delay(0.5)

        return results

    async def fetch_historical(
        self,
        ticker: str,
        days: int = 10,
        end_date: str | None = None,
    ) -> list[BrokerSummary]:
        """
        Fetch broker summaries for multiple days (historical).

        Args:
            ticker: Stock ticker (e.g., "BBCA")
            days: Number of days to fetch (default 10)
            end_date: End date (YYYY-MM-DD), defaults to today

        Returns:
            List of BrokerSummary objects, sorted by date (oldest first)
        """
        from datetime import timedelta

        if not self.is_authenticated:
            log.error("Not authenticated. Run authentication first.")
            return []

        ticker = ticker.upper().strip()

        # Calculate dates
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end_dt = datetime.now()

        results = []
        trading_days_found = 0
        days_checked = 0
        max_days_to_check = days * 2  # Account for weekends/holidays

        async with httpx.AsyncClient(timeout=30.0) as client:
            while trading_days_found < days and days_checked < max_days_to_check:
                check_date = end_dt - timedelta(days=days_checked)
                date_str = check_date.strftime("%Y-%m-%d")

                # Skip weekends
                if check_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    days_checked += 1
                    continue

                url = f"{self.base_url}/marketdetectors/{ticker}"
                params = {
                    "from": date_str,
                    "to": date_str,
                    "transaction_type": "TRANSACTION_TYPE_NET",
                    "market_board": "MARKET_BOARD_REGULER",
                    "investor_type": "INVESTOR_TYPE_ALL",
                    "limit": 100,
                }

                try:
                    response = await client.get(
                        url,
                        headers=self._get_headers(),
                        params=params,
                    )

                    if response.status_code == 401:
                        log.error("Token expired!")
                        break

                    if response.status_code == 200:
                        data = response.json()
                        summary = self._parse_broker_summary_with_date(ticker, data, check_date)

                        if summary and summary.top_buyers:  # Has data
                            results.append(summary)
                            trading_days_found += 1

                    # Rate limiting
                    await self._delay(0.3)

                except Exception as e:
                    log.warning(f"Error fetching {ticker} for {date_str}: {e}")

                days_checked += 1

        # Sort by date (oldest first)
        results.sort(key=lambda x: x.date)

        log.info(f"Fetched {len(results)} days of broker data for {ticker}")
        return results

    def _parse_broker_summary_with_date(
        self, ticker: str, data: dict[str, Any], date: datetime
    ) -> BrokerSummary | None:
        """Parse broker summary with specific date."""
        summary = self._parse_broker_summary(ticker, data)
        if summary:
            summary.date = date
        return summary

    async def _delay(self, seconds: float) -> None:
        """Async delay for rate limiting."""
        import asyncio

        await asyncio.sleep(seconds)

    async def authenticate_playwright(self) -> bool:
        """
        Authenticate using Playwright browser automation.

        Returns:
            True if authentication successful
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            log.error("Playwright not installed. Run: pip install playwright && playwright install")
            return False

        username = settings.stockbit.username or os.getenv("STOCKBIT_USERNAME")
        password = settings.stockbit.password or os.getenv("STOCKBIT_PASSWORD")

        if not username or not password:
            log.error("Stockbit credentials not found. Set STOCKBIT_USERNAME and STOCKBIT_PASSWORD")
            return False

        max_retries = 2

        for attempt in range(max_retries):
            use_cookies = (attempt == 0) and self.auth_state_file.exists()
            log.info(f"Attempt {attempt + 1}/{max_retries} (Using cookies: {use_cookies})")

            found_token = None

            async with async_playwright() as p:
                log.info("Launching browser...")
                browser = await p.chromium.launch(headless=settings.stockbit.headless)

                # Load existing session if available
                if use_cookies:
                    log.info("Loading previous session cookies...")
                    context = await browser.new_context(storage_state=str(self.auth_state_file))
                else:
                    log.info("Starting fresh session...")
                    context = await browser.new_context()

                page = await context.new_page()

                # Listen to network requests to catch the API token
                async def handle_request(request):
                    nonlocal found_token
                    if found_token:
                        return

                    headers = request.headers
                    if "authorization" in headers:
                        auth = headers["authorization"]
                        if auth.startswith("Bearer "):
                            log.info(f"Token found in request to: {request.url}")
                            found_token = auth.split(" ")[1]

                page.on("request", handle_request)

                try:
                    log.info("Navigating to Stockbit login...")
                    await page.goto("https://stockbit.com/login", timeout=60000)

                    # Check login status
                    log.info(f"Checking login status... (URL: {page.url})")
                    try:
                        await page.wait_for_selector("#username", state="visible", timeout=20000)
                        is_login_page = True
                    except Exception:
                        log.info("Login input not found - may be already logged in")
                        is_login_page = False

                    if is_login_page:
                        log.info("Login page detected. Entering credentials...")
                        await page.fill("#username", username)
                        await page.fill("#password", password)
                        await page.click("#email-login-button")
                        log.info("Clicked login button...")
                        await page.wait_for_timeout(3000)
                    else:
                        log.info("Already logged in via cookies. Navigating to home...")
                        await page.goto("https://stockbit.com/")

                    # Wait for token
                    log.info("Waiting for token capture...")
                    start_time = time.time()
                    while not found_token and time.time() - start_time < 30:
                        await page.wait_for_timeout(1000)

                    if found_token:
                        log.info("Token capture success!")
                        self._save_token(found_token)

                        # Save cookies & auth state
                        self.auth_state_file.parent.mkdir(parents=True, exist_ok=True)
                        await context.storage_state(path=str(self.auth_state_file))
                        log.info(f"Session saved to {self.auth_state_file}")

                        await browser.close()
                        return True
                    else:
                        log.warning("Failed to capture token within 30 seconds")

                except Exception as e:
                    log.error(f"Error during authentication: {e}")

                await browser.close()

        log.error("All authentication attempts failed")
        return False

        username = settings.stockbit.username or os.getenv("STOCKBIT_USERNAME")
        password = settings.stockbit.password or os.getenv("STOCKBIT_PASSWORD")

        if not username or not password:
            log.error("Stockbit credentials not found. Set STOCKBIT_USERNAME and STOCKBIT_PASSWORD")
            return False

        found_token = None

        async with async_playwright() as p:
            log.info("Launching browser...")
            browser = await p.chromium.launch(headless=settings.stockbit.headless)

            # Load existing session if available
            if self.auth_state_file.exists():
                log.info("Loading previous session cookies...")
                context = await browser.new_context(storage_state=str(self.auth_state_file))
            else:
                context = await browser.new_context()

            page = await context.new_page()

            # Listen to network requests to catch the API token
            async def handle_request(request):
                nonlocal found_token
                if found_token:
                    return

                headers = request.headers
                if "authorization" in headers:
                    auth = headers["authorization"]
                    if auth.startswith("Bearer "):
                        log.info(f"Token found in request to: {request.url}")
                        found_token = auth.split(" ")[1]

            page.on("request", handle_request)

            log.info("Navigating to Stockbit login...")
            await page.goto("https://stockbit.com/login")

            try:
                # Check if we need to login
                try:
                    await page.wait_for_selector(
                        'input[name="username"]', state="visible", timeout=5000
                    )
                    log.info("Entering credentials...")
                    await page.fill('input[name="username"]', username)
                    await page.fill('input[name="password"]', password)
                    await page.click('button[type="submit"]')
                    await page.wait_for_timeout(3000)
                except Exception:
                    log.info("Already logged in via cookies")

                # Navigate to a page that triggers API calls with token
                log.info("Navigating to broker summary page to capture token...")
                await page.goto("https://stockbit.com/symbol/BBCA/broker-summary")
                await page.wait_for_timeout(3000)

                # Also try market detector page
                if not found_token:
                    log.info("Trying market detector page...")
                    await page.goto("https://stockbit.com/symbol/BBCA")
                    await page.wait_for_timeout(3000)

                # Wait for token
                log.info("Waiting for token capture...")
                start_time = time.time()
                while not found_token and time.time() - start_time < 30:
                    await page.wait_for_timeout(1000)

                if found_token:
                    log.info("Token capture success!")
                    self._save_token(found_token)

                    # Save cookies
                    self.auth_state_file.parent.mkdir(parents=True, exist_ok=True)
                    await context.storage_state(path=str(self.auth_state_file))
                    log.info(f"Session cookies saved to {self.auth_state_file}")

                    await browser.close()
                    return True
                else:
                    log.error("Failed to capture token within 60 seconds")
                    await browser.close()
                    return False

            except Exception as e:
                log.error(f"Error during authentication: {e}")
                await browser.close()
                return False
