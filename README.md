# GimbotSaham & Pulse CLI

<div align="center">

![GimbotSaham Pro Web](https://img.shields.io/badge/GimbotSaham-Pro_Web-7c3aed?style=for-the-badge&logo=html5&logoColor=white)
![Pulse CLI](https://img.shields.io/badge/Pulse-CLI-58a6ff?style=for-the-badge&logo=python&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-Production_Ready-brightgreen?style=for-the-badge)

**GimbotSaham Web Dashboard & Stock Intelligence Engine**

*Analisis Saham Indonesia Interaktif dengan Dual Gauge, Visual Quadrant, Bandarmology, Beneficial Owner AHU Kemenkumham, dan Solvency Multi-Asset Fix.*

[![GitHub](https://img.shields.io/badge/GitHub-sewagimbot--kreativv%2Fgimbot26-181717?style=flat-square&logo=github)](https://github.com/sewagimbot-kreativv/gimbot26)

</div>

---

## 🚀 Status Versi Saat Ini (Current Version Status)

### 🌟 Fitur Unggulan GimbotSaham Pro Web Dashboard (`index.html`)
1. **Desain 3-Kolom Presisi & Header Terpusat**:
   - Ticker & nama emiten tampil di **tengah atas header** sejajar dengan brand `GimbotSaham PRO WEB`.
   - Layout 3 kolom padat tanpa ruang kosong (*no blank space*).
2. **Kartu Analisis Gabungan Valuation, Quality & Broker Flow**:
   - **Double Circular Progress Gauges**: Visual lingkaran persentase *Valuation Score* (skor harga murah/mahal) dan *Quality Score* (skor kualitas fundamental) side-by-side.
   - **Verdict Status Badge**: *Diamond (Undervalue)*, *Premium*, *Value Trap*, atau *Junk*.
   - **Flow & Foreign Net**: Status Akumulasi/Distribusi Broker beserta angka transaksi bersih asing (*Foreign Net Buy/Sell*).
3. **Peta Kuadran Saham (Stock Positioning Map)**:
   - Chart scatter plot 2D (Sumbu X: Valuasi, Sumbu Y: Kualitas) yang **mengingat seluruh emiten** yang pernah dipanggil sepanjang sesi tanpa menimpa data terdahulu.
4. **Pembobotan Sektor Dinamis (Bank & Financial Services)**:
   - **Sektor Finansial & Bank**: Pembobotan rasio **P/B (Price-to-Book)** diperbesar hingga **30 poin** (maksimal), dan bobot P/E kecil (**5 poin**).
   - **Sektor Non-Finansial**: Pembobotan rasio **P/E (Price-to-Earnings)** diperbesar hingga **30 poin** (maksimal), dan bobot P/B kecil (**5 poin**).
5. **Koreksi Data Solvency (Debt/Equity & Book Value USD/IDR)**:
   - **Debt to Equity Ratio**: Otomatis mengonversi data yfinance dari persen ke rasio murni + persen (contoh SMDR: **`0.66 (65.8%)`** dengan status **`Low Risk`**), presisi selaras dengan tabel Solvency Stockbit.
   - **Kurs USD/IDR Live**: Mengambil acuan kurs live dari Yahoo Finance (`USDIDR=X`) untuk mengonversi nilai buku berdenominasi USD ke IDR sehingga P/B ratio tidak lagi anomali (SMDR P/B: **`0.58`** *Undervalued*).
6. **Beneficial Owner (Pemilik Manfaat)**:
   - Menampilkan data Ultimate Beneficial Owner (UBO) pada profil perusahaan (contoh: *SMDR: Shanti L. Poesposoetjipto, Ratna Djuwita Hatma & Chandraleika M. Mulia*, *BBCA: Keluarga Hartono*) lengkap dengan link navigasi langsung ke portal resmi **[AHU Kemenkumham (bo.ahu.go.id)](https://ahu.go.id/pencarian/profil-pemilik-manfaat)**.
7. **Built-in DNS CONNECT Proxy**:
   - Proxy tunnel otomatis berjalan di background backend (`pulse_web_server.py`) untuk mengatasi isu DNS Name Resolution pada macOS Sandbox secara transparan.

---

## ⏪ Panduan Rollback & Kontrol Versi (Git Rollback Guide)

Jika di masa mendatang Anda ingin melakukan **rollback** (kembali ke versi commit sebelumnya), ikuti panduan berikut:

### 1. Memeriksa Riwayat Commit (Check History)
Lihat daftar commit beserta ID-nya:
```bash
git log --oneline -n 10
```

### 2. Opsi Rollback 1: Rollback Lunak (Soft Reset - Menjaga Kode Tetap Ada)
Mengembalikan histori commit ke versi terdahulu, tetapi seluruh perubahan kodingan Anda **tetap tersimpan di working directory**:
```bash
git reset --soft <COMMIT_ID>
```

### 3. Opsi Rollback 2: Rollback Total (Hard Reset - Kembali Utuh ke Versi Lama)
Mengembalikan repositori **100% utuh** seperti saat commit tertentu (perubahan yang belum di-commit akan dihapus):
```bash
# Langkah Opsional: Buat branch cadangan sebelum hard reset agar kode saat ini tidak hilang
git branch backup-gimbot-versi-ini

# Lakukan hard reset ke commit tujuan (misal commit ID: a698320)
git reset --hard <COMMIT_ID>
```

### 4. Opsi Rollback 3: Rollback File Spesifik
Jika Anda hanya ingin mengembalikan 1 file saja ke versi lama (misalnya mengembalikan `index.html` saja):
```bash
git checkout <COMMIT_ID> -- index.html
```

### 5. Memperbarui GitHub Setelah Rollback (Force Push)
Jika Anda telah melakukan rollback di lokal dan ingin menyinkronkan repositori GitHub:
```bash
git push -f origin main
```

---

## Overview

**Pulse CLI** adalah aplikasi Terminal User Interface (TUI) yang powerful untuk analisis pasar saham Indonesia (IDX). Menggabungkan:

- **Real-time Data** dari Yahoo Finance
- **Technical Analysis** (RSI, MACD, Bollinger Bands, Support/Resistance)
- **Fundamental Analysis** (PE, PB, ROE, Dividend Yield)
- **AI/LLM Integration** untuk analisis cerdas dan natural language
- **SAPTA Engine** - Sistem deteksi pre-markup berbasis Machine Learning
- **Trading Plan Generator** dengan TP/SL/Risk-Reward calculations
- **Broker Flow Analysis** via Stockbit integration

---

## Features

### Core Features

| Feature | Description |
|---------|-------------|
| **Smart Agent** | True agentic AI yang mengambil data real sebelum analisis |
| **Natural Language** | Tanya dalam Bahasa Indonesia atau English |
| **Stock Screening** | Filter 900+ saham IDX dengan berbagai kriteria |
| **Technical Analysis** | 15+ indikator teknikal otomatis |
| **Trading Plan** | Generate TP/SL/RR dengan position sizing |
| **SAPTA Detection** | Deteksi fase pre-markup dengan ML |
| **Price Forecast** | Prediksi harga dengan confidence interval |
| **Chart Generation** | Export chart sebagai PNG |

### Supported Analysis

```
Technical Indicators        Fundamental Metrics       SAPTA Modules
─────────────────────      ──────────────────────    ─────────────────────
• RSI (14)                 • P/E Ratio               • Supply Absorption
• MACD + Signal + Hist     • P/B Ratio               • Compression
• SMA (20, 50, 200)        • ROE / ROA               • BB Squeeze
• EMA (9, 21, 55)          • Net Profit Margin       • Elliott Wave
• Bollinger Bands          • Debt to Equity          • Time Projection
• Stochastic K/D           • Dividend Yield          • Anti-Distribution
• ATR (14)                 • Revenue Growth
• Support/Resistance       • Earnings Growth
• Volume Analysis          • Market Cap
```

---

## Installation

### Prerequisites

- **Python 3.11+** (required)
- **pip** or **uv** package manager
- **Git** (for cloning)

### Quick Install

```bash
# Clone repository
git clone https://github.com/sukirman1901/Pulse-CLI.git
cd Pulse-CLI

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install package
pip install -e .

# Install Playwright browsers (for Stockbit auth - optional)
playwright install chromium
```

### Install with Development Dependencies

```bash
pip install -e ".[dev]"
```

### Using uv (Faster)

```bash
# Install uv if not installed
pip install uv

# Install with uv
uv pip install -e .
```

### Verify Installation

```bash
# Check if pulse is installed
pulse --help

# Or run directly
python -m pulse.cli.app
```

---

## Usage

### Starting Pulse CLI

```bash
# Simply run
pulse
```

You'll see the TUI interface:

```
┌─────────────────────────────────────────────────────────────────┐
│ Pulse - Type /help for commands                                 │
│                                                                 │
│                                                                 │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ > Message Pulse...                                              │
│                                                           pulse │
└─────────────────────────────────────────────────────────────────┘
```

### Basic Interactions

#### Natural Language (Bahasa Indonesia)

```
> analisa BBCA
> gimana kondisi IHSG hari ini?
> bandingkan BBRI dan BMRI
> carikan saham yang oversold
> buatkan trading plan TLKM
> cek pre-markup ANTM
```

#### Natural Language (English)

```
> analyze BBCA
> what's the technical outlook for ASII?
> compare banking stocks BBCA BBRI BMRI
> find undervalued stocks
> generate trading plan for UNVR
```

#### Slash Commands

```
> /analyze BBCA
> /technical BBRI
> /fundamental TLKM
> /chart ASII 6mo
> /forecast UNVR 14
> /plan BMRI
> /sapta ANTM
> /screen oversold
```

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Submit message/command |
| `Ctrl+C` | Quit application |
| `Ctrl+L` | Clear chat history |
| `Escape` | Close command palette |
| `Tab` | Navigate command palette |
| `↑` `↓` | Navigate options |

---

## Commands

### Quick Reference

| Command | Aliases | Description |
|---------|---------|-------------|
| `/help` | `/h`, `/?` | Show available commands |
| `/analyze` | `/a`, `/stock` | Complete stock analysis |
| `/technical` | `/ta`, `/tech` | Technical analysis only |
| `/fundamental` | `/fa`, `/fund` | Fundamental analysis only |
| `/broker` | `/b`, `/flow` | Broker flow analysis (single day) |
| `/bandar` | `/bm`, `/bandarmology` | **Bandarmology analysis (multi-day)** |
| `/chart` | `/c`, `/grafik` | Generate price chart |
| `/forecast` | `/fc`, `/prediksi` | Price prediction |
| `/screen` | `/s`, `/filter` | Stock screening |
| `/sector` | `/sec` | Sector analysis |
| `/compare` | `/cmp`, `/vs` | Compare multiple stocks |
| `/plan` | `/tp`, `/sl` | Trading plan generator |
| `/sapta` | `/premarkup` | SAPTA pre-markup detection |
| `/ihsg` | `/index`, `/market` | Market index status |
| `/models` | `/model`, `/m` | Switch AI model |
| `/auth` | `/login` | Stockbit authentication (set token) |
| `/clear` | `/cls` | Clear chat history |

### Command Details

#### `/analyze <TICKER>` - Complete Analysis

Analisis lengkap mencakup harga, teknikal, dan AI insight.

```
/analyze BBCA
```

Output:
```
BBCA - Bank Central Asia Tbk

Price: Rp 9,850 (+75, +0.77%)
Volume: 15,234,500 (Avg: 12,456,000)
Range: 9,775 - 9,900
52W: 8,100 - 10,450

Technical:
  RSI(14): 58.3 - Neutral
  MACD: Bullish crossover
  Trend: Bullish
  Signal: Buy

AI Insight:
BBCA menunjukkan momentum positif dengan RSI di zona netral...
```

#### `/technical <TICKER>` - Technical Analysis

```
/technical BBRI
```

Output:
```
Technical Analysis: BBRI

  RSI(14): 45.2 (Neutral)
  MACD: -12.5 (Signal: -15.3) - Bullish
  SMA20: 5,425 | SMA50: 5,380
  Bollinger: 5,200 - 5,400 - 5,600
  Stochastic: K=35.2, D=38.5
  Support: 5,200 | Resistance: 5,600
  Trend: Sideways | Signal: Neutral
```

#### `/chart <TICKER> [period]` - Price Chart

Generate dan save chart sebagai PNG.

```
/chart TLKM 3mo
/chart ASII 1y
```

Periods: `1mo`, `3mo`, `6mo`, `1y`, `2y`

#### `/forecast <TICKER> [days]` - Price Forecast

```
/forecast UNVR 14
```

Output:
```
Forecast: UNVR (14 days)

Current: Rp 4,250
Target: Rp 4,420 (+4.00%)
Trend: UP
Support: Rp 4,100
Resistance: Rp 4,500
Confidence: 72%

Chart saved: charts/UNVR_forecast_20240115.png
```

#### `/screen <criteria>` - Stock Screening

**Preset Screeners:**

```
/screen oversold      # RSI < 30
/screen overbought    # RSI > 70
/screen bullish       # MACD bullish + price > SMA20
/screen bearish       # MACD bearish + price < SMA20
/screen breakout      # Near resistance + volume spike
/screen momentum      # RSI 50-70 + MACD bullish
/screen undervalued   # PE < 15 + ROE > 10%
```

**Flexible Criteria:**

```
/screen rsi<30
/screen pe<15
/screen rsi>70 and pe<20
```

**Universe Options:**

```
/screen oversold --universe=lq45      # 45 stocks (fast)
/screen bullish --universe=idx80      # 80 stocks
/screen momentum --universe=popular   # 113 stocks
/screen breakout --universe=all       # 955 stocks (slow)
```

#### `/plan <TICKER> [account_size]` - Trading Plan

```
/plan BBCA
/plan BBRI 50000000
```

Output:
```
TRADING PLAN: BBCA
Generated: 2024-01-15 14:30

=== ENTRY ===
Price: Rp 9,850 (current)
Type: Market
Trend: Bullish | Signal: Buy

=== TAKE PROFIT ===
TP1: Rp 10,150 (+3.05%) - Conservative
TP2: Rp 10,450 (+6.09%) - Moderate
TP3: Rp 10,800 (+9.64%) - Aggressive

=== STOP LOSS ===
SL: Rp 9,550 (-3.05%)
Method: Hybrid

=== RISK/REWARD ===
Risk: Rp 300 per share (3.05%)
Reward (TP1): Rp 300 (3.05%)
R:R to TP1: 1:1.0 [FAIR]
R:R to TP2: 1:2.0 [GOOD]

Trade Quality: FAIR
Confidence: 65%

=== POSITION SIZING (2% Risk) ===
Account: Rp 100,000,000
Max Risk: Rp 2,000,000
Suggested: 66 lot (6,600 shares)
Position Value: Rp 65,010,000 (65.0% of account)

=== EXECUTION STRATEGY ===
1. Entry: Buy at market or limit Rp 9,850
2. Set stop loss immediately at Rp 9,550
3. TP1: Sell 50% position at Rp 10,150
4. After TP1 hit: Move SL to breakeven
5. TP2: Sell remaining 50% at Rp 10,450
```

#### `/compare <TICKER1> <TICKER2> ...` - Compare Stocks

```
/compare BBCA BBRI BMRI BBNI
```

Output:
```
Stock Comparison

Ticker   Price        Change      Volume
------------------------------------------------
BBCA       9,850      +0.77%      15,234,500
BBRI       5,425      +1.23%      45,678,900
BMRI       6,150      +0.65%      23,456,700
BBNI       5,875      -0.42%      18,765,400
```

#### `/broker <TICKER>` - Broker Flow Analysis

Requires Stockbit authentication (see [Stockbit Authentication](#stockbit-authentication)).

```
/broker BBCA
```

Output:
```
BROKER SUMMARY - BBCA
============================================

TOP 5 BUYERS:
   SQ: 274,337 lot | Rp 222,457,800,000
   CC: 29,146 lot | Rp 23,690,252,500
   BB: 15,017 lot | Rp 12,166,650,000

TOP 5 SELLERS:
   BK: 67,196 lot | Rp 54,371,875,000
   KZ: 65,734 lot | Rp 53,276,152,500
   ZP: 62,642 lot | Rp 50,425,677,500

BANDAR DETECTOR:
   Overall: Acc
   Top 1: Big Acc (55%)
   Top 5: Normal Acc (17%)
```

#### `/auth` - Stockbit Authentication

Manage Stockbit token for broker flow analysis.

```
/auth                              # Check auth status
/auth status                       # Detailed token info
/auth set-token <JWT_TOKEN>        # Set token manually
```

Example:
```
/auth set-token eyJhbGciOiJSUzI1NiIs...
```

Output:
```
✅ Token saved successfully!

Token valid for: 23.5 hours
Saved to: data/stockbit/secrets.json

You can now use /broker command.
```

---

## Bandarmology Analysis

### Overview

**Bandarmology** adalah analisis mendalam tentang aktivitas broker (bandar) dalam trading saham. Fitur ini menganalisis data broker summary selama beberapa hari untuk mendeteksi pola akumulasi/distribusi dan kesiapan markup.

### Features

- **Multi-day Analysis** - Analisis 5-60 hari trading
- **Broker Profiling** - Klasifikasi broker berdasarkan karakteristik
- **Accumulation Phase Detection** - Deteksi fase akumulasi dari early hingga markup-ready
- **Pattern Recognition** - Deteksi pola seperti Crossing, Dominasi, Retail Trap
- **Flow Momentum Score** - Skor 0-100 untuk kekuatan flow
- **Markup Readiness Score** - Skor kesiapan markup

### Broker Profiles

| Profile | Brokers | Karakteristik |
|---------|---------|---------------|
| **Smart Money Foreign** | AK, BK, MS, GR, LG, KZ, CS, DX | Institusi asing, directional, high conviction |
| **Bandar/Gorengan** | SQ, MG, EP, DR, BZ | Sering terlibat pump & dump, hati-hati |
| **Retail** | XA, AZ, KI, YO, ZP | Platform retail, sering late, contrarian signal |
| **Local Institutional** | CC, NI, OD, TP, IF | Dana kelolaan lokal, lebih informed |
| **Market Maker** | YU, RX, PD | Sering di kedua sisi, lihat net position |

### Usage

**Single Stock Analysis:**

```
/bandar BBCA              # Analisis 10 hari (default)
/bandar BBRI 5            # Analisis 5 hari
/bandar ANTM 20           # Analisis 20 hari (~1 bulan)
/bandar TLKM --detailed   # Dengan daily timeline
```

**Scan for Markup Candidates:**

```
/bandar scan              # Scan LQ45
/bandar scan lq45         # Scan LQ45 (45 stocks)
/bandar scan idx80        # Scan IDX80 (80 stocks)
/bandar scan popular      # Scan popular stocks
```

### Example Output

```
=================================================================
BANDARMOLOGY REPORT: BBCA
Period: 10 days (2025-12-29 to 2026-01-08)
=================================================================

FLOW MOMENTUM: 78/100 [Buy] 🟢
MARKUP READINESS: 72/100
PHASE: Late Accumulation 📈
CONFIDENCE: 85%

-----------------------------------------------------------------
FLOW SUMMARY
-----------------------------------------------------------------
  Foreign Net     : +Rp 245.5B
  Smart Money Net : +Rp 180.2B
  Retail Net      : -Rp 45.3B
  Akumulasi Streak: 8 hari

-----------------------------------------------------------------
BROKER COMPOSITION
-----------------------------------------------------------------
  Smart Money :  45.0% ████████████░░░░░░░░
  Bandar      :  18.0% ███████░░░░░░░░░░░░░
  Retail      :  12.0% █████░░░░░░░░░░░░░░░
  Local Inst  :  25.0% ██████████░░░░░░░░░░

-----------------------------------------------------------------
PATTERN ALERTS
-----------------------------------------------------------------
  [+] HIGH Smart money akumulasi: AK, BK, MS NET BUY
  [+] Contrarian bullish: Retail jual, smart money beli
  [+] DOMINASI SQ menguasai 28% volume
  [+] HIGH MARKUP SIGNAL (4/4): 8 hari akumulasi, smart money NET BUY

-----------------------------------------------------------------
RECOMMENDATION
-----------------------------------------------------------------
  STRONG BUY - Akumulasi kuat, tunggu konfirmasi breakout.
```

### Accumulation Phases

| Phase | Description |
|-------|-------------|
| **Early Accumulation** | 2-3 hari konsisten beli |
| **Mid Accumulation** | 4-6 hari, volume mulai naik |
| **Late Accumulation** | 7+ hari, hampir siap markup |
| **Markup Ready** | Semua sinyal align, siap breakout |
| **Distribution** | Smart money mulai keluar |

### Pattern Detection

| Pattern | Description | Signal |
|---------|-------------|--------|
| **Crossing** | Broker sama di buy & sell side | Potensi distribusi terselubung |
| **Dominasi** | 1 broker > 25% volume | Big player masuk |
| **Retail Trap** | Retail beli, smart money jual | Bearish untuk retail |
| **Smart Money Entry** | Multiple SM brokers akumulasi | Bullish |
| **Markup Signal** | Semua kondisi align | Strong bullish |
| **Broker Consistency** | Broker sama beli berhari-hari | Akumulasi kuat |

---

## SAPTA Engine

### Overview

**SAPTA** (System for Analyzing Pre-markup Technical Accumulation) adalah engine ML-powered untuk mendeteksi saham yang sedang dalam fase **pre-markup** - fase akumulasi sebelum harga breakout.

### How It Works

SAPTA menggunakan 6 modul analisis:

| Module | Weight | Description |
|--------|--------|-------------|
| **Supply Absorption** | 25% | Deteksi akumulasi smart money melalui volume dan price action |
| **Compression** | 20% | Volatility contraction - range harga yang menyempit |
| **BB Squeeze** | 15% | Bollinger Band squeeze detection |
| **Elliott Wave** | 15% | Posisi wave dan Fibonacci retracement |
| **Time Projection** | 15% | Fibonacci time windows + planetary aspects |
| **Anti-Distribution** | 10% | Filter untuk menghindari fase distribusi |

### Status Levels

| Status | Score | Meaning |
|--------|-------|---------|
| **PRE-MARKUP** | >= 47 | Siap breakout dalam waktu dekat |
| **SIAP** | >= 35 | Hampir siap, perlu monitoring ketat |
| **WATCHLIST** | >= 24 | Masih dalam tahap akumulasi awal |
| **ABAIKAN** | < 24 | Belum menunjukkan sinyal pre-markup |

### Usage

**Single Stock Analysis:**

```
/sapta BBCA
/sapta ANTM --detailed
```

**Scan Multiple Stocks:**

```
/sapta scan              # Scan LQ45 (default)
/sapta scan lq45         # 45 stocks
/sapta scan idx80        # 80 stocks
/sapta scan popular      # 113 stocks
/sapta scan all          # 955 stocks
```

**Natural Language:**

```
> carikan saham pre-markup
> carikan saham siap breakout
> scan pre-markup semua saham
```

### Example Output

```
SAPTA Analysis: ANTM
========================================
Status: [PRE-MARKUP]
Score: 68.5/100
Confidence: HIGH
ML Probability: 78%
Wave Phase: Wave 3 (Impulse)
Fib Retracement: 61.8%
Projected Window: 5-8 days
Days to Window: 3

Module Breakdown
------------------------------
  [+] Absorption: 22.5/25
  [+] Compression: 18.0/20
  [+] BB Squeeze: 12.0/15
  [+] Elliott: 10.5/15
  [-] Time Projection: 5.5/15
  [+] Anti-Distribution: 0.0/10

Signals
------------------------------
  - High volume accumulation detected
  - Volatility compression 15 days
  - Bollinger squeeze active
  - Wave 3 position confirmed
  - Near Fibonacci time cluster
```

---

## Configuration

### Environment Variables

Create `.env` file in project root:

```env
# AI Configuration (CLIProxyAPI)
PULSE_AI__BASE_URL=http://localhost:8317/v1
PULSE_AI__API_KEY=your api CliProxyAPI
PULSE_AI__DEFAULT_MODEL=gemini-3-flash-preview

# Stockbit Authentication (for broker flow analysis)
# Option 1: Manual Token (RECOMMENDED - see "Stockbit Authentication" section)
STOCKBIT_TOKEN=eyJhbGciOiJSUzI1NiIs...

# Option 2: Username/Password (NOT recommended - CAPTCHA issues)
# STOCKBIT_USERNAME=your_username
# STOCKBIT_PASSWORD=your_password

# Debug
PULSE_DEBUG=false
```

---

## Stockbit Authentication

Broker flow analysis (`/broker` command) requires Stockbit authentication. Due to Stockbit's strict CAPTCHA protection, **manual token extraction** is the recommended method.

### Getting Your Stockbit Token

1. **Open Chrome** and go to https://stockbit.com
2. **Login** to your Stockbit account
3. **Open DevTools** (F12 or Cmd+Option+I on Mac)
4. Go to **Network** tab
5. **Click any stock** (e.g., BBCA) to trigger API requests
6. **Filter** requests by typing `exodus` in the filter box
7. **Click** on any request to `exodus.stockbit.com`
8. In the **Headers** tab, find `authorization: Bearer eyJhbG...`
9. **Copy** the token (everything after "Bearer ")

### Setting Your Token

**Method 1: Environment Variable (Recommended)**

Add to your `.env` file:
```env
STOCKBIT_TOKEN=eyJhbGciOiJSUzI1NiIs...your_full_token_here
```

**Method 2: CLI Command**

```
/auth set-token eyJhbGciOiJSUzI1NiIs...your_full_token_here
```

**Method 3: Direct File Edit**

Edit `data/stockbit/secrets.json`:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...your_full_token_here",
  "updated_at": 1704700000
}
```

### Token Status Commands

```
/auth              # Check authentication status
/auth status       # Detailed token status (expiry, source)
/auth set-token    # Show instructions for setting token
```

### Important Notes

- **Token expires in ~24 hours** - you'll need to refresh it daily
- Token is stored locally and never sent anywhere except Stockbit API
- If you see "Unauthorized" errors, your token has expired - get a new one
- Priority: `STOCKBIT_TOKEN` env var → `secrets.json` file

### Configuration File

Edit `config/pulse.yaml`:

```yaml
# AI Settings (CLIProxyAPI)
ai:
  base_url: "http://localhost:8317/v1"
  api_key: "opencode"
  default_model: "gemini-3-flash-preview"
  temperature: 0.7
  max_tokens: 4096
  timeout: 120

# Data Settings
data:
  cache_ttl: 3600  # 1 hour
  default_period: "3mo"

# Analysis Settings
analysis:
  rsi_period: 14
  rsi_oversold: 30
  rsi_overbought: 70
  macd_fast: 12
  macd_slow: 26
  macd_signal: 9

# UI Settings
ui:
  theme: "dark"
  chart_width: 60
  chart_height: 15
  max_results: 50
```

### Available AI Models

| Model ID | Display Name |
|----------|--------------|
| `gemini-3-flash-preview` | Gemini 3 Flash Preview |
| `gemini-2.5-flash` | Gemini 2.5 Flash |
| `gemini-2.5-flash-lite` | Gemini 2.5 Flash Lite |
| `gemini-claude-sonnet-4-5` | Claude Sonnet 4.5 |
| `gemini-claude-sonnet-4-5-thinking` | Claude Sonnet 4.5 Thinking |
| `gemini-claude-opus-4-5-thinking` | Claude Opus 4.5 Thinking |
| `gpt-oss-120b-medium` | GPT OSS 120B Medium |

Switch model:
```
/models              # Open model selector
/models gemini-3-flash-preview
```

---

## Stock Universe

### Preset Universes

| Universe | Count | Description |
|----------|-------|-------------|
| `LQ45` | 45 | Most liquid stocks |
| `IDX80` | 83 | LQ45 + additional liquid stocks |
| `POPULAR` | 113 | LQ45 + IDX80 + high retail interest |
| `ALL` | 955 | All IDX listed stocks |

### Data Source

Stock data fetched from Yahoo Finance with `.JK` suffix for Indonesian stocks.

Supported indices:
- **IHSG** (^JKSE) - IDX Composite
- **LQ45** (^JKLQ45) - IDX LQ45
- **IDX30** (^JKIDX30) - IDX30
- **JII** (^JKII) - Jakarta Islamic Index

---

## Project Structure

```
pulse-cli/
├── pulse/
│   ├── __init__.py
│   ├── cli/                      # TUI Application
│   │   ├── __init__.py
│   │   ├── app.py                # Main Textual app
│   │   └── commands/
│   │       ├── __init__.py
│   │       └── registry.py       # Command handlers
│   │
│   ├── core/                     # Core Business Logic
│   │   ├── __init__.py
│   │   ├── config.py             # Settings (Pydantic)
│   │   ├── models.py             # Data models
│   │   ├── smart_agent.py        # Agentic AI orchestrator
│   │   ├── screener.py           # Stock screening
│   │   ├── trading_plan.py       # TP/SL generator
│   │   ├── chart_generator.py    # PNG charts
│   │   ├── forecasting.py        # Price prediction
│   │   │
│   │   ├── data/                 # Data Layer
│   │   │   ├── __init__.py
│   │   │   ├── yfinance.py       # Yahoo Finance fetcher
│   │   │   ├── stockbit.py       # Stockbit integration
│   │   │   └── cache.py          # Disk cache
│   │   │
│   │   ├── analysis/             # Analysis Modules
│   │   │   ├── __init__.py
│   │   │   ├── technical.py      # Technical indicators
│   │   │   ├── fundamental.py    # Fundamental analysis
│   │   │   ├── broker_flow.py    # Broker flow
│   │   │   └── sector.py         # Sector analysis
│   │   │
│   │   └── sapta/                # SAPTA Engine
│   │       ├── __init__.py
│   │       ├── engine.py         # Main orchestrator
│   │       ├── models.py         # SAPTA models
│   │       ├── modules/          # 6 Analysis modules
│   │       │   ├── __init__.py
│   │       │   ├── base.py
│   │       │   ├── absorption.py
│   │       │   ├── compression.py
│   │       │   ├── bb_squeeze.py
│   │       │   ├── elliott.py
│   │       │   ├── time_projection.py
│   │       │   └── anti_distribution.py
│   │       ├── ml/               # Machine Learning
│   │       │   ├── __init__.py
│   │       │   ├── trainer.py
│   │       │   ├── features.py
│   │       │   ├── labeling.py
│   │       │   └── data_loader.py
│   │       └── data/             # Trained models
│   │           ├── sapta_model.pkl
│   │           └── thresholds.json
│   │
│   ├── ai/                       # AI Integration
│   │   ├── __init__.py
│   │   ├── client.py             # OpenAI-compatible client
│   │   └── prompts.py            # System prompts
│   │
│   └── utils/                    # Utilities
│       ├── __init__.py
│       ├── logger.py
│       ├── formatters.py
│       ├── validators.py
│       └── constants.py
│
├── config/
│   └── pulse.yaml                # Configuration file
│
├── data/
│   ├── tickers.json              # 955 IDX tickers
│   └── cache/                    # Disk cache
│
├── tests/                        # Test suite
│   └── ...
│
├── pyproject.toml                # Project config & dependencies
├── README.md                     # This file
├── .env.example                  # Environment template
└── .gitignore
```

---

## Development

### Setup Development Environment

```bash
# Clone and install
git clone https://github.com/yourusername/pulse-cli.git
cd pulse-cli

# Create venv
python -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pulse --cov-report=html

# Run specific test
pytest tests/test_core/test_screener.py -v
```

### Code Quality

```bash
# Linting with ruff
ruff check pulse/

# Type checking with mypy
mypy pulse/

# Format code
ruff format pulse/
```

### Training SAPTA Model

```bash
# Train new model with historical data
python -m pulse.core.sapta.ml.train_model

# This will:
# 1. Load historical price data
# 2. Generate features from 6 modules
# 3. Label data based on forward returns
# 4. Train XGBoost classifier
# 5. Save model to pulse/core/sapta/data/
```

---

## Troubleshooting

### Common Issues

**1. "No data found for XXXX"**

```
Cause: Ticker tidak valid atau tidak ada di Yahoo Finance
Solution: Pastikan ticker benar dengan suffix .JK (contoh: BBCA.JK)
```

**2. "AI request failed"**

```
Cause: AI backend tidak tersedia
Solution: 
  - Pastikan CLIProxyAPI running di localhost:8317
  - Atau ubah PULSE_AI__BASE_URL di .env
```

**3. "Insufficient data for SAPTA"**

```
Cause: Saham baru listing atau data historis < 100 hari
Solution: SAPTA membutuhkan minimal 100 hari data historis
```

**4. "Stockbit not authenticated" or "Unauthorized"**

```
Cause: Token tidak ada atau sudah expired (token valid ~24 jam)
Solution: 
  1. Dapatkan token baru dari browser (lihat "Stockbit Authentication" section)
  2. Set token dengan: /auth set-token <TOKEN>
  3. Atau tambahkan ke .env: STOCKBIT_TOKEN=<TOKEN>
```

**5. "Token is expired"**

```
Cause: Stockbit token hanya valid ~24 jam
Solution:
  1. Login ulang ke stockbit.com di browser
  2. Copy token baru dari DevTools > Network > Authorization header
  3. Update dengan /auth set-token atau edit .env
```

### Debug Mode

Enable debug logging:

```bash
PULSE_DEBUG=true pulse
```

Or in `.env`:
```env
PULSE_DEBUG=true
```

---

## Roadmap

- [ ] **v0.2.0** - Watchlist & Portfolio tracking
- [ ] **v0.2.1** - Alert notifications
- [ ] **v0.3.0** - Backtesting framework
- [ ] **v0.4.0** - Strategy builder
- [ ] **v0.5.0** - Multi-market support (US, Crypto)
- [ ] **v1.0.0** - Stable release

---

## Contributing

Contributions are welcome! Please read our contributing guidelines first.

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## Disclaimer

**IMPORTANT:** Pulse CLI is for **educational and informational purposes only**. 

- Not financial advice
- Past performance doesn't guarantee future results
- Always do your own research (DYOR)
- Invest responsibly

The developers are not responsible for any financial losses incurred from using this tool.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [Textual](https://github.com/Textualize/textual) - Amazing TUI framework
- [yfinance](https://github.com/ranaroussi/yfinance) - Yahoo Finance API wrapper
- [TA-Lib](https://github.com/bukosabino/ta) - Technical analysis library
- [Rich](https://github.com/Textualize/rich) - Beautiful terminal formatting

---

<div align="center">

**Made with :heart: for Indonesian Stock Market**

[Report Bug](https://github.com/sukirman1901/Pulse-CLI/issues) • [Request Feature](https://github.com/sukirman1901/Pulse-CLI/issues)

</div>
