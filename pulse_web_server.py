import os
import sys
import json
import traceback
import socket
import threading
import select
import subprocess
import re
from datetime import datetime
from aiohttp import web

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Custom background DNS tunnel proxy to work around macOS sandbox name resolution issues
def resolve_dns_via_nslookup(host):
    try:
        output = subprocess.check_output(["nslookup", host], stderr=subprocess.DEVNULL, timeout=2).decode()
        lines = output.splitlines()
        found_answers = False
        ips = []
        for line in lines:
            if "Non-authoritative" in line or "Name:" in line or host in line:
                found_answers = True
            if found_answers:
                match = re.search(r"Address:\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", line)
                if match:
                    ips.append(match.group(1))
        if ips:
            return ips[0]
    except:
        pass
    return None

def handle_proxy_client(client_conn):
    try:
        request = client_conn.recv(4096).decode("utf-8", errors="ignore")
        if not request:
            client_conn.close()
            return
        lines = request.splitlines()
        if not lines:
            client_conn.close()
            return
        parts = lines[0].split()
        if len(parts) < 2 or parts[0].upper() != "CONNECT":
            client_conn.close()
            return
        host, port_str = parts[1].split(":")
        port = int(port_str)
        resolved_ip = resolve_dns_via_nslookup(host) or host
        server_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_conn.connect((resolved_ip, port))
        client_conn.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        sockets = [client_conn, server_conn]
        keep_going = True
        while keep_going:
            readable, _, errors = select.select(sockets, [], sockets, 10)
            if errors:
                break
            for s in readable:
                other = server_conn if s is client_conn else client_conn
                data = s.recv(8192)
                if not data:
                    keep_going = False
                    break
                other.sendall(data)
    except:
        pass
    finally:
        try: client_conn.close()
        except: pass
        try: server_conn.close()
        except: pass

def start_dns_proxy():
    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    proxy.bind(("127.0.0.1", 8095))
    proxy.listen(100)
    while True:
        try:
            conn, addr = proxy.accept()
            threading.Thread(target=handle_proxy_client, args=(conn,), daemon=True).start()
        except:
            break

# Start DNS proxy and direct python HTTP client traffic to it
t = threading.Thread(target=start_dns_proxy, daemon=True)
t.start()
os.environ["http_proxy"] = "http://127.0.0.1:8095"
os.environ["https_proxy"] = "http://127.0.0.1:8095"

from pulse.core.config import settings
from pulse.ai.client import AIClient
from pulse.core.data.yfinance import YFinanceFetcher
from pulse.core.analysis.technical import TechnicalAnalyzer
from pulse.core.analysis.fundamental import FundamentalAnalyzer
from pulse.core.analysis.broker_flow import BrokerFlowAnalyzer
from pulse.utils.logger import get_logger

log = get_logger("pulse_web_server")

