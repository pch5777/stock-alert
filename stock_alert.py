#!/usr/bin/env python3
"""
📈 KIS 주식 급등 알림 봇 v4
- 급등 감지 후 30분~1시간 뒤 눌림목 자동 체크
- 시간대별 진입 안내 메시지
- API 오류 자동 복구
"""

import os
import requests
import time
import schedule
from datetime import datetime, time as dtime, timedelta

# ============================================================
# ⚙️ 환경변수 (Railway Variables에서 설정)
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
SCAN_INTERVAL         = 60       # 1분마다 스캔
ALERT_COOLDOWN        = 1800     # 30분 중복 알림 방지
MARKET_OPEN           = "09:00"
MARKET_CLOSE          = "15:30"
ENTRY_PULLBACK_RATIO  = 0.4
STOP_LOSS_PCT         = 0.07
TARGET_PCT            = 0.15

# 눌림목 체크 시작: 급등 감지 후 30분 뒤
PULLBACK_CHECK_START  = 30       # 분
# 눌림목 체크 종료: 급등 감지 후 90분 뒤 (또는 장 마감)
PULLBACK_CHECK_END    = 90       # 분

# ============================================================
# 🔐 KIS API
# ============================================================
_access_token  = None
_token_expires = 0
_session       = requests.Session()

def get_token(retry: int = 3) -> str:
    global _access_token, _token_expires
    if _access_token and time.time() < _token_expires:
        return _access_token
    _access_token = None
    for attempt in range(retry):
        try:
            resp = _session.post(
                f"{KIS_BASE_URL}/oauth2/tokenP",
                json={"grant_type": "client_credentials",
                      "appkey": KIS_APP_KEY, "appsecret": KIS_APP_SECRET},
                timeout=15
            )
            resp.raise_for_status()
            data           = resp.json()
            _access_token  = data["access_token"]
            _token_expires = time.time() + int(data.get("expires_in", 86400)) - 300
            print(f"✅ KIS 토큰 발급 완료 ({datetime.now().strftime('%H:%M:%S')})")
            return _access_token
        except Exception as e:
            print(f"⚠️ 토큰 발급 실패 ({attempt+1}/{retry}): {e}")
            time.sleep(5 * (attempt + 1))
    raise Exception("❌ KIS 토큰 발급 최종 실패")

def _headers(tr_id: str) -> dict:
    return {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {get_token()}",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET,
        "tr_id": tr_id,
        "custtype": "P",
    }

def _safe_get(url: str, tr_id: str, params: dict) -> dict:
    try:
        resp = _session.get(url, headers=_headers(tr_id), params=params, timeout=15)
        if resp.status_code == 403:
            global _access_token
            _access_token = None
            resp = _session.get(url, headers=_headers(tr_id), params=params, timeout=15)
        return resp.json() if resp.status_code == 200 else {}
    except Exception as e:
        print(f"⚠️ API 호출 오류 ({tr_id}): {e}")
        return {}

def get_stock_price(code: str) -> dict:
    url    = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
    data   = _safe_get(url, "FHKST01010100", params)
    o      = data.get("output", {})
    price  = int(o.get("stck_prpr", 0))
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
    data  = _safe_get(url, "FHPST01700000", params)
    items = data.get("output", [])
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
    data  = _safe_get(url, "FHPST01710000", params)
    items = data.get("output", [])
    return [{"code": i.get("mksc_shrn_iscd",""), "name": i.get("hts_kor_isnm",""),
             "price": int(i.get("stck_prpr",0)), "change_rate": float(i.get("prdy_ctrt",0)),
             "volume_ratio": float(i.get("vol_inrt",0) or 0)} for i in items if i.get("mksc_shrn_iscd")]

def get_investor_trend(code: str) -> dict:
    url    = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-investor"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
    data   = _safe_get(url, "FHKST01010900", params)
    output = data.get("output", [])
    if not output:
        return {}
    return {"foreign_net": int(output[0].get("frgn_ntby_qty", 0)),
            "institution_net": int(output[0].get("orgn_ntby_qty", 0))}

