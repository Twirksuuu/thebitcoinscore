"""
The Bitcoin Score — Next-Gen Contrarian BTC Accumulation Dashboard (app.py)
Designed after https://thebitcoinscore.com/ and enhanced with:
- Full EN / TR / ES localization toggle
- Exact Hero Card with giant Score (e.g. 68 /100), BUY MORE pill, live BTC Price,
  5-segment horizontal gauge with diamond needle (◆), and instant-keystroke 3-column DCA Calculator
- 4x2 Interactive 8-Signal Grid with live 30-day SVG sparklines + hover/click animated inspector
- Dynamic "Why Today's Score?" 4-factor synthesis panel
- Dual-Axis Interactive Chart (Gold Score trajectory vs. BTC Price & EMA200)
- Animated Horizontal Expanding 8-Signals Story Accordion
- Interactive Historical DCA Backtester (Smart Score DCA vs. Flat DCA)
- Time Spent in Each Zone, Real-World Cycle Examples & Smooth FAQ Accordion
"""

from __future__ import annotations

import importlib
import json
import os
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import streamlit.components.v1 as components

import data_fetcher
import scoring

from data_fetcher import build_master_dataset, fetch_bitcoin_magazine_news
from scoring import (
    SIGNAL_WEIGHTS,
    classify_score_zone,
    compute_accumulation_score,
    get_zone_distribution_report,
    run_dca_backtest,
)

