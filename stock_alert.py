#!/usr/bin/env python3
"""
📈 KIS 주식 급등 알림 봇
Railway 환경변수로 키 설정 - 파일 수정 불필요
"""

import os
import requests
import time
import schedule
from datetime import datetime, time as dtime

# ============================================================
# ⚙️ 환경변수에서 자동으로 키 읽어옴 (수정 불필요!)
# ============================================================
KIS_APP_KEY        = os.environ.get("KIS_APP_KEY", "")
KIS_APP_SECRET     = os.environ.get("KIS_APP_SECRET", "")
KIS_ACCOUNT_NO     = os.environ.get("KIS_ACCOUNT_NO", "")
KIS_BASE_URL       = "https://openapi.koreainvestment.com:9443"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

# ============================================================
# 📊 스캔 조건
# ============================================================
VOLUME_SURGE_RATIO    = 5.0
PRICE_SURGE_MIN       = 5.0
UPPER_LIMIT_THRESHOLD = 25.0
SCAN_INTERVAL         = 60
ALERT_COOLDOWN        = 1800
MARKET_OPEN           = "09:00"
MARKET_CLOSE          = "15:30"
ENTRY_TIME_START      = "10:00"
ENTRY_TIME_END        = "11:30"
ENTRY_PULLBACK_RATIO  = 0.4
STOP_LOSS_PCT         = 0.07
TARGET_PCT            = 0.15

# ============================================================
# 🔐 KIS API
# ============================================================
_access_token  = None
_token_expires = 0
_session       = requests.Session()