# ============================================================
# 🕐 시간대 판단
# ============================================================
def is_market_open() -> bool:
    now = datetime.now().time()
    o   = dtime(*map(int, MARKET_OPEN.split(":")))
    c   = dtime(*map(int, MARKET_CLOSE.split(":")))
    return o <= now <= c

def get_entry_msg(entry_price: int, stop: int, target: int,
                  detected_at: datetime) -> str:
    """
    급등 감지 시각 기준으로 시간대별 진입 안내 메시지 생성
    - 감지 직후 (0~30분):   30분 후 눌림목 대기 안내
    - 감지 후 30~90분:      눌림목 진입 적기
    - 감지 후 90분 이상:    오늘 진입 시간 종료
    - 14:30 이후 감지:      내일 장 초반 노려야 함
    """
    now          = datetime.now()
    elapsed_min  = (now - detected_at).seconds // 60
    market_close = now.replace(hour=15, minute=30, second=0)
    remaining    = int((market_close - now).seconds / 60)

    # 14:30 이후 감지 → 당일 눌림목 시간 부족
    if now.time() >= dtime(14, 30):
        return (
            f"⏳ <b>당일 진입 시간 부족</b>\n"
            f"📌 내일 장 초반 (9:00~10:00) 동향 확인 후 진입 고려\n"
            f"🎯 참고 진입가: <b>{entry_price:,}원</b>"
        )

    # 감지 후 0~30분: 눌림목 대기 중
    elif elapsed_min < PULLBACK_CHECK_START:
        wait = PULLBACK_CHECK_START - elapsed_min
        pullback_time = (detected_at + timedelta(minutes=PULLBACK_CHECK_START)).strftime("%H:%M")
        return (
            f"⏰ <b>눌림목 대기 중</b> ({wait}분 후 체크 시작)\n"
            f"🕐 {pullback_time} 부터 눌림목 진입 신호 체크\n"
            f"🎯 목표 진입가: <b>{entry_price:,}원</b>"
        )

    # 감지 후 30~90분: 눌림목 진입 적기
    elif elapsed_min <= PULLBACK_CHECK_END:
        return (
            f"⚡️ <b>지금 눌림목 진입 구간!</b>\n"
            f"🎯 목표 진입가: <b>{entry_price:,}원</b>\n"
            f"   (현재가 눌릴 때 분할 진입)"
        )

    # 감지 후 90분 이상: 진입 시간 종료
    else:
        return (
            f"⏳ <b>오늘 진입 시간대 종료</b>\n"
            f"📌 내일 장 초반 동향 확인 후 진입 고려\n"
            f"🎯 참고 진입가: <b>{entry_price:,}원</b>"
        )

# ============================================================
# 📊 스캐너
# ============================================================
_alert_history   = {}
_detected_stocks = {}  # { code: { high_price, detected_at, entry_price, stop, target } }

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
            "reasons": reasons, "detected_at": datetime.now()}

def check_pullback_signals() -> list:
    """
    감지된 종목 중 30~90분 지난 것들의 눌림목 체크
    """
    signals = []
    now     = datetime.now()

    for code, info in list(_detected_stocks.items()):
        detected_at = info.get("detected_at")
        if not detected_at:
            continue

        elapsed_min = (now - detected_at).seconds // 60

        # 30~90분 사이만 눌림목 체크
        if not (PULLBACK_CHECK_START <= elapsed_min <= PULLBACK_CHECK_END):
            continue

        # 14:30 이후는 체크 안 함 (시간 부족)
        if now.time() >= dtime(14, 30):
            continue

        try:
            cur   = get_stock_price(code)
            high  = info.get("high_price", 0)
            price = cur.get("price", 0)
            if not price or not high or price >= high:
                continue

            pullback = (high - price) / high * 100

            # 고점 대비 25~55% 되돌림 = 눌림목 진입 신호
            if 25 <= pullback <= 55:
                entry  = price
                stop   = int(entry * (1 - STOP_LOSS_PCT) / 10) * 10
                target = int(entry * (1 + TARGET_PCT) / 10) * 10

                signals.append({
                    "code": code,
                    "name": cur.get("name", code),
                    "price": price,
                    "change_rate": cur.get("change_rate", 0),
                    "volume_ratio": 0,
                    "signal_type": "ENTRY_POINT",
                    "score": 95,
                    "entry_price": entry,
                    "stop_loss": stop,
                    "target_price": target,
                    "reasons": [
                        f"🎯 눌림목 진입 시점!",
                        f"📌 고점 {high:,}원 → 현재 {price:,}원 (-{pullback:.1f}%)",
                        f"⏱ 급등 감지 후 {elapsed_min}분 경과",
                    ],
                    "detected_at": detected_at,
                })
        except:
            continue

    return signals

