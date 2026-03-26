"""
stock_alert.py
Version: v1.00 (2026-03-26)

목표: 연 30%+ 수익 | KIS API 기반 한국주식 급등 알림 봇
시장: KRX 정규장 + NXT + 야간
신호: 거래량급증·급등 / 눌림목반등 / DART공시 / 뉴스모멘텀
알림: 텔레그램 (🔴A급 진입가포함 / 🟡B급 모니터링 / 🔵C급 내부기록)
배포: Railway (환경변수 기반)

Changelog:
- v1.00 (2026-03-26): 최초 작성
  [#1] KRX / NXT / 야간 전체 시장 스캔 구조
  [#2] 신호 4종: 거래량급증·급등 / 눌림목반등 / DART공시 / 뉴스모멘텀
  [#3] 텔레그램 알림: 3색 등급 (🔴A / 🟡B / 🔵C)
  [#4] ATR 기반 진입가·손절가·목표가 자동 계산
  [#5] 진입 체인: analyze() → _dispatch_alert() 연결 확인
  [#6] 텔레그램 명령어: /menu /status /scan /help
  [#7] APScheduler 기반 자동 스캔 스케줄
  [#8] 매일 05:00 캐시 초기화
"""

import os
import time
import logging
import threading
import requests
import pytz
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

# ────────────────────────────────────────────
# 0. 로깅
# ────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)

# ────────────────────────────────────────────
# 1. 환경변수
# ────────────────────────────────────────────
KIS_APP_KEY    = os.environ.get("KIS_APP_KEY", "")
KIS_APP_SECRET = os.environ.get("KIS_APP_SECRET", "")
KIS_ACCOUNT    = os.environ.get("KIS_ACCOUNT", "")
KIS_MOCK       = os.environ.get("KIS_MOCK", "true").lower() == "true"

TG_TOKEN   = os.environ.get("TG_TOKEN", "")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "")

DART_API_KEY = os.environ.get("DART_API_KEY", "")

KST = pytz.timezone("Asia/Seoul")

# ────────────────────────────────────────────
# 2. 유틸리티
# ────────────────────────────────────────────
def _now_kst() -> datetime:
    return datetime.now(KST)

def _today_str() -> str:
    return _now_kst().strftime("%Y%m%d")

def _is_weekday() -> bool:
    return _now_kst().weekday() < 5

def _market_type() -> str:
    from datetime import time as dt
    t = _now_kst().time()
    if _is_weekday() and dt(9, 0) <= t <= dt(15, 30):
        return "KRX"
    if _is_weekday() and dt(8, 0) <= t <= dt(20, 0):
        return "NXT"
    if t >= dt(20, 10) or t <= dt(7, 30):
        return "NIGHT"
    return "CLOSED"

def _in_krx() -> bool:
    return _market_type() == "KRX"

def _in_nxt() -> bool:
    return _market_type() == "NXT"

def _in_night() -> bool:
    return _market_type() == "NIGHT"

# ────────────────────────────────────────────
# 3. KIS API 토큰
# ────────────────────────────────────────────
_token_info = {"token": "", "expires_at": 0.0}
_token_lock = threading.Lock()

def _kis_base() -> str:
    if KIS_MOCK:
        return "https://openapivts.koreainvestment.com:29443"
    return "https://openapi.koreainvestment.com:9443"

def _get_token() -> str:
    with _token_lock:
        now = time.time()
        if _token_info["token"] and now < _token_info["expires_at"] - 60:
            return _token_info["token"]
        try:
            r = requests.post(
                f"{_kis_base()}/oauth2/tokenP",
                json={
                    "grant_type": "client_credentials",
                    "appkey": KIS_APP_KEY,
                    "appsecret": KIS_APP_SECRET,
                },
                timeout=10,
            )
            r.raise_for_status()
            d = r.json()
            _token_info["token"] = d["access_token"]
            _token_info["expires_at"] = now + int(d.get("expires_in", 86400))
            log.info("KIS 토큰 발급 성공")
        except Exception as e:
            log.error(f"KIS 토큰 발급 실패: {e}")
        return _token_info["token"]