# ---------------------------------------------------------------------------
# PAGE CONFIG & GLOBAL CSS (MATCHING THEBITCOINSCORE.COM + GLASSMORPHIC POLISH)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="The Bitcoin Score | Accumulate BTC better. With numbers.",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;600;700;800&display=swap');

    .stApp {
        background:
            radial-gradient(900px 520px at 8% -6%, rgba(247,147,26,0.13), transparent 60%),
            radial-gradient(700px 480px at 100% 30%, rgba(16,185,129,0.06), transparent 60%),
            #0a0e14;
        background-attachment: fixed;
        color: #f1f5f9;
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif;
    }
    /* Hide Streamlit chrome */
    header[data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu, footer,
    [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display:none !important; }

    /* Entrance animation */
    @keyframes riseIn { from {opacity:0; transform:translateY(14px);} to {opacity:1; transform:none;} }
    .tbs-header { animation: riseIn .6s cubic-bezier(.22,1,.36,1) both; }
    .tbs-card { transition: transform .25s ease, border-color .25s ease, box-shadow .25s ease; }
    .tbs-card:hover { transform: translateY(-3px); border-color: rgba(247,147,26,.45); box-shadow: 0 18px 40px rgba(0,0,0,.5); }
    .why-box { background: linear-gradient(160deg, rgba(19,24,34,.9), rgba(13,17,24,.9)); backdrop-filter: blur(8px); }
    .why-item { transition: background .2s ease, padding-left .2s ease; border-radius: 8px; }
    .why-item:hover { background: rgba(247,147,26,.05); padding-left: 8px; }

    /* Streamlit widgets in brand style */
    [data-testid="stExpander"] { background:#11161f; border:1px solid #1f2937 !important; border-radius:14px !important; margin-bottom:10px; }
    [data-testid="stExpander"] summary:hover { color:#f7931a !important; }
    [data-testid="stDateInput"] input, [data-testid="stNumberInput"] input {
        background:#131822 !important; border-radius:10px !important; font-family:'JetBrains Mono',monospace !important; }
    [data-baseweb="input"], [data-baseweb="base-input"] { background:#131822 !important; border-color:#263142 !important; border-radius:10px !important; }
    [data-testid="stSegmentedControl"] button, [data-testid="stButtonGroup"] button {
        background:#131822 !important; border:1px solid #263142 !important; color:#94a3b8 !important;
        font-family:'JetBrains Mono',monospace !important; font-weight:700 !important; transition: all .2s ease; }
    [data-testid="stSegmentedControl"] button[aria-checked="true"], [data-testid="stButtonGroup"] button[aria-checked="true"],
    [data-testid="stButtonGroup"] button[kind$="Active"] {
        background:rgba(247,147,26,.15) !important; border-color:#f7931a !important; color:#fff !important; }
    [data-testid="stWidgetLabel"] p { color:#94a3b8 !important; font-size:.74rem !important; letter-spacing:.08em; text-transform:uppercase; font-weight:700 !important; }
    [data-testid="stPlotlyChart"] { border:1px solid #1f2937; border-radius:16px; overflow:hidden; }
    ::-webkit-scrollbar { width:8px; } ::-webkit-scrollbar-thumb { background:#1f2937; border-radius:8px; }
    ::-webkit-scrollbar-thumb:hover { background:#f7931a; }
    [data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #1f2937;
    }
    .block-container {
        padding-top: 1.8rem !important;
        padding-bottom: 3.5rem !important;
        max-width: 1120px !important;
    }

    /* Top Header matching thebitcoinscore.com */
    .tbs-header {
        margin-bottom: 22px;
    }
    .tbs-top-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 16px;
        margin-bottom: 14px;
    }
    .tbs-logo-group {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .tbs-logo-wrap {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
    }
    .tbs-orange-circle {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: #f7931a;
        color: #0a0e14;
        font-weight: 900;
        font-size: 1.55rem;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 22px rgba(247, 147, 26, 0.35);
    }
    .tbs-tri-bars {
        display: flex;
        gap: 3px;
    }
    .tbs-tri-bar {
        width: 11px;
        height: 4px;
        border-radius: 2px;
    }
    .tbs-main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.6px;
        line-height: 1.1;
    }

    .tbs-pill-bar {
        display: inline-flex;
        align-items: center;
        background: #131822;
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 5px 12px;
        gap: 8px;
        font-size: 0.75rem;
        color: #94a3b8;
        font-weight: 600;
        letter-spacing: 0.06em;
    }
    .tbs-live-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        color: #10b981;
        font-weight: 700;
    }
    .tbs-live-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10b981;
        box-shadow: 0 0 8px #10b981;
        animation: pulseLive 2s infinite;
    }
    @keyframes pulseLive {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(0.85); }
    }

    .tbs-orange-divider {
        height: 1px;
        background: linear-gradient(90deg, #f7931a 0%, rgba(247, 147, 26, 0.25) 55%, rgba(31, 41, 55, 0.1) 100%);
        margin: 14px 0 16px 0;
    }
    .tbs-tagline {
        font-size: 1.08rem;
        color: #cbd5e1;
        font-weight: 500;
        margin-bottom: 6px;
    }
    .tbs-subdesc {
        font-size: 0.94rem;
        color: #94a3b8;
        line-height: 1.5;
    }

    /* Why Today's Score Synthesis Box */
    .why-box {
        background: #11161f;
        border: 1px solid #1f2937;
        border-radius: 16px;
        padding: 22px 26px;
        margin: 20px 0;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
    }
    .why-title {
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.1em;
        color: #f7931a;
        text-transform: uppercase;
        margin-bottom: 12px;
    }
    .why-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 9px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        font-size: 0.95rem;
        color: #e2e8f0;
    }
    .why-item:last-child {
        border-bottom: none;
    }
    .why-dot {
        width: 9px;
        height: 9px;
        border-radius: 50%;
        flex-shrink: 0;
    }

    /* Section Headers */
    .sec-title-row {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        margin: 30px 0 14px 0;
        flex-wrap: wrap;
        gap: 8px;
    }
    .sec-title {
        font-size: 1.25rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.3px;
    }
    .sec-title span {
        color: #f7931a;
    }
    .sec-sub {
        font-size: 0.85rem;
        color: #64748b;
    }

    /* Story & Backtest Cards */
    .tbs-card {
        background: #11161f;
        border: 1px solid #1f2937;
        border-radius: 16px;
        padding: 24px 26px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        height: 100%;
    }
    .zone-bar-row {
        margin-bottom: 14px;
    }
    .zone-bar-top {
        display: flex;
        justify-content: space-between;
        font-weight: 700;
        font-size: 0.98rem;
        margin-bottom: 5px;
    }
    .zone-pill-fill {
        height: 12px;
        border-radius: 999px;
    }
    .zone-note {
        font-size: 0.84rem;
        color: #94a3b8;
        margin-top: 14px;
    }
    .cycle-item {
        padding-bottom: 12px;
        margin-bottom: 12px;
        border-bottom: 1px solid #1f2937;
    }
    .cycle-desc {
        font-size: 0.85rem;
        color: #94a3b8;
    }

    /* Bitcoin Magazine News Section */
    .news-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(310px, 1fr));
        gap: 16px;
        margin-top: 12px;
        margin-bottom: 18px;
    }
    .news-card {
        background: linear-gradient(165deg, #131924 0%, #0d1118 100%);
        border: 1px solid #1f2937;
        border-radius: 16px;
        padding: 16px 18px;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        gap: 12px;
        height: auto;
        text-decoration: none !important;
        transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.38);
        position: relative;
        overflow: hidden;
    }
    .news-card:hover {
        transform: translateY(-4px);
        border-color: rgba(247, 147, 26, 0.65);
        box-shadow: 0 18px 40px rgba(0, 0, 0, 0.55), 0 0 20px rgba(247, 147, 26, 0.12);
    }
    .news-card-featured {
        grid-column: span 2;
        display: grid;
        grid-template-columns: 1.25fr 1fr;
        gap: 22px;
        align-items: center;
    }
    @media (max-width: 820px) {
        .block-container {
            padding-left: 0.85rem !important;
            padding-right: 0.85rem !important;
            padding-top: 1rem !important;
        }
        .tbs-top-row {
            flex-direction: column;
            align-items: flex-start;
            gap: 10px;
        }
        .tbs-logo-text {
            font-size: 1.45rem !important;
        }
        .news-grid {
            grid-template-columns: 1fr !important;
            gap: 14px !important;
        }
        .news-card-featured {
            grid-column: span 1;
            grid-template-columns: 1fr;
        }
        .news-card-featured .news-thumb-wrap {
            height: 175px;
        }
    }
    .news-thumb-wrap {
        width: 100%;
        height: 235px;
        border-radius: 12px;
        overflow: hidden;
        margin-bottom: 12px;
        background-color: transparent;
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        border: none;
    }
    .news-card-featured .news-thumb-wrap {
        height: 270px;
        margin-bottom: 0;
    }
    .news-thumb {
        width: 100% !important;
        height: 100% !important;
        max-width: none !important;
        object-fit: cover !important;
        display: block !important;
        margin: 0 !important;
        transition: transform 0.35s ease;
    }
    .news-card:hover .news-thumb {
        transform: scale(1.04);
    }
    .news-meta-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        margin-bottom: 9px;
    }
    .news-badge {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #f7931a;
        background: rgba(247, 147, 26, 0.12);
        border: 1px solid rgba(247, 147, 26, 0.35);
        padding: 3px 9px;
        border-radius: 999px;
    }
    .news-date {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.70rem;
        color: #64748b;
    }
    .news-headline {
        font-size: 1.06rem;
        font-weight: 800;
        color: #f8fafc;
        line-height: 1.38;
        margin-bottom: 8px;
        transition: color 0.2s ease;
    }
    .news-card-featured .news-headline {
        font-size: 1.28rem;
    }
    .news-card:hover .news-headline {
        color: #f7931a;
    }
    .news-excerpt {
        font-size: 0.86rem;
        color: #94a3b8;
        line-height: 1.5;
        margin-bottom: 14px;
    }
    .news-footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 0.76rem;
        font-weight: 700;
        color: #cbd5e1;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
        padding-top: 10px;
        margin-top: auto;
    }
    .news-read-more {
        color: #f7931a;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.74rem;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# LOCALIZATION DICTIONARY (EN / TR)
# ---------------------------------------------------------------------------
I18N = {
    "EN": {
        "tagline": "Accumulate BTC better. With numbers.",
        "subdesc": "A single 0–100 score from 8 market indicators: 0 means overheated, 100 means a strong moment to accumulate.",
        "score_label": "SCORE",
        "btc_price_label": "BTC PRICE",
        "overheated": "OVERHEATED",
        "neutral": "NEUTRAL",
        "strong_buy": "STRONG BUY",
        "usual_contrib": "YOUR USUAL CONTRIBUTION",
        "suggested_dca": "SUGGESTED DCA",
        "to_put_in": "TO PUT IN TODAY",
        "sats_at_live": "sats at live price",
        "regime_lbl": "Regime",
        "calc_how": "HOW IT'S CALCULATED",
        "calc_why": "WHY IT MATTERS FOR ACCUMULATING BTC",
        "weight_lbl": "Weight",
        "trajectory_lbl": "30-DAY TRAJECTORY",
        "fav_accum": "Favorable for Accumulating",
        "neut_regime": "Neutral Regime",
        "caut_headwind": "Caution / Headwind",
        "indicators_title": "8 MARKET INDICATORS",
        "indicators_sub": "Hover or click any indicator card to unfold its 30-day sparkline & methodology",
        "why_title": "WHY TODAY'S SCORE? (KEY DRIVERS)",
        "why_mvrv_lbl": "On-Chain Valuation (MVRV)",
        "why_mvrv_txt": "realized value — well below the 3.5x cycle top threshold, signaling healthy accumulation territory.",
        "why_m2_lbl": "Global Liquidity (US M2)",
        "why_m2_txt": "year-over-year — expanding money supply acts as a structural tailwind for BTC.",
        "why_dxy_lbl": "Macro Dollar Index (DXY)",
        "why_dxy_risen": "risen",
        "why_dxy_fallen": "fallen",
        "why_dxy_headwind": "headwind for BTC",
        "why_dxy_tailwind": "tailwind for BTC",
        "why_sent_lbl": "Retail Sentiment & Search Interest",
        "why_sent_txt": "Google search interest sits in the",
        "why_sent_sub": "percentile — quiet accumulation without retail euphoria.",
        "chart_title": "SCORE VS. BITCOIN PRICE",
        "chart_sub": "Gold line = Accumulation Score (0–100) • Orange line = BTC Price (USD)",
        "log_scale_lbl": "Log BTC Scale",
        "ema_toggle_lbl": "Show 200d EMA",
        "backtest_title": "HISTORICAL VALIDATION & SMART DCA BACKTESTER",
        "backtest_sub": "Compare Score-Adjusted Smart DCA against Standard Flat DCA over any historical window",
        "bt_start_lbl": "Start Date",
        "bt_end_lbl": "End Date",
        "bt_daily_lbl": "Base Daily DCA Amount ($)",
        "bt_flat_title": "STANDARD FLAT DCA",
        "bt_smart_title": "SCORE-ADJUSTED SMART DCA",
        "bt_alpha_title": "SMART DCA ADVANTAGE (ALPHA)",
        "bt_total_invested": "Total Invested",
        "bt_curr_val": "Current Value",
        "bt_avg_price": "Avg Buy Price",
        "bt_cheaper_entry": "Cheaper Avg Entry",
        "bt_outperformance": "ROI Outperformance",
        "bt_period": "Tested Period",
        "days_lbl": "days",
        "zone_title": "TIME SPENT IN EACH ZONE (2018–2026 CALIBRATION)",
        "zone_sub": "Most of the time: neutral. Extremes are rare by design.",
        "cycle_title": "REAL-WORLD CYCLE BOTTOMS & TOPS",
        "cycle_ftx_sub": "Days from the actual FTX cycle bottom (~$15,500).",
        "cycle_bear_sub": "Deep in the 2018 bear market capitulation.",
        "cycle_ath_sub": "Weeks before the 2021 cycle all-time high (~$69,000).",
        "cycle_rally_sub": "Post-election parabolic rally (+50% above EMA200 trend while DXY rose).",
        "faq_title": "FREQUENTLY ASKED",
        "faq_span": "QUESTIONS",
        "news_title": "BITCOIN",
        "news_span": "NEWS",
        "news_sub": "Live 5 latest headlines sourced directly from BitcoinMagazine.com",
        "news_read": "Read on Bitcoin Magazine →",
        "fng_extreme_fear": "Extreme Fear",
        "fng_fear": "Fear",
        "fng_neutral": "Neutral",
        "fng_greed": "Greed",
        "fng_extreme_greed": "Extreme Greed",
        "rec_Strong Buy": "Increase Daily DCA by +50%",
        "recsub_Strong Buy": "Extreme fear & deep cycle valuation. Historically rare (~5% of days).",
        "rec_Buy More": "Increase Daily DCA by +25%",
        "recsub_Buy More": "Market flashes undervaluation signals.",
        "rec_Neutral": "Maintain Normal Daily DCA",
        "recsub_Neutral": "Market is at fair value equilibrium (~50% of days).",
        "rec_Caution": "Exercise Caution — Keep Base DCA",
        "recsub_Caution": "Momentum and valuations running warm (~20% of days).",
        "rec_Overheated": "Overheated Market — Pause Escalation",
        "recsub_Overheated": "Extreme greed and stretched valuation (~5% of days).",
    },
    "TR": {
        "tagline": "Sayılarla daha akıllı BTC biriktirin. Günlük DCA sinyali.",
        "subdesc": "8 piyasa göstergesinden tek bir 0–100 skoru: 0 aşırı ısınmış (tepe), 100 ise güçlü toplama/birikim fırsatını gösterir.",
        "score_label": "SKOR",
        "btc_price_label": "BTC FİYATI",
        "overheated": "AŞIRI ISINMIŞ",
        "neutral": "NÖTR",
        "strong_buy": "GÜÇLÜ ALIM",
        "usual_contrib": "NORMAL GÜNLÜK ALIMINIZ",
        "suggested_dca": "ÖNERİLEN ÇARPAN",
        "to_put_in": "BUGÜN ALINACAK TUTAR",
        "sats_at_live": "canlı fiyat ile yaklaşık satoshi",
        "regime_lbl": "Bölge",
        "calc_how": "NASIL HESAPLANIR?",
        "calc_why": "BTC BİRİKTİRMEK İÇİN NEDEN ÖNEMLİ?",
        "weight_lbl": "Ağırlık",
        "trajectory_lbl": "30 GÜNLÜK SEYİR",
        "fav_accum": "Birikim İçin Çok Uygun",
        "neut_regime": "Nötr Piyasa Dengesi",
        "caut_headwind": "Dikkat / Piyasa Rüzgarı Ters",
        "indicators_title": "8 PİYASA GÖSTERGESİ (CANLI)",
        "indicators_sub": "30 günlük trend grafiğini ve hesaplama detaylarını açmak için kartların üzerine gelin veya tıklayın",
        "why_title": "BUGÜNKÜ SKORUN NEDENİ (ANA ETKENLER)",
        "why_mvrv_lbl": "Zincir Üstü Değerleme (MVRV)",
        "why_mvrv_txt": "gerçekleşen piyasa değeri — 3.5x döngü tepe eşiğinin çok altında, sağlıklı birikim bölgesine işaret ediyor.",
        "why_m2_lbl": "Küresel Likidite (ABD M2)",
        "why_m2_txt": "yıllık büyüme — genişleyen para arzı Bitcoin için yapısal bir itici güç görevi görür.",
        "why_dxy_lbl": "Makro Dolar Endeksi (DXY)",
        "why_dxy_risen": "yükseldi",
        "why_dxy_fallen": "geriledi",
        "why_dxy_headwind": "BTC için karşı rüzgar (baskı)",
        "why_dxy_tailwind": "BTC için destekleyici rüzgar",
        "why_sent_lbl": "Bireysel İlgi & Arama Hacmi",
        "why_sent_txt": "Google arama ilgisi",
        "why_sent_sub": "yüzdelik dilimde — bireysel çılgınlık ve FOMO olmadan sessizce birikim yapılıyor.",
        "chart_title": "SKOR VE BITCOIN FİYAT GRAFİĞİ",
        "chart_sub": "Altın çizgi = Birikim Skoru (0–100) • Turuncu çizgi = BTC Fiyatı (USD)",
        "log_scale_lbl": "Logaritmik BTC Ölçeği",
        "ema_toggle_lbl": "200 Günlük EMA'yı Göster",
        "backtest_title": "TARİHSEL DOĞRULAMA & AKILLI DCA BACKTEST SİMÜLATÖRÜ",
        "backtest_sub": "Skor Bazlı Akıllı DCA stratejisini Standart Sabit DCA ile geçmiş veriler üzerinde karşılaştırın",
        "bt_start_lbl": "Başlangıç Tarihi",
        "bt_end_lbl": "Bitiş Tarihi",
        "bt_daily_lbl": "Temel Günlük DCA Tutarı ($)",
        "bt_flat_title": "STANDART SABİT DCA",
        "bt_smart_title": "SKOR AYARLI AKILLI DCA",
        "bt_alpha_title": "AKILLI DCA AVANTAJI (EKSTRA GETİRİ)",
        "bt_total_invested": "Toplam Yatırılan",
        "bt_curr_val": "Güncel Portföy Değeri",
        "bt_avg_price": "Ortalama Alış Maliyeti",
        "bt_cheaper_entry": "Daha Ucuz Alım İndirimi",
        "bt_outperformance": "Getiri Üstünlüğü (Alfa)",
        "bt_period": "Test Edilen Süre",
        "days_lbl": "gün",
        "zone_title": "HER BÖLGEDE GEÇİRİLEN ZAMAN (2018–2026 KALİBRASYONU)",
        "zone_sub": "Zamanın çoğu nötr geçer. Uç noktalar bilinçli olarak nadir görülür.",
        "cycle_title": "GERÇEK DÜNYADAN DÖNGÜ DİPLERİ VE TEPELERİ",
        "cycle_ftx_sub": "FTX çöküşündeki gerçek döngü dibine (~$15,500) sadece birkaç gün kala.",
        "cycle_bear_sub": "2018 ayı piyasasının en derin teslimiyet ve panik dönemi.",
        "cycle_ath_sub": "2021 döngüsünün tüm zamanlar rekorundan (~$69,000) birkaç hafta önce.",
        "cycle_rally_sub": "Seçim sonrası parabolik yükseliş (DXY artarken 200 günlük EMA'nın +%50 üzerine fırladı).",
        "faq_title": "SIKÇA SORULAN",
        "faq_span": "SORULAR",
        "news_title": "BITCOIN",
        "news_span": "HABERLERİ",
        "news_sub": "BitcoinMagazine.com kaynağından anlık çekilen son 5 güncel Bitcoin haberi",
        "news_read": "Haberi Oku (Bitcoin Magazine) →",
        "fng_extreme_fear": "Aşırı Korku",
        "fng_fear": "Korku",
        "fng_neutral": "Nötr",
        "fng_greed": "Açgözlülük",
        "fng_extreme_greed": "Aşırı Açgözlülük",
        "rec_Strong Buy": "Günlük DCA'nı %50 artır",
        "recsub_Strong Buy": "Aşırı korku ve derin döngü değeri. Tarihsel olarak nadir (~%5).",
        "rec_Buy More": "Günlük DCA'nı %25 artır",
        "recsub_Buy More": "Piyasa düşük değerlenme sinyalleri veriyor.",
        "rec_Neutral": "Normal günlük DCA'na devam et",
        "recsub_Neutral": "Piyasa adil değer dengesinde (~%50 zaman).",
        "rec_Caution": "Dikkatli ol — temel DCA'nı koru",
        "recsub_Caution": "Momentum ve değerleme ısınıyor (~%20 zaman).",
        "rec_Overheated": "Piyasa aşırı ısınmış — DCA'yı artırma",
        "recsub_Overheated": "Aşırı açgözlülük ve gergin değerleme (~%5 zaman).",
    },
}

SIGNALS_EXPLAINER = {
    "EN": [
        {
            "key": "mvrv",
            "title": "MVRV",
            "how": "Market Value divided by Realized Value — compares BTC's current price to the average price at which every coin last moved on-chain.",
            "why": "Near or below 1, the average holder is underwater — historically a strong signal of cycle bottoms. Above 3.5+ has flagged prior cycle tops.",
        },
        {
            "key": "google_trends",
            "title": "Google Trends",
            "how": "Worldwide search interest for \"Bitcoin,\" normalized 0–100 by Google itself.",
            "why": "Low interest often means the public isn't paying attention yet. Extreme search spikes have historically coincided with euphoric tops.",
        },
        {
            "key": "dxy",
            "title": "DXY",
            "how": "An official index tracking the US dollar's value against a basket of major currencies (EUR, JPY, GBP...). Pulled directly from the market.",
            "why": "BTC has historically moved inversely to the dollar. A weakening dollar has often coincided with risk assets like BTC gaining ground.",
        },
        {
            "key": "m2_yoy",
            "title": "Liquidity (M2)",
            "how": "Year-over-year growth in the US M2 money supply — cash, checking and savings deposits. Sourced directly from the Federal Reserve (FRED).",
            "why": "More money in the system tends to flow into risk assets over time. Expanding liquidity has historically been a tailwind for BTC.",
        },
        {
            "key": "fng",
            "title": "Fear & Greed",
            "how": "A daily 0–100 index blending market volatility, momentum, trading volume and social sentiment. Published by alternative.me.",
            "why": "Extreme fear has historically lined up with local bottoms — moments when buying felt terrible in the moment and great a year later.",
        },
        {
            "key": "ema200_ratio",
            "title": "EMA200 (daily)",
            "how": "The average closing price of the last 200 days, weighted so recent days count more. We measure how far today's price sits above or below it.",
            "why": "One of the most widely watched trend lines in all of finance. Deep dips below it have historically marked strong accumulation zones for BTC.",
        },
        {
            "key": "rsi14",
            "title": "RSI14",
            "how": "Relative Strength Index over the last 14 days — measures the speed and size of recent price moves on a 0–100 scale, using Wilder's original smoothing.",
            "why": "Below 30 is classic \"oversold\" territory (heavy selling, often overdone). Above 70 is \"overbought\" (rallies running hot).",
        },
        {
            "key": "btc_dominance",
            "title": "BTC Dominance",
            "how": "Bitcoin's share of the total cryptocurrency market cap, sourced from CoinGecko.",
            "why": "Rising dominance often signals capital consolidating into BTC over speculative altcoins. Weighted lightly (4%) as the most debated signal.",
        },
    ],
    "TR": [
        {
            "key": "mvrv",
            "title": "MVRV",
            "how": "Piyasa Değeri / Gerçekleşen Değer — BTC'nin anlık fiyatını, cüzdanlardaki her bir coinin zincir üstünde el değiştirdiği ortalama maliyetle karşılaştırır.",
            "why": "1 seviyesine yakın veya altında olması, ortalama yatırımcının zararda olduğunu gösterir — döngü diplerinin tarihsel en güçlü kanıtıdır. 3.5+ seviyeleri ise döngü tepelerini haber verir.",
        },
        {
            "key": "google_trends",
            "title": "Google Trends",
            "how": "Dünya genelinde \"Bitcoin\" kelimesinin Google tarafından 0–100 arasında normalize edilmiş doğrudan arama ilgisi.",
            "why": "Düşük arama ilgisi, henüz ana akım halkın piyasada olmadığını gösterir. Aşırı arama patlamaları ise daima coşkulu tepe noktalarıyla çakışmıştır.",
        },
        {
            "key": "dxy",
            "title": "DXY (Dolar Endeksi)",
            "how": "ABD dolarının majör para birimleri sepeti (EUR, JPY, GBP...) karşısındaki değerini ölçen resmi küresel endeks.",
            "why": "Bitcoin tarihsel olarak ABD doları ile ters korelasyon gösterir. Doların zayıflaması Bitcoin gibi risk ve değer saklama varlıklarına güçlü destek sağlar.",
        },
        {
            "key": "m2_yoy",
            "title": "Likidite (M2 Para Arzı)",
            "how": "ABD M2 para arzının (nakit, vadesiz ve tasarruf mevduatları) yıllık bazda (YoY) büyüme oranı. Doğrudan Fed verilerinden alınır.",
            "why": "Finansal sistemdeki para genişlemesi zamanla risk ve alternatif varlıklara akar. Büyüyen para arzı BTC birikimi için güçlü bir itici güçtür.",
        },
        {
            "key": "fng",
            "title": "Korku ve Açgözlülük",
            "how": "Piyasa volatilitesi, hacmi, sosyal medya ve anketleri harmanlayan 0–100 arası günlük duygu endeksi.",
            "why": "Aşırı korku (Extreme Fear), alım yapmanın en zor ancak 1 yıl sonra en karlı olduğu yerel dip noktalarıyla örtüşür.",
        },
        {
            "key": "ema200_ratio",
            "title": "EMA200 (200 Günlük)",
            "how": "Son 200 günün ağırlıklı kapanış ortalaması. Bugünün fiyatının bu uzun vadeli ortalamanın ne kadar altında/üstünde kaldığını ölçeriz.",
            "why": "Tüm finans dünyasının en çok izlediği ana trend çizgisi. Bu ortalamanın altına sarkan derin düşüşler BTC için tarihsel birikim fırsatı olmuştur.",
        },
        {
            "key": "rsi14",
            "title": "RSI14 (Göreceli Güç)",
            "how": "Wilder smoothing yöntemiyle son 14 günün fiyat hareket hızını ve momentumunu 0–100 aralığında ölçer.",
            "why": "30 altı aşırı satım (panik satışları, genellikle aşırıya kaçan dipler), 70 üzeri ise aşırı alım (piyasanın fazla ısındığı bölgeler) anlamına gelir.",
        },
        {
            "key": "btc_dominance",
            "title": "BTC Dominansı",
            "how": "Bitcoin'in toplam kripto piyasa değeri içindeki yüzde payı (CoinGecko).",
            "why": "Dominansın yükselmesi, spekülatif altcoinlerden çıkıp ana değer saklama varlığı Bitcoin'e kaçışı gösterir. En çok tartışılan metrik olduğu için ağırlığı düşük (%4) tutulmuştur.",
        },
    ],
}


def _fng_label(val: float, lang: str = "EN") -> str:
    lbls = I18N.get(lang, I18N["EN"])
    if val <= 24:
        return lbls.get("fng_extreme_fear", "Extreme Fear")
    if val <= 44:
        return lbls.get("fng_fear", "Fear")
    if val <= 55:
        return lbls.get("fng_neutral", "Neutral")
    if val <= 74:
        return lbls.get("fng_greed", "Greed")
    return lbls.get("fng_extreme_greed", "Extreme Greed")


def _signal_color(heat_sub_score: float) -> str:
    if heat_sub_score < 43.0:
        return "#10b981"
    if heat_sub_score <= 57.0:
        return "#94a3b8"
    return "#ef4444"


def _signal_status_text(heat_sub_score: float, lang: str = "EN") -> str:
    lbls = I18N.get(lang, I18N["EN"])
    if heat_sub_score < 43.0:
        return lbls.get("fav_accum", "Favorable for Accumulating")
    if heat_sub_score <= 57.0:
        return lbls.get("neut_regime", "Neutral Regime")
    return lbls.get("caut_headwind", "Caution / Headwind")


@st.cache_data(ttl=3600, show_spinner=False)
def load_scored_data(start_date: str, fred_api_key: str, force_refresh: bool = False) -> pd.DataFrame:
    cache_file = os.path.join(os.path.dirname(__file__), "btc_score_cache.csv")
    raw_df = build_master_dataset(
        start_date=start_date,
        fred_api_key=fred_api_key or None,
        cache_path=cache_file,
        cache_ttl_hours=1,
        force_refresh=force_refresh,
    )
    return compute_accumulation_score(raw_df, high_is_buy=True)


@st.cache_data(ttl=900, show_spinner=False)
def load_bitcoin_news(limit: int = 5, lang: str = "TR") -> list[dict[str, str]]:
    return fetch_bitcoin_magazine_news(limit=limit, target_lang=lang)


# ---------------------------------------------------------------------------
# HERO SCORE + INTERACTIVE DCA CALCULATOR + 8 SPARKLINE CARDS COMPONENT
# ---------------------------------------------------------------------------
def render_hero_and_signals_component(
    scored_df: pd.DataFrame, lang_dict: dict, lang: str = "TR", is_light: bool = False
) -> None:
    latest = scored_df.iloc[-1]
    last_30 = scored_df.iloc[-30:]
    score_val = int(round(float(latest["accumulation_score"])))
    zone = classify_score_zone(float(latest["accumulation_score"]), high_is_buy=True)

    btc_price = float(latest["close"])
    pct_1d = float(latest.get("pct_change_1d", 0.0))
    if pd.isna(pct_1d):
        pct_1d = 0.0
    pct_color = "#10b981" if pct_1d >= 0 else "#ef4444"
    pct_sign = "+" if pct_1d > 0 else ""

    fng_v = int(round(float(latest["fng"])))

    # Format display values for all 8 signals
    formatted_vals = {
        "mvrv": f"{float(latest['mvrv']):.2f}",
        "google_trends": f"{int(round(float(latest['google_trends'])))}",
        "dxy": f"{float(latest['dxy']):.2f}",
        "m2_yoy": f"{float(latest['m2_yoy']):.2f}%",
        "fng": f"{fng_v} ({_fng_label(fng_v, lang)})",
        "ema200_ratio": f"{float(latest['ema200_pct']):+.2f}%",
        "rsi14": f"{float(latest['rsi14']):.2f}",
        "btc_dominance": f"{float(latest['btc_dominance']):.2f}%",
    }

    series_col_map = {
        "mvrv": "mvrv",
        "google_trends": "google_trends",
        "dxy": "dxy",
        "m2_yoy": "m2_yoy",
        "fng": "fng",
        "ema200_ratio": "ema200_pct",
        "rsi14": "rsi14",
        "btc_dominance": "btc_dominance",
    }

    cards_payload = []
    dates_30 = [d.strftime("%b %d") for d in last_30.index]
    active_explainer = SIGNALS_EXPLAINER.get(lang, SIGNALS_EXPLAINER["EN"])
    for item in active_explainer:
        k = item["key"]
        col_name = series_col_map[k]
        heat_score = float(latest[f"score_{k}"])
        s_color = _signal_color(heat_score)
        s_status = _signal_status_text(heat_score, lang)
        vals_30 = [round(float(v), 2) for v in last_30[col_name].tolist()]
        weight_pct = int(round(SIGNAL_WEIGHTS[k] * 100))

        cards_payload.append(
            {
                "key": k,
                "title": item["title"],
                "val": formatted_vals[k],
                "color": s_color,
                "status": s_status,
                "weight": f"{weight_pct}%",
                "how": item["how"],
                "why": item["why"],
                "vals_30": vals_30,
                "dates_30": dates_30,
                "min_30": round(min(vals_30), 2),
                "max_30": round(max(vals_30), 2),
            }
        )

    payload_json = json.dumps(cards_payload)
    pointer_pct = min(max(float(latest["accumulation_score"]), 2.0), 98.0)
    mult = zone.dca_multiplier

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;600;700;800&display=swap');
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            background: transparent;
            color: #f1f5f9;
            font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
            overflow-x: hidden;
        }}

        /* 1. HERO CARD (Exact Match to thebitcoinscore.com + Enhanced Interactivity) */
        .hero-card {{
            background:
                radial-gradient(600px 260px at 0% 0%, {zone.color_hex}1f, transparent 65%),
                linear-gradient(165deg, #121824 0%, #0d1118 100%);
            border: 1px solid #1f2937;
            border-radius: 22px;
            padding: 32px 34px;
            box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255,255,255,0.04);
            margin-bottom: 26px;
            position: relative;
            overflow: hidden;
            animation: heroIn .7s cubic-bezier(.22,1,.36,1) both;
        }}
        .hero-card::before {{
            content:""; position:absolute; inset:0; border-radius:22px; padding:1px; pointer-events:none;
            background: linear-gradient(130deg, {zone.color_hex}88, transparent 35%, transparent 65%, rgba(247,147,26,.5));
            -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
            -webkit-mask-composite: xor; mask-composite: exclude;
        }}
        @keyframes heroIn {{ from {{opacity:0; transform:translateY(18px) scale(.985);}} to {{opacity:1; transform:none;}} }}
        @keyframes segIn {{ from {{transform:scaleX(0);}} to {{transform:scaleX(1);}} }}
        .g-seg {{ transform-origin:left; animation: segIn .7s cubic-bezier(.22,1,.36,1) both; }}
        .g-seg:nth-child(2){{animation-delay:.08s}} .g-seg:nth-child(3){{animation-delay:.16s}}
        .g-seg:nth-child(4){{animation-delay:.24s}} .g-seg:nth-child(5){{animation-delay:.32s}}
        @keyframes needleDrop {{ from {{opacity:0; transform:translate(-50%,-14px);}} to {{opacity:1; transform:translate(-50%,0);}} }}
        .ind-card {{ animation: heroIn .5s cubic-bezier(.22,1,.36,1) both; }}
        .hero-top-flex {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 20px;
            padding-bottom: 24px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.07);
        }}
        .score-giant-wrap {{
            display: flex;
            flex-direction: column;
            align-items: flex-start;
        }}
        .score-giant-row {{
            display: flex;
            align-items: baseline;
            gap: 6px;
        }}
        .score-giant {{
            font-size: 5.8rem;
            font-weight: 900;
            line-height: 0.92;
            letter-spacing: -3px;
            color: {zone.color_hex};
            text-shadow: 0 0 35px {zone.color_hex}40;
        }}
        .score-denom {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.35rem;
            font-weight: 600;
            color: #64748b;
        }}
        .zone-pill {{
            margin-top: 14px;
            display: inline-flex;
            align-items: center;
            padding: 5px 16px;
            border-radius: 999px;
            border: 1.5px solid {zone.color_hex};
            background: {zone.color_hex}15;
            color: {zone.color_hex};
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}

        /* BTC Price Block */
        .price-block {{
            text-align: right;
        }}
        .price-micro-label {{
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            color: #94a3b8;
            display: inline-flex;
            align-items: center;
            gap: 7px;
            margin-bottom: 6px;
        }}
        .live-pulse {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #10b981;
            box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
            animation: pulseGlow 2s infinite;
        }}
        @keyframes pulseGlow {{
            0% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }}
            70% {{ box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }}
        }}
        .price-row {{
            display: flex;
            align-items: baseline;
            justify-content: flex-end;
            gap: 10px;
        }}
        .price-val {{
            font-size: 2.35rem;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: -0.8px;
            transition: color 0.3s ease, text-shadow 0.3s ease;
        }}
        .price-val.price-flash,
        body.light-mode .price-val.price-flash {{
            color: #f7931a !important;
            text-shadow: 0 0 18px rgba(247, 147, 26, 0.45) !important;
        }}
        .price-chg {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.92rem;
            font-weight: 700;
            color: {pct_color};
        }}

        /* 5-Segment Gauge Bar with Vertical Tick & Diamond Needle */
        .gauge-section {{
            margin: 30px 0 26px 0;
        }}
        .gauge-bar-container {{
            position: relative;
            padding: 18px 0 10px 0;
        }}
        .gauge-segments {{
            display: grid;
            grid-template-columns: 25fr 15fr 20fr 15fr 25fr;
            gap: 5px;
            height: 9px;
            border-radius: 999px;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.6);
        }}
        .g-seg {{
            height: 100%;
            border-radius: 5px;
            position: relative;
        }}
        .needle-wrap {{
            position: absolute;
            top: -2px;
            left: {pointer_pct:.1f}%;
            transform: translateX(-50%);
            display: flex;
            flex-direction: column;
            align-items: center;
            pointer-events: none;
            animation: needleDrop .7s .4s cubic-bezier(.22,1,.36,1) both;
            z-index: 5;
            filter: drop-shadow(0 0 10px {zone.color_hex});
        }}
        .needle-svg {{
            width: 20px;
            height: 22px;
            animation: arrowBob 2s infinite ease-in-out;
        }}
        .needle-pulse-ring {{
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #ffffff;
            border: 2px solid {zone.color_hex};
            margin-top: -2px;
            box-shadow: 0 0 12px {zone.color_hex};
        }}
        @keyframes arrowBob {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-3px); }}
        }}
        .gauge-labels {{
            display: flex;
            justify-content: space-between;
            margin-top: 10px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.70rem;
            font-weight: 600;
            letter-spacing: 0.1em;
            color: #64748b;
        }}
        .g-lbl {{
            padding-top: 5px;
            border-top: 1px solid #334155;
        }}

        /* Dynamic Recommendation Headline */
        .dca-rec-title {{
            font-size: 1.75rem;
            font-weight: 800;
            color: {zone.color_hex};
            letter-spacing: -0.4px;
            margin-bottom: 6px;
        }}
        .dca-rec-sub {{
            font-size: 0.98rem;
            color: #94a3b8;
            margin-bottom: 22px;
        }}

        /* 3-Column Interactive DCA Calculator */
        .dca-calc-grid {{
            display: grid;
            grid-template-columns: 1.1fr 0.95fr 1.15fr;
            background: #0d1118;
            border: 1px solid #1f2937;
            border-radius: 14px;
            overflow: hidden;
            position: relative;
        }}
        .dca-col {{
            padding: 20px 22px;
            border-right: 1px solid #1f2937;
            position: relative;
        }}
        .dca-col:last-child {{
            border-right: none;
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(16, 185, 129, 0.04) 100%);
        }}
        .dca-col-lbl {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.70rem;
            font-weight: 700;
            letter-spacing: 0.09em;
            color: #94a3b8;
            text-transform: uppercase;
            margin-bottom: 12px;
        }}
        .dca-input-wrap {{
            display: flex;
            align-items: center;
            background: #131822;
            border: 1.5px solid #334155;
            border-radius: 10px;
            padding: 8px 14px;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }}
        .dca-input-wrap:focus-within {{
            border-color: #f7931a;
            box-shadow: 0 0 0 3px rgba(247, 147, 26, 0.2);
        }}
        .dollar-prefix {{
            font-size: 1.25rem;
            font-weight: 700;
            color: #64748b;
            margin-right: 6px;
        }}
        .dca-input {{
            background: transparent;
            border: none;
            outline: none;
            color: #ffffff;
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 1.45rem;
            font-weight: 800;
            width: 100%;
        }}
        .preset-row {{
            display: flex;
            align-items: center;
            gap: 6px;
            margin-top: 10px;
            flex-wrap: wrap;
        }}
        .preset-btn {{
            background: #161d29;
            border: 1px solid #263142;
            color: #94a3b8;
            border-radius: 6px;
            padding: 3px 9px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.18s ease;
        }}
        .preset-btn:hover {{
            border-color: #f7931a;
            color: #ffffff;
        }}
        .mult-val {{
            font-size: 2.25rem;
            font-weight: 800;
            color: #ffffff;
            margin-top: 4px;
        }}
        .eq-circle {{
            position: absolute;
            right: -15px;
            top: 50%;
            transform: translateY(-50%);
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: #131822;
            border: 1px solid #2d3748;
            color: #94a3b8;
            font-weight: 800;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 3;
        }}
        .today-out {{
            font-size: 2.35rem;
            font-weight: 900;
            color: #10b981;
            margin-top: 2px;
            letter-spacing: -0.5px;
        }}
        .sats-sub {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.76rem;
            color: #94a3b8;
            margin-top: 6px;
        }}

        /* 2. THE 8 MARKET INDICATORS (4x2 Grid + Animated Sparkline Inspector Drawer) */
        .ind-header-row {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin: 8px 0 12px 0;
        }}
        .ind-title {{
            font-size: 1.15rem;
            font-weight: 800;
            color: #ffffff;
        }}
        .ind-sub {{
            font-size: 0.82rem;
            color: #64748b;
        }}
        .ind-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
        }}
        .ind-card {{
            background: #11161f;
            border: 1px solid #1f2937;
            border-left: 3.5px solid #10b981;
            border-radius: 12px;
            padding: 14px 16px;
            cursor: pointer;
            transition: all 0.28s cubic-bezier(0.22, 1, 0.36, 1);
            position: relative;
        }}
        .ind-card:hover, .ind-card.selected {{
            transform: translateY(-2px);
            background: #161d2a;
            border-color: #f7931a;
            box-shadow: 0 10px 24px rgba(0, 0, 0, 0.45);
        }}
        .ind-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
        }}
        .ind-name {{
            font-size: 0.80rem;
            font-weight: 600;
            color: #94a3b8;
        }}
        .ind-dot {{
            width: 7px;
            height: 7px;
            border-radius: 50%;
        }}
        .ind-val-row {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
        }}
        .ind-val {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.22rem;
            font-weight: 800;
        }}
        .mini-spark {{
            width: 68px;
            height: 26px;
        }}

        /* Animated Expandable Signal Inspector Drawer */
        .inspector-drawer {{
            margin-top: 14px;
            background: linear-gradient(165deg, #131924 0%, #0d1118 100%);
            border: 1px solid rgba(247, 147, 26, 0.45);
            border-radius: 16px;
            padding: 22px 26px;
            display: grid;
            grid-template-columns: 1.15fr 1fr;
            gap: 26px;
            align-items: center;
            box-shadow: 0 14px 36px rgba(0, 0, 0, 0.6);
            transition: border-color 0.35s ease, box-shadow 0.35s ease;
            position: relative;
        }}
        .insp-content-anim {{
            animation: inspFadeSlide 0.38s cubic-bezier(0.22, 1, 0.36, 1) both;
        }}
        @keyframes inspFadeSlide {{
            from {{
                opacity: 0;
                transform: translateY(8px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        .insp-badge-row {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
        }}
        .insp-title {{
            font-size: 1.55rem;
            font-weight: 800;
            color: #ffffff;
        }}
        .insp-pill {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.74rem;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 999px;
        }}
        .insp-kicker {{
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            color: #f7931a;
            text-transform: uppercase;
            margin-top: 12px;
            margin-bottom: 4px;
        }}
        .insp-text {{
            font-size: 0.90rem;
            color: #cbd5e1;
            line-height: 1.52;
        }}
        .spark-box {{
            background: #0a0e14;
            border: 1px solid #1f2937;
            border-radius: 12px;
            padding: 14px 16px;
        }}
        .spark-header {{
            display: flex;
            justify-content: space-between;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.74rem;
            color: #94a3b8;
            margin-bottom: 8px;
        }}
        @media (max-width: 768px) {{
            .hero-card {{
                padding: 20px 16px;
                border-radius: 16px;
            }}
            .hero-top-flex {{
                flex-direction: column;
                align-items: flex-start;
                gap: 14px;
            }}
            .price-block {{
                text-align: left;
            }}
            .price-row {{
                justify-content: flex-start;
            }}
            .score-giant {{
                font-size: 3.4rem;
            }}
            .price-val {{
                font-size: 1.85rem;
            }}
            .dca-calc-grid {{
                grid-template-columns: 1fr !important;
                gap: 0 !important;
            }}
            .dca-col {{
                border-right: none !important;
                border-bottom: 1px solid rgba(148, 163, 184, 0.25);
            }}
            .dca-col:last-child {{
                border-bottom: none;
            }}
            .eq-circle {{
                display: none !important;
            }}
            .ind-header-row {{
                flex-direction: column;
                align-items: flex-start;
                gap: 4px;
            }}
            .ind-grid {{
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
            }}
            .inspector-drawer {{
                grid-template-columns: 1fr !important;
            }}
        }}
        @media (max-width: 440px) {{
            .ind-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        /* Light Mode Overrides (Soft Slate Toned Palette & High-Contrast Readability) */
        body.light-mode {{
            background: transparent !important;
            color: #0f172a !important;
        }}
        body.light-mode .hero-card {{
            background:
                radial-gradient(600px 260px at 0% 0%, {zone.color_hex}18, transparent 65%),
                linear-gradient(165deg, #f8fafc 0%, #f1f5f9 100%) !important;
            border: 1px solid #cbd5e1 !important;
            box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08) !important;
        }}
        body.light-mode .hero-card::before {{
            background: linear-gradient(130deg, {zone.color_hex}66, transparent 40%, transparent 65%, rgba(247, 147, 26, 0.35));
        }}
        body.light-mode .hero-top-flex {{
            border-bottom: 1px solid #cbd5e1 !important;
        }}
        body.light-mode .price-val {{
            color: #0f172a;
        }}
        body.light-mode .dca-input,
        body.light-mode .mult-val,
        body.light-mode .ind-title,
        body.light-mode .insp-title {{
            color: #0f172a !important;
        }}
        body.light-mode .score-denom,
        body.light-mode .price-micro-label,
        body.light-mode .dca-rec-sub,
        body.light-mode .dca-col-lbl,
        body.light-mode .sats-sub,
        body.light-mode .ind-sub,
        body.light-mode .ind-name,
        body.light-mode .spark-header,
        body.light-mode .gauge-labels {{
            color: #334155 !important;
            font-weight: 600 !important;
        }}
        body.light-mode .g-lbl {{
            border-top-color: #94a3b8 !important;
            color: #334155 !important;
        }}
        body.light-mode .gauge-segments {{
            box-shadow: inset 0 1px 3px rgba(15, 23, 42, 0.16) !important;
        }}
        body.light-mode .dca-calc-grid {{
            background: #e2e8f0 !important;
            border: 1px solid #cbd5e1 !important;
        }}
        body.light-mode .dca-col {{
            background: #f1f5f9 !important;
            border-right: 1px solid #cbd5e1 !important;
        }}
        body.light-mode .dca-col:last-child {{
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.16) 0%, rgba(16, 185, 129, 0.06) 100%) !important;
        }}
        body.light-mode .dca-input-wrap {{
            background: #ffffff !important;
            border: 1.5px solid #94a3b8 !important;
        }}
        body.light-mode .dollar-prefix {{
            color: #475569 !important;
        }}
        body.light-mode .preset-btn {{
            background: #ffffff !important;
            border: 1px solid #94a3b8 !important;
            color: #1e293b !important;
            font-weight: 700 !important;
        }}
        body.light-mode .preset-btn:hover {{
            background: #fff7ed !important;
            border-color: #f7931a !important;
            color: #c2410c !important;
        }}
        body.light-mode .eq-circle {{
            background: #ffffff !important;
            border: 1px solid #94a3b8 !important;
            color: #1e293b !important;
        }}
        body.light-mode .ind-card {{
            background: #f8fafc !important;
            border: 1px solid #cbd5e1 !important;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05) !important;
        }}
        body.light-mode .ind-card:hover,
        body.light-mode .ind-card.selected {{
            background: #ffffff !important;
            border-color: #f7931a !important;
            box-shadow: 0 8px 20px rgba(247, 147, 26, 0.15) !important;
        }}
        body.light-mode .inspector-drawer {{
            background: linear-gradient(165deg, #f8fafc 0%, #f1f5f9 100%) !important;
            border: 1.5px solid #f7931a !important;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08) !important;
        }}
        body.light-mode .insp-text {{
            color: #1e293b !important;
            font-weight: 500 !important;
        }}
        body.light-mode .spark-box {{
            background: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
        }}
    </style>
    </head>
    <body class="{'light-mode' if is_light else 'dark-mode'}">
        <!-- 1. HERO SCORE + DCA CALCULATOR CARD -->
        <div class="hero-card">
            <div class="hero-top-flex">
                <div class="score-giant-wrap">
                    <div class="score-giant-row">
                        <span class="score-giant" id="scoreNum">0</span>
                        <span class="score-denom">/100</span>
                    </div>
                    <div class="zone-pill">{zone.name.upper()}</div>
                </div>
                <div class="price-block">
                    <div class="price-micro-label">
                        {lang_dict['btc_price_label']} <span class="live-pulse"></span>
                    </div>
                    <div class="price-row">
                        <span class="price-val" id="liveBtcPrice">&nbsp;</span>
                        <span class="price-chg" id="liveBtcChg">{pct_sign}{pct_1d:.2f}%</span>
                    </div>
                </div>
            </div>

            <!-- 5-Segment Gauge Bar with Pure Sleek Arrow (No Number) -->
            <div class="gauge-section">
                <div class="gauge-bar-container">
                    <div class="needle-wrap">
                        <svg class="needle-svg" viewBox="0 0 24 26" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 24L2 6L12 11L22 6L12 24Z" fill="{zone.color_hex}" stroke="#0a0e14" stroke-width="1.5" stroke-linejoin="round"/>
                        </svg>
                        <div class="needle-pulse-ring"></div>
                    </div>
                    <div class="gauge-segments">
                        <div class="g-seg" style="background:linear-gradient(90deg, #ef4444, #dc2626);"></div>
                        <div class="g-seg" style="background:linear-gradient(90deg, #ea580c, #d97706);"></div>
                        <div class="g-seg" style="background:linear-gradient(90deg, #d97706, #64748b);"></div>
                        <div class="g-seg" style="background:linear-gradient(90deg, #059669, #10b981);"></div>
                        <div class="g-seg" style="background:linear-gradient(90deg, #10b981, #00f59b);"></div>
                    </div>
                </div>
                <div class="gauge-labels">
                    <span class="g-lbl">{lang_dict['overheated']}</span>
                    <span class="g-lbl">{lang_dict['neutral']}</span>
                    <span class="g-lbl">{lang_dict['strong_buy']}</span>
                </div>
            </div>

            <!-- Recommendation Headline -->
            <div class="dca-rec-title">{lang_dict.get('rec_' + zone.name, zone.dca_headline)}</div>
            <div class="dca-rec-sub">{lang_dict.get('recsub_' + zone.name, zone.dca_subtext)}</div>

            <!-- 3-Column Live DCA Calculator -->
            <div class="dca-calc-grid">
                <div class="dca-col">
                    <div class="dca-col-lbl">{lang_dict['usual_contrib']}</div>
                    <div class="dca-input-wrap">
                        <span class="dollar-prefix">$</span>
                        <input type="number" id="dcaBaseInput" class="dca-input" value="50" min="1" max="100000" step="5">
                    </div>
                    <div class="preset-row">
                        <button class="preset-btn" onclick="setDca(20)">$20</button>
                        <button class="preset-btn" onclick="setDca(50)">$50</button>
                        <button class="preset-btn" onclick="setDca(100)">$100</button>
                        <button class="preset-btn" onclick="setDca(250)">$250</button>
                        <button class="preset-btn" onclick="setDca(500)">$500</button>
                    </div>
                </div>
                <div class="dca-col">
                    <div class="dca-col-lbl">{lang_dict['suggested_dca']}</div>
                    <div class="mult-val">×{mult:.2f}</div>
                    <div class="sats-sub">{lang_dict['regime_lbl']}: {lang_dict.get(zone.name.lower(), zone.name)}</div>
                    <div class="eq-circle">=</div>
                </div>
                <div class="dca-col">
                    <div class="dca-col-lbl">{lang_dict['to_put_in']}</div>
                    <div class="today-out" id="dcaTodayOut">$62.50</div>
                    <div class="sats-sub" id="dcaSatsOut">≈ 85,045 {lang_dict['sats_at_live']}</div>
                </div>
            </div>
        </div>

        <!-- 2. THE 8 MARKET INDICATORS GRID + ANIMATED 30-DAY SPARKLINE INSPECTOR -->
        <div class="ind-header-row">
            <div class="ind-title">{lang_dict['indicators_title']}</div>
            <div class="ind-sub">{lang_dict['indicators_sub']}</div>
        </div>
        <div class="ind-grid" id="indGrid"></div>
        <div class="inspector-drawer" id="inspDrawer"></div>

        <script>
            const MULT = {mult};
            const BTC_PRICE = {btc_price};
            const cardsData = {payload_json};
            let selectedIdx = 0;

            let currentBtcPrice = {btc_price};

            // Score count-up animation
            (function() {{
                const el = document.getElementById('scoreNum');
                const target = {score_val};
                const t0 = performance.now(), dur = 1100;
                function step(t) {{
                    const p = Math.min((t - t0) / dur, 1);
                    const e = 1 - Math.pow(1 - p, 3);
                    el.textContent = Math.round(target * e);
                    if (p < 1) requestAnimationFrame(step);
                }}
                requestAnimationFrame(step);
            }})();

            const dcaInput = document.getElementById('dcaBaseInput');
            const dcaTodayOut = document.getElementById('dcaTodayOut');
            const dcaSatsOut = document.getElementById('dcaSatsOut');
            const livePriceEl = document.getElementById('liveBtcPrice');
            const liveChgEl = document.getElementById('liveBtcChg');
            const refreshTimerEl = document.getElementById('refreshTimer');

            function updateDcaCalc() {{
                const baseVal = parseFloat(dcaInput.value) || 0;
                const finalUsd = baseVal * MULT;
                const sats = Math.round((finalUsd / currentBtcPrice) * 100_000_000);
                dcaTodayOut.textContent = '$' + finalUsd.toLocaleString('en-US', {{
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }});
                dcaSatsOut.textContent = '≈ ' + sats.toLocaleString('en-US') + ' {lang_dict["sats_at_live"]}';
            }}

            function setDca(val) {{
                dcaInput.value = val;
                updateDcaCalc();
            }}

            dcaInput.addEventListener('input', updateDcaCalc);
            updateDcaCalc();

            
            let hasInitialPriceAnimated = false;
                        function animateBtcPriceCountUp(targetPrice) {{
                if (!livePriceEl) return;
                const target = Math.round(targetPrice);
                const dur = 380;
                const t0 = performance.now() - 20;
                function stepPrice(t) {{
                    const p = Math.min(Math.max((t - t0) / dur, 0.04), 1);
                    const e = 1 - Math.pow(1 - p, 3);
                    const val = Math.max(1, Math.round(target * e));
                    livePriceEl.textContent = '$' + val.toLocaleString('en-US');
                    if (p < 1) {{
                        requestAnimationFrame(stepPrice);
                    }} else {{
                        livePriceEl.textContent = '$' + target.toLocaleString('en-US');
                    }}
                }}
                requestAnimationFrame(stepPrice);
            }}

            function applyLivePrice(newPrice, priceChg) {{
                if (!newPrice || isNaN(newPrice)) return;
                currentBtcPrice = newPrice;
                if (!hasInitialPriceAnimated) {{
                    hasInitialPriceAnimated = true;
                    animateBtcPriceCountUp(newPrice);
                }} else if (livePriceEl) {{
                    livePriceEl.textContent = '$' + Math.round(newPrice).toLocaleString('en-US');
                    livePriceEl.classList.add('price-flash');
                    setTimeout(() => {{ if (livePriceEl) livePriceEl.classList.remove('price-flash'); }}, 650);
                }}
                if (liveChgEl && priceChg !== null && !isNaN(priceChg)) {{
                    const sign = priceChg >= 0 ? '+' : '';
                    liveChgEl.textContent = sign + priceChg.toFixed(2) + '%';
                    liveChgEl.style.color = priceChg >= 0 ? '#10b981' : '#ef4444';
                }}
                updateDcaCalc();
            }}
            
            async function fetchLiveBtcPrice() {{
                const fetchBinance = (url) =>
                    fetch(url).then(r => {{ if (!r.ok) throw new Error(); return r.json(); }}).then(d => {{
                        const p = parseFloat(d.lastPrice);
                        const c = parseFloat(d.priceChangePercent);
                        if (!p || isNaN(p)) throw new Error();
                        return {{ price: p, chg: c }};
                    }});
                const fetchCg = () =>
                    fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true')
                        .then(r => {{ if (!r.ok) throw new Error(); return r.json(); }})
                        .then(d => {{
                            const p = parseFloat(d.bitcoin.usd);
                            const c = parseFloat(d.bitcoin.usd_24h_change);
                            if (!p || isNaN(p)) throw new Error();
                            return {{ price: p, chg: c }};
                        }});
                try {{
                    const res = await Promise.any([
                        fetchBinance('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT'),
                        fetchBinance('https://data-api.binance.vision/api/v3/ticker/24hr?symbol=BTCUSDT'),
                        fetchCg()
                    ]);
                    applyLivePrice(res.price, res.chg);
                }} catch (e) {{}}
            }}

            
            fetchLiveBtcPrice();
            setInterval(fetchLiveBtcPrice, 5000);
            function buildSparkSvg(vals, color, width, height, fillArea) {{
                const minV = Math.min(...vals);
                const maxV = Math.max(...vals);
                const range = (maxV - minV) || 1;
                const pad = 4;
                const pts = vals.map((v, i) => {{
                    const x = pad + (i / (vals.length - 1)) * (width - pad * 2);
                    const y = (height - pad) - ((v - minV) / range) * (height - pad * 2);
                    return `${{x.toFixed(1)}},${{y.toFixed(1)}}`;
                }});
                const polylinePoints = pts.join(' ');
                if (!fillArea) {{
                    return `<svg viewBox="0 0 ${{width}} ${{height}}" class="mini-spark">
                        <polyline fill="none" stroke="${{color}}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" points="${{polylinePoints}}" />
                    </svg>`;
                }}
                const areaPoints = `${{pad}},${{height - pad}} ${{polylinePoints}} ${{width - pad}},${{height - pad}}`;
                const gradId = 'grad_' + Math.random().toString(36).substring(2, 7);
                return `<svg viewBox="0 0 ${{width}} ${{height}}" style="width:100%;height:145px;display:block;">
                    <defs>
                        <linearGradient id="${{gradId}}" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stop-color="${{color}}" stop-opacity="0.38"/>
                            <stop offset="100%" stop-color="${{color}}" stop-opacity="0.0"/>
                        </linearGradient>
                    </defs>
                    <polygon fill="url(#${{gradId}})" points="${{areaPoints}}" />
                    <polyline fill="none" stroke="${{color}}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" points="${{polylinePoints}}" />
                </svg>`;
            }}

            const indGrid = document.getElementById('indGrid');
            const inspDrawer = document.getElementById('inspDrawer');

            function renderIndicators() {{
                indGrid.innerHTML = '';
                cardsData.forEach((c, idx) => {{
                    const div = document.createElement('div');
                    div.className = 'ind-card' + (idx === selectedIdx ? ' selected' : '');
                    div.style.borderLeftColor = c.color;
                    div.style.animationDelay = (idx * 0.05) + 's';
                    div.innerHTML = `
                        <div class="ind-top">
                            <span class="ind-name">${{c.title}}</span>
                            <span class="ind-dot" style="background:${{c.color}};box-shadow:0 0 8px ${{c.color}};"></span>
                        </div>
                        <div class="ind-val-row">
                            <span class="ind-val" style="color:${{c.color}};">${{c.val}}</span>
                            ${{buildSparkSvg(c.vals_30, c.color, 68, 26, false)}}
                        </div>
                    `;
                    div.addEventListener('mouseenter', () => selectCard(idx));
                    div.addEventListener('click', () => selectCard(idx));
                    indGrid.appendChild(div);
                }});
                renderDrawer();
            }}

            function selectCard(idx) {{
                if (idx === selectedIdx) return;
                selectedIdx = idx;
                const allCards = indGrid.querySelectorAll('.ind-card');
                allCards.forEach((el, i) => el.classList.toggle('selected', i === selectedIdx));
                renderDrawer();
            }}

            function renderDrawer() {{
                const c = cardsData[selectedIdx];
                inspDrawer.style.borderColor = c.color + '88';
                inspDrawer.innerHTML = `
                    <div class="insp-content-anim">
                        <div class="insp-badge-row">
                            <span class="insp-title">${{c.title}}</span>
                            <span class="insp-pill" style="color:${{c.color}};border:1px solid ${{c.color}};background:${{c.color}}18;">
                                ${{c.val}} • ${{c.status}}
                            </span>
                            <span class="insp-pill" style="color:#f7931a;border:1px solid rgba(247,147,26,0.4);background:rgba(247,147,26,0.1);">
                                {lang_dict['weight_lbl']}: ${{c.weight}}
                            </span>
                        </div>
                        <div class="insp-kicker">{lang_dict['calc_how']}</div>
                        <div class="insp-text">${{c.how}}</div>
                        <div class="insp-kicker">{lang_dict['calc_why']}</div>
                        <div class="insp-text">${{c.why}}</div>
                    </div>
                    <div class="spark-box insp-content-anim">
                        <div class="spark-header">
                            <span>{lang_dict['trajectory_lbl']} (${{c.dates_30[0]}} – ${{c.dates_30[c.dates_30.length - 1]}})</span>
                            <span style="color:${{c.color}};font-weight:700;">Min: ${{c.min_30}} | Max: ${{c.max_30}}</span>
                        </div>
                        ${{buildSparkSvg(c.vals_30, c.color, 420, 145, true)}}
                    </div>
                `;
                syncIframeHeight();
            }}

            renderIndicators();

            function syncIframeHeight() {{
                try {{
                    const h = Math.ceil(document.body.scrollHeight || document.documentElement.scrollHeight);
                    if (window.frameElement) {{
                        window.frameElement.style.height = (h + 8) + 'px';
                    }} else if (window.parent) {{
                        const iframes = window.parent.document.querySelectorAll('iframe');
                        for (let ifr of iframes) {{
                            if (ifr.contentWindow === window) {{
                                ifr.style.height = (h + 8) + 'px';
                                break;
                            }}
                        }}
                    }}
                }} catch (e) {{}}
            }}
            setTimeout(syncIframeHeight, 50);
            setTimeout(syncIframeHeight, 300);
            window.addEventListener('resize', syncIframeHeight);
            if (typeof ResizeObserver !== 'undefined') {{
                new ResizeObserver(syncIframeHeight).observe(document.body);
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=1210, scrolling=False)


# ---------------------------------------------------------------------------
# DUAL-AXIS GOLD SCORE VS BTC PRICE INTERACTIVE CHART
# ---------------------------------------------------------------------------
def build_dual_axis_chart(
    df: pd.DataFrame, use_log_scale: bool = True, show_ema: bool = True, is_light: bool = False
) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Left Y-Axis: Gold Score Line (0-100) matching thebitcoinscore.com
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["accumulation_score"],
            name="The Bitcoin Score (0–100)",
            mode="lines",
            line=dict(color="#f59e0b", width=2.2),
            fill="tozeroy",
            fillcolor="rgba(245, 158, 11, 0.08)",
            hovertemplate="<b>Score:</b> %{y:.1f} / 100<extra></extra>",
        ),
        secondary_y=False,
    )

    # Right Y-Axis: BTC Price Line
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["close"],
            name="BTC Price (USD)",
            mode="lines",
            line=dict(color="#38bdf8", width=2.2),
            hovertemplate="<b>BTC Price:</b> $%{y:,.0f}<extra></extra>",
        ),
        secondary_y=True,
    )

    if show_ema:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["ema200"],
                name="200-Day EMA",
                mode="lines",
                line=dict(color="#64748b", width=1.4, dash="dot"),
                hovertemplate="<b>EMA200:</b> $%{y:,.0f}<extra></extra>",
            ),
            secondary_y=True,
        )

    # Highlight Strong Buy (>=75) and Overheated (<=25) signals on BTC Price
    sb_df = df[df["accumulation_score"] >= 75.0]
    oh_df = df[df["accumulation_score"] <= 25.0]

    fig.add_trace(
        go.Scatter(
            x=sb_df.index,
            y=sb_df["close"],
            name="Strong Buy Zone (≥75)",
            mode="markers",
            marker=dict(color="#10b981", size=5.5, symbol="triangle-up"),
            hovertemplate="<b>Strong Buy</b> ($%{y:,.0f})<extra></extra>",
        ),
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(
            x=oh_df.index,
            y=oh_df["close"],
            name="Overheated Zone (≤25)",
            mode="markers",
            marker=dict(color="#ef4444", size=5.5, symbol="triangle-down"),
            hovertemplate="<b>Overheated</b> ($%{y:,.0f})<extra></extra>",
        ),
        secondary_y=True,
    )

    text_col = "#0f172a" if is_light else "#f1f5f9"
    grid_col = "rgba(15,23,42,0.09)" if is_light else "rgba(255,255,255,0.05)"

    fig.update_yaxes(
        title_text="The Bitcoin Score (0–100)",
        title_font=dict(color=text_col, size=13),
        tickfont=dict(color=text_col, size=12),
        title_standoff=18,
        automargin=True,
        range=[0, 100],
        tickvals=[0, 25, 40, 60, 75, 100],
        gridcolor=grid_col,
        secondary_y=False,
    )
    fig.update_yaxes(
        title_text="BTC Price (USD)",
        title_font=dict(color=text_col, size=13),
        tickfont=dict(color=text_col, size=12),
        title_standoff=18,
        automargin=True,
        tickprefix="$",
        type="log" if use_log_scale else "linear",
        gridcolor="rgba(0,0,0,0)",
        secondary_y=True,
    )
    fig.update_xaxes(
        tickfont=dict(color=text_col, size=12),
        automargin=True,
        gridcolor=grid_col,
    )

    fig.update_layout(
        paper_bgcolor="#f8fafc" if is_light else "#11161f",
        plot_bgcolor="#f1f5f9" if is_light else "#0a0e14",
        font=dict(color=text_col, family="Plus Jakarta Sans, Inter"),
        height=540,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=text_col, size=12),
            bgcolor="rgba(248,250,252,0.92)" if is_light else "rgba(17,22,31,0.85)",
        ),
        margin=dict(l=72, r=78, t=55, b=40),
    )
    return fig