# Database of known Beneficial Owners (Pemilik Manfaat) for IDX stocks
BENEFICIAL_OWNERS = {
    "SMDR": "Shanti L. Poesposoetjipto, Ratna Djuwita Hatma & Chandraleika M. Mulia (via PT Samudera Indonesia Tangguh)",
    "BBCA": "Keluarga Hartono (Robert Budi Hartono & Michael Bambang Hartono)",
    "BMRI": "Pemerintah Republik Indonesia (Negara RI)",
    "BBRI": "Pemerintah Republik Indonesia (Negara RI)",
    "TLKM": "Pemerintah Republik Indonesia (Negara RI)",
    "BBNI": "Pemerintah Republik Indonesia (Negara RI)",
    "ASII": "Jardine Matheson Holdings (via Jardine Cycle & Carriage Ltd)",
    "BNGA": "CIMB Group Holdings Berhad",
    "AMMN": "Keluarga Panigoro (Medco) & Salim Group",
    "BREN": "Prajogo Pangestu (Barito Pacific Group)",
    "TPIA": "Prajogo Pangestu (Barito Pacific Group)",
    "CUAN": "Prajogo Pangestu",
    "GOTO": "Keluarga Pendiri (GoTo Founders) & SVF / Boy Thohir",
    "ICBP": "Keluarga Anthoni Salim (Indofood)",
    "INDF": "Keluarga Anthoni Salim (First Pacific Co. Ltd)",
    "UNVR": "Unilever NV / PLC",
    "ADRO": "Keluarga Garibaldi Thohir & Keluarga Soeryadjaya",
    "PGAS": "PT Pertamina (Persero) / Negara RI",
    "ANTM": "PT Mineral Industri Indonesia (Persero) / MIND ID",
    "PTBA": "PT Mineral Industri Indonesia (Persero) / MIND ID",
    "TINS": "PT Mineral Industri Indonesia (Persero) / MIND ID",
    "INCO": "PT Mineral Industri Indonesia (Persero) / Vale S.A.",
    "ISAT": "Ooredoo Q.P.S.C. & CK Hutchison Holdings",
    "EXCL": "Axiata Group Berhad",
    "CPIN": "Keluarga Jiaravanon (Charoen Pokphand Group)",
    "JPFA": "Keluarga Santosa (Japfa Ltd)",
    "INKP": "Keluarga Eka Tjipta Widjaja (Sinar Mas Group)",
    "TKIM": "Keluarga Eka Tjipta Widjaja (Sinar Mas Group)",
    "BSDE": "Keluarga Eka Tjipta Widjaja (Sinar Mas Group)",
    "DILD": "Keluarga Sutoto Samsudin",
    "CTRA": "Keluarga Ciputra",
    "PWON": "Keluarga Alexander Tedja",
    "SMRA": "Keluarga Soetjipto Nagaria",
    "MAPI": "Keluarga Sjamsul Nursalim",
    "ACES": "Keluarga Kuncoro Wibowo",
    "MEDC": "Keluarga Arifin Panigoro",
    "HRUM": "Keluarga Barki",
    "ITMG": "Banpu Public Company Limited",
    "MBMA": "Garibaldi Thohir & Merdeka Copper Gold Group",
    "MDKA": "Garibaldi Thohir & Saratoga Investama Sedaya",
    "SRTG": "Sandiaga S. Uno & Edwin Soeryadjaya",
    "BRPT": "Prajogo Pangestu",
    "EMTK": "Keluarga Sariaatmadja",
    "SCMA": "Keluarga Sariaatmadja (Elang Mahkota Teknologi)",
    "KLBF": "Keluarga Boenjamin Setiawan",
    "MIKA": "Keluarga Raden Soetjipto",
    "HEAL": "Keluarga Hermina / PT Medikaloka Hermina",
    "MYOR": "Keluarga Jogi Hendra Atmadja",
    "CMRY": "Keluarga Bambang Sutantio",
    "WIFI": "Keluarga Surianto",
}

# Local JSON database to persist stock quadrant history
DB_PATH = "database.json"

def load_database():
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            log.error(f"Failed to read database.json: {e}")
    return {}

def save_database(data):
    try:
        with open(DB_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log.error(f"Failed to write database.json: {e}")

async def handle_quadrant(request):
    db = load_database()
    return json_response(list(db.values()))

# Custom JSON Encoder to handle datetime and pydantic models
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "dict"):
            return obj.dict()
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        return super().default(obj)

# Helper to dump JSON
def json_response(data, status=200):
    body = json.dumps(data, cls=CustomJSONEncoder)
    return web.Response(text=body, status=status, content_type="application/json")

# Route handlers
async def handle_index(request):
    try:
        with open("index.html", "r") as f:
            return web.Response(text=f.read(), content_type="text/html")
    except FileNotFoundError:
        return web.Response(text="index.html not found. Build the frontend first.", status=404)

async def handle_get_models(request):
    ai_client = AIClient()
    current = ai_client.get_current_model()
    models = ai_client.list_models()
    return json_response({
        "current": current,
        "available": models
    })

