#!/usr/bin/env python3
"""
📈 KIS 주식 급등 알림 봇
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
버전: v30.5
날짜: 2026-03-01
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[변경 이력]

v30.5 (2026-03-01)  ← 현재
  ① /진입 명령어 추가 (실제 진입 확인 → /stats 내 실제 수익 집계)
  ② 트레일링 스탑 (목표가 도달 후 고점 -3% 시 자동 청산)
  ③ 연속 수익 공격 모드 (4회 연속 수익 → 최소점수 완화)
  ④ 이론/실제 수익 분리 (auto_tune=이론 전체, /stats=이론+내실제 분리)
  ⑤ 중앙 에러 로거 _log_error() (반복 오류 텔레그램 경고)
  ⑥ 섹터 감시 기간 동적 확장 (최대 24시간)
  ⑦ entry_pullback_ratio → 실제 진입가 계산에 연결
  ⑧ 재포착 시 signal_log "진입가변경" 자동 기록
  ⑨ auto_tune 진입미달 패턴 분석 (상승이탈/기간만료/재포착별 비율 자동조정)
  ⑩ /stats 진입미달 통계 블록 추가

v30.4 (2026-03-01)
  ① /진입 명령어 + Railway 400시간 주석
  ② 공휴일 즉시 종료 + 20:10 자동 종료
  ③ NXT 단독 시간대 국면/손익비/포지션 보정

v30.3 (2026-03-01)
  ① 실질 섹터 분류 4레이어 (상관계수+동반상승+DART지분+뉴스)
  ② NXT 시간대 국면 보수적 적용
  ③ 기능별 가중치 auto_tune 자동 조정

v30.0 (2026-03-01)
  ① 실질 섹터 스코어 기반 포트폴리오 중복 제거
  ② DART 지분 관계 함수 추가
  ③ 기능 기여도 추적 + 가중치 자동 조정

v29.0 (2026-03-01)
  ① 시장 국면 판단 (bull/normal/bear/crash)
  ② Kelly 기반 포지션 사이징
  ③ 손익비 동적 최적화 (국면별 ATR 배수)
  ④ 실적 발표 필터 (DART API)
  ⑤ 포트폴리오 관리 (동시 신호 중복 섹터 제거)

v28.0 (2026-03-01)
  ① RSI 보조지표 추가 (과매수 신호 차단, 과매도 눌림목 우대)
  ② 이동평균 정배열 필터 (역배열 시 신호 차단)
  ③ 볼린저밴드 돌파 가중 (+15점)
  ④ 유사패턴 매칭 (signal_log 기반 과거 성공률 표시)
  ⑤ 모든 파라미터 auto_tune 자동 최적화 연동
  ⑥ 알림 메시지에 보조지표 요약 표시

"""

BOT_VERSION = "v30.5"
BOT_DATE    = "2026-02-28"

import os, requests, time, schedule, json, random, threading, math
from datetime import datetime, time as dtime, timedelta
from bs4 import BeautifulSoup

# .env 파일 자동 로드 (python-dotenv 없어도 직접 파싱)
def _load_dotenv(path: str = ".env"):
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line: continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except FileNotFoundError: pass
_load_dotenv()

# ============================================================
# ⚙️ 환경변수
# ============================================================
KIS_APP_KEY        = os.environ.get("KIS_APP_KEY", "")
KIS_APP_SECRET     = os.environ.get("KIS_APP_SECRET", "")
KIS_ACCOUNT_NO     = os.environ.get("KIS_ACCOUNT_NO", "")
KIS_BASE_URL       = "https://openapi.koreainvestment.com:9443"
DART_API_KEY       = os.environ.get("DART_API_KEY", "")      # DART 공시 API
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

# TZ=Asia/Seoul 을 Railway 환경변수에 설정하면 모든 시간 계산이 한국 시간 기준
# (설정 안 하면 UTC 기준 → 스캔 시간이 9시간 어긋남)
_tz = os.environ.get("TZ", "")
if not _tz:
    print("⚠️ 환경변수 TZ 미설정 — Railway Variables에 TZ=Asia/Seoul 추가 권장")

# 백업 설정 (선택)
# GITHUB_GIST_TOKEN: github.com → Settings → Developer settings → Personal access tokens → gist 권한
# GITHUB_GIST_ID: 최초 실행 시 자동 생성, 이후 동일 Gist에 덮어씀
GITHUB_GIST_TOKEN  = os.environ.get("GITHUB_GIST_TOKEN", "")
GITHUB_GIST_ID     = os.environ.get("GITHUB_GIST_ID", "")   # 비워두면 자동 생성
BACKUP_INTERVAL_H  = 6   # 6시간마다 자동 백업

# ============================================================
# 📊 파라미터
# ============================================================
# 기본 스캔
VOLUME_SURGE_RATIO    = 5.0
PRICE_SURGE_MIN       = 5.0
UPPER_LIMIT_THRESHOLD = 25.0
EARLY_PRICE_MIN       = 10.0
EARLY_VOLUME_MIN      = 10.0
EARLY_HOGA_RATIO      = 3.0
EARLY_CONFIRM_COUNT   = 2
SCAN_INTERVAL         = 20    # 60→20초 (KIS API 분당 20회 한도 내 최대)
ALERT_COOLDOWN        = 1800
NEWS_SCAN_INTERVAL    = 45    # 120→45초 (크롤링 차단 방지 최소값)
DART_INTERVAL         = 60    # 180→60초 (DART API 여유 있음)
MARKET_OPEN           = "09:00"
MARKET_CLOSE          = "15:30"
ENTRY_PULLBACK_RATIO  = 0.4
MAX_CARRY_DAYS        = 3
CARRY_FILE            = "carry_stocks.json"
EARLY_LOG_FILE        = "early_detect_log.json"

# ATR
ATR_PERIOD       = 5
ATR_STOP_MULT    = 1.5
ATR_TARGET_MULT  = 3.0

# 시간대 필터
STRICT_OPEN_MINUTES  = 10
STRICT_CLOSE_MINUTES = 10

# ⑭ 중기 눌림목 파라미터
MID_PULLBACK_SCAN_INTERVAL = 90     # 300→90초 (일봉 기반이라 이 이상 빠르면 의미 없음)
MID_SURGE_MIN_PCT          = 15.0
MID_SURGE_LOOKBACK_DAYS    = 20
MID_PULLBACK_MIN           = 10.0
MID_PULLBACK_MAX           = 40.0
MID_PULLBACK_DAYS_MIN      = 2
MID_PULLBACK_DAYS_MAX      = 15
MID_VOL_RECOVERY_MIN       = 1.5
MID_ALERT_COOLDOWN         = 86400

# ⑮ 이평 괴리율
MA20_DISCOUNT_MIN  = -5.0   # 20일선 아래 최소 (%)
MA20_DISCOUNT_MAX  = -30.0  # 20일선 아래 최대 (%)
MA20_RECOVERY_MIN  = 1.0    # 이평 회복 최소 (%)

# ⑰ 거래량 표준편차
VOL_ZSCORE_MIN = 2.0         # 거래량 Z-score 최소 (2σ 이상 = 이상치)

# ⑯ 코스피 상대강도
KOSPI_CODE     = "0001"      # 코스피 지수 코드
RS_MIN         = 1.5         # 코스피 대비 최소 상대강도 배수

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

_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
]
def _random_ua() -> dict:
    return {"User-Agent": random.choice(_UA_POOL),
            "Accept-Language": "ko-KR,ko;q=0.9",
            "Referer": "https://finance.naver.com/"}

# ============================================================
# 🌐 상태 변수
# ============================================================
_access_token       = None
_token_expires      = 0
_session            = requests.Session()
_session.headers.update({"User-Agent": "Mozilla/5.0"})

# ⑤ 중앙 에러 로거 (중요 기능 오류 조용히 묻히지 않게)
_error_counts: dict = {}

def _log_error(func_name: str, e: Exception, critical: bool = False):
    _error_counts[func_name] = _error_counts.get(func_name, 0) + 1
    cnt = _error_counts[func_name]
    print(f"⚠️ [{func_name}] {type(e).__name__}: {e} (누적 {cnt}회)", flush=True)
    if critical or cnt in (5, 20, 100):
        try:
            send(f"🔴 <b>반복 오류 감지</b>\n"
                 f"함수: <code>{func_name}</code>  누적 {cnt}회\n"
                 f"오류: {type(e).__name__}: {str(e)[:100]}")
        except: pass

_alert_history      = {}
_detected_stocks    = {}
_pullback_history   = {}
_news_alert_history = {}
_early_cache        = {}
_sector_cache       = {}
_dart_seen_ids      = set()
_bot_paused         = False
_mid_pullback_alert_history = {}
_early_feedback     = {"total": 0, "success": 0}
_early_price_min_dynamic  = EARLY_PRICE_MIN
_early_volume_min_dynamic = EARLY_VOLUME_MIN

# ── 동적 테마 (가격상관관계 + 뉴스 공동언급으로 자동 생성) ──
_dynamic_theme_map  = {}
DYNAMIC_THEME_FILE  = "dynamic_themes.json"
CORR_MIN            = 0.70
CORR_LOOKBACK       = 20
NEWS_COOCCUR_FILE   = "news_cooccur.json"

# ── 섹터 지속 모니터링 ──
_sector_monitor     = {}
SECTOR_MONITOR_INTERVAL  = 180   # 600→180초 (3분)
SECTOR_MONITOR_MAX_HOURS = 6

# ── 진입가 감지 ──
_entry_watch        = {}
ENTRY_TOLERANCE_PCT  = 2.0   # 진입가 ±2% 이내 → 진입 구간
ENTRY_REWATCH_MINS   = 10    # 30→10분 (진입 구간이 빠르게 지나감)
ENTRY_WATCH_MAX_HOURS = 6    # 진입가 감시 최대 6시간 → 장 마감 시 자동 만료됨

# ── 오늘의 최우선 종목 ──
_today_top_signals: dict = {}
TOP_SIGNAL_SEND_AT       = "10:00"  # 시작 시각 (이후 1시간마다 반복)

# ── 뉴스 역추적 캐시 ──
_news_reverse_cache: dict = {}

# ── 컴팩트 알림 모드 ──
# True면 1~2줄 요약, False면 기존 상세 포맷
_compact_mode: bool = False
COMPACT_MODE_FILE   = "compact_mode.json"

def _load_compact_mode():
    global _compact_mode
    try:
        with open(COMPACT_MODE_FILE) as f:
            _compact_mode = json.load(f).get("compact", False)
    except: pass

def _save_compact_mode():
    try:
        with open(COMPACT_MODE_FILE, "w") as f:
            json.dump({"compact": _compact_mode}, f)
    except: pass

# ── 알림 중요도 레벨 ──
# CRITICAL(🔴): 즉시 발송  NORMAL(🟡): 즉시 발송  INFO(🔵): 묶어서 10분마다
ALERT_LEVEL_CRITICAL = "CRITICAL"
ALERT_LEVEL_NORMAL   = "NORMAL"
ALERT_LEVEL_INFO     = "INFO"
_pending_info_alerts: list = []   # INFO 레벨 묶음 대기열
INFO_FLUSH_INTERVAL  = 300        # 600→300초 (5분)

# ── 손절 후 재진입 감시 ──
# code → {name, stop_price, ts, signal_type, entry, stop, target}
# 만료 기준: 시간 제한 없이 장 마감(on_market_close)에서 일괄 초기화
_reentry_watch: dict = {}
REENTRY_BOUNCE_PCT  = 3.0   # 5→3% (V자 반등 빠른 포착)
REENTRY_VOL_MIN     = 1.5   # 2.0→1.5배 (조건 완화)

# ============================================================
# 🕐 시간 유틸
# ============================================================
# ── 한국 증시 휴장일 자동 관리 ──
# KRX 공공데이터 API로 매년 자동 갱신
_kr_holidays: set = set()
_holiday_loaded_year: int = 0

def _load_kr_holidays(year: int = None):
    """
    공공데이터포털 KRX 휴장일 API로 자동 조회
    API 실패 시 하드코딩 fallback 사용
    """
    global _kr_holidays, _holiday_loaded_year
    if year is None:
        year = datetime.now().year
    if _holiday_loaded_year == year and _kr_holidays:
        return

    # 1차: 공공데이터포털 한국천문연구원 특일 정보 API
    loaded = False
    pub_api_key = os.environ.get("PUBLIC_DATA_API_KEY", "")
    if pub_api_key:
        try:
            resp = requests.get(
                "http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo",
                params={"serviceKey": pub_api_key, "solYear": year,
                        "numOfRows": 50, "_type": "json"},
                timeout=10
            )
            items = resp.json().get("response",{}).get("body",{}).get("items",{}).get("item",[])
            if isinstance(items, dict): items = [items]
            holidays = {str(i["locdate"]) for i in items if i.get("locdate")}
            if holidays:
                _kr_holidays = holidays
                _holiday_loaded_year = year
                loaded = True
                print(f"  📅 공휴일 {len(holidays)}일 자동 로드 ({year}년)")
        except Exception as e:
            print(f"  ⚠️ 공휴일 API 실패: {e}")

    # 2차: KRX 장운영일정 스크래핑 fallback
    if not loaded:
        try:
            resp = requests.post(
                "http://open.krx.co.kr/contents/OPN/99/OPN99000001.jspx",
                data={"tboxisuCd_finder_secuprod0_0":"","isu_cd":"",
                      "isuCd":"","isu_nm":"","searchType":"1",
                      "strtDd": f"{year}0101","endDd": f"{year}1231",
                      "pagePath":"/contents/COM/GenerateOTP.jspx"},
                timeout=10
            )
            # 간단 파싱 (실패해도 괜찮음)
        except: pass

    # 3차: 하드코딩 fallback (API 모두 실패 시)
    if not loaded:
        fallback = {
            2025: {"20250101","20250128","20250129","20250130","20250301",
                   "20250505","20250506","20250603","20250606","20250815",
                   "20251003","20251008","20251009","20251225"},
            2026: {"20260101","20260127","20260128","20260129","20260301",
                   "20260505","20260525","20260606","20260815",
                   "20261002","20261003","20261005","20261009","20261225","20261231"},
        }
        _kr_holidays = fallback.get(year, set())
        _holiday_loaded_year = year
        print(f"  📅 공휴일 fallback 사용 ({year}년, {len(_kr_holidays)}일)")

def is_holiday(date_str: str = None) -> bool:
    """주말 또는 공휴일 여부"""
    now = datetime.strptime(date_str, "%Y%m%d") if date_str else datetime.now()
    _load_kr_holidays(now.year)
    return now.weekday() >= 5 or now.strftime("%Y%m%d") in _kr_holidays

def is_market_open() -> bool:
    now = datetime.now()
    if is_holiday(): return False
    return dtime(9, 0) <= now.time() <= dtime(15, 30)

def is_any_market_open() -> bool:
    """
    KRX 또는 NXT 중 하나라도 열려 있으면 True
    코드 전반에서 '장이 완전히 끝났는가'를 판단할 때 사용
    - KRX: 09:00~15:30
    - NXT: 08:00~20:00
    """
    return is_market_open() or is_nxt_open()

def is_nxt_listed(code: str) -> bool:
    """
    해당 종목이 NXT에 상장돼 있는지 확인
    _nxt_unavailable에 없으면 상장된 것으로 간주 (조회 시 자동 판별)
    """
    return code not in _nxt_unavailable

def effective_market_close() -> bool:
    """
    '실질적 장 마감' 여부
    - NXT 상장 종목: NXT 20:00 이후
    - KRX only 종목: KRX 15:30 이후
    코드에서 '장이 완전히 끝났다'는 판단이 필요할 때 사용
    """
    return not is_any_market_open()

def minutes_since(dt: datetime) -> int:
    return int((datetime.now() - dt).total_seconds() // 60)

def is_strict_time() -> bool:
    n   = datetime.now().time()
    o_e = (datetime.now().replace(hour=9,  minute=0)  + timedelta(minutes=STRICT_OPEN_MINUTES)).time()
    c_s = (datetime.now().replace(hour=15, minute=30) - timedelta(minutes=STRICT_CLOSE_MINUTES)).time()
    return n <= o_e or n >= c_s

# ============================================================
# 🔐 KIS API
# ============================================================
def get_token(retry: int = 3) -> str:
    global _access_token, _token_expires
    if _access_token and time.time() < _token_expires:
        return _access_token
    for attempt in range(retry):
        try:
            resp = _session.post(f"{KIS_BASE_URL}/oauth2/tokenP",
                json={"grant_type":"client_credentials","appkey":KIS_APP_KEY,"appsecret":KIS_APP_SECRET},
                timeout=15)
            resp.raise_for_status()
            d = resp.json()
            _access_token  = d["access_token"]
            _token_expires = time.time() + int(d.get("expires_in", 86400)) - 300
            print(f"✅ KIS 토큰 발급 ({datetime.now().strftime('%H:%M:%S')})")
            return _access_token
        except Exception as e:
            _log_error(f"get_token(attempt={attempt+1})", e, critical=attempt==2); time.sleep(5*(attempt+1))
    raise Exception("❌ KIS 토큰 최종 실패")

def _headers(tr_id: str) -> dict:
    return {"Content-Type":"application/json; charset=utf-8",
            "Authorization":f"Bearer {get_token()}",
            "appkey":KIS_APP_KEY,"appsecret":KIS_APP_SECRET,
            "tr_id":tr_id,"custtype":"P"}

def _safe_get(url: str, tr_id: str, params: dict) -> dict:
    try:
        resp = _session.get(url, headers=_headers(tr_id), params=params, timeout=15)
        if resp.status_code == 403:
            global _access_token; _access_token = None
            resp = _session.get(url, headers=_headers(tr_id), params=params, timeout=15)
        return resp.json() if resp.status_code == 200 else {}
    except Exception as e:
        print(f"⚠️ API 오류 ({tr_id}): {e}"); return {}

# ============================================================
# 📊 일봉 데이터 (공통 사용)
# ============================================================
_daily_cache = {}  # code → {items, ts}

def get_daily_data(code: str, days: int = 60) -> list:
    """일봉 데이터 조회 (캐시 30분)"""
    cached = _daily_cache.get(code)
    if cached and time.time() - cached["ts"] < 1800:
        return cached["items"]
    try:
        end   = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=days+10)).strftime("%Y%m%d")
        url   = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        params = {"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":code,
                  "FID_INPUT_DATE_1":start,"FID_INPUT_DATE_2":end,
                  "FID_PERIOD_DIV_CODE":"D","FID_ORG_ADJ_PRC":"0"}
        resp  = _session.get(url, headers=_headers("FHKST03010100"), params=params, timeout=15)
        items = resp.json().get("output2",[]) if resp.status_code == 200 else []
        items = sorted([{
            "date":  i.get("stck_bsop_date",""),
            "open":  int(i.get("stck_oprc",0)),
            "high":  int(i.get("stck_hgpr",0)),
            "low":   int(i.get("stck_lwpr",0)),
            "close": int(i.get("stck_clpr",0)),
            "vol":   int(i.get("acml_vol",0)),
        } for i in items if i.get("stck_bsop_date")], key=lambda x: x["date"])
        _daily_cache[code] = {"items": items, "ts": time.time()}
        return items
    except Exception as e:
        _log_error(f"get_daily_data({code})", e); return []

# ============================================================
# ⑦-A 보조지표 계산 (RSI / 이동평균 / 볼린저밴드 / 유사패턴)
# ============================================================

def calc_rsi(items: list, period: int = None) -> float:
    """
    RSI 계산. period는 _dynamic["rsi_period"] 자동 적용.
    반환: 0~100 (70↑ 과매수, 30↓ 과매도)
    """
    period = period or int(_dynamic.get("rsi_period", 14))
    closes = [i["close"] for i in items if i.get("close")]
    if len(closes) < period + 1:
        return 50.0  # 데이터 부족 시 중립값
    gains, losses = [], []
    for i in range(1, period + 1):
        diff = closes[-(period + 1 - i)] - closes[-(period + 2 - i)]
        (gains if diff > 0 else losses).append(abs(diff))
    avg_gain = sum(gains) / period if gains else 0
    avg_loss = sum(losses) / period if losses else 0
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)

def calc_ma_trend(items: list) -> dict:
    """
    이동평균선 정배열 여부 확인.
    _dynamic["ma_short"/"ma_mid"/"ma_long"] 자동 적용.
    반환: {"aligned": bool, "short": float, "mid": float, "long": float, "desc": str}
    """
    s = int(_dynamic.get("ma_short", 5))
    m = int(_dynamic.get("ma_mid",   20))
    l = int(_dynamic.get("ma_long",  60))
    closes = [i["close"] for i in items if i.get("close")]
    if len(closes) < l:
        return {"aligned": None, "short": 0, "mid": 0, "long": 0, "desc": "데이터부족"}
    ma_s = sum(closes[-s:]) / s
    ma_m = sum(closes[-m:]) / m
    ma_l = sum(closes[-l:]) / l
    aligned   = ma_s > ma_m > ma_l          # 정배열
    partially = ma_s > ma_m or ma_m > ma_l  # 부분 정배열
    if aligned:
        desc = f"✅ 정배열 ({s}>{m}>{l}일)"
    elif partially:
        desc = f"🟡 부분정배열"
    else:
        desc = f"🔴 역배열"
    return {"aligned": aligned, "partial": partially,
            "short": round(ma_s), "mid": round(ma_m), "long": round(ma_l), "desc": desc}

def calc_bollinger(items: list, period: int = None, k: float = 2.0) -> dict:
    """
    볼린저밴드 계산.
    반환: {"upper": int, "mid": int, "lower": int,
           "pct_b": float,  # 현재가가 밴드 내 위치 (0=하단, 1=상단)
           "breakout": bool, "desc": str}
    """
    period = period or int(_dynamic.get("bb_period", 20))
    closes = [i["close"] for i in items if i.get("close")]
    if len(closes) < period:
        return {"upper": 0, "mid": 0, "lower": 0, "pct_b": 0.5, "breakout": False, "desc": "데이터부족"}
    window = closes[-period:]
    mid    = sum(window) / period
    std    = (sum((c - mid) ** 2 for c in window) / period) ** 0.5
    upper  = int(mid + k * std)
    lower  = int(mid - k * std)
    cur    = closes[-1]
    pct_b  = round((cur - lower) / (upper - lower), 2) if upper != lower else 0.5
    breakout = cur >= upper
    if breakout:
        desc = f"🚀 상단 돌파 (밴드폭 {(upper-lower)/mid*100:.1f}%)"
    elif pct_b >= 0.8:
        desc = f"🔥 상단 근접 ({pct_b*100:.0f}%)"
    elif pct_b <= 0.2:
        desc = f"🎯 하단 근접 ({pct_b*100:.0f}%) — 반등 가능"
    else:
        desc = f"밴드 중간 ({pct_b*100:.0f}%)"
    return {"upper": upper, "mid": int(mid), "lower": lower,
            "pct_b": pct_b, "breakout": breakout, "desc": desc}

def calc_indicators(code: str) -> dict:
    """
    RSI + MA + 볼린저밴드 한 번에 계산.
    get_daily_data 캐시 활용 → API 추가 호출 없음.
    반환: {"rsi": float, "ma": dict, "bb": dict, "filter_pass": bool, "score_adj": int, "summary": str}
    """
    try:
        items = get_daily_data(code, 70)
        if len(items) < 20:
            return {"rsi": 50, "ma": {}, "bb": {}, "filter_pass": True, "score_adj": 0, "summary": ""}

        rsi = calc_rsi(items)
        ma  = calc_ma_trend(items)
        bb  = calc_bollinger(items)

        score_adj   = 0
        filter_pass = True
        reasons     = []

        # ── 기능별 가중치 적용 ──
        w_rsi = _dynamic.get("feat_w_rsi", 1.0)
        w_ma  = _dynamic.get("feat_w_ma",  1.0)
        w_bb  = _dynamic.get("feat_w_bb",  1.0)

        # ── RSI 필터 ──
        rsi_overbuy  = float(_dynamic.get("rsi_overbuy",  70))
        rsi_oversell = float(_dynamic.get("rsi_oversell", 30))
        if w_rsi > 0:
            if rsi >= rsi_overbuy:
                score_adj   -= int(15 * w_rsi)
                filter_pass  = w_rsi < 0.5   # 가중치 낮으면 차단 안 함
                reasons.append(f"⛔ RSI {rsi} 과매수 (w={w_rsi})")
            elif rsi <= rsi_oversell:
                score_adj += int(10 * w_rsi)
                reasons.append(f"🎯 RSI {rsi} 과매도 +{int(10*w_rsi)}점")
            elif rsi >= 60:
                score_adj += int(5 * w_rsi)
                reasons.append(f"📊 RSI {rsi} 강세 +{int(5*w_rsi)}점")

        # ── 이동평균 필터 ──
        if w_ma > 0:
            if ma.get("aligned") is False and not ma.get("partial"):
                score_adj -= int(10 * w_ma)
                if w_ma >= 0.8: filter_pass = False
                reasons.append(f"⛔ {ma.get('desc','역배열')} (w={w_ma})")
            elif ma.get("aligned"):
                score_adj += int(10 * w_ma)
                reasons.append(f"✅ {ma.get('desc','정배열')} +{int(10*w_ma)}점")
            elif ma.get("partial"):
                score_adj += int(3 * w_ma)
                reasons.append(f"🟡 부분정배열 +{int(3*w_ma)}점")

        # ── 볼린저밴드 필터 ──
        if w_bb > 0:
            if bb.get("breakout"):
                score_adj += int(15 * w_bb)
                reasons.append(f"🚀 볼린저 상단 돌파 +{int(15*w_bb)}점")
            elif bb.get("pct_b", 0.5) <= 0.2:
                score_adj += int(8 * w_bb)
                reasons.append(f"🎯 볼린저 하단 근접 +{int(8*w_bb)}점")

        summary = "\n".join(reasons) if reasons else ""
        return {"rsi": rsi, "ma": ma, "bb": bb,
                "filter_pass": filter_pass, "score_adj": score_adj, "summary": summary}
    except Exception as e:
        print(f"  ⚠️ 지표 계산 오류 ({code}): {e}")
        return {"rsi": 50, "ma": {}, "bb": {}, "filter_pass": True, "score_adj": 0, "summary": ""}