# ---------------------------------------------------------------------------
# MAIN APPLICATION
# ---------------------------------------------------------------------------
def main() -> None:
    # Top Utility Bar with Language Selector (EN | TR) & Theme Toggle (🌙 | ☀️)
    col_brand, col_lang = st.columns([2.8, 1.4])
    with col_lang:
        c_l1, c_l2 = st.columns(2)
        with c_l1:
            lang = st.segmented_control(
                "Language",
                options=["EN", "TR"],
                default="EN",
                label_visibility="collapsed",
            )
            if not lang:
                lang = "EN"
        with c_l2:
            theme_mode = st.segmented_control(
                "Theme",
                options=["🌙", "☀️"],
                default="🌙",
                label_visibility="collapsed",
            )
            if not theme_mode:
                theme_mode = "🌙"

    is_light = theme_mode == "☀️"
    if is_light:
        st.markdown(
            """
            <style>
                .stApp {
                    background: linear-gradient(180deg, #e2e8f0 0%, #edf2f7 40%, #e2e8f0 100%) !important;
                    color: #0f172a !important;
                }
                .tbs-main-title, .tbs-logo-text, .sec-title, .news-headline, .why-box h3,
                [data-testid="stExpander"] summary, [data-testid="stExpander"] summary p,
                .zone-bar-top, .tbs-card b, [data-testid="stWidgetLabel"] p,
                [data-testid="stCheckbox"] label span, [data-testid="stCheckbox"] p {
                    color: #0f172a !important;
                }
                .tbs-tagline {
                    color: #1e293b !important;
                    font-weight: 700 !important;
                }
                .tbs-subdesc, .tbs-sub, .sec-sub, .news-excerpt, .news-footer, .why-item,
                .cycle-desc, .zone-note, [data-testid="stExpander"] p {
                    color: #334155 !important;
                    font-weight: 500 !important;
                }
                .tbs-pill-bar {
                    background: #ecfdf5 !important;
                    border: 1px solid #6ee7b7 !important;
                    color: #065f46 !important;
                }
                .tbs-card, .why-box, .news-card, [data-testid="stExpander"], [data-testid="stPlotlyChart"] {
                    background: #f8fafc !important;
                    border: 1px solid #cbd5e1 !important;
                    box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06) !important;
                }
                .why-item, .cycle-item {
                    border-bottom-color: #cbd5e1 !important;
                }
                .news-thumb-wrap {
                    background-color: transparent !important;
                    border: none !important;
                }
                .news-footer {
                    border-top-color: #cbd5e1 !important;
                }
                .zone-bar-bg { background: #cbd5e1 !important; }
                [data-testid="stSegmentedControl"] button, [data-testid="stButtonGroup"] button {
                    background: #ffffff !important;
                    border-color: #94a3b8 !important;
                    color: #1e293b !important;
                }
                [data-testid="stSegmentedControl"] button[aria-checked="true"],
                [data-testid="stButtonGroup"] button[aria-checked="true"] {
                    background: rgba(247, 147, 26, 0.16) !important;
                    border-color: #f7931a !important;
                    color: #0f172a !important;
                }
                .disclaimer-banner {
                    background: #fff7ed !important;
                    border-color: #fdba74 !important;
                    color: #9a3412 !important;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )

    L = I18N[lang]

    scored_df = load_scored_data(start_date="2018-02-01", fred_api_key="")
    latest = scored_df.iloc[-1]

    with col_brand:
        st.markdown(
            f"""
            <div class="tbs-header">
                <div class="tbs-top-row">
                    <div class="tbs-logo-group">
                        <div class="tbs-logo-wrap">
                            <div class="tbs-orange-circle">₿</div>
                            <div class="tbs-tri-bars">
                                <div class="tbs-tri-bar" style="background:#ef4444;"></div>
                                <div class="tbs-tri-bar" style="background:#64748b;"></div>
                                <div class="tbs-tri-bar" style="background:#10b981;"></div>
                            </div>
                        </div>
                        <div class="tbs-main-title">The Bitcoin Score</div>
                    </div>
                    <div class="tbs-pill-bar">
                        <span class="tbs-live-badge"><span class="tbs-live-dot"></span> LIVE 8-FACTOR ENGINE</span>
                    </div>
                </div>
                <div class="tbs-orange-divider"></div>
                <div class="tbs-tagline">{L['tagline']}</div>
                <div class="tbs-subdesc">{L['subdesc']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -----------------------------------------------------------------------
    # 1. HERO CARD + LIVE DCA CALCULATOR + 8 INTERACTIVE SPARKLINE CARDS
    # -----------------------------------------------------------------------
    render_hero_and_signals_component(scored_df, L, lang=lang, is_light=is_light)

    # -----------------------------------------------------------------------
    # 2. "WHY TODAY'S SCORE?" SYNTHESIS SECTION (MATCHING THEBITCOINSCORE.COM)
    # -----------------------------------------------------------------------
    dxy_90d = float(latest.get("dxy_90d_roc", 0.0))
    m2_yoy = float(latest["m2_yoy"])
    gt_pct = float(latest.get("gt_percentile", 12.0))
    mvrv_val = float(latest["mvrv"])

    dxy_color = "#ef4444" if dxy_90d > 0 else "#10b981"
    dxy_word = L["why_dxy_risen"] if dxy_90d >= 0 else L["why_dxy_fallen"]
    dxy_effect = L["why_dxy_headwind"] if dxy_90d > 0 else L["why_dxy_tailwind"]

    st.markdown(
        f"""
        <div class="why-box">
            <div class="why-title">{L['why_title']}</div>
            <div class="why-item">
                <span class="why-dot" style="background:#10b981;box-shadow:0 0 8px #10b981;"></span>
                <span><b>{L['why_mvrv_lbl']}:</b> <b>{mvrv_val:.2f}x</b> {L['why_mvrv_txt']}</span>
            </div>
            <div class="why-item">
                <span class="why-dot" style="background:#10b981;box-shadow:0 0 8px #10b981;"></span>
                <span><b>{L['why_m2_lbl']}:</b> <b>{m2_yoy:+.2f}%</b> {L['why_m2_txt']}</span>
            </div>
            <div class="why-item">
                <span class="why-dot" style="background:{dxy_color};box-shadow:0 0 8px {dxy_color};"></span>
                <span><b>{L['why_dxy_lbl']}:</b> DXY {dxy_word} (90g: <b>{abs(dxy_90d):.2f}%</b>, Seviye: <b>{float(latest['dxy']):.2f}</b>) — {dxy_effect}.</span>
            </div>
            <div class="why-item">
                <span class="why-dot" style="background:#10b981;box-shadow:0 0 8px #10b981;"></span>
                <span><b>{L['why_sent_lbl']}:</b> Korku & Açgözlülük: <b>{int(latest['fng'])} ({_fng_label(float(latest['fng']), lang)})</b>, {L['why_sent_txt']} <b>%{gt_pct:.0f}</b> {L['why_sent_sub']}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------------------------
    # 3. DUAL-AXIS INTERACTIVE CHART (SCORE IN GOLD vs BTC PRICE)
    # -----------------------------------------------------------------------
    st.markdown(
        f"""
        <div class="sec-title-row">
            <div class="sec-title">{L['chart_title']}</div>
            <div class="sec-sub">{L['chart_sub']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_tf, c_log, c_ema = st.columns([2.2, 1.0, 1.0])
    with c_tf:
        tf_choice = st.segmented_control(
            "Timeframe",
            options=["3M", "1Y", "3Y", "5Y", "ALL (2018+)"],
            default="ALL (2018+)",
            label_visibility="collapsed",
        )
    with c_log:
        use_log = st.toggle(L["log_scale_lbl"], value=True)
    with c_ema:
        show_ema = st.toggle(L["ema_toggle_lbl"], value=True)

    plot_df = scored_df.copy()
    if tf_choice == "3M":
        plot_df = plot_df.loc[plot_df.index.max() - pd.DateOffset(months=3) :]
    elif tf_choice == "1Y":
        plot_df = plot_df.loc[plot_df.index.max() - pd.DateOffset(years=1) :]
    elif tf_choice == "3Y":
        plot_df = plot_df.loc[plot_df.index.max() - pd.DateOffset(years=3) :]
    elif tf_choice == "5Y":
        plot_df = plot_df.loc[plot_df.index.max() - pd.DateOffset(years=5) :]

    st.plotly_chart(
        build_dual_axis_chart(plot_df, use_log_scale=use_log, show_ema=show_ema, is_light=is_light),
        width="stretch",
        theme=None,
    )

    # -----------------------------------------------------------------------
    # 5. TIME SPENT IN EACH ZONE & REAL-WORLD EXAMPLES
    # -----------------------------------------------------------------------
    st.markdown("<div style='height:22px;'></div>", unsafe_allow_html=True)
    col_z1, col_z2 = st.columns(2, gap="large")

    strong_buy_lbl = "Güçlü Alım" if lang == "TR" else "Strong Buy"
    buy_more_lbl = "Daha Fazla Al" if lang == "TR" else "Buy More"
    neutral_lbl = "Nötr" if lang == "TR" else "Neutral"
    caution_lbl = "Dikkat" if lang == "TR" else "Caution"
    overheated_lbl = "Aşırı Isınmış" if lang == "TR" else "Overheated"

    with col_z1:
        st.markdown(
            f"""
            <div class="tbs-card">
                <div style="color:#f7931a;font-size:0.78rem;font-weight:800;letter-spacing:0.08em;margin-bottom:16px;">
                    {L['zone_title']}
                </div>
                <div class="zone-bar-row">
                    <div class="zone-bar-top"><span>{strong_buy_lbl} (75–100)</span><span style="color:#10b981;">~5%</span></div>
                    <div class="zone-pill-fill" style="width:12%;background:#059669;"></div>
                </div>
                <div class="zone-bar-row">
                    <div class="zone-bar-top"><span>{buy_more_lbl} (60–75)</span><span style="color:#10b981;">~20%</span></div>
                    <div class="zone-pill-fill" style="width:40%;background:#10b981;"></div>
                </div>
                <div class="zone-bar-row">
                    <div class="zone-bar-top"><span>{neutral_lbl} (40–60)</span><span style="color:#f59e0b;">~50%</span></div>
                    <div class="zone-pill-fill" style="width:100%;background:#f59e0b;"></div>
                </div>
                <div class="zone-bar-row">
                    <div class="zone-bar-top"><span>{caution_lbl} (25–40)</span><span style="color:#f59e0b;">~20%</span></div>
                    <div class="zone-pill-fill" style="width:40%;background:#d97706;"></div>
                </div>
                <div class="zone-bar-row">
                    <div class="zone-bar-top"><span>{overheated_lbl} (0–25)</span><span style="color:#ef4444;">~5%</span></div>
                    <div class="zone-pill-fill" style="width:12%;background:#ef4444;"></div>
                </div>
                <div class="zone-note">
                    {L['zone_sub']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_z2:
        st.markdown(
            f"""
            <div class="tbs-card">
                <div style="color:#f7931a;font-size:0.78rem;font-weight:800;letter-spacing:0.08em;margin-bottom:14px;">
                    {L['cycle_title']}
                </div>
                <div class="cycle-item">
                    <span style="color:#10b981;font-weight:800;">{strong_buy_lbl.upper()} • Ara 2022 (~$16,600)</span> — <b>{L['score_label']}: 84.8</b><br>
                    <span class="cycle-desc">{L['cycle_ftx_sub']}</span>
                </div>
                <div class="cycle-item">
                    <span style="color:#10b981;font-weight:800;">{strong_buy_lbl.upper()} • Şub–Nis 2018 (~$7,000)</span> — <b>{L['score_label']}: 85.0</b><br>
                    <span class="cycle-desc">{L['cycle_bear_sub']}</span>
                </div>
                <div class="cycle-item">
                    <span style="color:#ef4444;font-weight:800;">{overheated_lbl.upper()} • Eki 2021 (~$61,000)</span> — <b>{L['score_label']}: ~25.0</b><br>
                    <span class="cycle-desc">{L['cycle_ath_sub']}</span>
                </div>
                <div>
                    <span style="color:#ef4444;font-weight:800;">{overheated_lbl.upper()} • Kas 2024 (~$98,000)</span> — <b>{L['score_label']}: 23.3</b><br>
                    <span class="cycle-desc">{L['cycle_rally_sub']}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -----------------------------------------------------------------------
    # 6. BITCOIN NEWS (5 LIVE ARTICLES FROM BITCOINMAGAZINE.COM)
    # -----------------------------------------------------------------------
    st.markdown(
        f"""
        <div class="sec-title-row">
            <div class="sec-title">{L['news_title']} <span>{L['news_span']}</span></div>
            <div class="sec-sub">{L['news_sub']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    news_items = load_bitcoin_news(limit=5, lang=lang)
    if news_items:
        cards_html = ['<div class="news-grid">']
        for idx, art in enumerate(news_items):
            is_featured = idx == 0
            card_cls = "news-card news-card-featured" if is_featured else "news-card"
            thumb_html = ""
            if art.get("image"):
                thumb_html = (
                    f'<div class="news-thumb-wrap" style="background-image:url(\'{art["image"]}\');">'
                    f'<img src="{art["image"]}" class="news-thumb" alt="Bitcoin News" loading="lazy" '
                    f'style="width:100% !important;height:100% !important;max-width:none !important;object-fit:cover !important;display:block !important;margin:0 !important;">'
                    f"</div>"
                )
            cards_html.append(
                f'<a href="{art["link"]}" target="_blank" rel="noopener noreferrer" class="{card_cls}">'
                f"{thumb_html}"
                f'<div style="display:flex;flex-direction:column;flex:1;justify-content:space-between;">'
                f"<div>"
                f'<div class="news-meta-row">'
                f'<span class="news-badge">{art["category"]}</span>'
                f'<span class="news-date">{art["published"]}</span>'
                f"</div>"
                f'<div class="news-headline">{art["title"]}</div>'
                f'<div class="news-excerpt" style="margin-bottom:10px;">{art["summary"]}</div>'
                f"</div>"
                f'<div class="news-footer" style="margin-top:auto;padding-top:10px;">'
                f'<span>✍️ {art["author"]}</span>'
                f'<span class="news-read-more">{L["news_read"]}</span>'
                f"</div>"
                f"</div>"
                f"</a>"
            )
        cards_html.append("</div>")
        st.markdown("".join(cards_html), unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # 7. FREQUENTLY ASKED QUESTIONS (SMOOTH ACCORDION)
    # -----------------------------------------------------------------------
    st.markdown(
        f'<div class="sec-title-row"><div class="sec-title">{L["faq_title"]} <span>{L["faq_span"]}</span></div></div>',
        unsafe_allow_html=True,
    )
    if lang == "TR":
        faqs = [
            (
                "The Bitcoin Score (Birikim Skoru) nasıl çalışır?",
                "Zincir üstü değerleme (MVRV), teknik trend ve momentum (200 günlük EMA, Wilder RSI14), küresel makro likidite (ABD M2 yıllık değişimi, DXY), piyasa hissiyatı (Korku & Açgözlülük), halkın ilgisi (Google Trends) ve piyasa yapısı (BTC Dominansı) olmak üzere 8 bağımsız piyasa göstergesini her gün 0 ile 100 arasında tek bir bileşik skorda toplar.",
            ),
            (
                "8 gösterge nasıl ağırlıklandırılır ve kalibre edilir?",
                "MVRV (%22) ve EMA200 mesafesi (%18) en yüksek yapısal ağırlığa sahiptir. Ardından RSI14 (%14), Korku & Açgözlülük (%14), DXY (%10), M2 Likidite (%10), Google Trends (%8) ve BTC Dominansı (%4 - en tartışmalı metrik olduğu için hafif) gelir. Tarihsel dağılım ~%5 Güçlü Alım, ~%20 Daha Fazla Al, ~%50 Nötr, ~%20 Dikkat ve ~%5 Aşırı Isınmış olarak dengelenmiştir.",
            ),
            (
                "Skor ayarlı Akıllı DCA, standart sabit DCA'dan gerçekten daha mı çok kazandırır?",
                "Evet — piyasa aşırı korkulu ve ucuzken alım tutarını çarpanla (×1.25 ile ×1.50) artırarak, aşırı ısındığında ise alımları kısıp sakin kalarak ortalama BTC maliyetinizi sistematik biçimde düşürür. Tehlikeli 'tamamen gir / tamamen çık' zamanlama stresine girmeden üstün getiri (alfa) üretir.",
            ),
        ]
    else:
        faqs = [
            (
                "How does The Bitcoin Score work?",
                "It aggregates 8 independent market signals spanning on-chain valuation (MVRV), technical trend & momentum (200d EMA, Wilder's RSI14), macro liquidity (US M2 YoY, DXY), sentiment (Fear & Greed), retail attention (Google Trends), and market structure (BTC Dominance) into a single 0–100 daily score.",
            ),
            (
                "How are the 8 signals weighted and calibrated?",
                "MVRV (22%) and EMA200 distance (18%) carry the highest structural weight, followed by RSI14 (14%), Fear & Greed (14%), DXY (10%), M2 Liquidity (10%), Google Trends (8%), and BTC Dominance (lightly weighted at 4%). The composite score is quantile-calibrated so historical occupancy matches ~5% Strong Buy, ~20% Buy More, ~50% Neutral, ~20% Caution, and ~5% Overheated.",
            ),
            (
                "Does score-adjusted DCA actually outperform regular DCA?",
                "Yes — by scaling up daily contributions (×1.25 to ×1.50) when Bitcoin is undervalued and fearful, and scaling back when the market is overheated, Smart DCA systematically lowers your average BTC purchase price without attempting risky all-in/all-out market timing.",
            ),
        ]
    for q, a in faqs:
        with st.expander(q, expanded=False):
            st.write(a)

    disclaimer_text = (
        "⚠️ <b>Yasal Uyarı / Eğitim Amaçlıdır:</b> Bu platformda yer alan tüm veriler, skorlar, grafikler ve analizler yalnızca <b>eğitim ve bilgilendirme amaçlıdır</b>. Kesinlikle <b>yatırım tavsiyesi değildir</b>. Finansal kararlarınızı kendi araştırmanız ve risk toleransınız doğrultusunda alınız."
        if lang == "TR"
        else "⚠️ <b>Disclaimer / Educational Purpose Only:</b> All data, scores, charts, and analytics presented on this platform are strictly for <b>educational and informational purposes only</b> and do <b>not constitute financial or investment advice</b>. Always do your own research before making any financial decisions."
    )
    st.markdown(
        f"""
        <div class="disclaimer-banner" style="margin-top:28px;padding:16px 20px;border-radius:12px;background:rgba(247,147,26,0.08);border:1px solid rgba(247,147,26,0.28);color:#cbd5e1;font-size:0.84rem;line-height:1.55;text-align:center;">
            {disclaimer_text}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Scroll-reveal animations (runs in parent document via same-origin iframe)
    components.html(
        """
        <script>
        (function () {
            const doc = window.parent.document;
            if (!doc.getElementById('tbs-reveal-style')) {
                const s = doc.createElement('style');
                s.id = 'tbs-reveal-style';
                s.textContent = `
                    .tbs-reveal { opacity: 0; transform: translateY(28px) scale(.985);
                        transition: opacity .7s cubic-bezier(.22,1,.36,1), transform .7s cubic-bezier(.22,1,.36,1); }
                    .tbs-reveal.tbs-in { opacity: 1; transform: none; }
                    .news-card.tbs-reveal.tbs-in .news-thumb { animation: tbsZoom 1.2s cubic-bezier(.22,1,.36,1) both; }
                    @keyframes tbsZoom { from { transform: scale(1.12); } to { transform: scale(1); } }
                    .zone-pill-fill { transform-origin: left; }
                    .tbs-card.tbs-in .zone-pill-fill { animation: tbsBar 1s cubic-bezier(.22,1,.36,1) both; }
                    @keyframes tbsBar { from { transform: scaleX(0); } to { transform: scaleX(1); } }
                    @media (prefers-reduced-motion: reduce) { .tbs-reveal { opacity:1 !important; transform:none !important; transition:none !important; } }
                `;
                doc.head.appendChild(s);
            }
            const sel = '.sec-title-row, .why-box, .tbs-card, .news-card, [data-testid="stExpander"], .disclaimer-banner';
            const io = new window.parent.IntersectionObserver((entries) => {
                entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('tbs-in'); io.unobserve(e.target); } });
            }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
            function scan() {
                doc.querySelectorAll(sel).forEach((el) => {
                    if (el.dataset.tbsObs) return;
                    el.dataset.tbsObs = '1';
                    el.classList.add('tbs-reveal');
                    if (el.classList.contains('news-card')) {
                        const i = Array.from(el.parentNode.children).indexOf(el);
                        el.style.transitionDelay = (i * 0.09) + 's';
                    }
                    io.observe(el);
                });
            }
            scan();
            new window.parent.MutationObserver(scan).observe(doc.body, { childList: true, subtree: true });
        })();
        </script>
        """,
        height=0,
    )


if __name__ == "__main__":
    main()
