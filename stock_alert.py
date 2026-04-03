
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📈 KIS 주식 종목포착 알림 봇
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
버전: v161
날짜: 2026-04-03
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[변경 이력]
- v161 (2026-04-03): 사용자 지시에 따라 기초 알림 구조만 남기고 기존 세부 조건/점수체계/시나리오/추적 로직을 제거한 단순 재구성 버전. KIS 시세·일봉 조회, 네이버 상승률 기반 후보 수집, 텔레그램 발송, 주기 스캔만 유지하고 아래 6개 조건만 남겼다: ① 당일 상승 종목 검색 ② 추가 상승 가능 시 포착 알림 ③ 일봉·주봉 하향 추세 제외 ④ 일반 종목만 검색 ⑤ 공시/재료 검색 시 하향 예상 종목 제외 ⑥ 가짜 상승 제외.
- v160.9 (2026-04-02): NXT/KRX 익일 오픈 평가 시각 분리 — 직전 정상본.
"""

from __future__ import annotations

import html
import json
import logging
import os
import re
import threading
import time
from collections import deque
from datetime import datetime, timedelta, time as dtime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

try:
    import schedule  # type: ignore
except ModuleNotFoundError:
    class _SimpleJob:
        def __init__(self, scheduler: "_SimpleSchedule", interval: int = 1):
            self.scheduler = scheduler
            self.interval = max(1, int(interval or 1))
            self.unit = "seconds"
            self.at_time = "00:00"
            self.job_func = None
            self.args = ()
            self.kwargs = {}
            self.next_run_ts = time.time()

        @property
        def seconds(self):
            self.unit = "seconds"
            return self

        @property
        def day(self):
            self.unit = "days"
            return self

        def at(self, hhmm: str):
            self.at_time = str(hhmm or "00:00")
            return self

        def do(self, func, *args, **kwargs):
            self.job_func = func
            self.args = args
            self.kwargs = kwargs
            self._schedule_next(first=True)
            self.scheduler.jobs.append(self)
            return self

        def _schedule_next(self, first: bool = False):
            now = _now_kst()
            if self.unit == "seconds":
                base = time.time()
                self.next_run_ts = base if first else base + self.interval
                return
            hour, minute = (self.at_time.split(":") + ["0"])[:2]
            target = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
            if target <= now:
                target += timedelta(days=self.interval)
            self.next_run_ts = target.timestamp()

        def run_if_due(self):
            if self.job_func is None:
                return
            if time.time() < self.next_run_ts:
                return
            self.job_func(*self.args, **self.kwargs)
            self._schedule_next(first=False)

    class _SimpleSchedule:
        def __init__(self):
            self.jobs = []

        def every(self, interval: int = 1):
            return _SimpleJob(self, interval)

        def run_pending(self):
            for job in list(self.jobs):
                job.run_if_due()

    schedule = _SimpleSchedule()

from bs4 import BeautifulSoup

# ============================================================
# 기본 환경
# ============================================================

_KST = ZoneInfo("Asia/Seoul")
VERSION = "v161"
BOT_NAME = "주식 종목포착 알림 봇"
TODAY_STR = "2026-04-03"

def _now_kst() -> datetime:
    return datetime.now(_KST)

def _load_dotenv(path: str = ".env") -> None:
    try:
        with open(path, encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    except FileNotFoundError:
        return

_load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", ".")).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

KIS_APP_KEY = os.getenv("KIS_APP_KEY", "").strip()
KIS_APP_SECRET = os.getenv("KIS_APP_SECRET", "").strip()
KIS_BASE_URL = os.getenv("KIS_BASE_URL", "https://openapi.koreainvestment.com:9443").strip().rstrip("/")
DART_API_KEY = os.getenv("DART_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "20") or "20")
ALERT_COOLDOWN_SEC = int(os.getenv("ALERT_COOLDOWN_SEC", "1800") or "1800")
RANK_TOP_N = int(os.getenv("RANK_TOP_N", "40") or "40")
MIN_ALERT_SCORE = int(os.getenv("MIN_ALERT_SCORE", "70") or "70")
MIN_PRICE = int(os.getenv("MIN_PRICE", "1200") or "1200")
SCAN_START = dtime.fromisoformat(os.getenv("SCAN_START", "08:00"))
SCAN_END = dtime.fromisoformat(os.getenv("SCAN_END", "20:00"))

KIS_REST_LIMIT_PER_SEC = max(1, int(os.getenv("KIS_REST_LIMIT_PER_SEC", "14") or "14"))
KIS_TOKEN_LIMIT_PER_SEC = max(1, int(os.getenv("KIS_TOKEN_LIMIT_PER_SEC", "1") or "1"))

STATE_ALERT_FILE = DATA_DIR / "simple_alert_state.json"
STATE_KIS_TOKEN_FILE = DATA_DIR / "kis_token_state.json"

LOG_LEVEL = str(os.getenv("STOCK_ALERT_LOG_LEVEL", "INFO") or "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("stock_alert")

_session = requests.Session()
_session.headers.update({"User-Agent": "Mozilla/5.0"})

_kis_rate_lock = threading.Lock()
_kis_rest_call_times: deque[float] = deque()
_kis_token_call_times: deque[float] = deque()
_access_token = ""
_token_expires_ts = 0.0

# ============================================================
# 공통 유틸
# ============================================================

def normalize_stock_code(value: Any) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    return digits[-6:] if len(digits) >= 6 else digits.zfill(6) if digits else ""

def _read_json(path: Path, default: Any) -> Any:
    try:
        if not path.exists():
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        log.warning("JSON 로드 실패 %s: %s", path.name, exc)
        return default

def _write_json(path: Path, obj: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def _is_weekend_or_holiday(now: datetime | None = None) -> bool:
    dt = now or _now_kst()
    return dt.weekday() >= 5

def _is_scan_time(now: datetime | None = None) -> bool:
    dt = now or _now_kst()
    if _is_weekend_or_holiday(dt):
        return False
    t = dt.time()
    return SCAN_START <= t <= SCAN_END

def _pct(a: float, b: float) -> float:
    if not b:
        return 0.0
    return (a / b - 1.0) * 100.0

def _ma(values: list[float], period: int) -> float | None:
    if len(values) < period or period <= 0:
        return None
    return sum(values[-period:]) / period

def _ma_shift(values: list[float], period: int, shift: int) -> float | None:
    if len(values) < period + shift or period <= 0 or shift < 0:
        return None
    end = len(values) - shift
    start = end - period
    if start < 0:
        return None
    return sum(values[start:end]) / period

def _safe_int(value: Any) -> int:
    try:
        return int(float(str(value).replace(",", "").strip()))
    except Exception:
        return 0

def _safe_float(value: Any) -> float:
    try:
        return float(str(value).replace(",", "").replace("%", "").strip())
    except Exception:
        return 0.0

# ============================================================
# 텔레그램
# ============================================================

def _tg_request(method: str, payload: dict[str, Any], timeout_sec: int = 12) -> dict[str, Any] | None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return None
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    try:
        res = requests.post(url, json=payload, timeout=(5, timeout_sec))
        res.raise_for_status()
        return res.json()
    except Exception as exc:
        log.warning("텔레그램 %s 실패: %s", method, exc)
        return None

def send(text: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.info("텔레그램 미설정 상태라 콘솔 로그로만 남깁니다.\n%s", text)
        return
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    _tg_request("sendMessage", payload)

# ============================================================
# KIS API
# ============================================================

def _wait_for_kis_slot(kind: str = "rest") -> None:
    limit = KIS_TOKEN_LIMIT_PER_SEC if kind == "token" else KIS_REST_LIMIT_PER_SEC
    dq = _kis_token_call_times if kind == "token" else _kis_rest_call_times
    window = 1.0
    while True:
        sleep_for = 0.0
        with _kis_rate_lock:
            now = time.monotonic()
            while dq and now - dq[0] >= window:
                dq.popleft()
            if len(dq) < limit:
                dq.append(now)
                return
            sleep_for = max(0.02, window - (now - dq[0]) + 0.005)
        time.sleep(sleep_for)

def _load_kis_token_cache() -> str:
    global _access_token, _token_expires_ts
    data = _read_json(STATE_KIS_TOKEN_FILE, {})
    token = str(data.get("access_token", "") or "").strip()
    expires_at = float(data.get("expires_at", 0) or 0)
    base_url = str(data.get("base_url", "") or "").strip().rstrip("/")
    if not token or expires_at <= time.time() + 300:
        return ""
    if base_url and base_url != KIS_BASE_URL:
        return ""
    _access_token = token
    _token_expires_ts = expires_at
    return token

def _save_kis_token_cache(token: str, expires_at: float) -> None:
    _write_json(
        STATE_KIS_TOKEN_FILE,
        {
            "access_token": token,
            "expires_at": expires_at,
            "base_url": KIS_BASE_URL,
            "saved_at": time.time(),
        },
    )

def get_token() -> str:
    global _access_token, _token_expires_ts
    if _access_token and time.time() < _token_expires_ts:
        return _access_token
    cached = _load_kis_token_cache()
    if cached:
        return cached
    if not KIS_APP_KEY or not KIS_APP_SECRET:
        raise RuntimeError("KIS_APP_KEY 또는 KIS_APP_SECRET 누락")
    _wait_for_kis_slot("token")
    resp = _session.post(
        f"{KIS_BASE_URL}/oauth2/tokenP",
        json={
            "grant_type": "client_credentials",
            "appkey": KIS_APP_KEY,
            "appsecret": KIS_APP_SECRET,
        },
        timeout=(5, 15),
    )
    resp.raise_for_status()
    payload = resp.json()
    token = str(payload["access_token"])
    expires_ts = time.time() + int(payload.get("expires_in", 86400)) - 300
    _access_token = token
    _token_expires_ts = expires_ts
    _save_kis_token_cache(token, expires_ts)
    log.info("✅ KIS 토큰 발급 완료")
    return token

def _safe_get(url: str, tr_id: str, params: dict[str, Any]) -> dict[str, Any]:
    token = get_token()
    headers = {
        "authorization": f"Bearer {token}",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET,
        "tr_id": tr_id,
        "custtype": "P",
    }
    _wait_for_kis_slot("rest")
    resp = _session.get(url, headers=headers, params=params, timeout=(5, 15))
    if resp.status_code == 401:
        # 토큰 만료 가능성
        _write_json(STATE_KIS_TOKEN_FILE, {})
        global _access_token, _token_expires_ts
        _access_token = ""
        _token_expires_ts = 0.0
        token = get_token()
        headers["authorization"] = f"Bearer {token}"
        _wait_for_kis_slot("rest")
        resp = _session.get(url, headers=headers, params=params, timeout=(5, 15))
    resp.raise_for_status()
    return resp.json()

def get_stock_price(code: str) -> dict[str, Any]:
    code = normalize_stock_code(code)
    if not code:
        return {}
    data = _safe_get(
        f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price",
        "FHKST01010100",
        {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code},
    )
    out = data.get("output", {}) if isinstance(data, dict) else {}
    price = _safe_int(out.get("stck_prpr"))
    if price <= 0:
        return {}
    return {
        "code": code,
        "name": str(out.get("hts_kor_isnm", "") or code),
        "price": price,
        "change_rate": _safe_float(out.get("prdy_ctrt")),
        "today_vol": _safe_int(out.get("acml_vol")),
        "open": _safe_int(out.get("stck_oprc")),
        "high": _safe_int(out.get("stck_hgpr")),
        "low": _safe_int(out.get("stck_lwpr")),
        "prev_close": _safe_int(out.get("stck_sdpr")),
        "ask_qty": _safe_int(out.get("askp_rsqn1")),
        "bid_qty": _safe_int(out.get("bidp_rsqn1")),
        "market_cap_100m": _safe_int(out.get("hts_avls")),
    }

def get_daily_data(code: str, days: int = 160) -> list[dict[str, Any]]:
    code = normalize_stock_code(code)
    if not code:
        return []
    end = _now_kst().strftime("%Y%m%d")
    start = (_now_kst() - timedelta(days=days + 40)).strftime("%Y%m%d")
    data = _safe_get(
        f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
        "FHKST03010100",
        {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": code,
            "FID_INPUT_DATE_1": start,
            "FID_INPUT_DATE_2": end,
            "FID_PERIOD_DIV_CODE": "D",
            "FID_ORG_ADJ_PRC": "0",
        },
    )
    items = []
    for row in data.get("output2", []) if isinstance(data, dict) else []:
        date = str(row.get("stck_bsop_date", "") or "")
        if not date:
            continue
        items.append(
            {
                "date": date,
                "open": _safe_int(row.get("stck_oprc")),
                "high": _safe_int(row.get("stck_hgpr")),
                "low": _safe_int(row.get("stck_lwpr")),
                "close": _safe_int(row.get("stck_clpr")),
                "vol": _safe_int(row.get("acml_vol")),
            }
        )
    items.sort(key=lambda x: x["date"])
    return items[-days:] if days > 0 else items

# ============================================================
# 후보 수집
# ============================================================

GENERAL_STOCK_EXCLUDE_PATTERNS = [
    re.compile(p)
    for p in [
        r"스팩",
        r"SPAC",
        r"리츠",
        r"REIT",
        r"ETF",
        r"ETN",
        r"인버스",
        r"레버리지",
        r"\b2X\b",
        r"\b3X\b",
        r"우B?$",
        r"우C$",
        r"1우$",
        r"2우B$",
        r"전환우",
    ]
]
GENERAL_STOCK_PREFIX_BLOCK = (
    "KODEX",
    "TIGER",
    "KOSEF",
    "KBSTAR",
    "HANARO",
    "ARIRANG",
    "SOL",
    "ACE",
    "PLUS",
    "TREX",
    "RISE",
    "TIMEFOLIO",
)

def is_general_stock_name(name: str) -> bool:
    clean = str(name or "").strip()
    if not clean:
        return False
    if clean.upper().startswith(GENERAL_STOCK_PREFIX_BLOCK):
        return False
    return not any(p.search(clean) for p in GENERAL_STOCK_EXCLUDE_PATTERNS)

def fetch_naver_rise_rank(top_n: int = 40) -> list[dict[str, Any]]:
    url = "https://finance.naver.com/sise/sise_rise.naver"
    merged: list[dict[str, Any]] = []
    for market_label, sosok in [("KOSPI", "0"), ("KOSDAQ", "1")]:
        try:
            resp = requests.get(
                url,
                params={"sosok": sosok},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=(5, 10),
            )
            resp.raise_for_status()
            apparent = (resp.apparent_encoding or "").strip()
            if apparent:
                resp.encoding = apparent
            elif not (resp.encoding or "").strip():
                resp.encoding = "euc-kr"
            soup = BeautifulSoup(resp.text, "html.parser")
            rows = soup.select("table.type_2 tr, table.type_5 tr")
            local: list[dict[str, Any]] = []
            for row in rows:
                tds = row.find_all("td")
                if len(tds) < 4:
                    continue
                a_tag = row.find("a", href=lambda x: x and "code=" in str(x))
                if not a_tag:
                    continue
                match = re.search(r"code=(\d{6})", a_tag.get("href", ""))
                if not match:
                    continue
                code = match.group(1)
                name = a_tag.get_text(strip=True)
                rate = None
                for td in tds:
                    txt = td.get_text(strip=True).replace(",", "").replace("+", "").replace("%", "")
                    try:
                        val = float(txt)
                    except Exception:
                        continue
                    if -30 < val < 30 and val != 0:
                        rate = val
                        break
                if rate is None:
                    continue
                local.append(
                    {
                        "code": code,
                        "name": name,
                        "change_rate": rate,
                        "market_detail": market_label,
                        "source": "naver_rise",
                    }
                )
                if len(local) >= top_n:
                    break
            merged.extend(local)
        except Exception as exc:
            log.warning("네이버 %s 상승률 스크래핑 실패: %s", market_label, exc)
    dedup: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in sorted(merged, key=lambda x: float(x.get("change_rate", 0) or 0), reverse=True):
        code = str(item.get("code", "") or "")
        if code and code not in seen:
            seen.add(code)
            dedup.append(item)
    return dedup[:top_n]

# ============================================================
# 재료/공시 확인
# ============================================================

NEGATIVE_MATERIAL_KEYWORDS = [
    "유상증자",
    "감자",
    "관리종목",
    "상장폐지",
    "거래정지",
    "의견거절",
    "한정",
    "부도",
    "회생",
    "횡령",
    "배임",
    "소송",
    "불성실",
    "적자",
    "실적악화",
    "전환사채",
    "신주인수권부사채",
    "CB",
    "BW",
    "감사의견",
]
POSITIVE_MATERIAL_KEYWORDS = [
    "수주",
    "공급계약",
    "계약체결",
    "승인",
    "허가",
    "특허",
    "호실적",
    "흑자전환",
    "실적개선",
    "양산",
    "선정",
    "투자유치",
    "MOU",
    "국책",
    "정부",
]

def fetch_news_for_stock(code: str) -> list[str]:
    code = normalize_stock_code(code)
    if not code:
        return []
    headlines: list[str] = []
    try:
        url = f"https://finance.naver.com/item/news_news.naver?code={code}&page=1&sm=title_entity_id.basic"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=(5, 8))
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for row in soup.select("table.type5 tr")[:8]:
            title_el = row.select_one("td.title a")
            if not title_el:
                continue
            title = html.unescape(title_el.get_text(" ", strip=True))
            if title and title not in headlines:
                headlines.append(title)
            if len(headlines) >= 5:
                break
    except Exception as exc:
        log.warning("뉴스 조회 실패 %s: %s", code, exc)
    return headlines

def fetch_dart_titles(code: str, days_back: int = 5) -> list[str]:
    if not DART_API_KEY:
        return []
    code = normalize_stock_code(code)
    if not code:
        return []
    try:
        end = _now_kst().strftime("%Y%m%d")
        bgn = (_now_kst() - timedelta(days=days_back)).strftime("%Y%m%d")
        resp = requests.get(
            "https://opendart.fss.or.kr/api/list.json",
            params={
                "crtfc_key": DART_API_KEY,
                "bgn_de": bgn,
                "end_de": end,
                "stock_code": code,
                "page_count": 20,
            },
            timeout=(5, 8),
        )
        resp.raise_for_status()
        titles: list[str] = []
        for item in resp.json().get("list", []):
            title = str(item.get("report_nm", "") or "").strip()
            if title and title not in titles:
                titles.append(title)
        return titles[:10]
    except Exception as exc:
        log.warning("DART 조회 실패 %s: %s", code, exc)
        return []

def analyze_material_bias(code: str) -> dict[str, Any]:
    news_titles = fetch_news_for_stock(code)
    dart_titles = fetch_dart_titles(code)
    all_titles = [*dart_titles, *news_titles]
    negative_hits: list[str] = []
    positive_hits: list[str] = []
    joined = " ".join(all_titles)
    for kw in NEGATIVE_MATERIAL_KEYWORDS:
        if kw in joined:
            negative_hits.append(kw)
    for kw in POSITIVE_MATERIAL_KEYWORDS:
        if kw in joined:
            positive_hits.append(kw)
    return {
        "block": bool(negative_hits),
        "negative_hits": list(dict.fromkeys(negative_hits))[:5],
        "positive_hits": list(dict.fromkeys(positive_hits))[:5],
        "headline": all_titles[0] if all_titles else "",
    }

# ============================================================
# 추세/가짜상승/추가상승 평가
# ============================================================

def build_weekly_bars(daily: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[int, int], dict[str, Any]] = {}
    ordered_keys: list[tuple[int, int]] = []
    for row in daily:
        try:
            dt = datetime.strptime(row["date"], "%Y%m%d")
        except Exception:
            continue
        key = (dt.isocalendar().year, dt.isocalendar().week)
        if key not in buckets:
            buckets[key] = {
                "date": row["date"],
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "vol": row["vol"],
            }
            ordered_keys.append(key)
        else:
            bar = buckets[key]
            bar["high"] = max(bar["high"], row["high"])
            bar["low"] = min(bar["low"], row["low"])
            bar["close"] = row["close"]
            bar["vol"] += row["vol"]
    return [buckets[k] for k in ordered_keys]

def compute_volume_ratio(today_vol: int, daily: list[dict[str, Any]]) -> float:
    vols = [int(x.get("vol", 0) or 0) for x in daily[:-1] if int(x.get("vol", 0) or 0) > 0]
    base = sum(vols[-20:]) / min(len(vols[-20:]), 20) if vols else 0
    if base <= 0:
        return 0.0
    return round(today_vol / base, 2)

def evaluate_trend(daily: list[dict[str, Any]]) -> dict[str, Any]:
    closes = [float(x["close"]) for x in daily if x.get("close")]
    if len(closes) < 70:
        return {"pass": False, "reason": "일봉 데이터 부족", "daily_down": True, "weekly_down": True}

    ma20 = _ma(closes, 20)
    ma60 = _ma(closes, 60)
    ma20_prev = _ma_shift(closes, 20, 5)
    ma60_prev = _ma_shift(closes, 60, 5)
    last_close = closes[-1]

    daily_down = False
    if ma20 is None or ma60 is None:
        daily_down = True
    elif (last_close < ma20 and ma20 < ma60) or (ma20_prev is not None and ma20 < ma20_prev) or (ma60_prev is not None and ma60 < ma60_prev):
        daily_down = True

    weekly = build_weekly_bars(daily)
    wcloses = [float(x["close"]) for x in weekly if x.get("close")]
    if len(wcloses) < 12:
        return {"pass": False, "reason": "주봉 데이터 부족", "daily_down": daily_down, "weekly_down": True}

    ma5w = _ma(wcloses, 5)
    ma10w = _ma(wcloses, 10)
    ma5w_prev = _ma_shift(wcloses, 5, 2)
    ma10w_prev = _ma_shift(wcloses, 10, 2)
    last_week = wcloses[-1]

    weekly_down = False
    if ma5w is None or ma10w is None:
        weekly_down = True
    elif (last_week < ma5w and ma5w < ma10w) or (ma5w_prev is not None and ma5w < ma5w_prev) or (ma10w_prev is not None and ma10w < ma10w_prev):
        weekly_down = True

    return {
        "pass": not (daily_down or weekly_down),
        "reason": "" if not (daily_down or weekly_down) else "일봉/주봉 하향 추세",
        "daily_down": daily_down,
        "weekly_down": weekly_down,
        "ma20": round(ma20 or 0, 1),
        "ma60": round(ma60 or 0, 1),
        "ma5w": round(ma5w or 0, 1),
        "ma10w": round(ma10w or 0, 1),
        "weekly": weekly,
    }

def evaluate_fake_surge(quote: dict[str, Any], volume_ratio: float) -> dict[str, Any]:
    price = int(quote.get("price", 0) or 0)
    high = int(quote.get("high", 0) or 0)
    low = int(quote.get("low", 0) or 0)
    open_price = int(quote.get("open", 0) or 0)
    ask_qty = int(quote.get("ask_qty", 0) or 0)
    bid_qty = int(quote.get("bid_qty", 0) or 0)

    if price <= 0 or high <= 0 or low <= 0:
        return {"pass": False, "reason": "당일 가격 정보 부족"}

    day_range = max(1, high - low)
    close_pos = (price - low) / day_range
    upper_wick_ratio = max(0.0, (high - price) / day_range)
    high_gap_pct = (high - price) / high * 100.0 if high else 0.0
    bid_ask_ratio = bid_qty / max(ask_qty, 1) if (bid_qty or ask_qty) else 1.0

    reason = ""
    passed = True
    if price < open_price:
        passed = False
        reason = "시가 이탈"
    elif close_pos < 0.55:
        passed = False
        reason = "고가권 유지 실패"
    elif upper_wick_ratio > 0.45:
        passed = False
        reason = "윗꼬리 과다"
    elif high_gap_pct > 3.5:
        passed = False
        reason = "고가 대비 밀림"
    elif volume_ratio < 1.8:
        passed = False
        reason = "거래량 부족"
    elif bid_qty and ask_qty and bid_ask_ratio < 0.6:
        passed = False
        reason = "매수호가 약세"

    return {
        "pass": passed,
        "reason": reason,
        "close_pos": round(close_pos, 2),
        "upper_wick_ratio": round(upper_wick_ratio, 2),
        "high_gap_pct": round(high_gap_pct, 2),
        "bid_ask_ratio": round(bid_ask_ratio, 2),
    }

def score_candidate(quote: dict[str, Any], daily: list[dict[str, Any]], trend: dict[str, Any], material: dict[str, Any], fake: dict[str, Any], volume_ratio: float) -> dict[str, Any]:
    score = 0
    reasons: list[str] = []
    price = int(quote["price"])
    change_rate = float(quote["change_rate"])
    open_price = int(quote["open"])
    prev20_high = max((row["high"] for row in daily[-21:-1]), default=0)
    prev60_high = max((row["high"] for row in daily[-61:-1]), default=0)

    if 3.0 <= change_rate <= 18.0:
        score += 18
        reasons.append(f"당일 상승률 {change_rate:+.1f}%")
    elif 1.5 <= change_rate < 3.0:
        score += 8
        reasons.append("상승 시작 구간")
    elif 18.0 < change_rate <= 25.0:
        score += 10
        reasons.append("강한 상승 유지")
    else:
        reasons.append("상승률 구간 비선호")

    if volume_ratio >= 4.0:
        score += 18
        reasons.append(f"거래량 {volume_ratio:.1f}배")
    elif volume_ratio >= 2.5:
        score += 12
        reasons.append(f"거래량 {volume_ratio:.1f}배")
    elif volume_ratio >= 1.8:
        score += 6
        reasons.append(f"거래량 {volume_ratio:.1f}배")

    if price >= open_price > 0:
        score += 10
        reasons.append("시가 위 유지")

    if fake["close_pos"] >= 0.8:
        score += 16
        reasons.append("고가권 버팀 강함")
    elif fake["close_pos"] >= 0.65:
        score += 10
        reasons.append("고가권 유지")

    if fake["high_gap_pct"] <= 1.0:
        score += 12
    elif fake["high_gap_pct"] <= 2.0:
        score += 6

    if price >= prev20_high > 0:
        score += 8
        reasons.append("20일 고점 돌파")
    if price >= prev60_high > 0:
        score += 8
        reasons.append("60일 고점 돌파")

    if not trend["daily_down"]:
        score += 8
    if not trend["weekly_down"]:
        score += 8

    if material["positive_hits"]:
        score += 6
        reasons.append("재료/공시 긍정 키워드")

    if fake["bid_ask_ratio"] >= 1.0:
        score += 4

    return {"score": score, "reasons": reasons[:6]}

def evaluate_candidate(seed: dict[str, Any]) -> dict[str, Any] | None:
    code = normalize_stock_code(seed.get("code"))
    name = str(seed.get("name", "") or code)
    if not code or not name:
        return None
    if not is_general_stock_name(name):
        return None

    try:
        quote = get_stock_price(code)
    except Exception as exc:
        log.warning("시세 조회 실패 %s %s: %s", code, name, exc)
        return None
    if not quote or int(quote.get("price", 0) or 0) < MIN_PRICE:
        return None

    try:
        daily = get_daily_data(code, 160)
    except Exception as exc:
        log.warning("일봉 조회 실패 %s %s: %s", code, name, exc)
        return None
    if len(daily) < 70:
        return None

    volume_ratio = compute_volume_ratio(int(quote.get("today_vol", 0) or 0), daily)
    quote["volume_ratio"] = volume_ratio

    if float(quote.get("change_rate", 0.0) or 0.0) <= 0:
        return None

    trend = evaluate_trend(daily)
    if not trend["pass"]:
        return None

    fake = evaluate_fake_surge(quote, volume_ratio)
    if not fake["pass"]:
        return None

    material = analyze_material_bias(code)
    if material["block"]:
        return None

    scored = score_candidate(quote, daily, trend, material, fake, volume_ratio)
    score = int(scored["score"])
    if score < MIN_ALERT_SCORE:
        return None

    return {
        "code": code,
        "name": quote.get("name") or name,
        "price": int(quote["price"]),
        "change_rate": float(quote["change_rate"]),
        "volume_ratio": float(volume_ratio),
        "score": score,
        "quote": quote,
        "trend": trend,
        "fake": fake,
        "material": material,
        "reasons": scored["reasons"],
        "market_detail": str(seed.get("market_detail", "") or ""),
    }

# ============================================================
# 알림 상태
# ============================================================

def _load_alert_state() -> dict[str, Any]:
    data = _read_json(STATE_ALERT_FILE, {})
    return data if isinstance(data, dict) else {}

def _save_alert_state(state: dict[str, Any]) -> None:
    _write_json(STATE_ALERT_FILE, state)

def should_send_alert(code: str) -> bool:
    state = _load_alert_state()
    rec = state.get(code, {})
    last_ts = float(rec.get("ts", 0) or 0)
    return time.time() - last_ts >= ALERT_COOLDOWN_SEC

def mark_alert_sent(code: str, payload: dict[str, Any]) -> None:
    state = _load_alert_state()
    state[code] = {
        "ts": time.time(),
        "date": _now_kst().strftime("%Y%m%d"),
        "score": int(payload.get("score", 0) or 0),
        "change_rate": float(payload.get("change_rate", 0.0) or 0.0),
    }
    _save_alert_state(state)

def reset_daily_alert_state() -> None:
    today = _now_kst().strftime("%Y%m%d")
    state = _load_alert_state()
    new_state = {k: v for k, v in state.items() if str(v.get("date", "")) == today}
    _save_alert_state(new_state)
    log.info("🧹 일일 알림 상태 정리 완료")

# ============================================================
# 메시지 구성
# ============================================================

def format_alert(candidate: dict[str, Any]) -> str:
    quote = candidate["quote"]
    trend = candidate["trend"]
    fake = candidate["fake"]
    material = candidate["material"]
    reasons = candidate["reasons"]

    material_line = "없음"
    if material["positive_hits"]:
        material_line = ", ".join(material["positive_hits"][:3])
    elif material["headline"]:
        material_line = material["headline"][:40]

    reason_lines = "\n".join(f"• {r}" for r in reasons[:5])
    return (
        f"📈 <b>[추가상승 후보 포착]</b>\n"
        f"🕐 {_now_kst().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🟡 <b>{candidate['code']} {html.escape(candidate['name'])}</b>\n"
        f"💵 현재가 <b>{candidate['price']:,}원</b> / {candidate['change_rate']:+.1f}%\n"
        f"📊 거래량 {candidate['volume_ratio']:.1f}배 · 점수 {candidate['score']}점\n"
        f"🧭 일봉 MA20 {trend['ma20']:.1f} / MA60 {trend['ma60']:.1f}\n"
        f"🗓️ 주봉 MA5 {trend['ma5w']:.1f} / MA10 {trend['ma10w']:.1f}\n"
        f"🪤 가짜상승 필터 통과 · 고가대비 {fake['high_gap_pct']:.1f}% 이격\n"
        f"🧪 재료/공시 체크: {html.escape(material_line)}\n"
        f"✅ 포착 근거\n{reason_lines}"
    )

# ============================================================
# 실행 루프
# ============================================================

def run_scan() -> None:
    if not _is_scan_time():
        return

    try:
        seeds = fetch_naver_rise_rank(RANK_TOP_N)
    except Exception as exc:
        log.warning("후보 수집 실패: %s", exc)
        return

    if not seeds:
        log.info("상승률 후보 없음")
        return

    results: list[dict[str, Any]] = []
    for seed in seeds:
        candidate = evaluate_candidate(seed)
        if candidate:
            results.append(candidate)

    results.sort(key=lambda x: (int(x["score"]), float(x["change_rate"])), reverse=True)
    if not results:
        log.info("조건 통과 후보 없음")
        return

    sent_count = 0
    for candidate in results[:5]:
        code = candidate["code"]
        if not should_send_alert(code):
            continue
        send(format_alert(candidate))
        mark_alert_sent(code, candidate)
        sent_count += 1

    log.info("스캔 완료: 후보 %d건 / 발송 %d건", len(results), sent_count)

def send_startup_banner() -> None:
    text = (
        f"🤖 <b>{BOT_NAME} ON ({VERSION})</b>\n"
        f"📅 {TODAY_STR}\n\n"
        f"✅ 유지한 구조\n"
        f"• KIS 시세/일봉 조회\n"
        f"• 네이버 상승률 후보 수집\n"
        f"• 텔레그램 즉시 발송\n"
        f"• 주기 스캔 루프\n\n"
        f"🎯 현재 필터(6개)\n"
        f"1. 당일 상승 종목\n"
        f"2. 추가 상승 가능 시 알림\n"
        f"3. 일봉·주봉 하향 추세 제외\n"
        f"4. 일반 종목만 검색\n"
        f"5. 공시/재료 하방 예상 종목 제외\n"
        f"6. 가짜 상승 제외"
    )
    send(text)

def main() -> None:
    log.info("=== %s %s 시작 ===", BOT_NAME, VERSION)
    if not KIS_APP_KEY or not KIS_APP_SECRET:
        log.warning("KIS 환경변수가 비어 있습니다.")
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.warning("텔레그램 환경변수가 비어 있습니다. 콘솔 로그만 남깁니다.")

    send_startup_banner()
    reset_daily_alert_state()

    schedule.every(SCAN_INTERVAL).seconds.do(run_scan)
    schedule.every().day.at("08:00").do(reset_daily_alert_state)

    # 시작 직후 1회 수행
    run_scan()

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
