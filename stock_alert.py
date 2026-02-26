#!/usr/bin/env python3
"""
📈 KIS 주식 급등 알림 봇 v13
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
① 조기 포착 (상한가 전 선진입)
② 급등/상한가 감지 (외국인·기관 동반 체크)
③ 섹터 모멘텀 (동반 상승 확인 + 가산점)
④ 뉴스 → 실제 주가 상승 확인 후 알림 (2분, UA 랜덤)
⑤ DART 공시 → 실제 주가 확인 + 섹터 반응 (3분)
⑥ 눌림목 진입 포착 + 이월 (최대 3일)
⑦ EARLY_DETECT 자동 저장 → tracker.py 연동
⑧ ATR 기반 동적 손절·목표가
⑨ 거래량 비율 정확도 개선 (평균 거래량 대비)
⑩ 시간대별 필터 (장 초반·마감 직전 엄격 적용)
⑪ 전일 상한가 종목 가산점
⑫ 섹터 캐시 장 시작 시 초기화
⑬ 텔레그램 명령어 (/status /list /stop /resume)
⑭ 뉴스 다중 소스 (네이버·한국경제·연합뉴스)
⑮ tracker.py 피드백 반영 (EARLY_DETECT 조건 자동 조정)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os, requests, time, schedule, json, random, threading
from datetime import datetime, time as dtime, timedelta
from bs4 import BeautifulSoup
from collections import deque

# ============================================================
# ⚙️ 환경변수
# ============================================================
KIS_APP_KEY        = os.environ.get("KIS_APP_KEY", "")
KIS_APP_SECRET     = os.environ.get("KIS_APP_SECRET", "")
KIS_ACCOUNT_NO     = os.environ.get("KIS_ACCOUNT_NO", "")
KIS_BASE_URL       = "https://openapi.koreainvestment.com:9443"
DART_API_KEY       = os.environ.get("DART_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

# ============================================================
# 📊 스캔 조건
# ============================================================
VOLUME_SURGE_RATIO    = 5.0
PRICE_SURGE_MIN       = 5.0
UPPER_LIMIT_THRESHOLD = 25.0
EARLY_PRICE_MIN       = 10.0
EARLY_VOLUME_MIN      = 10.0
EARLY_HOGA_RATIO      = 3.0
EARLY_CONFIRM_COUNT   = 2
SCAN_INTERVAL         = 60       # 주식 스캔 1분
ALERT_COOLDOWN        = 1800     # 같은 종목 30분 재알림 방지
NEWS_SCAN_INTERVAL    = 120      # 뉴스 2분
DART_INTERVAL         = 180      # DART 3분
MARKET_OPEN           = "09:00"
MARKET_CLOSE          = "15:30"
ENTRY_PULLBACK_RATIO  = 0.4
PULLBACK_CHECK_AFTER  = 30
PULLBACK_MIN          = 25.0
PULLBACK_MAX          = 55.0
MAX_CARRY_DAYS        = 3
CARRY_FILE            = "carry_stocks.json"
EARLY_LOG_FILE        = "early_detect_log.json"
ATR_PERIOD            = 5        # ATR 계산 기간 (일)
ATR_STOP_MULT         = 1.5      # 손절: ATR × 1.5
ATR_TARGET_MULT       = 3.0      # 목표: ATR × 3.0
STRICT_OPEN_MINUTES   = 10       # 장 시작 후 엄격 적용 시간 (분)
STRICT_CLOSE_MINUTES  = 10       # 장 마감 전 엄격 적용 시간 (분)

# ============================================================
# 🗞️ 테마 섹터 맵
# ============================================================
THEME_MAP = {
    "밸류업":   {"desc":"밸류업 프로그램","sectors":["증권","은행","보험","금융"],
                 "stocks":[("001510","SK증권"),("001290","상상인증권"),("005940","NH투자증권"),
                           ("016360","삼성증권"),("006800","미래에셋증권"),("039490","키움증권")]},
    "AI반도체": {"desc":"AI/반도체 테마","sectors":["반도체","AI","HBM"],
                 "stocks":[("000660","SK하이닉스"),("005930","삼성전자"),("042700","한미반도체"),
                           ("403870","HPSP"),("357780","솔브레인")]},
    "2차전지":  {"desc":"2차전지/배터리 테마","sectors":["배터리","양극재","전해질"],
                 "stocks":[("086520","에코프로"),("247540","에코프로비엠"),("006400","삼성SDI"),
                           ("051910","LG화학"),("373220","LG에너지솔루션")]},
    "바이오":   {"desc":"바이오/제약 테마","sectors":["바이오","임상","FDA","신약"],
                 "stocks":[("207940","삼성바이오로직스"),("068270","셀트리온"),
                           ("196170","알테오젠"),("009420","한올바이오파마")]},
    "방산":     {"desc":"방위산업 테마","sectors":["방산","방위","무기"],
                 "stocks":[("012450","한화에어로스페이스"),("047810","한국항공우주"),
                           ("064350","현대로템"),("042660","한화오션")]},
    "원전":     {"desc":"원자력/원전 테마","sectors":["원전","원자력","SMR"],
                 "stocks":[("017800","현대엘리베이터"),("071970","STX중공업"),("298040","효성중공업")]},
    "수주":     {"desc":"대규모 수주/계약","sectors":["조선","건설","방산"],
                 "stocks":[("042660","한화오션"),("009540","HD한국조선해양"),("010140","삼성중공업")]},
}

# DART 키워드
DART_KEYWORDS = {
    "매우강함": ["수주","계약체결","공급계약","수출계약","임상","FDA","허가","신약","인수","합병","흑자전환"],
    "강함":     ["특허","기술이전","MOU","업무협약","증설","공장","자사주","배당"],
    "보통":     ["신규사업","진출","개발완료","수상","선정"],
}
DART_URGENT_KEYWORDS = [
    "유상증자","무상증자","주식분할","주식병합",
    "거래정지","상장폐지","관리종목",
    "횡령","배임","분식","조사",
    "최대주주변경","대표이사변경",
    "감사의견","영업정지","파산","워크아웃","회생",
    "공개매수","지분취득","자기주식취득",
]
DART_RISK_KEYWORDS = ["거래정지","상장폐지","횡령","배임","파산","워크아웃",
                      "감사의견","영업정지","회생","관리종목","분식","조사"]

# UA 풀 (네이버 크롤링 차단 방지)
_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

def _random_ua() -> dict:
    return {
        "User-Agent":      random.choice(_UA_POOL),
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer":         "https://finance.naver.com/",
    }

# ============================================================
# 🌐 상태 변수
# ============================================================
_access_token     = None
_token_expires    = 0
_session          = requests.Session()
_session.headers.update({"User-Agent": "Mozilla/5.0"})
_alert_history    = {}   # code → last_alert_time
_detected_stocks  = {}   # code → info (눌림목 추적용)
_pullback_history = {}   # code → last_pullback_time
_news_alert_history = {} # theme_key → last_alert_time
_early_cache      = {}   # code → {count, last_price, last_time}
_sector_cache     = {}   # code → {sector, stocks, ts}
_dart_seen_ids    = set()
_bot_paused       = False  # /stop 명령어로 일시정지

# ⑮ tracker 피드백: EARLY_DETECT 성공률 기반 조건 자동 조정
_early_feedback   = {"total": 0, "success": 0}  # success = 실제 수익 발생
_early_price_min_dynamic  = EARLY_PRICE_MIN
_early_volume_min_dynamic = EARLY_VOLUME_MIN

# ============================================================
# 🕐 시간 유틸
# ============================================================
def now_time() -> dtime:
    return datetime.now().time()

def is_market_open() -> bool:
    n = now_time()
    return dtime(9, 0) <= n <= dtime(15, 30)

def minutes_since(dt: datetime) -> int:
    return int((datetime.now() - dt).total_seconds() // 60)

def minutes_to_close() -> int:
    now = datetime.now()
    close = now.replace(hour=15, minute=30, second=0)
    return max(0, int((close - now).total_seconds() // 60))

def is_strict_time() -> bool:
    """장 시작 직후·마감 직전 → 조건 엄격 적용 구간"""
    n = now_time()
    open_end   = (datetime.now().replace(hour=9, minute=0) + timedelta(minutes=STRICT_OPEN_MINUTES)).time()
    close_start = (datetime.now().replace(hour=15, minute=30) - timedelta(minutes=STRICT_CLOSE_MINUTES)).time()
    return n <= open_end or n >= close_start

# ============================================================
# 🔐 KIS API
# ============================================================
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
            data          = resp.json()
            _access_token = data["access_token"]
            _token_expires = time.time() + int(data.get("expires_in", 86400)) - 300
            print(f"✅ KIS 토큰 발급 ({datetime.now().strftime('%H:%M:%S')})")
            return _access_token
        except Exception as e:
            print(f"⚠️ 토큰 발급 실패 ({attempt+1}/{retry}): {e}")
            time.sleep(5 * (attempt + 1))
    raise Exception("❌ KIS 토큰 발급 최종 실패")

def _headers(tr_id: str) -> dict:
    return {
        "Content-Type":  "application/json; charset=utf-8",
        "Authorization": f"Bearer {get_token()}",
        "appkey":        KIS_APP_KEY,
        "appsecret":     KIS_APP_SECRET,
        "tr_id":         tr_id,
        "custtype":      "P",
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
        print(f"⚠️ API 오류 ({tr_id}): {e}")
        return {}

# ============================================================
# ⑨ 거래량 비율 정확도 개선 (평균 거래량 대비 실제 배수)
# ============================================================
_avg_volume_cache = {}  # code → {avg_vol, ts}

def get_avg_volume(code: str) -> int:
    """최근 5일 평균 거래량 조회 (캐시 1시간)"""
    cached = _avg_volume_cache.get(code)
    if cached and time.time() - cached["ts"] < 3600:
        return cached["avg_vol"]
    try:
        end   = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d")
        url   = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        params = {"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":code,
                  "FID_INPUT_DATE_1":start,"FID_INPUT_DATE_2":end,
                  "FID_PERIOD_DIV_CODE":"D","FID_ORG_ADJ_PRC":"0"}
        resp  = _session.get(url, headers=_headers("FHKST03010100"), params=params, timeout=15)
        items = resp.json().get("output2", []) if resp.status_code == 200 else []
        vols  = [int(i.get("acml_vol", 0)) for i in items if i.get("acml_vol")]
        avg   = int(sum(vols[-5:]) / len(vols[-5:])) if len(vols) >= 3 else 0
        _avg_volume_cache[code] = {"avg_vol": avg, "ts": time.time()}
        return avg
    except:
        return 0

def get_real_volume_ratio(code: str, today_vol: int) -> float:
    """실제 거래량 배수 = 오늘 거래량 / 5일 평균"""
    avg = get_avg_volume(code)
    if not avg or not today_vol:
        return 0.0
    return round(today_vol / avg, 1)

# ============================================================
# 📈 주가 조회
# ============================================================
def get_stock_price(code: str) -> dict:
    url    = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
    data   = _safe_get(url, "FHKST01010100", params)
    o      = data.get("output", {})
    price  = int(o.get("stck_prpr", 0))
    if not price:
        return {}
    today_vol = int(o.get("acml_vol", 0))
    vol_ratio = get_real_volume_ratio(code, today_vol)  # ⑨ 정확한 거래량 배수
    return {
        "code":        code,
        "name":        o.get("hts_kor_isnm", ""),
        "price":       price,
        "change_rate": float(o.get("prdy_ctrt", 0)),
        "volume_ratio": vol_ratio,
        "today_vol":   today_vol,
        "high":        int(o.get("stck_hgpr", 0)),
        "ask_qty":     int(o.get("askp_rsqn1", 0)),
        "bid_qty":     int(o.get("bidp_rsqn1", 0)),
        "prev_close":  int(o.get("stck_sdpr", 0)),
        "bstp_code":   o.get("bstp_cls_code", ""),   # 업종 코드
    }

def get_upper_limit_stocks() -> list:
    url    = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/chgrate-pcls-100"
    params = {
        "FID_COND_MRKT_DIV_CODE":"J","FID_COND_SCR_DIV_CODE":"20170","FID_INPUT_ISCD":"0000",
        "FID_RANK_SORT_CLS_CODE":"0","FID_INPUT_CNT_1":"30","FID_PRC_CLS_CODE":"0",
        "FID_INPUT_PRICE_1":"1000","FID_INPUT_PRICE_2":"","FID_VOL_CNT":"100000",
        "FID_TRGT_CLS_CODE":"0","FID_TRGT_EXLS_CLS_CODE":"0","FID_DIV_CLS_CODE":"0",
        "FID_RSFL_RATE1":"5","FID_RSFL_RATE2":"",
    }
    data  = _safe_get(url, "FHPST01700000", params)
    return [{"code":i.get("mksc_shrn_iscd",""),"name":i.get("hts_kor_isnm",""),
             "price":int(i.get("stck_prpr",0)),"change_rate":float(i.get("prdy_ctrt",0)),
             "volume_ratio":float(i.get("vol_inrt",0) or 0)}
            for i in data.get("output",[]) if i.get("mksc_shrn_iscd")]

def get_volume_surge_stocks() -> list:
    url    = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/volume-rank"
    params = {
        "FID_COND_MRKT_DIV_CODE":"J","FID_COND_SCR_DIV_CODE":"20171","FID_INPUT_ISCD":"0000",
        "FID_DIV_CLS_CODE":"0","FID_BLNG_CLS_CODE":"0","FID_TRGT_CLS_CODE":"111111111",
        "FID_TRGT_EXLS_CLS_CODE":"000000","FID_INPUT_PRICE_1":"1000",
        "FID_INPUT_PRICE_2":"","FID_VOL_CNT":"30","FID_INPUT_DATE_1":"",
    }
    data  = _safe_get(url, "FHPST01710000", params)
    return [{"code":i.get("mksc_shrn_iscd",""),"name":i.get("hts_kor_isnm",""),
             "price":int(i.get("stck_prpr",0)),"change_rate":float(i.get("prdy_ctrt",0)),
             "volume_ratio":float(i.get("vol_inrt",0) or 0)}
            for i in data.get("output",[]) if i.get("mksc_shrn_iscd")]

def get_investor_trend(code: str) -> dict:
    url    = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-investor"
    params = {"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":code}
    data   = _safe_get(url, "FHKST01010900", params)
    output = data.get("output", [])
    if not output:
        return {}
    return {"foreign_net":  int(output[0].get("frgn_ntby_qty", 0)),
            "institution_net": int(output[0].get("orgn_ntby_qty", 0))}

# ============================================================
# ⑧ ATR 기반 동적 손절·목표가
# ============================================================
def get_atr(code: str) -> float:
    """최근 N일 ATR(평균 진폭) 계산"""
    try:
        end   = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=20)).strftime("%Y%m%d")
        url   = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        params = {"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":code,
                  "FID_INPUT_DATE_1":start,"FID_INPUT_DATE_2":end,
                  "FID_PERIOD_DIV_CODE":"D","FID_ORG_ADJ_PRC":"0"}
        resp  = _session.get(url, headers=_headers("FHKST03010100"), params=params, timeout=15)
        items = resp.json().get("output2",[]) if resp.status_code == 200 else []
        trs   = []
        for i in items[-ATR_PERIOD:]:
            h = int(i.get("stck_hgpr", 0))
            l = int(i.get("stck_lwpr", 0))
            c = int(i.get("stck_clpr", 0))
            if h and l:
                trs.append(h - l)
        return sum(trs) / len(trs) if trs else 0
    except:
        return 0

def calc_stop_target(code: str, entry: int) -> tuple:
    """ATR 기반 손절·목표가. ATR 조회 실패 시 고정 비율 폴백"""
    atr = get_atr(code)
    if atr and atr > 0:
        stop   = int((entry - atr * ATR_STOP_MULT)  / 10) * 10
        target = int((entry + atr * ATR_TARGET_MULT) / 10) * 10
        stop_pct   = round((entry - stop)   / entry * 100, 1)
        target_pct = round((target - entry) / entry * 100, 1)
        return stop, target, stop_pct, target_pct, True   # True = ATR 사용
    else:
        stop   = int(entry * 0.93 / 10) * 10
        target = int(entry * 1.15 / 10) * 10
        return stop, target, 7.0, 15.0, False              # False = 고정 비율

# ============================================================
# ⑪ 전일 상한가 여부 체크
# ============================================================
_prev_upper_cache = {}  # code → {is_upper, ts}

def was_upper_limit_yesterday(code: str) -> bool:
    """전일 상한가(+29% 이상) 여부"""
    cached = _prev_upper_cache.get(code)
    if cached and time.time() - cached["ts"] < 3600:
        return cached["is_upper"]
    try:
        end   = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=5)).strftime("%Y%m%d")
        url   = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        params = {"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":code,
                  "FID_INPUT_DATE_1":start,"FID_INPUT_DATE_2":end,
                  "FID_PERIOD_DIV_CODE":"D","FID_ORG_ADJ_PRC":"0"}
        resp  = _session.get(url, headers=_headers("FHKST03010100"), params=params, timeout=15)
        items = resp.json().get("output2",[]) if resp.status_code == 200 else []
        items = sorted(items, key=lambda x: x.get("stck_bsop_date",""))
        if len(items) >= 2:
            prev    = items[-2]
            prev_c  = int(prev.get("stck_clpr", 0))
            prev_o  = int(prev.get("stck_oprc", 0)) or prev_c
            chg     = (prev_c - prev_o) / prev_o * 100 if prev_o else 0
            is_upper = chg >= 29.0
        else:
            is_upper = False
        _prev_upper_cache[code] = {"is_upper": is_upper, "ts": time.time()}
        return is_upper
    except:
        return False

# ============================================================
# ⑥ 섹터 모멘텀
# ============================================================
def _clear_sector_cache():
    """⑫ 장 시작 시 섹터 캐시 초기화"""
    global _sector_cache, _avg_volume_cache, _prev_upper_cache
    _sector_cache.clear()
    _avg_volume_cache.clear()
    _prev_upper_cache.clear()
    print("🔄 캐시 초기화 완료 (섹터·거래량·전일상한가)")

def get_sector_stocks_from_kis(code: str) -> list:
    """KIS API로 동일 업종 종목 조회"""
    cached = _sector_cache.get(code)
    if cached and time.time() - cached["ts"] < 3600:
        return cached["stocks"]
    try:
        url    = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
        params = {"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":code}
        data   = _safe_get(url, "FHKST01010100", params)
        o      = data.get("output", {})
        bstp_code = o.get("bstp_cls_code", "")
        bstp_name = o.get("bstp_kor_isnm", "")
        if not bstp_code:
            return []
        url2    = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-member"
        params2 = {"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":bstp_code,"FID_INPUT_CNT_1":"20"}
        data2   = _safe_get(url2, "FHPST02430000", params2)
        stocks  = [(i.get("mksc_shrn_iscd",""), i.get("hts_kor_isnm",""))
                   for i in data2.get("output",[])
                   if i.get("mksc_shrn_iscd") and i.get("mksc_shrn_iscd") != code][:10]
        _sector_cache[code] = {"sector": bstp_name, "stocks": stocks, "ts": time.time()}
        return stocks
    except Exception as e:
        print(f"⚠️ 섹터 조회 오류 ({code}): {e}")
        return []

def get_theme_sector_stocks(code: str) -> tuple:
    """THEME_MAP → 없으면 KIS API 자동 조회. (theme_name, [(code,name)])"""
    for theme_key, theme_info in THEME_MAP.items():
        if code in [c for c, _ in theme_info["stocks"]]:
            peers = [(c, n) for c, n in theme_info["stocks"] if c != code]
            return theme_key, peers
    peers = get_sector_stocks_from_kis(code)
    return "기타업종", peers

def calc_sector_momentum(code: str, name: str) -> dict:
    """
    섹터 동반 상승 체크
    기준: 등락률 +2% 이상 AND 거래량 2배 이상 → strong / 등락률 +2% 이상 → weak
    가산점: 섹터 전체(+15) / 절반이상(+10) / 1개이상(+5) + 거래량동반2개(+5)
    """
    theme_name, peers = get_theme_sector_stocks(code)
    if not peers:
        return {"bonus":0,"theme":theme_name,"summary":"","rising":[],"flat":[],"detail":[]}

    results = []
    for peer_code, peer_name in peers[:8]:
        try:
            cur = get_stock_price(peer_code)
            if not cur:
                continue
            cr, vr = cur.get("change_rate",0), cur.get("volume_ratio",0)
            results.append({
                "code": peer_code, "name": peer_name,
                "change_rate": cr, "volume_ratio": vr,
                "strong": cr >= 2.0 and vr >= 2.0,
                "weak":   cr >= 2.0,
            })
            time.sleep(0.15)
        except:
            continue

    if not results:
        return {"bonus":0,"theme":theme_name,"summary":"","rising":[],"flat":[],"detail":[]}

    total       = len(results)
    react_cnt   = sum(1 for r in results if r["weak"])
    strong_cnt  = sum(1 for r in results if r["strong"])
    react_ratio = react_cnt / total if total else 0

    bonus = 0
    if react_ratio >= 1.0:   bonus = 15
    elif react_ratio >= 0.5: bonus = 10
    elif react_cnt >= 1:     bonus = 5
    if strong_cnt >= 2:      bonus += 5

    rising = [r for r in results if r["weak"]]
    flat   = [r for r in results if not r["weak"]]

    if bonus == 0:
        summary = f"📉 섹터 반응 없음 ({theme_name}: {react_cnt}/{total})"
    elif react_ratio >= 1.0:
        summary = f"🔥 섹터 전체 동반 상승! ({theme_name}: {react_cnt}/{total})"
    elif react_ratio >= 0.5:
        summary = f"✅ 섹터 절반 이상 반응 ({theme_name}: {react_cnt}/{total})"
    else:
        summary = f"🟡 섹터 일부 반응 ({theme_name}: {react_cnt}/{total})"

    return {"bonus":bonus,"theme":theme_name,"summary":summary,
            "rising":rising,"flat":flat,"detail":results}

# ============================================================
# 💾 저장·복원
# ============================================================
def save_early_detect(stock: dict):
    try:
        data = {}
        try:
            with open(EARLY_LOG_FILE,"r") as f: data = json.load(f)
        except: pass
        code = stock["code"]
        if code not in data:
            data[code] = {
                "code": code, "name": stock["name"],
                "detect_time":      datetime.now().strftime("%H:%M"),
                "detect_date":      datetime.now().strftime("%Y%m%d"),
                "detect_price":     stock["price"],
                "change_at_detect": stock["change_rate"],
                "volume_ratio":     stock["volume_ratio"],
                "entry_price":      stock["entry_price"],
                "stop_price":       stock["stop_loss"],
                "target_price":     stock["target_price"],
                "status": "추적중", "pnl_pct": 0,
                "exit_price": 0, "exit_date": "",
            }
            with open(EARLY_LOG_FILE,"w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"  💾 EARLY_DETECT 저장: {stock['name']} ({code})")
    except Exception as e:
        print(f"⚠️ EARLY_DETECT 저장 오류: {e}")

def save_carry_stocks():
    try:
        data = {code: {
            "name": info["name"], "high_price": info["high_price"],
            "entry_price": info["entry_price"], "stop_loss": info["stop_loss"],
            "target_price": info["target_price"],
            "detected_at": info["detected_at"].strftime("%Y%m%d%H%M%S"),
            "carry_day": info.get("carry_day", 0),
        } for code, info in _detected_stocks.items()}
        with open(CARRY_FILE,"w") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ 이월 저장 실패: {e}")

def load_carry_stocks():
    try:
        with open(CARRY_FILE,"r") as f: data = json.load(f)
        for code, info in data.items():
            carry_day = info.get("carry_day", 0)
            if carry_day >= MAX_CARRY_DAYS: continue
            _detected_stocks[code] = {
                "name": info["name"], "high_price": info["high_price"],
                "entry_price": info["entry_price"], "stop_loss": info["stop_loss"],
                "target_price": info["target_price"],
                "detected_at": datetime.strptime(info["detected_at"],"%Y%m%d%H%M%S"),
                "carry_day": carry_day,
            }
        if _detected_stocks:
            print(f"📂 이월 종목 {len(_detected_stocks)}개 복원")
            send(f"📂 <b>이월 종목 복원</b>\n" +
                 "\n".join([f"• {v['name']} ({k})" for k,v in _detected_stocks.items()]) +
                 "\n\n눌림목 체크 재개")
    except: pass

# ============================================================
# ⑮ tracker 피드백 → EARLY_DETECT 조건 자동 조정
# ============================================================
def load_tracker_feedback():
    """tracker.py가 업데이트한 early_detect_log.json 읽어서 성공률 계산"""
    global _early_feedback, _early_price_min_dynamic, _early_volume_min_dynamic
    try:
        with open(EARLY_LOG_FILE,"r") as f: data = json.load(f)
        completed = [v for v in data.values() if v.get("status") in ["수익","손실","종료"]]
        if len(completed) < 5:
            return  # 데이터 부족
        success = sum(1 for v in completed if v.get("pnl_pct",0) > 0)
        total   = len(completed)
        rate    = success / total
        _early_feedback = {"total": total, "success": success, "rate": rate}

        # 성공률 70% 이상 → 조건 완화, 50% 미만 → 조건 강화
        if rate >= 0.70:
            _early_price_min_dynamic  = max(EARLY_PRICE_MIN - 2, 7.0)
            _early_volume_min_dynamic = max(EARLY_VOLUME_MIN - 2, 7.0)
        elif rate < 0.50:
            _early_price_min_dynamic  = min(EARLY_PRICE_MIN + 2, 15.0)
            _early_volume_min_dynamic = min(EARLY_VOLUME_MIN + 2, 15.0)
        else:
            _early_price_min_dynamic  = EARLY_PRICE_MIN
            _early_volume_min_dynamic = EARLY_VOLUME_MIN

        print(f"  📊 EARLY_DETECT 성공률: {rate*100:.0f}% ({success}/{total}) "
              f"→ 조건: 등락률>{_early_price_min_dynamic}%, 거래량>{_early_volume_min_dynamic}배")
    except: pass

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

def _sector_block(s: dict) -> str:
    si = s.get("sector_info")
    if not si or not si.get("detail"):
        return ""
    rising, flat = si.get("rising",[]), si.get("flat",[])
    bonus, theme = si.get("bonus",0), si.get("theme","")
    block = f"🏭 <b>섹터 모멘텀</b> [{theme}]  +{bonus}점\n"
    for r in rising[:5]:
        vol_tag = f" 🔊{r['volume_ratio']:.0f}x" if r.get("volume_ratio",0) >= 2 else ""
        block  += f"  📈 {r['name']} <b>{r['change_rate']:+.1f}%</b>{vol_tag}\n"
    for r in flat[:3]:
        block  += f"  ➖ {r['name']} {r['change_rate']:+.1f}%\n"
    block += "━━━━━━━━━━━━━━━\n\n"
    return block

def send_alert(s: dict):
    emoji = {"UPPER_LIMIT":"🚨","NEAR_UPPER":"🔥","STRONG_BUY":"💎",
             "SURGE":"📈","ENTRY_POINT":"🎯","EARLY_DETECT":"🔍"}.get(s["signal_type"],"📊")
    title = {"UPPER_LIMIT":"상한가 감지","NEAR_UPPER":"상한가 근접","STRONG_BUY":"강력 매수 신호",
             "SURGE":"급등 감지","ENTRY_POINT":"★ 눌림목 진입 시점 ★",
             "EARLY_DETECT":"★ 조기 포착 - 선진입 기회 ★"}.get(s["signal_type"],"급등 감지")
    stars   = "★" * min(int(s["score"] / 20), 5)
    reasons = "\n".join(s["reasons"])
    now_str = datetime.now().strftime("%H:%M:%S")

    stop, target    = s["stop_loss"], s["target_price"]
    stop_pct        = s.get("stop_pct",7.0)
    target_pct      = s.get("target_pct",15.0)
    atr_tag         = " (ATR)" if s.get("atr_used") else " (고정)"

    # 엄격 시간대 경고
    strict_warn = "\n⏰ <b>장 시작·마감 근접 구간 — 변동성 주의</b>\n" if is_strict_time() else ""

    if s["signal_type"] == "ENTRY_POINT":
        entry_msg = f"⚡️ <b>지금 눌림목 진입 구간!</b>\n🎯 진입가: <b>{s['entry_price']:,}원</b>"
    elif s["signal_type"] == "EARLY_DETECT":
        entry_msg = (f"⚡️ <b>지금 바로 진입 고려!</b>\n"
                     f"🎯 목표 진입가: <b>{s['entry_price']:,}원</b>")
    else:
        detected_at = s.get("detected_at", datetime.now())
        elapsed     = minutes_since(detected_at)
        pullback_time = (detected_at + timedelta(minutes=PULLBACK_CHECK_AFTER)).strftime("%H:%M")
        if elapsed < PULLBACK_CHECK_AFTER:
            entry_msg = (f"⏰ <b>눌림목 대기 중</b> ({PULLBACK_CHECK_AFTER-elapsed}분 후 체크)\n"
                         f"🕐 {pullback_time} 부터 눌림목 체크\n"
                         f"🎯 목표 진입가: <b>{s['entry_price']:,}원</b>")
        else:
            entry_msg = (f"📡 <b>눌림목 실시간 체크 중</b>\n"
                         f"🎯 목표 진입가: <b>{s['entry_price']:,}원</b>\n"
                         f"   (고점 대비 {PULLBACK_MIN:.0f}~{PULLBACK_MAX:.0f}% 되돌림 시 즉시 알림)")

    prev_upper_tag = "\n🔁 <b>전일 상한가 종목!</b> 연속 상한가 가능성 체크" if s.get("prev_upper") else ""

    send(
        f"{emoji} <b>[{title}]</b>\n<b>{s['name']}</b>  {s['code']}\n🕐 {now_str}\n"
        f"{strict_warn}\n"
        f"💰 현재가: <b>{s['price']:,}원</b>  (<b>+{s['change_rate']:.1f}%</b>)\n"
        f"📊 거래량: <b>{s['volume_ratio']:.1f}배</b> (5일 평균 대비)\n"
        f"⭐ 신호강도: {stars} ({s['score']}점)\n"
        f"{prev_upper_tag}\n"
        f"━━━━━━━━━━━━━━━\n{reasons}\n━━━━━━━━━━━━━━━\n\n"
        + _sector_block(s)
        + f"{entry_msg}\n\n"
        f"🛡 손절가: <b>{stop:,}원</b>  (-{stop_pct:.1f}%){atr_tag}\n"
        f"🏆 목표가: <b>{target:,}원</b>  (+{target_pct:.1f}%){atr_tag}\n\n"
        f"⚠️ 투자 판단은 본인 책임입니다"
    )

# ============================================================
# ③ 분석 엔진
# ============================================================
def analyze(stock: dict) -> dict:
    code        = stock.get("code","")
    change_rate = stock.get("change_rate", 0)
    vol_ratio   = stock.get("volume_ratio", 0)
    price       = stock.get("price", 0)
    if not code or price < 500:
        return {}

    # ⑩ 시간대별 필터: 엄격 구간에서는 조건 강화
    strict   = is_strict_time()
    min_score = 70 if strict else 60

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
        score += 30; reasons.append(f"💥 거래량 {vol_ratio:.1f}배 폭발! (5일 평균 대비)")
    elif vol_ratio >= VOLUME_SURGE_RATIO:
        score += 20; reasons.append(f"📊 거래량 {vol_ratio:.1f}배 급증 (5일 평균 대비)")

    if score >= 25:
        try:
            inv   = get_investor_trend(code)
            f_net = inv.get("foreign_net", 0)
            i_net = inv.get("institution_net", 0)
            if f_net > 0 and i_net > 0:
                score += 25; signal_type = "STRONG_BUY"
                reasons.append("✅ 외국인+기관 동시 순매수")
            elif f_net > 0:
                score += 10; reasons.append("🟡 외국인 순매수")
            elif i_net > 0:
                score += 10; reasons.append("🟡 기관 순매수")
        except: pass

    if score < min_score:
        return {}

    # ⑪ 전일 상한가 체크
    prev_upper = was_upper_limit_yesterday(code)
    if prev_upper:
        score += 10
        reasons.append("🔁 전일 상한가 → 연속 상한가 가능성")

    # 섹터 모멘텀
    sector_info = calc_sector_momentum(code, stock.get("name", code))
    if sector_info["bonus"] > 0:
        score += sector_info["bonus"]
        reasons.append(sector_info["summary"])
        if sector_info.get("rising"):
            rising_text = ", ".join([f"{r['name']} {r['change_rate']:+.1f}%" for r in sector_info["rising"][:4]])
            reasons.append(f"📌 동반 상승: {rising_text}")
    else:
        if sector_info.get("summary"):
            reasons.append(sector_info["summary"])

    # ⑧ ATR 기반 손절·목표가
    open_est = price / (1 + change_rate / 100)
    entry    = int((price - (price - open_est) * ENTRY_PULLBACK_RATIO) / 10) * 10
    stop, target, stop_pct, target_pct, atr_used = calc_stop_target(code, entry)

    return {
        "code": code, "name": stock.get("name", code),
        "price": price, "change_rate": change_rate, "volume_ratio": vol_ratio,
        "signal_type": signal_type, "score": score,
        "sector_info": sector_info,
        "entry_price": entry, "stop_loss": stop, "target_price": target,
        "stop_pct": stop_pct, "target_pct": target_pct, "atr_used": atr_used,
        "prev_upper": prev_upper,
        "reasons": reasons, "detected_at": datetime.now(),
    }

# ============================================================
# ① 조기 포착
# ============================================================
def check_early_detection() -> list:
    signals    = []
    candidates = get_volume_surge_stocks()
    for stock in candidates:
        code        = stock.get("code","")
        change_rate = stock.get("change_rate", 0)
        vol_ratio   = stock.get("volume_ratio", 0)
        price       = stock.get("price", 0)
        if not code or price < 500: continue
        if change_rate >= UPPER_LIMIT_THRESHOLD: continue

        # ⑩ 엄격 시간대 더 높은 조건 적용
        price_min  = _early_price_min_dynamic  * (1.3 if is_strict_time() else 1.0)
        volume_min = _early_volume_min_dynamic * (1.3 if is_strict_time() else 1.0)

        if change_rate < price_min or vol_ratio < volume_min: continue
        try:
            detail  = get_stock_price(code)
            bid_qty = detail.get("bid_qty", 0)
            ask_qty = detail.get("ask_qty", 0)
            if ask_qty > 0 and bid_qty / ask_qty < EARLY_HOGA_RATIO: continue
        except: continue

        now   = datetime.now()
        cache = _early_cache.get(code)
        if cache is None:
            _early_cache[code] = {"count":1,"last_price":price,"last_time":now}; continue
        elapsed = (now - cache["last_time"]).seconds
        if 50 <= elapsed <= 180:
            if price >= cache["last_price"]:
                cache["count"] += 1; cache["last_price"] = price; cache["last_time"] = now
            else:
                _early_cache[code] = {"count":1,"last_price":price,"last_time":now}; continue
        else:
            _early_cache[code] = {"count":1,"last_price":price,"last_time":now}; continue
        if cache["count"] < EARLY_CONFIRM_COUNT: continue
        del _early_cache[code]

        open_est  = price / (1 + change_rate / 100)
        entry     = int((price - (price - open_est) * ENTRY_PULLBACK_RATIO) / 10) * 10
        stop, target, stop_pct, target_pct, atr_used = calc_stop_target(code, entry)
        hoga_text = f"{bid_qty/ask_qty:.1f}배" if ask_qty > 0 else "압도적"

        # ⑪ 전일 상한가
        prev_upper = was_upper_limit_yesterday(code)
        early_score = 85 + (10 if prev_upper else 0)

        early_reasons = [
            f"🔍 조기 포착! (상한가 전 선진입 기회)",
            f"📈 현재 +{change_rate:.1f}% 상승 중",
            f"💥 거래량 {vol_ratio:.1f}배 폭발 (5일 평균 대비)",
            f"📊 매수/매도 잔량 {hoga_text}",
            f"✅ 2분 연속 상승 확인",
        ]
        if prev_upper:
            early_reasons.append("🔁 전일 상한가 → 연속 상한가 가능성")

        # 섹터 모멘텀
        sector_info = calc_sector_momentum(code, stock.get("name", code))
        if sector_info["bonus"] > 0:
            early_score += sector_info["bonus"]
            early_reasons.append(sector_info["summary"])
            if sector_info.get("rising"):
                rising_text = ", ".join([f"{r['name']} {r['change_rate']:+.1f}%" for r in sector_info["rising"][:4]])
                early_reasons.append(f"📌 동반 상승: {rising_text}")
        elif sector_info.get("summary"):
            early_reasons.append(sector_info["summary"])

        signals.append({
            "code": code, "name": stock.get("name", code),
            "price": price, "change_rate": change_rate, "volume_ratio": vol_ratio,
            "signal_type": "EARLY_DETECT", "score": early_score,
            "sector_info": sector_info,
            "entry_price": entry, "stop_loss": stop, "target_price": target,
            "stop_pct": stop_pct, "target_pct": target_pct, "atr_used": atr_used,
            "prev_upper": prev_upper,
            "reasons": early_reasons, "detected_at": now,
        })
    return signals

# ============================================================
# 눌림목 체크
# ============================================================
def check_pullback_signals() -> list:
    signals = []
    for code, info in list(_detected_stocks.items()):
        detected_at = info.get("detected_at")
        if not detected_at or minutes_since(detected_at) < PULLBACK_CHECK_AFTER: continue
        if time.time() - _pullback_history.get(code, 0) < 1800: continue
        try:
            cur   = get_stock_price(code)
            high  = info.get("high_price", 0)
            price = cur.get("price", 0)
            if not price or not high: continue
            if price > high:
                _detected_stocks[code]["high_price"] = price; continue
            pullback = (high - price) / high * 100
            elapsed  = minutes_since(detected_at)
            carry    = info.get("carry_day", 0)
            if PULLBACK_MIN <= pullback <= PULLBACK_MAX:
                entry = price
                stop, target, stop_pct, target_pct, atr_used = calc_stop_target(code, entry)
                carry_text = f" (이월 {carry}일차)" if carry > 0 else ""
                signals.append({
                    "code": code, "name": cur.get("name", code),
                    "price": price, "change_rate": cur.get("change_rate", 0), "volume_ratio": 0,
                    "signal_type": "ENTRY_POINT", "score": 95,
                    "entry_price": entry, "stop_loss": stop, "target_price": target,
                    "stop_pct": stop_pct, "target_pct": target_pct, "atr_used": atr_used,
                    "prev_upper": False,
                    "reasons": [
                        f"🎯 눌림목 진입 시점{carry_text}",
                        f"📌 고점 {high:,}원 → 현재 {price:,}원 (-{pullback:.1f}%)",
                        f"⏱ 급등 감지 후 {elapsed}분 경과",
                    ],
                    "detected_at": detected_at,
                })
                _pullback_history[code] = time.time()
        except: continue
    return signals

# ============================================================
# ⑭ 뉴스 다중 소스
# ============================================================
def fetch_naver_news() -> list:
    try:
        url  = "https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258"
        resp = requests.get(url, timeout=10, headers=_random_ua())
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        return [t.get_text(strip=True) for t in soup.select(".realtimeNewsList .newsList li a")][:30]
    except: return []

def fetch_hankyung_news() -> list:
    try:
        url  = "https://www.hankyung.com/economy"
        resp = requests.get(url, timeout=10, headers=_random_ua())
        soup = BeautifulSoup(resp.text, "html.parser")
        return [t.get_text(strip=True) for t in soup.select("h3.news-tit, h2.tit")][:20]
    except: return []

def fetch_yonhap_news() -> list:
    try:
        url  = "https://www.yna.co.kr/economy/stock"
        resp = requests.get(url, timeout=10, headers=_random_ua())
        soup = BeautifulSoup(resp.text, "html.parser")
        return [t.get_text(strip=True) for t in soup.select(".news-tl")][:20]
    except: return []

def fetch_all_news() -> list:
    """3개 소스 병렬 크롤링"""
    results = []
    threads = [
        threading.Thread(target=lambda: results.extend(fetch_naver_news())),
        threading.Thread(target=lambda: results.extend(fetch_hankyung_news())),
        threading.Thread(target=lambda: results.extend(fetch_yonhap_news())),
    ]
    for t in threads: t.start()
    for t in threads: t.join(timeout=8)
    return list(dict.fromkeys(results))  # 중복 제거

def analyze_news_theme() -> list:
    """
    뉴스 감지 → 해당 테마 종목 실제 주가 상승 확인
    → 주가 반응 없으면 스킵 → 섹터 동반 반응 통합 알림
    """
    signals   = []
    headlines = fetch_all_news()
    if not headlines:
        return []
    print(f"  📰 뉴스 {len(headlines)}건 분석 중 (3개 소스)...")

    for theme_key, theme_info in THEME_MAP.items():
        if time.time() - _news_alert_history.get(theme_key, 0) < 14400:
            continue
        matched_headlines = [h for h in headlines
                             if theme_key in h or any(s in h for s in theme_info.get("sectors",[]))]
        if not matched_headlines:
            continue

        stock_status = []
        for code, name in theme_info["stocks"]:
            try:
                cur = get_stock_price(code)
                if not cur: continue
                cr, vr = cur.get("change_rate",0), cur.get("volume_ratio",0)
                stock_status.append({
                    "code": code, "name": name,
                    "price": cur["price"], "change_rate": cr, "volume_ratio": vr,
                    "rising":  cr >= 2.0,
                    "surging": cr >= 5.0,
                    "vol_on":  vr >= 2.0,
                    "not_yet": cr < 2.0,
                })
                time.sleep(0.2)
            except: continue

        if not stock_status: continue
        rising_stocks = [s for s in stock_status if s["rising"]]
        if not rising_stocks:
            print(f"  ⏭ [{theme_key}] 뉴스 감지됐지만 주가 반응 없음 → 스킵")
            continue

        total        = len(stock_status)
        react_ratio  = len(rising_stocks) / total
        sector_bonus = (15 if react_ratio >= 1.0 else 10 if react_ratio >= 0.5 else 5)
        if sum(1 for s in rising_stocks if s["vol_on"]) >= 2:
            sector_bonus += 5

        if [s for s in stock_status if s["surging"]] and react_ratio >= 0.5:
            strength = "매우강함"
        elif react_ratio >= 0.5:
            strength = "강함"
        else:
            strength = "보통"

        _news_alert_history[theme_key] = time.time()
        signals.append({
            "theme_key": theme_key, "theme_desc": theme_info["desc"],
            "headline":  matched_headlines[0][:60],
            "rising":    rising_stocks,
            "surging":   [s for s in stock_status if s["surging"]],
            "not_yet":   [s for s in stock_status if s["not_yet"]][:4],
            "react_ratio":    react_ratio,
            "sector_bonus":   sector_bonus,
            "signal_strength": strength,
            "total": total,
        })
    return signals

def send_news_theme_alert(signal: dict):
    now      = datetime.now().strftime("%H:%M:%S")
    strength = signal["signal_strength"]
    emoji    = {"매우강함":"🔥","강함":"✅","보통":"🟡"}.get(strength,"📢")
    react_pct = int(signal["react_ratio"] * 100)
    rising_block = "".join([
        f"  📈 <b>{s['name']}</b> {s['change_rate']:+.1f}%"
        + (f" 🔊{s['volume_ratio']:.0f}x" if s["vol_on"] else "")
        + (" 🚀" if s["surging"] else "") + "\n"
        for s in signal["rising"]
    ])
    not_yet_block = "".join([f"  ⏳ {s['name']} {s['change_rate']:+.1f}%\n" for s in signal["not_yet"]])
    send(
        f"{emoji} <b>[뉴스+주가 연동 알림]</b>  {strength}\n"
        f"🕐 {now}\n\n"
        f"📰 <b>{signal['theme_desc']}</b>\n"
        f"💬 {signal['headline']}...\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🏭 섹터 반응: <b>{len(signal['rising'])}/{signal['total']}개</b> 상승 ({react_pct}%)  +{signal['sector_bonus']}점\n\n"
        + (f"🔥 <b>실제 상승 중인 종목</b>\n{rising_block}\n" if rising_block else "")
        + (f"🎯 <b>아직 안 오른 관련주 (추격 기회)</b>\n{not_yet_block}\n" if not_yet_block else "")
        + "━━━━━━━━━━━━━━━\n⚠️ 투자 판단은 본인 책임입니다"
    )

# ============================================================
# ⑤ DART 공시
# ============================================================
def _fetch_dart_list(today: str) -> list:
    items = []
    for ptype in ["A","B","D"]:
        try:
            resp = requests.get(
                "https://opendart.fss.or.kr/api/list.json",
                params={"crtfc_key":DART_API_KEY,"bgn_de":today,"end_de":today,
                        "pblntf_ty":ptype,"page_count":100},
                timeout=15
            )
            items += resp.json().get("list",[])
        except: pass
    return items

def run_dart_intraday():
    """장중 3분마다: 공시 감지 → 실제 주가 상승 확인 → 섹터 반응 → 통합 알림"""
    if not DART_API_KEY or not is_market_open(): return
    today = datetime.now().strftime("%Y%m%d")
    try:
        for item in _fetch_dart_list(today):
            rcept_no = item.get("rcept_no","")
            if not rcept_no or rcept_no in _dart_seen_ids: continue
            title, company, code = item.get("report_nm",""), item.get("corp_name",""), item.get("stock_code","")
            if not code: continue

            matched_urgent = [kw for kw in DART_URGENT_KEYWORDS if kw in title]
            matched_pos    = [kw for level,kws in DART_KEYWORDS.items() for kw in kws if kw in title]
            if not matched_urgent and not matched_pos: continue

            _dart_seen_ids.add(rcept_no)
            is_risk = any(kw in title for kw in DART_RISK_KEYWORDS)

            try:    cur = get_stock_price(code)
            except: cur = {}
            price, change_rate = cur.get("price",0), cur.get("change_rate",0)
            vol_ratio = cur.get("volume_ratio", 0)
            is_rising = change_rate >= 1.0

            if not is_rising and not is_risk:
                print(f"  ⏭ DART [{company}] 주가 반응 없음 → 스킵")
                continue

            sector_info = calc_sector_momentum(code, company) if price else \
                          {"bonus":0,"detail":[],"summary":"","rising":[],"flat":[]}

            now_str   = datetime.now().strftime("%H:%M:%S")
            emoji     = "🚨" if is_risk else ("🚀" if change_rate >= 5.0 else "📢")
            tag       = "⚠️ 위험 공시" if is_risk else "✅ 주요 공시"
            price_str = (f"\n💰 현재가: <b>{price:,}원</b>  (<b>{change_rate:+.1f}%</b>)"
                         + (f"  🔊{vol_ratio:.1f}x" if vol_ratio >= 2 else "")) if price else ""

            sector_block = ""
            if sector_info.get("detail"):
                react_cnt = len(sector_info.get("rising",[]))
                total_cnt = len(sector_info["detail"])
                sector_block = f"\n🏭 섹터 반응: <b>{react_cnt}/{total_cnt}개</b> 동반 상승\n"
                sector_block += "".join([f"  📈 {r['name']} {r['change_rate']:+.1f}%\n"
                                         for r in sector_info.get("rising",[])[:4]])

            all_kw = list(dict.fromkeys(matched_urgent + matched_pos))
            send(
                f"{emoji} <b>[공시+주가 연동 알림]</b>  {tag}\n"
                f"🕐 {now_str}\n\n"
                f"<b>{company}</b>  ({code})\n"
                f"📌 {title}"
                f"{price_str}\n"
                f"🔑 키워드: {', '.join(all_kw)}"
                f"{sector_block}\n\n"
                f"⚠️ 투자 판단은 본인 책임입니다"
            )
            print(f"  📋 공시+주가 알림: {company} {change_rate:+.1f}% - {title}")
    except Exception as e:
        print(f"⚠️ 장중 DART 오류: {e}")

def analyze_dart_disclosures():
    """15:30 종합 공시 분석"""
    if not DART_API_KEY: return
    print("\n📋 DART 종합 분석...")
    today = datetime.now().strftime("%Y%m%d")
    try:
        scored = []
        for item in _fetch_dart_list(today):
            title, company, code = item.get("report_nm",""), item.get("corp_name",""), item.get("stock_code","")
            if not code: continue
            score, matched, strength = 0, [], ""
            for level, keywords in DART_KEYWORDS.items():
                for kw in keywords:
                    if kw in title:
                        score += {"매우강함":30,"강함":20,"보통":10}[level]
                        matched.append(kw); strength = level
            if score >= 30 and matched:
                scored.append({"code":code,"company":company,"title":title,
                                "score":score,"matched":matched,"strength":strength})
        scored.sort(key=lambda x: x["score"], reverse=True)
        top = scored[:5]
        if not top:
            send("📋 <b>오늘 주목할 공시 없음</b>"); return
        msg = f"📋 <b>내일 주목 종목 - DART 공시 분석</b>\n🗓 {today[:4]}.{today[4:6]}.{today[6:]}\n━━━━━━━━━━━━━━━\n\n"
        for i, item in enumerate(top, 1):
            e = {"매우강함":"🔴","강함":"🟡","보통":"🟢"}.get(item["strength"],"⚪")
            msg += f"{i}. {e} <b>{item['company']}</b> ({item['code']})\n   📌 {item['title']}\n   🔑 {', '.join(item['matched'])}\n   ⭐ {item['score']}점\n\n"
        msg += "━━━━━━━━━━━━━━━\n⚠️ 내일 장 시작 전 확인 후 진입 판단"
        send(msg)
    except Exception as e:
        print(f"⚠️ DART 분석 오류: {e}")

# ============================================================
# ⑬ 텔레그램 명령어 수신
# ============================================================
_tg_offset = 0

def poll_telegram_commands():
    """텔레그램 /status /list /stop /resume 명령어 처리"""
    global _tg_offset, _bot_paused
    try:
        resp = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
            params={"offset": _tg_offset, "timeout": 5},
            timeout=10
        )
        updates = resp.json().get("result", [])
        for update in updates:
            _tg_offset = update["update_id"] + 1
            msg  = update.get("message", {})
            text = msg.get("text", "").strip().lower()
            if not text.startswith("/"): continue

            if text == "/status":
                rate_str = ""
                if _early_feedback.get("total", 0) >= 5:
                    rate_str = (f"\n📊 EARLY_DETECT 성공률: "
                                f"{_early_feedback['success']}/{_early_feedback['total']} "
                                f"({_early_feedback.get('rate',0)*100:.0f}%)")
                send(
                    f"🤖 <b>봇 상태</b>  {'⏸ 일시정지' if _bot_paused else '▶️ 실행 중'}\n"
                    f"🕐 {datetime.now().strftime('%H:%M:%S')}\n"
                    f"📡 장 {'열림' if is_market_open() else '닫힘'}\n"
                    f"👁 감시 종목: {len(_detected_stocks)}개\n"
                    f"📂 이월 종목: {sum(1 for v in _detected_stocks.values() if v.get('carry_day',0)>0)}개"
                    f"{rate_str}\n"
                    f"⚙️ EARLY 조건: 등락률>{_early_price_min_dynamic}%, 거래량>{_early_volume_min_dynamic}배"
                )
            elif text == "/list":
                if not _detected_stocks:
                    send("📋 현재 감시 중인 종목 없음")
                else:
                    lines = [f"• <b>{v['name']}</b> ({k}) — {v.get('carry_day',0)}일차"
                             for k, v in _detected_stocks.items()]
                    send("📋 <b>감시 중인 종목</b>\n" + "\n".join(lines))
            elif text == "/stop":
                _bot_paused = True
                send("⏸ <b>봇 일시정지</b>\n/resume 으로 재개")
            elif text == "/resume":
                _bot_paused = False
                send("▶️ <b>봇 재개</b>")
            else:
                send("📌 사용 가능한 명령어:\n/status — 봇 상태\n/list — 감시 종목\n/stop — 일시정지\n/resume — 재개")
    except Exception as e:
        print(f"⚠️ 텔레그램 명령어 오류: {e}")

# ============================================================
# 장 마감 처리
# ============================================================
def on_market_close():
    carry_list = []
    for code, info in list(_detected_stocks.items()):
        carry_day = info.get("carry_day", 0)
        if carry_day >= MAX_CARRY_DAYS:
            del _detected_stocks[code]; continue
        _detected_stocks[code]["carry_day"]   = carry_day + 1
        _detected_stocks[code]["detected_at"] = datetime.now()
        carry_list.append(f"• {info['name']} ({code}) - {carry_day+1}일차")
    save_carry_stocks()
    load_tracker_feedback()  # ⑮ 피드백 업데이트
    msg = (f"🔔 <b>장 마감</b>  {datetime.now().strftime('%Y-%m-%d')}\n"
           f"오늘 감시 종목: <b>{len(_detected_stocks)}개</b>\n")
    if carry_list:
        msg += f"\n📂 <b>이월 종목 ({len(carry_list)}개)</b>\n" + "\n".join(carry_list) + "\n\n내일 장 시작부터 눌림목 재체크"
    send(msg)
    analyze_dart_disclosures()

# ============================================================
# 🔄 스캔 루프
# ============================================================
def run_news_scan():
    if not is_market_open() or _bot_paused: return
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 뉴스 스캔...", flush=True)
    try:
        for signal in analyze_news_theme():
            send_news_theme_alert(signal)
    except Exception as e:
        print(f"⚠️ 뉴스 스캔 오류: {e}")

def run_scan():
    if not is_market_open() or _bot_paused: return
    strict_tag = " [엄격 구간]" if is_strict_time() else ""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 스캔 중{strict_tag}...", flush=True)
    try:
        alerts, seen = [], set()
        for stock in get_upper_limit_stocks():
            if stock["code"] in seen: continue
            r = analyze(stock)
            if r and time.time() - _alert_history.get(r["code"],0) > ALERT_COOLDOWN:
                alerts.append(r); seen.add(r["code"])
        for stock in get_volume_surge_stocks():
            if stock["code"] in seen: continue
            r = analyze(stock)
            if r and time.time() - _alert_history.get(r["code"],0) > ALERT_COOLDOWN:
                alerts.append(r); seen.add(r["code"])
        for s in check_early_detection():
            if s["code"] not in seen and time.time() - _alert_history.get(s["code"],0) > ALERT_COOLDOWN:
                alerts.append(s); seen.add(s["code"])
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
            if s["signal_type"] == "EARLY_DETECT":
                save_early_detect(s)
            if s["signal_type"] != "ENTRY_POINT":
                if s["code"] not in _detected_stocks:
                    _detected_stocks[s["code"]] = {
                        "name": s["name"], "high_price": s["price"],
                        "entry_price": s["entry_price"], "stop_loss": s["stop_loss"],
                        "target_price": s["target_price"], "detected_at": s["detected_at"], "carry_day": 0,
                    }
                elif s["price"] > _detected_stocks[s["code"]]["high_price"]:
                    _detected_stocks[s["code"]]["high_price"] = s["price"]
            time.sleep(1)
    except Exception as e:
        print(f"⚠️ 스캔 오류: {e}")

# ============================================================
# 🚀 실행
# ============================================================
if __name__ == "__main__":
    print("=" * 55)
    print("📈 KIS 주식 급등 알림 봇 v13 시작")
    print("=" * 55)

    load_carry_stocks()
    load_tracker_feedback()

    send(
        "🤖 <b>주식 급등 알림 봇 ON (v13)</b>\n\n"
        "✅ 한국투자증권 API 연결\n\n"
        "<b>📡 스캔 주기</b>\n"
        "• 주식 급등/상한가: 1분\n"
        "• 뉴스 (3개 소스): 2분\n"
        "• DART 공시: 3분\n"
        "• DART 종합: 매일 15:30\n\n"
        "<b>🔧 주요 기능</b>\n"
        "🔍 조기 포착 (상한가 전 선진입)\n"
        "📈 급등·상한가·외국인·기관 통합 분석\n"
        "🏭 섹터 모멘텀 (동반 상승 +최대 20점)\n"
        "📰 뉴스+주가 실제 반응 연동\n"
        "📋 공시+주가 실제 반응 연동\n"
        "🎯 눌림목 진입 + 최대 3일 이월\n"
        "⚙️ ATR 기반 동적 손절·목표가\n"
        "📊 거래량 5일 평균 대비 정확 계산\n"
        "🔁 전일 상한가 가산점\n"
        "⏰ 장 초반·마감 직전 엄격 필터\n"
        "🔄 EARLY_DETECT 성공률 자동 조건 조정\n\n"
        "<b>💬 명령어</b>\n"
        "/status  /list  /stop  /resume"
    )

    schedule.every(SCAN_INTERVAL).seconds.do(run_scan)
    schedule.every(NEWS_SCAN_INTERVAL).seconds.do(run_news_scan)
    schedule.every(DART_INTERVAL).seconds.do(run_dart_intraday)
    schedule.every(30).seconds.do(poll_telegram_commands)
    schedule.every().day.at(MARKET_OPEN).do(lambda: (
        _clear_sector_cache(),
        send(f"🌅 <b>장 시작!</b>  {datetime.now().strftime('%Y-%m-%d')}\n"
             f"📂 이월 종목: {len(_detected_stocks)}개\n📡 스캔 중...")
    ))
    schedule.every().day.at(MARKET_CLOSE).do(on_market_close)

    run_scan()
    run_news_scan()

    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ 메인 루프 오류: {e}")
            time.sleep(5)