def get_token() -> str:
    global _access_token, _token_expires
    if _access_token and time.time() < _token_expires:
        return _access_token
    url  = f"{KIS_BASE_URL}/oauth2/tokenP"
    body = {"grant_type": "client_credentials",
            "appkey": KIS_APP_KEY, "appsecret": KIS_APP_SECRET}
    resp = _session.post(url, json=body, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    _access_token  = data["access_token"]
    _token_expires = time.time() + int(data.get("expires_in", 86400)) - 60
    print("✅ KIS 토큰 발급 완료")
    return _access_token

def _headers(tr_id: str) -> dict:
    return {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {get_token()}",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET,
        "tr_id": tr_id,
        "custtype": "P",
    }

def get_stock_price(code: str) -> dict:
    url    = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
    resp   = _session.get(url, headers=_headers("FHKST01010100"), params=params, timeout=10)
    if resp.status_code != 200:
        return {}
    o     = resp.json().get("output", {})
    price = int(o.get("stck_prpr", 0))
    if not price:
        return {}
    return {
        "code": code,
        "name": o.get("hts_kor_isnm", ""),
        "price": price,
        "change_rate": float(o.get("prdy_ctrt", 0)),
        "volume_ratio": float(o.get("vol_tnrt", 0)),
        "high": int(o.get("stck_hgpr", 0)),
    }

def get_upper_limit_stocks() -> list:
    url    = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/chgrate-pcls-100"
    params = {
        "FID_COND_MRKT_DIV_CODE": "J", "FID_COND_SCR_DIV_CODE": "20170",
        "FID_INPUT_ISCD": "0000", "FID_RANK_SORT_CLS_CODE": "0",
        "FID_INPUT_CNT_1": "30", "FID_PRC_CLS_CODE": "0",
        "FID_INPUT_PRICE_1": "1000", "FID_INPUT_PRICE_2": "",
        "FID_VOL_CNT": "100000", "FID_TRGT_CLS_CODE": "0",
        "FID_TRGT_EXLS_CLS_CODE": "0", "FID_DIV_CLS_CODE": "0",
        "FID_RSFL_RATE1": "5", "FID_RSFL_RATE2": "",
    }
    resp  = _session.get(url, headers=_headers("FHPST01700000"), params=params, timeout=10)
    if resp.status_code != 200:
        return []
    items = resp.json().get("output", [])
    return [{"code": i.get("mksc_shrn_iscd",""), "name": i.get("hts_kor_isnm",""),
             "price": int(i.get("stck_prpr",0)), "change_rate": float(i.get("prdy_ctrt",0)),
             "volume_ratio": float(i.get("vol_inrt",0) or 0)} for i in items if i.get("mksc_shrn_iscd")]

def get_volume_surge_stocks() -> list:
    url    = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/volume-rank"
    params = {
        "FID_COND_MRKT_DIV_CODE": "J", "FID_COND_SCR_DIV_CODE": "20171",
        "FID_INPUT_ISCD": "0000", "FID_DIV_CLS_CODE": "0",
        "FID_BLNG_CLS_CODE": "0", "FID_TRGT_CLS_CODE": "111111111",
        "FID_TRGT_EXLS_CLS_CODE": "000000", "FID_INPUT_PRICE_1": "1000",
        "FID_INPUT_PRICE_2": "", "FID_VOL_CNT": "30", "FID_INPUT_DATE_1": "",
    }
    resp  = _session.get(url, headers=_headers("FHPST01710000"), params=params, timeout=10)
    if resp.status_code != 200:
        return []
    items = resp.json().get("output", [])
    return [{"code": i.get("mksc_shrn_iscd",""), "name": i.get("hts_kor_isnm",""),
             "price": int(i.get("stck_prpr",0)), "change_rate": float(i.get("prdy_ctrt",0)),
             "volume_ratio": float(i.get("vol_inrt",0) or 0)} for i in items if i.get("mksc_shrn_iscd")]

def get_investor_trend(code: str) -> dict:
    url    = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-investor"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
    resp   = _session.get(url, headers=_headers("FHKST01010900"), params=params, timeout=10)
    if resp.status_code != 200:
        return {}
    output = resp.json().get("output", [])
    if not output:
        return {}
    return {"foreign_net": int(output[0].get("frgn_ntby_qty", 0)),
            "institution_net": int(output[0].get("orgn_ntby_qty", 0))}

# ============================================================
# 📊 스캐너
# ============================================================
_alert_history   = {}
_detected_stocks = {}

def is_market_open() -> bool:
    now = datetime.now().time()
    o   = dtime(*map(int, MARKET_OPEN.split(":")))
    c   = dtime(*map(int, MARKET_CLOSE.split(":")))
    return o <= now <= c

def is_entry_time() -> bool:
    now = datetime.now().time()
    s   = dtime(*map(int, ENTRY_TIME_START.split(":")))
    e   = dtime(*map(int, ENTRY_TIME_END.split(":")))
    return s <= now <= e

def analyze(stock: dict) -> dict:
    code        = stock.get("code", "")
    change_rate = stock.get("change_rate", 0)
    vol_ratio   = stock.get("volume_ratio", 0)
    price       = stock.get("price", 0)
    if not code or price < 500:
        return {}

    score, reasons, signal_type = 0, [], None

    if change_rate >= 29.0:
        score += 40; reasons.append("🚨 상한가 도달!"); signal_type = "UPPER_LIMIT"
    elif change_rate >= UPPER_LIMIT_THRESHOLD:
        score += 25; reasons.append(f"🔥 상한가 근접 (+{change_rate:.1f}%)"); signal_type = "NEAR_UPPER"
    elif change_rate >= PRICE_SURGE_MIN:
        score += 15; reasons.append(f"📈 급등 +{change_rate:.1f}%"); signal_type = "SURGE"
    else:
        return {}

    if vol_ratio >= VOLUME_SURGE_RATIO * 2:
        score += 30; reasons.append(f"💥 거래량 {vol_ratio:.0f}배 폭발!")
    elif vol_ratio >= VOLUME_SURGE_RATIO:
        score += 20; reasons.append(f"📊 거래량 {vol_ratio:.0f}배 급증")

    if score >= 25:
        try:
            inv   = get_investor_trend(code)
            f_net = inv.get("foreign_net", 0)
            i_net = inv.get("institution_net", 0)
            if f_net > 0 and i_net > 0:
                score += 25; signal_type = "STRONG_BUY"; reasons.append("✅ 외국인+기관 동시 순매수")
            elif f_net > 0:
                score += 10; reasons.append("🟡 외국인 순매수")
            elif i_net > 0:
                score += 10; reasons.append("🟡 기관 순매수")
        except:
            pass

    if score < 60:
        return {}

    open_est = price / (1 + change_rate / 100)
    entry    = int((price - (price - open_est) * ENTRY_PULLBACK_RATIO) / 10) * 10
    stop     = int(entry * (1 - STOP_LOSS_PCT) / 10) * 10
    target   = int(entry * (1 + TARGET_PCT) / 10) * 10

    return {"code": code, "name": stock.get("name", code), "price": price,
            "change_rate": change_rate, "volume_ratio": vol_ratio,
            "signal_type": signal_type, "score": score,
            "entry_price": entry, "stop_loss": stop, "target_price": target,
            "reasons": reasons, "is_entry_time": is_entry_time()}

def check_entry_points() -> list:
    signals = []
    for code, info in _detected_stocks.items():
        try:
            cur   = get_stock_price(code)
            high  = info.get("high_price", 0)
            price = cur.get("price", 0)
            if not price or not high or price >= high:
                continue
            pullback = (high - price) / high * 100
            if 25 <= pullback <= 55:
                entry  = price
                stop   = int(entry * (1 - STOP_LOSS_PCT) / 10) * 10
                target = int(entry * (1 + TARGET_PCT) / 10) * 10
                signals.append({
                    "code": code, "name": cur.get("name", code), "price": price,
                    "change_rate": cur.get("change_rate", 0), "volume_ratio": 0,
                    "signal_type": "ENTRY_POINT", "score": 95,
                    "entry_price": entry, "stop_loss": stop, "target_price": target,
                    "reasons": [f"🎯 진입 시점! 고점 대비 -{pullback:.1f}% 눌림목",
                                f"📌 고점 {high:,}원 → 현재 {price:,}원"],
                    "is_entry_time": True,
                })
        except:
            continue
    return signals

def run_scan():
    if not is_market_open():
        return
    now = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{now}] 스캔 중...", flush=True)

    alerts, seen = [], set()

    for stock in get_upper_limit_stocks():
        if stock["code"] in seen: continue
        r = analyze(stock)
        if r and time.time() - _alert_history.get(r["code"], 0) > ALERT_COOLDOWN:
            alerts.append(r); seen.add(r["code"])

    for stock in get_volume_surge_stocks():
        if stock["code"] in seen: continue
        r = analyze(stock)
        if r and time.time() - _alert_history.get(r["code"], 0) > ALERT_COOLDOWN:
            alerts.append(r); seen.add(r["code"])

    if is_entry_time():
        for s in check_entry_points():
            if s["code"] not in seen:
                alerts.append(s); seen.add(s["code"])

    alerts.sort(key=lambda x: x["score"], reverse=True)

    if not alerts:
        print("  → 조건 충족 종목 없음")
        return

    print(f"  → {len(alerts)}개 감지!")
    for s in alerts:
        print(f"  ✓ {s['name']} +{s['change_rate']:.1f}% [{s['signal_type']}] {s['score']}점")
        send_alert(s)
        _alert_history[s["code"]] = time.time()
        if s["code"] not in _detected_stocks:
            _detected_stocks[s["code"]] = {"high_price": s["price"]}
        elif s["price"] > _detected_stocks[s["code"]]["high_price"]:
            _detected_stocks[s["code"]]["high_price"] = s["price"]
        time.sleep(1)

