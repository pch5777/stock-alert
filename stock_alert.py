#!/usr/bin/env python3
"""
📈 KIS 주식 급등 알림 봇 v5
- 감지된 종목은 장 마감(15:30)까지 1분마다 눌림목 체크
- 당일 눌림목 미발생 시 다음날 장 시작부터 다시 체크
- API 오류 자동 복구
"""

import os
import requests
import time
import schedule
import json
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
SCAN_INTERVAL         = 60
ALERT_COOLDOWN        = 1800
MARKET_OPEN           = "09:00"
MARKET_CLOSE          = "15:30"
ENTRY_PULLBACK_RATIO  = 0.4
STOP_LOSS_PCT         = 0.07
TARGET_PCT            = 0.15

# 눌림목 체크: 감지 후 30분 뒤부터 시작
PULLBACK_CHECK_AFTER  = 30      # 분
# 눌림목 유효 범위: 고점 대비 25~55% 되돌림
PULLBACK_MIN          = 25.0
PULLBACK_MAX          = 55.0

# 이월 종목 최대 보유 기간 (일) - 너무 오래된 종목은 제거
MAX_CARRY_DAYS        = 3

# ============================================================
# 💾 이월 종목 저장 파일 (서버 재시작 시 복원)
# ============================================================
CARRY_FILE = "carry_stocks.json"

def save_carry_stocks():
    """이월 종목을 파일에 저장"""
    try:
        data = {}
        for code, info in _detected_stocks.items():
            data[code] = {
                "name":         info["name"],
                "high_price":   info["high_price"],
                "entry_price":  info["entry_price"],
                "stop_loss":    info["stop_loss"],
                "target_price": info["target_price"],
                "detected_at":  info["detected_at"].strftime("%Y%m%d%H%M%S"),
                "carry_day":    info.get("carry_day", 0),
            }
        with open(CARRY_FILE, "w") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ 이월 저장 실패: {e}")

def load_carry_stocks():
    """이월 종목 파일에서 복원"""
    try:
        with open(CARRY_FILE, "r") as f:
            data = json.load(f)
        for code, info in data.items():
            detected_at = datetime.strptime(info["detected_at"], "%Y%m%d%H%M%S")
            carry_day   = info.get("carry_day", 0)
            # 최대 보유 기간 초과 시 제외
            if carry_day >= MAX_CARRY_DAYS:
                continue
            _detected_stocks[code] = {
                "name":         info["name"],
                "high_price":   info["high_price"],
                "entry_price":  info["entry_price"],
                "stop_loss":    info["stop_loss"],
                "target_price": info["target_price"],
                "detected_at":  detected_at,
                "carry_day":    carry_day,
                "pullback_alerted": False,
            }
        if _detected_stocks:
            print(f"📂 이월 종목 {len(_detected_stocks)}개 복원")
            send(f"📂 <b>이월 종목 복원</b>\n"
                 f"다음 종목 눌림목 체크 재개:\n" +
                 "\n".join([f"• {v['name']} ({k})" for k, v in _detected_stocks.items()]))
    except:
        pass  # 파일 없으면 그냥 시작

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
# 🕐 시간 유틸
# ============================================================
def is_market_open() -> bool:
    now = datetime.now().time()
    o   = dtime(*map(int, MARKET_OPEN.split(":")))
    c   = dtime(*map(int, MARKET_CLOSE.split(":")))
    return o <= now <= c