def _headers(tr_id: str) -> dict:
    return {
        "content-type": "application/json",
        "authorization": f"Bearer {_get_token()}",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET,
        "tr_id": tr_id,
    }

# ────────────────────────────────────────────
# 4. 텔레그램
# ────────────────────────────────────────────
_tg_lock = threading.Lock()

def send_tg(msg: str):
    if not TG_TOKEN or not TG_CHAT_ID:
        log.info(f"[TG 미설정] {msg[:60]}")
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    for attempt in range(3):
        try:
            with _tg_lock:
                r = requests.post(
                    url,
                    json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"},
                    timeout=10,
                )
            if r.status_code == 200:
                return
            log.warning(f"TG 전송 실패 {r.status_code}")
        except Exception as e:
            log.error(f"TG 오류 {attempt+1}/3: {e}")
        time.sleep(2 ** attempt)

def _dispatch_alert(stock: dict):
    """
    진입 체인 최종 발송.
    A급 + entry_price > 0 → 진입가 포함 알림
    B급 → 모니터링 알림
    C급 → 내부 로그만 (사용자 알림 없음)
    진입 체인: analyze() → _dispatch_alert() 연결 확인
    """
    grade  = stock.get("grade", "C")
    icon   = {"A": "🔴", "B": "🟡", "C": "🔵"}.get(grade, "⚪")
    name   = stock.get("name", "")
    code   = stock.get("code", "")
    signal = stock.get("signal", "")
    price  = stock.get("price", 0)
    entry  = stock.get("entry_price", 0)
    stop   = stock.get("stop_price", 0)
    target = stock.get("target_price", 0)
    market = stock.get("market", "KRX")
    score  = stock.get("score", 0)

    if grade == "C":
        log.info(f"[C급 내부기록] {name}({code}) {signal} 점수:{score:.0f}")
        return

    if grade == "A" and entry > 0:
        msg = (
            f"{icon} <b>[A급] {name} ({code})</b>\n"
            f"시장: {market} | 신호: {signal}\n"
            f"현재가: {price:,}원\n"
            f"진입가: {entry:,}원 | 손절: {stop:,}원 | 목표: {target:,}원\n"
            f"점수: {score:.0f}"
        )
    else:
        msg = (
            f"{icon} <b>[B급 모니터링] {name} ({code})</b>\n"
            f"시장: {market} | 신호: {signal}\n"
            f"현재가: {price:,}원 | 점수: {score:.0f}"
        )

    send_tg(msg)
    log.info(f"알림 발송: {grade}급 {name}({code}) {signal}")

# ────────────────────────────────────────────
# 5. KIS 데이터 조회
# ────────────────────────────────────────────
def _get_stock_info(code: str) -> dict:
    try:
        r = requests.get(
            f"{_kis_base()}/uapi/domestic-stock/v1/quotations/inquire-price",
            headers=_headers("FHKST01010100"),
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code},
            timeout=5,
        )
        r.raise_for_status()
        o = r.json().get("output", {})
        return {
            "code": code,
            "name": o.get("hts_kor_isnm", ""),
            "price": int(o.get("stck_prpr", 0) or 0),
            "volume": int(o.get("acml_vol", 0) or 0),
            "change_rate": float(o.get("prdy_ctrt", 0) or 0),
        }
    except Exception as e:
        log.debug(f"현재가 조회 실패 {code}: {e}")
        return {}

def _get_volume_rank() -> list:
    try:
        r = requests.get(
            f"{_kis_base()}/uapi/domestic-stock/v1/quotations/volume-rank",
            headers=_headers("FHPST01710000"),
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_COND_SCR_DIV_CODE": "20171",
                "FID_INPUT_ISCD": "0000",
                "FID_DIV_CLS_CODE": "0",
                "FID_BLNG_CLS_CODE": "0",
                "FID_TRGT_CLS_CODE": "111111111",
                "FID_TRGT_EXLS_CLS_CODE": "000000",
                "FID_INPUT_PRICE_1": "1000",
                "FID_INPUT_PRICE_2": "500000",
                "FID_VOL_CNT": "100000",
                "FID_INPUT_DATE_1": "",
            },
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("output", [])
    except Exception as e:
        log.error(f"거래량 순위 조회 실패: {e}")
        return []