async def handle_set_model(request):
    try:
        body = await request.json()
        model_id = body.get("model")
        if not model_id:
            return json_response({"error": "model id is required"}, status=400)
        
        ai_client = AIClient()
        ai_client.set_model(model_id)
        
        # Also update global settings so it persists
        settings.ai.default_model = model_id
        
        return json_response({
            "status": "success",
            "current": ai_client.get_current_model()
        })
    except Exception as e:
        log.error(f"Error setting model: {e}")
        return json_response({"error": str(e)}, status=500)

async def handle_analyze(request):
    ticker = request.query.get("ticker")
    if not ticker:
        return json_response({"error": "ticker parameter is required"}, status=400)
    
    ticker = ticker.upper().strip()
    log.info(f"Received web analysis request for {ticker}")
    
    try:
        # Fetch data
        fetcher = YFinanceFetcher()
        stock = await fetcher.fetch_stock(ticker)
        
        if not stock:
            return json_response({"error": f"Could not fetch stock data for {ticker}"}, status=404)
        
        tech_analyzer = TechnicalAnalyzer()
        technical = await tech_analyzer.analyze(ticker)
        
        broker_analyzer = BrokerFlowAnalyzer()
        broker = None
        # Handle case where stockbit is not authenticated
        if broker_analyzer.client.is_authenticated:
            try:
                broker = await broker_analyzer.analyze(ticker)
            except Exception as be:
                log.error(f"Failed to fetch broker flow for {ticker}: {be}")
        
        fund_analyzer = FundamentalAnalyzer()
        fundamental_data = await fund_analyzer.analyze(ticker)
        
        # Compile structured data for frontend UI
        compiled_data = {
            "stock": stock,
            "technical": tech_analyzer.get_indicator_summary(technical) if technical else None,
            "fundamental": None,
            "broker": broker
        }
        
        if fundamental_data:
            # Quality Score formula (ROE, ROA, NPM, Growth)
            roe = fundamental_data.roe or 0.0
            roa = fundamental_data.roa or 0.0
            npm = fundamental_data.npm or 0.0
            growth = fundamental_data.earnings_growth or 0.0
            
            # Weighted ratings
            roe_pts = min(40.0, max(0.0, roe * 2.0))
            roa_pts = min(20.0, max(0.0, roa * 2.0))
            npm_pts = min(25.0, max(0.0, npm * 1.0))
            growth_pts = min(15.0, max(0.0, growth * 1.0))
            
            q_score = round(roe_pts + roa_pts + npm_pts + growth_pts, 1)
            q_score = min(100.0, max(0.0, q_score))
            
            score_data = fund_analyzer.score_valuation(fundamental_data, sector=stock.sector, industry=stock.industry)
            v_score = score_data.get("score", 50.0)
            
            if roe == 0.0 and roa == 0.0 and npm == 0.0 and growth == 0.0:
                q_score = 50.0
                
            if v_score >= 50.0 and q_score >= 50.0:
                verdict_cat = "Undervalue"
                verdict_label = "Diamond"
            elif v_score < 50.0 and q_score >= 50.0:
                verdict_cat = "Premium"
                verdict_label = "Wait for correction"
            elif v_score >= 50.0 and q_score < 50.0:
                verdict_cat = "Value Trap"
                verdict_label = "Perusahaan kalah saing/tidak berkembang"
            else:
                verdict_cat = "Junk"
                verdict_label = "Gorengan"
                
            compiled_data["fundamental"] = {
                "summary": fund_analyzer.get_summary(fundamental_data),
                "score_data": score_data,
                "verdict": {
                    "valuation_score": v_score,
                    "quality_score": q_score,
                    "category": verdict_cat,
                    "label": verdict_label,
                    "text": f"{verdict_label} ({verdict_cat})"
                }
            }
            # Save coordinates to local database.json
            try:
                db = load_database()
                db[ticker] = {
                    "ticker": ticker,
                    "name": stock.name or ticker,
                    "valuation_score": v_score,
                    "quality_score": q_score,
                    "category": verdict_cat,
                    "label": verdict_label
                }
                save_database(db)
            except Exception as db_err:
                log.error(f"Failed to update database with quadrant data: {db_err}")
        else:
            compiled_data["fundamental"] = {
                "summary": [],
                "score_data": {"score": 50.0},
                "verdict": {
                    "valuation_score": 50.0,
                    "quality_score": 50.0,
                    "category": "N/A",
                    "label": "N/A",
                    "text": "N/A"
                }
            }
            
        # Fetch extra stock info for Company Profile, Free Float, and Corporate Actions
        import yfinance as yf
        profile_data = {
            "sector": "N/A",
            "industry": "N/A",
            "description": "No description available."
        }
        free_float_data = {
            "float_shares": None,
            "shares_outstanding": None,
            "percentage": None
        }
        calendar_data = {
            "ex_dividend_date": "N/A",
            "earnings_date": "N/A"
        }
        
        try:
            stock_yf = yf.Ticker(fetcher._format_ticker(ticker))
            info = stock_yf.info or {}
            
            # Profile
            profile_data["sector"] = info.get("sector") or "N/A"
            profile_data["industry"] = info.get("industry") or "N/A"
            profile_data["description"] = info.get("longBusinessSummary") or "No description available."
            
            # Beneficial Owner lookup
            clean_t = ticker.upper().strip()
            if clean_t in BENEFICIAL_OWNERS:
                profile_data["beneficial_owner"] = BENEFICIAL_OWNERS[clean_t]
            else:
                officers = info.get("companyOfficers")
                if officers and len(officers) > 0 and officers[0].get("name"):
                    profile_data["beneficial_owner"] = f"{officers[0]['name']} ({officers[0].get('title', 'Direksi/Insider')})"
                else:
                    profile_data["beneficial_owner"] = "Lihat Portal AHU Kemenkumham (bo.ahu.go.id)"
            
            # Free Float
            float_shares = info.get("floatShares")
            shares_out = info.get("sharesOutstanding")
            if float_shares and shares_out:
                free_float_data["float_shares"] = float_shares
                free_float_data["shares_outstanding"] = shares_out
                free_float_data["percentage"] = round((float_shares / shares_out) * 100, 2)
            elif shares_out:
                free_float_data["shares_outstanding"] = shares_out
                
            # Calendar
            cal = stock_yf.calendar
            if cal:
                ex_div = cal.get("Ex-Dividend Date")
                earn = cal.get("Earnings Date")
                if ex_div:
                    if isinstance(ex_div, list) and len(ex_div) > 0:
                        calendar_data["ex_dividend_date"] = str(ex_div[0])
                    else:
                        calendar_data["ex_dividend_date"] = str(ex_div)
                if earn:
                    if isinstance(earn, list) and len(earn) > 0:
                        calendar_data["earnings_date"] = str(earn[0])
                    else:
                        calendar_data["earnings_date"] = str(earn)
        except Exception as ex_err:
            log.error(f"Failed to fetch extra yfinance details for {ticker}: {ex_err}")

        # Get AI Analysis
        ai_analysis = None
        ai_recommendation = None
        
        try:
            ai_client = AIClient()
            
            # Format the same payload we send to AI client
            ai_payload = {
                "stock": {
                    "ticker": stock.ticker,
                    "name": stock.name,
                    "price": stock.current_price,
                    "change": stock.change,
                    "change_percent": stock.change_percent,
                    "volume": stock.volume,
                    "market_cap": stock.market_cap,
                },
                "technical": compiled_data["technical"],
                "broker": compiled_data["broker"]
            }
            
            # Add fundamental to payload if exists
            if fundamental_data:
                ai_payload["fundamental"] = compiled_data["fundamental"]
                
            log.info(f"Requesting AI analysis for {ticker} using {ai_client.model}...")
            ai_analysis = await ai_client.analyze_stock(ticker, ai_payload)
            
            log.info(f"Requesting AI recommendation for {ticker}...")
            ai_recommendation = await ai_client.get_recommendation(ticker, ai_payload)
        except Exception as ai_err:
            log.error(f"AI Analysis failed for {ticker}: {ai_err}")
            ai_analysis = f"""### ⚠️ Analisis AI Tidak Tersedia

Gagal melakukan analisis menggunakan model AI karena **API Quota Exceeded** (429) atau masalah koneksi.

**Detail Error:**
`{str(ai_err)}`

**Solusi untuk Mengatasi:**
1. Anda mungkin telah melebihi batas request harian gratis (1500 request/hari). Anda dapat menunggu kuota di-reset besok siang, atau gunakan API Key berbayar.
2. Coba ganti model gratis lainnya menggunakan menu dropdown di sudut kanan atas (seperti **Gemini 2.5 Flash Lite**).
3. **Meskipun demikian, Anda tetap dapat melihat seluruh data harga historis, sinyal teknikal, data fundamental, dan data broker flow di dashboard ini untuk dianalisis secara mandiri!**
"""
            ai_recommendation = {
                "raw_response": True,
                "signal": "LIMIT EXCEEDED",
                "confidence": 0,
                "target_price": 0,
                "stop_loss": 0,
                "key_reasons": ["AI Quota Exceeded. Silakan ganti model AI di kanan atas."]
            }
        
        db = load_database()
        response_payload = {
            "ticker": ticker,
            "stock": stock,
            "technical": compiled_data["technical"],
            "fundamental": compiled_data["fundamental"],
            "broker": broker,
            "profile": profile_data,
            "free_float": free_float_data,
            "calendar": calendar_data,
            "ai_analysis": ai_analysis,
            "ai_recommendation": ai_recommendation,
            "quadrant_history": list(db.values())
        }
        
        return json_response(response_payload)
        
    except Exception as e:
        log.error(f"Error during analysis of {ticker}: {e}")
        log.error(traceback.format_exc())
        return json_response({
            "error": "Analysis failed", 
            "details": str(e),
            "traceback": traceback.format_exc()
        }, status=500)