# ── 유사 패턴 매칭 (signal_log 기반) ──
def find_similar_patterns(code: str, signal_type: str, change_rate: float, vol_ratio: float) -> str:
    """
    signal_log.json에서 비슷한 조건의 과거 신호를 찾아 성공률 반환.
    유사 기준: 같은 신호 유형 + 상승률 ±3% + 거래량 ±3배
    반환: 텔레그램 표시용 문자열 (없으면 "")
    """
    try:
        data = {}
        try:
            with open(SIGNAL_LOG_FILE, "r") as f: data = json.load(f)
        except: return ""

        completed = [v for v in data.values()
                     if v.get("status") in ["수익","손실","본전"]
                     and v.get("signal_type") == signal_type]
        if len(completed) < 3:
            return ""

        # 유사 조건 필터
        similar = [v for v in completed
                   if abs(v.get("change_at_detect", 0) - change_rate) <= 3.0
                   and abs(v.get("volume_ratio", 0) - vol_ratio) <= 3.0]

        if len(similar) < 2:
            # 유사 조건 없으면 같은 신호 유형 전체 통계
            similar = completed

        wins     = sum(1 for v in similar if v["pnl_pct"] > 0)
        win_rate = round(wins / len(similar) * 100)
        avg_pnl  = round(sum(v["pnl_pct"] for v in similar) / len(similar), 1)
        best     = max(similar, key=lambda x: x["pnl_pct"])
        worst    = min(similar, key=lambda x: x["pnl_pct"])

        bar = "🟢" * (win_rate // 20) + "⬜" * (5 - win_rate // 20)
        label = "유사 조건" if len(similar) < len(completed) else "동일 신호 유형"

        return (f"🔍 <b>과거 유사 패턴</b> ({label} {len(similar)}건)\n"
                f"  {bar} 성공률 {win_rate}%  평균 {avg_pnl:+.1f}%\n"
                f"  최고 {best['pnl_pct']:+.1f}%  최저 {worst['pnl_pct']:+.1f}%")
    except:
        return ""

# ============================================================
# ⑦ 거래량 5일 평균 대비 정확 계산
# ============================================================
_avg_volume_cache = {}

def get_avg_volume(code: str) -> int:
    cached = _avg_volume_cache.get(code)
    if cached and time.time() - cached["ts"] < 3600:
        return cached["avg_vol"]
    items = get_daily_data(code, 20)
    vols  = [i["vol"] for i in items if i["vol"]]
    avg   = int(sum(vols[-5:]) / len(vols[-5:])) if len(vols) >= 3 else 0
    _avg_volume_cache[code] = {"avg_vol": avg, "ts": time.time()}
    return avg

def get_real_volume_ratio(code: str, today_vol: int) -> float:
    avg = get_avg_volume(code)
    return round(today_vol / avg, 1) if avg and today_vol else 0.0

# ============================================================
# ⑧ ATR 기반 동적 손절·목표가
# ============================================================
def get_atr(code: str) -> float:
    items = get_daily_data(code, 20)
    trs   = [i["high"] - i["low"] for i in items[-ATR_PERIOD:] if i["high"] and i["low"]]
    return sum(trs) / len(trs) if trs else 0

def calc_stop_target(code: str, entry: int) -> tuple:
    atr = get_atr(code)
    if atr > 0:
        stop   = int((entry - atr * ATR_STOP_MULT)  / 10) * 10
        target = int((entry + atr * ATR_TARGET_MULT) / 10) * 10
        return stop, target, round((entry-stop)/entry*100,1), round((target-entry)/entry*100,1), True
    stop   = int(entry * 0.93 / 10) * 10
    target = int(entry * 1.15 / 10) * 10
    return stop, target, 7.0, 15.0, False

# ============================================================
# ⑨ 전일 상한가 체크
# ============================================================
_prev_upper_cache = {}

def was_upper_limit_yesterday(code: str) -> bool:
    cached = _prev_upper_cache.get(code)
    if cached and time.time() - cached["ts"] < 3600:
        return cached["is_upper"]
    items    = get_daily_data(code, 10)
    is_upper = False
    if len(items) >= 2:
        prev     = items[-2]
        prev_o   = prev["open"] or prev["close"]
        chg      = (prev["close"] - prev_o) / prev_o * 100 if prev_o else 0
        is_upper = chg >= 29.0
    _prev_upper_cache[code] = {"is_upper": is_upper, "ts": time.time()}
    return is_upper

# ============================================================
# ⑩ 캐시 초기화
# ============================================================
# ============================================================
# 💾 자동 백업 시스템
# ============================================================
_last_backup_ts: float = 0
_gist_id_runtime: str  = GITHUB_GIST_ID   # 런타임 중 생성된 Gist ID 보관

def backup_to_gist() -> bool:
    """
    현재 stock_alert.py를 GitHub Gist에 자동 백업
    - GITHUB_GIST_ID 있으면 기존 Gist 업데이트 (PATCH)
    - 없으면 새 Gist 생성 (POST) → ID를 _gist_id_runtime에 저장
    반환: 성공 여부
    """
    global _gist_id_runtime
    if not GITHUB_GIST_TOKEN:
        return False
    try:
        script_path = os.path.abspath(__file__)
        with open(script_path, "r", encoding="utf-8") as f:
            code = f.read()
        ts_str   = datetime.now().strftime("%Y-%m-%d %H:%M")
        filename = f"stock_alert_{BOT_VERSION}.py"
        headers  = {
            "Authorization": f"token {GITHUB_GIST_TOKEN}",
            "Accept": "application/vnd.github+json",
        }
        payload = {
            "description": f"주식 급등 알림 봇 {BOT_VERSION} — 백업 {ts_str}",
            "public": False,
            "files": {filename: {"content": code}},
        }
        if _gist_id_runtime:
            # 기존 Gist 업데이트
            resp = requests.patch(
                f"https://api.github.com/gists/{_gist_id_runtime}",
                json=payload, headers=headers, timeout=20
            )
        else:
            # 새 Gist 생성
            resp = requests.post(
                "https://api.github.com/gists",
                json=payload, headers=headers, timeout=20
            )
            if resp.status_code in (200, 201):
                _gist_id_runtime = resp.json().get("id", "")
                print(f"  💾 새 Gist 생성: {_gist_id_runtime}")

        ok = resp.status_code in (200, 201)
        if ok:
            print(f"  💾 Gist 백업 완료: {BOT_VERSION}  {ts_str}")
        else:
            print(f"  ⚠️ Gist 백업 실패: {resp.status_code}")
        return ok
    except Exception as e:
        print(f"  ⚠️ Gist 백업 오류: {e}")
        return False

def backup_to_telegram() -> bool:
    """
    현재 stock_alert.py를 텔레그램으로 파일 전송 (백업용)
    GitHub 토큰 없을 때 대안으로 사용
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        script_path = os.path.abspath(__file__)
        ts_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(script_path, "rb") as f:
            resp = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument",
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "caption": f"💾 자동 백업  {BOT_VERSION}  {ts_str}",
                },
                files={"document": (f"stock_alert_{BOT_VERSION}_{datetime.now().strftime('%Y%m%d_%H%M')}.py", f)},
                timeout=30
            )
        ok = resp.status_code == 200
        if ok: print(f"  💾 텔레그램 파일 백업 완료: {ts_str}")
        else:  print(f"  ⚠️ 텔레그램 백업 실패: {resp.status_code}")
        return ok
    except Exception as e:
        print(f"  ⚠️ 텔레그램 백업 오류: {e}")
        return False

def run_auto_backup(notify: bool = False):
    """
    자동 백업 실행 — Gist 우선, 없으면 텔레그램 파일 전송
    notify=True면 텔레그램으로 백업 완료 메시지도 전송
    """
    global _last_backup_ts
    now = time.time()
    if now - _last_backup_ts < BACKUP_INTERVAL_H * 3600 - 60:
        return   # 인터벌 미달
    _last_backup_ts = now

    ok_gist = backup_to_gist()
    ok_tg   = False
    if not ok_gist:
        ok_tg = backup_to_telegram()

    if notify and (ok_gist or ok_tg):
        method = "GitHub Gist" if ok_gist else "텔레그램 파일"
        send(f"💾 <b>자동 백업 완료</b>  {BOT_VERSION}\n"
             f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
             f"📦 방법: {method}")
    elif notify and not ok_gist and not ok_tg:
        print("  ⚠️ 백업 실패 — GITHUB_GIST_TOKEN 또는 텔레그램 설정 확인")


def _clear_all_cache():
    global _sector_cache, _avg_volume_cache, _prev_upper_cache, _daily_cache
    global _nxt_cache, _nxt_unavailable, _early_cache, _news_reverse_cache
    global _kospi_cache, _sector_monitor, _pending_info_alerts
    _sector_cache.clear();       _avg_volume_cache.clear()
    _prev_upper_cache.clear();   _daily_cache.clear()
    _nxt_cache.clear();          _nxt_unavailable.clear()
    _early_cache.clear();        _news_reverse_cache.clear()
    _sector_monitor.clear();     _pending_info_alerts.clear()
    _kospi_cache["ts"] = 0;      _kospi_cache["change"] = 0.0
    reset_top_signals_daily()    # 날짜 넘어가면 TOP 종목 풀도 초기화
    print("🔄 전체 캐시 초기화 완료 (NXT + 전체 캐시 포함)")

# ============================================================
# ⑮ 20일 이동평균 괴리율 (Renaissance 평균회귀)
# ============================================================
def get_ma20_deviation(code: str) -> float:
    """현재가 기준 20일 이평 대비 괴리율 (%) — 음수면 이평 아래"""
    items = get_daily_data(code, 30)
    if len(items) < 20:
        return 0.0
    ma20  = sum(i["close"] for i in items[-20:]) / 20
    price = items[-1]["close"]
    return round((price - ma20) / ma20 * 100, 2) if ma20 else 0.0

# ============================================================
# ⑯ 코스피 상대강도 (시장 중립 필터)
# ============================================================
_kospi_cache = {"change": 0.0, "ts": 0}

def get_kospi_change() -> float:
    """코스피 당일 등락률"""
    if time.time() - _kospi_cache["ts"] < 300:
        return _kospi_cache["change"]
    try:
        url    = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-index-price"
        params = {"FID_COND_MRKT_DIV_CODE":"U","FID_INPUT_ISCD":KOSPI_CODE}
        data   = _safe_get(url, "FHPUP02100000", params)
        o      = data.get("output", {})
        chg    = float(o.get("bstp_nmix_prdy_ctrt", 0))
        _kospi_cache["change"] = chg
        _kospi_cache["ts"]     = time.time()
        return chg
    except:
        return 0.0

def get_relative_strength(stock_change: float) -> float:
    """종목 등락률 / 코스피 등락률 = 상대강도"""
    kospi = get_kospi_change()
    if not kospi or kospi == 0:
        return stock_change  # 코스피 보합이면 그냥 종목 등락률
    return round(stock_change / abs(kospi), 2)

# ============================================================
# ⑰ 거래량 표준편차 Z-score (통계적 이상 탐지)
# ============================================================
def get_volume_zscore(code: str, today_vol: int) -> float:
    """오늘 거래량의 Z-score (과거 20일 기준)"""
    items = get_daily_data(code, 30)
    vols  = [i["vol"] for i in items[-20:] if i["vol"]]
    if len(vols) < 5:
        return 0.0
    mean = sum(vols) / len(vols)
    std  = math.sqrt(sum((v - mean) ** 2 for v in vols) / len(vols))
    return round((today_vol - mean) / std, 2) if std > 0 else 0.0

# ============================================================
# ⑭ 중기 눌림목 핵심 분석 함수
# ============================================================
def analyze_mid_pullback(code: str, name: str) -> dict:
    """
    퀀트펀드 눌림목 모멘텀 분석 (AQR 방식 응용)

    패턴:
      1단계: 1차 급등 확인 (20일 내 +15% 이상)
      2단계: 건강한 눌림 확인
             - 고점 대비 -10~40% 조정
             - 눌림 기간: 2~15일
             - 눌림 중 거래량 감소 (관심 유지되는 건강한 조정)
      3단계: 재상승 시작 신호
             - 당일 양봉 (종가 > 시가)
             - 거래량 회복 (눌림 평균의 1.5배 이상)
             - 20일선 회복 시작
      4단계: 섹터 동반 + 코스피 상대강도

    반환: grade(A/B/C), score, reasons, entry/stop/target
    """
    items = get_daily_data(code, MID_SURGE_LOOKBACK_DAYS + MID_PULLBACK_DAYS_MAX + 10)
    if len(items) < 10:
        return {}

    today  = items[-1]
    price  = today["close"]
    if price < 500:
        return {}

    # ━━━ 1단계: 1차 급등 확인 ━━━
    # 최근 20일 내에서 저점 → 고점 상승률 계산
    lookback = items[-(MID_SURGE_LOOKBACK_DAYS + MID_PULLBACK_DAYS_MAX):-1]
    if not lookback:
        return {}

    surge_peak_idx  = -1
    surge_peak_price = 0
    surge_from_price = 0
    surge_pct        = 0

    for i in range(len(lookback) - 1, -1, -1):
        candidate_high = lookback[i]["high"]
        # 이 고점 이전의 저점 탐색 (최대 20일 이전)
        search_start = max(0, i - MID_SURGE_LOOKBACK_DAYS)
        base_low = min(lookback[j]["low"] for j in range(search_start, i+1) if lookback[j]["low"])
        if not base_low:
            continue
        pct = (candidate_high - base_low) / base_low * 100
        if pct >= _dynamic["mid_surge_min_pct"] and candidate_high > surge_peak_price:
            surge_peak_price = candidate_high
            surge_from_price = base_low
            surge_peak_idx   = i
            surge_pct        = round(pct, 1)

    if surge_peak_idx < 0 or surge_peak_price == 0:
        return {}  # 1차 급등 없음

    # ━━━ 2단계: 건강한 눌림 확인 ━━━
    # 급등 고점 이후 ~ 오늘까지의 데이터
    after_peak = lookback[surge_peak_idx+1:] + [today]
    if not after_peak:
        return {}

    pullback_low   = min(d["low"]   for d in after_peak if d["low"])
    pullback_days  = len(after_peak)
    pullback_pct   = round((surge_peak_price - pullback_low) / surge_peak_price * 100, 1)

    # 눌림 깊이·기간 검증
    if not (_dynamic["mid_pullback_min"] <= pullback_pct <= _dynamic["mid_pullback_max"]):
        return {}
    if not (MID_PULLBACK_DAYS_MIN <= pullback_days <= MID_PULLBACK_DAYS_MAX):
        return {}

    # 눌림 중 거래량 감소 여부 (건강한 눌림 = 거래량 줄면서 쉬는 것)
    surge_vols    = [d["vol"] for d in lookback[max(0,surge_peak_idx-3):surge_peak_idx+1] if d["vol"]]
    pullback_vols = [d["vol"] for d in after_peak[:-1] if d["vol"]]  # 오늘 제외
    avg_surge_vol   = sum(surge_vols)    / len(surge_vols)    if surge_vols    else 0
    avg_pullback_vol = sum(pullback_vols) / len(pullback_vols) if pullback_vols else 0
    vol_dried = avg_pullback_vol < avg_surge_vol * 0.7 if avg_surge_vol else False

    # ━━━ 3단계: 재상승 시작 신호 ━━━
    today_vol     = today["vol"]
    today_open    = today["open"]
    today_close   = today["close"]
    today_high    = today["high"]

    # 당일 양봉 확인
    is_bullish = today_close > today_open if today_open else False

    # 거래량 회복 (눌림 평균 대비)
    vol_recovered = (today_vol >= avg_pullback_vol * _dynamic["mid_vol_recovery"]) if avg_pullback_vol else False

    # 20일 이동평균 계산
    ma_items = items[-20:]
    ma20     = sum(i["close"] for i in ma_items) / len(ma_items) if len(ma_items) >= 20 else 0
    ma20_dev = round((today_close - ma20) / ma20 * 100, 1) if ma20 else 0

    # 이평 회복 시작 (20일선을 향해 올라오는 중)
    prev_close   = items[-2]["close"] if len(items) >= 2 else 0
    ma20_recovering = (today_close > prev_close and ma20_dev > -15) if prev_close and ma20 else False

    # 고점 대비 현재 위치 (반등 진행도)
    current_pullback = round((surge_peak_price - today_close) / surge_peak_price * 100, 1)

    # ━━━ 4단계: 스코어 계산 ━━━
    score   = 0
    reasons = []
    grade   = "C"

    # 1차 급등 강도
    if surge_pct >= 40:   score += 25; reasons.append(f"🚀 1차 급등 {surge_pct:.0f}% (강력)")
    elif surge_pct >= 25: score += 20; reasons.append(f"📈 1차 급등 {surge_pct:.0f}%")
    else:                 score += 15; reasons.append(f"📈 1차 급등 {surge_pct:.0f}%")

    # 눌림 품질 (건강한 눌림일수록 높은 점수)
    if vol_dried:
        score += 15; reasons.append(f"✅ 건강한 눌림 (거래량 감소 확인, -{pullback_pct:.0f}%)")
    else:
        score += 8;  reasons.append(f"🟡 눌림 {pullback_pct:.0f}% ({pullback_days}일간)")

    # 눌림 깊이 — 황금 구간 (15~30%)이 가장 이상적
    if 15 <= pullback_pct <= 30:
        score += 15; reasons.append(f"🎯 황금 눌림 구간 ({pullback_pct:.0f}%)")
    elif 10 <= pullback_pct < 15:
        score += 8;  reasons.append(f"🟡 얕은 눌림 ({pullback_pct:.0f}%)")
    else:
        score += 5;  reasons.append(f"🟠 깊은 눌림 ({pullback_pct:.0f}%)")

    # 재상승 신호
    if is_bullish:
        score += 10; reasons.append("🕯 당일 양봉 확인")
    if vol_recovered:
        vol_ratio_vs_pb = round(today_vol / avg_pullback_vol, 1) if avg_pullback_vol else 0
        score += 15; reasons.append(f"💥 거래량 회복 (눌림 평균 대비 {vol_ratio_vs_pb:.1f}배)")
    if ma20_recovering:
        score += 10; reasons.append(f"📊 20일선 회복 중 (현재 {ma20_dev:+.1f}%)")

    # ━━━ 4-1: 코스피 상대강도 체크 ⑯ ━━━
    kospi_chg = get_kospi_change()
    today_chg  = round((today_close - (items[-2]["close"] if len(items)>=2 else today_close))
                       / (items[-2]["close"] or today_close) * 100, 2)
    rs = get_relative_strength(today_chg)
    if rs >= RS_MIN:
        score += 10; reasons.append(f"💪 코스피 상대강도 {rs:.1f}배 (코스피 {kospi_chg:+.1f}%)")

    # ━━━ 4-2: 거래량 Z-score ⑰ ━━━
    z = get_volume_zscore(code, today_vol)
    if z >= VOL_ZSCORE_MIN:
        score += 10; reasons.append(f"📊 거래량 이상 급증 (Z-score {z:.1f}σ)")

    # ━━━ 4-3: 20일선 괴리율 ⑮ ━━━
    if MA20_DISCOUNT_MAX <= ma20_dev <= MA20_DISCOUNT_MIN:
        score += 5; reasons.append(f"📐 20일선 저점 근접 ({ma20_dev:+.1f}%)")

    # ━━━ 4-4: NXT 신뢰도 보정 ━━━
    nxt_delta, nxt_reason = 0, ""
    try:
        nxt_delta, nxt_reason = nxt_score_bonus(code)
        if nxt_delta != 0:
            score += nxt_delta
            if nxt_reason: reasons.append(nxt_reason)
    except: pass

    # 최소 조건: 양봉 + 거래량 회복 둘 다 없으면 재상승 미확인
    if not is_bullish and not vol_recovered:
        return {}

    # 등급 결정
    if score >= 80:   grade = "A"
    elif score >= 60: grade = "B"
    elif score >= 45: grade = "C"
    else:             return {}  # 점수 미달

    # 손절·목표가
    entry = today_close
    stop, target, stop_pct, target_pct, atr_used = calc_stop_target(code, entry)

    return {
        "code": code, "name": name,
        "price": today_close, "change_rate": today_chg,
        "volume_ratio": round(today_vol / avg_surge_vol, 1) if avg_surge_vol else 0,
        "signal_type": "MID_PULLBACK",
        "grade": grade, "score": score,
        "surge_pct":     surge_pct,
        "pullback_pct":  pullback_pct,
        "pullback_days": pullback_days,
        "current_pullback": current_pullback,
        "vol_dried":     vol_dried,
        "vol_recovered": vol_recovered,
        "is_bullish":    is_bullish,
        "ma20_dev":      ma20_dev,
        "rs":            rs,
        "vol_zscore":    z,
        "entry_price":   entry,
        "stop_loss":     stop, "target_price": target,
        "stop_pct":      stop_pct, "target_pct": target_pct,
        "atr_used":      atr_used,
        "reasons":       reasons,
        "detected_at":   datetime.now(),
    }

# ============================================================
# 중기 눌림목 스캐너 후보군 자동 확장
# ============================================================
_dynamic_candidates = {}   # code → {name, desc, added_ts}

def refresh_dynamic_candidates():
    """
    거래량 상위 50종목을 자동으로 후보군에 편입
    → THEME_MAP에 없는 종목(아주IB투자, 국전약품 등)도 포착 가능
    매일 장 시작 시 + 1시간마다 갱신
    """
    try:
        # 거래량 급증 상위 종목
        vol_stocks = get_volume_surge_stocks()
        # 상한가 근접 상위 종목
        upper_stocks = get_upper_limit_stocks()
        candidates = {s["code"]: s["name"] for s in vol_stocks + upper_stocks if s.get("code")}
        for code, name in candidates.items():
            if code not in _dynamic_candidates:
                _dynamic_candidates[code] = {"name": name, "desc": "자동편입", "added_ts": time.time()}
        print(f"  🔄 동적 후보군: {len(_dynamic_candidates)}개 종목")
    except Exception as e:
        print(f"⚠️ 동적 후보군 갱신 오류: {e}")

def get_all_scan_candidates() -> list:
    """
    THEME_MAP + 동적 후보군 합산 → 중복 제거
    반환: [(code, name, desc), ...]
    """
    seen = set()
    result = []
    # THEME_MAP 우선
    for theme_info in THEME_MAP.values():
        for c, n in theme_info["stocks"]:
            if c not in seen:
                seen.add(c); result.append((c, n, theme_info["desc"]))
    # 동적 후보군 추가 (THEME_MAP에 없는 종목만)
    for code, info in _dynamic_candidates.items():
        if code not in seen:
            seen.add(code); result.append((code, info["name"], info["desc"]))
    return result

# ============================================================
# 장중 실시간 눌림목 돌파 감지
# ============================================================
def check_intraday_pullback_breakout(code: str, name: str) -> dict:
    """
    어제까지 눌림 완성 + 오늘 장 중 돌파 실시간 감지
    (일봉 완성 기다리지 않음 → 아주IB투자, 국전약품 같은 케이스 포착)

    조건:
      - 어제까지 일봉: 1차 급등 이후 눌림 패턴 완성
      - 오늘 장 중:  거래량 폭발 (5일 평균 3배 이상)
                     + 현재가 > 어제 종가 (양봉 진행 중)
                     + 상승률 5% 이상 (돌파 신호)
    """
    # 어제까지 데이터로 눌림 패턴 확인 (오늘 제외)
    items = get_daily_data(code, MID_SURGE_LOOKBACK_DAYS + MID_PULLBACK_DAYS_MAX + 5)
    if len(items) < 8:
        return {}

    # 오늘 실시간 데이터
    cur = get_stock_price(code)
    if not cur or not cur.get("price"):
        return {}
    today_price  = cur["price"]
    today_chg    = cur["change_rate"]
    today_vol    = cur["today_vol"]
    vol_ratio    = cur["volume_ratio"]

    # 최소 조건: 오늘 +5% 이상, 거래량 3배 이상
    if today_chg < 5.0 or vol_ratio < 3.0:
        return {}

    # 어제까지 데이터에서 눌림 패턴 확인
    hist = items[:-1]   # 오늘 제외 (어제까지)
    if len(hist) < 6:
        return {}

    prev_close = hist[-1]["close"]  # 어제 종가

    # 1차 급등 탐색 (어제까지 데이터)
    surge_peak_price = 0; surge_pct = 0; surge_peak_idx = -1
    for i in range(len(hist)-1, max(0, len(hist)-MID_SURGE_LOOKBACK_DAYS)-1, -1):
        candidate_high = hist[i]["high"]
        search_start   = max(0, i - MID_SURGE_LOOKBACK_DAYS)
        lows = [hist[j]["low"] for j in range(search_start, i+1) if hist[j]["low"]]
        if not lows: continue
        base_low = min(lows)
        pct = (candidate_high - base_low) / base_low * 100
        if pct >= _dynamic["mid_surge_min_pct"] and candidate_high > surge_peak_price:
            surge_peak_price = candidate_high; surge_pct = round(pct,1); surge_peak_idx = i

    if surge_peak_idx < 0 or surge_peak_price == 0:
        return {}

    # 눌림 확인 (고점 이후 ~ 어제까지)
    after_peak = hist[surge_peak_idx+1:]
    if not after_peak:
        return {}
    pullback_low  = min(d["low"]  for d in after_peak if d["low"])
    pullback_days = len(after_peak)
    pullback_pct  = round((surge_peak_price - pullback_low) / surge_peak_price * 100, 1)

    if not (_dynamic["mid_pullback_min"] <= pullback_pct <= _dynamic["mid_pullback_max"]):
        return {}
    if not (MID_PULLBACK_DAYS_MIN <= pullback_days <= MID_PULLBACK_DAYS_MAX):
        return {}

    # 거래량 감소 여부
    surge_vols    = [d["vol"] for d in hist[max(0,surge_peak_idx-3):surge_peak_idx+1] if d["vol"]]
    pb_vols       = [d["vol"] for d in after_peak if d["vol"]]
    avg_surge_vol = sum(surge_vols)/len(surge_vols) if surge_vols else 0
    avg_pb_vol    = sum(pb_vols)/len(pb_vols) if pb_vols else 0
    vol_dried     = avg_pb_vol < avg_surge_vol * 0.7 if avg_surge_vol else False

    # 오늘 돌파 강도
    z    = get_volume_zscore(code, today_vol)
    rs   = get_relative_strength(today_chg)
    ma20 = sum(d["close"] for d in hist[-20:])/20 if len(hist)>=20 else 0
    ma20_dev = round((today_price-ma20)/ma20*100,1) if ma20 else 0

    # 스코어
    score = 0; reasons = []
    reasons.append(f"⚡️ <b>장중 돌파 감지!</b> (어제까지 눌림 완성 → 오늘 돌파)")
    if surge_pct >= 40: score+=25; reasons.append(f"🚀 1차 급등 {surge_pct:.0f}% (강력)")
    elif surge_pct >= 25: score+=20; reasons.append(f"📈 1차 급등 {surge_pct:.0f}%")
    else: score+=15; reasons.append(f"📈 1차 급등 {surge_pct:.0f}%")

    if vol_dried: score+=15; reasons.append(f"✅ 눌림 중 거래량 감소 확인 (건강한 조정)")
    else: score+=8; reasons.append(f"🟡 눌림 {pullback_pct:.0f}% ({pullback_days}일간)")

    if 15 <= pullback_pct <= 30: score+=15; reasons.append(f"🎯 황금 눌림 구간 ({pullback_pct:.0f}%)")
    elif pullback_pct < 15: score+=8; reasons.append(f"🟡 얕은 눌림 ({pullback_pct:.0f}%)")
    else: score+=5; reasons.append(f"🟠 깊은 눌림 ({pullback_pct:.0f}%)")

    # 오늘 돌파 신호 강도
    if today_chg >= 20: score+=30; reasons.append(f"🚨 오늘 +{today_chg:.0f}% 강력 돌파!")
    elif today_chg >= 10: score+=20; reasons.append(f"🔥 오늘 +{today_chg:.0f}% 돌파")
    else: score+=10; reasons.append(f"📈 오늘 +{today_chg:.1f}% 돌파 시작")

    if vol_ratio >= 10: score+=20; reasons.append(f"💥 거래량 {vol_ratio:.0f}배 폭발 (5일 평균 대비)")
    elif vol_ratio >= 5: score+=15; reasons.append(f"💥 거래량 {vol_ratio:.0f}배 급증")
    else: score+=8; reasons.append(f"📊 거래량 {vol_ratio:.1f}배")

    if z >= VOL_ZSCORE_MIN: score+=10; reasons.append(f"📊 거래량 Z-score {z:.1f}σ")
    if rs >= RS_MIN: score+=10; reasons.append(f"💪 코스피 상대강도 {rs:.1f}배")
    if ma20_dev > 0: score+=5; reasons.append(f"📐 20일선 돌파 (+{ma20_dev:.1f}%)")

    if score < 45:
        return {}

    grade = "A" if score>=80 else "B" if score>=60 else "C"
    entry = today_price
    stop, target, stop_pct, target_pct, atr_used = calc_stop_target(code, entry)

    return {
        "code": code, "name": name, "price": today_price, "change_rate": today_chg,
        "volume_ratio": vol_ratio, "signal_type": "MID_PULLBACK",
        "is_intraday": True,   # 장중 돌파 표시
        "grade": grade, "score": score,
        "surge_pct": surge_pct, "pullback_pct": pullback_pct, "pullback_days": pullback_days,
        "current_pullback": round((surge_peak_price-today_price)/surge_peak_price*100,1),
        "vol_dried": vol_dried, "vol_recovered": True, "is_bullish": True,
        "ma20_dev": ma20_dev, "rs": rs, "vol_zscore": z,
        "entry_price": entry, "stop_loss": stop, "target_price": target,
        "stop_pct": stop_pct, "target_pct": target_pct, "atr_used": atr_used,
        "reasons": reasons, "detected_at": datetime.now(),
    }

# ============================================================
# 중기 눌림목 스캐너 — THEME_MAP + 동적 후보군 전체 스캔
# ============================================================
def run_mid_pullback_scan():
    """
    90초마다 전체 후보군 중기 눌림목 체크
    ① 일봉 완성 기준 중기 눌림목 (KRX 장중에만)
    ② KRX 마감 후에도 NXT 급등 종목은 눌림목 체크 계속
    """
    krx_open = is_market_open()
    nxt_open = is_nxt_open()
    if not krx_open and not nxt_open: return
    if _bot_paused: return
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 중기 눌림목 스캔{'(NXT포함)' if nxt_open else ''}...", flush=True)

    # 동적 후보군 갱신 (30분마다)
    if not _dynamic_candidates or time.time() - min(
            v["added_ts"] for v in _dynamic_candidates.values()) > 1800:
        refresh_dynamic_candidates()

    all_candidates = get_all_scan_candidates()
    signals = []

    for code, name, theme_desc in all_candidates:
        if time.time() - _mid_pullback_alert_history.get(code, 0) < MID_ALERT_COOLDOWN:
            continue
        try:
            # ① 일봉 기준 중기 눌림목
            result = analyze_mid_pullback(code, name)
            if not result:
                # ② 일봉 패턴 미완성이면 장중 돌파 감지로 재시도
                result = check_intraday_pullback_breakout(code, name)
            if result:
                result["theme_desc"] = theme_desc
                sector_info = calc_sector_momentum(code, name)
                result["sector_info"] = sector_info
                result["score"] += sector_info.get("bonus", 0)
                signals.append(result)
            time.sleep(0.3)
        except Exception as e:
            print(f"⚠️ 중기 눌림목 오류 ({code}): {e}")
            continue

    if not signals:
        print("  → 중기 눌림목 조건 충족 종목 없음")
        return

    signals.sort(key=lambda x: x["score"], reverse=True)
    for s in signals[:3]:
        send_mid_pullback_alert(s)
        save_signal_log(s)
        register_entry_watch(s)                     # ★ 진입가 감시 등록
        start_sector_monitor(s["code"], s["name"])  # ★ 섹터 지속 모니터링
        _mid_pullback_alert_history[s["code"]] = time.time()
        tag = "[장중돌파]" if s.get("is_intraday") else "[일봉]"
        print(f"  ✓ 중기 눌림목 {tag}: {s['name']} [{s['grade']}등급] {s['score']}점")

def send_mid_pullback_alert(s: dict):
    grade_emoji = {"A":"🏆","B":"🥈","C":"🥉"}.get(s["grade"],"📊")
    grade_text  = {"A":"A등급 (최우선)","B":"B등급 (우선)","C":"C등급 (참고)"}.get(s["grade"],"")
    now_str     = datetime.now().strftime("%H:%M:%S")
    reasons     = "\n".join(s["reasons"])
    atr_tag     = " (ATR)" if s.get("atr_used") else " (고정)"
    entry  = s.get("entry_price", 0)
    stop   = s.get("stop_loss", 0)
    target = s.get("target_price", 0)
    price  = s.get("price", 0)
    diff_from_entry = ((price - entry) / entry * 100) if entry and price else 0
    entry_block = (
        f"┌─────────────────────\n"
        f"│ 🟣 <b>진입 포인트</b>\n"
        f"│ 🎯 진입가  <b>{entry:,}원</b>  ← 현재 {diff_from_entry:+.1f}%\n"
        f"│ 🛡 손절가  <b>{stop:,}원</b>  (-{s['stop_pct']:.1f}%){atr_tag}\n"
        f"│ 🏆 목표가  <b>{target:,}원</b>  (+{s['target_pct']:.1f}%){atr_tag}\n"
        f"└─────────────────────"
    )

    si = s.get("sector_info") or {}
    theme     = si.get("theme", "")
    rising    = si.get("rising", [])
    flat      = si.get("flat", [])
    detail    = si.get("detail", [])
    si_summary = si.get("summary", "")
    bonus     = si.get("bonus", 0)

    if detail:
        bonus_tag    = f"  +{bonus}점" if bonus > 0 else ""
        sector_block = f"\n━━━━━━━━━━━━━━━\n🏭 <b>섹터 모멘텀</b> [{theme}]{bonus_tag}\n"
        if si_summary:
            sector_block += f"  {si_summary}\n"
        for r in rising[:5]:
            vol_tag       = f" 🔊{r['volume_ratio']:.0f}x" if r.get("volume_ratio", 0) >= 2 else ""
            sector_block += f"  📈 {r['name']} <b>{r['change_rate']:+.1f}%</b>{vol_tag}\n"
        for r in flat[:3]:
            sector_block += f"  ➖ {r['name']} {r['change_rate']:+.1f}%\n"
    elif theme:
        sector_block = f"\n━━━━━━━━━━━━━━━\n🏭 섹터 [{theme}]: 동업종 조회 중\n"
    else:
        sector_block = f"\n━━━━━━━━━━━━━━━\n🏭 섹터: 조회 실패\n"

    intraday_tag = "  ⚡️ 장중 돌파" if s.get("is_intraday") else ""
    send_with_chart_buttons(
        f"{grade_emoji} <b>[중기 눌림목 진입 신호]</b>  {grade_text}{intraday_tag}\n"
        f"🕐 {now_str}  |  테마: {s.get('theme_desc','')}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🟣 <b>{s['name']}</b>  <code>{s['code']}</code>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📈 <b>패턴 요약</b>\n"
        f"  1차 급등: <b>+{s['surge_pct']:.0f}%</b>\n"
        f"  눌림 깊이: <b>-{s['pullback_pct']:.0f}%</b>  ({s['pullback_days']}일간)\n"
        f"  현재 고점 대비: <b>-{s['current_pullback']:.0f}%</b> 위치\n"
        f"  20일선 대비: <b>{s['ma20_dev']:+.1f}%</b>\n"
        f"  거래량 Z-score: <b>{s['vol_zscore']:.1f}σ</b>\n"
        f"  코스피 상대강도: <b>{s['rs']:.1f}배</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{reasons}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{sector_block}\n"
        f"💰 현재가: <b>{s['price']:,}원</b>  ({s['change_rate']:+.1f}%)\n"
        f"\n{entry_block}",
        s["code"], s["name"]
    )

# ============================================================
# 주가 조회
# ============================================================
def get_stock_price(code: str) -> dict:
    url    = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
    params = {"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":code}
    data   = _safe_get(url, "FHKST01010100", params)
    o      = data.get("output", {})
    price  = int(o.get("stck_prpr", 0))
    if not price: return {}
    today_vol = int(o.get("acml_vol", 0))
    return {
        "code": code, "name": o.get("hts_kor_isnm",""),
        "price": price, "change_rate": float(o.get("prdy_ctrt",0)),
        "volume_ratio": get_real_volume_ratio(code, today_vol),
        "today_vol": today_vol,
        "high": int(o.get("stck_hgpr",0)),
        "ask_qty": int(o.get("askp_rsqn1",0)),
        "bid_qty": int(o.get("bidp_rsqn1",0)),
        "prev_close": int(o.get("stck_sdpr",0)),
        "bstp_code": o.get("bstp_cls_code",""),
    }

def get_upper_limit_stocks() -> list:
    data = _safe_get(f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/chgrate-pcls-100",
                     "FHPST01700000", {
        "FID_COND_MRKT_DIV_CODE":"J","FID_COND_SCR_DIV_CODE":"20170","FID_INPUT_ISCD":"0000",
        "FID_RANK_SORT_CLS_CODE":"0","FID_INPUT_CNT_1":"30","FID_PRC_CLS_CODE":"0",
        "FID_INPUT_PRICE_1":"1000","FID_INPUT_PRICE_2":"","FID_VOL_CNT":"100000",
        "FID_TRGT_CLS_CODE":"0","FID_TRGT_EXLS_CLS_CODE":"0","FID_DIV_CLS_CODE":"0",
        "FID_RSFL_RATE1":"5","FID_RSFL_RATE2":"",
    })
    return [{"code":i.get("mksc_shrn_iscd",""),"name":i.get("hts_kor_isnm",""),
             "price":int(i.get("stck_prpr",0)),"change_rate":float(i.get("prdy_ctrt",0)),
             "volume_ratio":float(i.get("vol_inrt",0) or 0), "market":"KRX"}
            for i in data.get("output",[]) if i.get("mksc_shrn_iscd")]

def get_volume_surge_stocks() -> list:
    data = _safe_get(f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/volume-rank",
                     "FHPST01710000", {
        "FID_COND_MRKT_DIV_CODE":"J","FID_COND_SCR_DIV_CODE":"20171","FID_INPUT_ISCD":"0000",
        "FID_DIV_CLS_CODE":"0","FID_BLNG_CLS_CODE":"0","FID_TRGT_CLS_CODE":"111111111",
        "FID_TRGT_EXLS_CLS_CODE":"000000","FID_INPUT_PRICE_1":"1000",
        "FID_INPUT_PRICE_2":"","FID_VOL_CNT":"30","FID_INPUT_DATE_1":"",
    })
    return [{"code":i.get("mksc_shrn_iscd",""),"name":i.get("hts_kor_isnm",""),
             "price":int(i.get("stck_prpr",0)),"change_rate":float(i.get("prdy_ctrt",0)),
             "volume_ratio":float(i.get("vol_inrt",0) or 0), "market":"KRX"}
            for i in data.get("output",[]) if i.get("mksc_shrn_iscd")]

# ── NXT (넥스트레이드) 조회 ──
# NXT는 KRX와 동일 종목이 복수 시장에서 거래됨
# 시장 구분: NX (넥스트레이드), 오전 8:00~오후 8:00 운영
NXT_OPEN  = dtime(8, 0)
NXT_CLOSE = dtime(20, 0)

def is_nxt_open() -> bool:
    """NXT는 주말/공휴일 제외, 08:00~20:00"""
    if is_holiday(): return False
    return NXT_OPEN <= datetime.now().time() <= NXT_CLOSE

def get_nxt_surge_stocks() -> list:
    """NXT 급등/거래량 상위 종목 조회"""
    try:
        data = _safe_get(f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/volume-rank",
                         "FHPST01710000", {
            "FID_COND_MRKT_DIV_CODE":"NX","FID_COND_SCR_DIV_CODE":"20171",
            "FID_INPUT_ISCD":"0000","FID_DIV_CLS_CODE":"0","FID_BLNG_CLS_CODE":"0",
            "FID_TRGT_CLS_CODE":"111111111","FID_TRGT_EXLS_CLS_CODE":"000000",
            "FID_INPUT_PRICE_1":"1000","FID_INPUT_PRICE_2":"",
            "FID_VOL_CNT":"20","FID_INPUT_DATE_1":"",
        })
        return [{"code":i.get("mksc_shrn_iscd",""),"name":i.get("hts_kor_isnm",""),
                 "price":int(i.get("stck_prpr",0)),"change_rate":float(i.get("prdy_ctrt",0)),
                 "volume_ratio":float(i.get("vol_inrt",0) or 0), "market":"NXT"}
                for i in data.get("output",[]) if i.get("mksc_shrn_iscd")]
    except Exception as e:
        print(f"⚠️ NXT 조회 오류: {e}"); return []

def get_nxt_stock_price(code: str) -> dict:
    """NXT 개별 종목 현재가 조회"""
    url    = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
    params = {"FID_COND_MRKT_DIV_CODE":"NX","FID_INPUT_ISCD":code}
    data   = _safe_get(url, "FHKST01010100", params)
    o      = data.get("output", {})
    price  = int(o.get("stck_prpr", 0))
    if not price: return {}
    return {
        "code": code, "name": o.get("hts_kor_isnm",""),
        "price": price, "change_rate": float(o.get("prdy_ctrt",0)),
        "volume_ratio": float(o.get("vol_inrt",0) or 0),
        "today_vol": int(o.get("acml_vol",0)),
        "market": "NXT",
    }

def get_nxt_investor_trend(code: str) -> dict:
    """NXT 외인·기관 순매수 조회"""
    data   = _safe_get(f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-investor",
                       "FHKST01010900", {"FID_COND_MRKT_DIV_CODE":"NX","FID_INPUT_ISCD":code})
    output = data.get("output", [])
    if not output: return {}
    return {
        "foreign_net":     int(output[0].get("frgn_ntby_qty", 0)),
        "institution_net": int(output[0].get("orgn_ntby_qty", 0)),
    }

# NXT 데이터 캐시 (종목별 5분 유효)
_nxt_cache: dict = {}        # code → {data, ts}
_nxt_unavailable: set = set()  # NXT 비상장/거래없는 종목 (당일 재조회 안 함)

def get_nxt_info(code: str) -> dict:
    """
    NXT 종합 정보 (캐시 5분)
    NXT 비상장 종목은 _nxt_unavailable에 기록 → 당일 재조회 없음
    반환: {price, change_rate, volume_ratio, foreign_net, institution_net,
            vs_krx_pct, vol_surge, inv_bullish, inv_bearish}
    """
    if code in _nxt_unavailable: return {}   # 비상장 종목 빠르게 스킵
    cached = _nxt_cache.get(code)
    if cached and time.time() - cached["ts"] < 300:
        return cached["data"]
    if not is_nxt_open():
        return {}
    try:
        p = get_nxt_stock_price(code)
        if not p:
            _nxt_unavailable.add(code)       # 조회 실패 → 비상장으로 간주
            return {}
        inv = {}
        try: inv = get_nxt_investor_trend(code)
        except: pass

        krx = get_stock_price(code)
        krx_price = krx.get("price", 0)
        vs_krx = round((p["price"] - krx_price) / krx_price * 100, 2) if krx_price else 0

        f_net = inv.get("foreign_net", 0)
        i_net = inv.get("institution_net", 0)

        result = {
            "price":           p["price"],
            "change_rate":     p["change_rate"],
            "volume_ratio":    p["volume_ratio"],
            "foreign_net":     f_net,
            "institution_net": i_net,
            "vs_krx_pct":      vs_krx,
            "vol_surge":       p["volume_ratio"] >= 3.0,
            "inv_bullish":     f_net > 0 and i_net > 0,
            "inv_bearish":     f_net < 0 and i_net < 0,
            "nxt_listed":      True,          # NXT 상장 확인됨
        }
        _nxt_cache[code] = {"data": result, "ts": time.time()}
        return result
    except Exception as e:
        print(f"⚠️ NXT 정보 오류 ({code}): {e}")
        _nxt_unavailable.add(code)
        return {}

def nxt_score_bonus(code: str) -> tuple:
    """
    NXT 데이터 기반 신호 보정값 반환
    returns: (score_delta, reason_str)
    score_delta > 0 → 강화 / < 0 → 감점
    """
    if not is_nxt_open(): return 0, ""
    nxt = get_nxt_info(code)
    if not nxt: return 0, ""

    delta, reasons = 0, []

    if nxt["inv_bullish"]:
        delta += 15
        reasons.append(f"🔵 NXT 외인+기관 동시매수 ({nxt['foreign_net']:+,}주)")
    elif nxt["foreign_net"] > 0:
        delta += 7
        reasons.append(f"🔵 NXT 외인 순매수 ({nxt['foreign_net']:+,}주)")
    elif nxt["institution_net"] > 0:
        delta += 5
        reasons.append(f"🔵 NXT 기관 순매수 ({nxt['institution_net']:+,}주)")

    if nxt["inv_bearish"]:
        delta -= 15
        reasons.append(f"🔴 NXT 외인+기관 동시매도 ({nxt['foreign_net']:+,}주)")
    elif nxt["foreign_net"] < -3000:
        delta -= 10
        reasons.append(f"🔴 NXT 외인 대량매도 ({nxt['foreign_net']:+,}주)")

    if nxt["vol_surge"] and delta > 0:
        delta += 5
        reasons.append(f"🔵 NXT 거래량 급증 ({nxt['volume_ratio']:.1f}배)")

    if nxt["vs_krx_pct"] > 1.0:
        delta += 5
        reasons.append(f"🔵 NXT 프리미엄 +{nxt['vs_krx_pct']:.1f}% (내일 갭상 주목)")
    elif nxt["vs_krx_pct"] < -1.0:
        delta -= 5
        reasons.append(f"🔴 NXT 디스카운트 {nxt['vs_krx_pct']:.1f}%")

    return delta, "\n".join(reasons)

def get_investor_trend(code: str) -> dict:
    data   = _safe_get(f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-investor",
                       "FHKST01010900", {"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":code})
    output = data.get("output",[])
    if not output: return {}
    return {"foreign_net":   int(output[0].get("frgn_ntby_qty",0)),
            "institution_net": int(output[0].get("orgn_ntby_qty",0))}

# ============================================================
# 섹터 모멘텀
# ============================================================
def get_sector_stocks_from_kis(code: str) -> list:
    """
    동일 업종 종목 조회 (3단계 폴백)

    1순위: 거래량 급증 + 상한가 근접 종목 중 업종코드 직접 매칭
           → 실제 장 중 움직이는 동업종 종목만 추출 (가장 실용적)
    2순위: 등락률 상위 조회 전체에서 업종코드 필터
    3순위: 그래도 없으면 빈 결과 (업종 조회 실패 표시)
    """
    cached = _sector_cache.get(code)
    if cached and time.time() - cached["ts"] < 3600:
        return cached["stocks"]
    try:
        # 1단계: 해당 종목의 업종 코드·이름 조회
        data      = _safe_get(f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price",
                              "FHKST01010100",
                              {"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":code})
        o         = data.get("output", {})
        bstp_code = o.get("bstp_cls_code", "")
        bstp_name = o.get("bstp_kor_isnm", "") or "동일업종"

        if not bstp_code:
            _sector_cache[code] = {"sector":"업종미상","stocks":[],"ts":time.time()}
            return []

        stocks = []

        # 2단계: 거래량 상위 + 상한가 근접 종목을 각각 업종코드 조회해서 매칭
        # → "지금 같이 움직이는 종목"을 실시간으로 찾는 가장 실용적인 방법
        candidates = {}
        try:
            for s in get_volume_surge_stocks() + get_upper_limit_stocks():
                if s.get("code") and s["code"] != code:
                    candidates[s["code"]] = s["name"]
        except: pass

        for peer_code, peer_name in list(candidates.items())[:30]:
            if len(stocks) >= 8: break
            try:
                d2 = _safe_get(f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price",
                               "FHKST01010100",
                               {"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":peer_code})
                peer_bstp = d2.get("output",{}).get("bstp_cls_code","")
                if peer_bstp == bstp_code:
                    stocks.append((peer_code, peer_name))
                time.sleep(0.1)
            except: continue

        # 3단계: 위에서도 없으면 등락률 상위 전체에서 한번 더 시도
        if not stocks:
            try:
                data3 = _safe_get(
                    f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/chgrate-pcls-100",
                    "FHPST01700000",
                    {"FID_COND_MRKT_DIV_CODE":"J","FID_COND_SCR_DIV_CODE":"20170",
                     "FID_INPUT_ISCD":"0000","FID_RANK_SORT_CLS_CODE":"0",
                     "FID_INPUT_CNT_1":"50","FID_PRC_CLS_CODE":"0",
                     "FID_INPUT_PRICE_1":"500","FID_INPUT_PRICE_2":"",
                     "FID_VOL_CNT":"1000","FID_TRGT_CLS_CODE":"0",
                     "FID_TRGT_EXLS_CLS_CODE":"0","FID_DIV_CLS_CODE":"0",
                     "FID_RSFL_RATE1":"-30","FID_RSFL_RATE2":"30"}
                )
                for i in data3.get("output",[]):
                    peer_code = i.get("mksc_shrn_iscd","")
                    if not peer_code or peer_code == code: continue
                    try:
                        d4 = _safe_get(f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price",
                                       "FHKST01010100",
                                       {"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":peer_code})
                        if d4.get("output",{}).get("bstp_cls_code","") == bstp_code:
                            stocks.append((peer_code, i.get("hts_kor_isnm","")))
                        time.sleep(0.1)
                    except: continue
                    if len(stocks) >= 6: break
            except: pass

        _sector_cache[code] = {"sector": bstp_name, "stocks": stocks, "ts": time.time()}
        print(f"  🏭 [{bstp_name}] 동업종 {len(stocks)}개 조회됨 (업종코드: {bstp_code})")
        return stocks
    except Exception as e:
        print(f"⚠️ 섹터 조회 오류 ({code}): {e}")
        return []

# ============================================================
# ① 가격 상관관계 기반 동적 테마 탐지
# ============================================================
def calc_price_correlation(code_a: str, code_b: str) -> float:
    """두 종목의 최근 N일 수익률 피어슨 상관계수 계산"""
    try:
        items_a = get_daily_data(code_a, CORR_LOOKBACK + 5)
        items_b = get_daily_data(code_b, CORR_LOOKBACK + 5)
        closes_a = [i["close"] for i in items_a[-CORR_LOOKBACK:] if i["close"]]
        closes_b = [i["close"] for i in items_b[-CORR_LOOKBACK:] if i["close"]]
        n = min(len(closes_a), len(closes_b))
        if n < 10:
            return 0.0
        # 일간 수익률로 변환
        rets_a = [(closes_a[i] - closes_a[i-1]) / closes_a[i-1] for i in range(1, n)]
        rets_b = [(closes_b[i] - closes_b[i-1]) / closes_b[i-1] for i in range(1, n)]
        n2 = len(rets_a)
        mean_a = sum(rets_a) / n2
        mean_b = sum(rets_b) / n2
        cov  = sum((rets_a[i]-mean_a)*(rets_b[i]-mean_b) for i in range(n2)) / n2
        std_a = math.sqrt(sum((r-mean_a)**2 for r in rets_a) / n2)
        std_b = math.sqrt(sum((r-mean_b)**2 for r in rets_b) / n2)
        if std_a == 0 or std_b == 0:
            return 0.0
        return round(cov / (std_a * std_b), 3)
    except:
        return 0.0

def build_correlation_theme(code: str, name: str) -> list:
    """
    급등 종목과 상관관계 높은 종목들을 탐색 → 동적 테마 구성
    거래량 상위 + 상한가 상위에서 후보 선정 → 상관계수 0.7 이상만 채택
    캐시 1시간
    """
    cache_key = f"corr_{code}"
    cached = _sector_cache.get(cache_key)
    if cached and time.time() - cached["ts"] < 3600:
        return cached["peers"]

    try:
        candidates = {}
        for s in (get_volume_surge_stocks() + get_upper_limit_stocks()):
            c = s.get("code","")
            if c and c != code:
                candidates[c] = s.get("name", c)
        # 최대 20개 후보만 계산 (API 부하 방지)
        peers = []
        for peer_code, peer_name in list(candidates.items())[:20]:
            corr = calc_price_correlation(code, peer_code)
            if corr >= CORR_MIN:
                peers.append((peer_code, peer_name, corr))
            time.sleep(0.05)
        peers.sort(key=lambda x: x[2], reverse=True)
        result = [(c, n) for c, n, _ in peers[:6]]
        _sector_cache[cache_key] = {"peers": result, "ts": time.time()}
        if result:
            print(f"  🔗 [{name}] 가격 상관관계 종목 {len(result)}개: {[n for _,n in result]}")
        return result
    except Exception as e:
        print(f"⚠️ 상관관계 계산 오류 ({code}): {e}")
        return []

# ============================================================
# ② 뉴스 공동언급 기반 테마 자동 확장
# ============================================================
_news_cooccur = {}   # code → {peers: {code: count}, last_headline: str, ts}

def extract_stock_mentions(headlines: list, known_stocks: dict) -> dict:
    """
    뉴스 헤드라인에서 종목명 추출 → 같은 기사에 함께 언급된 종목 쌍 기록
    known_stocks: {code: name}
    """
    cooccur = {}   # code → {peer_code: count}
    for headline in headlines:
        mentioned = [code for code, name in known_stocks.items() if name in headline]
        if len(mentioned) < 2:
            continue
        for i, c1 in enumerate(mentioned):
            for c2 in mentioned[i+1:]:
                cooccur.setdefault(c1, {}).setdefault(c2, 0)
                cooccur[c1][c2] += 1
                cooccur.setdefault(c2, {}).setdefault(c1, 0)
                cooccur[c2][c1] += 1
    return cooccur

def update_news_cooccur(headlines: list):
    """뉴스 공동언급 DB 업데이트 (뉴스 스캔 시마다 호출)"""
    global _news_cooccur
    # 알려진 종목 풀 구성 (THEME_MAP + 동적 후보군)
    known = {}
    for ti in THEME_MAP.values():
        for c, n in ti["stocks"]:
            known[c] = n
    for c, info in _dynamic_candidates.items():
        known[c] = info["name"]

    new_pairs = extract_stock_mentions(headlines, known)
    for code, peers in new_pairs.items():
        if code not in _news_cooccur:
            _news_cooccur[code] = {"peers": {}, "ts": time.time()}
        for peer_code, cnt in peers.items():
            prev = _news_cooccur[code]["peers"].get(peer_code, 0)
            _news_cooccur[code]["peers"][peer_code] = prev + cnt
        _news_cooccur[code]["ts"] = time.time()

    # 파일 저장 (장 마감 후 분석용)
    try:
        with open(NEWS_COOCCUR_FILE, "w") as f:
            json.dump(_news_cooccur, f, ensure_ascii=False, indent=2)
    except: pass

def get_news_cooccur_peers(code: str) -> list:
    """뉴스에서 함께 언급된 횟수 상위 종목 반환 [(code, name, count)]"""
    if code not in _news_cooccur:
        return []
    peers_raw = _news_cooccur[code]["peers"]
    # 알려진 종목 이름 역매핑
    name_map = {}
    for ti in THEME_MAP.values():
        for c, n in ti["stocks"]: name_map[c] = n
    for c, info in _dynamic_candidates.items():
        name_map[c] = info["name"]

    result = sorted(
        [(c, name_map.get(c, c), cnt) for c, cnt in peers_raw.items() if cnt >= 2],
        key=lambda x: x[2], reverse=True
    )
    return result[:6]

# ============================================================
# ③ THEME_MAP 자동 업데이트 (급등 감지 시 호출)
# ============================================================
def auto_update_theme(code: str, name: str, trigger: str = "급등"):
    """
    급등/상한가/중기눌림목 포착 시 해당 종목의 상관관계 종목을 동적 테마로 등록
    trigger: 왜 이 테마가 만들어졌는지 (알림에 표시됨)
    """
    global _dynamic_theme_map

    # 이미 등록된 테마면 스킵
    for tk, ti in _dynamic_theme_map.items():
        if code in [c for c, _ in ti["stocks"]]:
            return

    # 가격 상관관계 + 뉴스 공동언급 통합
    corr_peers  = build_correlation_theme(code, name)        # [(code, name)]
    news_peers_raw = get_news_cooccur_peers(code)            # [(code, name, count)]
    news_peers  = [(c, n) for c, n, _ in news_peers_raw]

    # 합산 (중복 제거)
    seen = set()
    all_peers = []
    for c, n in (corr_peers + news_peers):
        if c not in seen and c != code:
            seen.add(c); all_peers.append((c, n))

    if not all_peers:
        return

    # 이유 설명 생성
    reasons = []
    if corr_peers:
        reasons.append(f"가격 상관관계 {len(corr_peers)}종목")
    if news_peers:
        reasons.append(f"뉴스 공동언급 {len(news_peers)}종목")
    reason_str = " + ".join(reasons)

    theme_key = f"auto_{code}_{datetime.now().strftime('%m%d')}"
    _dynamic_theme_map[theme_key] = {
        "desc":   f"{name} 연관 테마 ({trigger})",
        "reason": reason_str,
        "stocks": [(code, name)] + all_peers,
        "ts":     time.time(),
    }
    print(f"  🆕 동적 테마 생성: [{theme_key}] {name} + {[n for _,n in all_peers]} ({reason_str})")

    # 파일 저장
    try:
        with open(DYNAMIC_THEME_FILE, "w") as f:
            json.dump({k: {**v, "stocks": v["stocks"]} for k,v in _dynamic_theme_map.items()},
                      f, ensure_ascii=False, indent=2)
    except: pass

def load_dynamic_themes():
    """장 시작 시 동적 테마 파일 복원"""
    global _dynamic_theme_map
    try:
        with open(DYNAMIC_THEME_FILE, "r") as f:
            data = json.load(f)
        # 오늘 날짜 것만 유지
        today = datetime.now().strftime("%m%d")
        _dynamic_theme_map = {k: v for k, v in data.items() if today in k or
                               time.time() - v.get("ts", 0) < 86400}
        if _dynamic_theme_map:
            print(f"  📂 동적 테마 {len(_dynamic_theme_map)}개 복원")
    except: pass


# ============================================================
# 🏗️ 실질 섹터 분류 (4레이어 가중 스코어)
# ============================================================
_dart_related_cache: dict = {}   # code → {related: [...], ts}
_real_sector_cache:  dict = {}   # code → {sector_id, score, peers, ts}

def get_dart_related_stocks(code: str) -> list:
    """
    DART 지분공시에서 모자/관계회사 종목 조회.
    반환: [(code, name, reason)] 
    예: [("005930", "삼성전자", "최대주주")]
    캐시 24시간 (지분관계는 자주 안 바뀜)
    """
    if not DART_API_KEY:
        return []
    cached = _dart_related_cache.get(code)
    if cached and time.time() - cached["ts"] < 86400:
        return cached["related"]
    try:
        # DART 기업개황에서 corp_code 조회
        url = "https://opendart.fss.or.kr/api/company.json"
        resp = _session.get(url, params={"crtfc_key": DART_API_KEY, "stock_code": code}, timeout=10)
        if resp.status_code != 200:
            _dart_related_cache[code] = {"related": [], "ts": time.time()}
            return []
        corp_code = resp.json().get("corp_code", "")
        if not corp_code:
            _dart_related_cache[code] = {"related": [], "ts": time.time()}
            return []

        # 최대주주 현황 조회 (대표적 지분 공시)
        url2  = "https://opendart.fss.or.kr/api/hyslrSttus.json"
        year  = datetime.now().strftime("%Y")
        resp2 = _session.get(url2, params={
            "crtfc_key": DART_API_KEY, "corp_code": corp_code,
            "bsns_year": year, "reprt_code": "11011"  # 사업보고서
        }, timeout=10)
        items = resp2.json().get("list", []) if resp2.status_code == 200 else []

        related = []
        for item in items:
            relate_stock = item.get("stock_code", "").strip()
            relate_name  = item.get("nm", "").strip()
            relate_type  = item.get("relate", "").strip()
            if relate_stock and relate_stock != code:
                related.append((relate_stock, relate_name, relate_type or "관계회사"))
        _dart_related_cache[code] = {"related": related[:10], "ts": time.time()}
        return related[:10]
    except:
        _dart_related_cache[code] = {"related": [], "ts": time.time()}
        return []

def calc_real_sector_score(code_a: str, code_b: str,
                            name_a: str = "", name_b: str = "") -> dict:
    """
    두 종목 간 실질 섹터 연관성 스코어 (0~100).
    4가지 레이어 가중 합산:
      ① 주가 상관계수 0.7↑  → 40점
      ② 당일 동반 상승 중   → 30점
      ③ DART 지분 연결      → 20점
      ④ 뉴스 동시 언급      → 10점
    반환: {"score": int, "layers": dict, "label": str}
    """
    score   = 0
    layers  = {}

    # ① 주가 상관계수 (60일)
    try:
        corr = calc_price_correlation(code_a, code_b)
        if corr >= 0.7:
            pts = int(40 * min((corr - 0.7) / 0.3 + 0.5, 1.0))  # 0.7→20점, 1.0→40점
            score += pts
            layers["상관계수"] = f"{corr:.2f} (+{pts}점)"
        elif corr >= 0.5:
            score += 10
            layers["상관계수"] = f"{corr:.2f} (+10점)"
    except: pass

    # ② 당일 동반 상승 (실시간)
    try:
        pa = get_stock_price(code_a)
        pb = get_stock_price(code_b)
        cr_a = pa.get("change_rate", 0)
        cr_b = pb.get("change_rate", 0)
        if cr_a >= 2.0 and cr_b >= 2.0:
            score += 30
            layers["동반상승"] = f"+{cr_a:.1f}%/+{cr_b:.1f}% (+30점)"
        elif cr_a >= 1.0 and cr_b >= 1.0:
            score += 15
            layers["동반상승"] = f"+{cr_a:.1f}%/+{cr_b:.1f}% (+15점)"
    except: pass

    # ③ DART 지분 관계
    try:
        related = get_dart_related_stocks(code_a)
        dart_hit = next((r for r in related if r[0] == code_b), None)
        if dart_hit:
            score += 20
            layers["DART지분"] = f"{dart_hit[2]} (+20점)"
    except: pass

    # ④ 뉴스 동시 언급
    try:
        cooccur_a = _news_cooccur.get(code_a, {}).get("peers", {})
        if code_b in cooccur_a and cooccur_a[code_b] >= 2:
            score += 10
            layers["뉴스동시언급"] = f"{cooccur_a[code_b]}회 (+10점)"
    except: pass

    if score >= 60:   label = "🔴 강한 연관"
    elif score >= 40: label = "🟠 보통 연관"
    elif score >= 20: label = "🟡 약한 연관"
    else:             label = "⬜ 연관 없음"

    return {"score": score, "layers": layers, "label": label}

def get_real_sector_peers(code: str, name: str) -> list:
    """
    현재 스캔 중인 종목 후보군에서 실질 섹터 스코어 40 이상인 종목 반환.
    캐시 30분.
    반환: [(code, name, score, label)]
    """
    cache_key = f"real_{code}"
    cached = _real_sector_cache.get(cache_key)
    if cached and time.time() - cached["ts"] < 1800:
        return cached["peers"]

    try:
        candidates = {}
        for s in (get_volume_surge_stocks() + get_upper_limit_stocks()):
            c = s.get("code","")
            if c and c != code:
                candidates[c] = s.get("name", c)

        # DART 관계회사도 후보에 추가
        for dart_code, dart_name, _ in get_dart_related_stocks(code):
            if dart_code not in candidates:
                candidates[dart_code] = dart_name

        peers = []
        for peer_code, peer_name in list(candidates.items())[:25]:
            rs = calc_real_sector_score(code, peer_code, name, peer_name)
            if rs["score"] >= 40:
                peers.append((peer_code, peer_name, rs["score"], rs["label"]))
            time.sleep(0.05)

        peers.sort(key=lambda x: x[2], reverse=True)
        result = peers[:8]
        _real_sector_cache[cache_key] = {"peers": result, "ts": time.time()}
        if result:
            print(f"  🏗️ [{name}] 실질섹터: {[(n, s) for _, n, s, _ in result[:3]]}")
        return result
    except Exception as e:
        print(f"⚠️ 실질섹터 계산 오류 ({code}): {e}")
        return []

def get_theme_sector_stocks(code: str) -> tuple:
    """
    종목 코드 → (테마명, [(peer_code, peer_name)]) 반환
    우선순위:
      1. 하드코딩 THEME_MAP
      2. 동적 테마맵 (가격상관관계 + 뉴스 공동언급으로 자동 생성)
      3. KIS 업종코드 매칭
    각 소스를 병합해서 가장 풍부한 정보 제공
    """
    peers_all = {}   # code → (name, source, reason)

    # 1. THEME_MAP
    theme_name = "기타업종"
    for tk, ti in THEME_MAP.items():
        if code in [c for c,_ in ti["stocks"]]:
            theme_name = tk
            for c, n in ti["stocks"]:
                if c != code:
                    peers_all[c] = (n, "테마", tk)
            break

    # 2. 동적 테마맵
    dyn_reason = ""
    for tk, ti in _dynamic_theme_map.items():
        if code in [c for c,_ in ti["stocks"]]:
            if theme_name == "기타업종":
                theme_name = ti["desc"]
            dyn_reason = ti.get("reason", "")
            for c, n in ti["stocks"]:
                if c != code and c not in peers_all:
                    peers_all[c] = (n, "동적테마", ti["desc"])
            break

    # 3. KIS 업종코드 매칭 (나머지 채우기용)
    kis_peers = get_sector_stocks_from_kis(code)
    for c, n in kis_peers:
        if c not in peers_all:
            peers_all[c] = (n, "업종코드", "")

    peers = [(c, n) for c, (n, src, rsn) in peers_all.items()]
    return theme_name, peers, peers_all   # peers_all은 소스 정보 포함

def calc_sector_momentum(code: str, name: str) -> dict:
    theme_name, peers, peers_all = get_theme_sector_stocks(code)
    if not peers:
        return {"bonus":0,"theme":theme_name,"summary":"","rising":[],"flat":[],"detail":[],"sources":{}}
    results = []
    for peer_code, peer_name in peers[:8]:
        try:
            cur = get_stock_price(peer_code)
            if not cur: continue
            cr, vr = cur.get("change_rate",0), cur.get("volume_ratio",0)
            src, rsn = peers_all.get(peer_code, (peer_name, "업종코드", ""))[1:]
            results.append({"code":peer_code,"name":peer_name,"change_rate":cr,"volume_ratio":vr,
                             "strong":cr>=2.0 and vr>=2.0,"weak":cr>=2.0,
                             "source":src, "reason":rsn})
            time.sleep(0.15)
        except: continue
    if not results:
        return {"bonus":0,"theme":theme_name,"summary":"","rising":[],"flat":[],"detail":[],"sources":{}}
    total, react_cnt = len(results), sum(1 for r in results if r["weak"])
    strong_cnt = sum(1 for r in results if r["strong"])
    react_ratio = react_cnt / total
    bonus = (15 if react_ratio>=1.0 else 10 if react_ratio>=0.5 else 5 if react_cnt>=1 else 0)
    if strong_cnt >= 2: bonus += 5
    rising = [r for r in results if r["weak"]]
    flat   = [r for r in results if not r["weak"]]
    if bonus == 0:            summary = f"📉 섹터 반응 없음 ({theme_name}: {react_cnt}/{total})"
    elif react_ratio >= 1.0:  summary = f"🔥 섹터 전체 동반 상승! ({theme_name}: {react_cnt}/{total})"
    elif react_ratio >= 0.5:  summary = f"✅ 섹터 절반 이상 반응 ({theme_name}: {react_cnt}/{total})"
    else:                     summary = f"🟡 섹터 일부 반응 ({theme_name}: {react_cnt}/{total})"

    # ── NXT 섹터 동향 보정 ──
    # 섹터 내 종목들의 NXT 외인 동향이 일치할수록 신뢰도 ↑
    if is_nxt_open() and results:
        nxt_bullish_cnt = 0
        nxt_bearish_cnt = 0
        for r in results[:4]:   # API 부하 제한: 최대 4종목
            try:
                nxt = get_nxt_info(r["code"])
                if nxt.get("inv_bullish"): nxt_bullish_cnt += 1
                elif nxt.get("inv_bearish"): nxt_bearish_cnt += 1
                time.sleep(0.1)
            except: continue
        if nxt_bullish_cnt >= 2:
            bonus = min(bonus + 10, 30)
            summary += f"  🔵 NXT {nxt_bullish_cnt}종목 외인+기관 매수"
        elif nxt_bearish_cnt >= 2:
            bonus = max(bonus - 10, 0)
            summary += f"  🔴 NXT {nxt_bearish_cnt}종목 외인+기관 매도"

    # 소스별 분류 (알림에 '왜 묶였는지' 표시용)
    sources = {}
    for r in results:
        src = r.get("source","업종코드")
        sources.setdefault(src, []).append(r["name"])

    return {"bonus":bonus,"theme":theme_name,"summary":summary,
            "rising":rising,"flat":flat,"detail":results,"sources":sources}

# ============================================================
# 💾 저장·복원
# ============================================================
# ============================================================
# 📋 신호 로그 저장 (모든 신호 유형 공통)
# ============================================================
SIGNAL_LOG_FILE = "signal_log.json"   # 모든 신호 추적 (신규)

def _is_real_trade(rec: dict) -> bool:
    """
    실제 진입한 거래만 통계에 포함할지 판단.
    actual_entry=False(명시적 미진입) 또는 진입미달 상태는 제외.
    """
    if rec.get("actual_entry") is False:
        return False
    if rec.get("entry_miss") is not None:
        return False
    if "진입미달" in str(rec.get("exit_reason", "")):
        return False
    return True

def save_signal_log(stock: dict):
    """
    알림 발송된 모든 신호를 로그에 저장
    - UPPER_LIMIT / NEAR_UPPER / SURGE / EARLY_DETECT / MID_PULLBACK / ENTRY_POINT
    - 이후 track_signal_results()가 목표가·손절가 도달 여부를 자동 체크
    """
    try:
        data = {}
        try:
            with open(SIGNAL_LOG_FILE, "r") as f: data = json.load(f)
        except: pass

        code     = stock["code"]
        sig_type = stock.get("signal_type", "UNKNOWN")
        # 같은 종목이 이미 추적 중이면 업데이트하지 않음 (중복 방지)
        log_key  = f"{code}_{stock.get('detected_at', datetime.now()).strftime('%Y%m%d%H%M')}"

        # 신호 발생 시 활성화된 기능 플래그 기록
        indic    = stock.get("indic", {})
        position = stock.get("position", {})
        feature_flags = {
            "rsi":              indic.get("rsi", 50),
            "ma_aligned":       indic.get("ma", {}).get("aligned"),
            "bb_breakout":      indic.get("bb", {}).get("breakout", False),
            "sector_bonus":     stock.get("sector_info", {}).get("bonus", 0),
            "regime":           stock.get("regime", "normal"),
            "earnings_risk":    stock.get("earnings_risk", "none"),
            "position_pct":     position.get("pct", 8.0),
            "nxt_delta":        stock.get("nxt_delta", 0),
            "indic_score_adj":  indic.get("score_adj", 0),
        }

        data[log_key] = {
            "log_key":      log_key,
            "code":         code,
            "name":         stock["name"],
            "signal_type":  sig_type,
            "score":        stock.get("score", 0),
            "grade":        stock.get("grade", "B"),
            "sector_bonus": stock.get("sector_info", {}).get("bonus", 0),
            "sector_theme": stock.get("sector_info", {}).get("theme", ""),
            "detect_date":  datetime.now().strftime("%Y%m%d"),
            "detect_time":  datetime.now().strftime("%H:%M:%S"),
            "detect_price": stock["price"],
            "change_at_detect": stock.get("change_rate", 0),
            "volume_ratio": stock.get("volume_ratio", 0),
            "rsi_at_signal": indic.get("rsi", 50),
            "entry_price":  stock.get("entry_price", stock["price"]),
            "stop_price":   stock.get("stop_loss", 0),
            "target_price": stock.get("target_price", 0),
            "atr_used":     stock.get("atr_used", False),
            "feature_flags": feature_flags,
            # ── 이론 추적 결과 (봇 자동 계산 → auto_tune 학습용) ──
            "status":            "추적중",   # 봇 추적 상태
            "exit_price":        0,
            "exit_date":         "",
            "exit_time":         "",
            "pnl_pct":           0.0,        # 이론 수익률 (봇 학습 기준)
            "exit_reason":       "",
            "max_price":         stock["price"],
            "min_price":         stock["price"],
            # ── 실제 진입 결과 (사용자 입력 → 내 수익 통계용) ──
            "actual_entry":      None,       # True=진입함 / False=진입안함 / None=미확인
            "actual_pnl":        None,       # 실제 수익률 (사용자 /result 입력)
            "actual_exit_date":  "",
            "skip_reason":       "",         # 진입 못 한 이유 (/skip으로 기록)
        }
        with open(SIGNAL_LOG_FILE, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  💾 신호 저장: {stock['name']} [{sig_type}] 진입{stock.get('entry_price',0):,} 손절{stock.get('stop_loss',0):,} 목표{stock.get('target_price',0):,}")
    except Exception as e:
        print(f"⚠️ 신호 저장 오류: {e}")

# 하위 호환성 유지 (기존 EARLY_LOG_FILE도 동시에 저장)
def save_early_detect(stock: dict):
    save_signal_log(stock)
    try:
        data = {}
        try:
            with open(EARLY_LOG_FILE, "r") as f: data = json.load(f)
        except: pass
        code = stock["code"]
        if code not in data:
            data[code] = {
                "code": code, "name": stock["name"],
                "detect_time":  datetime.now().strftime("%H:%M"),
                "detect_date":  datetime.now().strftime("%Y%m%d"),
                "detect_price": stock["price"],
                "change_at_detect": stock["change_rate"],
                "volume_ratio": stock["volume_ratio"],
                "entry_price":  stock["entry_price"],
                "stop_price":   stock["stop_loss"],
                "target_price": stock["target_price"],
                "signal_type":  stock.get("signal_type", "EARLY_DETECT"),
                "sector_bonus": stock.get("sector_info", {}).get("bonus", 0),
                "status": "추적중", "pnl_pct": 0, "exit_price": 0, "exit_date": "",
            }
            with open(EARLY_LOG_FILE, "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ EARLY 저장 오류: {e}")

# ============================================================
# 📡 신호 결과 자동 추적 (매 스캔마다 호출)
# ============================================================
# 추적 제한 시간: 신호 발생 후 최대 N일
TRACK_MAX_DAYS   = 5
# 시간 초과 시 당일 종가 기준으로 결과 기록
TRACK_TIMEOUT_RESULT = "시간초과"

_tracking_notified = set()   # 이미 결과 알림 보낸 log_key

# ============================================================
# ✍️ 수동 매도 결과 입력 보조
# ============================================================
def _send_pending_result_reminder():
    """
    장 마감 시 추적 중인 종목 중 오늘 신호이면서 아직 결과 미입력인 것들을
    텔레그램으로 알려줌.

    ※ 입력하지 않으면?
      - 목표가/손절가 도달 시 자동 확정 (계속 감시)
      - TRACK_MAX_DAYS(5일) 경과 시 그날 종가 기준으로 자동 기록
      - NXT 상장 종목은 20:00까지 자동 감시 후 기록
    """
    try:
        data = {}
        try:
            with open(SIGNAL_LOG_FILE, "r") as f: data = json.load(f)
        except: return

        today   = datetime.now().strftime("%Y%m%d")
        pending = [
            v for v in data.values()
            if v.get("status") == "추적중"
            and v.get("detect_date") == today
        ]
        if not pending:
            return

        # NXT 운영 중이면 NXT 마감 후 발송 (20:05), KRX만이면 15:30 후 발송
        # 이 함수는 두 시점 모두에서 호출되므로 중복 방지 플래그 사용
        reminder_key = f"reminder_{today}"
        if reminder_key in _tracking_notified:
            return
        _tracking_notified.add(reminder_key)

        nxt_running = is_nxt_open()
        timing_note = ("🔵 NXT 마감(20:00) 후에도 NXT 상장 종목은 자동 감시됩니다."
                       if nxt_running else
                       "💡 내일도 자동 추적됩니다. (최대 5일)")

        msg = (f"✍️ <b>오늘 결과 미입력 종목</b>  ({len(pending)}건)\n"
               f"━━━━━━━━━━━━━━━\n"
               f"실제 매도하셨다면 /result 로 입력해주세요.\n"
               f"입력 안 하셔도 봇이 자동 추적합니다.\n\n")

        sig_labels = {
            "UPPER_LIMIT":"상한가","NEAR_UPPER":"상한가근접","SURGE":"급등",
            "EARLY_DETECT":"조기포착","MID_PULLBACK":"중기눌림목",
            "ENTRY_POINT":"단기눌림목","STRONG_BUY":"강력매수",
        }
        for v in pending:
            entry = v.get("entry_price", 0)
            code  = v.get("code", "")
            # NXT 먼저, 없으면 KRX 현재가
            try:
                if is_nxt_open() and is_nxt_listed(code):
                    cur_p = get_nxt_stock_price(code).get("price", 0) or get_stock_price(code).get("price", 0)
                else:
                    cur_p = get_stock_price(code).get("price", 0)
                cur_pnl = round((cur_p - entry) / entry * 100, 1) if entry and cur_p else 0
                pnl_emoji = "🟢" if cur_pnl >= 0 else "🔴"
                cur_str = f"  현재 {cur_p:,}원  {pnl_emoji}{cur_pnl:+.1f}%"
            except:
                cur_str = ""
            sig = sig_labels.get(v.get("signal_type",""), "")
            msg += (f"• <b>{v['name']}</b>  {sig}\n"
                    f"  진입 {entry:,}원  손절 {v.get('stop_price',0):,}  목표 {v.get('target_price',0):,}\n"
                    f"{cur_str}\n"
                    f"  → <code>/result {v['name']} +수익률</code>\n\n")

        msg += f"━━━━━━━━━━━━━━━\n{timing_note}"
        send(msg)

    except Exception as e:
        print(f"⚠️ 결과 입력 알림 오류: {e}")

def track_signal_results():
    """
    추적 중인 모든 신호의 현재가를 조회해서
    ① 목표가 도달 → 수익 확정
    ② 손절가 도달 → 손실 확정
    ③ N일 경과   → 현재가 기준 결과 기록
    결과 확정 시 텔레그램 알림 발송
    """
    try:
        data = {}
        try:
            with open(SIGNAL_LOG_FILE, "r") as f: data = json.load(f)
        except: return

        updated = False
        today   = datetime.now().strftime("%Y%m%d")

        for log_key, rec in data.items():
            if rec.get("status") != "추적중": continue
            if log_key in _tracking_notified:  continue

            code         = rec["code"]
            entry        = rec.get("entry_price", 0)
            stop         = rec.get("stop_price",  0)
            target       = rec.get("target_price", 0)
            detect_date  = rec.get("detect_date", today)

            if not entry or not stop or not target: continue

            # 경과 일수 계산
            try:
                elapsed_days = (datetime.strptime(today, "%Y%m%d") -
                                datetime.strptime(detect_date, "%Y%m%d")).days
            except:
                elapsed_days = 0

            # 현재가 조회 — KRX 장중이면 KRX, 마감 후면 NXT 사용
            try:
                if is_market_open():
                    cur   = get_stock_price(code)
                    price = cur.get("price", 0)
                elif is_nxt_open():
                    # KRX 마감 후 NXT 가격으로 추적 (15:30~20:00)
                    nxt_cur = get_nxt_stock_price(code)
                    price   = nxt_cur.get("price", 0)
                    if not price:          # NXT 거래 없으면 KRX 종가
                        cur   = get_stock_price(code)
                        price = cur.get("price", 0)
                else:
                    continue   # 모든 시장 마감
                if not price: continue
            except:
                continue

            # 최고가·최저가 업데이트 (MDD 계산용)
            rec["max_price"] = max(rec.get("max_price", price), price)
            rec["min_price"] = min(rec.get("min_price", price), price)
            updated = True

            # ── 분할 청산 가이드 (목표가 도달 전 중간 알림) ──
            if entry and target:
                pnl_now  = (price - entry) / entry * 100
                half_pct = (target - entry) / entry * 100 / 2   # 목표의 절반
                partial_key = f"{log_key}_partial"
                if (pnl_now >= half_pct
                        and partial_key not in _tracking_notified
                        and half_pct > 3.0):
                    _tracking_notified.add(partial_key)
                    inv_info = ""
                    try:
                        inv   = get_investor_trend(code)
                        f_net = inv.get("foreign_net", 0)
                        i_net = inv.get("institution_net", 0)
                        if f_net > 0 and i_net > 0:
                            inv_info = "\n  ✅ 외국인+기관 순매수 — 홀딩 우호적"
                        elif f_net < 0 or i_net < 0:
                            inv_info = "\n  ⚠️ 외국인/기관 매도 전환 — 익절 고려"
                    except: pass
                    send_with_chart_buttons(
                        f"💡 <b>[분할 청산 타이밍]</b>\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"🟢 <b>{rec['name']}</b>  <code>{code}</code>\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"현재 <b>+{pnl_now:.1f}%</b>  (목표의 {pnl_now/((target-entry)/entry*100)*100:.0f}%)\n"
                        f"📍 현재가: <b>{price:,}원</b>\n"
                        f"🏆 목표가: <b>{target:,}원</b>  (+{(target-entry)/entry*100:.1f}%)\n"
                        f"{inv_info}\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"💡 절반 익절 후 나머지 홀딩 전략 고려",
                        code, rec["name"]
                    )
                    print(f"  💡 분할 청산 가이드: {rec['name']} +{pnl_now:.1f}%")

            # ── ② 트레일링 스탑 ──
            # 목표가 도달 후 최고가에서 -3% 하락하면 자동 청산 (더 먹기)
            trailing_key = f"{log_key}_trailing"
            if rec.get("trailing_active"):
                trail_stop = rec.get("trailing_stop", target)
                if price > rec.get("max_price", price):
                    # 최고가 갱신 → 트레일링 스탑 끌어올리기
                    new_trail = int(price * 0.97 / 10) * 10
                    if new_trail > trail_stop:
                        rec["trailing_stop"] = new_trail
                if price <= rec["trailing_stop"]:
                    exit_reason = "트레일링스탑"
                    exit_price  = price
                    pnl_pct     = round((exit_price - entry) / entry * 100, 2) if entry else 0
                    status      = "수익" if pnl_pct > 0 else "본전"
                    rec["status"]      = status
                    rec["exit_price"]  = exit_price
                    rec["exit_date"]   = today
                    rec["exit_time"]   = datetime.now().strftime("%H:%M:%S")
                    rec["pnl_pct"]     = pnl_pct
                    rec["exit_reason"] = exit_reason
                    _tracking_notified.add(log_key)
                    updated = True
                    _send_tracking_result(rec)
                    print(f"  📊 트레일링 청산: {rec['name']} {pnl_pct:+.1f}%")
                    continue

            # ── 결과 판정 ──
            exit_reason = None
            exit_price  = price

            if price >= target:
                # 목표가 도달 → 트레일링 스탑 모드 전환 (바로 청산 안 함)
                if not rec.get("trailing_active"):
                    rec["trailing_active"] = True
                    rec["trailing_stop"]   = int(price * 0.97 / 10) * 10
                    updated = True
                    if trailing_key not in _tracking_notified:
                        _tracking_notified.add(trailing_key)
                        send_with_chart_buttons(
                            f"🎯 <b>[목표가 도달 → 트레일링 모드]</b>\n"
                            f"━━━━━━━━━━━━━━━\n"
                            f"🟢 <b>{rec['name']}</b>  <code>{code}</code>\n"
                            f"현재가 <b>{price:,}원</b>  목표가 {target:,}원\n"
                            f"━━━━━━━━━━━━━━━\n"
                            f"✅ 목표 달성! 추가 상승 시 자동으로 더 먹습니다\n"
                            f"📉 고점 대비 -3% 하락 시 자동 청산",
                            code, rec["name"]
                        )
                continue   # 트레일링 모드로 계속 추적
            elif price <= stop:
                exit_reason = "손절가"
            elif elapsed_days >= TRACK_MAX_DAYS:
                exit_reason = TRACK_TIMEOUT_RESULT

            if not exit_reason:
                continue   # 아직 추적 중

            # ── 이론 수익률 계산 (봇 학습용) ──
            pnl_pct = round((exit_price - entry) / entry * 100, 2) if entry else 0
            status  = "수익" if pnl_pct > 0 else ("손실" if pnl_pct < 0 else "본전")

            # 이론 결과 저장 (항상)
            rec["status"]      = status
            rec["exit_price"]  = exit_price
            rec["exit_date"]   = today
            rec["exit_time"]   = datetime.now().strftime("%H:%M:%S")
            rec["pnl_pct"]     = pnl_pct        # 이론 수익률
            rec["exit_reason"] = exit_reason

            # 실제 진입 여부가 None(미확인)인 경우 → 진입 확인 요청 알림
            if rec.get("actual_entry") is None and exit_reason != TRACK_TIMEOUT_RESULT:
                _request_actual_entry_confirm(rec)

            _tracking_notified.add(log_key)

            # ── 결과 알림 ──
            _send_tracking_result(rec)
            print(f"  📊 추적 완료: {rec['name']} {pnl_pct:+.1f}% ({exit_reason}) [이론]")

            # 연속 손절 카운터 업데이트 (긴급 튜닝용)
            global _consecutive_loss_count
            if pnl_pct <= 0:
                _consecutive_loss_count += 1
                _consecutive_win_count  = 0   # 손실 시 연속 수익 카운터 리셋
                if _consecutive_loss_count >= EMERGENCY_TUNE_THRESHOLD:
                    print(f"  🚨 연속 손절 {_consecutive_loss_count}회 → 긴급 튜닝 실행")
                    auto_tune(notify=True)
                    _consecutive_loss_count = 0
            else:
                _consecutive_loss_count = 0
                _consecutive_win_count  += 1
                # ③ 연속 수익 공격 모드
                if _consecutive_win_count >= WIN_STREAK_THRESHOLD:
                    old_n = _dynamic["min_score_normal"]
                    old_s = _dynamic["min_score_strict"]
                    if old_n > 50:
                        _dynamic["min_score_normal"] = max(old_n - 3, 50)
                        _dynamic["min_score_strict"] = max(old_s - 3, 60)
                        print(f"  🔥 연속 수익 {_consecutive_win_count}회 → 공격 모드: 최소점수 {old_n}→{_dynamic['min_score_normal']}")
                        try:
                            send(f"🔥 <b>연속 수익 {_consecutive_win_count}회!</b>\n"
                                 f"신호 기준 완화: {old_n}→{_dynamic['min_score_normal']}점\n"
                                 f"더 많은 신호를 포착합니다")
                        except: pass

        if updated:
            with open(SIGNAL_LOG_FILE, "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            # tracker 피드백 즉시 갱신
            load_tracker_feedback()

    except Exception as e:
        _log_error("track_signal_results", e, critical=True)


def _send_tracking_result(rec: dict):
    """결과 확정 텔레그램 알림 + 손절 원인 분석"""
    pnl      = rec["pnl_pct"]
    reason   = rec["exit_reason"]
    sig_type = rec.get("signal_type", "")
    name     = rec["name"]
    code     = rec["code"]
    entry    = rec.get("entry_price", 0)
    exit_p   = rec["exit_price"]
    max_p    = rec.get("max_price", exit_p)
    min_p    = rec.get("min_price", exit_p)
    theme    = rec.get("sector_theme", "")
    bonus    = rec.get("sector_bonus", 0)

    if reason == "목표가":
        emoji = "🎯✅"; title = "목표가 달성!"
    elif reason == "손절가":
        emoji = "🛡🔴"; title = "손절가 도달"
    elif reason == TRACK_TIMEOUT_RESULT:
        emoji = "⏱"; title = f"{TRACK_MAX_DAYS}일 경과 결과"
    else:
        emoji = "📊"; title = "결과 확정"

    pnl_emoji = "✅" if pnl > 0 else ("🔴" if pnl < 0 else "➖")
    sig_labels = {
        "UPPER_LIMIT":"상한가", "NEAR_UPPER":"상한가근접",
        "SURGE":"급등", "EARLY_DETECT":"조기포착",
        "MID_PULLBACK":"중기눌림목", "ENTRY_POINT":"단기눌림목",
        "STRONG_BUY":"강력매수",
    }
    sig_label = sig_labels.get(sig_type, sig_type)
    theme_tag = f"\n🏭 테마: {theme} (+{bonus}점)" if bonus > 0 else "\n🔍 단독 상승"
    mdd = round((min_p - entry) / entry * 100, 1) if entry else 0

    # ── 손절 원인 분석 ──
    cause_block = ""
    if reason == "손절가":
        causes = []
        try:
            cur = get_stock_price(code)
            p   = cur.get("price", 0)
            if p:
                inv = get_investor_trend(code)
                f_net = inv.get("foreign_net", 0)
                i_net = inv.get("institution_net", 0)
                vr    = cur.get("volume_ratio", 0)

                if f_net < -5000:  causes.append(f"🔴 외국인 대량 매도 ({f_net:+,}주)")
                elif f_net < 0:    causes.append(f"🟠 외국인 순매도 ({f_net:+,}주)")
                if i_net < -3000:  causes.append(f"🔴 기관 대량 매도 ({i_net:+,}주)")
                elif i_net < 0:    causes.append(f"🟠 기관 순매도 ({i_net:+,}주)")
                if vr and vr < 0.5: causes.append(f"📉 거래량 급감 ({vr:.1f}배 — 매수세 소멸)")
                if vr and vr > 5:   causes.append(f"🌊 거래량 급증 속 하락 (세력 매도 가능성)")
                if not causes:      causes.append("⚠️ 특이 원인 미감지 (기술적 손절)")
        except: causes = ["조회 실패"]
        cause_block = "\n━━━━━━━━━━━━━━━\n🔍 <b>손절 원인 분석</b>\n" + "\n".join(f"  {c}" for c in causes) + "\n"

    # ── 분할 청산 가이드 (수익 시) ──
    profit_guide = ""
    if pnl > 0 and reason == "목표가" and entry and target:
        target = rec.get("target_price", exit_p)
        r2 = int(entry + (target - entry) * 1.5)
        profit_guide = (
            f"\n━━━━━━━━━━━━━━━\n"
            f"💡 <b>추가 보유 고려</b>\n"
            f"  현재 +{pnl:.1f}% 달성\n"
            f"  R2 목표: {r2:,}원  (+{(r2-entry)/entry*100:.1f}%)\n"
            f"  → 절반 익절 후 나머지 홀딩 전략\n"
        )

    send_with_chart_buttons(
        f"{emoji} <b>[자동 추적 결과]</b>  {title}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{pnl_emoji} <b>{name}</b>  <code>{code}</code>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"신호: {sig_label}  |  감지: {rec.get('detect_date','')} {rec.get('detect_time','')}\n"
        f"{theme_tag}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"진입가:  <b>{entry:,}원</b>\n"
        f"청산가:  <b>{exit_p:,}원</b>  ({reason})\n"
        f"최고가:  {max_p:,}원  |  최저가: {min_p:,}원\n"
        f"최대낙폭: {mdd:+.1f}%\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{pnl_emoji} <b>수익률: {pnl:+.1f}%</b>"
        f"{cause_block}"
        f"{profit_guide}",
        code, name
    )

    # ── 손절 시 재진입 감시 등록 (KRX + NXT 모두) ──
    if reason == "손절가" and is_any_market_open():
        try:
            # KRX 장중이면 KRX 가격, 마감 후 NXT 있으면 NXT 가격
            if is_market_open():
                cur_price = get_stock_price(code).get("price", 0)
            elif is_nxt_open():
                cur_price = get_nxt_stock_price(code).get("price", 0) or get_stock_price(code).get("price", 0)
            else:
                cur_price = 0
            if cur_price:
                _reentry_watch[code] = {
                    "name":        name,
                    "stop_price":  cur_price,
                    "entry":       rec.get("entry_price", 0),
                    "stop":        rec.get("stop_price", 0),
                    "target":      rec.get("target_price", 0),
                    "signal_type": rec.get("signal_type", ""),
                    "ts":          time.time(),
                }
                print(f"  🔄 재진입 감시 등록: {name} ({code}) 손절가 {cur_price:,}")
        except: pass

def check_reentry_watch():
    """
    손절 종목 재진입 감시 — 20초마다 run_scan에서 호출
    만료: 장 완전 마감(KRX only→15:30, NXT 상장→20:00) 또는 on_market_close
    조건: 손절가 대비 +3% 반등 + 거래량 1.5배 이상
    """
    if not _reentry_watch: return
    expired = []
    for code, w in list(_reentry_watch.items()):
        # 종목별 실질 마감 판단
        nxt_ok  = is_nxt_open() and is_nxt_listed(code)
        krx_ok  = is_market_open()
        if not krx_ok and not nxt_ok:
            expired.append(code); continue   # 모든 시장 마감 → 만료
        try:
            # KRX 장중이면 KRX 가격, 마감 후면 NXT 가격
            if krx_ok:
                cur   = get_stock_price(code)
                price = cur.get("price", 0)
                vr    = cur.get("volume_ratio", 0)
            else:
                cur   = get_nxt_stock_price(code)
                price = cur.get("price", 0)
                vr    = cur.get("volume_ratio", 0)
                if not price:   # NXT 거래 없으면 스킵 (마감 아님)
                    continue
            if not price: continue

            bounce = (price - w["stop_price"]) / w["stop_price"] * 100
            mkt_tag = " 🔵NXT" if not krx_ok and nxt_ok else ""
            if bounce >= REENTRY_BOUNCE_PCT and vr >= REENTRY_VOL_MIN:
                sig_labels = {"UPPER_LIMIT":"상한가","NEAR_UPPER":"상한가근접",
                              "SURGE":"급등","EARLY_DETECT":"조기포착",
                              "MID_PULLBACK":"중기눌림목","ENTRY_POINT":"단기눌림목"}
                sig = sig_labels.get(w["signal_type"], w["signal_type"])
                stop_new, target_new, sp, tp, atr = calc_stop_target(code, price)
                rr = round((target_new - price) / (price - stop_new), 1) if price > stop_new else 0
                send_with_chart_buttons(
                    f"🔄 <b>[손절 후 재진입 후보{mkt_tag}]</b>\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🟡 <b>{w['name']}</b>  <code>{code}</code>\n"
                    f"원신호: {sig}\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"📍 손절가:  {w['stop_price']:,}원\n"
                    f"📈 현재가:  <b>{price:,}원</b>  (+{bounce:.1f}% 반등)\n"
                    f"🔊 거래량:  {vr:.1f}배 (회복)\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"┌─────────────────────\n"
                    f"│ 🎯 재진입가  <b>{price:,}원</b>\n"
                    f"│ 🛡 손절가   <b>{stop_new:,}원</b>  (-{sp:.1f}%)\n"
                    f"│ 🏆 목표가   <b>{target_new:,}원</b>  (+{tp:.1f}%)\n"
                    f"│ 손익비:    {rr:.1f} : 1\n"
                    f"└─────────────────────\n"
                    f"⚠️ 손절 후 재진입 — 물타기 아님, 새 포지션으로 판단",
                    code, w["name"]
                )
                expired.append(code)
                print(f"  🔄 재진입 신호: {w['name']} {price:,} (+{bounce:.1f}%){mkt_tag}")
        except: continue
    for code in expired:
        _reentry_watch.pop(code, None)

def save_carry_stocks():
    try:
        with open(CARRY_FILE,"w") as f:
            json.dump({code: {
                "name":info["name"],"high_price":info["high_price"],
                "entry_price":info["entry_price"],"stop_loss":info["stop_loss"],
                "target_price":info["target_price"],
                "detected_at":info["detected_at"].strftime("%Y%m%d%H%M%S"),
                "carry_day":info.get("carry_day",0),
            } for code,info in _detected_stocks.items()}, f, ensure_ascii=False)
    except Exception as e: print(f"⚠️ 이월 저장 실패: {e}")

def load_carry_stocks():
    """Railway 재시작 시 추적 상태 전체 복원"""
    # ① 이월 종목 복원
    try:
        with open(CARRY_FILE,"r") as f: data = json.load(f)
        for code, info in data.items():
            carry_day = info.get("carry_day",0)
            if carry_day >= MAX_CARRY_DAYS: continue
            _detected_stocks[code] = {
                "name":info["name"],"high_price":info["high_price"],
                "entry_price":info["entry_price"],"stop_loss":info["stop_loss"],
                "target_price":info["target_price"],
                "detected_at":datetime.strptime(info["detected_at"],"%Y%m%d%H%M%S"),
                "carry_day":carry_day,
            }
        if _detected_stocks:
            print(f"📂 이월 종목 {len(_detected_stocks)}개 복원")
    except: pass

    # ② signal_log에서 추적 중 종목 복원 (이월 파일에 없는 당일 추적 종목)
    try:
        with open(SIGNAL_LOG_FILE,"r") as f: sig_data = json.load(f)
        today = datetime.now().strftime("%Y%m%d")
        restored = 0
        for rec in sig_data.values():
            code = rec.get("code","")
            if (rec.get("status") == "추적중"
                    and rec.get("detect_date") == today
                    and code not in _detected_stocks):
                _detected_stocks[code] = {
                    "name":        rec["name"],
                    "high_price":  rec.get("detect_price", 0),
                    "entry_price": rec.get("entry_price", 0),
                    "stop_loss":   rec.get("stop_price", 0),
                    "target_price":rec.get("target_price", 0),
                    "detected_at": datetime.now(),
                    "carry_day":   0,
                }
                restored += 1
        if restored:
            print(f"  📋 signal_log에서 추적 중 종목 {restored}개 추가 복원")
    except: pass

    # 복원 알림
    if _detected_stocks:
        send(f"🔄 <b>봇 재시작 — 추적 상태 복원</b>\n"
             f"📂 감시 중 종목 {len(_detected_stocks)}개\n" +
             "\n".join([f"• {v['name']} ({k})" for k,v in list(_detected_stocks.items())[:6]]) +
             ("\n  ..." if len(_detected_stocks) > 6 else "") +
             "\n\n📡 스캔 재개")

    # ③ 컴팩트 모드 복원
    _load_compact_mode()

# ============================================================
# 🧠 자동 조건 조정 엔진
# ============================================================
AUTO_TUNE_FILE   = "auto_tune_log.json"   # 조정 이력 저장
DYNAMIC_PARAMS_FILE = "dynamic_params.json"  # 조정된 파라미터 영구 저장
MIN_SAMPLES      = 5    # 20→5: 더 빠르게 반응 (적은 샘플로도 조정)

# 동적 조정 변수 (기본값 = 파라미터 원본값)
_dynamic = {
    # 조기 포착
    "early_price_min":    EARLY_PRICE_MIN,
    "early_volume_min":   EARLY_VOLUME_MIN,
    # 중기 눌림목
    "mid_surge_min_pct":  MID_SURGE_MIN_PCT,
    "mid_pullback_min":   MID_PULLBACK_MIN,
    "mid_pullback_max":   MID_PULLBACK_MAX,
    "mid_vol_recovery":   MID_VOL_RECOVERY_MIN,
    # 급등 진입
    "min_score_normal":   60,
    "min_score_strict":   70,
    # 테마 가중치 (테마 동반 시 최소 점수 완화)
    "themed_score_bonus": 0,
    # ATR 손절배수 동적 조정
    "atr_stop_mult":      ATR_STOP_MULT,
    # 시간대별 최소점수 보정 (기본 0: 보정 없음, +N: 해당 시간대 더 엄격)
    "timeslot_score_adj": {"장초반": 0, "오전": 0, "오후": 0, "장후반": 0},
    # ── 보조지표 파라미터 (auto_tune 자동 조정) ──
    "rsi_period":    14,
    "rsi_overbuy":   70.0,
    "rsi_oversell":  30.0,
    "ma_short":       5,
    "ma_mid":        20,
    "ma_long":       60,
    "bb_period":     20,
    # ── 기능별 가중치 (auto_tune이 자동 조정, 0=비활성화) ──
    "feat_w_rsi":       1.0,    # RSI 필터 가중치
    "feat_w_ma":        1.0,    # 이동평균 정배열 가중치
    "feat_w_bb":        1.0,    # 볼린저밴드 가중치
    "feat_w_sector":    1.0,    # 섹터 모멘텀 가중치
    "feat_w_nxt":       1.0,    # NXT 보정 가중치
    # ── 시장 국면 판단 ──
    "regime_mode":         "normal",   # "bull" / "normal" / "bear" / "crash"
    "regime_score_mult":   1.0,        # 신호 점수 배율 (하락장 0.7, 상승장 1.2)
    "regime_min_add":      0,          # 최소 점수 추가 보정
    # ── 포지션 사이징 ──
    "position_base_pct":   8.0,        # 기본 투자비중 (%)
    # ── 손익비 동적 조정 ──
    "atr_target_mult":     ATR_TARGET_MULT,   # 목표가 배수 (변동성 따라 조정)
    # ── 포트폴리오 동시 신호 관리 ──
    "max_same_sector":     2,          # 같은 섹터 동시 신호 최대
}

# 긴급 튜닝: 연속 손절/수익 카운터
_consecutive_loss_count: int = 0
_consecutive_win_count:  int = 0   # ③ 연속 수익 카운터
EMERGENCY_TUNE_THRESHOLD   = 3     # 연속 손절 N회 → 즉시 조건 강화
WIN_STREAK_THRESHOLD       = 4     # 연속 수익 N회 → 공격 모드 진입

def _save_dynamic_params():
    """
    현재 _dynamic 값을 파일에 저장
    → Railway 재시작 후에도 조정값 유지
    """
    try:
        with open(DYNAMIC_PARAMS_FILE, "w") as f:
            json.dump(_dynamic, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ dynamic_params 저장 실패: {e}")

def _load_dynamic_params():
    """
    저장된 _dynamic 값을 불러와서 현재 세션에 복원
    파일 없으면 기본값 유지
    """
    global _dynamic, _early_price_min_dynamic, _early_volume_min_dynamic
    try:
        with open(DYNAMIC_PARAMS_FILE) as f:
            saved = json.load(f)
        # 저장된 값 중 유효한 키만 덮어씀 (새로 추가된 키는 기본값 유지)
        for k, v in saved.items():
            if k in _dynamic:
                _dynamic[k] = v
        _early_price_min_dynamic  = _dynamic["early_price_min"]
        _early_volume_min_dynamic = _dynamic["early_volume_min"]
        print(f"  🔧 동적 파라미터 복원 완료 (min_score={_dynamic['min_score_normal']}점, "
              f"atr_stop={_dynamic['atr_stop_mult']})")
    except FileNotFoundError:
        print("  🔧 dynamic_params.json 없음 → 기본값 사용")
    except Exception as e:
        print(f"  ⚠️ dynamic_params 복원 실패: {e}")

def load_tracker_feedback():
    """기존 함수 — 하위 호환용. auto_tune()을 호출"""
    auto_tune(notify=False)

def _get_timeslot(detect_time: str) -> str:
    """
    신호 발생 시간(HH:MM:SS 또는 HH:MM)을 4개 구간으로 분류
    장초반 09:00~10:00 / 오전 10:00~12:00 / 오후 12:00~14:00 / 장후반 14:00~15:30
    """
    try:
        t = detect_time[:5]   # "HH:MM"
        h, m = int(t[:2]), int(t[3:])
        minutes = h * 60 + m
        if minutes < 10 * 60:              return "장초반"   # ~10:00
        elif minutes < 12 * 60:            return "오전"     # 10:00~12:00
        elif minutes < 14 * 60:            return "오후"     # 12:00~14:00
        else:                              return "장후반"   # 14:00~
    except:
        return "기타"

def analyze_timeslot_winrate(completed: list) -> dict:
    """
    완료 신호를 시간대별로 분류해 승률·평균 수익률 반환
    반환: {"장초반": {"win":N,"total":N,"avg":F}, ...}
    """
    slots = {"장초반": [], "오전": [], "오후": [], "장후반": [], "기타": []}
    for r in completed:
        t = r.get("detect_time", r.get("detected_at", ""))
        slot = _get_timeslot(t)
        slots[slot].append(r["pnl_pct"])
    result = {}
    for slot, pnls in slots.items():
        if not pnls: continue
        result[slot] = {
            "win":   sum(1 for p in pnls if p > 0),
            "total": len(pnls),
            "avg":   round(sum(pnls) / len(pnls), 1),
            "rate":  round(sum(1 for p in pnls if p > 0) / len(pnls) * 100, 0),
        }
    return result

def analyze_loss_pattern(completed: list) -> str:
    """
    손실 종목들의 공통 패턴 분석 → 텍스트 요약 반환
    분석 항목: 손절 이유 분포 / 시간대 / 신호유형 / 테마여부
    """
    losses = [r for r in completed if r.get("pnl_pct", 0) <= 0]
    if len(losses) < 3:
        return ""

    lines = [f"🔴 <b>손실 패턴 분석</b>  ({len(losses)}건)"]

    # 손절 이유 분포
    reasons = {}
    for r in losses:
        ex = r.get("exit_reason", "?")
        reasons[ex] = reasons.get(ex, 0) + 1
    reason_str = "  ".join([f"{k}:{v}건" for k, v in sorted(reasons.items(), key=lambda x: -x[1])])
    lines.append(f"  청산 이유: {reason_str}")

    # 시간대별 손실 집중도
    slot_counts = {}
    for r in losses:
        t = r.get("detect_time", r.get("detected_at", ""))
        slot = _get_timeslot(t)
        slot_counts[slot] = slot_counts.get(slot, 0) + 1
    worst_slot = max(slot_counts, key=slot_counts.get) if slot_counts else None
    if worst_slot:
        lines.append(f"  손실 집중 시간대: {worst_slot} ({slot_counts[worst_slot]}건)")

    # 신호 유형별 손실
    type_counts = {}
    for r in losses:
        t = r.get("signal_type", "기타")
        type_counts[t] = type_counts.get(t, 0) + 1
    worst_type = max(type_counts, key=type_counts.get) if type_counts else None
    if worst_type:
        type_labels = {"UPPER_LIMIT":"상한가","NEAR_UPPER":"상한가근접","SURGE":"급등",
                       "EARLY_DETECT":"조기포착","MID_PULLBACK":"중기눌림목",
                       "ENTRY_POINT":"단기눌림목","STRONG_BUY":"강력매수"}
        lines.append(f"  손실 많은 신호: {type_labels.get(worst_type, worst_type)} ({type_counts[worst_type]}건)")

    # 단독 vs 테마 손실 비율
    solo_loss   = sum(1 for r in losses if not r.get("sector_bonus", 0))
    themed_loss = sum(1 for r in losses if r.get("sector_bonus", 0))
    if solo_loss + themed_loss > 0:
        lines.append(f"  단독:{solo_loss}건  테마동반:{themed_loss}건")

    return "\n".join(lines)

def auto_tune(notify: bool = True):
    """
    signal_log.json 기반으로 신호 유형별 성과를 분석해서
    조건을 자동으로 조정. 장 마감마다 호출.

    조정 원칙:
      - 승률 < 40%  → 조건 강화 (더 까다롭게)
      - 승률 > 70%  → 조건 완화 (더 많이 잡기)
      - 40~70%      → 유지
      - 샘플 < MIN_SAMPLES(5건) 이면 조정 안 함
      - 연속 손절 3회 이상 → 긴급 즉시 강화
      - 시간대별 승률 낮은 구간 → 해당 구간 최소점수 상향
      - ATR 손절배수 동적 조정
    """
    global _dynamic, _early_price_min_dynamic, _early_volume_min_dynamic
    global _consecutive_loss_count

    try:
        data = {}
        try:
            with open(SIGNAL_LOG_FILE, "r") as f: data = json.load(f)
        except: return

        # auto_tune은 이론 데이터 전부 사용 (미진입 포함 — 봇 조건 최적화용)
        completed = [v for v in data.values()
                     if v.get("status") in ["수익", "손실", "본전"]]
        if len(completed) < MIN_SAMPLES:
            return

        changes = []

        # ── 신호 유형별 승률 계산 ──
        by_type = {}
        for v in completed:
            t = v.get("signal_type", "기타")
            by_type.setdefault(t, []).append(v)

        # ── ① 긴급 튜닝: 연속 손절 3회 이상 ──
        recent = sorted(completed, key=lambda x: x.get("exit_date","") + x.get("exit_time",""))[-5:]
        recent_loss_streak = 0
        for r in reversed(recent):
            if r.get("pnl_pct", 0) <= 0:
                recent_loss_streak += 1
            else:
                break
        if recent_loss_streak >= EMERGENCY_TUNE_THRESHOLD:
            old_n = _dynamic["min_score_normal"]
            old_s = _dynamic["min_score_strict"]
            _dynamic["min_score_normal"] = min(old_n + 8, 85)
            _dynamic["min_score_strict"] = min(old_s + 8, 90)
            changes.append(f"🚨 <b>긴급 튜닝</b>: 연속 손절 {recent_loss_streak}회\n"
                           f"   최소점수 즉시 강화: {old_n}→{_dynamic['min_score_normal']}점")

        # ── ② EARLY_DETECT 조정 ──
        early_recs = by_type.get("EARLY_DETECT", [])
        if len(early_recs) >= MIN_SAMPLES:
            rate = sum(1 for r in early_recs if r["pnl_pct"] > 0) / len(early_recs)
            old_p = _dynamic["early_price_min"]
            old_v = _dynamic["early_volume_min"]
            if rate < 0.40:
                _dynamic["early_price_min"]  = min(old_p + 2.0, 18.0)
                _dynamic["early_volume_min"] = min(old_v + 2.0, 18.0)
                changes.append(f"🔍 조기포착 조건 강화 (승률 {rate*100:.0f}%)\n"
                                f"   가격 {old_p}→{_dynamic['early_price_min']}%  "
                                f"거래량 {old_v}→{_dynamic['early_volume_min']}배")
            elif rate > 0.70:
                _dynamic["early_price_min"]  = max(old_p - 1.0, 7.0)
                _dynamic["early_volume_min"] = max(old_v - 1.0, 7.0)
                changes.append(f"🔍 조기포착 조건 완화 (승률 {rate*100:.0f}%)\n"
                                f"   가격 {old_p}→{_dynamic['early_price_min']}%  "
                                f"거래량 {old_v}→{_dynamic['early_volume_min']}배")
            _early_price_min_dynamic  = _dynamic["early_price_min"]
            _early_volume_min_dynamic = _dynamic["early_volume_min"]

        # ── ③ MID_PULLBACK 조정 ──
        mid_recs = by_type.get("MID_PULLBACK", [])
        if len(mid_recs) >= MIN_SAMPLES:
            rate      = sum(1 for r in mid_recs if r["pnl_pct"] > 0) / len(mid_recs)
            old_surge = _dynamic["mid_surge_min_pct"]
            old_min   = _dynamic["mid_pullback_min"]
            old_max   = _dynamic["mid_pullback_max"]
            if rate < 0.40:
                _dynamic["mid_surge_min_pct"] = min(old_surge + 3.0, 25.0)
                _dynamic["mid_pullback_min"]  = min(old_min + 2.0, 15.0)
                _dynamic["mid_pullback_max"]  = max(old_max - 5.0, 30.0)
                changes.append(f"🏆 중기눌림목 조건 강화 (승률 {rate*100:.0f}%)\n"
                                f"   1차급등 {old_surge}→{_dynamic['mid_surge_min_pct']}%\n"
                                f"   눌림범위 {old_min}~{old_max}→"
                                f"{_dynamic['mid_pullback_min']}~{_dynamic['mid_pullback_max']}%")
            elif rate > 0.70:
                _dynamic["mid_surge_min_pct"] = max(old_surge - 2.0, 10.0)
                _dynamic["mid_pullback_min"]  = max(old_min - 2.0, 8.0)
                changes.append(f"🏆 중기눌림목 조건 완화 (승률 {rate*100:.0f}%)\n"
                                f"   1차급등 {old_surge}→{_dynamic['mid_surge_min_pct']}%")

        # ── ④ 최소 점수 조정 ──
        if len(completed) >= MIN_SAMPLES:
            rate  = sum(1 for r in completed if r["pnl_pct"] > 0) / len(completed)
            old_n = _dynamic["min_score_normal"]
            old_s = _dynamic["min_score_strict"]
            if rate < 0.40:
                _dynamic["min_score_normal"] = min(old_n + 5, 80)
                _dynamic["min_score_strict"] = min(old_s + 5, 85)
                changes.append(f"⭐ 최소 점수 강화: {old_n}→{_dynamic['min_score_normal']}점")
            elif rate > 0.70:
                _dynamic["min_score_normal"] = max(old_n - 3, 50)
                _dynamic["min_score_strict"] = max(old_s - 3, 60)
                changes.append(f"⭐ 최소 점수 완화: {old_n}→{_dynamic['min_score_normal']}점")

        # ── ⑤ ATR 손절배수 동적 조정 ──
        # 손절가 도달 비율이 높으면 손절이 너무 타이트 → 배수 늘리기
        # 만료(timeout) 비율이 높으면 손절이 너무 루즈 → 배수 줄이기
        stop_hits   = sum(1 for r in completed if r.get("exit_reason") == "손절가")
        timeout_hit = sum(1 for r in completed if r.get("exit_reason") in ["만료", "timeout", TRACK_TIMEOUT_RESULT])
        old_atr     = _dynamic["atr_stop_mult"]
        if len(completed) >= MIN_SAMPLES:
            stop_ratio    = stop_hits   / len(completed)
            timeout_ratio = timeout_hit / len(completed)
            if stop_ratio > 0.50 and old_atr < 2.5:
                _dynamic["atr_stop_mult"] = round(min(old_atr + 0.2, 2.5), 1)
                changes.append(f"📐 ATR 손절배수 확대: {old_atr}→{_dynamic['atr_stop_mult']} (손절 너무 빈번)")
            elif timeout_ratio > 0.40 and old_atr > 1.0:
                _dynamic["atr_stop_mult"] = round(max(old_atr - 0.2, 1.0), 1)
                changes.append(f"📐 ATR 손절배수 축소: {old_atr}→{_dynamic['atr_stop_mult']} (손절 너무 느슨)")

        # ── ⑥ 시간대별 승률 분석 → 낮은 구간 최소점수 상향 ──
        slot_stats = analyze_timeslot_winrate(completed)
        new_slot_adj = dict(_dynamic["timeslot_score_adj"])
        slot_changes = []
        for slot, st in slot_stats.items():
            if st["total"] < 3: continue
            old_adj = new_slot_adj.get(slot, 0)
            if st["rate"] < 35 and old_adj < 20:
                new_slot_adj[slot] = old_adj + 5
                slot_changes.append(f"{slot}(승률{st['rate']:.0f}%→+{new_slot_adj[slot]}점)")
            elif st["rate"] > 70 and old_adj > 0:
                new_slot_adj[slot] = max(old_adj - 3, 0)
                slot_changes.append(f"{slot}(승률{st['rate']:.0f}%→점수 완화)")
        if slot_changes:
            _dynamic["timeslot_score_adj"] = new_slot_adj
            changes.append(f"🕐 시간대별 점수 조정: {', '.join(slot_changes)}")

        # ── ⑦ 단독 vs 테마 격차 분석 ──
        solo_recs   = [r for r in completed if not r.get("sector_bonus", 0)]
        themed_recs = [r for r in completed if r.get("sector_bonus", 0)]
        if len(solo_recs) >= 3 and len(themed_recs) >= 3:
            solo_rate   = sum(1 for r in solo_recs   if r["pnl_pct"] > 0) / len(solo_recs)
            themed_rate = sum(1 for r in themed_recs if r["pnl_pct"] > 0) / len(themed_recs)
            gap         = themed_rate - solo_rate
            old_bonus   = _dynamic["themed_score_bonus"]
            if gap > 0.20:
                _dynamic["themed_score_bonus"] = min(old_bonus + 5, 20)
                changes.append(f"🏭 테마 동반 우대 강화\n"
                                f"   격차 {gap*100:.0f}%p → 보너스 {old_bonus}→{_dynamic['themed_score_bonus']}점\n"
                                f"   (단독 {solo_rate*100:.0f}%  테마 {themed_rate*100:.0f}%)")
            elif gap < 0.05:
                _dynamic["themed_score_bonus"] = max(old_bonus - 3, 0)

        # ── ⑧ 목표가 배수 동적 조정 ──
        # 목표가 도달 비율이 낮고 만료 많으면 → 목표가 너무 높음 → 배수 축소
        target_hits = sum(1 for r in completed if r.get("exit_reason") == "목표가")
        if len(completed) >= MIN_SAMPLES:
            tgt_ratio = target_hits / len(completed)
            old_tgt   = _dynamic.get("atr_target_mult", ATR_TARGET_MULT)
            if tgt_ratio < 0.20 and old_tgt > 2.0:
                _dynamic["atr_target_mult"] = round(max(old_tgt - 0.3, 2.0), 1)
                changes.append(f"🎯 목표가 배수 축소: {old_tgt}→{_dynamic['atr_target_mult']} (목표 도달률 {tgt_ratio*100:.0f}%)")
            elif tgt_ratio > 0.50 and old_tgt < 5.0:
                _dynamic["atr_target_mult"] = round(min(old_tgt + 0.2, 5.0), 1)
                changes.append(f"🎯 목표가 배수 확대: {old_tgt}→{_dynamic['atr_target_mult']} (목표 도달률 양호)")

        # ── ⑨ 포지션 기본비중 자동 조정 ──
        # 전체 승률 높으면 비중 살짝 상향, 낮으면 하향
        if len(completed) >= MIN_SAMPLES * 2:
            overall_win = sum(1 for r in completed if r["pnl_pct"] > 0) / len(completed)
            old_pos = _dynamic.get("position_base_pct", 8.0)
            if overall_win > 0.65 and old_pos < 15.0:
                _dynamic["position_base_pct"] = round(min(old_pos + 0.5, 15.0), 1)
                changes.append(f"💰 포지션 비중 상향: {old_pos}%→{_dynamic['position_base_pct']}% (승률 {overall_win*100:.0f}%)")
            elif overall_win < 0.40 and old_pos > 4.0:
                _dynamic["position_base_pct"] = round(max(old_pos - 1.0, 4.0), 1)
                changes.append(f"💰 포지션 비중 하향: {old_pos}%→{_dynamic['position_base_pct']}% (승률 저조)")

        # ── ⑪ 스킵 패턴 학습 ──
        # ── 진입가 미달 패턴 분석 → entry_pullback_ratio 자동 조정 ──
        # "진입미달_상승이탈": 진입가가 너무 낮게 설정 → 비율 올리기 (더 공격적)
        # "진입미달_기간만료": 진입가가 너무 높게 설정 → 비율 낮추기 (더 보수적)
        # "진입가변경": 같은 종목 재포착 반복 → 변동성 큰 상황, 비율 완화
        miss_recs = [r for r in data.values()
                     if r.get("status") in ["진입미달", "진입가변경"]
                     and r.get("detect_date", "") >= (
                         datetime.now() - timedelta(days=30)
                     ).strftime("%Y%m%d")]

        if len(miss_recs) >= 5:
            surge_miss   = sum(1 for r in miss_recs if "상승이탈"   in str(r.get("exit_reason","")))
            expire_miss  = sum(1 for r in miss_recs if "기간만료"   in str(r.get("exit_reason","")))
            reentry_miss = sum(1 for r in miss_recs if "진입가변경" in str(r.get("exit_reason","")))
            total_miss   = len(miss_recs)
            old_ratio    = _dynamic.get("entry_pullback_ratio", ENTRY_PULLBACK_RATIO)

            if surge_miss / total_miss >= 0.5:
                # 절반 이상이 상승이탈 → 진입가 너무 낮음 → 비율 올리기 (진입가를 현재가에 더 가깝게)
                new_ratio = round(min(old_ratio + 0.05, 0.7), 2)
                if new_ratio != old_ratio:
                    _dynamic["entry_pullback_ratio"] = new_ratio
                    changes.append(
                        f"📈 진입가 비율 상향: {old_ratio:.2f}→{new_ratio:.2f} "
                        f"(상승이탈 {surge_miss}/{total_miss}건 — 진입가 너무 낮았음)"
                    )
            elif expire_miss / total_miss >= 0.6:
                # 60% 이상이 기간만료 → 진입가 너무 높음 → 비율 낮추기 (진입가를 더 눌림목으로)
                new_ratio = round(max(old_ratio - 0.05, 0.2), 2)
                if new_ratio != old_ratio:
                    _dynamic["entry_pullback_ratio"] = new_ratio
                    changes.append(
                        f"📉 진입가 비율 하향: {old_ratio:.2f}→{new_ratio:.2f} "
                        f"(기간만료 {expire_miss}/{total_miss}건 — 진입가 너무 높았음)"
                    )
            if reentry_miss >= 3:
                # 재포착 반복 → 변동성 큰 종목들 → 진입가 범위 완화
                new_ratio = round(max(old_ratio - 0.03, 0.2), 2)
                if new_ratio != old_ratio:
                    _dynamic["entry_pullback_ratio"] = new_ratio
                    changes.append(
                        f"🔄 재포착 반복 {reentry_miss}건 → 진입가 비율 완화: {old_ratio:.2f}→{new_ratio:.2f}"
                    )

        # 자주 스킵하는 이유가 "이미상승"이면 → entry_pullback_ratio 더 완화
        # 자주 스킵하는 이유가 "시간없음"이면 → ALERT_COOLDOWN 늘리기 (신호 집중)
        skipped_recs = [r for r in data.values() if r.get("actual_entry") is False]
        if len(skipped_recs) >= 5:
            skip_reasons = {}
            for r in skipped_recs:
                reason = r.get("skip_reason", "").strip()
                if reason: skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
            top_reason = max(skip_reasons, key=skip_reasons.get) if skip_reasons else ""
            if "이미상승" in top_reason or "상승" in top_reason:
                # 진입가가 너무 낮아서 기회를 못 잡는 패턴 → pullback 완화
                old_ratio = _dynamic.get("entry_pullback_ratio", ENTRY_PULLBACK_RATIO)
                if old_ratio > 0.15:
                    _dynamic["entry_pullback_ratio"] = round(old_ratio - 0.03, 2)
                    changes.append(f"📈 스킵패턴 학습: '이미상승' 빈번 → 진입가 비율 완화 {old_ratio:.2f}→{_dynamic['entry_pullback_ratio']:.2f}")
            # 스킵 기회비용 계산 (놓친 이론 수익 평균)
            skip_pnls = [r.get("pnl_pct", 0) for r in skipped_recs if r.get("pnl_pct")]
            if skip_pnls:
                opp_avg = sum(skip_pnls) / len(skip_pnls)
                if opp_avg > 5.0:
                    changes.append(f"💡 스킵 기회비용: 평균 {opp_avg:+.1f}% 놓치는 중 (알림 설정 점검 권장)")

        # ── ⑩ 기능별 기여도 분석 + 자동 가중치 조정 ──
        # feature_flags가 기록된 충분한 샘플이 있을 때만 분석
        feat_recs = [r for r in completed if r.get("feature_flags")]
        if len(feat_recs) >= MIN_SAMPLES * 2:
            feat_analyses = {
                "feat_w_rsi":    ("rsi",         lambda r: r.get("feature_flags",{}).get("indic_score_adj",0) != 0),
                "feat_w_ma":     ("ma_aligned",  lambda r: r.get("feature_flags",{}).get("ma_aligned") is True),
                "feat_w_bb":     ("bb_breakout", lambda r: r.get("feature_flags",{}).get("bb_breakout") is True),
                "feat_w_sector": ("sector",      lambda r: r.get("feature_flags",{}).get("sector_bonus",0) > 0),
                "feat_w_nxt":    ("nxt",         lambda r: r.get("feature_flags",{}).get("nxt_delta",0) != 0),
            }
            for feat_key, (feat_name, feat_filter) in feat_analyses.items():
                with_feat    = [r for r in feat_recs if feat_filter(r)]
                without_feat = [r for r in feat_recs if not feat_filter(r)]
                if len(with_feat) < 3 or len(without_feat) < 3:
                    continue
                win_with    = sum(1 for r in with_feat    if r["pnl_pct"] > 0) / len(with_feat)
                win_without = sum(1 for r in without_feat if r["pnl_pct"] > 0) / len(without_feat)
                avg_with    = sum(r["pnl_pct"] for r in with_feat)    / len(with_feat)
                avg_without = sum(r["pnl_pct"] for r in without_feat) / len(without_feat)
                old_w = _dynamic.get(feat_key, 1.0)
                contribution = (win_with - win_without) + (avg_with - avg_without) / 20

                if contribution < -0.15 and old_w > 0.3:
                    # 기능이 오히려 수익을 깎고 있음 → 가중치 축소
                    new_w = round(max(old_w - 0.2, 0.2), 1)
                    _dynamic[feat_key] = new_w
                    changes.append(
                        f"🔻 [{feat_name}] 기여도 저조 → 가중치 {old_w}→{new_w} "
                        f"(있을때 승률{win_with*100:.0f}% vs 없을때 {win_without*100:.0f}%)"
                    )
                elif contribution > 0.15 and old_w < 1.5:
                    # 기능이 수익에 기여 → 가중치 강화
                    new_w = round(min(old_w + 0.1, 1.5), 1)
                    _dynamic[feat_key] = new_w
                    changes.append(
                        f"🔺 [{feat_name}] 기여도 양호 → 가중치 {old_w}→{new_w} "
                        f"(있을때 승률{win_with*100:.0f}% vs 없을때 {win_without*100:.0f}%)"
                    )

        # ── ⑧ RSI 기간 자동 조정 ──
        # RSI 차단된 신호 중 이후 성공한 케이스 비율이 높으면 → 기준 완화
        if len(completed) >= MIN_SAMPLES * 2:
            blocked_ok = [r for r in completed
                          if r.get("rsi_at_signal", 50) >= _dynamic["rsi_overbuy"]
                          and r["pnl_pct"] > 0]
            all_rsi_high = [r for r in completed if r.get("rsi_at_signal", 50) >= 65]
            if len(all_rsi_high) >= 3:
                rsi_high_rate = sum(1 for r in all_rsi_high if r["pnl_pct"] > 0) / len(all_rsi_high)
                old_ob = _dynamic["rsi_overbuy"]
                if rsi_high_rate > 0.65 and old_ob < 80:
                    _dynamic["rsi_overbuy"] = min(old_ob + 2, 80)
                    changes.append(f"📊 RSI 과매수 기준 완화: {old_ob:.0f}→{_dynamic['rsi_overbuy']:.0f} (고RSI 성공률 {rsi_high_rate*100:.0f}%)")
                elif rsi_high_rate < 0.35 and old_ob > 60:
                    _dynamic["rsi_overbuy"] = max(old_ob - 2, 60)
                    changes.append(f"📊 RSI 과매수 기준 강화: {old_ob:.0f}→{_dynamic['rsi_overbuy']:.0f} (고RSI 성공률 저조)")

        # ── 조정 이력 저장 ──
        if changes:
            tune_log = {}
            try:
                with open(AUTO_TUNE_FILE, "r") as f: tune_log = json.load(f)
            except: pass
            tune_log[datetime.now().strftime("%Y%m%d_%H%M")] = {
                "changes":  changes,
                "params":   {k: v for k, v in _dynamic.items() if k != "timeslot_score_adj"},
                "samples":  len(completed),
            }
            with open(AUTO_TUNE_FILE, "w") as f:
                json.dump(tune_log, f, ensure_ascii=False, indent=2)

            if notify:
                change_text = "\n".join(changes)
                send(f"🔧 <b>조건 자동 조정 완료</b>\n"
                     f"근거: {len(completed)}건 결과 분석\n"
                     f"━━━━━━━━━━━━━━━\n"
                     f"{change_text}\n\n"
                     f"/stats 로 전체 통계 확인")
            # ★ 조정값 파일에 저장 → 재시작 후에도 유지
            _save_dynamic_params()
        else:
            print(f"  🧠 자동 조정: 변경 없음 ({len(completed)}건 분석)")

    except Exception as e:
        _log_error("auto_tune", e, critical=True)

# ============================================================
# 📊 차트 기능 (이미지 전송 + 링크)
# ============================================================
def _chart_links(code: str, name: str) -> str:
    """차트 링크 — 인라인 키보드 버튼으로 외부 브라우저 오픈"""
    # 빈 문자열 반환 (링크는 send_with_chart_buttons로 별도 처리)
    return ""

# ============================================================
# 📡 섹터 지속 모니터링
# ============================================================
def start_sector_monitor(code: str, name: str):
    if code in _sector_monitor:
        return
    _sector_monitor[code] = {
        "name": name, "known_codes": set(),
        "last_update": time.time(), "alert_count": 0, "start_ts": time.time(),
    }
    def _monitor_loop(code=code, name=name):
        while True:
            time.sleep(SECTOR_MONITOR_INTERVAL)
            info = _sector_monitor.get(code)
            if not info: break
            # NXT 포함 실질 장 마감 체크
            if not is_any_market_open():
                _sector_monitor.pop(code, None); break
            # ⑥ 동적 감시 기간: 섹터가 계속 강하면 최대 24시간까지 연장
            elapsed_h   = (time.time() - info["start_ts"]) / 3600
            alert_cnt   = info.get("alert_count", 0)
            # 알림이 많이 발생 = 테마가 살아있음 → 시간 연장
            max_hours   = min(SECTOR_MONITOR_MAX_HOURS + alert_cnt * 2, 24)
            if elapsed_h > max_hours:
                print(f"  📡 섹터 감시 종료: {info.get('name',code)} ({elapsed_h:.1f}h, 알림 {alert_cnt}회)")
                _sector_monitor.pop(code, None); break
            try:
                _sector_cache.pop(code, None)
                si = calc_sector_momentum(code, name)
                if not si.get("detail"): continue
                new_rising = [r for r in si.get("rising",[]) if r["code"] not in info["known_codes"]]
                info["known_codes"].update({r["code"] for r in si.get("detail",[])})
                if new_rising or info["alert_count"] == 0:
                    info["alert_count"] += 1
                    theme   = si.get("theme",""); rising = si.get("rising",[]); flat = si.get("flat",[])
                    bonus   = si.get("bonus",0); summary = si.get("summary","")
                    new_set = {x["code"] for x in new_rising}
                    tag     = f"🆕 {len(new_rising)}종목 추가" if new_rising and info["alert_count"]>1 else f"#{info['alert_count']}회 업데이트"
                    lines   = f"🏭 <b>섹터 모멘텀</b> [{theme}]  {tag}\n"
                    lines  += f"  {summary}\n" if summary else ""
                    for r in rising[:5]:
                        vt    = f" 🔊{r['volume_ratio']:.0f}x" if r.get("volume_ratio",0)>=2 else ""
                        new_t = " 🆕" if r["code"] in new_set else ""
                        lines += f"  📈 {r['name']} <b>{r['change_rate']:+.1f}%</b>{vt}{new_t}\n"
                    for r in flat[:2]:
                        lines += f"  ➖ {r['name']} {r['change_rate']:+.1f}%\n"
                    if bonus > 0:
                        lines += f"  💡 섹터 가산점: +{bonus}점\n"
                    send_with_chart_buttons(
                        f"🏭 <b>[{name} 섹터 모니터링]</b>\n━━━━━━━━━━━━━━━\n{lines}",
                        code, name
                    )
            except Exception as e:
                print(f"⚠️ 섹터 모니터 오류 ({code}): {e}")
    threading.Thread(target=_monitor_loop, daemon=True).start()
    print(f"  📡 섹터 모니터링 시작: {name}")

# ============================================================
# 🎯 진입가 감지
# ============================================================
def register_top_signal(s: dict):
    """신호 발생마다 오늘의 최우선 종목 풀에 추가 (점수 높은 종목 유지)"""
    code  = s.get("code","")
    score = s.get("score", 0)
    if not code: return
    existing = _today_top_signals.get(code, {})
    if score > existing.get("score", 0):
        _today_top_signals[code] = {
            "score":       score,
            "name":        s.get("name", code),
            "signal_type": s.get("signal_type",""),
            "entry_price": s.get("entry_price", 0),
            "stop_loss":   s.get("stop_loss", 0),
            "target_price":s.get("target_price", 0),
            "reasons":     s.get("reasons", []),
            "detected_at": datetime.now().strftime("%H:%M"),
            "nxt_delta":   s.get("nxt_delta", 0),
        }

def send_top_signals():
    """10:00~장마감까지 1시간마다 — 최우선 종목 TOP 5 발송"""
    if not _today_top_signals: return

    sig_labels = {
        "UPPER_LIMIT":"상한가","NEAR_UPPER":"상한가근접","SURGE":"급등",
        "EARLY_DETECT":"조기포착","MID_PULLBACK":"중기눌림목",
        "ENTRY_POINT":"단기눌림목","STRONG_BUY":"강력매수",
    }
    top5  = sorted(_today_top_signals.values(), key=lambda x: x["score"], reverse=True)[:5]
    medals = ["🥇","🥈","🥉","4️⃣","5️⃣"]
    msg   = f"🏆 <b>최우선 종목 TOP 5</b>  {datetime.now().strftime('%m/%d %H:%M')}\n━━━━━━━━━━━━━━━\n"
    for i, t in enumerate(top5, 1):
        medal   = medals[i-1]
        sig     = sig_labels.get(t["signal_type"], t["signal_type"])
        nxt_tag = f"  🔵NXT +{t['nxt_delta']}pt" if t.get("nxt_delta",0) > 0 else ""
        entry   = t.get("entry_price", 0)
        stop    = t.get("stop_loss", 0)
        target  = t.get("target_price", 0)
        rr      = round((target - entry) / (entry - stop), 1) if entry and stop and entry > stop else 0
        msg += (
            f"\n{medal} <b>{t['name']}</b>  {sig}  {t['score']}점{nxt_tag}\n"
            f"   포착: {t['detected_at']}\n"
            f"   🎯 진입 {entry:,}  🛡 손절 {stop:,}  🏆 목표 {target:,}\n"
            f"   손익비: {rr:.1f}:1\n"
        )
    msg += "\n━━━━━━━━━━━━━━━\n💡 점수·NXT·손익비 종합 순위"
    send(msg)

def reset_top_signals_daily():
    """장 시작 시 최우선 종목 풀 초기화"""
    _today_top_signals.clear()


def register_entry_watch(s: dict):
    entry = s.get("entry_price", 0)
    if not entry: return
    code = s["code"]

    # ── 같은 종목 기존 감시 제거 (재포착 시 진입가 갱신) ──
    old_keys = [k for k, w in _entry_watch.items() if w["code"] == code]
    for k in old_keys:
        old_entry  = _entry_watch[k].get("entry_price", 0)
        miss_count = _entry_watch[k].get("miss_count", 0)
        print(f"  🔄 진입가 갱신: {s['name']} {old_entry:,}→{entry:,}원 (미도달 {miss_count}회)")
        # signal_log의 기존 "추적중" 레코드를 "진입가변경"으로 업데이트
        try:
            sig_data = {}
            try:
                with open(SIGNAL_LOG_FILE, "r") as f_r: sig_data = json.load(f_r)
            except: pass
            for lk, rec in sig_data.items():
                if (rec.get("code") == code
                        and rec.get("status") == "추적중"
                        and rec.get("signal_type") == _entry_watch[k].get("signal_type")):
                    rec["status"]        = "진입가변경"
                    rec["exit_reason"]   = "재포착_진입가변경"
                    rec["old_entry"]     = old_entry
                    rec["new_entry"]     = entry
                    rec["pnl_pct"]       = 0.0
                    break
            with open(SIGNAL_LOG_FILE, "w") as f_w:
                json.dump(sig_data, f_w, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 진입가변경 기록 오류: {e}")
        del _entry_watch[k]

    log_key = f"{code}_{datetime.now().strftime('%Y%m%d%H%M')}"
    _entry_watch[log_key] = {
        "code": code, "name": s["name"], "entry_price": entry,
        "stop_loss":    s.get("stop_loss", 0),
        "target_price": s.get("target_price", 0),
        "signal_type":  s.get("signal_type", ""),
        "detect_time":  datetime.now().strftime("%H:%M"),
        "last_notified_ts": 0,
        "notify_count": 0,
        "miss_count":   len(old_keys),        # 이 종목 누적 재포착 횟수
        "registered_ts": time.time(),
        "expire_ts":    time.time() + 86400 * MAX_CARRY_DAYS,  # 3일 감시
        "peak_price":   s.get("price", 0),    # 포착 시점 가격 (상승 추적용)
    }
    print(f"  🎯 진입가 감시 등록: {s['name']} {entry:,}원 (만료: {MAX_CARRY_DAYS}일 후)")

def _record_entry_miss(watch: dict, reason: str, final_price: int):
    """진입가 미도달 만료 시 signal_log에 기록 → auto_tune 학습"""
    try:
        data = {}
        try:
            with open(SIGNAL_LOG_FILE, "r") as f: data = json.load(f)
        except: pass
        entry     = watch.get("entry_price", 0)
        miss_away = round((final_price - entry) / entry * 100, 1) if entry else 0
        peak      = watch.get("peak_price", final_price)
        peak_away = round((peak - entry) / entry * 100, 1) if entry else 0
        for log_key, rec in data.items():
            if (rec.get("code") == watch["code"]
                    and rec.get("status") == "추적중"
                    and rec.get("signal_type") == watch.get("signal_type")):
                rec["entry_miss"]      = reason
                rec["entry_miss_away"] = miss_away
                rec["entry_peak_away"] = peak_away
                rec["miss_count"]      = watch.get("miss_count", 0)
                rec["status"]          = "진입미달"
                rec["pnl_pct"]         = 0.0
                rec["exit_reason"]     = f"진입미달_{reason}"
                break
        with open(SIGNAL_LOG_FILE, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  📝 진입미달 기록: {watch['name']} {reason} (진입가 대비 {miss_away:+.1f}%)")
    except Exception as e:
        print(f"⚠️ 진입미달 기록 오류: {e}")

def check_entry_watch():
    if not _entry_watch: return
    use_nxt = not is_market_open() and is_nxt_open()
    expired = []
    for log_key, watch in list(_entry_watch.items()):
        # ── 만료 체크 (3일) ──
        if time.time() > watch.get("expire_ts", watch["registered_ts"] + 86400):
            _record_entry_miss(watch, "기간만료", watch.get("peak_price", 0))
            miss_count = watch.get("miss_count", 0) + 1
            if miss_count >= 3:
                old_ratio = _dynamic.get("entry_pullback_ratio", ENTRY_PULLBACK_RATIO)
                if old_ratio > 0.15:
                    _dynamic["entry_pullback_ratio"] = round(old_ratio - 0.05, 2)
                    print(f"  🔧 진입가 비율 완화: {old_ratio:.2f}→{_dynamic['entry_pullback_ratio']:.2f} (미도달 {miss_count}회)")
            expired.append(log_key); continue

        try:
            if use_nxt:
                cur   = get_nxt_stock_price(watch["code"])
                price = cur.get("price", 0)
                if not price:
                    cur   = get_stock_price(watch["code"])
                    price = cur.get("price", 0)
            else:
                cur   = get_stock_price(watch["code"])
                price = cur.get("price", 0)
            if not price: continue

            # 최고가 갱신
            if price > watch.get("peak_price", 0):
                watch["peak_price"] = price

            entry    = watch["entry_price"]
            diff_pct = (price - entry) / entry * 100

            # ── 상승 이탈: 진입가보다 +10% 이상 올라가버리면 포기 ──
            if diff_pct >= 10.0:
                _record_entry_miss(watch, "상승이탈", price)
                send_with_chart_buttons(
                    f"📈 <b>[진입가 이탈]</b>\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"<b>{watch['name']}</b>  <code>{watch['code']}</code>\n"
                    f"진입가 {entry:,}원에서 +{diff_pct:.1f}% 상승 이탈\n"
                    f"진입 기회 없이 상승 → 감시 종료",
                    watch["code"], watch["name"]
                )
                expired.append(log_key); continue

            # ── 진입가 ±2% 이내 진입 구간 ──
            if abs(diff_pct) <= ENTRY_TOLERANCE_PCT:
                now_ts       = time.time()
                last_ts      = watch.get("last_notified_ts", 0)
                notify_count = watch.get("notify_count", 0)
                cooldown_sec = ENTRY_REWATCH_MINS * 60
                if notify_count >= 3: expired.append(log_key); continue
                if now_ts - last_ts < cooldown_sec: continue
                watch["last_notified_ts"] = now_ts
                watch["notify_count"]     = notify_count + 1
                sig_labels = {
                    "UPPER_LIMIT":"상한가","NEAR_UPPER":"상한가근접","SURGE":"급등",
                    "EARLY_DETECT":"조기포착","MID_PULLBACK":"중기눌림목","ENTRY_POINT":"단기눌림목",
                }
                sig       = sig_labels.get(watch["signal_type"], watch["signal_type"])
                diff_str  = f"+{diff_pct:.1f}%" if diff_pct >= 0 else f"{diff_pct:.1f}%"
                stop_pct  = round((watch["stop_loss"]    - entry) / entry * 100, 1) if entry else 0
                tgt_pct   = round((watch["target_price"] - entry) / entry * 100, 1) if entry else 0
                nxt_notice = "\n🔵 <b>NXT 기준 가격</b>" if use_nxt else ""
                count_tag  = f"  ({notify_count+1}/3회)" if notify_count > 0 else ""
                send_with_chart_buttons(
                    f"🔔🔔 <b>[진입가 도달!{count_tag}]</b> 🔔🔔{nxt_notice}\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🟢 <b>{watch['name']}</b>  <code>{watch['code']}</code>\n"
                    f"원신호: {sig}  |  포착: {watch['detect_time']}\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"┌─────────────────────\n"
                    f"│ ⚡️ <b>지금 진입 구간!</b>\n"
                    f"│ 📍 현재가  <b>{price:,}원</b>  ({diff_str})\n"
                    f"│ 🎯 진입가  <b>{entry:,}원</b>  ◀ 목표!\n"
                    f"│ 🛡 손절가  <b>{watch['stop_loss']:,}원</b>  ({stop_pct:+.1f}%)\n"
                    f"│ 🏆 목표가  <b>{watch['target_price']:,}원</b>  ({tgt_pct:+.1f}%)\n"
                    f"└─────────────────────",
                    watch["code"], watch["name"]
                )
                print(f"  🎯 진입가 도달 ({notify_count+1}회): {watch['name']} {price:,} / 진입 {entry:,}")
        except: continue
    for k in expired:
        _entry_watch.pop(k, None)

def send_with_chart_buttons(text: str, code: str, name: str):
    """
    텍스트 메시지 + 인라인 키보드 버튼(네이버 차트 링크) 전송
    버튼은 기기 기본 브라우저(외부)로 열림
    """
    naver = f"https://finance.naver.com/item/fchart.naver?code={code}"
    keyboard = {
        "inline_keyboard": [[
            {"text": f"📈 {name} 차트 보기 (네이버)", "url": naver},
        ]]
    }
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id":      TELEGRAM_CHAT_ID,
                "text":         text,
                "parse_mode":   "HTML",
                "reply_markup": keyboard,
            },
            timeout=10
        )
    except Exception as e:
        print(f"⚠️ 텔레그램 오류: {e}")

def send(text: str):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                      json={"chat_id":TELEGRAM_CHAT_ID,"text":text,"parse_mode":"HTML"},timeout=10)
    except Exception as e: print(f"⚠️ 텔레그램 오류: {e}")

def send_by_level(text: str, level: str = ALERT_LEVEL_NORMAL,
                  code: str = "", name: str = ""):
    """
    중요도별 알림 발송
    CRITICAL / NORMAL → 즉시 발송
    INFO              → _pending_info_alerts 대기열에 추가 (10분마다 묶음 발송)
    """
    if level in (ALERT_LEVEL_CRITICAL, ALERT_LEVEL_NORMAL):
        if code and name:
            send_with_chart_buttons(text, code, name)
        else:
            send(text)
    else:  # INFO
        _pending_info_alerts.append({"text": text, "ts": time.time()})

def flush_info_alerts():
    """INFO 알림 묶음 발송 (5분마다 스케줄) + 오래된 항목 자동 제거"""
    if not _pending_info_alerts: return
    now = time.time()
    # 1시간 이상 된 항목은 조용히 제거 (너무 오래된 참고 알림은 의미 없음)
    stale = [a for a in _pending_info_alerts if now - a["ts"] > 3600]
    for a in stale:
        _pending_info_alerts.remove(a)
    # 최대 20개 초과 시 오래된 것부터 제거
    while len(_pending_info_alerts) > 20:
        _pending_info_alerts.pop(0)
    # 5분 이상 된 것만 발송
    to_send = [a for a in _pending_info_alerts if now - a["ts"] >= 300]
    if not to_send: return
    for a in to_send:
        try: _pending_info_alerts.remove(a)
        except: pass
    if len(to_send) == 1:
        send(to_send[0]["text"])
    else:
        combined = f"🔵 <b>참고 알림 묶음</b>  {len(to_send)}건\n━━━━━━━━━━━━━━━\n"
        for a in to_send:
            first_line = a["text"].split("\n")[0][:60]
            combined  += f"• {first_line}\n"
        send(combined)

def get_alert_level(signal_type: str, score: int, nxt_delta: int = 0) -> str:
    """
    신호 유형 + 점수 → 중요도 레벨 결정
    CRITICAL: 상한가·강력매수·NXT보정 +10 이상 고점수
    NORMAL:   급등·조기포착·중기눌림목
    INFO:     참고용 섹터 업데이트·낮은 점수
    """
    if signal_type in ("UPPER_LIMIT", "STRONG_BUY"): return ALERT_LEVEL_CRITICAL
    if signal_type == "NEAR_UPPER" and score >= 85:  return ALERT_LEVEL_CRITICAL
    if nxt_delta >= 10 and score >= 80:              return ALERT_LEVEL_CRITICAL
    if score >= 75:                                   return ALERT_LEVEL_NORMAL
    if score >= 60:                                   return ALERT_LEVEL_NORMAL
    return ALERT_LEVEL_INFO

def _sector_block(s: dict) -> str:
    si = s.get("sector_info")
    if not si:
        return ""

    theme   = si.get("theme", "")
    bonus   = si.get("bonus", 0)
    summary = si.get("summary", "")
    detail  = si.get("detail", [])
    rising  = si.get("rising", [])
    flat    = si.get("flat", [])
    sources = si.get("sources", {})

    if not detail and not summary:
        return f"🏭 <b>섹터 모멘텀</b> [{theme}]  업종 조회 실패\n━━━━━━━━━━━━━━━\n\n"

    bonus_tag = f"  +{bonus}점" if bonus > 0 else ""
    block = f"🏭 <b>섹터 모멘텀</b> [{theme}]{bonus_tag}\n"

    # 왜 이 종목들이 묶였는지 표시
    if "동적테마" in sources:
        block += f"  🔗 연관 근거: 가격 상관관계·뉴스 공동언급\n"
    if "테마" in sources:
        block += f"  📌 테마 등록 종목\n"
    if "업종코드" in sources and len(sources) == 1:
        block += f"  📂 동일 업종 분류\n"

    if summary:
        block += f"  {summary}\n"

    for r in rising[:5]:
        src_tag  = " 🔗" if r.get("source") == "동적테마" else ""
        vol_tag  = f" 🔊{r['volume_ratio']:.0f}x" if r.get("volume_ratio", 0) >= 2 else ""
        block   += f"  📈 {r['name']} <b>{r['change_rate']:+.1f}%</b>{vol_tag}{src_tag}\n"

    for r in flat[:3]:
        src_tag = " 🔗" if r.get("source") == "동적테마" else ""
        block  += f"  ➖ {r['name']} {r['change_rate']:+.1f}%{src_tag}\n"

    return block + "━━━━━━━━━━━━━━━\n\n"

def send_alert(s: dict):
    emoji = {"UPPER_LIMIT":"🚨","NEAR_UPPER":"🔥","STRONG_BUY":"💎",
             "SURGE":"📈","ENTRY_POINT":"🎯","EARLY_DETECT":"🔍"}.get(s["signal_type"],"📊")
    title = {"UPPER_LIMIT":"상한가 감지","NEAR_UPPER":"상한가 근접","STRONG_BUY":"강력 매수 신호",
             "SURGE":"급등 감지","ENTRY_POINT":"★ 눌림목 진입 시점 ★",
             "EARLY_DETECT":"★ 조기 포착 - 선진입 기회 ★"}.get(s["signal_type"],"급등 감지")

    level    = get_alert_level(s["signal_type"], s.get("score",0), s.get("nxt_delta",0))
    nxt_badge = "\n🔵 <b>NXT (넥스트레이드) 거래</b>" if s.get("market") == "NXT" else ""
    lvl_icon  = {"CRITICAL":"🔴","NORMAL":"🟡","INFO":"🔵"}.get(level,"🟡")

    # ── 컴팩트 모드 ──
    if _compact_mode:
        name_dot = {"UPPER_LIMIT":"🔴","NEAR_UPPER":"🟠","STRONG_BUY":"🟢",
                    "SURGE":"🟡","EARLY_DETECT":"🔵","ENTRY_POINT":"🟣"}.get(s["signal_type"],"⚪")
        entry  = s.get("entry_price", 0)
        stop   = s.get("stop_loss", 0)
        target = s.get("target_price", 0)
        rr     = round((target-entry)/(entry-stop),1) if entry and stop and entry>stop else 0
        compact_text = (
            f"{lvl_icon}{emoji} {name_dot}<b>{s['name']}</b>  {s['change_rate']:+.1f}%  "
            f"{s['score']}점{nxt_badge}\n"
            f"진입 {entry:,} | 손절 {stop:,} | 목표 {target:,}  RR {rr:.1f}"
        )
        send_by_level(compact_text, level, s["code"], s["name"])
        return

    # ── 상세 모드 (기존) ──
    name_dot = {
        "UPPER_LIMIT": "🔴",
        "NEAR_UPPER":  "🟠",
        "STRONG_BUY":  "🟢",
        "SURGE":       "🟡",
        "EARLY_DETECT":"🔵",
        "ENTRY_POINT": "🟣",
    }.get(s["signal_type"], "⚪")

    stars    = "★" * min(int(s["score"]/20), 5)
    now_str  = datetime.now().strftime("%H:%M:%S")
    stop_pct = s.get("stop_pct",7.0); target_pct = s.get("target_pct",15.0)
    atr_tag  = " (ATR)" if s.get("atr_used") else " (고정)"
    strict_warn = "\n⏰ <b>장 시작·마감 근접 — 변동성 주의</b>\n" if is_strict_time() else ""
    prev_tag    = "\n🔁 <b>전일 상한가!</b> 연속 상한가 가능성" if s.get("prev_upper") else ""

    # 진입가 강조 블록
    entry  = s.get("entry_price", 0)
    stop   = s.get("stop_loss", 0)
    target = s.get("target_price", 0)
    price  = s.get("price", 0)
    diff_from_entry = ((price - entry) / entry * 100) if entry and price else 0

    detected_at = s.get("detected_at", datetime.now())
    if s["signal_type"] == "ENTRY_POINT":
        entry_block = (
            f"┌─────────────────────\n"
            f"│ ⚡️ <b>지금 진입 구간!</b>\n"
            f"│ 🎯 진입가  <b>{entry:,}원</b>  ← 현재 {diff_from_entry:+.1f}%\n"
            f"│ 🛡 손절가  <b>{stop:,}원</b>  (-{stop_pct:.1f}%){atr_tag}\n"
            f"│ 🏆 목표가  <b>{target:,}원</b>  (+{target_pct:.1f}%){atr_tag}\n"
            f"└─────────────────────"
        )
    elif s["signal_type"] == "EARLY_DETECT":
        entry_block = (
            f"┌─────────────────────\n"
            f"│ ⚡️ <b>선진입 고려!</b>\n"
            f"│ 🎯 목표진입  <b>{entry:,}원</b>  ← 현재 {diff_from_entry:+.1f}%\n"
            f"│ 🛡 손절가   <b>{stop:,}원</b>  (-{stop_pct:.1f}%){atr_tag}\n"
            f"│ 🏆 목표가   <b>{target:,}원</b>  (+{target_pct:.1f}%){atr_tag}\n"
            f"└─────────────────────"
        )
    else:
        elapsed = minutes_since(detected_at)
        wait_msg = f"⏰ 눌림목 대기 ({30-elapsed}분 후 체크)" if elapsed < 30 else "📡 눌림목 실시간 체크 중"
        entry_block = (
            f"┌─────────────────────\n"
            f"│ {wait_msg}\n"
            f"│ 🎯 목표진입  <b>{entry:,}원</b>  ← 현재 {diff_from_entry:+.1f}%\n"
            f"│ 🛡 손절가   <b>{stop:,}원</b>  (-{stop_pct:.1f}%){atr_tag}\n"
            f"│ 🏆 목표가   <b>{target:,}원</b>  (+{target_pct:.1f}%){atr_tag}\n"
            f"└─────────────────────"
        )

    # NXT 여부 (상세 모드용 - 컴팩트는 위에서 처리됨)
    nxt_badge = "\n🔵 <b>NXT (넥스트레이드) 거래</b>" if s.get("market") == "NXT" else ""


    # 보조지표 + 포지션 사이징 + 유사패턴 블록
    indic = s.get("indic") or calc_indicators(code)
    rsi     = indic.get("rsi", 50)
    ma_desc = indic.get("ma", {}).get("desc", "")
    bb_desc = indic.get("bb", {}).get("desc", "")
    indic_block = (
        f"━━━━━━━━━━━━━━━\n"
        f"📐 <b>보조지표</b>\n"
        f"  RSI {rsi}  |  {ma_desc}\n"
        f"  볼린저: {bb_desc}\n"
    ) if ma_desc else ""

    pos = s.get("position", {})
    if pos:
        pct   = pos.get("pct", 8.0)
        guide = pos.get("guide", "")
        wr    = pos.get("win_rate")
        samp  = pos.get("samples", 0)
        wr_str = f"  과거승률 {wr:.0f}% ({samp}건)\n" if wr else ""
        position_block = (
            f"━━━━━━━━━━━━━━━\n"
            f"💰 <b>포지션 가이드</b>  권장 <b>{pct}%</b>\n"
            f"{wr_str}"
            f"  {guide}\n"
        )
    else:
        position_block = ""

    pattern_block = find_similar_patterns(
        s["code"], s["signal_type"],
        s.get("change_rate", 0), s.get("volume_ratio", 0)
    )
    if pattern_block:
        pattern_block = "━━━━━━━━━━━━━━━\n" + pattern_block + "\n"

    _send_alert_detail(s, emoji, title, nxt_badge, name_dot, stars, now_str,
                       stop_pct, target_pct, atr_tag, strict_warn, prev_tag,
                       entry_block, indic_block, position_block, pattern_block, level)

# ── 내부 헬퍼: 상세 모드 실제 발송 (send_alert에서 호출) ──
def _send_alert_detail(s, emoji, title, nxt_badge, name_dot, stars, now_str,
                       stop_pct, target_pct, atr_tag, strict_warn, prev_tag,
                       entry_block, indic_block, position_block, pattern_block, level):
    send_by_level(
        f"{emoji} <b>[{title}]</b>{nxt_badge}\n"
        f"🕐 {now_str}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{name_dot} <b>{s['name']}</b>  <code>{s['code']}</code>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{strict_warn}"
        f"💰 현재가: <b>{s['price']:,}원</b>  (<b>{s['change_rate']:+.1f}%</b>)\n"
        f"📊 거래량: <b>{s['volume_ratio']:.1f}배</b> (5일 평균 대비)\n"
        f"⭐ 신호강도: {stars} ({s['score']}점)\n"
        f"{prev_tag}\n"
        f"━━━━━━━━━━━━━━━\n"
        + "\n".join(s["reasons"]) + "\n"
        + indic_block
        + position_block
        + pattern_block
        + "━━━━━━━━━━━━━━━\n\n"
        + _sector_block(s)
        + f"\n{entry_block}",
        level, s["code"], s["name"]
    )



# ============================================================
# 분석 엔진 (당일 급등)
# ============================================================
def analyze(stock: dict) -> dict:
    code = stock.get("code",""); change_rate = stock.get("change_rate",0)
    vol_ratio = stock.get("volume_ratio",0); price = stock.get("price",0)
    if not code or price < 500: return {}

    strict    = is_strict_time()
    min_score = _dynamic["min_score_strict"] if strict else _dynamic["min_score_normal"]
    score, reasons, signal_type = 0, [], None

    if change_rate >= 29.0:
        score+=40; reasons.append("🚨 상한가 도달!"); signal_type="UPPER_LIMIT"
    elif change_rate >= UPPER_LIMIT_THRESHOLD:
        score+=25; reasons.append(f"🔥 상한가 근접 (+{change_rate:.1f}%)"); signal_type="NEAR_UPPER"
    elif change_rate >= PRICE_SURGE_MIN:
        score+=15; reasons.append(f"📈 급등 +{change_rate:.1f}%"); signal_type="SURGE"
    else: return {}

    if vol_ratio >= VOLUME_SURGE_RATIO*2:
        score+=30; reasons.append(f"💥 거래량 {vol_ratio:.1f}배 폭발 (5일 평균 대비)")
    elif vol_ratio >= VOLUME_SURGE_RATIO:
        score+=20; reasons.append(f"📊 거래량 {vol_ratio:.1f}배 급증 (5일 평균 대비)")

    # 코스피 상대강도 ⑯
    rs = get_relative_strength(change_rate)
    if rs >= RS_MIN:
        score+=10; reasons.append(f"💪 코스피 상대강도 {rs:.1f}배")

    if score >= 25:
        try:
            inv = get_investor_trend(code)
            f_net, i_net = inv.get("foreign_net",0), inv.get("institution_net",0)
            if f_net>0 and i_net>0: score+=25; signal_type="STRONG_BUY"; reasons.append("✅ 외국인+기관 동시 순매수")
            elif f_net>0: score+=10; reasons.append(f"🟡 외국인 순매수 ({f_net:+,}주)")
            elif i_net>0: score+=10; reasons.append(f"🟡 기관 순매수 ({i_net:+,}주)")
            elif f_net<0 and i_net<0: reasons.append(f"⚠️ 외국인({f_net:+,}) 기관({i_net:+,}) 동시 매도")
        except: inv = {}; f_net = 0; i_net = 0

    if score < min_score: return {}

    # ── 보조지표 필터 (RSI / 이동평균 / 볼린저밴드) ──
    indic = calc_indicators(code)
    if not indic["filter_pass"] and signal_type not in ("UPPER_LIMIT", "NEAR_UPPER"):
        return {}
    score += indic["score_adj"]
    if indic["summary"]:
        for line in indic["summary"].split("\n"):
            if line: reasons.append(line)
    if score < min_score: return {}

    # 전일 상한가 ⑨
    prev_upper = was_upper_limit_yesterday(code)
    if prev_upper: score+=10; reasons.append("🔁 전일 상한가 → 연속 상한가 가능성")

    # 거래량 Z-score ⑰
    try:
        cur_detail = get_stock_price(code)
        z = get_volume_zscore(code, cur_detail.get("today_vol",0))
        if z >= VOL_ZSCORE_MIN: score+=10; reasons.append(f"📊 거래량 이상 급증 (Z-score {z:.1f}σ)")
    except: pass

    # 섹터 모멘텀
    sector_info = calc_sector_momentum(code, stock.get("name",code))
    if sector_info["bonus"]>0:
        score+=sector_info["bonus"]; reasons.append(sector_info["summary"])
        if sector_info.get("rising"):
            reasons.append("📌 동반 상승: " + ", ".join([f"{r['name']} {r['change_rate']:+.1f}%" for r in sector_info["rising"][:4]]))
    elif sector_info.get("summary"):
        reasons.append(sector_info["summary"])

    # ── NXT 보정 (장 중에만, 백그라운드 영향 최소화) ──
    nxt_delta, nxt_reason = 0, ""
    try:
        nxt_delta, nxt_reason = nxt_score_bonus(code)
        if nxt_delta != 0:
            score += nxt_delta
            if nxt_reason: reasons.append(nxt_reason)
    except: pass

    # ── ① 시장 국면 보정 ──
    regime = get_market_regime()
    regime_mode = regime.get("mode", "normal")
    if regime_mode == "crash" and signal_type not in ("UPPER_LIMIT", "STRONG_BUY"):
        return {}   # 급락장: 상한가/강력매수만 허용
    min_add = regime.get("min_add", 0)
    if score < min_score + min_add: return {}
    if regime_mode != "normal":
        reasons.append(f"🌐 시장: {regime_label()} (코스피 {regime.get('chg_1d',0):+.1f}%)")

    # ── ④ 실적 발표 필터 ──
    earnings = check_earnings_risk(code, stock.get("name", code))
    if earnings["risk"] == "high":
        reasons.append(earnings["desc"])
    elif earnings["risk"] == "warn":
        reasons.append(earnings["desc"])
        score = int(score * 0.85)   # 실적 발표 3일 전 → 점수 15% 감점
        if score < min_score: return {}

    open_est     = price/(1+change_rate/100)
    _pullback_r  = _dynamic.get("entry_pullback_ratio", ENTRY_PULLBACK_RATIO)
    entry        = int((price-(price-open_est)*_pullback_r)/10)*10

    # ── ③ 손익비 동적 조정 ──
    stop, target, stop_pct, target_pct, atr_used = calc_dynamic_stop_target(code, entry)

    # 등급 계산
    if   score >= 80: grade = "A"
    elif score >= 60: grade = "B"
    else:             grade = "C"

    # ── ② 포지션 사이징 ──
    position = calc_position_size(signal_type, score, grade)

    return {"code":code,"name":stock.get("name",code),"price":price,
            "change_rate":change_rate,"volume_ratio":vol_ratio,
            "signal_type":signal_type,"score":score,"sector_info":sector_info,
            "entry_price":entry,"stop_loss":stop,"target_price":target,
            "stop_pct":stop_pct,"target_pct":target_pct,"atr_used":atr_used,
            "prev_upper":prev_upper,"reasons":reasons,"detected_at":datetime.now(),
            "nxt_delta": nxt_delta,
            "regime": regime_mode,
            "earnings_risk": earnings["risk"],
            "position": position,
            "indic": indic,
            "grade": grade}

# ============================================================
# 조기 포착
# ============================================================
def check_early_detection() -> list:
    signals = []
    for stock in get_volume_surge_stocks():
        code = stock.get("code",""); change_rate = stock.get("change_rate",0)
        vol_ratio = stock.get("volume_ratio",0); price = stock.get("price",0)
        if not code or price < 500: continue
        if change_rate >= UPPER_LIMIT_THRESHOLD: continue
        price_min  = _early_price_min_dynamic  * (1.3 if is_strict_time() else 1.0)
        volume_min = _early_volume_min_dynamic * (1.3 if is_strict_time() else 1.0)
        if change_rate < price_min or vol_ratio < volume_min: continue
        try:
            detail = get_stock_price(code)
            bid_qty, ask_qty = detail.get("bid_qty",0), detail.get("ask_qty",0)
            if ask_qty > 0 and bid_qty/ask_qty < EARLY_HOGA_RATIO: continue
        except: continue

        now = datetime.now()
        cache = _early_cache.get(code)
        if cache is None:
            _early_cache[code] = {"count":1,"last_price":price,"last_time":now}; continue
        elapsed = (now - cache["last_time"]).seconds
        if 15 <= elapsed <= 80:   # 20초 스캔 기준: 1~4회 사이 재확인
            if price >= cache["last_price"]:
                cache["count"]+=1; cache["last_price"]=price; cache["last_time"]=now
            else: _early_cache[code]={"count":1,"last_price":price,"last_time":now}; continue
        else: _early_cache[code]={"count":1,"last_price":price,"last_time":now}; continue
        if cache["count"] < EARLY_CONFIRM_COUNT: continue
        del _early_cache[code]

        open_est     = price/(1+change_rate/100)
        _pullback_r  = _dynamic.get("entry_pullback_ratio", ENTRY_PULLBACK_RATIO)
        entry        = int((price-(price-open_est)*_pullback_r)/10)*10
        stop, target, stop_pct, target_pct, atr_used = calc_stop_target(code, entry)
        hoga_text = f"{bid_qty/ask_qty:.1f}배" if ask_qty > 0 else "압도적"
        prev_upper = was_upper_limit_yesterday(code)
        early_score = 85 + (10 if prev_upper else 0)
        reasons = [f"🔍 조기 포착!",f"📈 현재 +{change_rate:.1f}%",
                   f"💥 거래량 {vol_ratio:.1f}배 (5일 평균 대비)",
                   f"📊 매수/매도 잔량 {hoga_text}",f"✅ 2분 연속 상승 확인"]
        if prev_upper: reasons.append("🔁 전일 상한가 → 연속 상한가 가능성")
        # 코스피 상대강도
        rs = get_relative_strength(change_rate)
        if rs >= RS_MIN: early_score+=10; reasons.append(f"💪 코스피 상대강도 {rs:.1f}배")
        # 거래량 Z-score
        try:
            z = get_volume_zscore(code, detail.get("today_vol",0))
            if z >= VOL_ZSCORE_MIN: early_score+=10; reasons.append(f"📊 거래량 Z-score {z:.1f}σ")
        except: pass
        sector_info = calc_sector_momentum(code, stock.get("name",code))
        if sector_info["bonus"]>0:
            early_score+=sector_info["bonus"]; reasons.append(sector_info["summary"])
            if sector_info.get("rising"):
                reasons.append("📌 동반 상승: "+"".join([f"{r['name']} {r['change_rate']:+.1f}%" for r in sector_info["rising"][:4]]))
        elif sector_info.get("summary"): reasons.append(sector_info["summary"])

        # NXT 보정
        try:
            nd, nr = nxt_score_bonus(code)
            if nd != 0: early_score += nd
            if nr: reasons.append(nr)
        except: pass

        signals.append({"code":code,"name":stock.get("name",code),"price":price,
                        "change_rate":change_rate,"volume_ratio":vol_ratio,
                        "signal_type":"EARLY_DETECT","score":early_score,"sector_info":sector_info,
                        "entry_price":entry,"stop_loss":stop,"target_price":target,
                        "stop_pct":stop_pct,"target_pct":target_pct,"atr_used":atr_used,
                        "prev_upper":prev_upper,"reasons":reasons,"detected_at":now})

    # ── 장 전 NXT 선포착 (08:00~08:59) ──
    # KRX 개장 전 NXT에서 이미 급등 중인 종목을 미리 포착
    now_t = datetime.now().time()
    if dtime(8, 0) <= now_t < dtime(9, 0):
        for stock in get_nxt_surge_stocks():
            code = stock.get("code",""); price = stock.get("price",0)
            vr   = stock.get("volume_ratio",0); cr = stock.get("change_rate",0)
            if not code or price < 500 or code in {s["code"] for s in signals}: continue
            if cr < 5.0 or vr < 5.0: continue   # NXT 장 전 기준 더 엄격

            nxt = get_nxt_info(code)
            pre_score = 70
            pre_reasons = [
                f"🌅 장 전 NXT 선포착!",
                f"📈 NXT 현재 +{cr:.1f}%  (KRX 개장 전)",
                f"💥 NXT 거래량 {vr:.1f}배",
            ]
            if nxt.get("inv_bullish"):
                pre_score += 15
                pre_reasons.append(f"🔵 NXT 외인+기관 매수 ({nxt['foreign_net']:+,}주)")
            if nxt.get("vs_krx_pct", 0) > 0.5:
                pre_score += 10
                pre_reasons.append(f"🔵 NXT 프리미엄 +{nxt['vs_krx_pct']:.1f}% → KRX 갭상 주목")
            if pre_score < 75: continue

            entry = price
            stop, target, stop_pct, target_pct, atr_used = calc_stop_target(code, entry)
            pre_key = f"NXT_PRE_{code}"
            if time.time() - _alert_history.get(pre_key, 0) < 3600: continue
            _alert_history[pre_key] = time.time()

            signals.append({"code":code,"name":stock.get("name",code),"price":price,
                            "change_rate":cr,"volume_ratio":vr,
                            "signal_type":"EARLY_DETECT","score":pre_score,
                            "sector_info":{},"market":"NXT",
                            "entry_price":entry,"stop_loss":stop,"target_price":target,
                            "stop_pct":stop_pct,"target_pct":target_pct,"atr_used":atr_used,
                            "prev_upper":False,"reasons":pre_reasons,
                            "detected_at":datetime.now()})

    return signals

# ============================================================
# 단기 눌림목 체크 (당일 급등 후)
# ============================================================
def check_pullback_signals() -> list:
    signals = []
    for code, info in list(_detected_stocks.items()):
        detected_at = info.get("detected_at")
        if not detected_at or minutes_since(detected_at) < 30: continue
        if time.time() - _pullback_history.get(code,0) < 1800: continue
        try:
            cur = get_stock_price(code)
            high = info.get("high_price",0); price = cur.get("price",0)
            if not price or not high: continue
            if price > high: _detected_stocks[code]["high_price"]=price; continue
            pullback = (high-price)/high*100
            carry    = info.get("carry_day",0)
            if 25.0 <= pullback <= 55.0:
                entry = price
                stop, target, stop_pct, target_pct, atr_used = calc_stop_target(code, entry)
                carry_text = f" (이월 {carry}일차)" if carry>0 else ""
                signals.append({"code":code,"name":cur.get("name",code),"price":price,
                                 "change_rate":cur.get("change_rate",0),"volume_ratio":0,
                                 "signal_type":"ENTRY_POINT","score":95,
                                 "entry_price":entry,"stop_loss":stop,"target_price":target,
                                 "stop_pct":stop_pct,"target_pct":target_pct,"atr_used":atr_used,
                                 "prev_upper":False,
                                 "reasons":[f"🎯 단기 눌림목{carry_text}",
                                            f"📌 고점 {high:,}원 → 현재 {price:,}원 (-{pullback:.1f}%)",
                                            f"⏱ 급등 후 {minutes_since(detected_at)}분 경과"],
                                 "detected_at":detected_at})
                _pullback_history[code] = time.time()
        except: continue
    return signals

# ============================================================
# 뉴스 (3개 소스 병렬)
# ============================================================
def fetch_news_for_stock(code: str, name: str) -> list:
    """
    급등 종목 → 관련 뉴스 역추적
    네이버 금융 종목 뉴스 페이지 스크래핑
    returns: [{"title": str, "time": str}, ...]  최대 3건
    """
    cached = _news_reverse_cache.get(code)
    if cached and time.time() - cached.get("ts", 0) < 1800:
        return cached.get("news", [])
    news = []
    try:
        url  = f"https://finance.naver.com/item/news_news.naver?code={code}&page=1&sm=title_entity_id.basic"
        resp = requests.get(url, headers=_random_ua(), timeout=8)
        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select("table.type5 tr")
        for row in rows[:5]:
            title_el = row.select_one("td.title a")
            time_el  = row.select_one("td.date")
            if not title_el: continue
            title = title_el.get_text(strip=True)
            t     = time_el.get_text(strip=True) if time_el else ""
            # 종목명 또는 관련 키워드 포함 여부 필터
            if len(title) > 5:
                news.append({"title": title[:40], "time": t})
            if len(news) >= 3: break
    except: pass
    _news_reverse_cache[code] = {"news": news, "ts": time.time()}
    return news

_news_alert_sent: dict = {}   # code → ts (뉴스 알림 쿨다운, 30분)

def news_block_for_alert(code: str, name: str) -> str:
    """알림 직후 백그라운드로 뉴스 역추적 — 30분 쿨다운으로 중복 크롤링 방지"""
    now = time.time()
    if now - _news_alert_sent.get(code, 0) < 1800: return  # 30분 쿨다운
    _news_alert_sent[code] = now
    def _fetch():
        try:
            articles = fetch_news_for_stock(code, name)
            if not articles: return
            lines = "\n".join(f"  📰 {a['title']}  <i>{a['time']}</i>" for a in articles)
            send_with_chart_buttons(
                f"📰 <b>[{name} 관련 뉴스]</b>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"{lines}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"💡 뉴스 있음 — 재료 확인 후 진입 판단",
                code, name
            )
        except: pass
    threading.Thread(target=_fetch, daemon=True).start()

def fetch_naver_news() -> list:
    try:
        resp = requests.get("https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258",
                            timeout=10, headers=_random_ua())
        soup = BeautifulSoup(resp.text, "html.parser")
        return [t.get_text(strip=True) for t in soup.select(".realtimeNewsList .newsList li a")][:30]
    except: return []

def fetch_hankyung_news() -> list:
    try:
        resp = requests.get("https://www.hankyung.com/economy", timeout=10, headers=_random_ua())
        soup = BeautifulSoup(resp.text, "html.parser")
        return [t.get_text(strip=True) for t in soup.select("h3.news-tit, h2.tit")][:20]
    except: return []

def fetch_yonhap_news() -> list:
    try:
        resp = requests.get("https://www.yna.co.kr/economy/stock", timeout=10, headers=_random_ua())
        soup = BeautifulSoup(resp.text, "html.parser")
        return [t.get_text(strip=True) for t in soup.select(".news-tl")][:20]
    except: return []

def fetch_all_news() -> list:
    results = []
    threads = [
        threading.Thread(target=lambda: results.extend(fetch_naver_news())),
        threading.Thread(target=lambda: results.extend(fetch_hankyung_news())),
        threading.Thread(target=lambda: results.extend(fetch_yonhap_news())),
    ]
    for t in threads: t.start()
    for t in threads: t.join(timeout=8)
    return list(dict.fromkeys(results))

def analyze_news_theme(headlines: list = None) -> list:
    signals = []
    if headlines is None:                      # 직접 호출 시에만 크롤링
        headlines = fetch_all_news()
    if not headlines: return []
    print(f"  📰 뉴스 {len(headlines)}건 (3개 소스)")
    for theme_key, theme_info in THEME_MAP.items():
        if time.time() - _news_alert_history.get(theme_key,0) < 14400: continue
        matched = [h for h in headlines if theme_key in h or any(s in h for s in theme_info.get("sectors",[]))]
        if not matched: continue
        stock_status = []
        for code, name in theme_info["stocks"]:
            try:
                cur = get_stock_price(code)
                if not cur: continue
                cr, vr = cur.get("change_rate",0), cur.get("volume_ratio",0)
                stock_status.append({"code":code,"name":name,"price":cur["price"],
                                     "change_rate":cr,"volume_ratio":vr,
                                     "rising":cr>=2.0,"surging":cr>=5.0,"vol_on":vr>=2.0,"not_yet":cr<2.0})
                time.sleep(0.2)
            except: continue
        if not stock_status: continue
        rising_stocks = [s for s in stock_status if s["rising"]]
        if not rising_stocks:
            print(f"  ⏭ [{theme_key}] 뉴스 있지만 주가 반응 없음 → 스킵"); continue
        total = len(stock_status); react_ratio = len(rising_stocks)/total
        sector_bonus = (15 if react_ratio>=1.0 else 10 if react_ratio>=0.5 else 5)
        if sum(1 for s in rising_stocks if s["vol_on"]) >= 2: sector_bonus+=5
        strength = ("매우강함" if [s for s in stock_status if s["surging"]] and react_ratio>=0.5
                    else "강함" if react_ratio>=0.5 else "보통")
        _news_alert_history[theme_key] = time.time()
        signals.append({"theme_key":theme_key,"theme_desc":theme_info["desc"],
                         "headline":matched[0][:60],"rising":rising_stocks,
                         "surging":[s for s in stock_status if s["surging"]],
                         "not_yet":[s for s in stock_status if s["not_yet"]][:4],
                         "react_ratio":react_ratio,"sector_bonus":sector_bonus,
                         "signal_strength":strength,"total":total})
    return signals

def send_news_theme_alert(signal: dict):
    emoji = {"매우강함":"🔥","강함":"✅","보통":"🟡"}.get(signal["signal_strength"],"📢")
    react_pct = int(signal["react_ratio"]*100)
    rising_block = "".join([f"  📈 <b>{s['name']}</b> {s['change_rate']:+.1f}%"
                             +(f" 🔊{s['volume_ratio']:.0f}x" if s["vol_on"] else "")
                             +(" 🚀" if s["surging"] else "")+"\n" for s in signal["rising"]])
    not_yet_block = "".join([f"  ⏳ {s['name']} {s['change_rate']:+.1f}%\n" for s in signal["not_yet"]])
    send(f"{emoji} <b>[뉴스+주가 연동]</b>  {signal['signal_strength']}\n"
         f"🕐 {datetime.now().strftime('%H:%M:%S')}\n\n"
         f"📰 <b>{signal['theme_desc']}</b>\n💬 {signal['headline']}...\n\n"
         f"━━━━━━━━━━━━━━━\n"
         f"🏭 섹터 반응: <b>{len(signal['rising'])}/{signal['total']}개</b> ({react_pct}%)  +{signal['sector_bonus']}점\n\n"
         +(f"🔥 <b>실제 상승 중</b>\n{rising_block}\n" if rising_block else "")
         +(f"🎯 <b>아직 안 오른 종목 (추격 기회)</b>\n{not_yet_block}\n" if not_yet_block else "")
         +"━━━━━━━━━━━━━━━")

# ============================================================
# DART
# ============================================================
def _fetch_dart_list(today: str) -> list:
    items = []
    for ptype in ["A","B","D"]:
        try:
            resp = requests.get("https://opendart.fss.or.kr/api/list.json",
                                params={"crtfc_key":DART_API_KEY,"bgn_de":today,"end_de":today,
                                        "pblntf_ty":ptype,"page_count":100},timeout=15)
            items += resp.json().get("list",[])
        except: pass
    return items

def run_dart_intraday():
    if not DART_API_KEY or not is_market_open(): return
    today = datetime.now().strftime("%Y%m%d")
    try:
        for item in _fetch_dart_list(today):
            rcept_no = item.get("rcept_no","")
            if not rcept_no or rcept_no in _dart_seen_ids: continue
            title,company,code = item.get("report_nm",""),item.get("corp_name",""),item.get("stock_code","")
            if not code: continue
            matched_urgent = [kw for kw in DART_URGENT_KEYWORDS if kw in title]
            matched_pos    = [kw for level,kws in DART_KEYWORDS.items() for kw in kws if kw in title]
            if not matched_urgent and not matched_pos: continue
            _dart_seen_ids.add(rcept_no)
            is_risk = any(kw in title for kw in DART_RISK_KEYWORDS)

            # ── 주가 상세 조회 (실패해도 최대한 표시) ──
            cur         = {}
            price       = 0
            change_rate = 0
            vol_ratio   = 0
            today_vol   = 0
            for _attempt in range(2):
                try:
                    cur         = get_stock_price(code)
                    price       = cur.get("price", 0)
                    change_rate = cur.get("change_rate", 0)
                    vol_ratio   = cur.get("volume_ratio", 0)
                    today_vol   = cur.get("today_vol", 0)
                    if price: break
                except: time.sleep(1)

            if not (change_rate >= 1.0) and not is_risk:
                print(f"  ⏭ DART [{company}] 주가 반응 없음 → 스킵"); continue

            # ── 추가 지표 (각각 독립적으로 실패 허용) ──
            z = 0
            try: z = get_volume_zscore(code, today_vol) if today_vol else 0
            except: pass

            rs = 0
            try: rs = get_relative_strength(change_rate)
            except: pass

            ma20_dev = 0.0
            try: ma20_dev = get_ma20_deviation(code)
            except: pass

            prev_upper = False
            try: prev_upper = was_upper_limit_yesterday(code)
            except: pass

            # 외국인·기관 수급
            inv_text = ""
            try:
                inv   = get_investor_trend(code)
                f_net = inv.get("foreign_net", 0)
                i_net = inv.get("institution_net", 0)
                if   f_net > 0 and i_net > 0: inv_text = "\n✅ 외국인+기관 동시 순매수"
                elif f_net > 0:               inv_text = "\n🟡 외국인 순매수"
                elif i_net > 0:               inv_text = "\n🟡 기관 순매수"
                elif f_net < 0 and i_net < 0: inv_text = "\n🔴 외국인+기관 동시 순매도"
            except: pass

            # ATR 손절·목표가
            entry = price or 0
            stop = target = stop_pct = target_pct = 0
            atr_used = False
            if price:
                try:
                    stop, target, stop_pct, target_pct, atr_used = calc_stop_target(code, entry)
                except: pass
            atr_tag = " (ATR)" if atr_used else " (고정)"

            # 섹터 모멘텀 (실패 시 백그라운드 재시도)
            sector_info = {"bonus":0,"detail":[],"rising":[],"flat":[],"theme":"","summary":""}
            try:
                if price:
                    sector_info = calc_sector_momentum(code, company)
            except: pass

            # 섹터 지속 모니터링 + 진입가 감시 등록 (공시 발생 종목)
            if price:
                start_sector_monitor(code, company)

            # ── 이모지 및 등급 ──
            emoji = "🚨" if is_risk else ("🚀" if change_rate >= 10.0 else "📢")
            tag   = "⚠️ 위험 공시" if is_risk else "✅ 주요 공시"
            all_kw = list(dict.fromkeys(matched_urgent + matched_pos))

            # ── 주가 블록 (항상 표시, 조회 실패 시 안내) ──
            if price:
                vol_str    = f"<b>{vol_ratio:.1f}배</b> (5일 평균 대비)" if vol_ratio else "조회 중"
                zscore_str = f"  📊 Z={z:.1f}σ" if z >= VOL_ZSCORE_MIN else ""
                rs_str     = f"  💪 RS={rs:.1f}x" if rs >= RS_MIN else ""
                ma_str     = f"  📐 20일선 {ma20_dev:+.1f}%" if ma20_dev else ""
                prev_str   = "\n🔁 전일 상한가 종목" if prev_upper else ""
                price_block = (
                    f"\n━━━━━━━━━━━━━━━\n"
                    f"💰 현재가: <b>{price:,}원</b>  (<b>{change_rate:+.1f}%</b>)\n"
                    f"📊 거래량: {vol_str}{zscore_str}\n"
                    f"📈 코스피 상대강도: {rs_str if rs_str else '—'}{ma_str}"
                    f"{inv_text}{prev_str}"
                )
            else:
                price_block = "\n━━━━━━━━━━━━━━━\n💰 현재가: 조회 실패 (장 중 API 지연)"

            # ── 손절·목표가 블록 ──
            if price and stop and target:
                stop_block = (
                    f"\n━━━━━━━━━━━━━━━\n"
                    f"🎯 진입가: <b>{entry:,}원</b>\n"
                    f"🛡 손절가: <b>{stop:,}원</b>  (-{stop_pct:.1f}%){atr_tag}\n"
                    f"🏆 목표가: <b>{target:,}원</b>  (+{target_pct:.1f}%){atr_tag}"
                )
            else:
                stop_block = ""

            # ── 섹터 블록 ──
            sector_block = ""
            rising = sector_info.get("rising", [])
            flat   = sector_info.get("flat", [])
            detail = sector_info.get("detail", [])
            theme  = sector_info.get("theme", "")
            if detail:
                react_cnt    = len(rising)
                total_cnt    = len(detail)
                sector_block = f"\n━━━━━━━━━━━━━━━\n🏭 섹터 [{theme}]: <b>{react_cnt}/{total_cnt}개</b> 동반 상승\n"
                sector_block += "".join([
                    f"  📈 {r['name']} {r['change_rate']:+.1f}%"
                    + (f" 🔊{r['volume_ratio']:.0f}x" if r.get("volume_ratio",0)>=2 else "") + "\n"
                    for r in rising[:4]
                ])
                for r in flat[:2]:
                    sector_block += f"  ➖ {r['name']} {r['change_rate']:+.1f}%\n"
            elif theme:
                sector_block = f"\n━━━━━━━━━━━━━━━\n🏭 섹터 [{theme}]: 동업종 조회 중\n"

            send_with_chart_buttons(
                f"{emoji} <b>[공시+주가 연동]</b>  {tag}\n"
                f"🕐 {datetime.now().strftime('%H:%M:%S')}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"{'🔴' if is_risk else '🟡'} <b>{company}</b>  <code>{code}</code>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📌 {title}\n"
                f"🔑 키워드: {', '.join(all_kw)}"
                f"{price_block}"
                f"{sector_block}"
                f"{stop_block}",
                code, company
            )
            print(f"  📋 공시 알림: {company} {change_rate:+.1f}% - {title}")
    except Exception as e: print(f"⚠️ DART 오류: {e}")

def analyze_dart_disclosures():
    if not DART_API_KEY: return
    today = datetime.now().strftime("%Y%m%d")
    try:
        scored = []
        for item in _fetch_dart_list(today):
            title,company,code = item.get("report_nm",""),item.get("corp_name",""),item.get("stock_code","")
            if not code: continue
            score,matched,strength = 0,[],""
            for level,keywords in DART_KEYWORDS.items():
                for kw in keywords:
                    if kw in title:
                        score+={"매우강함":30,"강함":20,"보통":10}[level]; matched.append(kw); strength=level
            if score>=30 and matched:
                scored.append({"code":code,"company":company,"title":title,"score":score,"matched":matched,"strength":strength})
        scored.sort(key=lambda x:x["score"],reverse=True)
        if not scored[:5]: send("📋 <b>오늘 주목할 공시 없음</b>"); return
        msg = f"📋 <b>내일 주목 종목 - DART 분석</b>\n🗓 {today[:4]}.{today[4:6]}.{today[6:]}\n━━━━━━━━━━━━━━━\n\n"
        for i,item in enumerate(scored[:5],1):
            e = {"매우강함":"🔴","강함":"🟡","보통":"🟢"}.get(item["strength"],"⚪")
            msg += f"{i}. {e} <b>{item['company']}</b> ({item['code']})\n   📌 {item['title']}\n   🔑 {', '.join(item['matched'])}\n   ⭐ {item['score']}점\n\n"
        send(msg+"━━━━━━━━━━━━━━━\n⚠️ 내일 장 시작 전 확인 후 진입 판단")
    except Exception as e: print(f"⚠️ DART 분석 오류: {e}")

# ============================================================
# 텔레그램 명령어
# ============================================================
_tg_offset = 0

def _send_menu(title: str = ""):
    """
    인라인 버튼 메뉴 발송
    버튼을 누르면 해당 명령어 텍스트가 채팅창에 입력됨
    (텔레그램 callback_query 방식 대신 switch_inline_query_current_chat 사용)
    """
    menu_title = title or "📌 <b>명령어 메뉴</b>  — 버튼을 눌러 실행하세요"
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🤖 봇 상태",        "callback_data": "cmd_status"},
                {"text": "📋 감시 종목",       "callback_data": "cmd_list"},
                {"text": "🏆 오늘 TOP 5",      "callback_data": "cmd_top"},
            ],
            [
                {"text": "📊 일일 성과",       "callback_data": "cmd_daily"},
                {"text": "📅 이번 주 성과",    "callback_data": "cmd_week"},
                {"text": "📈 승률 통계",       "callback_data": "cmd_stats"},
            ],
            [
                {"text": "🔵 NXT 현황",        "callback_data": "cmd_nxt"},
                {"text": "⏸ 알림 정지",        "callback_data": "cmd_stop"},
                {"text": "▶️ 알림 재개",        "callback_data": "cmd_resume"},
            ],
            [
                {"text": "🗜 컴팩트 전환",      "callback_data": "cmd_compact"},
                {"text": "⚙️ BotFather 설정법", "callback_data": "cmd_setup"},
            ],
        ]
    }
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id":    TELEGRAM_CHAT_ID,
                "text":       menu_title,
                "parse_mode": "HTML",
                "reply_markup": keyboard,
            },
            timeout=10
        )
    except Exception as e:
        print(f"⚠️ 메뉴 발송 오류: {e}")
        send(menu_title)   # 버튼 실패 시 텍스트로 폴백

def _handle_callback(callback_id: str, data: str):
    """인라인 버튼 콜백 처리"""
    # 버튼 누름 확인 응답 (텔레그램 필수)
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery",
            json={"callback_query_id": callback_id},
            timeout=5
        )
    except: pass

    cmd_map = {
        "cmd_status":  "/status",
        "cmd_list":    "/list",
        "cmd_top":     "/top",
        "cmd_daily":   "/daily",
        "cmd_nxt":     "/nxt",
        "cmd_week":    "/week",
        "cmd_stats":   "/stats",
        "cmd_stop":    "/stop",
        "cmd_resume":  "/resume",
        "cmd_compact": "/compact",
        "cmd_setup":   "/설정",
    }
    return cmd_map.get(data, "")


def poll_telegram_commands():
    global _tg_offset, _bot_paused
    try:
        resp = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
                            params={"offset":_tg_offset,"timeout":5},timeout=10)
        for update in resp.json().get("result",[]):
            _tg_offset = update["update_id"]+1

            # ── 인라인 버튼 콜백 처리 ──
            cb = update.get("callback_query")
            if cb:
                text = _handle_callback(cb["id"], cb.get("data",""))
                if not text: continue
                raw = text
            else:
                raw  = update.get("message",{}).get("text","").strip()
                if not raw: continue

            text = raw.lower()
            if not text.startswith("/"): continue

            # ── /status ──
            if text == "/status":
                rate_str = (f"\n📊 EARLY 성공률: {_early_feedback['success']}/{_early_feedback['total']} "
                            f"({_early_feedback.get('rate',0)*100:.0f}%)") if _early_feedback.get("total",0)>=5 else ""
                nxt_str  = f"\n🔵 NXT: {'운영 중' if is_nxt_open() else '마감'}"
                send(f"🤖 <b>봇 상태</b>  {BOT_VERSION}  {'⏸ 일시정지' if _bot_paused else '▶️ 실행 중'}\n"
                     f"🕐 {datetime.now().strftime('%H:%M:%S')}  📅 {BOT_DATE}\n"
                     f"📡 장 {'열림' if is_market_open() else '닫힘'}{nxt_str}\n"
                     f"👁 감시: {len(_detected_stocks)}개  |  동적테마: {len(_dynamic_theme_map)}개\n"
                     f"⚙️ EARLY 조건: >{_early_price_min_dynamic}%, >{_early_volume_min_dynamic}배{rate_str}\n\n"
                     f"💬 /result 종목명 수익률  로 결과 기록\n"
                     f"예) /result 대주산업 +12.5")

            # ── /list ──
            elif text == "/list":
                if not _detected_stocks:
                    send("📋 감시 중인 종목 없음")
                else:
                    send("📋 <b>감시 중인 종목</b>\n" +
                         "\n".join([f"• <b>{v['name']}</b> ({k}) — {v.get('carry_day',0)}일차"
                                    for k, v in _detected_stocks.items()]))

            # ── /stop / /resume ──
            elif text == "/stop":
                _bot_paused = True;  send("⏸ <b>봇 일시정지</b>  /resume 으로 재개")
            elif text == "/resume":
                _bot_paused = False; send("▶️ <b>봇 재개</b>")

            # ── /compact — 컴팩트 모드 토글 ──
            elif text in ("/compact", "/컴팩트"):
                global _compact_mode
                _compact_mode = not _compact_mode
                _save_compact_mode()
                mode_str = "🗜 <b>컴팩트 모드 ON</b>\n알림이 1~2줄 요약으로 발송됩니다" \
                           if _compact_mode else \
                           "📋 <b>상세 모드 ON</b>\n알림이 기존 상세 포맷으로 발송됩니다"
                send(mode_str)

            # ── /백업 — 즉시 수동 백업 ──
            elif text in ("/백업", "/backup"):
                send("💾 <b>수동 백업 시작...</b>")
                ok_gist = backup_to_gist()
                ok_tg   = False
                if not ok_gist:
                    ok_tg = backup_to_telegram()
                if ok_gist:
                    send(f"✅ <b>GitHub Gist 백업 완료</b>  {BOT_VERSION}\n"
                         f"Gist ID: <code>{_gist_id_runtime}</code>")
                elif ok_tg:
                    send(f"✅ <b>텔레그램 파일 백업 완료</b>  {BOT_VERSION}")
                else:
                    send("❌ 백업 실패\n"
                         "Railway Variables에 <b>GITHUB_GIST_TOKEN</b> 설정 필요\n"
                         "또는 텔레그램 봇 설정 확인")

            # ── /top — 오늘의 최우선 종목 즉시 조회 ──
            elif text == "/top":
                if not _today_top_signals:
                    send("📊 오늘 포착된 신호 없음 (장 시작 후 신호 누적 중)")
                else:
                    send_top_signals()

            # ── /nxt — NXT 현재 동향 즉시 조회 ──
            elif text == "/nxt":
                if not is_nxt_open():
                    send("🔵 NXT 현재 마감 중 (08:00~20:00 운영)")
                else:
                    try:
                        stocks = get_nxt_surge_stocks()
                        if not stocks:
                            send("🔵 NXT 현재 급등 종목 없음")
                        else:
                            top = sorted(stocks, key=lambda x: abs(x.get("change_rate",0)), reverse=True)[:7]
                            lines = "\n".join(
                                f"  {'📈' if s['change_rate']>0 else '📉'} {s['name']} "
                                f"<b>{s['change_rate']:+.1f}%</b>  🔊{s.get('volume_ratio',0):.0f}x"
                                for s in top
                            )
                            send(f"🔵 <b>NXT 실시간 동향</b>  {datetime.now().strftime('%H:%M')}\n"
                                 f"━━━━━━━━━━━━━━━\n{lines}")
                    except Exception as e:
                        send(f"⚠️ NXT 조회 오류: {e}")

            # ── /week — 이번 주 잠정 성과 즉시 조회 ──
            elif text == "/week":
                try:
                    data = {}
                    with open(SIGNAL_LOG_FILE,"r") as f: data = json.load(f)
                    today    = datetime.now()
                    this_mon = (today - timedelta(days=today.weekday())).strftime("%Y%m%d")
                    this_fri = today.strftime("%Y%m%d")
                    week_done    = [v for v in data.values()
                                    if this_mon <= v.get("detect_date","") <= this_fri
                                    and v.get("status") in ["수익","손실","본전"]]
                    week_tracking = [v for v in data.values()
                                     if this_mon <= v.get("detect_date","") <= this_fri
                                     and v.get("status") == "추적중"]
                    if not week_done and not week_tracking:
                        send("📅 이번 주 신호 없음"); continue
                    msg = f"📅 <b>이번 주 잠정 성과</b>  {this_mon[4:6]}/{this_mon[6:]} ~ {this_fri[4:6]}/{this_fri[6:]}\n━━━━━━━━━━━━━━━\n"
                    if week_done:
                        pnls    = [v["pnl_pct"] for v in week_done]
                        wins    = sum(1 for p in pnls if p > 0)
                        avg_pnl = sum(pnls) / len(pnls)
                        msg += (f"\n✅ <b>확정</b>  {len(week_done)}건\n"
                                f"  승률 {wins/len(week_done)*100:.0f}%  평균 {avg_pnl:+.1f}%\n")
                        for v in sorted(week_done, key=lambda x: x.get("pnl_pct",0), reverse=True)[:5]:
                            dot = "✅" if v["pnl_pct"]>0 else "🔴"
                            msg += f"  {dot} {v['name']} {v['pnl_pct']:+.1f}%\n"
                    if week_tracking:
                        msg += f"\n⏳ <b>추적 중</b>  {len(week_tracking)}건\n"
                        for v in week_tracking[:4]:
                            try:
                                cur   = get_stock_price(v["code"])
                                price = cur.get("price",0)
                                entry = v.get("entry_price",0)
                                if price and entry:
                                    pnl = (price-entry)/entry*100
                                    dot = "🟢" if pnl>=0 else "🟠"
                                    msg += f"  {dot} {v['name']} {pnl:+.1f}% (잠정)\n"
                            except: continue
                    send(msg)
                except Exception as e:
                    send(f"⚠️ 주간 조회 오류: {e}")

            # ── /daily — 오늘 일일 성과 즉시 조회 ──
            elif text in ("/daily", "/오늘"):
                try:
                    data = {}
                    with open(SIGNAL_LOG_FILE,"r") as f: data = json.load(f)
                    today     = datetime.now().strftime("%Y%m%d")
                    today_str = datetime.now().strftime("%m/%d")
                    sig_labels = {
                        "UPPER_LIMIT":"상한가","NEAR_UPPER":"상한가근접","SURGE":"급등",
                        "EARLY_DETECT":"조기포착","MID_PULLBACK":"중기눌림목",
                        "ENTRY_POINT":"단기눌림목","STRONG_BUY":"강력매수",
                    }
                    today_recs   = [v for v in data.values() if v.get("detect_date") == today]
                    done_today   = [v for v in today_recs if v.get("status") != "추적중"]
                    tracking_today = [v for v in today_recs if v.get("status") == "추적중"]
                    # 이월 추적 중 포함
                    all_tracking = [v for v in data.values() if v.get("status") == "추적중"]

                    if not today_recs and not all_tracking:
                        send(f"📊 {today_str} 오늘 신호 없음"); continue

                    msg = f"📊 <b>일일 성과</b>  {today_str}  {datetime.now().strftime('%H:%M')}\n━━━━━━━━━━━━━━━\n"

                    # ── 오늘 확정 결과 ──
                    if done_today:
                        pnls     = [v.get("pnl_pct",0) for v in done_today]
                        wins     = sum(1 for p in pnls if p > 0)
                        losses   = sum(1 for p in pnls if p < 0)
                        avg_pnl  = sum(pnls) / len(pnls)
                        win_rate = round(wins / len(done_today) * 100)
                        msg += (f"\n✅ <b>오늘 확정  {len(done_today)}건</b>\n"
                                f"  승률 <b>{win_rate}%</b>  평균 <b>{avg_pnl:+.1f}%</b>"
                                f"  수익 {wins}건  손실 {losses}건\n")
                        for v in sorted(done_today, key=lambda x: x.get("pnl_pct",0), reverse=True):
                            pnl  = v.get("pnl_pct", 0)
                            dot  = "✅" if pnl > 0 else ("🔴" if pnl < 0 else "➖")
                            sig  = sig_labels.get(v.get("signal_type",""), "")
                            msg += f"  {dot} {v['name']} <b>{pnl:+.1f}%</b>  {sig}\n"
                    else:
                        msg += "\n📭 오늘 확정된 신호 없음\n"

                    # ── 추적 중 잠정 수익률 ──
                    if all_tracking:
                        msg += f"\n⏳ <b>추적 중  {len(all_tracking)}건</b>  (잠정)\n"
                        rows = []
                        for v in all_tracking:
                            try:
                                price = 0
                                if is_nxt_open() and is_nxt_listed(v.get("code","")):
                                    price = get_nxt_stock_price(v["code"]).get("price", 0)
                                if not price:
                                    price = get_stock_price(v["code"]).get("price", 0)
                                entry = v.get("entry_price", 0)
                                if price and entry:
                                    pnl = (price - entry) / entry * 100
                                    nxt_tag = " 🔵" if is_nxt_open() and is_nxt_listed(v.get("code","")) else ""
                                    rows.append((pnl, v["name"], nxt_tag))
                            except: continue
                        for pnl, name, nxt_tag in sorted(rows, key=lambda x: x[0], reverse=True):
                            dot = "🟢" if pnl >= 0 else "🟠"
                            msg += f"  {dot} {name} <b>{pnl:+.1f}%</b>{nxt_tag}\n"

                    send(msg)
                except Exception as e:
                    send(f"⚠️ 일일 성과 조회 오류: {e}")

            # ── /result 종목명 수익률 ──
            elif text.startswith("/result"):
                _handle_result_command(raw)

            # ── /skip 종목명 이유 ──
            elif text.startswith("/진입"):
                _handle_entry_confirm_command(raw)
            elif text.startswith("/skip"):
                _handle_skip_command(raw)

            # ── /stats ──
            elif text == "/stats":
                _send_stats()

            # ── /menu 또는 /도움 — 버튼 메뉴 ──
            elif text in ("/menu", "/도움", "/help"):
                _send_menu()

            # ── /설정 — BotFather 명령어 등록 가이드 ──
            elif text in ("/설정", "/setup"):
                send(
                    "⚙️ <b>BotFather 명령어 등록 방법</b>\n"
                    "텔레그램에서 / 입력 시 한글 설명이 자동완성으로 뜨게 됩니다\n\n"
                    "<b>① @BotFather 에게 아래 명령어 전송</b>\n"
                    "<code>/setcommands</code>\n\n"
                    "<b>② 봇 선택 후 아래 내용 그대로 복붙</b>\n"
                    "━━━━━━━━━━━━━━━\n"
                    "<code>"
                    "status - 🤖 봇 상태 및 버전 확인\n"
                    "list - 📋 현재 감시 중인 종목 목록\n"
                    "top - 🏆 오늘의 최우선 종목 TOP 5\n"
                    "daily - 📊 오늘 일일 성과 즉시 조회\n"
                    "nxt - 🔵 NXT 넥스트레이드 실시간 동향\n"
                    "week - 📅 이번 주 잠정 성과 조회\n"
                    "stats - 📈 신호 유형별 승률 통계\n"
                    "compact - 🗜 컴팩트·상세 알림 모드 전환\n"
                    "stop - ⏸ 알림 일시 정지\n"
                    "resume - ▶️ 알림 재개\n"
                    "menu - 📌 버튼 메뉴 열기\n"
                    "result - ✍️ 수익률 수동 기록 (예: result 대주산업 +12.5)"
                    "</code>\n"
                    "━━━━━━━━━━━━━━━\n"
                    "③ 등록 완료 후 채팅창에서 / 입력하면\n"
                    "   한글 설명과 함께 자동완성이 나타납니다"
                )

            # ── 알 수 없는 명령어 → 메뉴 표시 ──
            else:
                _send_menu(f"❓ <b>'{raw}'</b> 는 알 수 없는 명령어예요\n아래 버튼으로 실행해보세요")
    except Exception as e:
        print(f"⚠️ TG 명령어 오류: {e}")



def _request_actual_entry_confirm(rec: dict):
    """
    이론 추적 완료 시 → 실제 진입 여부 확인 요청 알림.
    사용자가 /result 또는 /skip으로 응답.
    """
    name    = rec.get("name", "")
    code    = rec.get("code", "")
    pnl     = rec.get("pnl_pct", 0)
    sig     = rec.get("signal_type", "")
    pnl_str = f"+{pnl:.1f}%" if pnl >= 0 else f"{pnl:.1f}%"
    emoji   = "✅" if pnl > 0 else "🔴"
    msg = (
        f"❓ <b>[진입 여부 확인]</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{emoji} <b>{name}</b>  <code>{code}</code>\n"
        f"이론 결과: <b>{pnl_str}</b>  [{sig}]\n"
        f"━━━━━━━━━━━━━━━\n"
        f"이 종목에 실제 진입하셨나요?\n\n"
        f"✅ 진입했다면:\n"
        f"<code>/result {name} 실제수익률</code>\n"
        f"예) /result {name} +8.5\n\n"
        f"⏭ 진입 못 했다면:\n"
        f"<code>/skip {name} 이유</code>\n"
        f"예) /skip {name} 시간없음"
    )
    send(msg)


def _handle_entry_confirm_command(raw: str):
    """
    /진입 종목명 [실제진입가]  처리
    예) /진입 대주산업          ← 봇이 계산한 진입가로 확정
    예) /진입 대주산업 15300    ← 실제 진입가 직접 입력

    목적: 내가 실제 진입한 종목을 기록해서 /stats의 "내 실제 수익" 에 반영.
    봇의 이론 추적(signal_log)은 계속 병행 → 봇 조건 학습에 활용됨.
    즉, 진입 여부와 무관하게 이론 데이터는 항상 쌓임.
    """
    try:
        parts      = raw.strip().split(maxsplit=2)
        name_input = parts[1] if len(parts) > 1 else ""
        price_input = parts[2] if len(parts) > 2 else ""

        if not name_input:
            send("⚠️ 형식: /진입 종목명 [실제진입가]\n"
                 "예) /진입 대주산업\n"
                 "예) /진입 대주산업 15300"); return

        data = {}
        try:
            with open(SIGNAL_LOG_FILE, "r") as f: data = json.load(f)
        except: pass

        matched = []
        for log_key, rec in data.items():
            if name_input in rec.get("name", "") and rec.get("actual_entry") is None:
                matched.append((log_key, rec))

        if not matched:
            send(f"❓ '{name_input}' 종목을 찾을 수 없어요.\n"
                 f"추적 중인 종목명을 확인해주세요."); return

        # 가장 최근 신호 선택
        matched.sort(key=lambda x: x[1].get("detect_date",""), reverse=True)
        log_key, rec = matched[0]

        # 실제 진입가 처리
        try:
            actual_price = int(price_input) if price_input else rec.get("entry_price", 0)
        except:
            actual_price = rec.get("entry_price", 0)

        rec["actual_entry"]       = True
        rec["actual_entry_price"] = actual_price
        # 실제 진입가로 손절/목표 재계산
        if actual_price and actual_price != rec.get("entry_price", 0):
            diff_ratio = actual_price / rec["entry_price"] if rec.get("entry_price") else 1
            rec["stop_price"]    = int(rec.get("stop_price",  0) * diff_ratio / 10) * 10
            rec["target_price"]  = int(rec.get("target_price", 0) * diff_ratio / 10) * 10

        with open(SIGNAL_LOG_FILE, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        entry_p  = actual_price or rec.get("entry_price", 0)
        stop_p   = rec.get("stop_price", 0)
        target_p = rec.get("target_price", 0)
        stop_pct  = round((stop_p   - entry_p) / entry_p * 100, 1) if entry_p else 0
        tgt_pct   = round((target_p - entry_p) / entry_p * 100, 1) if entry_p else 0
        send(f"✅ <b>[진입 확정]</b>\n"
             f"━━━━━━━━━━━━━━━\n"
             f"🟢 <b>{rec['name']}</b>  <code>{rec['code']}</code>\n"
             f"━━━━━━━━━━━━━━━\n"
             f"📍 실제 진입가: <b>{entry_p:,}원</b>\n"
             f"🛡 손절가:  <b>{stop_p:,}원</b>  ({stop_pct:+.1f}%)\n"
             f"🏆 목표가:  <b>{target_p:,}원</b>  ({tgt_pct:+.1f}%)\n"
             f"━━━━━━━━━━━━━━━\n"
             f"이 기준으로 자동 추적을 시작합니다.\n"
             f"결과는 /result 로 직접 입력하거나\n"
             f"목표가/손절가 도달 시 자동 확정됩니다.")
        print(f"  ✅ 진입 확정: {rec['name']} {entry_p:,}원")
    except Exception as e:
        _log_error("_handle_entry_confirm_command", e)
        send(f"⚠️ /진입 처리 오류: {e}")

def _handle_skip_command(raw: str):
    """
    /skip 종목명 이유  처리
    예) /skip 대주산업 시간없음
    → actual_entry=False, skip_reason 기록
    → 봇 학습: 어떤 상황에서 진입 기회를 놓치는지 패턴 분석
    """
    try:
        parts      = raw.strip().split(maxsplit=2)
        name_input = parts[1] if len(parts) > 1 else ""
        reason     = parts[2] if len(parts) > 2 else "미입력"

        if not name_input:
            send("⚠️ 형식: /skip 종목명 이유\n예) /skip 대주산업 시간없음\n\n"
                 "이유 예시: 시간없음 / 조건불일치 / 이미상승 / 분산투자 / 기타"); return

        data = {}
        try:
            with open(SIGNAL_LOG_FILE, "r") as f: data = json.load(f)
        except: pass

        matched_key  = None
        matched_name = None
        # 가장 최근 해당 종목 찾기
        for key in sorted(data.keys(), reverse=True):
            rec = data[key]
            if name_input in rec.get("name", ""):
                matched_key  = key
                matched_name = rec["name"]
                break

        if not matched_key:
            send(f"⚠️ '{name_input}' 종목을 찾을 수 없어요.\n/list 로 감시 중인 종목 확인"); return

        data[matched_key]["actual_entry"]  = False
        data[matched_key]["skip_reason"]   = reason
        data[matched_key]["actual_pnl"]    = None

        with open(SIGNAL_LOG_FILE, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        theo_pnl = data[matched_key].get("pnl_pct", 0)
        theo_str = f"+{theo_pnl:.1f}%" if theo_pnl >= 0 else f"{theo_pnl:.1f}%"
        send(
            f"⏭ <b>진입 스킵 기록 완료</b>\n"
            f"종목: <b>{matched_name}</b>\n"
            f"이유: {reason}\n"
            f"이론 수익률: {theo_str} (봇 학습에 반영됩니다)\n\n"
            f"💡 스킵 패턴도 쌓이면 봇이 진입 타이밍을 개선해요."
        )
        print(f"  ⏭ 스킵 기록: {matched_name} / {reason}")

    except Exception as e:
        send(f"⚠️ 스킵 기록 오류: {e}")

def _handle_result_command(raw: str):
    """
    /result 종목명 수익률  처리
    예) /result 대주산업 +12.5
    → signal_log.json (메인) + early_detect_log.json (하위호환) 동시 업데이트
    → 자동 튜닝 즉시 반영
    """
    try:
        parts = raw.strip().split()
        if len(parts) < 3:
            send("⚠️ 형식: /result 종목명 수익률\n예) /result 대주산업 +12.5"); return
        name_input = parts[1]
        pnl_str    = parts[2].replace("%","")
        pnl        = float(pnl_str)

        result_emoji = "✅" if pnl > 0 else ("🔴" if pnl < 0 else "➖")
        status       = "수익" if pnl > 0 else ("손실" if pnl < 0 else "본전")
        today        = datetime.now().strftime("%Y%m%d")
        matched_name = None
        signal_type  = "MANUAL"

        # ── ① signal_log.json 에서 추적 중인 종목 찾기 (메인) ──
        sig_data = {}
        sig_matched_key = None
        try:
            with open(SIGNAL_LOG_FILE, "r") as f: sig_data = json.load(f)
        except: pass

        # 종목명 포함 + 추적중 상태인 것 우선 매칭
        for key, rec in sig_data.items():
            if name_input in rec.get("name", "") and rec.get("status") == "추적중":
                sig_matched_key = key
                matched_name    = rec["name"]
                signal_type     = rec.get("signal_type", "MANUAL")
                # 현재가 조회해서 수익률 검증
                try:
                    cur_p = get_stock_price(rec["code"]).get("price", 0)
                    entry = rec.get("entry_price", 0)
                    if cur_p and entry:
                        auto_pnl = round((cur_p - entry) / entry * 100, 1)
                        # 입력값과 자동계산값이 5%p 이상 차이나면 경고
                        if abs(pnl - auto_pnl) > 5:
                            send(f"⚠️ 입력 수익률({pnl:+.1f}%)과 현재가 기준({auto_pnl:+.1f}%) 차이가 큽니다.\n"
                                 f"현재가: {cur_p:,}원  |  입력값 그대로 기록합니다.")
                except: pass
                break

        if sig_matched_key:
            rec = sig_data[sig_matched_key]
            # 이론 수익률이 아직 없으면 함께 기록
            if not rec.get("pnl_pct"):
                rec["pnl_pct"]     = pnl
                rec["status"]      = status
                rec["exit_date"]   = today
                rec["exit_time"]   = datetime.now().strftime("%H:%M:%S")
                rec["exit_reason"] = "수동입력"
            # 실제 진입 결과 기록 (별도 보존)
            rec["actual_entry"]     = True
            rec["actual_pnl"]       = pnl
            rec["actual_exit_date"] = today
            rec["skip_reason"]      = ""
            with open(SIGNAL_LOG_FILE, "w") as f:
                json.dump(sig_data, f, ensure_ascii=False, indent=2)

        # ── ② early_detect_log.json 도 동시 업데이트 (하위 호환) ──
        early_data = {}
        try:
            with open(EARLY_LOG_FILE, "r") as f: early_data = json.load(f)
        except: pass

        early_matched = None
        for code, info in early_data.items():
            if name_input in info.get("name", ""):
                early_matched = code; break

        if early_matched:
            early_data[early_matched].update({
                "status": status, "pnl_pct": pnl,
                "exit_date": today,
            })
        else:
            # 둘 다 없으면 수동 기록으로 signal_log에 새로 추가
            new_key = f"manual_{datetime.now().strftime('%m%d%H%M')}"
            sig_data[new_key] = {
                "log_key": new_key, "code": new_key,
                "name": name_input, "signal_type": "MANUAL",
                "detect_date": today, "detect_time": datetime.now().strftime("%H:%M:%S"),
                "detect_price": 0, "entry_price": 0,
                "stop_price": 0, "target_price": 0,
                "status": status, "pnl_pct": pnl,
                "exit_date": today, "exit_time": datetime.now().strftime("%H:%M:%S"),
                "exit_reason": "수동입력",
                "score": 0, "sector_bonus": 0, "sector_theme": "",
            }
            with open(SIGNAL_LOG_FILE, "w") as f:
                json.dump(sig_data, f, ensure_ascii=False, indent=2)
            matched_name = name_input

        if early_matched:
            with open(EARLY_LOG_FILE, "w") as f:
                json.dump(early_data, f, ensure_ascii=False, indent=2)

        display_name = matched_name or name_input
        send(f"{result_emoji} <b>결과 기록 완료</b>\n"
             f"종목: <b>{display_name}</b>\n"
             f"수익률: <b>{pnl:+.1f}%</b>  ({status})\n"
             f"신호: {signal_type}\n\n"
             f"/stats 로 전체 통계 확인")

        # 즉시 자동 튜닝 반영
        load_tracker_feedback()

    except ValueError:
        send("⚠️ 수익률 형식 오류. 예) /result 대주산업 +12.5")
    except Exception as e:
        send(f"⚠️ 결과 기록 오류: {e}")


def _send_stats():
    """신호 유형별 승률·평균 수익률 통계 전송 (signal_log.json 기반)"""
    try:
        data = {}
        try:
            with open(SIGNAL_LOG_FILE, "r") as f: data = json.load(f)
        except: pass

        # ── 이론 완료 (전체 — 봇 학습 + 신호 품질 평가용) ──
        completed      = [v for v in data.values() if v.get("status") in ["수익","손실","본전"]]
        tracking       = [v for v in data.values() if v.get("status") == "추적중"]
        # ── 실제 진입 (내 수익 통계용 — /result 또는 /진입 확인분만) ──
        actual_entered = [v for v in data.values()
                          if v.get("actual_entry") is True and v.get("actual_pnl") is not None]
        skipped        = [v for v in data.values() if v.get("actual_entry") is False]
        unconfirmed    = [v for v in completed     if v.get("actual_entry") is None]

        if len(completed) < 3:
            send(f"📊 아직 이론 결과가 {len(completed)}건뿐이에요. (추적 중: {len(tracking)}건)\n"
                 f"결과가 쌓이면 자동으로 통계가 갱신돼요."); return


        type_labels = {
            "UPPER_LIMIT":  "🚨 상한가",
            "NEAR_UPPER":   "🔥 상한가근접",
            "STRONG_BUY":   "💎 강력매수",
            "SURGE":        "📈 급등",
            "EARLY_DETECT": "🔍 조기포착",
            "ENTRY_POINT":  "🎯 단기눌림목",
            "MID_PULLBACK": "🏆 중기눌림목",
            "MANUAL":       "✏️ 수동",
        }

        # ── 이론 통계 ──
        total_pnl  = [v["pnl_pct"] for v in completed]
        total_win  = sum(1 for p in total_pnl if p > 0)
        avg_pnl    = sum(total_pnl) / len(total_pnl)
        total_rate = total_win / len(total_pnl) * 100

        # ── 실제 진입 통계 ──
        actual_msg = ""
        if actual_entered:
            a_pnls = [v["actual_pnl"] for v in actual_entered]
            a_win  = sum(1 for p in a_pnls if p > 0)
            a_avg  = sum(a_pnls) / len(a_pnls)
            a_rate = a_win / len(a_pnls) * 100
            actual_msg = (f"💰 <b>내 실제 수익</b>  {len(actual_entered)}건\n"
                          f"  승률 <b>{a_rate:.0f}%</b>  평균 <b>{a_avg:+.1f}%</b>\n")
        elif unconfirmed:
            actual_msg = f"❓ 확인 대기 {len(unconfirmed)}건  (/result 또는 /skip 로 기록)\n"

        # ── 스킵 패턴 분석 ──
        skip_msg = ""
        if skipped:
            skip_reasons = {}
            for v in skipped:
                r = v.get("skip_reason", "미입력")
                skip_reasons[r] = skip_reasons.get(r, 0) + 1
            skip_top = sorted(skip_reasons.items(), key=lambda x: -x[1])[:3]
            skip_str = "  /  ".join([f"{r}:{n}건" for r, n in skip_top])
            # 스킵한 신호들의 이론 수익률 평균 (기회비용)
            skip_pnls = [v.get("pnl_pct", 0) for v in skipped if v.get("pnl_pct")]
            opp_cost  = sum(skip_pnls) / len(skip_pnls) if skip_pnls else 0
            skip_msg  = (f"⏭ <b>스킵</b>  {len(skipped)}건  (이론 평균 {opp_cost:+.1f}%)\n"
                         f"  이유: {skip_str}\n")

        # ── 진입미달 통계 ──
        miss_all      = [v for v in data.values() if v.get("status") in ["진입미달", "진입가변경"]]
        miss_surge    = sum(1 for v in miss_all if "상승이탈"   in str(v.get("exit_reason","")))
        miss_expire   = sum(1 for v in miss_all if "기간만료"   in str(v.get("exit_reason","")))
        miss_reentry  = sum(1 for v in miss_all if "진입가변경" in str(v.get("exit_reason","")))
        cur_ratio     = _dynamic.get("entry_pullback_ratio", ENTRY_PULLBACK_RATIO)

        miss_msg = ""
        if miss_all:
            miss_msg = (f"⚠️ <b>진입 미달</b>  {len(miss_all)}건\n"
                        f"  상승이탈 {miss_surge}건  기간만료 {miss_expire}건  재포착 {miss_reentry}건\n"
                        f"  현재 진입가 비율: <b>{cur_ratio:.2f}</b>  (0.2=보수적 ↔ 0.7=공격적)\n")

        msg = (f"📊 <b>신호 성과 통계</b>\n"
               f"━━━━━━━━━━━━━━━\n"
               f"🤖 <b>이론 수익률</b> (봇 학습 기준)  {len(completed)}건\n"
               f"  승률 <b>{total_rate:.0f}%</b>  평균 <b>{avg_pnl:+.1f}%</b>  추적중 {len(tracking)}건\n"
               f"━━━━━━━━━━━━━━━\n"
               + actual_msg
               + skip_msg
               + miss_msg
               + f"━━━━━━━━━━━━━━━\n")

        # 신호 유형별
        by_type = {}
        for v in completed:
            t = v.get("signal_type", "기타")
            by_type.setdefault(t, []).append(v)

        for t, recs in sorted(by_type.items(), key=lambda x: -len(x[1])):
            pnls = [r["pnl_pct"] for r in recs]
            win  = sum(1 for p in pnls if p > 0)
            rate = win / len(pnls) * 100
            avg  = sum(pnls) / len(pnls)
            best = max(pnls); worst = min(pnls)
            label = type_labels.get(t, t)
            bar   = "🟢" * int(rate/20) + "⬜" * (5 - int(rate/20))
            # 청산 이유 분포
            reasons = {}
            for r in recs:
                ex = r.get("exit_reason", "?")
                reasons[ex] = reasons.get(ex, 0) + 1
            reason_str = "  ".join([f"{k}:{v}건" for k, v in reasons.items()])
            msg += (f"\n{label}  ({len(recs)}건)\n"
                    f"  {bar}  승률 {rate:.0f}%  평균 {avg:+.1f}%\n"
                    f"  최고 {best:+.1f}%  최저 {worst:+.1f}%\n"
                    f"  {reason_str}\n")

        # 단독 vs 테마 동반 비교
        solo   = [v for v in completed if not v.get("sector_bonus", 0)]
        themed = [v for v in completed if v.get("sector_bonus", 0)]
        if solo and themed:
            solo_avg   = sum(v["pnl_pct"] for v in solo)   / len(solo)
            themed_avg = sum(v["pnl_pct"] for v in themed) / len(themed)
            solo_win   = sum(1 for v in solo   if v["pnl_pct"] > 0) / len(solo)   * 100
            themed_win = sum(1 for v in themed if v["pnl_pct"] > 0) / len(themed) * 100
            msg += (f"\n━━━━━━━━━━━━━━━\n"
                    f"🔍 단독 상승:  승률 {solo_win:.0f}%  평균 {solo_avg:+.1f}% ({len(solo)}건)\n"
                    f"🏭 테마 동반:  승률 {themed_win:.0f}%  평균 {themed_avg:+.1f}% ({len(themed)}건)\n")

        # ── 시간대별 승률 분석 ──
        slot_stats = analyze_timeslot_winrate(completed)
        if slot_stats:
            slot_order = ["장초반", "오전", "오후", "장후반", "기타"]
            msg += "\n━━━━━━━━━━━━━━━\n🕐 <b>시간대별 승률</b>\n"
            for slot in slot_order:
                if slot not in slot_stats: continue
                st  = slot_stats[slot]
                adj = _dynamic["timeslot_score_adj"].get(slot, 0)
                adj_str = f"  [+{adj}점 보정 중]" if adj > 0 else ""
                bar = "🟢" * int(st["rate"] / 20) + "⬜" * (5 - int(st["rate"] / 20))
                msg += (f"  {slot}: {bar}  승률 {st['rate']:.0f}%  "
                        f"평균 {st['avg']:+.1f}%  ({st['total']}건){adj_str}\n")

        # ── 손실 패턴 분석 ──
        loss_pattern = analyze_loss_pattern(completed)
        if loss_pattern:
            msg += f"\n━━━━━━━━━━━━━━━\n{loss_pattern}\n"

        # ── 시장 국면 현황 ──
        regime = get_market_regime()
        rmode  = regime.get("mode", "normal")
        rlabels = {"bull":"🟢 상승장","normal":"🔵 보통장","bear":"🟠 하락장","crash":"🔴 급락장"}
        mult_map = {"bull":"기준 완화 (×1.15)","normal":"표준","bear":"기준 강화 (×0.75)","crash":"급락장 — 상한가만 허용"}
        msg += (f"\n━━━━━━━━━━━━━━━\n"
                f"🌐 <b>현재 시장 국면</b>: {rlabels.get(rmode,'보통장')}\n"
                f"  코스피 당일 {regime.get('chg_1d',0):+.1f}%  |  5일 {regime.get('chg_5d',0):+.1f}%\n"
                f"  신호 기준: {mult_map.get(rmode,'표준')}\n")

        # ── 포지션 사이징 요약 ──
        if completed:
            a_recs = [v for v in completed if v.get("grade","B") == "A"]
            b_recs = [v for v in completed if v.get("grade","B") == "B"]
            if a_recs:
                a_avg = sum(v["pnl_pct"] for v in a_recs) / len(a_recs)
                a_win = sum(1 for v in a_recs if v["pnl_pct"] > 0) / len(a_recs) * 100
                msg += (f"\n━━━━━━━━━━━━━━━\n"
                        f"💰 <b>등급별 성과</b>\n"
                        f"  A등급: {len(a_recs)}건  승률 {a_win:.0f}%  평균 {a_avg:+.1f}%\n")
            if b_recs:
                b_avg = sum(v["pnl_pct"] for v in b_recs) / len(b_recs)
                b_win = sum(1 for v in b_recs if v["pnl_pct"] > 0) / len(b_recs) * 100
                msg += f"  B등급: {len(b_recs)}건  승률 {b_win:.0f}%  평균 {b_avg:+.1f}%\n"

        # ── 현재 _dynamic 파라미터 요약 ──
        msg += (f"\n━━━━━━━━━━━━━━━\n"
                f"⚙️ <b>현재 자동 조정 파라미터</b>\n"
                f"  최소점수: {_dynamic['min_score_normal']}점 (엄격: {_dynamic['min_score_strict']}점)\n"
                f"  RSI 과매수 기준: {_dynamic['rsi_overbuy']:.0f}\n"
                f"  ATR 손절:{_dynamic['atr_stop_mult']} / 목표:{_dynamic.get('atr_target_mult', ATR_TARGET_MULT)}\n"
                f"  포지션 기본비중: {_dynamic.get('position_base_pct',8.0)}%\n")

        # ── 기능별 기여도 현황 ──
        feat_labels = {
            "feat_w_rsi":    "RSI 필터",
            "feat_w_ma":     "이동평균",
            "feat_w_bb":     "볼린저밴드",
            "feat_w_sector": "섹터모멘텀",
            "feat_w_nxt":    "NXT 보정",
        }
        msg += f"\n━━━━━━━━━━━━━━━\n🔧 <b>기능별 가중치</b> (auto_tune 자동 조정)\n"
        for fk, flabel in feat_labels.items():
            w = _dynamic.get(fk, 1.0)
            if w >= 1.2:   status = "🔺 강화"
            elif w >= 0.8: status = "✅ 정상"
            elif w >= 0.4: status = "🔻 약화"
            else:           status = "⛔ 거의 비활성"
            bar = "█" * int(w * 5) + "░" * max(0, 5 - int(w * 5))
            msg += f"  {flabel}: {bar} {w:.1f}  {status}\n"

        send(msg)
    except Exception as e:
        send(f"⚠️ 통계 오류: {e}")

# ============================================================
# 장 마감
# ============================================================
def on_market_close():
    # 재진입 감시 — KRX only 종목만 초기화, NXT 상장 종목은 20:00까지 유지
    nxt_remain = {c: w for c, w in _reentry_watch.items() if is_nxt_listed(c)}
    krx_only   = {c: w for c, w in _reentry_watch.items() if not is_nxt_listed(c)}
    if krx_only:
        for c in krx_only: _reentry_watch.pop(c, None)
        print(f"  🔄 KRX 재진입 감시 {len(krx_only)}건 만료 (15:30)")
    if nxt_remain:
        print(f"  🔵 NXT 재진입 감시 {len(nxt_remain)}건 유지 (→20:00)")

    carry_list = []
    for code, info in list(_detected_stocks.items()):
        carry_day = info.get("carry_day",0)
        if carry_day >= MAX_CARRY_DAYS: del _detected_stocks[code]; continue
        _detected_stocks[code]["carry_day"]   = carry_day+1
        _detected_stocks[code]["detected_at"] = datetime.now()
        carry_list.append(f"• {info['name']} ({code}) - {carry_day+1}일차")
    save_carry_stocks()
    auto_tune(notify=True)
    _send_pending_result_reminder()   # ★ 오늘 미입력 종목 알림

    today = datetime.now().strftime("%Y%m%d")
    today_str = datetime.now().strftime("%Y-%m-%d")
    try:
        data = {}
        with open(SIGNAL_LOG_FILE,"r") as f: data = json.load(f)

        today_recs   = [v for v in data.values() if v.get("detect_date") == today]
        done_today   = [v for v in today_recs if v.get("status") != "추적중"]
        # 전체 추적 중 (날짜 무관)
        all_tracking = [v for v in data.values() if v.get("status") == "추적중"]

        sig_labels = {
            "UPPER_LIMIT":"상한가","NEAR_UPPER":"상한가근접","SURGE":"급등",
            "EARLY_DETECT":"조기포착","MID_PULLBACK":"중기눌림목",
            "ENTRY_POINT":"단기눌림목","STRONG_BUY":"강력매수",
        }

        msg = f"🔔 <b>장 마감 리포트</b>  {today_str}\n━━━━━━━━━━━━━━━\n"

        # ── 오늘 확정 결과 ──
        if done_today:
            wins   = sum(1 for v in done_today if v.get("pnl_pct",0) > 0)
            losses = sum(1 for v in done_today if v.get("pnl_pct",0) < 0)
            win_rate = round(wins / len(done_today) * 100) if done_today else 0
            avg_pnl  = sum(v.get("pnl_pct",0) for v in done_today) / len(done_today)
            msg += (f"\n📊 <b>오늘 확정 결과</b>  ({len(done_today)}건)\n"
                    f"  승률 <b>{win_rate}%</b>  평균 <b>{avg_pnl:+.1f}%</b>"
                    f"  |  수익 {wins}건  손실 {losses}건\n")
            for v in sorted(done_today, key=lambda x: x.get("pnl_pct",0), reverse=True):
                pnl   = v.get("pnl_pct", 0)
                dot   = "✅" if pnl > 0 else ("🔴" if pnl < 0 else "➖")
                label = sig_labels.get(v.get("signal_type",""), "")
                theme = f"[{v['sector_theme']}]" if v.get("sector_bonus",0) > 0 else "[단독]"
                msg  += f"  {dot} {v['name']} <b>{pnl:+.1f}%</b>  {label} {theme}\n"
        else:
            msg += "\n📊 오늘 확정된 신호 없음\n"

        # ── 전체 추적 중 (오늘 + 이월) 잠정 수익률 ──
        if all_tracking:
            msg += f"\n⏳ <b>추적 중</b>  ({len(all_tracking)}건)\n"
            tracking_results = []
            for v in all_tracking:
                try:
                    # 장 마감 후면 NXT 가격 우선 사용
                    price = 0
                    if is_nxt_open():
                        nxt_p = get_nxt_stock_price(v["code"])
                        price = nxt_p.get("price", 0)
                    if not price:
                        cur   = get_stock_price(v["code"])
                        price = cur.get("price", 0)
                    entry = v.get("entry_price", 0)
                    if price and entry:
                        pnl      = round((price - entry) / entry * 100, 1)
                        days_ago = (datetime.strptime(today, "%Y%m%d") -
                                    datetime.strptime(v.get("detect_date", today), "%Y%m%d")).days
                        day_tag  = f" {days_ago}일째" if days_ago > 0 else " 오늘"
                        dot      = "🟢" if pnl >= 0 else "🟠"
                        label    = sig_labels.get(v.get("signal_type",""), "")
                        nxt_tag  = " 🔵NXT" if is_nxt_open() else ""
                        tracking_results.append((pnl, f"  {dot} {v['name']} <b>{pnl:+.1f}%</b>  {label}{day_tag}{nxt_tag}\n"))
                    time.sleep(0.1)
                except: continue
            # 수익률 높은 순 정렬
            for _, line in sorted(tracking_results, key=lambda x: x[0], reverse=True):
                msg += line

        if carry_list:
            msg += f"\n📂 <b>이월 종목</b>  ({len(carry_list)}개)\n" + "\n".join(carry_list) + "\n"

        # ── 누적 성과 요약 (전체 완료 건) ──
        all_done = [v for v in data.values() if v.get("status") in ["수익","손실","본전"]]
        if len(all_done) >= 5:
            total_win  = sum(1 for v in all_done if v.get("pnl_pct",0) > 0)
            total_avg  = sum(v.get("pnl_pct",0) for v in all_done) / len(all_done)
            total_rate = round(total_win / len(all_done) * 100)
            msg += (f"\n━━━━━━━━━━━━━━━\n"
                    f"📈 <b>누적 성과</b>  {len(all_done)}건\n"
                    f"  승률 <b>{total_rate}%</b>  평균 <b>{total_avg:+.1f}%</b>\n")

    except Exception as e:
        msg = (f"🔔 <b>장 마감</b>  {today_str}\n"
               f"감시 종목: <b>{len(_detected_stocks)}개</b>\n"
               f"⚠️ 리포트 오류: {e}\n")
        if carry_list:
            msg += f"\n📂 <b>이월</b> ({len(carry_list)}개)\n" + "\n".join(carry_list)

    send(msg)
    analyze_dart_disclosures()

    # 금요일 장 마감 = 주간 리포트 (금요일이 공휴일이라 목요일에 마감하는 경우도 처리)
    now = datetime.now()
    is_friday = now.weekday() == 4
    next_day_holiday = is_holiday((now + timedelta(days=1)).strftime("%Y%m%d"))
    is_last_trading_day = is_friday or (now.weekday() == 3 and next_day_holiday)
    if is_last_trading_day:
        send_weekly_report()

def send_premarket_briefing():
    """매일 08:50 장 시작 전 브리핑 — 주말/공휴일 스킵"""
    if is_holiday(): return
    today = datetime.now().strftime("%Y-%m-%d (%a)")
    msg   = f"🌅 <b>장 시작 전 브리핑</b>  {today}\n━━━━━━━━━━━━━━━\n"

    # ── ① 이월 감시 종목 ──
    if _detected_stocks:
        msg += f"\n📂 <b>감시 중 종목</b>  ({len(_detected_stocks)}개)\n"
        for code, info in list(_detected_stocks.items())[:6]:
            try:
                cur   = get_stock_price(code)
                price = cur.get("price", 0)
                entry = info.get("entry_price", 0)
                if price and entry:
                    pnl = round((price - entry) / entry * 100, 1)
                    dot = "🟢" if pnl >= 0 else "🔴"
                    msg += f"  {dot} {info['name']}  진입 {entry:,} → 현재 {price:,} ({pnl:+.1f}%)\n"
                time.sleep(0.15)
            except: continue
    else:
        msg += "\n📂 감시 중 종목 없음\n"

    # ── ② 어제 상한가 종목 ──
    try:
        upper_yest = []
        data = {}
        try:
            with open(SIGNAL_LOG_FILE, "r") as f: data = json.load(f)
        except: pass
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        upper_yest = [v for v in data.values()
                      if v.get("detect_date") == yesterday
                      and v.get("signal_type") == "UPPER_LIMIT"]
        if upper_yest:
            msg += f"\n🔁 <b>전일 상한가 → 오늘 연속 주목</b>\n"
            for v in upper_yest[:4]:
                msg += f"  🚨 {v['name']}  ({v['code']})\n"
    except: pass

    # ── ③ 오늘 DART 예정 공시 (최근 등록 기준) ──
    try:
        if DART_API_KEY:
            today_str = datetime.now().strftime("%Y%m%d")
            dart_list = _fetch_dart_list(today_str)
            hot = [i for i in dart_list[:10]
                   if any(kw in i.get("report_nm","")
                          for kw in ["유상증자","무상증자","합병","분할","실적","배당","자사주"])]
            if hot:
                msg += f"\n📌 <b>오늘 공시 주목</b>  ({len(hot)}건)\n"
                for h in hot[:4]:
                    msg += f"  • {h.get('corp_name','')}  {h.get('report_nm','')[:20]}\n"
    except: pass

    # ── ④ 현재 파라미터 상태 ──
    tuned = any([
        _dynamic["early_price_min"]  != EARLY_PRICE_MIN,
        _dynamic["mid_surge_min_pct"] != MID_SURGE_MIN_PCT,
        _dynamic["min_score_normal"] != 60,
    ])
    if tuned:
        msg += (f"\n⚙️ <b>자동 조정된 파라미터</b>\n"
                f"  조기포착 기준: {_dynamic['early_price_min']:.0f}%  "
                f"중기눌림목: {_dynamic['mid_surge_min_pct']:.0f}%\n"
                f"  최소점수: {_dynamic['min_score_normal']}점\n")

    # ── ⑤ NXT 장전 동향 (08:00~09:00 사이에만) ──
    try:
        nxt_stocks = get_nxt_surge_stocks()
        if nxt_stocks:
            # 변동률 상위 5개
            hot_nxt = sorted(nxt_stocks, key=lambda x: abs(x.get("change_rate",0)), reverse=True)[:5]
            msg += f"\n🔵 <b>NXT 장전 동향</b>  (KRX 개장 전)\n"
            for s in hot_nxt:
                cr  = s.get("change_rate", 0)
                vr  = s.get("volume_ratio", 0)
                dot = "📈" if cr > 0 else "📉"
                vt  = f" 🔊{vr:.0f}x" if vr >= 3 else ""
                msg += f"  {dot} {s['name']} <b>{cr:+.1f}%</b>{vt}\n"

            # 외인 순매수 상위 종목 (NXT 선취매 신호)
            nxt_foreign_buys = []
            for s in nxt_stocks[:8]:
                try:
                    inv = get_nxt_investor_trend(s["code"])
                    fn  = inv.get("foreign_net", 0)
                    if fn > 1000:
                        nxt_foreign_buys.append((s["name"], fn, s.get("change_rate",0)))
                    time.sleep(0.1)
                except: continue
            if nxt_foreign_buys:
                msg += f"\n  💡 외인 선취매 주목:\n"
                for nm, fn, cr in sorted(nxt_foreign_buys, key=lambda x: -x[1])[:3]:
                    msg += f"    🔵 {nm} 외인 {fn:+,}주  ({cr:+.1f}%)\n"
    except: pass

    # ── 시장 국면 브리핑 ──
    try:
        regime = get_market_regime()
        rmode  = regime.get("mode", "normal")
        rlabels = {"bull":"🟢 상승장","normal":"🔵 보통장","bear":"🟠 하락장","crash":"🔴 급락장"}
        regime_warn = ""
        if rmode == "crash":
            regime_warn = "\n⚠️ <b>급락장 모드</b> — 상한가 신호만 발송됩니다"
        elif rmode == "bear":
            regime_warn = "\n🟠 <b>하락장 모드</b> — 신호 기준 강화, 포지션 축소 권장"
        elif rmode == "bull":
            regime_warn = "\n🟢 <b>상승장 모드</b> — 신호 기준 완화, 적극 대응 가능"
        msg += (f"\n━━━━━━━━━━━━━━━\n"
                f"🌐 시장 국면: <b>{rlabels.get(rmode,'보통장')}</b>"
                f"{regime_warn}\n")
    except: pass

    msg += f"\n━━━━━━━━━━━━━━━\n⏰ 09:00 장 시작"
    send(msg)


def send_weekly_report():
    """매주 금요일 15:35 — 이번 주 성과 자동 발송 + AI 분석"""
    # 같은 주에 이미 발송했으면 스킵 (on_market_close와 스케줄 중복 방지)
    global _weekly_report_sent_week
    this_week_key = datetime.now().strftime("%Y-W%W")
    if getattr(send_weekly_report, "_sent_week", "") == this_week_key:
        return
    send_weekly_report._sent_week = this_week_key
    try:
        data = {}
        try:
            with open(SIGNAL_LOG_FILE, "r") as f: data = json.load(f)
        except: return

        today    = datetime.now()
        # 이번 주 월요일 ~ 오늘(금요일)
        this_mon = (today - timedelta(days=today.weekday())).strftime("%Y%m%d")
        this_fri = today.strftime("%Y%m%d")

        week_recs = [v for v in data.values()
                     if this_mon <= v.get("detect_date","") <= this_fri
                     and v.get("status") in ["수익","손실","본전"]]

        if not week_recs:
            send(f"📅 <b>주간 리포트</b>  {this_mon[:4]}.{this_mon[4:6]}.{this_mon[6:]} ~ {this_fri[6:]}\n이번 주 완료된 신호 없음")
            return

        pnls     = [v["pnl_pct"] for v in week_recs]
        wins     = sum(1 for p in pnls if p > 0)
        losses   = sum(1 for p in pnls if p < 0)
        win_rate = round(wins / len(pnls) * 100)
        avg_pnl  = round(sum(pnls) / len(pnls), 1)
        best     = max(week_recs, key=lambda x: x["pnl_pct"])
        worst    = min(week_recs, key=lambda x: x["pnl_pct"])

        by_type = {}
        for v in week_recs:
            t = v.get("signal_type","기타")
            by_type.setdefault(t, []).append(v["pnl_pct"])

        type_labels = {
            "UPPER_LIMIT":"상한가","NEAR_UPPER":"상한가근접","SURGE":"급등",
            "EARLY_DETECT":"조기포착","MID_PULLBACK":"중기눌림목",
            "ENTRY_POINT":"단기눌림목","STRONG_BUY":"강력매수",
        }
        type_lines = ""
        for t, ps in sorted(by_type.items(), key=lambda x: -len(x[1])):
            w = sum(1 for p in ps if p > 0)
            type_lines += f"  {type_labels.get(t,t)}: {w}/{len(ps)}건  평균 {sum(ps)/len(ps):+.1f}%\n"

        solo_pnls   = [v["pnl_pct"] for v in week_recs if not v.get("sector_bonus",0)]
        themed_pnls = [v["pnl_pct"] for v in week_recs if v.get("sector_bonus",0)]
        compare = ""
        if solo_pnls and themed_pnls:
            compare = (f"\n🔍 단독:  승률 {sum(1 for p in solo_pnls if p>0)/len(solo_pnls)*100:.0f}%"
                       f"  평균 {sum(solo_pnls)/len(solo_pnls):+.1f}%  ({len(solo_pnls)}건)\n"
                       f"🏭 테마:  승률 {sum(1 for p in themed_pnls if p>0)/len(themed_pnls)*100:.0f}%"
                       f"  평균 {sum(themed_pnls)/len(themed_pnls):+.1f}%  ({len(themed_pnls)}건)")

        report_text = (
            f"총 {len(week_recs)}건  승률 {win_rate}%  평균 {avg_pnl:+.1f}%  "
            f"수익 {wins}건 손실 {losses}건\n"
            f"{type_lines}{compare}\n"
            f"최고: {best['name']} {best['pnl_pct']:+.1f}%  "
            f"최저: {worst['name']} {worst['pnl_pct']:+.1f}%"
        )

        send(
            f"📅 <b>주간 자동 리포트</b>\n"
            f"{this_mon[:4]}.{this_mon[4:6]}.{this_mon[6:]} ~ {this_fri[:4]}.{this_fri[4:6]}.{this_fri[6:]}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"{report_text}"
        )

        # ── AI 분석 (Claude API) ──
        auto_tune(notify=True)                          # 조건 자동 조정
        _send_ai_analysis(week_recs, report_text)       # Claude가 패턴 분석

    except Exception as e:
        print(f"⚠️ 주간 리포트 오류: {e}")


ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

def _send_ai_analysis(week_recs: list, summary: str):
    """
    주간 결과를 Claude API로 분석 요청 → 개선 제안 텔레그램 발송
    봇 스스로 자기 신호를 평가하고 개선점을 찾음
    """
    try:
        # 상세 데이터 구성
        details = []
        for v in week_recs:
            details.append(
                f"- {v['name']} [{v.get('signal_type','')}] "
                f"진입{v.get('entry_price',0):,} → {v.get('exit_reason','')} {v['pnl_pct']:+.1f}% "
                f"테마:{v.get('sector_theme','없음')} 보너스:{v.get('sector_bonus',0)}점 "
                f"손절:{v.get('stop_price',0):,} 목표:{v.get('target_price',0):,}"
            )
        detail_text = "\n".join(details)

        # 현재 동적 파라미터 상태
        params_text = (
            f"조기포착 최소가격변동: {_dynamic['early_price_min']}%\n"
            f"조기포착 최소거래량: {_dynamic['early_volume_min']}배\n"
            f"중기눌림목 1차급등: {_dynamic['mid_surge_min_pct']}%\n"
            f"중기눌림목 눌림범위: {_dynamic['mid_pullback_min']}~{_dynamic['mid_pullback_max']}%\n"
            f"최소점수(일반/엄격): {_dynamic['min_score_normal']}/{_dynamic['min_score_strict']}점\n"
            f"테마보너스: {_dynamic['themed_score_bonus']}점"
        )

        prompt = f"""당신은 한국 주식 알림 봇의 성과를 분석하는 퀀트 분석가입니다.