def minutes_since(dt: datetime) -> int:
    return int((datetime.now() - dt).total_seconds() // 60)

# ============================================================
# 📊 스캐너
# ============================================================
_alert_history    = {}
_detected_stocks  = {}  # { code: { name, high_price, entry_price, stop_loss, target_price, detected_at, carry_day, pullback_alerted } }
_pullback_history = {}  # { code: last_pullback_alert_time } - 눌림목 중복 알림 방지

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
    감지된 전체 종목 장 마감까지 눌림목 체크
    - 감지 후 30분 이후부터 체크 시작
    - 눌림목 알림 후 30분 쿨다운
    """
    signals = []
    now     = datetime.now()

    for code, info in list(_detected_stocks.items()):
        detected_at = info.get("detected_at")
        if not detected_at:
            continue

        # 감지 후 30분 이전은 체크 안 함
        if minutes_since(detected_at) < PULLBACK_CHECK_AFTER:
            continue

        # 눌림목 알림 쿨다운 (30분)
        last_pullback = _pullback_history.get(code, 0)
        if time.time() - last_pullback < 1800:
            continue

        try:
            cur   = get_stock_price(code)
            high  = info.get("high_price", 0)
            price = cur.get("price", 0)
            if not price or not high:
                continue

            # 고점 업데이트
            if price > high:
                _detected_stocks[code]["high_price"] = price
                continue

            pullback = (high - price) / high * 100
            elapsed  = minutes_since(detected_at)
            carry    = info.get("carry_day", 0)

            if PULLBACK_MIN <= pullback <= PULLBACK_MAX:
                entry  = price
                stop   = int(entry * (1 - STOP_LOSS_PCT) / 10) * 10
                target = int(entry * (1 + TARGET_PCT) / 10) * 10

                carry_text = f" (이월 {carry}일차)" if carry > 0 else ""
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
                        f"🎯 눌림목 진입 시점{carry_text}",
                        f"📌 고점 {high:,}원 → 현재 {price:,}원 (-{pullback:.1f}%)",
                        f"⏱ 최초 급등 감지 후 {elapsed}분 경과",
                    ],
                    "detected_at": detected_at,
                })
                _pullback_history[code] = time.time()

        except:
            continue

    return signals

def on_market_close():
    """장 마감 시 눌림목 미발생 종목 이월 처리"""
    carry_list = []
    for code, info in list(_detected_stocks.items()):
        carry_day = info.get("carry_day", 0)
        if carry_day >= MAX_CARRY_DAYS:
            # 최대 보유 기간 초과 → 제거
            del _detected_stocks[code]
            continue
        # 이월 처리
        _detected_stocks[code]["carry_day"]    = carry_day + 1
        _detected_stocks[code]["detected_at"]  = datetime.now()  # 다음날 즉시 체크 가능하도록 리셋
        carry_list.append(f"• {info['name']} ({code}) - {carry_day+1}일차")

    save_carry_stocks()

    total = len(_detected_stocks)
    msg   = (
        f"🔔 <b>장 마감</b>  {datetime.now().strftime('%Y-%m-%d')}\n"
        f"오늘 감지 종목: <b>{total}개</b>\n"
    )
    if carry_list:
        msg += f"\n📂 <b>내일 이월 종목 ({len(carry_list)}개)</b>\n"
        msg += "\n".join(carry_list)
        msg += "\n\n내일 장 시작 시 눌림목 체크 재개"
    send(msg)

def run_scan():
    if not is_market_open():
        return
    now = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{now}] 스캔 중...", flush=True)

    try:
        alerts, seen = [], set()

        # ① 새 급등 종목 스캔
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

        # ② 기존 감지 종목 눌림목 체크 (장 마감까지 전체)
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

            # 신규 급등 종목 등록
            if s["signal_type"] != "ENTRY_POINT":
                if s["code"] not in _detected_stocks:
                    _detected_stocks[s["code"]] = {
                        "name":             s["name"],
                        "high_price":       s["price"],
                        "entry_price":      s["entry_price"],
                        "stop_loss":        s["stop_loss"],
                        "target_price":     s["target_price"],
                        "detected_at":      s["detected_at"],
                        "carry_day":        0,
                        "pullback_alerted": False,
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

    if s["signal_type"] == "ENTRY_POINT":
        entry_msg = (
            f"⚡️ <b>지금 눌림목 진입 구간!</b>\n"
            f"🎯 진입가: <b>{s['entry_price']:,}원</b>\n"
            f"   (분할 매수 추천)"
        )
    else:
        detected_at  = s.get("detected_at", datetime.now())
        elapsed      = minutes_since(detected_at)
        pullback_time = (detected_at + timedelta(minutes=PULLBACK_CHECK_AFTER)).strftime("%H:%M")
        if elapsed < PULLBACK_CHECK_AFTER:
            wait = PULLBACK_CHECK_AFTER - elapsed
            entry_msg = (
                f"⏰ <b>눌림목 대기 중</b> ({wait}분 후 체크 시작)\n"
                f"🕐 {pullback_time} 부터 장 마감까지 눌림목 체크\n"
                f"🎯 목표 진입가: <b>{s['entry_price']:,}원</b>"
            )
        else:
            entry_msg = (
                f"📡 <b>눌림목 실시간 체크 중</b>\n"
                f"🎯 목표 진입가: <b>{s['entry_price']:,}원</b>\n"
                f"   (고점 대비 25~55% 되돌림 시 즉시 알림)"
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
    print("📈 KIS 주식 급등 알림 봇 v5 시작")
    print("=" * 50)

    # 이월 종목 복원
    load_carry_stocks()

    send("🤖 <b>주식 급등 알림 봇 ON (v5)</b>\n\n"
         "✅ 한국투자증권 API 연결\n"
         "📡 실시간 스캔 (1분 주기)\n"
         "🎯 감지 종목 장 마감까지 눌림목 체크\n"
         "📂 당일 미발생 시 다음날 자동 이월\n\n"
         "<b>눌림목 체크 방식</b>\n"
         "• 급등 감지 후 30분 뒤부터 체크 시작\n"
         "• 장 마감(15:30)까지 1분마다 체크\n"
         "• 당일 미발생 → 다음날 장 시작부터 재체크\n"
         f"• 최대 {MAX_CARRY_DAYS}일 이월")

    schedule.every(SCAN_INTERVAL).seconds.do(run_scan)
    schedule.every().day.at(MARKET_OPEN).do(
        lambda: send(f"🌅 <b>장 시작!</b>  {datetime.now().strftime('%Y-%m-%d')}\n"
                     f"📂 이월 종목: {len(_detected_stocks)}개\n📡 스캔 중..."))
    schedule.every().day.at(MARKET_CLOSE).do(on_market_close)

    run_scan()

    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ 메인 루프 오류 (계속 실행): {e}")
            time.sleep(5)
