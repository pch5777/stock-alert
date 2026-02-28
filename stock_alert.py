#!/usr/bin/env python3
"""
📈 KIS 주식 급등 알림 봇
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
버전: v16.0
날짜: 2026-02-28
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[변경 이력]

v27.0 (2026-02-28)  ← 현재
  ① 결과 미입력 알림 NXT 반영
     - KRX 마감(15:30)과 NXT 마감(20:05) 두 시점에서 모두 발송
     - 중복 방지 플래그로 같은 날 2회 이상 발송 안 함
     - NXT 운영 중이면 NXT 가격 기준 현재 수익률 표시
     - 미입력 시 처리 방식 명확히 안내 (자동 5일 추적 후 종가 기록)
  ② Railway 환경변수 TZ 경고
     - TZ=Asia/Seoul 미설정 시 시작 시 경고 출력
     - DART_API_KEY 환경변수 주석 명확화

v26.0 (2026-02-28)
  ① 동적 파라미터 영구 저장 (재시작 후에도 유지)
     - auto_tune 조정값을 dynamic_params.json에 저장
     - 봇 시작 시 자동으로 이전 조정값 복원
     - Railway 재시작해도 학습된 조건값 유지
  ② /result 수동입력 개선
     - signal_log.json (메인) + early_detect_log.json 동시 업데이트
     - 입력값과 현재가 기준 수익률 차이 5%p 이상이면 경고
     - 로그에 없는 종목도 수동 기록 가능 (signal_log에 MANUAL로 추가)
  ③ 장 마감 시 결과 미입력 종목 자동 알림
     - 오늘 신호 중 아직 추적중인 종목 목록 자동 발송
     - 현재가와 현재 수익률 함께 표시
     - /result 입력 가이드 포함

v25.0 (2026-02-28)
  ① 시간대별 승률 분석 추가
     - 장초반(09:00~10:00) / 오전(10:00~12:00) / 오후(12:00~14:00) / 장후반(14:00~15:30) 구간별 승률
     - /stats 에 시간대 분석 섹션 추가
     - 장마감 리포트에도 오늘 시간대 요약 포함
  ② 손실 패턴 자동 분석 강화
     - 손절 원인 유형화: 거래량소멸 / 외인매도 / 시장급락 / 단순손절
     - 손실 종목 공통점 자동 추출 (시간대 / 신호유형 / 테마여부)
     - /stats 에 "손실 패턴" 섹션 추가
     - 주간리포트 AI 분석 프롬프트에 손실패턴 데이터 포함
  ③ auto_tune 더 적극적으로 개선
     - MIN_SAMPLES 20→5 (더 빠르게 반응)
     - 조정 주기: 장마감마다 → 매일 + 샘플 3건 이상이면 즉시 반영
     - 손절률 연속 3회 이상이면 즉시 조건 강화 (긴급 튜닝)
     - ATR 손절배수 동적 조정 추가 (손절이 너무 타이트/루즈하면 자동 보정)
     - 시간대별 승률 낮은 구간 자동 감지 → 해당 구간 최소점수 상향

v24.0 (2026-02-28)
  ① TOP 5 알림 1시간 간격 자동 발송
     - 10:00부터 장마감까지 매 정시 자동 발송
     - KRX 마감(15:30) 후에도 NXT 운영 중이면 계속 발송 (최대 19:00)
     - is_any_market_open() 체크로 장 닫힌 시간은 자동 스킵
     - _top_signal_sent_today 플래그 제거 (반복 발송 방해 요소 제거)
     - /top 명령어도 플래그 우회 코드 불필요 → 단순화
     - 알림 헤더에 발송 시각 표시 (예: "최우선 종목 TOP 5  02/28 11:00")

v23.0 (2026-02-28)
  ① 자동 백업 시스템
     - GitHub Gist 백업: 6시간마다 자동 실행 (비공개 Gist)
     - 텔레그램 파일 전송: Gist 토큰 없을 때 대안
     - /백업 명령어: 즉시 수동 백업 + Gist ID 확인
     - /설정 명령어: Gist 토큰 발급 가이드 포함
     - Railway Variables: GITHUB_GIST_TOKEN 하나만 추가하면 됨
  ② 성능 최적화 (렉/버벅임 제거)
     - run_scan 신호당 sleep(1) 제거 (5신호=5초 블록 → 0초)
     - 섹터 모니터 스레드 최대 8개 제한 (무제한 → 제어)
     - 뉴스 역추적 30분 쿨다운 (동일 종목 중복 크롤링 방지)
     - _pending_info_alerts 최대 20개 + 1시간 자동 만료 (무한 누적 방지)
  ③ 메뉴 버튼 일일 성과 추가 + TOP 3→5
     - 📊 일일 성과 버튼 추가 (/daily 또는 /오늘)
     - 오늘 확정 결과 + 추적 중 잠정 수익률 (NXT 우선)
     - 최우선 종목 TOP 3 → TOP 5로 확대
     - 메뉴·BotFather 목록 모두 반영

v22.0 (2026-02-28)

v21.0 (2026-02-28)
  ① 장 마감 기준 NXT 완전 반영 + 앞으로의 기준 통일
     is_any_market_open()  — KRX or NXT 중 하나라도 열리면 True
     is_nxt_listed(code)   — NXT 상장 여부 확인 (비상장 캐시 활용)
     effective_market_close() — 실질 마감 여부
  ② 재진입 감시 NXT 연장
     - KRX only 종목: 15:30 마감 → 초기화
     - NXT 상장 종목: 20:00까지 NXT 가격으로 계속 감시
     - 20:05 스케줄로 NXT 마감 후 전체 초기화
  ③ 손절 후 재진입 등록 NXT 포함
     - KRX 장중: KRX 가격으로 등록
     - KRX 마감 후 NXT 운영 중: NXT 가격으로 등록
  ④ run_scan NXT 전용 모드
     - KRX 마감(15:30) 후에도 NXT 스캔·추적 체크 계속
     - 조기포착·단기눌림목은 KRX 장중에만 (NXT 마감 시까지 아님)
  ⑤ run_mid_pullback_scan NXT 포함
     - KRX 마감 후에도 NXT 급등 종목 눌림목 체크 계속

v20.0 (2026-02-28)
  ① 텔레그램 인라인 버튼 메뉴
     - /menu 또는 /도움 → 9개 기능 버튼으로 즉시 실행
     - 인라인 버튼 콜백 처리 (_handle_callback)
     - 알 수 없는 명령어 → 자동으로 메뉴 표시
  ② /설정 명령어 — BotFather 자동완성 등록 가이드
     - 복붙 가능한 한글 설명 목록 자동 출력
     - 등록 후 / 입력 시 한글 설명 자동완성 활성
  ③ 진입가 재알림 주기 최적화
     - 쿨다운: 30분 → 10분 (진입 구간 빠르게 지나감)
     - 20초 스캔 기준 조기포착 재확인 간격 조정
  ④ 손절 후 재진입 감시 최적화
     - 반등 조건: +5% → +3% (V자 반등 빠른 포착)
     - 거래량 조건: 2.0배 → 1.5배 완화
     - 만료 기준: 시간 제한 → 장 마감 시 자동 일괄 초기화

v19.0 (2026-02-28)
  ① 전체 스캔 주기 최적화 (KIS API 한도 내 최대 속도)
     급등 스캔:    60초 → 20초  (3배 빠름)
     뉴스 스캔:   120초 → 45초
     DART 공시:   180초 → 60초  (3배 빠름)
     중기 눌림목:  300초 → 90초
     섹터 모니터:  600초 → 180초
     텔레그램:      30초 → 10초  (명령어 즉시 반응)
     INFO 묶음:    600초 → 300초
  ② 조기 포착 재확인 간격 조정 (20초 스캔 기준 맞춤)

v18.0 (2026-02-28)
  ① 알림 3단계 중요도 분류 (🔴긴급 / 🟡일반 / 🔵참고)
     - get_alert_level() — 신호유형+점수+NXT보정으로 자동 결정
     - INFO 알림 10분마다 묶음 발송 (flush_info_alerts)
  ② 컴팩트 알림 모드
     - /compact 명령어로 즉시 전환
     - 1~2줄 요약: 종목명 / 변동률 / 점수 / 진입·손절·목표 / RR
     - 설정 파일 저장 (재시작 후에도 유지)
  ③ 손절 후 재진입 감시
     - 손절 확정 즉시 _reentry_watch 등록
     - 손절가 대비 +5% 반등 + 거래량 2배 이상 시 재진입 후보 알림
     - 최대 3시간 감시 후 자동 만료
  ④ Railway 재시작 완전 복원
     - carry_stocks + signal_log 추적 중 종목 동시 복원
     - 컴팩트 모드 설정 복원
     - 재시작 시 텔레그램 복원 현황 알림

v17.0 (2026-02-28)
  ① 오늘의 최우선 종목 TOP 5 (10:00 자동 발송 + /top 즉시 조회)
  ② 진입 재알림 (30분 쿨다운, 최대 3회)
  ③ 텔레그램 명령어 추가 (/top /nxt /week /compact)
  ④ 급등 종목 뉴스 역추적 (백그라운드 자동 조회)
  ① NXT 전면 연동
     - get_nxt_info() 캐시 + 비상장 종목 자동 제외 (_nxt_unavailable)
     - nxt_score_bonus() — 외인/기관/거래량/프리미엄 점수 보정
     - 급등·눌림목·조기포착·섹터 분석에 NXT 점수 반영
     - KRX 개장 전(08:00~09:00) NXT 선포착
     - KRX 마감 후(15:30~20:00) NXT로 진입가·손절 감시 연장
     - 장 마감 리포트에 NXT 실시간 수익률 표시
     - 08:50 브리핑에 NXT 외인 선취매 포함
  ② 공휴일 자동화
     - 공공데이터포털 API 자동 조회 (PUBLIC_DATA_API_KEY)
     - API 실패 시 하드코딩 fallback
     - 주말·공휴일 전체 스캔 자동 차단

v15.0 (2026-02-27)
  ① 종목명 신호별 색상 (🔴🟠🟡🟢🔵🟣)
  ② 진입가 박스 UI (┌─ 박스, 현재가 대비 % 실시간 표시)
  ③ 섹터 재조회 장 마감까지 10분마다 계속 모니터링
  ④ 분할 청산 가이드 (목표의 50% 도달 시 자동 알림)
  ⑤ 손절 원인 분석 (외인 매도량·거래량 급감 자동 분석)
  ⑥ 외인·기관 순매수 수량 표시
  ⑦ 차트 링크 인라인 버튼 → 외부 브라우저 오픈
  ⑧ 장 시작 전 브리핑 (매일 08:50)
  ⑨ 일별 리포트 개선 (전체 추적 중 잠정 수익률 + 누적 성과)
  ⑩ 주간 리포트 금요일 15:35으로 변경

v14.0 (2026-02-27)
  ① 중기 눌림목 스캐너 (AQR 모멘텀 팩터)
  ② 20일 이동평균 괴리율 (Renaissance 평균회귀)
  ③ 코스피 상대강도 (시장 중립 필터)
  ④ 거래량 Z-score 이상 탐지
  ⑤ 모멘텀 재점화 스코어
  ⑥ 자동 결과 추적 시스템
  ⑦ 자동 조건 조정 엔진
  ⑧ AI 주간 분석 (Claude API 연동)
  ⑨ 퀀트 눌림목 전략 (진입가·손절가·목표가 자동 계산)

v13.0 이하
  ① 조기 포착 (상한가 전 선진입)
  ② 급등/상한가 감지 (외국인·기관 동반)
  ③ 섹터 모멘텀 (동반 상승 + 가산점)
  ④ 뉴스 → 실제 주가 확인
  ⑤ DART 공시 → 실제 주가 확인
  ⑥ ATR 기반 동적 손절·목표가
  ⑦ 텔레그램 명령어 (/status /list /stop /resume)
  ⑧ 이월 눌림목 (최대 3일)
  ⑨ 동적 테마 자동 생성
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

BOT_VERSION = "v27.0"
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
            print(f"⚠️ 토큰 실패 ({attempt+1}): {e}"); time.sleep(5*(attempt+1))
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
    except:
        return []

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

        data[log_key] = {
            "log_key":      log_key,
            "code":         code,
            "name":         stock["name"],
            "signal_type":  sig_type,
            "score":        stock.get("score", 0),
            "sector_bonus": stock.get("sector_info", {}).get("bonus", 0),
            "sector_theme": stock.get("sector_info", {}).get("theme", ""),
            "detect_date":  datetime.now().strftime("%Y%m%d"),
            "detect_time":  datetime.now().strftime("%H:%M:%S"),
            "detect_price": stock["price"],
            "change_at_detect": stock.get("change_rate", 0),
            "volume_ratio": stock.get("volume_ratio", 0),
            "entry_price":  stock.get("entry_price", stock["price"]),
            "stop_price":   stock.get("stop_loss", 0),
            "target_price": stock.get("target_price", 0),
            "atr_used":     stock.get("atr_used", False),
            # 추적 결과 (초기값)
            "status":       "추적중",
            "exit_price":   0,
            "exit_date":    "",
            "exit_time":    "",
            "pnl_pct":      0.0,
            "exit_reason":  "",   # "목표가", "손절가", "시간초과", "수동"
            "max_price":    stock["price"],   # 추적 중 최고가 (MDD 계산용)
            "min_price":    stock["price"],   # 추적 중 최저가
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

            # ── 결과 판정 ──
            exit_reason = None
            exit_price  = price

            if price >= target:
                exit_reason = "목표가"
            elif price <= stop:
                exit_reason = "손절가"
            elif elapsed_days >= TRACK_MAX_DAYS:
                exit_reason = TRACK_TIMEOUT_RESULT

            if not exit_reason:
                continue   # 아직 추적 중

            # 수익률 계산
            pnl_pct = round((exit_price - entry) / entry * 100, 2) if entry else 0
            status  = "수익" if pnl_pct > 0 else ("손실" if pnl_pct < 0 else "본전")

            # 로그 업데이트
            rec["status"]      = status
            rec["exit_price"]  = exit_price
            rec["exit_date"]   = today
            rec["exit_time"]   = datetime.now().strftime("%H:%M:%S")
            rec["pnl_pct"]     = pnl_pct
            rec["exit_reason"] = exit_reason
            _tracking_notified.add(log_key)

            # ── 결과 알림 ──
            _send_tracking_result(rec)
            print(f"  📊 추적 완료: {rec['name']} {pnl_pct:+.1f}% ({exit_reason})")

            # 연속 손절 카운터 업데이트 (긴급 튜닝용)
            global _consecutive_loss_count
            if pnl_pct <= 0:
                _consecutive_loss_count += 1
                if _consecutive_loss_count >= EMERGENCY_TUNE_THRESHOLD:
                    print(f"  🚨 연속 손절 {_consecutive_loss_count}회 → 긴급 튜닝 실행")
                    auto_tune(notify=True)
                    _consecutive_loss_count = 0
            else:
                _consecutive_loss_count = 0   # 수익 나면 카운터 리셋

        if updated:
            with open(SIGNAL_LOG_FILE, "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            # tracker 피드백 즉시 갱신
            load_tracker_feedback()

    except Exception as e:
        print(f"⚠️ 추적 오류: {e}")


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
}

# 긴급 튜닝: 연속 손절 카운터
_consecutive_loss_count: int = 0
EMERGENCY_TUNE_THRESHOLD   = 3   # 연속 손절 N회 → 즉시 조건 강화

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
        print(f"⚠️ 자동 조정 오류: {e}")

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
            if (time.time() - info["start_ts"]) / 3600 > SECTOR_MONITOR_MAX_HOURS:
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
    log_key = f"{s['code']}_{datetime.now().strftime('%Y%m%d%H%M')}"
    _entry_watch[log_key] = {
        "code": s["code"], "name": s["name"], "entry_price": entry,
        "stop_loss": s.get("stop_loss",0), "target_price": s.get("target_price",0),
        "signal_type": s.get("signal_type",""), "detect_time": datetime.now().strftime("%H:%M"),
        "last_notified_ts": 0,   # 0 = 아직 미알림, 이후 타임스탬프로 쿨다운 관리
        "notify_count": 0,       # 알림 횟수 (최대 3회)
        "registered_ts": time.time(),
    }
    print(f"  🎯 진입가 감시 등록: {s['name']} {entry:,}원")

def check_entry_watch():
    if not _entry_watch: return
    # KRX 마감 후 NXT 운영 중이면 NXT 가격으로 진입가 감시 계속
    use_nxt = not is_market_open() and is_nxt_open()
    expired = []
    for log_key, watch in list(_entry_watch.items()):
        if time.time() - watch["registered_ts"] > 86400 or watch["notified"]:
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
            entry    = watch["entry_price"]
            diff_pct = (price - entry) / entry * 100

            # 진입가 ±2% 이내 진입 구간
            if abs(diff_pct) <= ENTRY_TOLERANCE_PCT:
                now_ts       = time.time()
                last_ts      = watch.get("last_notified_ts", 0)
                notify_count = watch.get("notify_count", 0)
                cooldown_sec = ENTRY_REWATCH_MINS * 60

                # 최대 3회, 쿨다운 지난 경우만 알림
                if notify_count >= 3: expired.append(log_key); continue
                if now_ts - last_ts < cooldown_sec: continue

                watch["last_notified_ts"] = now_ts
                watch["notify_count"]     = notify_count + 1

                sig_labels = {
                    "UPPER_LIMIT":"상한가","NEAR_UPPER":"상한가근접","SURGE":"급등",
                    "EARLY_DETECT":"조기포착","MID_PULLBACK":"중기눌림목","ENTRY_POINT":"단기눌림목",
                }
                sig        = sig_labels.get(watch["signal_type"], watch["signal_type"])
                diff_str   = f"+{diff_pct:.1f}%" if diff_pct >= 0 else f"{diff_pct:.1f}%"
                stop_pct   = round((watch["stop_loss"]   - entry) / entry * 100, 1) if entry else 0
                tgt_pct    = round((watch["target_price"] - entry) / entry * 100, 1) if entry else 0
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

    _send_alert_detail(s, emoji, title, nxt_badge, name_dot, stars, now_str,
                       stop_pct, target_pct, atr_tag, strict_warn, prev_tag,
                       entry_block, level)

# ── 내부 헬퍼: 상세 모드 실제 발송 (send_alert에서 호출) ──
def _send_alert_detail(s, emoji, title, nxt_badge, name_dot, stars, now_str,
                       stop_pct, target_pct, atr_tag, strict_warn, prev_tag,
                       entry_block, level):
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
        f"━━━━━━━━━━━━━━━\n\n"
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

    open_est = price/(1+change_rate/100)
    entry    = int((price-(price-open_est)*ENTRY_PULLBACK_RATIO)/10)*10
    stop, target, stop_pct, target_pct, atr_used = calc_stop_target(code, entry)
    return {"code":code,"name":stock.get("name",code),"price":price,
            "change_rate":change_rate,"volume_ratio":vol_ratio,
            "signal_type":signal_type,"score":score,"sector_info":sector_info,
            "entry_price":entry,"stop_loss":stop,"target_price":target,
            "stop_pct":stop_pct,"target_pct":target_pct,"atr_used":atr_used,
            "prev_upper":prev_upper,"reasons":reasons,"detected_at":datetime.now(),
            "nxt_delta": nxt_delta}

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

        open_est = price/(1+change_rate/100)
        entry = int((price-(price-open_est)*ENTRY_PULLBACK_RATIO)/10)*10
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
            sig_data[sig_matched_key].update({
                "status":      status,
                "pnl_pct":     pnl,
                "exit_date":   today,
                "exit_time":   datetime.now().strftime("%H:%M:%S"),
                "exit_reason": "수동입력",
            })
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

        completed = [v for v in data.values() if v.get("status") in ["수익","손실","본전"]]
        tracking  = [v for v in data.values() if v.get("status") == "추적중"]

        if len(completed) < 3:
            send(f"📊 아직 결과가 {len(completed)}건뿐이에요. (추적 중: {len(tracking)}건)\n"
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

        total_pnl  = [v["pnl_pct"] for v in completed]
        total_win  = sum(1 for p in total_pnl if p > 0)
        avg_pnl    = sum(total_pnl) / len(total_pnl)
        total_rate = total_win / len(total_pnl) * 100

        msg = (f"📊 <b>자동 추적 성과 통계</b>\n"
               f"완료 {len(completed)}건  |  추적 중 {len(tracking)}건\n"
               f"전체 승률 <b>{total_rate:.0f}%</b>  |  평균 <b>{avg_pnl:+.1f}%</b>\n"
               f"━━━━━━━━━━━━━━━\n")

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
        if not alerts: print("  → 조건 충족 없음")
        else:
            print(f"  → {len(alerts)}개 감지!")
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
    except Exception as e: print(f"⚠️ 스캔 오류: {e}")

# ============================================================
# 🚀 실행
# ============================================================
if __name__ == "__main__":
    print("="*55)
    print(f"📈 KIS 주식 급등 알림 봇 {BOT_VERSION} 시작")
    print(f"   업데이트: {BOT_DATE}")
    print("="*55)

    load_carry_stocks()
    load_tracker_feedback()
    load_dynamic_themes()
    refresh_dynamic_candidates()
    _load_dynamic_params()          # ★ 재시작 후 조정된 파라미터 복원
    _load_kr_holidays(datetime.now().year)   # 공휴일 선로드

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
    # 6시간마다 자동 백업 (Gist 우선, 없으면 텔레그램 파일)
    schedule.every(BACKUP_INTERVAL_H).hours.do(lambda: run_auto_backup(notify=False))

    # 봇 시작 시 공휴일 미리 로드
    _load_kr_holidays(datetime.now().year)

    run_scan()
    run_news_scan()
    run_mid_pullback_scan()

    while True:
        try:
            schedule.run_pending(); time.sleep(1)
        except Exception as e:
            print(f"⚠️ 메인 루프 오류: {e}"); time.sleep(5)
