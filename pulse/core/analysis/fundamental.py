"""Fundamental analysis engine."""

from typing import Any

from pulse.core.data.yfinance import YFinanceFetcher
from pulse.core.models import FundamentalData, SignalType
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class FundamentalAnalyzer:
    """Fundamental analysis engine."""

    def __init__(self):
        """Initialize fundamental analyzer."""
        self.fetcher = YFinanceFetcher()

    async def analyze(self, ticker: str) -> FundamentalData | None:
        """
        Perform fundamental analysis on a stock.
        
        Args:
            ticker: Stock ticker
            
        Returns:
            FundamentalData object or None
        """
        return await self.fetcher.fetch_fundamentals(ticker)

    def score_valuation(
        self,
        data: FundamentalData,
        sector: str | None = None,
        industry: str | None = None
    ) -> dict[str, Any]:
        """
        Score stock valuation based on fundamental metrics.
        
        Args:
            data: FundamentalData object
            sector: Optional stock sector
            industry: Optional stock industry
            
        Returns:
            Valuation score and breakdown
        """
        scores = []
        max_score = 0

        # Check if financial service or bank
        is_bank_or_financial = False
        if sector and any(w in sector.lower() for w in ["financial services", "financials", "financial"]):
            is_bank_or_financial = True
        elif industry and "bank" in industry.lower():
            is_bank_or_financial = True

        # P/E Ratio scoring
        if data.pe_ratio is not None:
            if is_bank_or_financial:
                # Max 5 points
                max_score += 5
                if data.pe_ratio < 0:
                    scores.append(0)
                elif data.pe_ratio < 10:
                    scores.append(5)
                elif data.pe_ratio < 15:
                    scores.append(4)
                elif data.pe_ratio < 25:
                    scores.append(3)
                elif data.pe_ratio < 40:
                    scores.append(1)
                else:
                    scores.append(0)
            else:
                # Max 30 points
                max_score += 30
                if data.pe_ratio < 0:
                    scores.append(0)
                elif data.pe_ratio < 10:
                    scores.append(30)
                elif data.pe_ratio < 15:
                    scores.append(22)
                elif data.pe_ratio < 25:
                    scores.append(15)
                elif data.pe_ratio < 40:
                    scores.append(7)
                else:
                    scores.append(0)
        else:
            scores.append(0)

        # P/B Ratio scoring
        if data.pb_ratio is not None:
            if is_bank_or_financial:
                # Max 30 points
                max_score += 30
                if data.pb_ratio < 1:
                    scores.append(30)
                elif data.pb_ratio < 2:
                    scores.append(24)
                elif data.pb_ratio < 3:
                    scores.append(16)
                elif data.pb_ratio < 5:
                    scores.append(8)
                else:
                    scores.append(0)
            else:
                # Max 5 points
                max_score += 5
                if data.pb_ratio < 1:
                    scores.append(5)
                elif data.pb_ratio < 2:
                    scores.append(4)
                elif data.pb_ratio < 3:
                    scores.append(3)
                elif data.pb_ratio < 5:
                    scores.append(1)
                else:
                    scores.append(0)
        else:
            scores.append(0)

        # ROE scoring
        if data.roe is not None:
            max_score += 20
            if data.roe > 20:
                scores.append(20)
            elif data.roe > 15:
                scores.append(15)
            elif data.roe > 10:
                scores.append(10)
            elif data.roe > 5:
                scores.append(5)
            else:
                scores.append(0)
        else:
            scores.append(0)

        # ROA scoring
        if data.roa is not None:
            max_score += 15
            if data.roa > 10:
                scores.append(15)
            elif data.roa > 5:
                scores.append(10)
            elif data.roa > 2:
                scores.append(5)
            else:
                scores.append(0)
        else:
            scores.append(0)

        # Debt/Equity scoring
        if data.debt_to_equity is not None:
            max_score += 15
            if data.debt_to_equity < 0.5:
                scores.append(15)
            elif data.debt_to_equity < 1:
                scores.append(12)
            elif data.debt_to_equity < 2:
                scores.append(8)
            elif data.debt_to_equity < 3:
                scores.append(4)
            else:
                scores.append(0)
        else:
            scores.append(0)

        # Dividend Yield scoring
        if data.dividend_yield is not None:
            max_score += 15
            if data.dividend_yield > 5:
                scores.append(15)
            elif data.dividend_yield > 3:
                scores.append(12)
            elif data.dividend_yield > 1:
                scores.append(8)
            elif data.dividend_yield > 0:
                scores.append(4)
            else:
                scores.append(0)
        else:
            scores.append(0)

        total_score = sum(scores)
        normalized_score = (total_score / max_score * 100) if max_score > 0 else 0

        return {
            "score": round(normalized_score, 1),
            "max_score": 100,
            "breakdown": {
                "pe_score": scores[0],
                "pb_score": scores[1],
                "roe_score": scores[2],
                "roa_score": scores[3],
                "debt_score": scores[4],
                "dividend_score": scores[5],
            }
        }

    def get_valuation_signal(self, score: float) -> SignalType:
        """
        Get trading signal based on valuation score.
        
        Args:
            score: Valuation score (0-100)
            
        Returns:
            SignalType
        """
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

    def compare_peers(
        self,
        fundamentals: list[FundamentalData],
    ) -> list[dict[str, Any]]:
        """
        Compare fundamental metrics across peer stocks.
        
        Args:
            fundamentals: List of FundamentalData for peer stocks
            
        Returns:
            Comparison data sorted by score
        """
        results = []

        for data in fundamentals:
            score_data = self.score_valuation(data)

            results.append({
                "ticker": data.ticker,
                "pe_ratio": data.pe_ratio,
                "pb_ratio": data.pb_ratio,
                "roe": data.roe,
                "debt_to_equity": data.debt_to_equity,
                "dividend_yield": data.dividend_yield,
                "market_cap": data.market_cap,
                "score": score_data["score"],
                "signal": self.get_valuation_signal(score_data["score"]).value,
            })

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)

        return results

    def get_summary(self, data: FundamentalData) -> list[dict[str, Any]]:
        """
        Generate human-readable fundamental summary.
        
        Args:
            data: FundamentalData object
            
        Returns:
            List of metric summaries
        """
        summary = []

        # Valuation metrics
        if data.pe_ratio is not None:
            status = "Cheap" if data.pe_ratio < 15 else "Expensive" if data.pe_ratio > 30 else "Fair"
            summary.append({
                "category": "Valuation",
                "name": "P/E Ratio",
                "value": f"{data.pe_ratio:.2f}",
                "status": status,
            })

        if data.pb_ratio is not None:
            status = "Undervalued" if data.pb_ratio < 1 else "Overvalued" if data.pb_ratio > 3 else "Fair"
            summary.append({
                "category": "Valuation",
                "name": "P/B Ratio",
                "value": f"{data.pb_ratio:.2f}",
                "status": status,
            })

        # Profitability metrics
        if data.roe is not None:
            status = "Excellent" if data.roe > 20 else "Good" if data.roe > 15 else "Average" if data.roe > 10 else "Poor"
            summary.append({
                "category": "Profitability",
                "name": "ROE",
                "value": f"{data.roe:.2f}%",
                "status": status,
            })

        if data.roa is not None:
            status = "Good" if data.roa > 10 else "Average" if data.roa > 5 else "Poor"
            summary.append({
                "category": "Profitability",
                "name": "ROA",
                "value": f"{data.roa:.2f}%",
                "status": status,
            })

        if data.npm is not None:
            summary.append({
                "category": "Profitability",
                "name": "Net Profit Margin",
                "value": f"{data.npm:.2f}%",
                "status": "",
            })

        if data.debt_to_equity is not None:
            status = "Low Risk" if data.debt_to_equity < 1 else "Moderate" if data.debt_to_equity < 2 else "High Risk"
            summary.append({
                "category": "Financial Health",
                "name": "Debt/Equity",
                "value": f"{data.debt_to_equity:.2f} ({data.debt_to_equity * 100:.1f}%)",
                "status": status,
            })

        if data.current_ratio is not None:
            status = "Healthy" if data.current_ratio > 1.5 else "Adequate" if data.current_ratio > 1 else "Concerning"
            summary.append({
                "category": "Financial Health",
                "name": "Current Ratio",
                "value": f"{data.current_ratio:.2f}",
                "status": status,
            })

        # Dividend
        if data.dividend_yield is not None and data.dividend_yield > 0:
            status = "High" if data.dividend_yield > 5 else "Moderate" if data.dividend_yield > 2 else "Low"
            summary.append({
                "category": "Dividend",
                "name": "Dividend Yield",
                "value": f"{data.dividend_yield:.2f}%",
                "status": status,
            })

        # Growth
        if data.earnings_growth is not None:
            status = "Strong" if data.earnings_growth > 20 else "Moderate" if data.earnings_growth > 10 else "Weak" if data.earnings_growth > 0 else "Declining"
            summary.append({
                "category": "Growth",
                "name": "Earnings Growth",
                "value": f"{data.earnings_growth:.2f}%",
                "status": status,
            })

        return summary
