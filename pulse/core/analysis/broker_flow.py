"""Broker flow / bandar analysis engine."""

from typing import Any

from pulse.core.data.stockbit import StockbitClient
from pulse.core.models import (
    AccDistType,
    BrokerSummary,
    BrokerTransaction,
    BrokerType,
    SignalType,
)
from pulse.utils.constants import BROKER_CODES, MAJOR_BROKERS
from pulse.utils.formatters import format_currency
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class BrokerFlowAnalyzer:
    """Analyze broker flow / bandar activity."""

    def __init__(self):
        """Initialize broker flow analyzer."""
        self.client = StockbitClient()

    async def analyze(
        self,
        ticker: str,
        days: int = 5,
    ) -> dict[str, Any] | None:
        """
        Analyze broker flow for a stock.
        
        Args:
            ticker: Stock ticker
            days: Number of days to analyze
            
        Returns:
            Analysis result dictionary
        """
        import asyncio
        from datetime import datetime, timedelta
        
        def get_weekdays_ago(base_date: datetime, n_days: int) -> datetime:
            current = base_date
            days_found = 0
            while days_found < n_days - 1:
                current -= timedelta(days=1)
                if current.weekday() < 5:
                    days_found += 1
            return current

        # 1. Search backwards starting from today to find the latest trading date with data
        today = datetime.now()
        summary = None
        latest_date = today
        
        # Try today
        today_str = today.strftime("%Y-%m-%d")
        summary = await self.client.fetch_broker_summary(ticker, start_date=today_str, end_date=today_str)
        
        # If no data for today, look back up to 10 calendar days
        if not summary or (not summary.top_buyers and not summary.top_sellers):
            log.info(f"No broker summary data for today ({today_str}) for {ticker}. Searching previous days...")
            for i in range(1, 11):
                check_date = today - timedelta(days=i)
                # Skip weekends
                if check_date.weekday() >= 5:
                    continue
                date_str = check_date.strftime("%Y-%m-%d")
                summary = await self.client.fetch_broker_summary(ticker, start_date=date_str, end_date=date_str)
                if summary and (summary.top_buyers or summary.top_sellers):
                    latest_date = check_date
                    log.info(f"Found recent broker data for {ticker} on date {date_str}")
                    break
            else:
                log.warning(f"Could not find any recent broker data for {ticker} in the last 10 days.")
                # Fallback to today's summary (which might be empty)
                summary = await self.client.fetch_broker_summary(ticker, start_date=today_str, end_date=today_str)
                latest_date = today

        if not summary:
            return None

        # 2. Perform 1-day analysis using the found latest summary
        analysis = self._analyze_summary(summary)
        
        # Add root-level keys for frontend compatibility
        analysis["flow_category"] = summary.bandar.broker_accdist.value if (summary.bandar and summary.bandar.broker_accdist) else "NEUTRAL"
        analysis["top_buyers"] = [
            {
                "broker": b.broker_code,
                "value": b.buy_value,
                "percentage": (b.buy_value / summary.total_buy_value * 100) if summary.total_buy_value > 0 else 0.0
            }
            for b in summary.top_buyers
        ]
        analysis["top_sellers"] = [
            {
                "broker": s.broker_code,
                "value": s.sell_value,
                "percentage": (s.sell_value / summary.total_sell_value * 100) if summary.total_sell_value > 0 else 0.0
            }
            for s in summary.top_sellers
        ]

        # Helper to fetch and parse a specific period summary
        async def fetch_period_data(p_days: int) -> dict[str, Any]:
            start_dt = get_weekdays_ago(latest_date, p_days)
            start_str = start_dt.strftime("%Y-%m-%d")
            end_str = latest_date.strftime("%Y-%m-%d")
            
            p_summary = await self.client.fetch_broker_summary(ticker, start_date=start_str, end_date=end_str)
            if not p_summary:
                return {
                    "flow_category": "NEUTRAL",
                    "top_buyers": [],
                    "top_sellers": [],
                    "date_range": f"{start_str} s/d {end_str}"
                }
            
            return {
                "flow_category": p_summary.bandar.broker_accdist.value if (p_summary.bandar and p_summary.bandar.broker_accdist) else "NEUTRAL",
                "top_buyers": [
                    {
                        "broker": b.broker_code,
                        "value": b.buy_value,
                        "percentage": (b.buy_value / p_summary.total_buy_value * 100) if p_summary.total_buy_value > 0 else 0.0
                    }
                    for b in p_summary.top_buyers
                ],
                "top_sellers": [
                    {
                        "broker": s.broker_code,
                        "value": s.sell_value,
                        "percentage": (s.sell_value / p_summary.total_sell_value * 100) if p_summary.total_sell_value > 0 else 0.0
                    }
                    for s in p_summary.top_sellers
                ],
                "date_range": f"{start_str} s/d {end_str}"
            }

        # 3. Fetch periods: 5, 10, 30 days
        periods = {
            "1": {
                "flow_category": analysis["flow_category"],
                "top_buyers": analysis["top_buyers"],
                "top_sellers": analysis["top_sellers"],
                "date_range": f"{latest_date.strftime('%Y-%m-%d')}"
            }
        }
        
        # Parallel fetch for 5, 10, 30 days
        data_5, data_10, data_30 = await asyncio.gather(
            fetch_period_data(5),
            fetch_period_data(10),
            fetch_period_data(30)
        )
        
        periods["5"] = data_5
        periods["10"] = data_10
        periods["30"] = data_30
        
        analysis["periods"] = periods
        return analysis

    def _analyze_summary(self, summary: BrokerSummary) -> dict[str, Any]:
        """Analyze a broker summary."""
        analysis = {
            "ticker": summary.ticker,
            "date": summary.date.strftime("%Y-%m-%d"),
            "signal": SignalType.NEUTRAL,
            "score": 50,
            "foreign_flow": {},
            "bandar_activity": {},
            "top_brokers": {},
            "insights": [],
        }

        # Foreign flow analysis
        analysis["foreign_flow"] = self._analyze_foreign_flow(summary)

        # Bandar activity
        if summary.bandar:
            analysis["bandar_activity"] = self._analyze_bandar(summary)

        # Top broker analysis
        analysis["top_brokers"] = self._analyze_top_brokers(summary)

        # Calculate overall score and signal
        score = self._calculate_score(analysis)
        analysis["score"] = score
        analysis["signal"] = self._score_to_signal(score)

        # Generate insights
        analysis["insights"] = self._generate_insights(summary, analysis)

        return analysis

    def _analyze_foreign_flow(self, summary: BrokerSummary) -> dict[str, Any]:
        """Analyze foreign investor flow."""
        foreign_buyers = [b for b in summary.top_buyers if b.broker_type == BrokerType.ASING]
        foreign_sellers = [s for s in summary.top_sellers if s.broker_type == BrokerType.ASING]

        foreign_buy_value = sum(b.buy_value for b in foreign_buyers)
        foreign_sell_value = sum(s.sell_value for s in foreign_sellers)

        return {
            "net_value": summary.foreign_net_buy,
            "net_value_formatted": format_currency(summary.foreign_net_buy),
            "buy_value": foreign_buy_value,
            "sell_value": foreign_sell_value,
            "is_net_buyer": summary.foreign_net_buy > 0,
            "buyer_count": len(foreign_buyers),
            "seller_count": len(foreign_sellers),
            "top_foreign_buyers": [
                {"code": b.broker_code, "name": b.broker_name, "value": b.buy_value}
                for b in foreign_buyers[:3]
            ],
            "top_foreign_sellers": [
                {"code": s.broker_code, "name": s.broker_name, "value": s.sell_value}
                for s in foreign_sellers[:3]
            ],
        }

    def _analyze_bandar(self, summary: BrokerSummary) -> dict[str, Any]:
        """Analyze bandar/smart money activity."""
        bandar = summary.bandar

        if not bandar:
            return {}

        # Determine accumulation/distribution
        is_accumulating = bandar.broker_accdist in [AccDistType.ACCUMULATION, AccDistType.SMALL_ACC]
        is_distributing = bandar.broker_accdist in [AccDistType.DISTRIBUTION, AccDistType.SMALL_DIST]

        return {
            "accdist": bandar.broker_accdist.value,
            "is_accumulating": is_accumulating,
            "is_distributing": is_distributing,
            "top1_percent": bandar.top1_percent,
            "top1_amount": bandar.top1_amount,
            "top1_accdist": bandar.top1_accdist.value if bandar.top1_accdist else None,
            "top5_percent": bandar.top5_percent,
            "top5_amount": bandar.top5_amount,
            "top5_accdist": bandar.top5_accdist.value if bandar.top5_accdist else None,
            "total_buyer": bandar.total_buyer,
            "total_seller": bandar.total_seller,
            "buyer_seller_ratio": bandar.buyer_seller_ratio,
        }

    def _analyze_top_brokers(self, summary: BrokerSummary) -> dict[str, Any]:
        """Analyze top broker activity."""
        # Identify major broker activity
        major_foreign = MAJOR_BROKERS.get("FOREIGN_BIG", [])
        major_local = MAJOR_BROKERS.get("LOCAL_BIG", [])
        retail = MAJOR_BROKERS.get("RETAIL", [])

        def find_broker_activity(codes: list[str], transactions: list[BrokerTransaction]) -> list[dict]:
            result = []
            for t in transactions:
                if t.broker_code in codes:
                    result.append({
                        "code": t.broker_code,
                        "name": t.broker_name or BROKER_CODES.get(t.broker_code, "Unknown"),
                        "value": t.buy_value if t.buy_value > 0 else -t.sell_value,
                        "type": t.broker_type.value,
                    })
            return result

        return {
            "top_5_buyers": [
                {
                    "code": b.broker_code,
                    "name": b.broker_name,
                    "type": b.broker_type.value,
                    "value": b.buy_value,
                    "value_formatted": format_currency(b.buy_value),
                    "lot": b.buy_lot,
                }
                for b in summary.top_buyers[:5]
            ],
            "top_5_sellers": [
                {
                    "code": s.broker_code,
                    "name": s.broker_name,
                    "type": s.broker_type.value,
                    "value": s.sell_value,
                    "value_formatted": format_currency(s.sell_value),
                    "lot": s.sell_lot,
                }
                for s in summary.top_sellers[:5]
            ],
            "major_foreign_activity": find_broker_activity(
                major_foreign,
                summary.top_buyers + summary.top_sellers
            ),
            "retail_activity": find_broker_activity(
                retail,
                summary.top_buyers + summary.top_sellers
            ),
        }

    def _calculate_score(self, analysis: dict[str, Any]) -> float:
        """Calculate overall broker flow score (0-100)."""
        score = 50  # Start neutral

        # Foreign flow impact (±20 points)
        foreign = analysis.get("foreign_flow", {})
        if foreign.get("is_net_buyer"):
            net = foreign.get("net_value", 0)
            if net > 10_000_000_000:  # > 10B
                score += 20
            elif net > 5_000_000_000:  # > 5B
                score += 15
            elif net > 1_000_000_000:  # > 1B
                score += 10
            else:
                score += 5
        elif foreign.get("net_value", 0) < 0:
            net = abs(foreign.get("net_value", 0))
            if net > 10_000_000_000:
                score -= 20
            elif net > 5_000_000_000:
                score -= 15
            elif net > 1_000_000_000:
                score -= 10
            else:
                score -= 5

        # Bandar activity impact (±20 points)
        bandar = analysis.get("bandar_activity", {})
        if bandar.get("is_accumulating"):
            score += 15
            if bandar.get("top1_percent", 0) > 10:
                score += 5
        elif bandar.get("is_distributing"):
            score -= 15
            if abs(bandar.get("top1_percent", 0)) > 10:
                score -= 5

        # Buyer/seller ratio impact (±10 points)
        ratio = bandar.get("buyer_seller_ratio", 1)
        if ratio > 2:
            score += 10
        elif ratio > 1.5:
            score += 5
        elif ratio < 0.5:
            score -= 10
        elif ratio < 0.7:
            score -= 5

        return max(0, min(100, score))

    def _score_to_signal(self, score: float) -> SignalType:
        """Convert score to trading signal."""
        if score >= 80:
            return SignalType.STRONG_BUY
        elif score >= 65:
            return SignalType.BUY
        elif score >= 40:
            return SignalType.NEUTRAL
        elif score >= 25:
            return SignalType.SELL
        else:
            return SignalType.STRONG_SELL

    def _generate_insights(
        self,
        summary: BrokerSummary,
        analysis: dict[str, Any],
    ) -> list[str]:
        """Generate human-readable insights."""
        insights = []

        # Foreign flow insight
        foreign = analysis.get("foreign_flow", {})
        if foreign.get("is_net_buyer"):
            net_formatted = format_currency(foreign.get("net_value", 0))
            insights.append(f"🟢 Foreign NET BUY {net_formatted}")
        elif foreign.get("net_value", 0) < 0:
            net_formatted = format_currency(abs(foreign.get("net_value", 0)))
            insights.append(f"🔴 Foreign NET SELL {net_formatted}")

        # Bandar insight
        bandar = analysis.get("bandar_activity", {})
        if bandar.get("is_accumulating"):
            insights.append(f"🟢 Bandar sedang AKUMULASI ({bandar.get('accdist')})")
        elif bandar.get("is_distributing"):
            insights.append(f"🔴 Bandar sedang DISTRIBUSI ({bandar.get('accdist')})")

        # Top broker insight
        top_brokers = analysis.get("top_brokers", {})
        if top_brokers.get("top_5_buyers"):
            top_buyer = top_brokers["top_5_buyers"][0]
            insights.append(
                f"📊 Top Buyer: {top_buyer['code']} ({top_buyer['type']}) - {top_buyer['value_formatted']}"
            )

        # Buyer/seller ratio
        ratio = bandar.get("buyer_seller_ratio", 1)
        if ratio > 2:
            insights.append(f"🟢 Dominasi buyer (rasio {ratio:.1f}x)")
        elif ratio < 0.5:
            insights.append(f"🔴 Dominasi seller (rasio {ratio:.1f}x)")

        return insights

    def format_summary_table(self, analysis: dict[str, Any]) -> str:
        """Format analysis as ASCII table."""
        lines = []
        lines.append(f"═══ Broker Flow: {analysis['ticker']} ({analysis['date']}) ═══")
        lines.append("")

        # Signal
        signal = analysis.get("signal", SignalType.NEUTRAL)
        score = analysis.get("score", 50)
        lines.append(f"Signal: {signal.value} (Score: {score}/100)")
        lines.append("")

        # Foreign Flow
        foreign = analysis.get("foreign_flow", {})
        lines.append("─── Foreign Flow ───")
        lines.append(f"Net: {foreign.get('net_value_formatted', '-')}")
        lines.append(f"Status: {'NET BUY' if foreign.get('is_net_buyer') else 'NET SELL'}")
        lines.append("")

        # Bandar Activity
        bandar = analysis.get("bandar_activity", {})
        if bandar:
            lines.append("─── Bandar Activity ───")
            lines.append(f"Status: {bandar.get('accdist', '-')}")
            lines.append(f"Top 1 Broker: {bandar.get('top1_percent', 0):.1f}%")
            lines.append(f"Buyer/Seller: {bandar.get('buyer_seller_ratio', 0):.2f}x")
            lines.append("")

        # Top Brokers
        top = analysis.get("top_brokers", {})
        if top.get("top_5_buyers"):
            lines.append("─── Top 5 Buyers ───")
            for i, b in enumerate(top["top_5_buyers"], 1):
                lines.append(f"{i}. {b['code']} ({b['type']}): {b['value_formatted']}")
            lines.append("")

        # Insights
        insights = analysis.get("insights", [])
        if insights:
            lines.append("─── Insights ───")
            for insight in insights:
                lines.append(insight)

        return "\n".join(lines)