[이번 주 신호 결과 요약]
{summary}

[종목별 상세]
{detail_text}

[현재 봇 파라미터]
{params_text}

위 데이터를 분석해서 다음을 한국어로 답해주세요:

1. **패턴 분석** (2~3줄): 수익 종목과 손실 종목에서 보이는 공통점
2. **개선 제안** (구체적 수치 포함, 2~3가지): 어떤 파라미터를 어떻게 바꾸면 좋을지
3. **주의 신호** (1줄): 다음 주에 특히 조심해야 할 패턴

간결하게, 실행 가능한 제안 위주로 작성해주세요."""

        resp = requests.post(
            ANTHROPIC_API_URL,
            headers={"Content-Type": "application/json"},
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 800,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        result = resp.json()
        ai_text = result.get("content", [{}])[0].get("text", "")

        if ai_text:
            # 텔레그램 4096자 제한 고려해서 앞 1200자만
            send(f"🤖 <b>AI 주간 분석</b>\n━━━━━━━━━━━━━━━\n{ai_text[:1200]}")
    except Exception as e:
        print(f"⚠️ AI 분석 오류: {e}")
def run_news_scan():
    if not is_any_market_open() or _bot_paused: return   # NXT 포함 체크
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 뉴스 스캔...", flush=True)
    try:
        headlines = fetch_all_news()   # 한 번만 호출
        if not headlines: return
        # 뉴스 공동언급 DB 업데이트 (백그라운드)
        threading.Thread(target=update_news_cooccur, args=(headlines,), daemon=True).start()
        # 테마 분석은 가져온 헤드라인 재사용 (이중 크롤링 제거)
        for signal in analyze_news_theme(headlines=headlines):
            send_news_theme_alert(signal)
    except Exception as e: print(f"⚠️ 뉴스 오류: {e}")


# ============================================================
# 🌐 ① 시장 국면 판단 (Market Regime)
# ============================================================
_regime_cache = {"mode": "normal", "ts": 0, "kospi_5d": []}

def get_market_regime() -> dict:
    """
    코스피 5일 흐름으로 시장 국면 판단.
    bull(상승) / normal(보통) / bear(하락) / crash(급락)
    → 국면별로 신호 기준 자동 강화/완화
    """
    if time.time() - _regime_cache["ts"] < 600:  # 10분 캐시
        return _regime_cache

    try:
        chg_today = get_kospi_change()
        items = get_daily_data("0001", 10)  # 코스피 일봉
        if not items:
            return _regime_cache

        # 5일 누적 등락
        closes = [i["close"] for i in items if i.get("close")]
        if len(closes) >= 5:
            chg_5d = (closes[-1] - closes[-5]) / closes[-5] * 100
        else:
            chg_5d = 0

        # 국면 판단
        if chg_today <= -3.0 or chg_5d <= -7.0:
            mode = "crash"
        elif chg_today <= -1.5 or chg_5d <= -3.0:
            mode = "bear"
        elif chg_today >= 1.0 and chg_5d >= 2.0:
            mode = "bull"
        else:
            mode = "normal"

        # 신호 배율 설정
        mult_map  = {"crash": 0.5, "bear": 0.75, "normal": 1.0, "bull": 1.15}
        add_map   = {"crash": 15,  "bear": 8,    "normal": 0,   "bull": -5}

        # ── NXT 시간대 보정 (15:30~20:00) ──
        # KRX 마감 후 NXT만 운영 중이면 거래량 얇아서 변동성 높음
        # → 포지션 비중 자동 축소, 목표가 보수적
        nxt_only = is_nxt_open() and not is_market_open()
        if nxt_only:
            # NXT 단독 시간대: 국면 한 단계 보수적으로
            nxt_mode_map = {"bull": "normal", "normal": "bear",
                            "bear": "bear",   "crash":  "crash"}
            mode = nxt_mode_map.get(mode, mode)
            mult_map[mode] = max(mult_map.get(mode, 1.0) * 0.85, 0.5)

        _regime_cache.update({
            "mode":     mode,
            "chg_1d":   chg_today,
            "chg_5d":   chg_5d,
            "mult":     mult_map[mode],
            "min_add":  add_map[mode],
            "nxt_only": nxt_only,
            "ts":       time.time(),
        })
        _dynamic["regime_mode"]       = mode
        _dynamic["regime_score_mult"] = mult_map[mode]
        _dynamic["regime_min_add"]    = add_map[mode]

    except Exception as e:
        print(f"⚠️ 시장 국면 판단 오류: {e}")

    return _regime_cache

def regime_label() -> str:
    r = get_market_regime()
    labels = {"bull":"🟢 상승장","normal":"🔵 보통장","bear":"🟠 하락장","crash":"🔴 급락장"}
    return labels.get(r.get("mode","normal"), "🔵 보통장")

# ============================================================
# 💰 ② 포지션 사이징 가이드 (Kelly 기반)
# ============================================================
def calc_position_size(signal_type: str, score: int, grade: str) -> dict:
    """
    신호 등급 + 과거 승률 기반 권장 투자비중 계산.
    켈리 공식: f = (p*b - q) / b  (p=승률, q=1-p, b=손익비)
    반환: {"pct": float, "amount_guide": str, "kelly": float}
    """
    try:
        # 과거 신호 유형별 승률 조회
        data = {}
        try:
            with open(SIGNAL_LOG_FILE, "r") as f: data = json.load(f)
        except: pass

        same_type = [v for v in data.values()
                     if v.get("signal_type") == signal_type
                     and v.get("status") in ["수익","손실","본전"]]

        if len(same_type) >= 5:
            wins  = sum(1 for v in same_type if v["pnl_pct"] > 0)
            p     = wins / len(same_type)
            avg_w = sum(v["pnl_pct"] for v in same_type if v["pnl_pct"] > 0) / max(wins, 1)
            avg_l = abs(sum(v["pnl_pct"] for v in same_type if v["pnl_pct"] < 0) / max(len(same_type)-wins, 1))
            b     = avg_w / avg_l if avg_l else 2.0
            kelly = max(0, (p * b - (1-p)) / b)
            kelly = min(kelly * 0.5, 0.20)  # 하프 켈리, 최대 20%
        else:
            p     = 0.55  # 기본값
            kelly = 0.08

        # 등급별 보정
        grade_mult = {"A": 1.3, "B": 1.0, "C": 0.7}.get(grade, 1.0)

        # 시장 국면 보정
        regime_info  = get_market_regime()
        regime       = regime_info.get("mode", "normal")
        nxt_only     = regime_info.get("nxt_only", False)
        regime_mult  = {"bull": 1.2, "normal": 1.0, "bear": 0.6, "crash": 0.3}.get(regime, 1.0)
        # NXT 단독 시간대: 포지션 비중 추가 20% 축소
        if nxt_only:
            regime_mult = max(regime_mult * 0.8, 0.3)

        base_pct = _dynamic.get("position_base_pct", 8.0)
        final_pct = round(min(base_pct * grade_mult * regime_mult, 20.0), 1)

        if regime in ("bear", "crash"):
            guide = f"⚠️ {regime_label()} — 비중 축소 권장"
        elif grade == "A" and p >= 0.6:
            guide = f"💪 고확률 신호 — 적극 진입 고려"
        else:
            guide = f"📊 표준 비중"

        return {
            "pct":    final_pct,
            "kelly":  round(kelly * 100, 1),
            "guide":  guide,
            "win_rate": round(p * 100, 1) if len(same_type) >= 5 else None,
            "samples":  len(same_type),
        }
    except:
        return {"pct": 8.0, "kelly": 8.0, "guide": "📊 표준 비중", "win_rate": None, "samples": 0}

# ============================================================
# 📐 ③ 손익비 동적 최적화
# ============================================================
def calc_dynamic_stop_target(code: str, entry: int) -> tuple:
    """
    시장 변동성 + 국면에 따라 손절/목표가 배수 동적 조정.
    기존 calc_stop_target 대체.
    반환: (stop, target, stop_pct, target_pct, atr_used)
    """
    atr = get_atr(code)
    if not atr:
        stop   = int(entry * 0.93 / 10) * 10
        target = int(entry * 1.15 / 10) * 10
        return stop, target, 7.0, 15.0, False

    regime_info = get_market_regime()
    regime  = regime_info.get("mode", "normal")
    nxt_only = regime_info.get("nxt_only", False)
    stop_m  = _dynamic.get("atr_stop_mult",   ATR_STOP_MULT)
    tgt_m   = _dynamic.get("atr_target_mult", ATR_TARGET_MULT)

    # 시장 국면 보정
    if regime == "crash":
        stop_m  = max(stop_m  * 0.8, 1.0)
        tgt_m   = max(tgt_m   * 0.7, 2.0)
    elif regime == "bear":
        stop_m  = max(stop_m  * 0.9, 1.0)
        tgt_m   = max(tgt_m   * 0.8, 2.0)
    elif regime == "bull":
        tgt_m   = min(tgt_m   * 1.2, 5.0)

    # NXT 단독 시간대 보정: 거래량 얇아 변동성 높음 → 손절 여유 + 목표 축소
    if nxt_only:
        stop_m  = max(stop_m  * 0.85, 1.0)   # 손절 더 여유롭게
        tgt_m   = max(tgt_m   * 0.80, 1.5)   # 목표 보수적

    stop      = int((entry - atr * stop_m)  / 10) * 10
    target    = int((entry + atr * tgt_m)   / 10) * 10
    stop_pct  = round((entry - stop)   / entry * 100, 1)
    tgt_pct   = round((target - entry) / entry * 100, 1)
    return stop, target, stop_pct, tgt_pct, True

# ============================================================
# 📅 ④ 실적 발표 전후 필터
# ============================================================
_earnings_cache: dict = {}   # {code: {"date": "YYYYMMDD", "ts": float}}

def check_earnings_risk(code: str, name: str) -> dict:
    """
    DART에서 최근 실적 발표 일정 확인.
    발표 3일 전이면 경고, 당일/다음날이면 강경고.
    반환: {"risk": "none"/"warn"/"high", "desc": str}
    """
    if not DART_API_KEY:
        return {"risk": "none", "desc": ""}

    cached = _earnings_cache.get(code)
    if cached and time.time() - cached["ts"] < 3600:
        return cached["result"]

    try:
        today   = datetime.now()
        bgn_de  = today.strftime("%Y%m%d")
        end_de  = (today + timedelta(days=7)).strftime("%Y%m%d")

        url    = "https://opendart.fss.or.kr/api/list.json"
        params = {
            "crtfc_key": DART_API_KEY,
            "bgn_de":    bgn_de,
            "end_de":    end_de,
            "pblntf_ty": "A",           # 정기공시 (실적)
            "corp_name": name[:4],      # 종목명 앞 4글자로 검색
            "page_count": 10,
        }
        resp = _session.get(url, params=params, timeout=10)
        items = resp.json().get("list", []) if resp.status_code == 200 else []

        result = {"risk": "none", "desc": ""}
        for item in items:
            rpt_nm = item.get("report_nm", "")
            rcept_dt = item.get("rcept_dt", "")
            if any(kw in rpt_nm for kw in ["사업보고서","분기보고서","반기보고서"]):
                try:
                    rpt_date = datetime.strptime(rcept_dt, "%Y%m%d")
                    diff = (rpt_date - today).days
                    if diff <= 1:
                        result = {"risk": "high",
                                  "desc": f"⚠️ 실적발표 임박! ({rcept_dt}) — 변동성 주의"}
                    elif diff <= 3:
                        result = {"risk": "warn",
                                  "desc": f"📅 실적발표 {diff}일 전 ({rcept_dt}) — 관망 고려"}
                    break
                except: pass

        _earnings_cache[code] = {"result": result, "ts": time.time()}
        return result

    except:
        return {"risk": "none", "desc": ""}

# ============================================================
# 🗂️ ⑤ 동시 신호 포트폴리오 관리
# ============================================================
def filter_portfolio_signals(alerts: list) -> list:
    """
    동시 다발 신호에서 실질 섹터 스코어 기반 중복 제거.
    - 두 신호 간 real_sector_score >= 50 이면 같은 실질섹터로 판단
    - 점수 높은 것 1개만 통과 (나머지 제외)
    - 국면별 총 신호 수 제한
    """
    if not alerts:
        return alerts

    regime    = get_market_regime().get("mode", "normal")
    max_total = {"bull": 8, "normal": 6, "bear": 3, "crash": 1}.get(regime, 6)

    # 점수 내림차순 정렬
    sorted_alerts = sorted(alerts, key=lambda x: x.get("score", 0), reverse=True)

    passed   = []
    excluded = set()

    for i, s in enumerate(sorted_alerts):
        if len(passed) >= max_total:
            break
        if s["code"] in excluded:
            continue
        passed.append(s)
        # 아직 통과 안 된 뒤 신호들과 실질 섹터 비교
        for j in range(i + 1, len(sorted_alerts)):
            peer = sorted_alerts[j]
            if peer["code"] in excluded:
                continue
            try:
                rs = calc_real_sector_score(s["code"], peer["code"],
                                            s["name"], peer["name"])
                if rs["score"] >= 50:
                    excluded.add(peer["code"])
                    print(f"  🗂️ 실질섹터 중복 제외: {peer['name']} ({rs['label']}, {rs['score']}점)")
            except:
                pass

    if len(passed) < len(sorted_alerts):
        skipped = len(sorted_alerts) - len(passed)
        print(f"  🗂️ 포트폴리오 필터: {skipped}개 제외 ({regime}장, 최대 {max_total}개)")

    return passed

def run_scan():
    # KRX 마감 후에도 NXT 운영 중이면 NXT 스캔 + 추적 체크 계속
    krx_open = is_market_open()
    nxt_open = is_nxt_open()
    if not krx_open and not nxt_open: return   # 모든 시장 마감
    if _bot_paused: return

    strict_tag = " [엄격]" if is_strict_time() else ""
    mkt_tag    = "KRX+NXT" if krx_open and nxt_open else ("NXT전용" if nxt_open else "KRX")
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 스캔{strict_tag} [{mkt_tag}]...", flush=True)
    try:
        alerts, seen = [], set()

        # KRX 스캔 (장 중에만)
        if krx_open:
            for stock in get_upper_limit_stocks():
                if stock["code"] in seen: continue
                r = analyze(stock)
                if r and time.time()-_alert_history.get(r["code"],0)>ALERT_COOLDOWN:
                    alerts.append(r); seen.add(r["code"])
            for stock in get_volume_surge_stocks():
                if stock["code"] in seen: continue
                r = analyze(stock)
                if r and time.time()-_alert_history.get(r["code"],0)>ALERT_COOLDOWN:
                    alerts.append(r); seen.add(r["code"])

        # ── NXT 스캔 (NXT 운영 시간에만) ──
        if nxt_open:
            for stock in get_nxt_surge_stocks():
                if stock["code"] in seen: continue
                r = analyze(stock)
                if r and time.time()-_alert_history.get(f"NXT_{r['code']}",0)>ALERT_COOLDOWN:
                    r["market"] = "NXT"
                    alerts.append(r); seen.add(stock["code"])

        # 조기포착·단기눌림목은 KRX 장중에만 의미 있음
        if krx_open:
            for s in check_early_detection():
                if s["code"] not in seen and time.time()-_alert_history.get(s["code"],0)>ALERT_COOLDOWN:
                    alerts.append(s); seen.add(s["code"])
            for s in check_pullback_signals():
                if s["code"] not in seen: alerts.append(s); seen.add(s["code"])
        # ── ⑤ 포트폴리오 필터 ──
        alerts = filter_portfolio_signals(alerts)

        if not alerts: print("  → 조건 충족 없음")
        else:
            print(f"  → {len(alerts)}개 감지! [{regime_label()}]")
            for s in alerts:
                is_nxt = s.get("market") == "NXT"
                hist_key = f"NXT_{s['code']}" if is_nxt else s["code"]
                mkt_tag  = " 🔵NXT" if is_nxt else ""
                print(f"  ✓ {s['name']}{mkt_tag} {s['change_rate']:+.1f}% [{s['signal_type']}] {s['score']}점")
                send_alert(s); _alert_history[hist_key] = time.time()
                save_signal_log(s)
                if s["signal_type"] == "EARLY_DETECT": save_early_detect(s)
                register_entry_watch(s)
                register_top_signal(s)
                # 섹터 모니터: 동시 최대 8개 스레드 제한
                if len(_sector_monitor) < 8:
                    start_sector_monitor(s["code"], s["name"])
                news_block_for_alert(s["code"], s["name"])
                try:
                    threading.Thread(
                        target=auto_update_theme,
                        args=(s["code"], s["name"], s["signal_type"]),
                        daemon=True
                    ).start()
                except: pass
                if s["signal_type"] != "ENTRY_POINT":
                    if s["code"] not in _detected_stocks:
                        _detected_stocks[s["code"]] = {"name":s["name"],"high_price":s["price"],
                            "entry_price":s["entry_price"],"stop_loss":s["stop_loss"],
                            "target_price":s["target_price"],"detected_at":s["detected_at"],"carry_day":0}
                    elif s["price"] > _detected_stocks[s["code"]]["high_price"]:
                        _detected_stocks[s["code"]]["high_price"] = s["price"]
                # sleep 제거: 20초 스캔 주기에서 신호당 1초 블록 불필요

        check_entry_watch()     # ★ 진입가 도달 체크
        check_reentry_watch()   # ★ 손절 후 재진입 감시
        track_signal_results()  # ★ 추적 중 신호 결과 체크
    except Exception as e: _log_error("run_scan", e, critical=True)

# ============================================================
# 🚀 실행
# ============================================================
def _shutdown(reason: str = "정상 종료"):
    """
    봇 자동 종료 — Railway Cron 환경에서 사용.
    Railway $5 플랜 400시간/월 제한 관리:
      - 평일 22일 × 12.2시간(08:00~20:10) ≈ 268시간 → 400시간 이내 여유
      - 공휴일 즉시 종료 (수 분 내) → 낭비 최소화
      - 주말 Cron 미실행 (0-4 = 일~목 UTC = 월~금 KST)
    """
    print(f"\n{'='*55}")
    print(f"🔴 봇 종료: {reason}  ({datetime.now().strftime('%H:%M')})")
    print(f"{'='*55}")
    try:
        send(f"🔴 <b>봇 자동 종료</b>  {reason}\n"
             f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    except: pass
    import os, sys
    sys.exit(0)

if __name__ == "__main__":
    print("="*55)
    print(f"📈 KIS 주식 급등 알림 봇 {BOT_VERSION} 시작")
    print(f"   업데이트: {BOT_DATE}")
    print("="*55)

    # ── 공휴일/주말 체크 → 즉시 종료 ──
    _load_kr_holidays(datetime.now().year)
    if is_holiday():
        print(f"📅 오늘은 공휴일/주말 — 봇 즉시 종료")
        try:
            send(f"📅 오늘은 공휴일/주말이에요. 봇을 시작하지 않아요.")
        except: pass
        import sys; sys.exit(0)

    load_carry_stocks()
    load_tracker_feedback()
    load_dynamic_themes()
    refresh_dynamic_candidates()
    _load_dynamic_params()          # ★ 재시작 후 조정된 파라미터 복원

    send(
        f"🤖 <b>주식 급등 알림 봇 ON ({BOT_VERSION})</b>\n"
        f"📅 {BOT_DATE}\n\n"
        "✅ 한국투자증권 API 연결\n"
        "🔵 NXT(넥스트레이드) 연동 활성\n\n"
        "<b>📡 스캔 주기</b>\n"
        "• 급등/상한가 스캔: <b>20초</b>\n"
        "• 중기 눌림목: <b>90초</b>\n"
        "• 뉴스 (3개 소스): <b>45초</b>\n"
        "• DART 공시: <b>60초</b>\n"
        "• 텔레그램 명령어: <b>10초</b>\n"
        "• NXT 장전 선포착: 08:00~09:00\n"
        "• NXT 마감 후 추적: 15:30~20:00\n\n"
        "💬 <b>/menu</b> — 버튼 메뉴 열기\n"
        "⚙️ <b>/설정</b> — BotFather 명령어 자동완성 등록법"
    )

    schedule.every(SCAN_INTERVAL).seconds.do(run_scan)
    schedule.every(NEWS_SCAN_INTERVAL).seconds.do(run_news_scan)
    schedule.every(DART_INTERVAL).seconds.do(run_dart_intraday)
    schedule.every(MID_PULLBACK_SCAN_INTERVAL).seconds.do(run_mid_pullback_scan)
    schedule.every(10).seconds.do(poll_telegram_commands)  # 30→10초
    schedule.every(INFO_FLUSH_INTERVAL).seconds.do(flush_info_alerts)  # INFO 알림 묶음 발송
    schedule.every().day.at("08:50").do(send_premarket_briefing)
    # TOP 5: 10:00부터 장마감까지 1시간마다 자동 발송
    # KRX only 종목: ~15:30, NXT 상장 종목 포함 시: ~20:00
    for _top_hhmm in ["10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00"]:
        schedule.every().day.at(_top_hhmm).do(
            lambda: None if is_holiday() or not is_any_market_open() else send_top_signals()
        )
    schedule.every().day.at(MARKET_OPEN).do(lambda: (
        None if is_holiday() else (
        _clear_all_cache(),
        reset_top_signals_daily(),                               # 최우선 종목 풀 초기화
        refresh_dynamic_candidates(),
        send(f"🌅 <b>장 시작!</b>  {datetime.now().strftime('%Y-%m-%d')}\n"
             f"📂 이월: {len(_detected_stocks)}개  |  📡 전체 스캔 시작")
    )))
    schedule.every().day.at(MARKET_CLOSE).do(
        lambda: None if is_holiday() else on_market_close()
    )
    # NXT 완전 마감 후 잔여 재진입 감시 초기화 + 결과 미입력 알림 (NXT 상장 종목용)
    schedule.every().day.at("20:05").do(
        lambda: (
            _reentry_watch.clear(),
            _send_pending_result_reminder(),   # NXT 마감 후 최종 미입력 알림
            print("🔵 NXT 마감(20:00) — 재진입 감시 전체 초기화")
        ) if not is_holiday() else None
    )
    # 평일만 백업 (장 운영일에만)
    schedule.every(BACKUP_INTERVAL_H).hours.do(
        lambda: run_auto_backup(notify=False) if not is_holiday() else None
    )

    # NXT 마감 후 자동 종료 (20:10)
    schedule.every().day.at("20:10").do(
        lambda: _shutdown("NXT 마감 (20:00) — 오늘 운영 완료")
        if not is_holiday() else None
    )

    run_scan()
    run_news_scan()
    run_mid_pullback_scan()

    while True:
        try:
            schedule.run_pending(); time.sleep(1)
        except Exception as e:
            print(f"⚠️ 메인 루프 오류: {e}"); time.sleep(5)