# ============================================================
# 📨 텔레그램
# ============================================================
def send(text: str):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10
        )
    except Exception as e:
        print(f"⚠️ 텔레그램 오류: {e}")

def send_alert(s: dict):
    emoji = {"UPPER_LIMIT":"🚨","NEAR_UPPER":"🔥","STRONG_BUY":"💎",
             "SURGE":"📈","ENTRY_POINT":"🎯"}.get(s["signal_type"], "📊")
    title = {"UPPER_LIMIT":"상한가 감지","NEAR_UPPER":"상한가 근접",
             "STRONG_BUY":"강력 매수 신호","SURGE":"급등 감지",
             "ENTRY_POINT":"★ 진입 시점 ★"}.get(s["signal_type"], "급등 감지")
    stars   = "★" * min(int(s["score"] / 20), 5)
    reasons = "\n".join(s["reasons"])
    now     = datetime.now().strftime("%H:%M:%S")

    if s["signal_type"] == "ENTRY_POINT":
        entry_msg = "⚡️ <b>지금 진입 적기입니다!</b>"
    elif s["is_entry_time"]:
        entry_msg = f"⏰ 최적 진입 시간대\n🎯 목표 진입가: <b>{s['entry_price']:,}원</b>"
    else:
        entry_msg = f"⏳ 10:00~11:30 눌림목 대기\n🎯 목표 진입가: <b>{s['entry_price']:,}원</b>"

    send(
        f"{emoji} <b>[{title}]</b>\n"
        f"<b>{s['name']}</b>  {s['code']}\n"
        f"🕐 {now}\n\n"
        f"💰 현재가: <b>{s['price']:,}원</b>  (<b>+{s['change_rate']:.1f}%</b>)\n"
        f"⭐ 신호강도: {stars} ({s['score']}점)\n\n"
        f"━━━━━━━━━━━━━━━\n{reasons}\n━━━━━━━━━━━━━━━\n\n"
        f"{entry_msg}\n\n"
        f"🛡 손절가: <b>{s['stop_loss']:,}원</b>  (-7%)\n"
        f"🏆 목표가: <b>{s['target_price']:,}원</b>  (+15%)\n\n"
        f"⚠️ 투자 판단은 본인 책임입니다"
    )

# ============================================================
# 🚀 실행
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("📈 KIS 주식 급등 알림 봇 시작")
    print("=" * 50)

    send("🤖 <b>주식 급등 알림 봇 ON</b>\n\n"
         "✅ 한국투자증권 API 연결\n"
         "📡 실시간 스캔 시작 (1분 주기)\n\n"
         "<b>감지 조건</b>\n"
         "• 거래량 5배+ 급증\n"
         "• 상승률 5%+ / 상한가 근접\n"
         "• 외국인·기관 수급 동반 시 우선 알림")

    schedule.every(SCAN_INTERVAL).seconds.do(run_scan)
    schedule.every().day.at(MARKET_OPEN).do(
        lambda: send(f"🌅 <b>장 시작!</b> {datetime.now().strftime('%Y-%m-%d')}\n📡 스캔 중..."))
    schedule.every().day.at(MARKET_CLOSE).do(
        lambda: send(f"🔔 <b>장 마감</b>\n오늘 감지 종목: <b>{len(_detected_stocks)}개</b>"))

    run_scan()

    while True:
        schedule.run_pending()
        time.sleep(1)