def _get_daily_prices(code: str, days: int = 40) -> list:
    try:
        start = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        r = requests.get(
            f"{_kis_base()}/uapi/domestic-stock/v1/quotations/inquire-daily-price",
            headers=_headers("FHKST01010400"),
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_PERIOD_DIV_CODE": "D",
                "FID_ORG_ADJ_PRC": "0",
                "FID_INPUT_DATE_1": start,
                "FID_INPUT_DATE_2": _today_str(),
            },
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("output2", [])
    except Exception as e:
        log.debug(f"일봉 조회 실패 {code}: {e}")
        return []

# ────────────────────────────────────────────
# 6. DART 공시
# ────────────────────────────────────────────
_DART_POSITIVE = ["자기주식소각", "무상증자", "배당"]
_DART_WATCH    = ["자기주식취득", "유상증자", "실적", "매출"]

def _fetch_dart() -> list:
    if not DART_API_KEY:
        return []
    try:
        r = requests.get(
            "https://opendart.fss.or.kr/api/list.json",
            params={
                "crtfc_key": DART_API_KEY,
                "bgn_de": (datetime.now() - timedelta(days=1)).strftime("%Y%m%d"),
                "end_de": _today_str(),
                "page_count": 40,
            },
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("list", [])
    except Exception as e:
        log.error(f"DART 조회 실패: {e}")
        return []

def _parse_dart(item: dict):
    report = item.get("report_nm", "")
    code   = item.get("stock_code", "")
    corp   = item.get("corp_name", "")
    if not code:
        return None
    for kw in _DART_POSITIVE + _DART_WATCH:
        if kw in report:
            score = 72 if kw in _DART_POSITIVE else 55
            return {"code": code, "name": corp, "signal": f"DART:{kw}", "score": score}
    return None

# ────────────────────────────────────────────
# 7. 분석 (진입 체인 핵심)
# ────────────────────────────────────────────
def _calc_atr(history: list, period: int = 14) -> float:
    trs = []
    for i in range(1, min(period + 1, len(history))):
        h = int(history[i].get("stck_hgpr", 0) or 0)
        l = int(history[i].get("stck_lwpr", 0) or 0)
        c = int(history[i-1].get("stck_clpr", 0) or 0)
        if c > 0:
            trs.append(max(h - l, abs(h - c), abs(l - c)))
    return sum(trs) / len(trs) if trs else 0.0

def analyze(stock: dict) -> dict:
    """
    종목 분석 → grade / entry_price / stop_price / target_price 산출.
    모든 신호 감지 함수는 반드시 이 함수를 거쳐야 한다.
    진입 체인: analyze() → _dispatch_alert()
    """
    code  = stock.get("code", "")
    price = stock.get("price", 0)

    if price <= 0:
        stock["grade"] = "C"
        return stock

    history = _get_daily_prices(code, 30)
    atr = _calc_atr(history)
    if atr <= 0:
        atr = price * 0.02

    score       = float(stock.get("score", 50))
    change_rate = stock.get("change_rate", 0)
    volume      = stock.get("volume", 0)
    signal      = stock.get("signal", "")

    if change_rate >= 10:    score += 15
    elif change_rate >= 5:   score += 8
    if volume > 5_000_000:   score += 10
    elif volume > 1_000_000: score += 5
    if "DART" in signal:     score += 8
    if "눌림목" in signal:   score += 5
    score = min(score, 100)

    if score >= 75:   grade = "A"
    elif score >= 55: grade = "B"
    else:             grade = "C"

    entry_price  = price
    stop_price   = max(round((price - atr * 1.5) / 10) * 10, 1)
    target_price = round((price + atr * 3.0) / 10) * 10

    stock.update({
        "score":        round(score, 1),
        "grade":        grade,
        "entry_price":  entry_price,
        "stop_price":   stop_price,
        "target_price": target_price,
        "atr":          round(atr, 1),
    })
    return stock

# ────────────────────────────────────────────
# 8. 신호 감지
# ────────────────────────────────────────────
_sent: dict = {"volume": set(), "pullback": set(), "dart": set(), "news": set()}

def scan_volume_surge():
    if not (_in_krx() or _in_nxt()):
        return
    market = _market_type()
    log.info(f"[{market}] 거래량 급증 스캔")
    for row in _get_volume_rank()[:30]:
        code        = row.get("mksc_shrn_iscd", "")
        name        = row.get("hts_kor_isnm", "")
        change_rate = float(row.get("prdy_ctrt", 0) or 0)
        volume      = int(row.get("acml_vol", 0) or 0)
        price       = int(row.get("stck_prpr", 0) or 0)
        if not code or code in _sent["volume"]:
            continue
        if change_rate < 5 or volume < 500_000:
            continue
        signal = "거래량급증+급등" if change_rate >= 10 else "거래량급증"
        stock = analyze({
            "code": code, "name": name, "price": price,
            "volume": volume, "change_rate": change_rate,
            "signal": signal, "score": 60, "market": market,
        })
        _dispatch_alert(stock)
        if stock["grade"] == "A":
            _sent["volume"].add(code)

def scan_pullback():
    if not _in_krx():
        return
    log.info("[KRX] 눌림목 스캔")
    for row in _get_volume_rank()[:50]:
        code = row.get("mksc_shrn_iscd", "")
        name = row.get("hts_kor_isnm", "")
        if not code or code in _sent["pullback"]:
            continue
        history = _get_daily_prices(code, 30)
        if len(history) < 10:
            continue
        closes = [int(d.get("stck_clpr", 0) or 0) for d in history]
        if closes[0] <= 0:
            continue
        recent_high = max(closes[5:]) if len(closes) > 5 else closes[0]
        if recent_high <= 0:
            continue
        drop = (recent_high - closes[0]) / recent_high * 100
        if not (8 <= drop <= 25):
            continue
        if len(closes) >= 2 and closes[0] <= closes[1]:
            continue
        info = _get_stock_info(code)
        if not info:
            continue
        stock = analyze({**info, "signal": "눌림목반등", "score": 65, "market": "KRX"})
        _dispatch_alert(stock)
        if stock["grade"] == "A":
            _sent["pullback"].add(code)

def scan_dart():
    log.info("[DART] 공시 스캔")
    for item in _fetch_dart():
        sig = _parse_dart(item)
        if not sig:
            continue
        key = f"{sig['code']}_{sig['signal']}"
        if key in _sent["dart"]:
            continue
        info = _get_stock_info(sig["code"])
        if info:
            sig.update(info)
        sig["market"] = _market_type()
        stock = analyze(sig)
        _dispatch_alert(stock)
        _sent["dart"].add(key)

def scan_news_momentum():
    if not _in_krx():
        return
    log.info("[KRX] 뉴스 모멘텀 스캔")
    for row in _get_volume_rank()[:20]:
        code        = row.get("mksc_shrn_iscd", "")
        name        = row.get("hts_kor_isnm", "")
        change_rate = float(row.get("prdy_ctrt", 0) or 0)
        vol_ratio   = float(row.get("vol_inrt", 0) or 0)
        price       = int(row.get("stck_prpr", 0) or 0)
        volume      = int(row.get("acml_vol", 0) or 0)
        if not code or code in _sent["news"]:
            continue
        if change_rate < 5 or vol_ratio < 200:
            continue
        stock = analyze({
            "code": code, "name": name, "price": price,
            "volume": volume, "change_rate": change_rate,
            "signal": "뉴스모멘텀", "score": 65, "market": "KRX",
        })
        _dispatch_alert(stock)
        if stock["grade"] == "A":
            _sent["news"].add(code)

def scan_night():
    if not _in_night():
        return
    log.info("[NIGHT] 야간 모니터링 실행")

# ────────────────────────────────────────────
# 9. 일일 초기화
# ────────────────────────────────────────────
def reset_daily():
    for s in _sent.values():
        s.clear()
    log.info("일일 캐시 초기화 완료")
    send_tg("🌅 <b>일일 초기화 완료</b> — 오늘도 좋은 거래 되세요!")

# ────────────────────────────────────────────
# 10. 텔레그램 명령어
# ────────────────────────────────────────────
_last_upd = 0

def _handle_cmd(text: str):
    text = text.strip().lower()
    now  = _now_kst().strftime("%Y-%m-%d %H:%M")
    mkt  = _market_type()

    if text in ("/start", "/menu"):
        send_tg(
            f"📊 <b>주식 알림 봇 v1.00</b>\n"
            f"시각: {now} | 시장: {mkt}\n\n"
            "/status — 현재 상태\n"
            "/scan — 즉시 전체 스캔\n"
            "/help — 등급 설명"
        )
    elif text == "/status":
        send_tg(
            f"⚙️ <b>상태</b>\n"
            f"시각: {now} | 시장: {mkt}\n"
            f"거래량 포착: {len(_sent['volume'])}건\n"
            f"눌림목 포착: {len(_sent['pullback'])}건\n"
            f"DART 포착: {len(_sent['dart'])}건\n"
            f"뉴스 포착: {len(_sent['news'])}건"
        )
    elif text == "/scan":
        send_tg("🔍 즉시 스캔 시작...")
        scan_volume_surge()
        scan_pullback()
        scan_dart()
        scan_news_momentum()
        send_tg("✅ 스캔 완료")
    elif text == "/help":
        send_tg(
            "📖 <b>알림 등급 안내</b>\n\n"
            "🔴 <b>A급</b> — 진입가·손절가·목표가 포함\n"
            "🟡 <b>B급</b> — 모니터링 알림\n"
            "🔵 <b>C급</b> — 내부 기록만 (알림 없음)\n\n"
            "<b>신호 종류</b>\n"
            "• 거래량급증+급등\n"
            "• 눌림목반등\n"
            "• DART공시\n"
            "• 뉴스모멘텀"
        )
    else:
        send_tg(f"❓ 모르는 명령어: {text}\n/menu 로 확인하세요")

def poll_tg():
    global _last_upd
    if not TG_TOKEN:
        return
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates",
            params={"offset": _last_upd + 1, "timeout": 5},
            timeout=10,
        )
        r.raise_for_status()
        for upd in r.json().get("result", []):
            _last_upd = upd["update_id"]
            txt = upd.get("message", {}).get("text", "")
            if txt.startswith("/"):
                _handle_cmd(txt)
    except Exception as e:
        log.debug(f"TG 폴링 오류: {e}")