def run_scan():
    if not is_market_open():
        return
    now = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{now}] 스캔 중...", flush=True)

    try:
        alerts, seen = [], set()

        # ① 급등/상한가 종목 스캔
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

        # ② 눌림목 진입 시점 체크 (감지 후 30~90분)
        for s in check_pullback_signals():
            if s["code"] not in seen:
                alerts.append(s); seen.add(s["code"])

        alerts.sort(key=lambda x: x["score"], reverse=True)

        if not alerts:
            print("  → 조건 충족 종목 없음"); return

        print(f"  → {len(alerts)}개 감지!")
        for s in alerts:
            print(f"  ✓ {s['name']} +{s['change_rate']:.1f}% [{s['signal_type']}] {s['score']}점")
            send_alert(s)
            _alert_history[s["code"]] = time.time()

            # 급등 감지 종목 등록 (눌림목 모니터링용)
            if s["signal_type"] != "ENTRY_POINT":
                if s["code"] not in _detected_stocks:
                    _detected_stocks[s["code"]] = {
                        "high_price":  s["price"],
                        "detected_at": s["detected_at"],
                        "entry_price": s["entry_price"],
                        "stop_loss":   s["stop_loss"],
                        "target_price":s["target_price"],
                    }
                elif s["price"] > _detected_stocks[s["code"]]["high_price"]:
                    _detected_stocks[s["code"]]["high_price"] = s["price"]

            time.sleep(1)

    except Exception as e:
        print(f"⚠️ 스캔 오류 (다음 스캔에서 재시도): {e}")

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
             "ENTRY_POINT":"★ 눌림목 진입 시점 ★"}.get(s["signal_type"], "급등 감지")
    stars   = "★" * min(int(s["score"] / 20), 5)
    reasons = "\n".join(s["reasons"])
    now     = datetime.now().strftime("%H:%M:%S")

    # 진입 안내 메시지
    if s["signal_type"] == "ENTRY_POINT":
        entry_msg = (
            f"⚡️ <b>지금 눌림목 진입 구간!</b>\n"
            f"🎯 진입가: <b>{s['entry_price']:,}원</b>\n"
            f"   (분할 매수 추천)"
        )
    else:
        detected_at = s.get("detected_at", datetime.now())
        entry_msg   = get_entry_msg(
            s["entry_price"], s["stop_loss"], s["target_price"], detected_at
        )

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
    print("📈 KIS 주식 급등 알림 봇 v4 시작")
    print("=" * 50)

    send("🤖 <b>주식 급등 알림 봇 ON (v4)</b>\n\n"
         "✅ 한국투자증권 API 연결\n"
         "📡 실시간 스캔 (1분 주기)\n"
         "🎯 급등 감지 후 30~90분 눌림목 자동 체크\n\n"
         "<b>눌림목 체크 방식</b>\n"
         "• 급등 감지 즉시 → 30분 후 체크 예고\n"
         "• 감지 후 30~90분 → 눌림목 진입 신호 체크\n"
         "• 14:30 이후 감지 → 내일 진입 안내")

    schedule.every(SCAN_INTERVAL).seconds.do(run_scan)
    schedule.every().day.at(MARKET_OPEN).do(
        lambda: send(f"🌅 <b>장 시작!</b> {datetime.now().strftime('%Y-%m-%d')}\n📡 스캔 중..."))
    schedule.every().day.at(MARKET_CLOSE).do(
        lambda: send(f"🔔 <b>장 마감</b>\n오늘 감지 종목: <b>{len(_detected_stocks)}개</b>"))

    run_scan()

    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ 메인 루프 오류 (계속 실행): {e}")
            time.sleep(5)