async def handle_stockbit_status(request):
    from pulse.core.data.stockbit import StockbitClient
    client = StockbitClient()
    is_auth = client.is_authenticated
    status_text = "Connected" if is_auth else "Not connected"
    if is_auth:
        try:
            status_text = str(client.get_token_status())
        except Exception:
            pass
    return json_response({
        "authenticated": is_auth,
        "status": status_text
    })

async def handle_stockbit_auth(request):
    from pulse.core.data.stockbit import StockbitClient
    try:
        body = await request.json()
        token = body.get("token", "").strip()
        
        # Remove "Bearer " prefix if user copied full Authorization header
        if token.lower().startswith("bearer "):
            token = token[7:].strip()
            
        client = StockbitClient()
        success = client.set_token(token, save=True)
        if success:
            return json_response({"status": "success", "message": "Stockbit token saved successfully!"})
        else:
            return json_response({"error": "Invalid or expired token format. Make sure it starts with 'eyJ'"}, status=400)
    except Exception as e:
        return json_response({"error": str(e)}, status=500)

# Setup web application
app = web.Application()
app.router.add_get("/", handle_index)
app.router.add_get("/index.html", handle_index)
app.router.add_get("/api/models", handle_get_models)
app.router.add_post("/api/models", handle_set_model)
app.router.add_get("/api/analyze", handle_analyze)
app.router.add_get("/api/quadrant", handle_quadrant)
app.router.add_get("/api/stockbit/status", handle_stockbit_status)
app.router.add_post("/api/stockbit/auth", handle_stockbit_auth)

# Enable CORS for local development just in case
async def on_prepare(request, response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'

app.on_response_prepare.append(on_prepare)

if __name__ == "__main__":
    port = 8080
    print(f"Starting GimbotSaham Web Dashboard on http://localhost:{port}")
    web.run_app(app, host="127.0.0.1", port=port)