# ────────────────────────────────────────────
# 11. 스케줄러
# ────────────────────────────────────────────
def start_scheduler():
    sched = BackgroundScheduler(timezone=KST)
    sched.add_job(scan_volume_surge,  "cron", day_of_week="mon-fri", hour="8-20",  minute="*/2")
    sched.add_job(scan_pullback,      "cron", day_of_week="mon-fri", hour="9-15",  minute="*/30")
    sched.add_job(scan_dart,          "interval", hours=1)
    sched.add_job(scan_news_momentum, "cron", day_of_week="mon-fri", hour="9-15",  minute="*/5")
    sched.add_job(scan_night,         "interval", minutes=30)
    sched.add_job(reset_daily,        "cron", hour=5, minute=0)
    sched.add_job(poll_tg,            "interval", seconds=3)
    sched.start()
    log.info("스케줄러 시작")
    return sched

# ────────────────────────────────────────────
# 12. 메인
# ────────────────────────────────────────────
def main():
    log.info("=" * 50)
    log.info("주식 알림 봇 v1.00 시작")
    log.info(f"모의투자: {KIS_MOCK} | 시장: {_market_type()}")
    log.info("=" * 50)

    missing = [v for v in ["KIS_APP_KEY", "KIS_APP_SECRET", "TG_TOKEN", "TG_CHAT_ID"]
               if not os.environ.get(v)]
    if missing:
        log.warning(f"환경변수 누락: {', '.join(missing)}")

    send_tg(
        f"🚀 <b>주식 알림 봇 v1.00 시작</b>\n"
        f"시각: {_now_kst().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"시장: {_market_type()}\n"
        f"/menu 로 명령어 확인"
    )

    sched = start_scheduler()
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        sched.shutdown()
        log.info("봇 종료")

if __name__ == "__main__":
    main()
