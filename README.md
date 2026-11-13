# ⚡ The Bitcoin Score

> **Accumulate BTC better. With numbers.**  
> A single 0–100 contrarian accumulation metric driven by 8 independent on-chain, technical, and macroeconomic market indicators.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://thebitcoinscore-7f64tlr4wik5bv3gd2pfzs.streamlit.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

---

## 🎯 Overview

Most retail market participants buy aggressively when Bitcoin is trading at all-time highs and stop accumulating during brutal bear-market bottoms. **The Bitcoin Score** flips emotional bias on its head using a transparent, multi-factor framework:

- **0–25 (Overheated):** Parabolic momentum, extreme greed, elevated MVRV. Caution advised.
- **25–40 (Caution):** Neutral to overheated conditions.
- **40–60 (Neutral):** Fair-value equilibrium (~50% of historical time). Normal DCA suggested.
- **60–75 (Buy More):** Undervaluation signals emerging across liquidity and on-chain metrics (+25% DCA).
- **75–100 (Strong Buy):** Rare, deep cyclical bottoms with extreme fear and historical capitulation (+50% DCA).

---

## 🔬 The 8 Market Indicators

| Indicator | Type | Weight | Description |
| :--- | :--- | :---: | :--- |
| **MVRV Z-Score** | On-Chain | 20% | Market Value vs. Realized Value of all coins on-chain. |
| **200-Day EMA Ratio** | Technical | 15% | Price distance above/below institutional 200-day trend. |
| **RSI-14 (Wilder)** | Technical | 10% | 14-day momentum smoothed with Wilder's original formula. |
| **Crypto Fear & Greed** | Sentiment | 15% | Multi-source sentiment index quantifying market panic/greed. |
| **US M2 Money Supply YoY** | Macro | 10% | Annual change in Federal Reserve M2 liquidity. |
| **US Dollar Index (DXY)** | Macro | 10% | Global reserve fiat currency strength and risk appetite. |
| **Google Trends (Bitcoin)** | Public Interest | 10% | Worldwide search interest measuring retail curiosity. |
| **Bitcoin Dominance** | Market Structure | 10% | BTC market cap share relative to the total crypto market. |

---

## ✨ Features

- **Real-Time BTC Price (5s):** Live price feeds via Binance & CoinGecko with smooth highlight transitions.
- **Interactive Smart DCA Calculator:** Adjust daily dollar allocation and calculate suggested Bitcoin sats in real time based on current score regime.
- **Interactive Dual-Axis Chart:** Plotly chart displaying the historical score trajectory alongside BTC price (with Logarithmic scale and 200d EMA toggle).
- **Live Bitcoin News:** Automated news feed curating the latest articles from [Bitcoin Magazine](https://bitcoinmagazine.com/), translated into Turkish.
- **Bilingual Interface:** Full seamless support for both English (EN) and Turkish (TR).
- **Dark Glassmorphic UI:** Modern responsive dashboard styled with custom CSS and typography.

---

## 🚀 Quick Start (Local Run)

### 1. Clone the repository
```bash
git clone https://github.com/Twirksuuu/thebitcoinscore.git
cd thebitcoinscore
```

### 2. Set up virtual environment
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Streamlit application
```bash
streamlit run app.py
```
Open your browser and navigate to `http://localhost:8501`.

---

## 🌐 Live Demo & Custom Domain

- **Streamlit Community Cloud:** [thebitcoinscore-7f64tlr4wik5bv3gd2pfzs.streamlit.app](https://thebitcoinscore-7f64tlr4wik5bv3gd2pfzs.streamlit.app/)
- **Custom Domain:** `breachy.store` / `www.breachy.store`

---

## ⚠️ Disclaimer (Educational Purpose Only)

This project and all metrics, scores, charts, and news feeds provided on **The Bitcoin Score** are strictly for **educational and informational purposes only** and do **not** constitute financial, investment, or trading advice. Always do your own research (DYOR) before making any financial decisions.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
