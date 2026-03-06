#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📈 KIS 주식 급등 알림 봇
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
버전: v37.30-partialbasis1
날짜: 2026-03-06
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[변경 이력]

- v37.30-partialbasis1 (2026-03-06): 분할 청산 타이밍 메시지에 분할 청산 기준 정보를 추가. 현재 수익률, 절반 익절 기준 수익률, 목표 도달률, 현재가-진입가-목표가를 함께 표시해 지금 분할 청산이 왜 정당한지 즉시 판단 가능하게 개선.
- v37.29-partialentryfix1 (2026-03-06): 분할 청산 타이밍 메시지에 진입가가 누락되던 문제 수정. 일반 분기와 외국인/기관 매매 코멘트 분기 모두에서 현재가-진입가-목표가가 함께 표시되도록 정합화.

- v37.28b-etfscore-exitentry-sectoricon1 (2026-03-06): ETF/ETN/지수형 종목을 점수용 전용으로 분리해 포착/진입감시/분할청산/섹터모니터 대상에서 제외. 분할 청산 메시지에 진입가 추가. 섹터 모니터링/뉴스+주가 연동 하위 종목 표기를 이모티콘 대신 부호형(🟩/⬜/🟥)으로 정리.

- v37.27-sector-namefix1 (2026-03-06): 섹터 모니터링 하위 종목 리스트에서 종목명이 비어 보이던 문제를 보완. calc_sector_momentum() 단계에서 peer 종목명을 즉시 복구하고, 섹터 모멘텀 메시지/요약 생성 직전에도 _resolve_stock_name() fallback을 적용해 하단 섹터 종목명 누락을 줄임.

- v37.26-strict-namefix1 (2026-03-06): 포착/중기 눌림목/진입감시 알림에서 종목명이 비어 보이던 문제를 수정. 후보군 편입, 신호 생성, 로그 저장, 진입 감시 등록, 차트 버튼 발송 단계에 종목명 복구 fallback을 추가하여 코드만 보이던 현상을 방지.

- v37.25-strict-cleanup1 (2026-03-06): 엄격 진입가 도달 체계로 전환하기 위해 과거 signal_log의 비실진입(actual_entry!=True) 자동 entry_hit 기록을 1회성으로 초기화하는 마이그레이션 추가. 실행 전 원본 signal_log 백업 생성, cleanup 마커 파일로 재실행 방지.
- v37.24-strict-entryhit1 (2026-03-06): 진입가 도달(entry_hit) 판정을 ATR 허용오차 기반에서 엄격형으로 변경. 이제 현재가가 진입가 이하(price <= entry)일 때만 [진입가 도달!] 알림과 entry_hit 기록이 발생하도록 수정. 허용오차만으로 진입가 도달로 처리되던 오인식을 방지.

- v37.23-allin1 (2026-03-06): v37.18 기능(섹터/뉴스연동 감시상태 표기, 손익 방어, 07:30 장전 워치리스트, 레짐 한글화)을 유지하면서 대시보드 상수 누락(NameError) 안정화 및 RSS XML 파싱 경고(XMLParsedAsHTMLWarning) 제거(BeautifulSoup html.parser fallback 제거).
- v37.18-newslink-watch1 (2026-03-05): '뉴스+주가 연동' 알림의 종목 리스트에도 포착/진입감시 종목 상태를 표기(진입가 도달 시 진입가 대비 현재가 수익률, 미도달 시 '미도달' 표시).

- v37.17-sector-watch1 (2026-03-05): 섹터 모니터링 메시지에 '포착/진입감시 종목' 상태를 표기(진입가 도달 시 진입가 대비 현재가 수익률, 미도달 시 '미도달' 표시). 섹터 스냅샷에 현재가(price) 포함.

- v37.16-profit-guard2-ui2 (2026-03-05): 장전 워치리스트 발송 시간을 07:55 → 07:30으로 변경(비장중 이슈 반영 포함). 야간 무알림 구간도 20:00~07:30으로 조정.

- v37.14-profit-guard1 (2026-03-05): (1) 장마감 전/후 '진입가 도달(entry_hit)' 감시 종목에 대해 지정학/뉴스/DART/지표 리스크 감지 시 손익 방어 가이드 자동 알림(쿨다운 포함). (2) 비장중(장종료/휴장) 이슈(지정학 섹터영향 + DART 강재료)를 07:30 익개장 워치리스트에 반영하여 섹터·종목 후보 알림.

- v37.12-hotfix-news7 (2026-03-05): RSS/XML 파싱을 표준 XML 파서(ElementTree) 우선으로 변경하여 XMLParsedAsHTMLWarning 제거 및 뉴스 스캔 안정성 개선.

- v37.11-hotfix-news6 (2026-03-05): 뉴스 소스 3→6 확장(타이틀+description 사용), 시작 배너 문구 갱신. 상품(B) 제외/상한가 쿨다운/404 비활성화는 유지.


- v37.10-all5-fix10B (2026-03-05): 후보군(포착/진입감시)에서 커버드콜/타겟위클리/월배당/채권/리츠 + 인버스/레버리지 상품 제외(B), 레짐/점수조정 센서로만 활용.
- v37.10-all5-fix13-exitvirtual (2026-03-05): 분할 청산 가이드 기본을 '가상 진입(진입가 도달 entry_hit=True)' 기준으로 변경. 필요 시 ALLOW_VIRTUAL_EXIT_GUIDE=0으로 '실진입(actual_entry=True)'만 허용. 종목별 30분 쿨다운 유지.
v37.10-all5-fix7 (2026-03-05)
- [Fix] GEO_SECTOR_BIAS 전역 기본값을 실제 코드에 선언하여 신호 저장 오류 제거

v37.10-all5-fix6 (2026-03-05)
- [Fix] get_us_market_signals: compute_market_regime 호출 시 nasdaq_fut_pct NameError 제거(nasdaq_chg 사용)
- [Fix] GEO_SECTOR_BIAS 기본값 정의로 신호 저장 오류 제거

v37.10-all5-fix4 (2026-03-05)
- [Fix] MARKET_REGIME 기본값/compute_market_regime 추가(NameError 제거)
- [Fix] 랭킹 API 404 발생 시 실제로 '오늘 비활성' 파일 기록(재시도 완전 차단)
- [Fix] inquire-daily-trade 404 시 오늘 비활성 처리(로그/호출 스팸 방지)
v37.10-all5-fix3 (2026-03-05)
- [Fix] chgrate-pcls-100 404 발생 시 오늘은 랭킹 API 호출 중단(재시도 스팸/지연 제거) → 유니버스 후보군만 사용
v37.10-all5 (2026-03-05)
- [ALL] 5개 개선 일괄 적용: (1) 크래시가드+에러로그/1회알림 (2) 레짐피처 저장+리포트 (3) 유니버스 자동확장/축소+다양성 제한 (4) 텔레그램 대시보드(편집 업데이트) (5) 지정학/뉴스 점수보정 통합+소스 자동차단

v37.9-universe3 (2026-03-05)
- 오버나이트 위험 알림: 20:00~07:30 야간에는 즉시 발송 금지(저장만) → 07:30 워치리스트 요약에 함께 재알림

v37.9-universe2 (2026-03-05)
- 장 종료(비장중)에는 '급등 상위' 후보군 생성 스킵 → 익개장 워치리스트 생성/저장
- 익개장 07:30 워치리스트 요약 알림(야간 무알림)

v37.9-universe1 (2026-03-05)
- KIS 랭킹 API(chgrate-pcls-100) 404 시 유니버스 기반 후보군 생성으로 자동 대체
- 유니버스(최대 200) 구성: carry/signal_log 기반 + 파일(universe.json) 지원
- 후보군 계산 캐시(45초)로 API 호출 부담 완화

v37.8-fixbaseurl3 (2026-03-05)  ← 현재
  [Fix] KIS API 오류 시 응답 진단 강화(url/status/content-type/body snippet) + JSON 에러 필드 파싱
  [Keep] KIS_BASE_URL 환경변수 우선 + 실전 기본값(9443) 유지, VTS 자동 스왑 차단

v37.8-fixbaseurl2 (2026-03-05)
  [Fix] 모듈 도큐스트링이 파일 첫 문장이 되도록 정리 → 버전/날짜 파싱 unknown 방지
  [Keep] KIS_BASE_URL 환경변수 우선 + 실전 기본값(9443) 유지, VTS 자동 스왑 차단

"""


# ============================================================
# 후보군(포착/진입감시) 제외 규칙  (B 옵션)
# - 커버드콜/타겟위클리/월배당/채권/리츠 + 인버스/레버리지 상품은
#   "실전 진입 대상"에서 제외하되, 레짐/조건 조정 센서로는 활용 가능.
# ============================================================
EXCLUDE_TRADE_KEYWORDS = [
    # Income / covered-call / weekly products
    "커버드콜", "Covered Call", "coveredcall",
    "타겟위클리", "Target Weekly", "타겟 위클리",
    "월배당", "Monthly", "월지급", "인컴", "Income",
    # Bonds / REITs
    "채권", "Bond", "채권형",
    "리츠", "REIT",
    # Inverse / Leveraged
    "인버스", "Inverse", "inverse",
    "레버리지", "Leveraged", "leverage", "레버",
]

def is_trade_candidate_name(name: str) -> bool:
    """실전 진입(포착/진입감시) 대상인지 판단"""
    if not name:
        return True
    for kw in EXCLUDE_TRADE_KEYWORDS:
        if kw and kw in name:
            return False
    return True



# 버전을 도큐스트링에서 자동 파싱 → 한 곳(docstring)만 수정하면 모든 표시에 반영
import sys
import hashlib
import traceback
import re as _re


# === Regime label localization (Korean) ===
REGIME_KO_MAP = {
    "risk_on": "강세장",
    "neutral": "보통장",
    "risk_off": "약세장",
    "panic": "패닉장",
    "unknown": "보통장",
}

def regime_label_ko(label: str) -> str:
    try:
        return REGIME_KO_MAP.get((label or "").strip().lower(), "보통장")
    except Exception:
        return "보통장"



# --- Global state defaults (to prevent NameError at runtime) ---
GEO_SECTOR_BIAS: dict = {}
MARKET_REGIME: dict = {"label": "unknown", "details": {}}

# --- HOTFIX: safe response JSON parsing (prevents JSONDecodeError / empty responses) ---
def safe_json_response(resp):
    """Return resp.json() safely; if invalid/empty/HTML, return {}."""
    try:
        txt = (getattr(resp, "text", "") or "")
        if not txt.strip():
            return {}
        ct = (getattr(resp, "headers", {}) or {}).get("Content-Type", "")
        ct = (ct or "").lower()
        if "json" not in ct and txt.lstrip().startswith("<"):
            return {}
        return resp.json()
    except Exception:
        return {}

# --- HOTFIX: safe parsing helpers ---
def safe_int(value, default=0):
    """Convert value to int safely. Handles '', '-', None, commas, floats."""
    try:
        if value is None:
            return default
        s = str(value).replace(",", "").strip()
        if s in ("", "-", "None", "null", "NULL"):
            return default
        return int(float(s))
    except Exception:
        return default

def normalize_stock_code(value):
    """Return 6-digit numeric stock code or None."""
    if value is None:
        return None
    s = str(value).strip()
    if len(s) == 6 and s.isdigit():
        return s
    return None

_ver_match = _re.search(r"버전:\s*(v[0-9][0-9A-Za-z._-]*)", __doc__ or "")
BOT_VERSION = _ver_match.group(1) if _ver_match else "unknown"
_date_match = _re.search(r"날짜:\s*([\d-]+)", __doc__ or "")
BOT_DATE    = _date_match.group(1) if _date_match else "unknown"

import os, requests, time, schedule, json, random, threading, math
import xml.etree.ElementTree as ET
from datetime import datetime, time as dtime, timedelta
from zoneinfo import ZoneInfo

# Timezone helpers (always Asia/Seoul for scheduling gates)
_KST = ZoneInfo("Asia/Seoul")
def _now_kst() -> datetime:
    return datetime.now(_KST)

def _is_quiet_night(now: datetime | None = None) -> bool:
    """Quiet night window: 20:00~07:30 (no push; store only)."""
    now = now or _now_kst()
    t = now.time()
    return (t >= dtime(20, 0)) or (t < dtime(7, 55))
from bs4 import BeautifulSoup
# ── Simple throttles to reduce Telegram spam ────────────────────────────────
_LAST_ALERT_TS: dict[str, int] = {}

def _throttle_ok(store: dict, key: str, cooldown_sec: int) -> bool:
    now = int(time.time())
    last = int(store.get(key, 0) or 0)
    if now - last < cooldown_sec:
        return False
    store[key] = now
    return True


# Market regime snapshot (updated periodically; safe default)
MARKET_REGIME: dict = {"label": "unknown", "detail": {}}

def compute_market_regime(nasdaq_fut_pct: float | None, vix: float | None, dxy: float | None) -> dict:
    """Return a simple market regime label for feature/logging.

    - risk_off: futures down and/or VIX/DXY elevated
    - risk_on:  futures up and VIX contained
    - neutral:  otherwise

    This is intentionally conservative; it is used for *conditioning* signals, not trading directly.
    """
    try:
        fut = float(nasdaq_fut_pct) if nasdaq_fut_pct is not None else 0.0
    except Exception:
        fut = 0.0
    try:
        v = float(vix) if vix is not None else None
    except Exception:
        v = None
    try:
        d = float(dxy) if dxy is not None else None
    except Exception:
        d = None

    # Heuristics (tunable later)
    risk_off = False
    risk_on = False

    if fut <= -0.6:
        risk_off = True
    if fut >= 0.6:
        risk_on = True

    if v is not None:
        if v >= 25:
            risk_off = True
        elif v <= 18 and fut >= 0.2:
            risk_on = True

    if d is not None:
        if d >= 103:
            risk_off = True
        elif d <= 100 and fut >= 0.2:
            risk_on = True

    label = "neutral"
    if risk_off and not risk_on:
        label = "risk_off"
    elif risk_on and not risk_off:
        label = "risk_on"

    return {"label": label, "detail": {"nasdaq_fut_pct": fut, "vix": v, "dxy": d}}


# ============================================================
# 💾 Persistent Storage (코드 교체/배포에도 데이터 보존)
#   - Railway Volume(/data) + 환경변수 STOCK_ALERT_DATA_DIR 지원
#   - 파일은 모두 DATA_DIR 아래로 강제
#   - JSON 저장은 atomic write + 백업 스냅샷(최근 N개)로 보호
# ============================================================
DATA_DIR = os.getenv("STOCK_ALERT_DATA_DIR") or os.path.join(
    os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "."), "stock_alert"
)
DATA_DIR = os.path.abspath(DATA_DIR)
# --- Dashboard scheduling/state (prevent NameError & allow env overrides) ---
DASHBOARD_UPDATE_EVERY_SEC = int(os.getenv("DASHBOARD_UPDATE_EVERY_SEC", "30"))
DASHBOARD_STATE_FILE = os.getenv("DASHBOARD_STATE_FILE") or os.path.join(DATA_DIR, "dashboard_state.json")
_LAST_DASHBOARD_TS = 0.0

MAX_STATE_BACKUPS = int(os.getenv("MAX_STATE_BACKUPS", "30") or "30")
_BACKUP_DIR = os.path.join(DATA_DIR, "backups")

_PERSIST_FILES = [
    "signal_log.json",
    "dynamic_params.json",
    "carry_stocks.json",
    "early_detect_log.json",
    "auto_tune_log.json",
    "dynamic_themes.json",
    "news_cooccur.json",
    "compact_mode.json",
]

def _ensure_dir(path: str):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        print(f"⚠️ DATA_DIR 생성 실패: {path} ({e})")

def _snapshot_backup(file_path: str):
    """기존 파일이 있으면 backups로 스냅샷 백업(최근 N개 유지)"""
    try:
        if not os.path.isfile(file_path):
            return
        _ensure_dir(_BACKUP_DIR)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = os.path.basename(file_path)
        backup_path = os.path.join(_BACKUP_DIR, f"{base}.{ts}.bak")
        # copy (binary safe)
        with open(file_path, "rb") as rf, open(backup_path, "wb") as wf:
            wf.write(rf.read())

        # prune old backups
        backups = sorted(
            [p for p in os.listdir(_BACKUP_DIR) if p.startswith(base + ".")],
            reverse=True,
        )
        for old in backups[MAX_STATE_BACKUPS:]:
            try:
                os.remove(os.path.join(_BACKUP_DIR, old))
            except:
                pass
    except Exception as e:
        print(f"⚠️ 백업 스냅샷 실패: {os.path.basename(file_path)} ({e})")

def _atomic_write_bytes(file_path: str, data: bytes):
    """tmp → fsync → os.replace 로 원자적 저장"""
    _ensure_dir(os.path.dirname(file_path))
    tmp_path = file_path + ".tmp"
    with open(tmp_path, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, file_path)

def _write_json_atomic(file_path: str, obj, indent: int = 2):
    try:
        _snapshot_backup(file_path)
        payload = json.dumps(obj, ensure_ascii=False, indent=indent).encode("utf-8")
        _atomic_write_bytes(file_path, payload)
    except Exception as e:
        print(f"⚠️ JSON 저장 실패: {os.path.basename(file_path)} ({e})")

def _migrate_legacy_files():
    """기존(현재 작업 디렉토리)에 있던 JSON이 있으면 DATA_DIR로 1회 복사"""
    try:
        cwd = os.getcwd()
        for fn in _PERSIST_FILES:
            legacy = os.path.join(cwd, fn)
            target = os.path.join(DATA_DIR, fn)
            if os.path.isfile(legacy) and not os.path.isfile(target):
                _ensure_dir(DATA_DIR)
                try:
                    with open(legacy, "rb") as rf, open(target, "wb") as wf:
                        wf.write(rf.read())
                    print(f"✅ 레거시 파일 이관: {fn} → {target}")
                except Exception as e:
                    print(f"⚠️ 레거시 이관 실패: {fn} ({e})")
    except Exception as e:
        print(f"⚠️ 레거시 이관 로직 오류: {e}")

def _storage_diagnostics_once():
    """시작 시 1회: DATA_DIR/볼륨/쓰기 가능 여부/파일 목록 출력"""
    try:
        _ensure_dir(DATA_DIR)
        _ensure_dir(_BACKUP_DIR)
        rp = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "")
        print("=======================================================")
        print("💾 Persistent Storage Check")
        print(f"   DATA_DIR: {DATA_DIR}")
        if rp:
            print(f"   RAILWAY_VOLUME_MOUNT_PATH: {rp}")
        # writable test
        test_path = os.path.join(DATA_DIR, ".write_test")
        try:
            with open(test_path, "w", encoding="utf-8") as f:
                f.write(datetime.now().isoformat())
            os.remove(test_path)
            print("   Writable: ✅ OK")
            # persistent probe file (kept) to prove writes survive redeploys
            probe_path = os.path.join(DATA_DIR, ".storage_ok")
            try:
                with open(probe_path, "w", encoding="utf-8") as f:
                    f.write(datetime.now().isoformat())
                print(f"   Probe file: {probe_path} ✅ wrote")
            except Exception as pe:
                print(f"   Probe file: ❌ FAIL ({pe})")
        except Exception as e:
            print(f"   Writable: ❌ FAIL ({e})")
        # list key files
        existing = []
        for fn in _PERSIST_FILES:
            fp = os.path.join(DATA_DIR, fn)
            if os.path.isfile(fp):
                try:
                    size = os.path.getsize(fp)
                    existing.append(f"{fn}({size}B)")
                except:
                    existing.append(fn)
        print("   Files:", ", ".join(existing) if existing else "(none)")
        print("=======================================================")
    except Exception as e:
        print(f"⚠️ 스토리지 진단 실패: {e}")


# --- HOTFIX v37.3: safe AI response extractor (prevents KeyError: 'content') ---
def extract_ai_text(resp_json):
    """Safely extract analysis text from AI provider response."""
    try:
        # Anthropic-style: {"content":[{"text":"..."}]}
        content = resp_json.get("content")
        if isinstance(content, list) and content:
            t = content[0].get("text", "")
            if t:
                return str(t).strip()
    except Exception:
        pass
    try:
        # OpenAI-style: {"choices":[{"message":{"content":"..."}}]}
        choices = resp_json.get("choices")
        if isinstance(choices, list) and choices:
            msg = (choices[0].get("message") or {})
            t = msg.get("content", "")
            if t:
                return str(t).strip()
    except Exception:
        pass
    return ""


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
KIS_BASE_URL       = os.environ.get("KIS_BASE_URL", "https://openapi.koreainvestment.com:9443").strip()
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
CARRY_FILE            = os.path.join(DATA_DIR, "carry_stocks.json")
EARLY_LOG_FILE        = os.path.join(DATA_DIR, "early_detect_log.json")

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

# 디버그: 어떤 KIS 서버로 붙는지 1회 출력(환경 혼동 방지)
try:
    print(f"🔗 KIS_BASE_URL: {KIS_BASE_URL}", flush=True)
except Exception:
    pass

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
DYNAMIC_THEME_FILE  = os.path.join(DATA_DIR, "dynamic_themes.json")
CORR_MIN            = 0.70
CORR_LOOKBACK       = 20
NEWS_COOCCUR_FILE   = os.path.join(DATA_DIR, "news_cooccur.json")

# ── 섹터 지속 모니터링 ──
_sector_monitor     = {}
SECTOR_MONITOR_INTERVAL  = 180   # 600→180초 (3분)
SECTOR_MONITOR_MAX_HOURS = 6

# ── 진입가 감지 ──
_entry_watch        = {}
ENTRY_TOLERANCE_PCT  = 2.0   # 진입가 ±2% 이내 → 진입 구간
ENTRY_REWATCH_MINS   = 10    # 30→10분 (진입 구간이 빠르게 지나감)
ENTRY_WATCH_MAX_HOURS = 6    # 진입가 감시 최대 6시간 → 장 마감 시 자동 만료됨

# ── 분할 청산 가이드(메시지 스팸 방지) ──
ALLOW_VIRTUAL_EXIT_GUIDE = os.getenv('ALLOW_VIRTUAL_EXIT_GUIDE', '1') == '1'  # 1이면 '진입가 도달'만으로도 가이드 허용
PARTIAL_EXIT_GUIDE_COOLDOWN_MIN = int(os.getenv('PARTIAL_EXIT_GUIDE_COOLDOWN_MIN', '30') or '30')
_partial_exit_last_ts: dict[str, float] = {}  # code -> last sent ts

# ── 오늘의 최우선 종목 ──
_today_top_signals: dict = {}
TOP_SIGNAL_SEND_AT       = "10:00"  # 시작 시각 (이후 1시간마다 반복)

# ── 뉴스 역추적 캐시 ──
_news_reverse_cache: dict = {}

# v37.0: 지정학 상태 전방 선언 (실제 초기화는 get_market_regime 영역)
# _geo_event_state, _us_cache 등은 파일 하단에서 정의됨 (Python 모듈 로딩 순서상 안전)

# ── 컴팩트 알림 모드 ──
# True면 1~2줄 요약, False면 기존 상세 포맷
_compact_mode: bool = False
COMPACT_MODE_FILE   = os.path.join(DATA_DIR, "compact_mode.json")

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
# REENTRY_BOUNCE_PCT 제거 — calc_reentry_bounce() ATR 기반으로 대체됨
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
    """v37.0: KRX + NXT 장 초반/후반 엄격 시간대 판별"""
    n   = datetime.now().time()
    # KRX 장 초반/후반
    o_e = (datetime.now().replace(hour=9,  minute=0)  + timedelta(minutes=STRICT_OPEN_MINUTES)).time()
    c_s = (datetime.now().replace(hour=15, minute=30) - timedelta(minutes=STRICT_CLOSE_MINUTES)).time()
    if dtime(9, 0) <= n <= o_e or n >= c_s:
        return True
    # NXT 장전 초반 (08:00~08:10) + 장후반 (19:50~20:00)
    if n <= dtime(8, STRICT_OPEN_MINUTES):
        return is_nxt_open()  # NXT 열려있을 때만
    if dtime(19, 50) <= n <= dtime(20, 0):
        return True
    return False

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
    """KIS GET with retry/backoff. Never raises.

    On failure, prints a compact diagnostic (url/status/content-type/body-snippet).
    """
    last_exc = None
    last_status = None
    last_ct = ""
    last_body_snip = ""
    last_url = url

    for attempt in range(3):
        try:
            resp = _session.get(url, headers=_headers(tr_id), params=params, timeout=15)
            last_status = getattr(resp, "status_code", None)
            last_ct = ((getattr(resp, "headers", {}) or {}).get("Content-Type", "") or "")
            last_url = getattr(resp, "url", url) or url

            # If token expired, refresh once then retry.
            if last_status == 403:
                global _access_token
                _access_token = None
                resp = _session.get(url, headers=_headers(tr_id), params=params, timeout=15)
                last_status = getattr(resp, "status_code", None)
                last_ct = ((getattr(resp, "headers", {}) or {}).get("Content-Type", "") or "")
                last_url = getattr(resp, "url", url) or url

            if last_status == 200:
                return safe_json_response(resp)

            # Capture a small, safe snippet for debugging.
            try:
                raw = (getattr(resp, "text", "") or "").strip()
                raw = " ".join(raw.split())  # collapse whitespace
                last_body_snip = raw[:200]
            except Exception:
                last_body_snip = ""

            # If server returned JSON error, prefer its fields.
            j = safe_json_response(resp)
            if isinstance(j, dict) and j:
                msg_cd = j.get("msg_cd") or j.get("error_code") or j.get("code")
                msg1 = j.get("msg1") or j.get("message") or j.get("error_description") or j.get("error")
                rt_cd = j.get("rt_cd")
                last_exc = f"rt_cd={rt_cd} msg_cd={msg_cd} msg={msg1}"
            else:
                last_exc = None

        except Exception as e:
            last_exc = e

        try:
            time.sleep(0.8 * (2 ** attempt))
        except Exception:
            pass

    # Auto-disable unsupported endpoints for the rest of the day (to avoid noisy retries)
    try:
        if last_status == 404 and isinstance(last_url, str):
            if "chgrate-pcls-100" in last_url:
                _disable_rank_api_for_today("404")
            if "inquire-daily-trade" in last_url:
                _disable_daily_trade_api_for_today("404")
    except Exception:
        pass

    try:
        print(
            f"⚠️ API 오류 ({tr_id}): url={last_url} status={last_status} ct={last_ct} "
            f"err={last_exc} body={last_body_snip}"
        )
    except Exception:
        pass
    return {}



def _safe_get_meta(url: str, tr_id: str, params: dict):
    """_safe_get + (status, content_type, body_snippet) 를 함께 반환."""
    last_exc = None
    last_status = None
    last_ct = ""
    last_body_snip = ""
    last_url = url

    for attempt in range(3):
        try:
            resp = _session.get(url, headers=_headers(tr_id), params=params, timeout=15)
            last_status = getattr(resp, "status_code", None)
            last_ct = ((getattr(resp, "headers", {}) or {}).get("Content-Type", "") or "")

            if last_status != 200:
                try:
                    txt = getattr(resp, "text", "") or ""
                    last_body_snip = (txt[:200] + ("…" if len(txt) > 200 else "")).replace("\n", " ").replace("\r", " ")
                except:
                    last_body_snip = ""
                break

            try:
                data = resp.json()
            except Exception as e:
                last_exc = e
                try:
                    txt = getattr(resp, "text", "") or ""
                    last_body_snip = (txt[:200] + ("…" if len(txt) > 200 else "")).replace("\n", " ").replace("\r", " ")
                except:
                    last_body_snip = ""
                break

            return data or {}, last_status, last_ct, last_body_snip
        except Exception as e:
            last_exc = e
            time.sleep(0.8 * (attempt + 1))

    try:
        print(f"⚠️ API 오류 ({tr_id}): url={last_url} status={last_status} ct={last_ct} err={last_exc} body={last_body_snip}")
    except:
        pass

    return {}, last_status, last_ct, last_body_snip

# ============================================================
# 📊 일봉 데이터 (공통 사용)
# ============================================================
_daily_cache = {}  # code → {items, ts}
_atr_cache   = {}  # code → {atr, date}  하루 1회 갱신

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
        resp_json = _safe_get(url, "FHKST03010100", params)
        items = resp_json.get("output2", []) if isinstance(resp_json, dict) else []
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
    v37.0 강화: signal_log.json 과거 신호 분석.
    ① 동일 종목 전적 → ② 유사 조건 패턴 (동일 신호유형 + 상승률±3 + 거래량±3)
    """
    try:
        data = _load_signal_history()
        completed = _get_completed_signals(data)
        if len(completed) < 3:
            return ""

        lines = []

        # ── ① 동일 종목 전적 (최우선 정보) ──
        same_stock = [v for v in completed if v.get("code") == code]
        if len(same_stock) >= 2:
            s_wins = sum(1 for v in same_stock if v["pnl_pct"] > 0)
            s_wr   = round(s_wins / len(same_stock) * 100)
            s_avg  = round(sum(v["pnl_pct"] for v in same_stock) / len(same_stock), 1)
            s_best = max(same_stock, key=lambda x: x["pnl_pct"])
            s_emoji = "🟢" if s_wr >= 60 else ("🟡" if s_wr >= 40 else "🔴")
            s_name = same_stock[0].get("name", code)
            lines.append(
                f"  {s_emoji} <b>{s_name} 전적</b>: {len(same_stock)}건 승률 {s_wr}% 평균 {s_avg:+.1f}%"
                f" (최고 {s_best['pnl_pct']:+.1f}%)"
            )

        # ── ② 유사 조건 패턴 (기존 로직) ──
        same_type = [v for v in completed if v.get("signal_type") == signal_type]
        if len(same_type) >= 3:
            similar = [v for v in same_type
                       if abs(v.get("change_at_detect", 0) - change_rate) <= 3.0
                       and abs(v.get("volume_ratio", 0) - vol_ratio) <= 3.0]
            if len(similar) < 2:
                similar = same_type
            wins     = sum(1 for v in similar if v["pnl_pct"] > 0)
            win_rate = round(wins / len(similar) * 100)
            avg_pnl  = round(sum(v["pnl_pct"] for v in similar) / len(similar), 1)
            best     = max(similar, key=lambda x: x["pnl_pct"])
            worst    = min(similar, key=lambda x: x["pnl_pct"])
            bar   = "🟢" * (win_rate // 20) + "⬜" * (5 - win_rate // 20)
            label = "유사 조건" if len(similar) < len(same_type) else "동일 신호"
            lines.append(
                f"  {bar} {label} {len(similar)}건  승률 {win_rate}%  평균 {avg_pnl:+.1f}%"
                f"\n  최고 {best['pnl_pct']:+.1f}%  최저 {worst['pnl_pct']:+.1f}%"
            )

        if not lines:
            return ""

        return f"🔍 <b>과거 유사 패턴</b>\n" + "\n".join(lines)
    except:
        return ""

# ============================================================
# v37.0 — 📊 중앙 이력 조회 시스템 (signal_log 기반)
# 모든 알림/브리핑에서 과거 유사 상황 참조
# ============================================================
_history_cache: dict = {"data": {}, "ts": 0}

def _load_signal_history() -> dict:
    """signal_log.json 캐시 로드 (5분 TTL)"""
    if time.time() - _history_cache["ts"] < 300 and _history_cache["data"]:
        return _history_cache["data"]
    try:
        with open(SIGNAL_LOG_FILE, "r") as f:
            _history_cache["data"] = json.load(f)
        _history_cache["ts"] = time.time()
    except:
        _history_cache["data"] = {}
    return _history_cache["data"]

def _get_completed_signals(data: dict = None) -> list:
    """완료된 신호만 추출"""
    if data is None:
        data = _load_signal_history()
    return [v for v in data.values()
            if v.get("status") in ("수익", "손실", "본전")
            and v.get("pnl_pct", 0) != 0]

def _format_history_stats(records: list, label: str = "과거 이력") -> str:
    """공통 통계 포맷 (최소 2건 이상)"""
    if len(records) < 2:
        return ""
    total  = len(records)
    wins   = sum(1 for r in records if r["pnl_pct"] > 0)
    avg    = round(sum(r["pnl_pct"] for r in records) / total, 1)
    wr     = round(wins / total * 100)
    emoji  = "🟢" if wr >= 60 else ("🟡" if wr >= 40 else "🔴")
    return f"{emoji} {label}: {total}건 중 {wins}건↑ ({wr}%) 평균{avg:+.1f}%"

def _format_recent_examples(records: list, max_n: int = 3) -> str:
    """최근 사례 포맷"""
    recent = sorted(records, key=lambda x: x.get("detect_date",""), reverse=True)[:max_n]
    parts = []
    for r in recent:
        d = r.get("detect_date", "")
        d_str = f"({d[4:6]}/{d[6:8]})" if d and len(d) == 8 else ""
        parts.append(f"{r.get('name','?')} {r['pnl_pct']:+.1f}%{d_str}")
    return " | ".join(parts) if parts else ""


def get_stock_track_record(code: str, name: str = "") -> str:
    """
    ① 동일 종목의 과거 신호 전적.
    send_alert / DART / 브리핑에서 사용.
    """
    completed = _get_completed_signals()
    same_stock = [r for r in completed if r.get("code") == code]
    if len(same_stock) < 2:
        return ""
    stats = _format_history_stats(same_stock, f"{name or code} 전적")
    recent = _format_recent_examples(same_stock, 2)
    result = f"  {stats}"
    if recent:
        result += f"\n     {recent}"
    return result


def get_dart_keyword_history(code: str, name: str, keywords: list) -> str:
    """
    ② 같은 종목의 유사 공시 후 결과.
    DART run_dart_intraday에서 사용.
    키워드 매칭 or 동일 종목 전적.
    """
    data = _load_signal_history()
    completed = _get_completed_signals(data)
    if not completed:
        return ""

    # 1순위: 같은 종목의 완료 신호
    same_stock = [r for r in completed if r.get("code") == code]

    # 2순위: 같은 종목 없으면 같은 섹터 + DART 연관 신호
    if len(same_stock) < 2:
        # sector_theme에서 같은 테마 찾기
        dart_kw_set = set(kw for kw in keywords if len(kw) >= 2)
        related = []
        for r in completed:
            theme = r.get("sector_theme", "")
            # 공시 키워드가 feature_flags에 반영됐거나 같은 테마면 매칭
            if dart_kw_set and theme:
                for kw in dart_kw_set:
                    if kw in theme or theme in kw:
                        related.append(r)
                        break
        if len(related) >= 2:
            stats = _format_history_stats(related, "유사 공시 섹터")
            return f"━━━━━━━━━━━━━━━\n📊 {stats}"

    if len(same_stock) < 2:
        return ""

    stats = _format_history_stats(same_stock, f"{name} 과거 공시 반응")
    recent = _format_recent_examples(same_stock, 2)
    result = f"━━━━━━━━━━━━━━━\n📊 {stats}"
    if recent:
        result += f"\n     {recent}"
    return result


def get_regime_history(regime: str) -> str:
    """
    ③ 동일 시장 국면에서의 과거 전체 신호 승률.
    오버나이트 위험 알림 / 장전 브리핑에서 사용.
    """
    completed = _get_completed_signals()
    if len(completed) < 5:
        return ""

    same_regime = [r for r in completed
                   if r.get("feature_flags", {}).get("regime") == regime
                   or r.get("regime") == regime]
    if len(same_regime) < 3:
        return ""

    regime_label = {
        "crisis": "위기", "risk_off": "위험회피", "normal": "보통",
        "bull": "강세", "euphoria": "과열"
    }
    label = regime_label.get(regime, regime)
    return _format_history_stats(same_regime, f"{label} 국면 과거")


def get_weekly_comparison(week_records: list) -> str:
    """
    ④ 이번 주 실적 vs 역대 평균 비교.
    주간 리포트에서 사용.
    """
    completed = _get_completed_signals()
    if len(completed) < 10 or not week_records:
        return ""

    all_wr   = round(sum(1 for r in completed if r["pnl_pct"] > 0) / len(completed) * 100)
    all_avg  = round(sum(r["pnl_pct"] for r in completed) / len(completed), 1)

    w_pnls   = [r["pnl_pct"] for r in week_records]
    w_wr     = round(sum(1 for p in w_pnls if p > 0) / len(w_pnls) * 100)
    w_avg    = round(sum(w_pnls) / len(w_pnls), 1)

    wr_diff  = w_wr - all_wr
    avg_diff = round(w_avg - all_avg, 1)

    wr_icon  = "📈" if wr_diff > 0 else ("📉" if wr_diff < 0 else "➡️")
    avg_icon = "📈" if avg_diff > 0 else ("📉" if avg_diff < 0 else "➡️")

    return (f"\n📊 <b>역대 대비</b>  (전체 {len(completed)}건)\n"
            f"  {wr_icon} 승률: 이번주 {w_wr}% vs 역대 {all_wr}%  ({wr_diff:+d}%p)\n"
            f"  {avg_icon} 수익: 이번주 {w_avg:+.1f}% vs 역대 {all_avg:+.1f}%  ({avg_diff:+.1f}%p)")


def get_overnight_history() -> str:
    """
    ⑤ 오버나이트 보유 후 다음날 결과 통계.
    오버나이트 위험 알림에서 사용.
    """
    completed = _get_completed_signals()
    if len(completed) < 5:
        return ""

    # 장 마감 후 감지된 신호 (14시 이후) 또는 추적 2일 이상
    overnight = []
    for r in completed:
        t = r.get("detect_time", "09:00")
        try:
            if t >= "14:00" or (r.get("exit_date","") > r.get("detect_date","")):
                overnight.append(r)
        except: pass

    if len(overnight) < 3:
        return ""

    return _format_history_stats(overnight, "오버나이트 보유")


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
    today = datetime.now().strftime("%Y%m%d")
    cached = _atr_cache.get(code)
    if cached and cached.get("date") == today:
        return cached["atr"]
    items = get_daily_data(code, 20)
    trs   = [i["high"] - i["low"] for i in items[-ATR_PERIOD:] if i["high"] and i["low"]]
    atr   = sum(trs) / len(trs) if trs else 0
    _atr_cache[code] = {"atr": atr, "date": today}
    return atr

def get_atr_regime_mult() -> float:
    """
    현재 시장 국면에 따른 ATR 배수 반환.
    트레일링 스탑 / 진입 허용범위 / 재진입 기준 등에 공통 사용.
      bull  → 0.8  (타이트하게 — 수익 빨리 확보)
      normal→ 1.2
      bear  → 1.8  (여유있게 — 노이즈에 안 털림)
      crash → 2.5
    NXT 단독 시간대면 추가 × 1.3 (변동성 높음)
    """
    regime_info = get_market_regime()
    regime      = regime_info.get("mode", "normal")
    nxt_only    = regime_info.get("nxt_only", False)
    base = {"bull": 0.8, "normal": 1.2, "bear": 1.8, "crash": 2.5}.get(regime, 1.2)
    return round(base * (1.3 if nxt_only else 1.0), 2)

def calc_atr_pct(code: str, price: int, fallback_pct: float = 2.0) -> float:
    """
    종목 ATR을 현재가 대비 %로 반환.
    ATR 조회 실패 시 fallback_pct 사용.
    """
    try:
        atr = get_atr(code)
        if atr > 0 and price > 0:
            return round(atr / price * 100, 2)
    except: pass
    return fallback_pct

def calc_trailing_stop(code: str, high_price: int) -> int:
    """
    트레일링 스탑 가격 계산.
    고점 - ATR × 국면배수 (최소 -1.5%, 최대 -8%)
    """
    try:
        atr  = get_atr(code)
        mult = get_atr_regime_mult()
        if atr > 0:
            trail_gap = int(atr * mult)
            trail_pct = trail_gap / high_price * 100 if high_price else 3.0
            # 최소 1.5%, 최대 8% 범위 제한
            trail_pct = max(1.5, min(trail_pct, 8.0))
            trail_gap = int(high_price * trail_pct / 100)
            return int((high_price - trail_gap) / 10) * 10
    except: pass
    # fallback: 고점 × 0.97
    return int(high_price * 0.97 / 10) * 10

def calc_entry_tolerance(code: str, price: int) -> float:
    """
    진입가 허용범위 (±%) 계산.
    ATR 기반으로 종목마다 다르게 적용.
    최소 1.0%, 최대 4.0%
    """
    atr_pct = calc_atr_pct(code, price, fallback_pct=2.0)
    mult    = get_atr_regime_mult()
    tol     = round(atr_pct * mult * 0.5, 1)
    return max(1.0, min(tol, 4.0))

def calc_reentry_bounce(code: str, price: int) -> float:
    """
    손절 후 재진입 반등 기준 (%) 계산.
    ATR × 0.5 배수 (최소 1.5%, 최대 6.0%)
    """
    atr_pct = calc_atr_pct(code, price, fallback_pct=3.0)
    mult    = get_atr_regime_mult()
    bounce  = round(atr_pct * mult * 0.5, 1)
    return max(1.5, min(bounce, 6.0))

def calc_surge_escape_pct(code: str, price: int) -> float:
    """
    진입가 상승이탈 판단 기준 (%) — 진입가보다 이 % 이상 오르면 포기.
    ATR × 3배 (최소 5%, 최대 15%)
    """
    atr_pct = calc_atr_pct(code, price, fallback_pct=3.0)
    mult    = get_atr_regime_mult()
    escape  = round(atr_pct * mult * 3.0, 1)
    return max(5.0, min(escape, 15.0))

def calc_partial_exit_min_pct(code: str, price: int) -> float:
    """
    분할 청산 트리거 최소 수익률 (%) — 이 이상 수익일 때만 분할 청산 알림.
    ATR × 1배 (최소 1.5%, 최대 5.0%)
    """
    atr_pct = calc_atr_pct(code, price, fallback_pct=2.0)
    return max(1.5, min(round(atr_pct, 1), 5.0))

def calc_trailing_stop_price(code: str, price: int) -> int:
    """고점 기준 트레일링 스탑 — calc_trailing_stop의 별칭"""
    return calc_trailing_stop(code, price)

def calc_stop_target(code: str, entry: int) -> tuple:
    atr = get_atr(code)
    if atr > 0:
        stop   = int((entry - atr * ATR_STOP_MULT)  / 10) * 10
        target = int((entry + atr * ATR_TARGET_MULT) / 10) * 10
        return stop, target, round((entry-stop)/entry*100,1), round((target-entry)/entry*100,1), True
    # ATR 실패 시 국면 배수 적용 fallback
    _rm   = get_atr_regime_mult()
    _stop_pct   = max(0.05, 0.07 * _rm)
    _target_pct = max(0.08, 0.15 / _rm)
    stop   = int(entry * (1 - _stop_pct)   / 10) * 10
    target = int(entry * (1 + _target_pct) / 10) * 10
    return stop, target, round(_stop_pct*100,1), round(_target_pct*100,1), False

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


def _prune_cache(cache: dict, max_size: int = 200, ttl: int = 3600):
    """v37.0: 캐시 크기 제한 + TTL 만료 항목 제거 (메모리 누수 방지)"""
    if len(cache) <= max_size:
        return
    now = time.time()
    expired = [k for k, v in cache.items()
               if isinstance(v, dict) and now - v.get("ts", 0) > ttl]
    for k in expired:
        del cache[k]
    # 여전히 초과면 가장 오래된 항목부터 제거
    if len(cache) > max_size:
        sorted_keys = sorted(
            [k for k, v in cache.items() if isinstance(v, dict) and "ts" in v],
            key=lambda k: cache[k].get("ts", 0)
        )
        for k in sorted_keys[:len(cache) - max_size]:
            del cache[k]

def _prune_all_caches():
    """장중 주기적으로 호출 — 캐시 크기 제한"""
    for c in (_daily_cache, _force_cache, _deep_news_cache, _nxt_cache,
              _sector_cache, _avg_volume_cache, _short_cache, _foreign_cache):
        _prune_cache(c, max_size=200, ttl=3600)

# v37.0: _nxt_unavailable 주 1회 초기화 플래그
_nxt_unavailable_reset_week: str = ""

def _clear_all_cache():
    global _sector_cache, _avg_volume_cache, _prev_upper_cache, _daily_cache
    global _nxt_cache, _nxt_unavailable, _early_cache, _news_reverse_cache
    global _kospi_cache, _sector_monitor, _pending_info_alerts
    global _nxt_unavailable_reset_week
    _sector_cache.clear();       _avg_volume_cache.clear()
    _prev_upper_cache.clear();   _daily_cache.clear();   _atr_cache.clear()
    _us_cache.clear();   _short_cache.clear();   _foreign_cache.clear()
    _vp_cache.clear();   _pre_dart_cache.clear();   _theme_rotation_cache.clear()
    _geo_cache.clear()
    _deep_news_cache.clear()
    _force_cache.clear()
    _nxt_cache.clear()
    # v37.0: _nxt_unavailable 주 1회만 초기화 (NXT 상장 여부는 거의 안 바뀜)
    this_week = datetime.now().strftime("%Y-W%W")
    if _nxt_unavailable_reset_week != this_week:
        _nxt_unavailable.clear()
        _nxt_unavailable_reset_week = this_week
        print("  🔵 NXT 비상장 캐시 주간 초기화")
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
            _w_nxt = _dynamic.get("feat_w_nxt", 1.0)
            score += int(nxt_delta * _w_nxt)
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


# ============================================================
# 🔭 Next-open Watchlist (장 종료 후 후보군 대체)
#   - 장이 닫혀 있을 때는 '급등 상위' 후보군 산출을 스킵하고
#     익개장 전 확인용 워치리스트를 저장/요약 전송한다.
# ============================================================
WATCHLIST_NEXT_OPEN_FILE = os.path.join(DATA_DIR, "watchlist_next_open.json")
OVERNIGHT_RISK_LAST_FILE   = os.path.join(DATA_DIR, "overnight_risk_last.json")
_UNIVERSE_RANK_TTL_SEC = int(os.getenv("UNIVERSE_RANK_TTL_SEC", "45") or "45")  # reuse if set

def _read_json_safe(path: str, default):
    try:
        if not os.path.isfile(path):
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def build_next_open_watchlist(max_codes: int = 30) -> dict:
    """장 종료 후: 내일 감시할 워치리스트를 생성해서 파일로 저장."""
    # 우선순위: carry_stocks → 최근 signal_log 종목 → (있으면) universe.json
    carry = _read_json_safe(os.path.join(DATA_DIR, "carry_stocks.json"), {})
    siglog = _read_json_safe(os.path.join(DATA_DIR, "signal_log.json"), [])
    universe = _read_json_safe(os.path.join(DATA_DIR, "universe.json"), {})

    codes = []
    seen = set()

    # carry_stocks 구조가 dict/list 어떤 형태든 대응
    if isinstance(carry, dict):
        for k in list(carry.keys()):
            c = normalize_stock_code(k)
            if c and c not in seen:
                seen.add(c); codes.append(c)
    elif isinstance(carry, list):
        for item in carry:
            c = normalize_stock_code(item.get("code") if isinstance(item, dict) else item)
            if c and c not in seen:
                seen.add(c); codes.append(c)

    # 최근 신호/추적 종목
    if isinstance(siglog, list):
        # 최근 것부터
        for rec in reversed(siglog[-500:]):  # 너무 오래는 보지 않음
            if not isinstance(rec, dict):
                continue
            c = normalize_stock_code(rec.get("code") or rec.get("stock_code") or rec.get("종목코드"))
            if c and c not in seen:
                seen.add(c); codes.append(c)
            if len(codes) >= max_codes:
                break

    # universe.json (사용자 지정 유니버스가 있으면 보충)
    if isinstance(universe, dict):
        ulist = universe.get("codes") or universe.get("universe") or universe.get("tickers") or []
        if isinstance(ulist, list):
            for u in ulist:
                c = normalize_stock_code(u)
                if c and c not in seen:
                    seen.add(c); codes.append(c)
                if len(codes) >= max_codes:
                    break

    payload = {
        "ts": time.time(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "max_codes": max_codes,
        "codes": codes[:max_codes],
    }
    try:
        _ensure_dir(DATA_DIR)
        _write_json_atomic(WATCHLIST_NEXT_OPEN_FILE, payload, indent=2)
    except Exception as e:
        print(f"⚠️ 워치리스트 저장 실패: {e}")
    return payload

def _scan_recent_dart_materials(days_back: int = 1, max_items: int = 6) -> list:
    """비장중/장전용: 최근(오늘+어제) DART 공시 중 '재료(강/매우강)'만 추려서 반환.
    반환: [{code,name,title,grade}, ...]
    """
    if not DART_API_KEY:
        return []
    out = []
    try:
        today = datetime.now().strftime("%Y%m%d")
        dates = [today]
        if days_back >= 1:
            yday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
            dates.append(yday)

        # 키워드 우선순위
        strong = DART_KEYWORDS.get("매우강함", []) + DART_KEYWORDS.get("강함", [])
        strong = [k for k in strong if k]

        seen = set()
        for d in dates:
            dart_list = _fetch_dart_list(d) if DART_API_KEY else []
            for it in (dart_list or []):
                title = (it.get("report_nm") or it.get("title") or "").strip()
                code  = normalize_stock_code(it.get("stock_code") or it.get("stock_code") or it.get("stock_code"))
                if not title or not code:
                    continue
                # 리스크 공시는 제외 (손익 방어 쪽에서 따로 처리)
                if any(rk in title for rk in DART_RISK_KEYWORDS):
                    continue
                hit_kw = next((k for k in strong if k in title), None)
                if not hit_kw:
                    continue
                key = (code, title)
                if key in seen:
                    continue
                seen.add(key)
                name = _lookup_name_by_code(code)
                grade = "매우강함" if any(k in title for k in DART_KEYWORDS.get("매우강함", [])) else "강함"
                out.append({"code": code, "name": name, "title": title, "grade": grade})
                if len(out) >= max_items:
                    return out
    except Exception as e:
        _log_error("_scan_recent_dart_materials", e)
    return out

def _build_preopen_issue_section(max_lines: int = 12) -> str:
    """장전(07:30) 워치리스트에 붙일 '이슈 기반 섹터/종목' 섹션 생성."""
    lines = []
    try:
        # 1) 지정학/거시 이슈(섹터 방향)
        geo = _geo_event_state or {}
        if geo.get("active") and time.time() - float(geo.get("ts", 0) or 0) < 3600 * 12:
            sec_dirs = geo.get("sector_directions", []) or []
            if not sec_dirs and geo.get("sectors"):
                # sector_directions가 없으면 fallback 생성
                sec_dirs = _build_fallback_sector_directions(geo.get("kws", []) or [], geo.get("sectors") or [])
            # 상승 섹터만 상위 3개
            ups = [sd for sd in sec_dirs if str(sd.get("direction","")) in ("상승","up","positive","bull")]
            if ups:
                lines.append("🌍 이슈(지정학) 기반 유리 섹터")
                for sd in ups[:3]:
                    sec = sd.get("sector","")
                    reason = (sd.get("reason","") or "").strip()
                    stocks = _get_geo_sector_stocks(sec, max_n=3) if sec else []
                    stk = " / ".join([n for c,n in stocks]) if stocks else ""
                    if stk:
                        lines.append(f" • {sec}: {stk}")
                    else:
                        lines.append(f" • {sec}")
                    if reason:
                        lines.append(f"   - {reason}")
        # 2) DART 강재료(전일~금일)
        darts = _scan_recent_dart_materials(days_back=1, max_items=5)
        if darts:
            lines.append("📢 공시(DART) 강재료 후보")
            for d in darts[:5]:
                nm = d.get("name") or d.get("code")
                title = d.get("title","")
                grade = d.get("grade","")
                lines.append(f" • {nm}: {grade} — {title}")
    except Exception:
        pass

    # 길이 제한
    lines = [ln for ln in lines if ln.strip()]
    if not lines:
        return ""
    if len(lines) > max_lines:
        lines = lines[:max_lines] + ["…(생략)"]
    return "\n".join(lines)

def send_preopen_watchlist():
    """익개장 전(07:30) 워치리스트 요약 전송 + 비장중 이슈(지정학/DART) 반영"""
    try:
        data = _read_json_safe(WATCHLIST_NEXT_OPEN_FILE, {})
        codes = data.get("codes") if isinstance(data, dict) else None
        if not codes:
            return
        # 너무 길면 상위 15개만 표시
        show = codes[:15]
        msg = "⏰ 익개장 전 워치리스트\n" + " / ".join(show)

        # Include overnight risk recap (saved during night / last run)
        try:
            _ov = _read_json_safe(OVERNIGHT_RISK_LAST_FILE, {})
            _ov_msg = _ov.get("msg") if isinstance(_ov, dict) else None
            if _ov_msg:
                # Keep it short: top 6 lines max
                _lines = [ln for ln in str(_ov_msg).splitlines() if ln.strip()]
                if len(_lines) > 6:
                    _lines = _lines[:6] + ["…(생략)"]
                msg += "\n\n" + "\n".join(_lines)
        except Exception:
            pass

        # NEW: off-hours issues (geo sectors + DART strong materials)
        try:
            issue_sec = _build_preopen_issue_section()
            if issue_sec:
                msg += "\n\n" + issue_sec
        except Exception:
            pass

        send_by_level(msg, level=ALERT_LEVEL_NORMAL)
    except Exception as e:
        print(f"⚠️ send_preopen_watchlist 오류: {e}")

def _resolve_stock_name(code: str, name_hint: str = "", cur: dict | None = None) -> str:
    """종목명이 비어 있을 때 현재가 응답 / signal_log / 코드 순으로 복구."""
    try:
        nm = str(name_hint or "").strip()
        if nm:
            return nm

        if isinstance(cur, dict):
            nm = str(cur.get("name", "") or "").strip()
            if nm:
                return nm

        try:
            info = get_stock_price(code)
            nm = str((info or {}).get("name", "") or "").strip()
            if nm:
                return nm
        except Exception:
            pass

        try:
            with open(SIGNAL_LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
            for _k, rec in sorted(data.items(), reverse=True):
                if not isinstance(rec, dict):
                    continue
                if str(rec.get("code", "")) == str(code):
                    nm = str(rec.get("name", "") or "").strip()
                    if nm:
                        return nm
        except Exception:
            pass
    except Exception:
        pass
    return str(code or "").strip()


def refresh_dynamic_candidates():
    """
    거래량 상위 50종목을 자동으로 후보군에 편입
    → THEME_MAP에 없는 종목(아주IB투자, 국전약품 등)도 포착 가능
    매일 장 시작 시 + 1시간마다 갱신
    """
    if not is_any_market_open():
        build_next_open_watchlist(max_codes=30)
        print("  💤 비장중: 동적 후보군 갱신 스킵 → 익개장 워치리스트 저장")
        return

    try:
        # 거래량 급증 상위 종목
        vol_stocks = get_volume_surge_stocks()
        # 상한가 근접 상위 종목
        upper_stocks = get_upper_limit_stocks()
        candidates = {}
        excluded_cnt = 0
        for s in vol_stocks + upper_stocks:
            code = s.get("code")
            if not code:
                continue
            name = _resolve_stock_name(code, s.get("name", ""))
            if not is_trade_candidate_name(name):
                excluded_cnt += 1
                continue
            candidates[code] = name
        for code, name in candidates.items():
            if code not in _dynamic_candidates:
                _dynamic_candidates[code] = {"name": name, "desc": "자동편입", "added_ts": time.time()}
            else:
                _dynamic_candidates[code]["name"] = name
        print(f"  🔄 동적 후보군: {len(_dynamic_candidates)}개 종목 (제외 {excluded_cnt}개)")
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
                resolved_name = _resolve_stock_name(c, n)
                if is_trade_candidate_name(resolved_name):
                    seen.add(c); result.append((c, resolved_name, theme_info["desc"]))
    # 동적 후보군 추가 (THEME_MAP에 없는 종목만)
    for code, info in _dynamic_candidates.items():
        if code not in seen:
            resolved_name = _resolve_stock_name(code, info.get("name", ""))
            if is_trade_candidate_name(resolved_name):
                seen.add(code); result.append((code, resolved_name, info["desc"]))
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
        "code": code, "name": _resolve_stock_name(code, name, cur), "price": today_price, "change_rate": today_chg,
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
        name = _resolve_stock_name(code, name)
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
                _w_sec = _dynamic.get("feat_w_sector", 1.0)
                result["score"] += int(sector_info.get("bonus", 0) * _w_sec)
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
        if is_scoring_only_instrument(s.get("code", ""), s.get("name", "")):
            print(f"  ⏭ 점수전용 종목 제외: {s.get('name', s.get('code',''))}")
            continue
        send_mid_pullback_alert(s)
        save_signal_log(s)
        register_entry_watch(s)                     # ★ 진입가 감시 등록
        start_sector_monitor(s["code"], s["name"])  # ★ 섹터 지속 모니터링
        _mid_pullback_alert_history[s["code"]] = time.time()
        tag = "[장중돌파]" if s.get("is_intraday") else "[일봉]"
        print(f"  ✓ 중기 눌림목 {tag}: {s['name']} [{s['grade']}등급] {s['score']}점")

def send_mid_pullback_alert(s: dict):
    stock_name  = _resolve_stock_name(s.get("code", ""), s.get("name", ""))
    s["name"] = stock_name
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
            sector_block += f"  ➖ {_resolve_stock_name(r['code'], r.get('name',''))} {r['change_rate']:+.1f}%\n"
    elif theme:
        sector_block = f"\n━━━━━━━━━━━━━━━\n🏭 섹터 [{theme}]: 동업종 조회 중\n"
    else:
        sector_block = f"\n━━━━━━━━━━━━━━━\n🏭 섹터: 조회 실패\n"

    intraday_tag = "  ⚡️ 장중 돌파" if s.get("is_intraday") else ""
    send_with_chart_buttons(
        f"{grade_emoji} <b>[중기 눌림목 진입 신호]</b>  {grade_text}{intraday_tag}\n"
        f"🕐 {now_str}  |  테마: {s.get('theme_desc','')}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🟣 <b>{stock_name}</b>  <code>{s['code']}</code>\n"
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
        s["code"], stock_name
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
    mktcap_raw = int(o.get("hts_avls", 0) or 0)  # 시가총액 (억원)
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
        "mktcap":    mktcap_raw,       # 억원 단위
        "cap_size":  ("large" if mktcap_raw >= 10000   # 1조 이상
                      else "mid" if mktcap_raw >= 1000  # 1000억 이상
                      else "small"),
    }



# ============================================================
# 후보군 생성 fallback (랭킹 API 404 대비)
# ============================================================
UNIVERSE_FILE = os.path.join(DATA_DIR, "universe.json")
_UNIVERSE_CACHE = {"ts": 0.0, "codes": []}
_UNIVERSE_RANK_CACHE = {"ts": 0.0, "items": []}

UNIVERSE_MAX = int(os.getenv("UNIVERSE_MAX", "200") or "200")
UNIVERSE_CACHE_TTL_SEC = int(os.getenv("UNIVERSE_CACHE_TTL_SEC", "3600") or "3600")
UNIVERSE_RANK_TTL_SEC = int(os.getenv("UNIVERSE_RANK_TTL_SEC", "45") or "45")

UNIVERSE_MIN_PRICE = int(os.getenv("UNIVERSE_MIN_PRICE", "1000") or "1000")
UNIVERSE_MIN_VOL = int(os.getenv("UNIVERSE_MIN_VOL", "100000") or "100000")
UNIVERSE_MIN_RSFL = float(os.getenv("UNIVERSE_MIN_RSFL", "5") or "5")

def _extract_codes_recursive(obj, out: set, limit: int = 5000):
    if len(out) >= limit:
        return
    if isinstance(obj, str):
        s = obj.strip()
        if len(s) == 6 and s.isdigit():
            out.add(s)
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            _extract_codes_recursive(k, out, limit)
            _extract_codes_recursive(v, out, limit)
        return
    if isinstance(obj, (list, tuple, set)):
        for v in obj:
            _extract_codes_recursive(v, out, limit)
        return

def _load_universe_codes() -> list:
    now = time.time()
    if now - _UNIVERSE_CACHE["ts"] < UNIVERSE_CACHE_TTL_SEC and _UNIVERSE_CACHE["codes"]:
        return _UNIVERSE_CACHE["codes"]

    codes = []

    # user-provided universe.json
    try:
        if os.path.exists(UNIVERSE_FILE):
            with open(UNIVERSE_FILE, "r", encoding="utf-8") as f:
                j = json.load(f)
            arr = j.get("codes") if isinstance(j, dict) else j
            for c in (arr or []):
                s = str(c).strip()
                if len(s) == 6 and s.isdigit():
                    codes.append(s)
    except Exception as e:
        print(f"⚠️ universe.json 로드 실패: {e}")

    # carry_stocks.json
    try:
        carry_path = os.path.join(DATA_DIR, "carry_stocks.json")
        if os.path.exists(carry_path):
            with open(carry_path, "r", encoding="utf-8") as f:
                j = json.load(f)
            found = set()
            _extract_codes_recursive(j, found, limit=2000)
            codes.extend(sorted(found))
    except:
        pass

    # signal_log.json
    try:
        if os.path.exists(SIGNAL_LOG_FILE):
            with open(SIGNAL_LOG_FILE, "r", encoding="utf-8") as f:
                j = json.load(f)
            found = set()
            _extract_codes_recursive(j, found, limit=5000)
            codes.extend(sorted(found))
    except:
        pass

    seen = set()
    uniq = []
    for c in codes:
        if c not in seen:
            seen.add(c)
            uniq.append(c)

    _UNIVERSE_CACHE["ts"] = now
    _UNIVERSE_CACHE["codes"] = uniq[: max(UNIVERSE_MAX, 50)]
    return _UNIVERSE_CACHE["codes"]

def update_universe_from_performance(days: int = 30, max_codes: int = 300) -> None:
    """
    최근 성과 기반으로 universe.json을 자동 갱신.
    - 목적: '최적 조건 만들기'에 유리한 종목을 유니버스에 더 많이 포함
    - 안전장치: 데이터가 부족하면 갱신하지 않음
    """
    try:
        # signal_log 로드
        log = {}
        try:
            with open(SIGNAL_LOG_FILE, "r", encoding="utf-8") as f:
                log = json.load(f) or {}
        except Exception:
            return

        if not isinstance(log, dict) or not log:
            return

        cutoff = datetime.now() - timedelta(days=days)
        stats = {}  # code -> {"n":..,"win":..,"avg":..}
        for k, v in log.items():
            if not isinstance(v, dict):
                continue
            code = v.get("code")
            if not code:
                continue
            # 시간 추정: detected_at 있으면 사용, 없으면 log_key prefix로 날짜 파싱
            dt = None
            if isinstance(v.get("detected_at"), str):
                try:
                    dt = datetime.fromisoformat(v["detected_at"])
                except Exception:
                    dt = None
            if dt is None and isinstance(v.get("log_key"), str):
                m = re.search(r"(\d{8})(\d{4})", v["log_key"])
                if m:
                    try:
                        dt = datetime.strptime(m.group(1)+m.group(2), "%Y%m%d%H%M")
                    except Exception:
                        dt = None
            if dt is None:
                continue
            if dt < cutoff:
                continue

            outcome = v.get("outcome")  # "win"/"loss"/"flat" 등
            ret = v.get("ret_pct")  # 있으면
            st = stats.setdefault(code, {"n": 0, "win": 0, "sum": 0.0})
            st["n"] += 1
            if outcome == "win":
                st["win"] += 1
            if isinstance(ret, (int, float)):
                st["sum"] += float(ret)

        # 최소 샘플 확보
        if len(stats) < 30:
            return

        scored = []
        for code, st in stats.items():
            n = st["n"]
            winrate = st["win"] / n if n else 0.0
            avg = st["sum"] / n if n else 0.0
            # 간단 점수: winrate 중심 + 수익 보너스
            score = winrate * 100 + avg
            scored.append((score, winrate, avg, n, code))

        scored.sort(reverse=True)
        top_codes = [c for *_rest, c in scored[:max_codes]]

        # carry_stocks 우선 유지
        carry_codes = []
        try:
            if os.path.exists(CARRY_STOCKS_FILE):
                with open(CARRY_STOCKS_FILE, "r", encoding="utf-8") as f:
                    j = json.load(f) or {}
                carry_codes = list((j.get("codes") or j.get("watch") or j.get("carry") or []))
        except Exception:
            carry_codes = []
        merged = []
        for c in (carry_codes + top_codes):
            if c and c not in merged:
                merged.append(c)

        # 너무 적으면 갱신하지 않음
        if len(merged) < 50:
            return

        _atomic_write_json(UNIVERSE_FILE, {"codes": merged[:max_codes]})
        # cache reset
        _UNIVERSE_CACHE["ts"] = 0.0
        print(f"🧠 universe.json 자동 갱신: {len(merged[:max_codes])}종목 (최근 {days}일 성과 기반)")
    except Exception as e:
        _log_error("update_universe_from_performance", e)

def _rank_from_universe() -> list:
    now = time.time()
    if now - _UNIVERSE_RANK_CACHE["ts"] < UNIVERSE_RANK_TTL_SEC and _UNIVERSE_RANK_CACHE["items"]:
        return _UNIVERSE_RANK_CACHE["items"]

    codes = _load_universe_codes()[:UNIVERSE_MAX]
    items = []
    for code in codes:
        info = get_stock_price(code)
        if not info:
            continue
        if info.get("price", 0) < UNIVERSE_MIN_PRICE:
            continue
        if info.get("today_vol", 0) < UNIVERSE_MIN_VOL:
            continue
        if float(info.get("change_rate", 0) or 0) < UNIVERSE_MIN_RSFL:
            continue

        items.append({
            "code": info.get("code",""),
            "name": info.get("name",""),
            "price": int(info.get("price",0) or 0),
            "change_rate": float(info.get("change_rate",0) or 0),
            "volume_ratio": float(info.get("volume_ratio",0) or 0),
            "market": "KRX",
        })

    items.sort(key=lambda x: (x.get("change_rate",0), x.get("volume_ratio",0), x.get("price",0)), reverse=True)
    items = items[:30]

    # [v37.10-all5] 다양성 제한(테마/섹터 쏠림 완화)
    max_per_theme = int(os.getenv("UNIVERSE_MAX_PER_THEME", "6") or "6")
    if max_per_theme > 0:
        bucket = {}
        diversified = []
        for it in items:
            key = it.get("theme") or it.get("sector") or ""
            if not key:
                diversified.append(it)
                continue
            cnt = bucket.get(key, 0)
            if cnt >= max_per_theme:
                continue
            bucket[key] = cnt + 1
            diversified.append(it)
        items = diversified[:30]

    _UNIVERSE_RANK_CACHE["ts"] = now
    _UNIVERSE_RANK_CACHE["items"] = items
    return items


# --- Rank API disable guard (avoid repeated 404 spam) ---
_RANK_API_DISABLE_FILE = os.path.join(DATA_DIR, "rank_api_disable.json")
_rank_api_disable_notified = False

# Daily trade (history) endpoint availability (some accounts/envs may not support certain paths)
_DAILY_TRADE_DISABLE_FILE = os.path.join(DATA_DIR, "daily_trade_api_disable.json")
_daily_trade_disable_notified = False

def _daily_trade_api_disabled_today() -> bool:
    try:
        if not os.path.exists(_DAILY_TRADE_DISABLE_FILE):
            return False
        with open(_DAILY_TRADE_DISABLE_FILE, "r", encoding="utf-8") as f:
            obj = json.load(f)
        disabled_date = str(obj.get("disabled_date", ""))
        return disabled_date == _now_kst().date().isoformat()
    except Exception:
        return False

def _disable_daily_trade_api_for_today(reason: str) -> None:
    try:
        os.makedirs(os.path.dirname(_DAILY_TRADE_DISABLE_FILE), exist_ok=True)
        with open(_DAILY_TRADE_DISABLE_FILE, "w", encoding="utf-8") as f:
            json.dump({"disabled_date": _now_kst().date().isoformat(), "reason": str(reason)}, f, ensure_ascii=False)
    except Exception:
        pass


def _rank_api_disabled_today() -> bool:
    try:
        if not os.path.exists(_RANK_API_DISABLE_FILE):
            return False
        with open(_RANK_API_DISABLE_FILE, "r", encoding="utf-8") as f:
            obj = json.load(f)
        disabled_date = str(obj.get("disabled_date", ""))
        return disabled_date == _now_kst().date().isoformat()
    except Exception:
        return False

def _disable_rank_api_for_today(reason: str) -> None:
    try:
        os.makedirs(os.path.dirname(_RANK_API_DISABLE_FILE), exist_ok=True)
        with open(_RANK_API_DISABLE_FILE, "w", encoding="utf-8") as f:
            json.dump({"disabled_date": _now_kst().date().isoformat(), "reason": reason}, f, ensure_ascii=False)
    except Exception:
        pass

def _rank_api_fallback(reason: str) -> list:
    """Fallback to universe ranking and (optionally) disable rank API for the rest of the day."""
    global _rank_api_disable_notified
    # Mark disabled for today unless this is already the disabled_today path
    if reason != "disabled_today":
        _disable_rank_api_for_today(str(reason))
    if not _rank_api_disable_notified:
        print(f"⚠️ [KIS] chgrate-pcls-100 비활성(오늘) → 유니버스 후보군 사용 ({reason})")
        _rank_api_disable_notified = True
    return _rank_from_universe()


def get_upper_limit_stocks() -> list:
    if _rank_api_disabled_today():
        return _rank_api_fallback('disabled_today')

    url = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/chgrate-pcls-100"
    params = {
        "FID_COND_MRKT_DIV_CODE":"J","FID_COND_SCR_DIV_CODE":"20170","FID_INPUT_ISCD":"0000",
        "FID_RANK_SORT_CLS_CODE":"0","FID_INPUT_CNT_1":"30","FID_PRC_CLS_CODE":"0",
        "FID_INPUT_PRICE_1":"1000","FID_INPUT_PRICE_2":"","FID_VOL_CNT":"100000",
        "FID_TRGT_CLS_CODE":"0","FID_TRGT_EXLS_CLS_CODE":"0","FID_DIV_CLS_CODE":"0",
        "FID_RSFL_RATE1":"5","FID_RSFL_RATE2":"",
    }

    data, status, ct, body = _safe_get_meta(url, "FHPST01700000", params)

    if status == 404:
        _disable_rank_api_for_today("404")
        return _rank_api_fallback("404")

    items = [{
        "code": i.get("mksc_shrn_iscd",""), "name": i.get("hts_kor_isnm",""),
        "price": int(i.get("stck_prpr",0)), "change_rate": float(i.get("prdy_ctrt",0)),
        "volume_ratio": float(i.get("vol_inrt",0) or 0), "market":"KRX"
    } for i in (data.get("output", []) if isinstance(data, dict) else [])]

    if not items and os.getenv("ENABLE_UNIVERSE_FALLBACK", "1") == "1":
        print(f"⚠️ [KIS] 랭킹 응답 비어있음(status={status}, ct={ct}) → 유니버스 후보군으로 대체")
        return _rank_from_universe()

    return items

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
        "foreign_net":     safe_int(output[0].get('frgn_ntby_qty', 0)),
        "institution_net": safe_int(output[0].get('orgn_ntby_qty', 0)),
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
    return {
        "foreign_net":     safe_int(output[0].get('frgn_ntby_qty', 0)),
        "institution_net": safe_int(output[0].get('orgn_ntby_qty', 0)),
        "retail_net":      safe_int(output[0].get('prsn_ntby_qty', 0)),  # 개인 순매수
    }

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
            if _rank_api_disabled_today():
                # 오늘 랭킹 API 비활성화 상태이면 3단계 시도하지 않음
                return stocks
            try:
                url3 = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/chgrate-pcls-100"
                data3, status3, ct3, body3 = _safe_get_meta(
                    url3,
                    "FHPST01700000",
                    {"FID_COND_MRKT_DIV_CODE":"J","FID_COND_SCR_DIV_CODE":"20170",
                     "FID_INPUT_ISCD":"0000","FID_RANK_SORT_CLS_CODE":"0",
                     "FID_INPUT_CNT_1":"50","FID_PRC_CLS_CODE":"0",
                     "FID_INPUT_PRICE_1":"500","FID_INPUT_PRICE_2":"",
                     "FID_VOL_CNT":"1000","FID_TRGT_CLS_CODE":"0",
                     "FID_TRGT_EXLS_CLS_CODE":"0","FID_DIV_CLS_CODE":"0",
                     "FID_RSFL_RATE1":"-30","FID_RSFL_RATE2":"30"}
                )
                if status3 == 404:
                    _disable_rank_api_for_today("404")
                    return stocks
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
        _write_json_atomic(NEWS_COOCCUR_FILE, _news_cooccur, indent=2)
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
    # [v37.10-all5] 지정학/뉴스 섹터 바이어스(점수 보정)
    geo_bias = 0
    try:
        geo_bias = int(globals().get('GEO_SECTOR_BIAS', {}).get(theme_name, 0) or 0)
    except Exception:
        geo_bias = 0
    if not peers:
        return {"bonus":0,"theme":theme_name,"summary":"","rising":[],"flat":[],"detail":[],"sources":{}}
    results = []
    for peer_code, peer_name in peers[:8]:
        try:
            cur = get_stock_price(peer_code)
            if not cur: continue
            safe_peer_name = _resolve_stock_name(peer_code, peer_name, cur)
            cr, vr = cur.get("change_rate",0), cur.get("volume_ratio",0)
            src, rsn = peers_all.get(peer_code, (safe_peer_name, "업종코드", ""))[1:]
            results.append({"code":peer_code,"name":safe_peer_name,"price":cur.get("price",0),"change_rate":cr,"volume_ratio":vr,
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

    bonus = int(bonus + geo_bias)
    return {"bonus":bonus,"theme":theme_name,"summary":summary,
            "rising":rising,"flat":flat,"detail":results,"sources":sources}

# ============================================================
# 💾 저장·복원
# ============================================================
# ============================================================
# 📋 신호 로그 저장 (모든 신호 유형 공통)
# ============================================================
SIGNAL_LOG_FILE = os.path.join(DATA_DIR, "signal_log.json")   # 모든 신호 추적 (신규)

# ============================================================
# 🎯 최적조건 만들기용 데이터/튜닝 설정
#   - signal_log는 최대 N건만 유지 (너무 커지면 튜닝 품질/속도 저하)
#   - params_snapshot(신호 당시 파라미터) + feature_snapshot(상황/지표) 저장
#   - params_snapshot 성과 비교로 점진적(auto) 튜닝
# ============================================================
SIGNAL_LOG_MAX_RECORDS = int(os.getenv("SIGNAL_LOG_MAX_RECORDS", "50000") or "50000")
STRICT_ENTRY_CLEANUP_MARKER = os.path.join(DATA_DIR, "strict_entry_cleanup_v37_25.done")

def _strict_cleanup_legacy_entry_hits() -> None:
    """엄격 진입가 도달 체계 전환용 1회성 마이그레이션.
    과거 허용오차 기반으로 기록됐을 수 있는 비실진입 entry_hit를 초기화한다.
    새 strict hit가 재시작 때 지워지지 않도록 marker 파일로 1회만 수행한다.
    """
    try:
        if os.path.exists(STRICT_ENTRY_CLEANUP_MARKER):
            return
        if not os.path.exists(SIGNAL_LOG_FILE):
            with open(STRICT_ENTRY_CLEANUP_MARKER, "w", encoding="utf-8") as f:
                f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            return

        with open(SIGNAL_LOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
        if not isinstance(data, dict):
            return

        changed = 0
        now_s = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        backup_path = os.path.join(DATA_DIR, f"signal_log.before_strict_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

        for _k, rec in data.items():
            if not isinstance(rec, dict):
                continue
            if rec.get("actual_entry") is True:
                continue
            if rec.get("entry_hit") is True:
                rec["legacy_entry_hit"] = True
                rec["legacy_entry_hit_time"] = rec.get("entry_hit_time")
                rec["legacy_entry_hit_reset_at"] = now_s
                rec["legacy_entry_hit_reset_reason"] = "strict_cleanup_non_actual_entry"
                rec["entry_hit"] = False
                rec["entry_hit_time"] = None
                changed += 1

        if changed > 0:
            with open(SIGNAL_LOG_FILE, "r", encoding="utf-8") as f:
                original = json.load(f) or {}
            _write_json_atomic(backup_path, original, indent=2)
            _write_json_atomic(SIGNAL_LOG_FILE, data, indent=2)
            print(f"🧹 strict cleanup: 과거 비실진입 entry_hit {changed}건 초기화, 백업={os.path.basename(backup_path)}")
        else:
            print("🧹 strict cleanup: 초기화할 과거 비실진입 entry_hit 없음")

        with open(STRICT_ENTRY_CLEANUP_MARKER, "w", encoding="utf-8") as f:
            f.write(now_s)
    except Exception as e:
        print(f"⚠️ strict cleanup 오류: {e}")

TUNE_LOOKBACK_DAYS = int(os.getenv("TUNE_LOOKBACK_DAYS", "30") or "30")
TUNE_MIN_SAMPLES   = int(os.getenv("TUNE_MIN_SAMPLES", "30") or "30")
TUNE_ALPHA         = float(os.getenv("TUNE_ALPHA", "0.35") or "0.35")  # 0~1, 클수록 빠르게 반영

def _safe_float(x, default=0.0):
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default

def _prune_signal_log(data: dict) -> dict:
    """signal_log.json이 너무 커지면 오래된 기록부터 정리."""
    try:
        if not isinstance(data, dict):
            return data
        if len(data) <= SIGNAL_LOG_MAX_RECORDS:
            return data
        # detect_date+time → 정렬 키(없으면 key 자체)
        def _k(item):
            k, v = item
            d = str(v.get("detect_date", ""))
            t = str(v.get("detect_time", ""))
            if len(d) == 8 and len(t) >= 5:
                return d + t.replace(":", "")[:6]
            return k
        items = sorted(data.items(), key=_k)
        keep = dict(items[-SIGNAL_LOG_MAX_RECORDS:])
        return keep
    except Exception:
        return data

def _get_params_snapshot() -> dict:
    """신호 당시 '조건'을 최소 핵심만 스냅샷(최적화용)."""
    try:
        # 너무 많은 키를 저장하면 튜닝 데이터가 지저분해짐 → 핵심만
        keys = [
            "min_score_normal", "min_score_strict",
            "atr_stop_mult", "atr_target_mult",
            "early_price_min", "early_volume_min",
            "mid_surge_min_pct", "mid_pullback_min", "mid_pullback_max",
            "themed_score_bonus",
            # 가중치(기여도 튜닝용)
            "feat_w_rsi", "feat_w_ma", "feat_w_bb", "feat_w_sector", "feat_w_nxt", "feat_w_geo",
        ]
        snap = {k: _dynamic.get(k) for k in keys if k in _dynamic}
        snap["_v"] = BOT_VERSION
        return snap
    except Exception:
        return {"_v": BOT_VERSION}

def _tune_score(records: list) -> float:
    """
    파라미터 후보의 성능 점수.
    - 평균 수익률(+)을 중심으로, 손실/드로우다운(MAE)을 페널티로 반영.
    """
    if not records:
        return -1e9
    pnls = [_safe_float(r.get("pnl_pct"), 0.0) for r in records]
    maes = [_safe_float(r.get("mae_pct"), 0.0) for r in records]  # 음수(손실폭)
    # MAE는 보통 음수이므로 abs로 페널티
    avg = sum(pnls) / len(pnls)
    win = sum(1 for p in pnls if p > 0)
    wr  = win / len(pnls)
    avg_abs_mae = (sum(abs(x) for x in maes) / len(maes)) if maes else 0.0
    # 점수: 평균수익 + (승률-0.5)*2 보너스 - MAE 페널티
    return avg + (wr - 0.5) * 2.0 - avg_abs_mae * 0.35

def _select_best_params(completed: list) -> dict:
    """최근 lookback 구간에서 params_snapshot별 성능 비교 → best snapshot 반환."""
    if not completed:
        return {}
    # lookback filter
    try:
        cutoff = datetime.now() - timedelta(days=TUNE_LOOKBACK_DAYS)
        filtered = []
        for r in completed:
            d = r.get("exit_date") or r.get("detect_date")
            t = r.get("exit_time") or r.get("detect_time") or "00:00:00"
            if d and len(str(d)) == 8:
                try:
                    dt = datetime.strptime(str(d) + str(t)[:8], "%Y%m%d%H:%M:%S")
                except Exception:
                    try:
                        dt = datetime.strptime(str(d), "%Y%m%d")
                    except Exception:
                        dt = None
                if dt and dt >= cutoff:
                    filtered.append(r)
            else:
                filtered.append(r)
    except Exception:
        filtered = completed

    groups = {}
    for r in filtered:
        snap = r.get("params_snapshot")
        if not isinstance(snap, dict):
            continue
        # signature (핵심 값만)
        sig = (
            snap.get("min_score_normal"),
            snap.get("min_score_strict"),
            snap.get("atr_stop_mult"),
            snap.get("atr_target_mult"),
        )
        groups.setdefault(sig, []).append(r)

    # 충분한 샘플만
    scored = []
    for sig, recs in groups.items():
        if len(recs) < TUNE_MIN_SAMPLES:
            continue
        scored.append((_tune_score(recs), sig, recs))

    if not scored:
        return {}
    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_sig, best_recs = scored[0]
    # best snapshot은 대표 1개를 사용
    best_snap = dict(best_recs[0].get("params_snapshot", {}))
    best_snap["_score"] = round(best_score, 4)
    best_snap["_n"] = len(best_recs)
    return best_snap

def _apply_result_labels(rec: dict):
    """추적 결과를 최적화/튜닝에 쓰기 좋게 라벨링(MFE/MAE/보유기간 등)."""
    try:
        entry = _safe_float(rec.get("entry_price"), 0.0)
        if entry <= 0:
            return
        max_p = _safe_float(rec.get("max_price"), entry)
        min_p = _safe_float(rec.get("min_price"), entry)
        rec["mfe_pct"] = round((max_p - entry) / entry * 100, 2)
        rec["mae_pct"] = round((min_p - entry) / entry * 100, 2)  # 보통 음수
        # 보유 기간(분) — detect_date/time 또는 log_key 기반
        try:
            d = str(rec.get("detect_date", ""))
            t = str(rec.get("detect_time", "00:00:00"))
            dt0 = datetime.strptime(d + t[:8], "%Y%m%d%H:%M:%S")
            d2 = str(rec.get("exit_date", ""))
            t2 = str(rec.get("exit_time", "00:00:00"))
            dt1 = datetime.strptime(d2 + t2[:8], "%Y%m%d%H:%M:%S")
            rec["hold_minutes"] = int((dt1 - dt0).total_seconds() // 60)
        except Exception:
            pass
        pnl = _safe_float(rec.get("pnl_pct"), 0.0)
        if pnl > 0:
            rec["outcome"] = "win"
        elif pnl < 0:
            rec["outcome"] = "loss"
        else:
            rec["outcome"] = "flat"
    except Exception:
        pass



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
        stock_name = _resolve_stock_name(code, stock.get("name", ""))
        stock["name"] = stock_name
        sig_type = stock.get("signal_type", "UNKNOWN")
        # 같은 종목이 이미 추적 중이면 업데이트하지 않음 (중복 방지)
        log_key  = f"{code}_{stock.get('detected_at', datetime.now()).strftime('%Y%m%d%H%M')}"

        # 신호 발생 시 활성화된 기능 플래그 기록
        indic    = stock.get("indic", {})
        position = stock.get("position", {})
        _geo_st = _geo_event_state if _geo_event_state.get("active") else {}
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
            # ── 지정학 이벤트 기여도 (auto_tune 학습용) ──
            "geo_active":       bool(_geo_st),
            "geo_uncertainty":  _geo_st.get("uncertainty", ""),
            "geo_sector_adj":   locals().get("_geo_adj_applied", 0),
        }


        # ── 최적화용 스냅샷 (신호 당시 조건/상황) ──
        params_snapshot = _get_params_snapshot()
        feature_snapshot = {
            "regime": stock.get("regime", "normal"),
            "nxt_open": bool(is_nxt_open()),
            "krx_open": bool(is_market_open()),
            "strict_time": bool(is_strict_time()),
            "timeslot": _get_timeslot(datetime.now().strftime("%H:%M:%S")),
            "price": stock.get("price"),
            "change_rate": stock.get("change_rate", 0),
            "volume_ratio": stock.get("volume_ratio", 0),
            "rsi": indic.get("rsi", 50),
            "ma_aligned": indic.get("ma", {}).get("aligned"),
            "bb_pct_b": indic.get("bb", {}).get("pct_b", 0.5),
            "bb_breakout": indic.get("bb", {}).get("breakout", False),
            "sector_theme": stock.get("sector_info", {}).get("theme", ""),
            "sector_bonus": stock.get("sector_info", {}).get("bonus", 0),
        }

        data[log_key] = {
            "log_key":      log_key,
            "code":         code,
            "name":         stock_name,
            "signal_type":  sig_type,
            "score":        stock.get("score", 0),
            "grade":        stock.get("grade", "B"),
            "market_regime": MARKET_REGIME.get("label","unknown"),
            "market_regime_det": MARKET_REGIME.get("details",{}),
            "geo_sector_bias": globals().get('GEO_SECTOR_BIAS', {}),
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
            "params_snapshot":   params_snapshot,
            "feature_snapshot":  feature_snapshot,
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
        data = _prune_signal_log(data)
        _write_json_atomic(SIGNAL_LOG_FILE, data, indent=2)
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
            _write_json_atomic(EARLY_LOG_FILE, data, indent=2)
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
def send_overnight_risk_alerts():
    """장 마감 후 추적 중 종목 오버나이트 위험도 알림"""
    try:
        data = {}
        try:
            with open(SIGNAL_LOG_FILE, "r") as f: data = json.load(f)
        except: pass
        tracking = [v for v in data.values() if v.get("status") == "추적중"]
        if not tracking: return

        high_risk = []
        for rec in tracking:
            code  = rec.get("code","")
            name  = rec.get("name","")
            entry = rec.get("entry_price", 0)
            pnl   = rec.get("pnl_pct", 0.0)
            risk  = calc_overnight_risk(code, name, entry, pnl)
            if risk["level"] in ("high", "mid"):
                high_risk.append((rec, risk))

        if not high_risk: return

        msg = "🌙 <b>오버나이트 위험 알림</b>\n━━━━━━━━━━━━━━━\n"
        for rec, risk in high_risk:
            pnl_str = f"{rec.get('pnl_pct',0):+.1f}%"
            msg += (f"{'🔴' if risk['level']=='high' else '🟡'} "
                    f"<b>{rec['name']}</b>  현재 {pnl_str}\n"
                    f"  {risk['reason']}\n")

        # v37.0: 오버나이트 보유 과거 통계 + 현재 국면 이력
        try:
            _on_hist = get_overnight_history()
            if _on_hist:
                msg += f"\n📊 {_on_hist}\n"
            _regime = get_market_regime()
            _r_hist = get_regime_history(_regime)
            if _r_hist:
                msg += f"📊 {_r_hist}\n"
        except: pass
        # Save latest overnight risk message (for pre-open recap)
        try:
            _write_json_atomic(OVERNIGHT_RISK_LAST_FILE, {
                "ts": _now_kst().isoformat(timespec="seconds"),
                "msg": msg,
            })
        except Exception:
            pass

        # Quiet night: do not push; only store
        if _is_quiet_night():
            print("💤 야간(20:00~07:30): 오버나이트 위험 알림 저장만 수행")
            return

        send(msg)
    except Exception as e:
        _log_error("send_overnight_risk_alerts", e)


# ============================================================
# 🌙 오버나이트 모니터링 (장 마감 후 ~ 장 시작 전)
# ============================================================
_overnight_state: dict = {
    "last_us_regime": "neutral",  # 직전 미국 국면
    "last_vix":        20.0,      # 직전 VIX
    "alerted_regime":  "",        # 이미 알림 보낸 국면
    "summary_lines":   [],        # 오버나이트 요약 (브리핑용)
}

def run_overnight_monitor():
    """
    오버나이트(20:10~08:40) 주기적 실행.
    미국 시장 국면 변화 감지 → 즉시 알림.
    변화 없으면 조용히 넘어감 (스팸 방지).
    """
    try:
        now_h = datetime.now().hour
        # 오버나이트 시간대만 실행 (20:10~08:40)
        if not (now_h >= 20 or now_h < 9):
            return

        us = get_us_market_signals()
        cur_regime  = us.get("us_regime", "neutral")
        cur_vix     = us.get("vix", 20.0)
        nasdaq_chg  = us.get("nasdaq_chg", 0.0)
        gap_signal  = us.get("gap_signal", "flat")
        prev_regime = _overnight_state["last_us_regime"]
        prev_vix    = _overnight_state["last_vix"]

        alerts = []

        # ── 국면 변화 감지 ──
        regime_rank = {"risk_on": 0, "neutral": 1, "risk_off": 2, "panic": 3}
        cur_rank    = regime_rank.get(cur_regime, 1)
        prev_rank   = regime_rank.get(prev_regime, 1)

        if cur_rank > prev_rank and cur_regime != _overnight_state["alerted_regime"]:
            _overnight_state["alerted_regime"] = cur_regime
            regime_label = {"risk_off": "🟠 위험회피", "panic": "🔴 패닉"}
            alerts.append(
                f"⚠️ 미국 시장 국면 악화: {regime_label.get(cur_regime, cur_regime)}\n"
                f"  나스닥 {nasdaq_chg:+.1f}%  VIX {cur_vix:.0f}"
            )
        elif cur_rank < prev_rank and cur_regime != _overnight_state["alerted_regime"]:
            _overnight_state["alerted_regime"] = cur_regime
            alerts.append(
                f"✅ 미국 시장 국면 개선: 🟢 위험선호 전환\n"
                f"  나스닥 {nasdaq_chg:+.1f}%  VIX {cur_vix:.0f}"
            )

        # ── VIX 급등 단독 감지 (국면 변화 없어도) ──
        if cur_vix >= 30 and prev_vix < 30:
            alerts.append(f"🔴 VIX 공포 구간 진입: {cur_vix:.0f} (이전 {prev_vix:.0f})")
        elif cur_vix >= 25 and prev_vix < 25:
            alerts.append(f"🟠 VIX 불안 구간 진입: {cur_vix:.0f}")

        # ── 나스닥 급락 단독 감지 ──
        if nasdaq_chg <= -3.0 and prev_rank < 3:
            alerts.append(f"🔴 나스닥 급락 {nasdaq_chg:+.1f}% — 내일 갭하락 주의")
        elif nasdaq_chg >= 2.0 and prev_rank > 0:
            alerts.append(f"🟢 나스닥 강세 {nasdaq_chg:+.1f}% — 내일 갭상승 기대")

        # ── 상태 업데이트 ──
        _overnight_state["last_us_regime"] = cur_regime
        _overnight_state["last_vix"]       = cur_vix

        # ── 요약 누적 (브리핑용) ──
        ts_str = datetime.now().strftime("%H:%M")
        for a in alerts:
            line = f"[{ts_str}] {a}"
            _overnight_state["summary_lines"].append(line)
            # 최근 10개만 유지
            _overnight_state["summary_lines"] = _overnight_state["summary_lines"][-10:]

        # ── 지정학 이벤트 오버나이트 체크 ──
        try:
            headlines_by_src = _fetch_multi_source_headlines()
            if headlines_by_src:
                geo = analyze_geopolitical_event(headlines_by_src)
                if geo.get("detected") and geo.get("uncertainty") in ("high", "mid"):
                    alerts.append(
                        f"🌍 지정학 이벤트: {geo.get('summary','')}\n"
                        f"  관련 섹터: {', '.join(geo.get('sectors',[]))}"
                    )
        except: pass

        # ── 알림 발송 ──
        if alerts:
            gap_emoji = {"gap_up": "⬆️ 갭상승", "flat": "➡️ 갭 없음", "gap_down": "⬇️ 갭하락"}
            msg = (f"🌙 <b>오버나이트 알림</b>  {ts_str}\n"
                   f"━━━━━━━━━━━━━━━\n"
                   + "\n".join(alerts) +
                   f"\n\n내일 갭 예측: {gap_emoji.get(gap_signal, '➡️')}")
            send(msg)

    except Exception as e:
        _log_error("run_overnight_monitor", e)

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

            # ── ★ 보유 종목 뉴스/공시 실시간 악재 감시 ──
            _now_ts = time.time()
            _last_check = _carry_news_watch.get(code, 0)
            if _now_ts - _last_check >= 1800:  # 30분마다 체크
                _carry_news_watch[code] = _now_ts
                _rec_name = rec.get("name", code)
                pnl_now   = round((price - entry) / entry * 100, 2) if entry else 0

                # DART 위험 공시 체크
                try:
                    _d = check_dart_risk(code)
                    if _d["is_risk"]:
                        _dk = f"{log_key}_dart_exit"
                        if _dk not in _tracking_notified:
                            _tracking_notified.add(_dk)
                            _msg = (
                                "🚨 <b>[보유 종목 악재 공시 감지]</b>\n"
                                "━━━━━━━━━━━━━━━\n"
                                f"🔴 <b>{_rec_name}</b>  <code>{code}</code>\n"
                                "━━━━━━━━━━━━━━━\n"
                                f"📋 공시: {_d['title']}\n"
                                "━━━━━━━━━━━━━━━\n"
                                f"💰 현재가: <b>{price:,}원</b>  ({pnl_now:+.1f}%)\n"
                                "━━━━━━━━━━━━━━━\n"
                                "⚡ <b>즉시 매도 검토 권장</b>\n"
                                f"💡 /result {code} 로 결과 기록"
                            )
                            send_with_chart_buttons(_msg, code, _rec_name)
                            print(f"  🚨 보유종목 공시악재: {_rec_name} — {_d['title']}")
                except Exception as _e:
                    print(f"  ⚠️ 보유종목 DART체크오류: {_e}")

                # 뉴스 심층 감성 체크 (analyze_news_deep 활용)
                try:
                    _articles = fetch_news_for_stock(code, _rec_name)
                    if _articles:
                        _deep = analyze_news_deep(_articles, _rec_name, code)
                        _nadj = int(_deep.get("score_adj", 0) or 0)
                        _verd = _deep.get("verdict", "중립")
                        if _nadj <= -40:
                            _nk = f"{log_key}_news_exit"
                            if _nk not in _tracking_notified:
                                _tracking_notified.add(_nk)
                                _rps = "\n".join(
                                    f"  ⚠️ {rp}"
                                    for rp in _deep.get("risk_points", [])[:3]
                                )
                                _msg2 = (
                                    "⚠️ <b>[보유 종목 부정 뉴스 감지]</b>\n"
                                    "━━━━━━━━━━━━━━━\n"
                                    f"🟡 <b>{_rec_name}</b>  <code>{code}</code>\n"
                                    "━━━━━━━━━━━━━━━\n"
                                    f"📰 뉴스 판단: {_verd}  ({_nadj:+d}점)\n"
                                    f"{_rps}\n"
                                    "━━━━━━━━━━━━━━━\n"
                                    f"💰 현재가: <b>{price:,}원</b>  ({pnl_now:+.1f}%)\n"
                                    "━━━━━━━━━━━━━━━\n"
                                    "💡 손절가 재확인 후 매도 판단 권장\n"
                                    f"/result {code} 로 결과 기록"
                                )
                                send_with_chart_buttons(_msg2, code, _rec_name)
                                print(f"  ⚠️ 보유종목 부정뉴스: {_rec_name} 감성점수={_nadj}")
                except Exception as _e:
                    print(f"  ⚠️ 보유종목 뉴스체크오류: {_e}")

            # ── 분할 청산 가이드 (목표가 도달 전 중간 알림) ──
            if entry and target and ((rec.get('actual_entry') is True) or (ALLOW_VIRTUAL_EXIT_GUIDE and rec.get('entry_hit') is True)):
                pnl_now  = (price - entry) / entry * 100
                half_pct = (target - entry) / entry * 100 / 2   # 목표의 절반
                partial_key = f"{log_key}_partial"
                _partial_min = calc_partial_exit_min_pct(code, price)
                if (pnl_now >= half_pct
                        and partial_key not in _tracking_notified
                        and half_pct > _partial_min
                        and (time.time() - _partial_exit_last_ts.get(code, 0) >= PARTIAL_EXIT_GUIDE_COOLDOWN_MIN * 60)):
                    _tracking_notified.add(partial_key)
                    _partial_exit_last_ts[code] = time.time()
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
                    target_pct = ((target - entry) / entry * 100) if entry else 0
                    target_progress_pct = (pnl_now / target_pct * 100) if target_pct else 0
                    basis_gap_pct = ((price - entry) / entry * 100) if entry else 0
                    send_with_chart_buttons(
                        f"💡 <b>[분할 청산 타이밍]</b>\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"🟢 <b>{rec['name']}</b>  <code>{code}</code>\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"현재 <b>+{pnl_now:.1f}%</b>  (목표의 {target_progress_pct:.0f}%)\n"
                        f"📌 분할 기준: <b>+{half_pct:.1f}% 이상</b> 달성 시 1차 익절 검토\n"
                        f"✅ 현재 상태: 기준 대비 <b>{pnl_now-half_pct:+.1f}%p</b>\n"
                        f"📍 현재가: <b>{price:,}원</b>\n"
                        f"🎯 진입가: <b>{entry:,}원</b>  ({basis_gap_pct:+.1f}%)\n"
                        f"🏆 목표가: <b>{target:,}원</b>  (+{target_pct:.1f}%)\n"
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
                    # 최고가 갱신 → ATR+국면 기반 트레일링 스탑 끌어올리기
                    new_trail = calc_trailing_stop(code, price)
                    if new_trail > trail_stop:
                        rec["trailing_stop"] = new_trail

                # ── 수급 이탈 경고 (추적 중) ──
                try:
                    fp_key = f"force_warn_{code}"
                    if fp_key not in _tracking_notified:
                        fp = detect_force_pattern(code, name)
                        if fp.get("risk_flag"):
                            _tracking_notified.add(fp_key)
                            out_patterns = [p for p in fp.get("patterns", [])
                                            if p.get("score_adj", 0) < 0]
                            lines = ""
                            for op in out_patterns[:3]:
                                ce = {"high":"🔴","mid":"🟡","low":"⬜"}.get(op.get("confidence","low"),"⬜")
                                ck = {"high":"신뢰높음","mid":"참고용"}.get(op.get("confidence",""),"참고용")
                                lines += f"  {ce} {op['label']} [{ck}]\n  └ {op['detail']}\n"
                            send(
                                f"🔴 <b>[수급 이탈 경고]  {name}</b>\n"
                                f"━━━━━━━━━━━━━━━\n"
                                f"{lines}"
                                f"현재가: {cur_price:,}원  ({pnl_pct:+.1f}%)\n"
                                f"━━━━━━━━━━━━━━━\n"
                                f"⚠️ 통계적 패턴 감지 — 확증 아님, 익절/손절 직접 판단 필요"
                            )
                except:
                    pass

        # ── 테마 약세 전환 경고 (추적 중) ──
                try:
                    _rot      = detect_theme_rotation()
                    _si       = rec.get("sector_info") or {}
                    _tkey     = _si.get("theme", "") or _si.get("theme_key", "")
                    _weak_now = [k for k, v in _rot.get("weak", [])]
                    _theme_warn_key = f"theme_warn_{code}"
                    if (_tkey and _tkey in _weak_now
                            and _theme_warn_key not in _tracking_notified
                            and pnl_now > 0):
                        _tracking_notified.add(_theme_warn_key)
                        t_chg = _rot.get("themes", {}).get(_tkey, 0)
                        send_with_chart_buttons(
                            f"🔄 <b>[{name}] 테마 약세 전환 경고</b>\n"
                            f"  [{_tkey}] 현재 {t_chg:+.1f}% — 테마 식는 중\n"
                            f"  현재 수익 {pnl_now:+.1f}% — 익절 고려 권장",
                            code, name
                        )
                except: pass

                # ── 실시간 오버나이트 위험도 급등 시 즉시 알림 ──
                try:
                    _risk_key = f"overnight_risk_{code}"
                    if _risk_key not in _tracking_notified:
                        _risk = calc_overnight_risk(code, name, entry, pnl_now)
                        if _risk["level"] == "high":
                            _tracking_notified.add(_risk_key)
                            send_with_chart_buttons(
                                f"🔴 <b>[{name}] 오버나이트 위험 긴급 알림</b>\n"
                                f"  {_risk['reason']}\n"
                                f"  현재 {pnl_now:+.1f}% — 마감 전 매도 고려",
                                code, name
                            )
                except: pass

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
                    _apply_result_labels(rec)
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
                    rec["trailing_stop"]   = calc_trailing_stop(code, price)
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
            data = _prune_signal_log(data)
            _write_json_atomic(SIGNAL_LOG_FILE, data, indent=2)
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
            _reentry_min = calc_reentry_bounce(code, price)
            if bounce >= _reentry_min and vr >= REENTRY_VOL_MIN:
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
AUTO_TUNE_FILE   = os.path.join(DATA_DIR, "auto_tune_log.json")   # 조정 이력 저장
DYNAMIC_PARAMS_FILE = os.path.join(DATA_DIR, "dynamic_params.json")  # 조정된 파라미터 영구 저장
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
    "feat_w_geo":       1.0,    # 지정학 이벤트 섹터 보정 가중치
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
        _write_json_atomic(DYNAMIC_PARAMS_FILE, _dynamic, indent=2)
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
        # v37.0: 타입 강제 변환 (JSON str→int/float 오류 방지)
        for k, v in saved.items():
            if k in _dynamic:
                default = _dynamic[k]
                try:
                    if isinstance(default, int) and not isinstance(default, bool):
                        _dynamic[k] = int(v)
                    elif isinstance(default, float):
                        _dynamic[k] = float(v)
                    elif isinstance(default, dict) and isinstance(v, dict):
                        _dynamic[k] = v
                    elif isinstance(default, str):
                        _dynamic[k] = str(v)
                    else:
                        _dynamic[k] = v
                except (ValueError, TypeError):
                    pass  # 변환 실패 시 기본값 유지
        _early_price_min_dynamic  = _dynamic["early_price_min"]
        _early_volume_min_dynamic = _dynamic["early_volume_min"]
        print(f"  🔧 동적 파라미터 복원 완료 (min_score={_dynamic['min_score_normal']}점, "
              f"atr_stop={_dynamic['atr_stop_mult']})")
    except FileNotFoundError:
        print("  🔧 dynamic_params.json 없음 → 기본값 사용")
        # 저장 파일이 없으면 기본값을 즉시 저장해 다음 재시작부터 복원되도록 한다
        try:
            _save_dynamic_params()
            print("  💾 dynamic_params.json 기본값 저장 완료")
        except Exception as se:
            print(f"  ⚠️ dynamic_params 기본값 저장 실패: {se}")
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

        # ── 0) params_snapshot 기반 성능 튜닝 (최적조건 만들기 핵심) ──
        best = _select_best_params(completed)
        if best:
            try:
                # 현재값
                cur_min_n = int(_dynamic.get("min_score_normal", 60))
                cur_min_s = int(_dynamic.get("min_score_strict", 70))
                cur_atr_s = _safe_float(_dynamic.get("atr_stop_mult", 1.5), 1.5)
                cur_atr_t = _safe_float(_dynamic.get("atr_target_mult", 3.0), 3.0)

                # 후보값
                cand_min_n = int(best.get("min_score_normal", cur_min_n))
                cand_min_s = int(best.get("min_score_strict", cur_min_s))
                cand_atr_s = _safe_float(best.get("atr_stop_mult", cur_atr_s), cur_atr_s)
                cand_atr_t = _safe_float(best.get("atr_target_mult", cur_atr_t), cur_atr_t)

                # 스무딩(완만하게)
                new_min_n = int(round(cur_min_n * (1 - TUNE_ALPHA) + cand_min_n * TUNE_ALPHA))
                new_min_s = int(round(cur_min_s * (1 - TUNE_ALPHA) + cand_min_s * TUNE_ALPHA))
                new_atr_s = round(cur_atr_s * (1 - TUNE_ALPHA) + cand_atr_s * TUNE_ALPHA, 2)
                new_atr_t = round(cur_atr_t * (1 - TUNE_ALPHA) + cand_atr_t * TUNE_ALPHA, 2)

                # 가드레일
                new_min_n = max(45, min(new_min_n, 80))
                new_min_s = max(55, min(new_min_s, 90))
                new_atr_s = max(0.8, min(new_atr_s, 3.5))
                new_atr_t = max(1.5, min(new_atr_t, 6.0))

                # 반영
                if (new_min_n, new_min_s, new_atr_s, new_atr_t) != (cur_min_n, cur_min_s, cur_atr_s, cur_atr_t):
                    _dynamic["min_score_normal"] = new_min_n
                    _dynamic["min_score_strict"] = new_min_s
                    _dynamic["atr_stop_mult"]    = new_atr_s
                    _dynamic["atr_target_mult"]  = new_atr_t

                    changes.append(
                        f"🧠 <b>성능 기반 튜닝</b> (최근 {TUNE_LOOKBACK_DAYS}일 / n={best.get('_n','?')})\n"
                        f"- score {best.get('_score','?')} 기준 best params로 스무딩 적용\n"
                        f"- min_score: {cur_min_n}/{cur_min_s} → {new_min_n}/{new_min_s}\n"
                        f"- atr_stop/target: {cur_atr_s} / {cur_atr_t} → {new_atr_s} / {new_atr_t}"
                    )
            except Exception as te:
                _log_error("auto_tune.params_snapshot", te)


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
                "feat_w_geo":    ("geo",         lambda r: r.get("feature_flags",{}).get("geo_active", False)),
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
            _write_json_atomic(AUTO_TUNE_FILE, tune_log, indent=2)

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
    if is_scoring_only_instrument(code, name):
        return
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
                    def _watch_suffix(peer_code: str, peer_price: int) -> str:
                        """섹터 라인에 감시 상태/수익률 표기 (진입가 대비 현재가 기준)"""
                        try:
                            if not _entry_watch:
                                return ""
                            cand = [w for w in _entry_watch.values() if w.get('code') == peer_code]
                            if not cand:
                                return ""
                            w = max(cand, key=lambda x: x.get('registered_ts', 0))
                            entry = safe_int(w.get('entry_price', 0))
                            if not entry:
                                return ""
                            if w.get('entry_hit'):
                                if peer_price:
                                    pnl = (peer_price / entry - 1.0) * 100.0
                                    return f" ✅ <b>({pnl:+.1f}%)</b>"
                                return " ✅"
                            return " ⏳ <b>(미도달)</b>"
                        except Exception:
                            return ""

                    lines   = f"🏭 <b>섹터 모멘텀</b> [{theme}]  {tag}\n"
                    lines  += f"  {summary}\n" if summary else ""
                    for r in rising[:5]:
                        vt    = f" 🔊{r['volume_ratio']:.0f}x" if r.get("volume_ratio",0)>=2 else ""
                        new_t = " 🆕" if r["code"] in new_set else ""
                        wsuf  = _watch_suffix(r["code"], safe_int(r.get("price", 0)))
                        marker = '🟩' if r['change_rate'] > 0 else ('🟥' if r['change_rate'] < 0 else '⬜')
                        lines += f"  {marker} {_resolve_stock_name(r['code'], r.get('name',''))} <b>{r['change_rate']:+.1f}%</b>{vt}{new_t}{wsuf}\n"
                    for r in flat[:2]:
                        marker = '🟩' if r['change_rate'] > 0 else ('🟥' if r['change_rate'] < 0 else '⬜')
                        lines += f"  {marker} {_resolve_stock_name(r['code'], r.get('name',''))} {r['change_rate']:+.1f}%\n"
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
SCORING_ONLY_NAME_MARKERS = ("KODEX", "TIGER", "KOSEF", "KBSTAR", "ARIRANG", "HANARO", "ACE", "SOL", "ETF", "ETN")

def is_scoring_only_instrument(code: str, name: str = "") -> bool:
    """ETF/ETN/지수형 종목은 점수 참고용으로만 사용하고 실제 포착/감시 대상에서는 제외."""
    try:
        nm = str(name or "").upper()
        return any(m in nm for m in SCORING_ONLY_NAME_MARKERS)
    except Exception:
        return False

def _watch_suffix(peer_code: str, peer_price: int) -> str:
    """감시 상태/수익률 표기 (진입가 대비 현재가 기준)."""
    try:
        if not _entry_watch:
            return ""
        cand = [w for w in _entry_watch.values() if w.get('code') == peer_code]
        if not cand:
            return ""
        w = max(cand, key=lambda x: x.get('registered_ts', 0))
        entry = safe_int(w.get('entry_price', 0))
        if not entry:
            return ""
        if w.get('entry_hit'):
            if peer_price:
                pnl = (peer_price / entry - 1.0) * 100.0
                return f" ✅ <b>({pnl:+.1f}%)</b>"
            return " ✅"
        return " ⏳ <b>(미도달)</b>"
    except Exception:
        return ""

def register_top_signal(s: dict):
    """신호 발생마다 오늘의 최우선 종목 풀에 추가 (점수 높은 종목 유지)"""
    code  = s.get("code","")
    score = s.get("score", 0)
    if not code: return
    if is_scoring_only_instrument(code, s.get("name", "")):
        return
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
    stock_name = _resolve_stock_name(code, s.get("name", ""))
    if is_scoring_only_instrument(code, stock_name):
        return
    s["name"] = stock_name

    # ── 같은 종목 기존 감시 제거 (재포착 시 진입가 갱신) ──
    old_keys = [k for k, w in _entry_watch.items() if w["code"] == code]
    for k in old_keys:
        old_entry  = _entry_watch[k].get("entry_price", 0)
        miss_count = _entry_watch[k].get("miss_count", 0)
        print(f"  🔄 진입가 갱신: {stock_name} {old_entry:,}→{entry:,}원 (미도달 {miss_count}회)")
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
            _write_json_atomic(SIGNAL_LOG_FILE, sig_data, indent=2)
        except Exception as e:
            print(f"⚠️ 진입가변경 기록 오류: {e}")
        del _entry_watch[k]

    log_key = f"{code}_{datetime.now().strftime('%Y%m%d%H%M')}"
    _entry_watch[log_key] = {
        "code": code, "name": stock_name, "entry_price": entry,
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
    print(f"  🎯 진입가 감시 등록: {stock_name} {entry:,}원 (만료: {MAX_CARRY_DAYS}일 후)")

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
        _write_json_atomic(SIGNAL_LOG_FILE, data, indent=2)
        print(f"  📝 진입미달 기록: {watch['name']} {reason} (진입가 대비 {miss_away:+.1f}%)")
    except Exception as e:
        print(f"⚠️ 진입미달 기록 오류: {e}")


def _mark_entry_hit_in_signal_log(code: str, signal_type: str) -> None:
    """진입가 도달(HIT) 이벤트를 signal_log에 기록. (가상진입/학습용)"""
    try:
        data = {}
        try:
            with open(SIGNAL_LOG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            return
        now_s = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for _k, rec in data.items():
            if rec.get('code') == code and rec.get('status') == '추적중' and rec.get('signal_type') == signal_type:
                rec['entry_hit'] = True
                rec['entry_hit_time'] = now_s
                break
        _write_json_atomic(SIGNAL_LOG_FILE, data, indent=2)
    except Exception as e:
        print(f"⚠️ entry_hit 기록 오류: {e}")
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

            # ── 상승 이탈: ATR×국면 기반 기준 이상 오르면 포기 ──
            _escape_pct = calc_surge_escape_pct(watch["code"], entry)
            if diff_pct >= _escape_pct:
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

            # ── 엄격형 진입가 도달: 현재가가 진입가 이하일 때만 인정 ──
            if price <= entry:
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
                watch['entry_hit'] = True
                try:
                    _mark_entry_hit_in_signal_log(watch['code'], watch.get('signal_type',''))
                except Exception:
                    pass
                print(f"  🎯 진입가 도달 ({notify_count+1}회): {watch['name']} {price:,} / 진입 {entry:,}")
        except: continue
    for k in expired:
        _entry_watch.pop(k, None)

# ============================================================
# 🛡 장마감 전/후 손익 방어 가이드 (entry_hit 감시 종목)
#   - '진입가 도달' 후 모니터링 중인 종목에
#     지정학/뉴스/DART/지표 리스크가 생기면 손익 방어 안내를 자동 발송
# ============================================================
DEFENSE_KRX_CLOSE_WINDOW_MIN = int(os.getenv("DEFENSE_KRX_CLOSE_WINDOW_MIN", "25") or "25")  # 15:05~15:30
DEFENSE_NXT_CLOSE_WINDOW_MIN = int(os.getenv("DEFENSE_NXT_CLOSE_WINDOW_MIN", "25") or "25")  # 19:35~20:00
DEFENSE_ALERT_COOLDOWN_SEC   = int(os.getenv("DEFENSE_ALERT_COOLDOWN_SEC", "1800") or "1800")  # 30분
DEFENSE_LOSS_WARN_PCT        = float(os.getenv("DEFENSE_LOSS_WARN_PCT", "1.2") or "1.2")  # -1.2% 이하면 경고 강화
DEFENSE_PROFIT_LOCK_PCT      = float(os.getenv("DEFENSE_PROFIT_LOCK_PCT", "2.0") or "2.0")  # +2% 이상이면 익절 방어 권고

_NEG_NEWS_KWS = [
    "급락","하락","쇼크","우려","불확실","리스크","제재","관세","전쟁","공습","미사일","충돌","봉쇄",
    "압수수색","검찰","조사","횡령","배임","파산","회생","워크아웃","상장폐지","거래정지","관리종목",
    "하향","경고","부정","적자전환","실적부진","리콜","사고","해킹",
]

def _is_close_defense_window(now: datetime | None = None) -> bool:
    now = now or _now_kst()
    t = now.time()
    # KRX: 15:30 마감 기준
    krx_start = (datetime.combine(now.date(), dtime(15,30), tzinfo=_KST) - timedelta(minutes=DEFENSE_KRX_CLOSE_WINDOW_MIN)).time()
    krx_end   = dtime(15,30)
    # NXT: 20:00 마감 기준 (NXT만 열릴 수도 있음)
    nxt_start = (datetime.combine(now.date(), dtime(20,0), tzinfo=_KST) - timedelta(minutes=DEFENSE_NXT_CLOSE_WINDOW_MIN)).time()
    nxt_end   = dtime(20,0)
    in_krx = (t >= krx_start and t <= krx_end)
    in_nxt = (t >= nxt_start and t <= nxt_end)
    return in_krx or in_nxt

def _detect_defense_issues(code: str, name: str, entry: int, stop_loss: int) -> tuple[int, list[str]]:
    """리스크 점수(0~100)와 사유 리스트 반환."""
    score = 0
    reasons = []
    try:
        # 1) DART 리스크
        try:
            dr = check_dart_risk(code, name)
            if isinstance(dr, dict) and dr.get("is_risk"):
                score += 60
                reasons.append(f"⚠️ DART 리스크: {dr.get('title','')}".strip())
        except Exception:
            pass

        # 2) 지정학/거시 리스크(시장)
        try:
            geo = _geo_event_state or {}
            if geo.get("active") and time.time() - float(geo.get("ts",0) or 0) < 3600*12:
                unc = str(geo.get("uncertainty","mid"))
                adj = int(geo.get("score_adj",0) or 0)
                if unc == "high" and adj <= -5:
                    score += 20
                    reasons.append("🌍 지정학 불확실성(HIGH) — 시장 리스크오프 가능")
                elif adj <= -8:
                    score += 15
                    reasons.append("🌍 지정학 이벤트 — 변동성 확대 가능")
        except Exception:
            pass

        # 3) 최근 뉴스(타이틀 기반 간단 필터)
        try:
            news = fetch_news_for_stock(code, name) or []
            hits = []
            for n in news[:10]:
                for kw in _NEG_NEWS_KWS:
                    if kw in n and kw not in hits:
                        hits.append(kw)
            if hits:
                score += 15
                reasons.append(f"📰 부정 키워드 감지: {', '.join(hits[:4])}")
        except Exception:
            pass

        # 4) 가격/손익 상태
        try:
            cur = get_stock_price(code) or {}
            price = int(cur.get("price") or 0)
            if price and entry:
                pnl = (price - entry) / entry * 100
                if pnl <= -DEFENSE_LOSS_WARN_PCT:
                    score += 20
                    reasons.append(f"📉 진입가 대비 {pnl:.1f}% (방어 필요)")
                elif pnl >= DEFENSE_PROFIT_LOCK_PCT:
                    score += 10
                    reasons.append(f"📈 진입가 대비 +{pnl:.1f}% (익절 방어 권장)")
                # 손절선 근접
                if stop_loss and price <= stop_loss * 1.01:
                    score += 20
                    reasons.append("🛡 손절선 근접(1% 이내)")
        except Exception:
            pass

    except Exception:
        pass

    score = max(0, min(score, 100))
    return score, reasons

def run_entry_defense_monitor():
    """run_scan 루프에서 호출: 마감 구간에 entry_hit 종목의 리스크를 감지해 손익 방어 가이드 발송."""
    try:
        if not _entry_watch:
            return
        # 마감 구간이 아니면 불필요한 API 호출 줄이기
        if not _is_close_defense_window():
            return

        now_ts = time.time()
        use_nxt = (not is_market_open()) and is_nxt_open()

        for _k, w in list(_entry_watch.items()):
            if not isinstance(w, dict):
                continue
            if not w.get("entry_hit"):
                continue

            # 쿨다운(종목별)
            last = float(w.get("defense_last_ts", 0) or 0)
            if now_ts - last < DEFENSE_ALERT_COOLDOWN_SEC:
                continue

            code = w.get("code")
            name = w.get("name") or code
            entry = int(w.get("entry_price") or 0)
            stop  = int(w.get("stop_loss") or 0)
            if not code or not entry:
                continue

            # 현재가
            cur = get_nxt_stock_price(code) if use_nxt else get_stock_price(code)
            price = int((cur or {}).get("price") or 0)
            if not price:
                continue

            risk_score, reasons = _detect_defense_issues(code, name, entry, stop)
            if risk_score < 35 or not reasons:
                continue

            pnl = (price - entry) / entry * 100 if entry else 0.0

            # 가이드 구성(실전 수익 방어 중심)
            guide = []
            if pnl >= DEFENSE_PROFIT_LOCK_PCT:
                guide.append("✅ <b>수익 방어</b>: 1차 분할익절(예: 30~50%) + 잔량은 <b>진입가/단기저점 이탈 시 정리</b>")
                guide.append("✅ <b>트레일링</b>: 전일저가 또는 5분 저점 기준으로 손절선을 끌어올리기")
            else:
                guide.append("🛡 <b>손실 방어</b>: 손절선 엄수(이탈 시 기계적으로 정리) + 무리한 물타기 금지")
                guide.append("🛡 <b>리스크 발생</b>: 변동성 확대 구간이므로 진입/추가매수는 보수적으로")

            # 마감 임박 추가 코멘트
            if is_nxt_open() and not is_market_open():
                guide.append("🔵 <b>NXT 단독 시간</b>: 유동성 얇음 → 슬리피지/급변 가능, 보수적 대응 권장")
            else:
                guide.append("⏳ <b>장마감 임박</b>: 뉴스/공시 충격은 익일 갭으로 이어질 수 있어 방어 우선")
            parts = [
                f"🛡 <b>[손익 방어 알림]</b> (리스크 {risk_score}/100)",
                "━━━━━━━━━━━━━━━",
                f"<b>{name}</b>  <code>{code}</code>",
                f"현재가 <b>{price:,}</b> / 진입 {entry:,}  ({pnl:+.1f}%)",
                (f"손절 {stop:,}" if stop else ""),
                "━━━━━━━━━━━━━━━",
                *reasons[:4],
                "━━━━━━━━━━━━━━━",
                *guide[:4],
            ]
            msg = "\n".join([p for p in parts if p])
            send_with_chart_buttons(msg, code, name)

            # 기록
            w["defense_last_ts"] = now_ts

    except Exception as e:
        _log_error("run_entry_defense_monitor", e)

def send_with_chart_buttons(text: str, code: str, name: str):
    """
    텍스트 메시지 + 인라인 키보드 버튼(네이버 차트 링크) 전송
    버튼은 기기 기본 브라우저(외부)로 열림
    """
    safe_name = _resolve_stock_name(code, name)
    naver = f"https://finance.naver.com/item/fchart.naver?code={code}"
    keyboard = {
        "inline_keyboard": [[
            {"text": f"📈 {safe_name} 차트 보기 (네이버)", "url": naver},
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

def _tg_request(method: str, payload: dict, timeout: int = 10) -> dict | None:
    """Telegram Bot API 요청. 성공 시 response json 반환, 실패 시 None."""
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}",
            json=payload,
            timeout=timeout,
        )
        # Telegram은 실패 시에도 JSON을 주는 경우가 많음
        try:
            return r.json()
        except Exception:
            return None
    except Exception as e:
        print(f"⚠️ 텔레그램 오류: {e}")
        return None

def send(text: str, *, reply_markup: dict | None = None) -> int | None:
    """메시지 전송. 성공 시 message_id 반환."""
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    res = _tg_request("sendMessage", payload)
    try:
        if res and res.get("ok") and "result" in res:
            return res["result"].get("message_id")
    except Exception:
        pass
    return None

# =======================================================
# Crash guard (Step 1): unhandled exception hook
# =======================================================
_CRASH_NOTIFY_COOLDOWN_SEC = int(os.getenv("CRASH_NOTIFY_COOLDOWN_SEC", "1800") or "1800")
_last_crash_sig: str | None = None
_last_crash_ts: float = 0.0

def install_excepthook() -> None:
    """Unhandled 예외를 파일로 저장하고(영구저장), 텔레그램 알림을 쿨다운(기본 30분)으로 제한."""
    import sys, time, traceback as _tb
    from pathlib import Path

    def _handler(exc_type, exc, tb):
        global _last_crash_sig, _last_crash_ts
        try:
            # 1) crash log file
            data_dir = DATA_DIR  # already resolved earlier
            crash_dir = Path(data_dir) / "crash_logs"
            crash_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = f"crash_{ts}.txt"
            fpath = crash_dir / fname
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(_tb.format_exc())
            print(f"🚨 Unhandled exception saved: {fpath}", flush=True)

            # 2) cooldown notify
            sig = f"{exc_type.__name__}:{str(exc)[:200]}"
            now = time.time()
            if (_last_crash_sig != sig) or (now - _last_crash_ts > _CRASH_NOTIFY_COOLDOWN_SEC):
                _last_crash_sig, _last_crash_ts = sig, now
                try:
                    send(
                        f"🚨 봇 오류 감지\n"
                        f"- type: <b>{exc_type.__name__}</b>\n"
                        f"- msg: <code>{str(exc)[:250]}</code>\n"
                        f"- crash log: <code>{fname}</code>\n"
                        f"(같은 오류는 {_CRASH_NOTIFY_COOLDOWN_SEC//60}분에 1회만 알림)"
                    )
                except Exception:
                    pass
        except Exception:
            pass

        # keep default printing
        try:
            sys.__excepthook__(exc_type, exc, tb)
        except Exception:
            pass

    sys.excepthook = _handler

def edit_message(message_id: int, text: str, *, reply_markup: dict | None = None) -> bool:
    payload = {"chat_id": TELEGRAM_CHAT_ID, "message_id": message_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    res = _tg_request("editMessageText", payload)
    return bool(res and res.get("ok"))

def _load_dashboard_state() -> dict:
    try:
        with open(DASHBOARD_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_dashboard_state(state: dict) -> None:
    try:
        os.makedirs(os.path.dirname(DASHBOARD_STATE_FILE), exist_ok=True)
        _atomic_write_json(DASHBOARD_STATE_FILE, state)
    except Exception:
        pass

def update_dashboard(force: bool = False) -> None:
    # ensure MARKET_REGIME is populated; fall back to US signals if needed
    try:
        us = get_us_market_signals()
        if isinstance(us, dict) and us.get('us_regime'):
            MARKET_REGIME['label'] = us.get('us_regime') or MARKET_REGIME.get('label','neutral')
    except Exception:
        pass

    """대시보드 메시지(1개)를 편집 업데이트해서 메시지량 감소."""
    global _LAST_DASHBOARD_TS
    now = time.time()
    if (not force) and (now - _LAST_DASHBOARD_TS) < DASHBOARD_UPDATE_EVERY_SEC:
        return
    _LAST_DASHBOARD_TS = now

    tracked_n = 0
    try:
        tracked_n = len(_entry_watch.get("watch", {})) if isinstance(_entry_watch, dict) else 0
    except Exception:
        tracked_n = 0
    raw_regime = (MARKET_REGIME.get("label") or "neutral")
    regime = regime_label_ko(raw_regime)
    det = MARKET_REGIME.get("details", {}) or {}
    det_txt = ""
    try:
        fut = det.get("nasdaq_fut_pct")
        vix = det.get("vix")
        dxy = det.get("dxy")
        if fut is not None:
            det_txt = f" (FUT {float(fut):+.1f}% / VIX {vix} / DXY {dxy})"
    except Exception:
        det_txt = ""

    perf = ""
    try:
        perf = get_today_performance_summary()  # 있으면 사용
    except Exception:
        perf = ""

    text = (
        "📌 <b>운영 대시보드</b>\n"
        f"• 레짐: <b>{regime}</b>{det_txt}\n"
        f"• 진입 감시: <b>{tracked_n}</b> 종목\n"
    )
    if perf:
        text += f"• 오늘 성과: {perf}\n"
    text += f"• 업데이트: {datetime.now().strftime('%m-%d %H:%M')}\n"

    state = _load_dashboard_state()
    mid = state.get("message_id")
    if isinstance(mid, int):
        ok = edit_message(mid, text)
        if not ok:
            mid2 = send(text)
            if mid2:
                state["message_id"] = mid2
                _save_dashboard_state(state)
    else:
        mid2 = send(text)
        if mid2:
            state["message_id"] = mid2
            _save_dashboard_state(state)

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
    # v37.0: 슬라이스 할당으로 안전한 리스트 수정 (동시접근 경쟁 조건 제거)
    # 1시간 이상 된 항목 제거 + 최대 20개 유지
    fresh = [a for a in _pending_info_alerts if now - a["ts"] <= 3600][-20:]
    # 5분 이상 된 것만 발송 대상
    to_send = [a for a in fresh if now - a["ts"] >= 300]
    remaining = [a for a in fresh if now - a["ts"] < 300]
    _pending_info_alerts[:] = remaining  # 원자적 교체
    if not to_send: return
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
        block   += f"  📈 {_resolve_stock_name(r['code'], r.get('name',''))} <b>{r['change_rate']:+.1f}%</b>{vol_tag}{src_tag}\n"

    for r in flat[:3]:
        src_tag = " 🔗" if r.get("source") == "동적테마" else ""
        block  += f"  ➖ {_resolve_stock_name(r['code'], r.get('name',''))} {r['change_rate']:+.1f}%{src_tag}\n"

    return block + "━━━━━━━━━━━━━━━\n\n"

def send_alert(s: dict):
    s["name"] = _resolve_stock_name(s.get("code", ""), s.get("name", ""))
    # throttle repetitive alerts (reduce spam)
    try:
        st = s.get('signal_type','')
        if st in ('UPPER_LIMIT','NEAR_UPPER'):
            key = f"{st}:{s.get('code','')}"
            if not _throttle_ok(_LAST_ALERT_TS, key, 3600):
                return
    except Exception:
        pass

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
            inv   = get_investor_trend(code)
            f_net = inv.get("foreign_net",     0)
            i_net = inv.get("institution_net", 0)
            r_net = inv.get("retail_net",      0)
            # 3자 구도 우선 체크
            if f_net > 0 and i_net > 0 and r_net < 0:
                score += 30; signal_type = "STRONG_BUY"
                reasons.append(f"💎 외국인+기관 매수 / 개인 매도 (최강 수급구도) +30점")
            elif f_net > 0 and i_net > 0:
                score += 25; signal_type = "STRONG_BUY"
                reasons.append(f"✅ 외국인+기관 동시 순매수 +25점")
            elif f_net > 0:
                score += 10; reasons.append(f"🟡 외국인 순매수 ({f_net:+,}주) +10점")
            elif i_net > 0:
                score += 10; reasons.append(f"🟡 기관 순매수 ({i_net:+,}주) +10점")
            # 개인 수급 맥락 분석 (단순 악재 단정 X)
            if r_net > 0 and f_net < 0 and i_net < 0:
                cap_size = stock.get("cap_size") or "unknown"
                if cap_size == "unknown":
                    try:
                        _cp = get_stock_price(code)
                        cap_size = _cp.get("cap_size", "unknown")
                    except: pass
                retail_ev = eval_retail_signal(code, f_net, i_net, r_net, cap_size)
                if retail_ev:
                    score += retail_ev["score_adj"]
                    if retail_ev["score_adj"] != 0:
                        reasons.append(
                            f"{retail_ev['label']} {int(retail_ev['score_adj'] or 0):+d}점 — {retail_ev['detail']}"
                        )
                    else:
                        reasons.append(f"{retail_ev['label']} — {retail_ev['detail']}")
            elif f_net < 0 and i_net < 0:
                reasons.append(f"⚠️ 외국인({f_net:+,}) 기관({i_net:+,}) 동시 매도")
        except Exception as _e:
            _log_error(f"analyze_investor({stock.get('code', '')})", _e); inv = {}; f_net = 0; i_net = 0

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

    # v37.0: API 사전 캐싱 (get_stock_price 중복 호출 3→1회 절감)
    try: _cached_price = get_stock_price(code)
    except: _cached_price = {}

    # 전일 상한가 ⑨
    prev_upper = was_upper_limit_yesterday(code)
    if prev_upper: score+=10; reasons.append("🔁 전일 상한가 → 연속 상한가 가능성")

    # 거래량 Z-score ⑰
    try:
        cur_detail = _cached_price  # v37.0: 캐싱된 값 사용
        z = get_volume_zscore(code, cur_detail.get("today_vol",0))
        if z >= VOL_ZSCORE_MIN: score+=10; reasons.append(f"📊 거래량 이상 급증 (Z-score {z:.1f}σ)")
    except: pass

    # 섹터 모멘텀
    sector_info = calc_sector_momentum(code, stock.get("name",code))
    _w_sec = _dynamic.get("feat_w_sector", 1.0)
    sector_info["bonus"] = int(sector_info["bonus"] * _w_sec)
    if sector_info["bonus"]>0:
        score+=sector_info["bonus"]; reasons.append(sector_info["summary"])
        if sector_info.get("rising"):
            reasons.append("📌 동반 상승: " + ", ".join([f"{_resolve_stock_name(r['code'], r.get('name',''))} {r['change_rate']:+.1f}%" for r in sector_info["rising"][:4]]))
    elif sector_info.get("summary"):
        reasons.append(sector_info["summary"])

    # ── NXT 보정 (장 중에만, 백그라운드 영향 최소화) ──
    nxt_delta, nxt_reason = 0, ""
    try:
        nxt_delta, nxt_reason = nxt_score_bonus(code)
        if nxt_delta != 0:
            _w_nxt = _dynamic.get("feat_w_nxt", 1.0)
            score += int(nxt_delta * _w_nxt)
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

    # ── 미국 시장 점수 보정 ──
    us = {}  # v37.0: 초기화 (end-of-function 중복 fetch 제거)
    try:
        us = get_us_market_signals()
        us_adj = us.get("score_adj", 0)
        if us_adj != 0:
            score = max(0, score + us_adj)
            us_label = {"panic":"🔴 미국 패닉","risk_off":"🟠 미국 위험회피",
                        "neutral":"🔵 미국 중립","risk_on":"🟢 미국 위험선호"}
            reasons.append(f"{us_label.get(us.get('us_regime','neutral'),'🔵')} ({us_adj:+d}점)")
        if us.get("gap_signal") == "gap_down":
            reasons.append("⬇️ 내일 갭하락 가능성 (미국 약세)")
        elif us.get("gap_signal") == "gap_up":
            reasons.append("⬆️ 내일 갭상승 기대 (미국 강세)")
    except Exception as _e: _log_error("analyze_us", _e)

    # ── 공매도 잔고 비율 보정 ──
    short_ratio = 0.0  # v37.0: 초기화
    try:
        short_ratio = get_short_sell_ratio(code)
        if short_ratio >= 10:
            score -= 10
            reasons.append(f"⚠️ 공매도 잔고 {short_ratio:.1f}% — 반등 시 숏커버 기대 가능")
        elif short_ratio >= 5:
            score -= 5
            reasons.append(f"📉 공매도 잔고 {short_ratio:.1f}% — 주의")
    except: pass

    # ── 외국인+기관 연속 순매수 보정 ──
    f_days, i_days = 0, 0  # v37.0: 초기화
    try:
        f_days = get_foreign_consecutive_days(code)
        i_days = get_institution_consecutive_days(code)
        # 외국인+기관 동시 연속 매수 → 시너지 가중
        if f_days >= 3 and i_days >= 3:
            adj = min((f_days + i_days) * 2, 20)
            score += adj
            reasons.append(f"🔵 외국인 {f_days}일+기관 {i_days}일 동시 연속매수 (+{adj}점)")
        elif f_days >= 3:
            adj = min(f_days * 3, 15)
            score += adj
            reasons.append(f"🔵 외국인 {f_days}일 연속 순매수 (+{adj}점)")
        elif i_days >= 3:
            adj = min(i_days * 2, 10)
            score += adj
            reasons.append(f"🏦 기관 {i_days}일 연속 순매수 (+{adj}점)")
        elif f_days <= -3:
            adj = min(abs(f_days) * 3, 15)
            score -= adj
            reasons.append(f"🔴 외국인 {abs(f_days)}일 연속 순매도 (-{adj}점)")
        elif i_days <= -3:
            adj = min(abs(i_days) * 2, 10)
            score -= adj
            reasons.append(f"🔴 기관 {abs(i_days)}일 연속 순매도 (-{adj}점)")
    except: pass

    # ── 뉴스 심층 분석 (본문 + Claude API) ──
    try:
        _articles = fetch_news_for_stock(code, stock.get("name", code))
        if _articles:
            deep = analyze_news_deep(_articles, stock.get("name", code), code)
            adj  = int(deep.get("score_adj", 0) or 0)
            verd = deep.get("verdict", "중립")
            conf = deep.get("confidence", "low")
            conf_emoji = {"high":"🔍","mid":"📰","low":"📰"}.get(conf,"📰")

            if adj != 0:
                score += adj
                # 표면호재실질악재 특별 경고
                if verd == "표면호재실질악재":
                    reasons.append(f"⚠️ 표면호재실질악재 주의 ({deep.get('reason','')}) {adj:+d}점")
                elif verd == "표면악재실질호재":
                    reasons.append(f"💡 표면악재실질호재 ({deep.get('reason','')}) {adj:+d}점")
                elif adj > 0:
                    reasons.append(f"{conf_emoji} 뉴스 {verd} ({deep.get('reason','')}) {adj:+d}점")
                else:
                    reasons.append(f"{conf_emoji} 뉴스 {verd} ({deep.get('reason','')}) {adj:+d}점")

            # 리스크 포인트 있으면 추가 표시
            for rp in deep.get("risk_points", [])[:2]:
                reasons.append(f"  ⚠️ {rp}")
    except Exception as _e: _log_error(f"analyze_news({code})", _e)

    # ── 지정학 이벤트 보정 ──
    try:
        if _geo_event_state.get("active") and time.time() - _geo_event_state.get("ts",0) < 3600:
            si           = stock.get("sector_info") or {}
            stock_sector = si.get("theme", "") or si.get("sector", "")
            geo_unc      = _geo_event_state.get("uncertainty", "low")
            unc_label    = {"high":"🔴","mid":"🟠","low":"🟢"}

            # sector_directions 있으면 섹터별 개별 보정
            sec_dirs = _geo_event_state.get("sector_directions", [])
            matched  = False
            _geo_adj_applied = 0  # feature_flags 기록용
            if sec_dirs and stock_sector:
                for sd in sec_dirs:
                    sec_name = sd.get("sector", "")
                    if sec_name in stock_sector or stock_sector in sec_name:
                        adj = max(-15, min(sd.get("score_adj", 0), 15))
                        _dir = sd.get("direction", "중립")
                        _arrow = _DIR_DISPLAY.get(_dir, "―")
                        # 하락 섹터 + 상한가 아닌 신호 → 강한 패널티
                        if _dir == "하락" and signal_type not in ("UPPER_LIMIT", "STRONG_BUY"):
                            adj = min(adj, -8)
                        if adj != 0:
                            _w_geo = _dynamic.get("feat_w_geo", 1.0)
                            adj_weighted = int(adj * _w_geo)
                            score += adj_weighted
                            _geo_adj_applied = adj_weighted
                            reasons.append(
                                f"🌍 [{sec_name}] {_arrow}  "
                                f"({sd.get('reason','')}) {adj_weighted:+d}점"
                            )
                        elif _dir != "중립":
                            reasons.append(
                                f"🌍 [{sec_name}] {_arrow}  ({sd.get('reason','')})"
                            )
                        matched = True
                        break

            # sector_directions 없으면 전체 score_adj fallback
            if not matched:
                geo_sectors = _geo_event_state.get("sectors", [])
                geo_adj     = int(_geo_event_state.get("score_adj", 0) or 0)
                if stock_sector and (any(s in stock_sector for s in geo_sectors)
                                     or any(stock_sector in s for s in geo_sectors)):
                    if geo_adj != 0:
                        score += geo_adj
                        _geo_adj_applied = geo_adj
                        reasons.append(
                            f"🌍 지정학 관련 섹터 {unc_label.get(geo_unc,'')} {geo_adj:+d}점"
                        )
    except Exception as _e: _log_error(f"analyze_geo({code})", _e)

    # ── 테마 로테이션 보정 ──
    try:
        rotation  = detect_theme_rotation()
        si        = stock.get("sector_info") or {}
        theme_key = si.get("theme", "") or si.get("theme_key", "")
        if theme_key:
            theme_scores = rotation.get("themes", {})
            t_chg        = theme_scores.get(theme_key, 0)
            strong_themes = [k for k, v in rotation.get("strong", [])]
            weak_themes   = [k for k, v in rotation.get("weak",   [])]
            if theme_key in strong_themes:
                score += 8
                reasons.append(f"🔄 [{theme_key}] 테마 강세 ({t_chg:+.1f}%) +8점")
            elif theme_key in weak_themes:
                score -= 8
                reasons.append(f"🔄 [{theme_key}] 테마 약세 ({t_chg:+.1f}%) -8점")
    except: pass

    # ── ④ 실적 발표 필터 ──
    earnings = check_earnings_risk(code, stock.get("name", code))
    if earnings["risk"] == "high":
        reasons.append(earnings["desc"])
    elif earnings["risk"] == "warn":
        reasons.append(earnings["desc"])
        score = int(score * 0.85)   # 실적 발표 3일 전 → 점수 15% 감점
        if score < min_score: return {}

    # ── ⑤ DART 리스크 차단 필터 ──
    # 상한가(UPPER_LIMIT)는 이미 장중 확인된 종목이므로 예외
    _dart_r = check_dart_risk(code)
    if _dart_r["is_risk"] and signal_type not in ("UPPER_LIMIT",):
        print(f"  🚫 DART리스크차단 [{stock.get('name', code)}]: {_dart_r['title']}")
        return {}

    open_est     = price/(1+change_rate/100)
    _pullback_r  = _dynamic.get("entry_pullback_ratio", ENTRY_PULLBACK_RATIO)
    entry        = int((price-(price-open_est)*_pullback_r)/10)*10

    # ── ③ 손익비 동적 조정 ──
    stop, target, stop_pct, target_pct, atr_used = calc_dynamic_stop_target(code, entry)

    # ── 매물대/지지저항선 보정 ──
    try:
        vp = calc_volume_profile(code, entry)
        if vp.get("score_adj") != 0:
            score += vp["score_adj"]
            if vp.get("reason"): reasons.append(vp["reason"])
    except: pass

    # ── 공시 전 이상 거래량 보정 ──
    try:
        pre_dart = detect_pre_dart_volume(code, stock.get("name", code))
        if pre_dart.get("detected") and pre_dart.get("score_adj"):
            score += pre_dart["score_adj"]
            reasons.append(pre_dart["reason"])
    except: pass

    # ── 수급 이상 패턴 보정 ──
    try:
        cur_p     = _cached_price  # v37.0: 캐싱된 값 사용
        ask_qty   = cur_p.get("ask_qty", 0)
        bid_qty   = cur_p.get("bid_qty", 0)
        fp        = detect_force_pattern(
            code, stock.get("name", code),
            price=price, change_rate=change_rate, vol_ratio=vol_ratio,
            ask_qty=ask_qty, bid_qty=bid_qty
        )
        fp_adj = fp.get("total_adj", 0)
        if fp_adj != 0:
            score += fp_adj
        for p in fp.get("patterns", []):
            if p.get("score_adj", 0) != 0 or p.get("confidence") == "high":
                conf_emoji = {"high":"🔴","mid":"🟡","low":"⬜"}.get(p["confidence"],"⬜")
                reasons.append(
                    f"{conf_emoji} [{p['confidence'].upper()}] {p['label']} "
                    f"{int(p['score_adj'] or 0):+d}점 — {p['detail']}"
                )
        if fp.get("risk_flag"):
            reasons.append("⚠️ 수급 이탈 신호 감지 — 포지션 축소 검토")
    except Exception as _e:
        _log_error(f"detect_force({code})", _e)

    # 등급 계산
    if   score >= 80: grade = "A"
    elif score >= 60: grade = "B"
    else:             grade = "C"

    # ── ② 포지션 사이징 ──
    position = calc_position_size(signal_type, score, grade)

    # v37.0: 이미 위에서 가져온 값 재사용 (중복 API 호출 제거)
    return {"code":code,"name":stock.get("name",code),"price":price,
            "change_rate":change_rate,"volume_ratio":vol_ratio,
            "signal_type":signal_type,"score":score,"sector_info":sector_info,
            "entry_price":entry,"stop_loss":stop,"target_price":target,
            "stop_pct":stop_pct,"target_pct":target_pct,"atr_used":atr_used,
            "prev_upper":prev_upper,"reasons":reasons,"detected_at":datetime.now(),
            "nxt_delta": nxt_delta,
            "regime": regime_mode,
            "us_regime":    us.get("us_regime","neutral"),
            "gap_signal":   us.get("gap_signal","flat"),
            "foreign_days": f_days,
            "institution_days": i_days,
            "short_ratio":  short_ratio,
            "earnings_risk": earnings["risk"],
            "position": position,
            "indic": indic,
            "grade": grade,
            "dart_risk": _dart_r["is_risk"]}

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
                reasons.append("📌 동반 상승: "+"".join([f"{_resolve_stock_name(r['code'], r.get('name',''))} {r['change_rate']:+.1f}%" for r in sector_info["rising"][:4]]))
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
            title    = title_el.get_text(strip=True)
            t        = time_el.get_text(strip=True) if time_el else ""
            href     = title_el.get("href", "")
            # 절대 URL 변환
            if href and href.startswith("/"):
                href = "https://finance.naver.com" + href
            if len(title) > 5:
                news.append({"title": title, "time": t, "url": href})
            if len(news) >= 3: break
    except: pass
    _news_reverse_cache[code] = {"news": news, "ts": time.time()}
    return news

_news_alert_sent: dict = {}   # code → ts (뉴스 알림 쿨다운, 30분)

# ============================================================
# 🚨 DART 리스크 차단 + 보유 종목 뉴스 감시 (v33.0)
# ============================================================
_dart_risk_cache: dict = {}   # code → {is_risk, title, ts}  (10분 캐시)
_carry_news_watch: dict = {}  # code → last_check_ts          (30분 쿨다운)


def check_dart_risk(code: str) -> dict:
    """
    종목별 최근 5일 DART 공시 → 리스크 키워드 있으면 True 반환
    analyze() 내 매수 신호 최종 차단 판단에 사용
    returns: {"is_risk": bool, "title": str}
    """
    if not DART_API_KEY:
        return {"is_risk": False, "title": ""}

    now = time.time()
    cached = _dart_risk_cache.get(code)
    if cached and now - cached.get("ts", 0) < 600:   # 10분 캐시
        return cached

    result = {"is_risk": False, "title": "", "ts": now}
    try:
        today = datetime.now().strftime("%Y%m%d")
        bgn   = (datetime.now() - timedelta(days=5)).strftime("%Y%m%d")
        resp  = requests.get(
            "https://opendart.fss.or.kr/api/list.json",
            params={
                "crtfc_key":  DART_API_KEY,
                "bgn_de":     bgn,
                "end_de":     today,
                "stock_code": code,
                "page_count": 20,
            },
            timeout=8
        )
        for item in resp.json().get("list", []):
            title = item.get("report_nm", "")
            if any(kw in title for kw in DART_RISK_KEYWORDS):
                result["is_risk"] = True
                result["title"]   = title
                break
    except Exception as e:
        print(f"  ⚠️ DART리스크체크오류 [{code}]: {e}")

    _dart_risk_cache[code] = result
    return result

def news_block_for_alert(code: str, name: str) -> str:
    """알림 직후 백그라운드로 뉴스 역추적 — 30분 쿨다운으로 중복 크롤링 방지"""
    now = time.time()
    if now - _news_alert_sent.get(code, 0) < 1800: return  # 30분 쿨다운
    _news_alert_sent[code] = now
    def _fetch():
        try:
            articles = fetch_news_for_stock(code, name)
            if not articles: return

            # 심층 분석
            deep  = analyze_news_deep(articles, name, code)
            verd  = deep.get("verdict","중립")
            adj   = deep.get("score_adj",0)
            rsn   = deep.get("reason","")
            rps   = deep.get("risk_points",[])

            verd_emoji = {
                "실질호재":       "✅",
                "실질악재":       "❌",
                "표면호재실질악재":"⚠️",
                "표면악재실질호재":"💡",
                "불확실":         "❓",
                "중립":           "📰",
            }.get(verd, "📰")

            lines = "\n".join(f"  📰 {a['title']}  <i>{a['time']}</i>" for a in articles)

            risk_text = ""
            if rps:
                risk_text = "\n⚠️ 주의사항:\n" + "\n".join(f"  🔸 {r}" for r in rps[:3])

            send_with_chart_buttons(
                f"{verd_emoji} <b>[{name} 뉴스 분석]</b>  {verd}  {adj:+d}점\n"
                f"━━━━━━━━━━━━━━━\n"
                f"{lines}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"💡 {rsn}"
                f"{risk_text}",
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

def fetch_maekyung_news() -> list:
    """매일경제 RSS (가능하면)"""
    # 일부 환경에서 차단될 수 있어 실패 시 빈 리스트 반환
    url_candidates = [
        "https://www.mk.co.kr/rss/30000001/",   # 경제/증권 (변경될 수 있음)
        "https://www.mk.co.kr/rss/50300009/",   # 증권 (변경될 수 있음)
    ]
    items = []
    for url in url_candidates:
        items = _fetch_rss_headlines(url, max_items=10)
        if items:
            break
    return items

def fetch_google_news_kr_market() -> list:
    """Google News RSS (한국 증시/경제 쿼리)"""
    q = "KOSPI OR 코스피 OR 코스닥 OR 증시 OR 주식"
    url = f"https://news.google.com/rss/search?q={requests.utils.quote(q)}&hl=ko&gl=KR&ceid=KR:ko"
    return _fetch_rss_headlines(url, max_items=10)

def fetch_google_news_semicon_export() -> list:
    """Google News RSS (반도체/수출규제/지정학 키워드)"""
    q = "반도체 OR 수출규제 OR 지정학 OR 전쟁 OR 유가"
    url = f"https://news.google.com/rss/search?q={requests.utils.quote(q)}&hl=ko&gl=KR&ceid=KR:ko"
    return _fetch_rss_headlines(url, max_items=10)


def fetch_all_news() -> list:
    # v37.0: Queue 기반 스레드 안전 수집 (list.extend 경쟁 조건 제거)
    from queue import Queue
    _q = Queue()
    threads = [
        threading.Thread(target=lambda fn=f: _q.put(fn()), daemon=True)
        for f in (fetch_naver_news, fetch_hankyung_news, fetch_yonhap_news, fetch_maekyung_news, fetch_google_news_kr_market, fetch_google_news_semicon_export)
    ]
    for t in threads: t.start()
    for t in threads: t.join(timeout=8)
    results = []
    while not _q.empty():
        try: results.extend(_q.get_nowait())
        except: break
    return list(dict.fromkeys(results))




# ============================================================

# 🕵️ 수급 이상 패턴 감지 (세력 흔적 추적)
# ============================================================
# ※ 주의: 아래 감지 신호는 통계적 이상 패턴이며,
#         실제 세력 존재를 확증하지 않습니다.
#         투자 판단의 보조 지표로만 활용하세요.
# ============================================================

_force_cache: dict = {}   # code → {result, ts}

def _get_minute_data(code: str, count: int = 30) -> list:
    """
    KIS 분봉 데이터 조회 (최근 count개).
    반환: [{"time": str, "open": int, "close": int, "volume": int}, ...]
    """
    try:
        data = _safe_get(
            f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice",
            "FHKST03010200",
            {
                "FID_ETC_CLS_CODE":    "",
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD":      code,
                "FID_INPUT_HOUR_1":    datetime.now().strftime("%H%M%S"),
                "FID_PW_DATA_INCU_YN": "N",
            }
        )
        items = data.get("output2", [])
        result = []
        for i in items[:count]:
            t   = i.get("stck_cntg_hour", "")
            c   = int(i.get("stck_prpr",   0) or 0)
            v   = int(i.get("cntg_vol",     0) or 0)
            o   = int(i.get("stck_oprc",    0) or 0)
            if c and v:
                result.append({"time": t, "open": o, "close": c, "volume": v})
        return result
    except:
        return []

def detect_force_pattern(code: str, name: str,
                         price: float = 0,
                         change_rate: float = 0,
                         vol_ratio: float = 0,
                         ask_qty: int = 0,
                         bid_qty: int = 0) -> dict:
    """
    수급 이상 패턴 종합 감지.

    반환: {
        patterns: [
            {
                type: str,          # 패턴 유형
                label: str,         # 표시 레이블
                confidence: str,    # "high"/"mid"/"low"
                score_adj: int,     # 점수 보정
                detail: str,        # 상세 설명
            }
        ],
        total_adj: int,         # 합산 점수 보정
        summary: str,           # 텔레그램 요약
        risk_flag: bool,        # 세력 이탈(dump) 의심
    }
    """
    cached = _force_cache.get(code)
    if cached and time.time() - cached.get("ts", 0) < 600:  # 10분 캐시
        return cached

    patterns  = []
    total_adj = 0
    risk_flag = False

    # ─────────────────────────────────────────────
    # 패턴 1: 호가 비대칭 (매수벽/매도벽)
    # ─────────────────────────────────────────────
    try:
        if ask_qty > 0 and bid_qty > 0:
            ratio = bid_qty / ask_qty  # >1 → 매수 우위
            if ratio >= 3.0:
                patterns.append({
                    "type":       "bid_wall",
                    "label":      "📊 매수벽 형성",
                    "confidence": "mid",
                    "score_adj":  +8,
                    "detail":     f"매수잔량 {ratio:.1f}배 우위 (매수:{bid_qty:,} vs 매도:{ask_qty:,}) — 단기 지지 가능",
                })
                total_adj += 8
            elif ratio >= 2.0:
                patterns.append({
                    "type":       "bid_wall",
                    "label":      "📊 매수 우위",
                    "confidence": "low",
                    "score_adj":  +4,
                    "detail":     f"매수잔량 {ratio:.1f}배 우위 — 참고용",
                })
                total_adj += 4
            elif ratio <= 0.3:
                # 매도잔량 압도적 → 매도벽 (세력 이탈 가능성)
                patterns.append({
                    "type":       "ask_wall",
                    "label":      "⚠️ 매도벽 감지",
                    "confidence": "mid",
                    "score_adj":  -8,
                    "detail":     f"매도잔량 {1/ratio:.1f}배 우위 — 상승 저항 또는 세력 이탈 가능성",
                })
                total_adj -= 8
                risk_flag = True
    except:
        pass

    # ─────────────────────────────────────────────
    # 패턴 2: 일봉 매집 패턴 (거래량↑ + 가격 횡보)
    # ─────────────────────────────────────────────
    try:
        daily = get_daily_data(code, 30)
        if len(daily) >= 10:
            closes  = [int(d.get("stck_clpr", 0)) for d in daily if d.get("stck_clpr")]
            volumes = [int(d.get("acml_vol",  0)) for d in daily if d.get("acml_vol")]

            if len(closes) >= 10 and len(volumes) >= 10:
                # 최근 5일 vs 이전 20일 비교
                recent_vol = sum(volumes[-5:]) / 5
                base_vol   = sum(volumes[-25:-5]) / 20 if len(volumes) >= 25 else sum(volumes[:-5]) / max(len(volumes)-5, 1)

                recent_hi  = max(closes[-5:])
                recent_lo  = min(closes[-5:])
                price_range_pct = (recent_hi - recent_lo) / recent_lo * 100 if recent_lo else 0

                vol_surge   = recent_vol / base_vol if base_vol else 1
                is_sideways = price_range_pct <= 4.0   # 최근 5일 가격 횡보 ±2%

                if vol_surge >= 2.5 and is_sideways:
                    conf = "high" if vol_surge >= 4.0 else "mid"
                    adj  = +12 if conf == "high" else +8
                    patterns.append({
                        "type":       "accumulation",
                        "label":      "🔍 매집 패턴 의심",
                        "confidence": conf,
                        "score_adj":  adj,
                        "detail":     (f"거래량 {vol_surge:.1f}배 급증 + 가격 횡보 {price_range_pct:.1f}% "
                                       f"(5일) — 통계적 이상, 확증 아님"),
                    })
                    total_adj += adj

                # 주가↓ + 거래량↑ → 저점 매집 가능성
                price_5d_chg = (closes[-1] - closes[-5]) / closes[-5] * 100 if closes[-5] else 0
                if price_5d_chg <= -3.0 and vol_surge >= 2.0:
                    patterns.append({
                        "type":       "bottom_accumulation",
                        "label":      "💡 하락 중 거래량 역행",
                        "confidence": "mid",
                        "score_adj":  +6,
                        "detail":     (f"주가 {price_5d_chg:.1f}% 하락에도 거래량 {vol_surge:.1f}배 "
                                       f"— 저점 매집 가능성 (역발상 신호)"),
                    })
                    total_adj += 6

    except:
        pass

    # ─────────────────────────────────────────────
    # 패턴 3: 스마트머니 역방향 (외국인↓+기관↑)
    # ─────────────────────────────────────────────
    try:
        inv    = get_investor_trend(code)
        f_net  = inv.get("foreign_net",     0)
        i_net  = inv.get("institution_net", 0)
        r_net  = inv.get("retail_net",      0)  # 개인

        # 기관 대규모 매수 + 외국인 매도 → 기관 주도 수급
        if i_net >= 50000 and f_net < 0:
            patterns.append({
                "type":       "smart_money_in",
                "label":      "🏦 기관 주도 매수",
                "confidence": "high",
                "score_adj":  +10,
                "detail":     (f"기관 +{i_net:,}주 / 외국인 {f_net:,}주 — "
                               f"기관이 외국인 매물 흡수"),
            })
            total_adj += 10

        # 외국인 대규모 매수 + 기관 매도 → 외국인 주도
        elif f_net >= 50000 and i_net < 0:
            patterns.append({
                "type":       "foreign_smart_money",
                "label":      "🌐 외국인 주도 매수",
                "confidence": "high",
                "score_adj":  +10,
                "detail":     (f"외국인 +{f_net:,}주 / 기관 {i_net:,}주 — "
                               f"외국인 단독 수급"),
            })
            total_adj += 10

        # 외국인+기관 동시 매수 + 개인 매도 → 가장 강한 신호
        if f_net >= 30000 and i_net >= 30000 and r_net < 0:
            patterns.append({
                "type":       "institutional_vs_retail",
                "label":      "💎 기관+외국인 동시 매수 / 개인 매도",
                "confidence": "high",
                "score_adj":  +12,
                "detail":     (f"외국인 +{f_net:,}주 + 기관 +{i_net:,}주 매수 "
                               f"/ 개인 {r_net:,}주 매도 — "
                               f"개인 물량을 기관+외국인이 흡수하는 구도"),
            })
            total_adj += 12

        # 개인만 대량 매수 → 맥락 분석 후 판단
        if r_net >= 100000 and f_net < 0 and i_net < 0:
            cap_size = "unknown"
            try:
                _cp = get_stock_price(code)
                cap_size = _cp.get("cap_size", "unknown")
            except: pass
            retail_ev = eval_retail_signal(code, f_net, i_net, r_net, cap_size)
            if retail_ev:
                adj = retail_ev.get("score_adj", 0)
                patterns.append({
                    "type":       "retail_buying_context",
                    "label":      retail_ev["label"],
                    "confidence": retail_ev["confidence"],
                    "score_adj":  adj,
                    "detail":     retail_ev["detail"],
                })
                total_adj += adj
                if adj < 0:
                    risk_flag = True

        # 외국인+기관 동시 대규모 매도 → 이탈 가능성
        elif f_net <= -50000 and i_net <= -50000:
            patterns.append({
                "type":       "smart_money_out",
                "label":      "🔴 외국인+기관 동시 이탈",
                "confidence": "high",
                "score_adj":  -12,
                "detail":     (f"외국인 {f_net:,}주 + 기관 {i_net:,}주 동시 매도"),
            })
            total_adj -= 12
            risk_flag = True

    except:
        pass

    # ─────────────────────────────────────────────
    # 패턴 4: 장 막판 대량 체결 (다음날 갭상승 예측)
    # ─────────────────────────────────────────────
    try:
        now_h = datetime.now().hour
        now_m = datetime.now().minute
        # 14:50~15:20 사이에만 체크
        if (now_h == 14 and now_m >= 50) or (now_h == 15 and now_m <= 20):
            mins = _get_minute_data(code, count=30)
            if len(mins) >= 10:
                # 전체 평균 분당 거래량
                avg_vol = sum(m["volume"] for m in mins) / len(mins)
                # 마지막 5분 거래량
                last5_vol = sum(m["volume"] for m in mins[:5]) / 5  # 최신순
                surge_ratio = last5_vol / avg_vol if avg_vol else 1

                if surge_ratio >= 3.0:
                    conf = "high" if surge_ratio >= 5.0 else "mid"
                    adj  = +10 if conf == "high" else +6
                    patterns.append({
                        "type":       "closing_surge",
                        "label":      "⏰ 장 막판 대량체결",
                        "confidence": conf,
                        "score_adj":  adj,
                        "detail":     (f"마감 직전 분당 거래량 {surge_ratio:.1f}배 급증 — "
                                       f"다음날 갭상승 가능성 (확증 아님)"),
                    })
                    total_adj += adj
    except:
        pass

    # ─────────────────────────────────────────────
    # 패턴 5: 연속 양봉 + 거래량 계단식 증가
    # ─────────────────────────────────────────────
    try:
        daily = get_daily_data(code, 15)
        if len(daily) >= 7:
            closes  = [int(d.get("stck_clpr", 0)) for d in daily[-7:] if d.get("stck_clpr")]
            opens   = [int(d.get("stck_oprc", 0)) for d in daily[-7:] if d.get("stck_oprc")]
            volumes = [int(d.get("acml_vol",  0)) for d in daily[-7:] if d.get("acml_vol")]

            if len(closes) >= 5 and len(volumes) >= 5:
                # 최근 3일 연속 양봉 여부
                bull_days = sum(1 for i in range(min(3, len(closes)))
                                if i < len(opens) and closes[-(i+1)] > opens[-(i+1)])
                # 거래량 계단식 증가 (매일 전날보다 많음)
                vol_staircase = all(volumes[-(i+1)] > volumes[-(i+2)]
                                    for i in range(min(3, len(volumes)-1)))

                if bull_days >= 3 and vol_staircase:
                    patterns.append({
                        "type":       "staircase_volume",
                        "label":      "📶 거래량 계단식 증가",
                        "confidence": "mid",
                        "score_adj":  +8,
                        "detail":     (f"연속 {bull_days}일 양봉 + 거래량 매일 증가 — "
                                       f"상승 탄력 유지 (통계적 강세 패턴)"),
                    })
                    total_adj += 8

    except:
        pass

    # ─────────────────────────────────────────────
    # 패턴 6: 분봉 일정 간격 매수 (자동 분할매수 의심)
    # ─────────────────────────────────────────────
    try:
        if is_market_open():
            mins = _get_minute_data(code, count=60)
            if len(mins) >= 20:
                # 분당 거래량 목록 (최신→과거 순)
                vols = [m["volume"] for m in mins]
                avg  = sum(vols) / len(vols)
                # 일정 간격(5분마다) 거래량 급등 패턴
                spike_intervals = []
                for i in range(0, len(vols)-5, 5):
                    window = vols[i:i+5]
                    if max(window) >= avg * 2.5:
                        spike_intervals.append(i)
                # 3개 이상 간격에서 스파이크 → 분할매수 패턴
                if len(spike_intervals) >= 3:
                    patterns.append({
                        "type":       "interval_buying",
                        "label":      "🤖 일정 간격 분할매수 패턴",
                        "confidence": "mid",
                        "score_adj":  +7,
                        "detail":     (f"5분 간격으로 {len(spike_intervals)}회 거래량 급등 감지 — "
                                       f"알고리즘 또는 세력 분할매수 패턴 의심 (확증 아님)"),
                    })
                    total_adj += 7

                # 분봉 고점 낮아짐 + 거래량 증가 → dump 징후
                closes_min = [m["close"] for m in mins[:20]]
                vols_min   = [m["volume"] for m in mins[:20]]
                if len(closes_min) >= 10 and len(vols_min) >= 10:
                    # 최근 10분 고점이 이전 10분 고점보다 낮음
                    recent_hi = max(closes_min[:10])
                    prev_hi   = max(closes_min[10:])
                    recent_vol = sum(vols_min[:10]) / 10
                    prev_vol   = sum(vols_min[10:]) / 10
                    if recent_hi < prev_hi * 0.99 and recent_vol > prev_vol * 1.5:
                        patterns.append({
                            "type":       "distribution",
                            "label":      "🔻 고점 낮아짐 + 거래량 증가",
                            "confidence": "mid",
                            "score_adj":  -8,
                            "detail":     (f"분봉 고점 {(recent_hi/prev_hi-1)*100:.1f}% 하락에도 "
                                           f"거래량 {recent_vol/prev_vol:.1f}배 증가 — "
                                           f"분산(dump) 초기 징후 가능성"),
                        })
                        total_adj -= 8
                        risk_flag  = True
    except:
        pass

    # ─────────────────────────────────────────────
    # 결과 종합
    # ─────────────────────────────────────────────
    total_adj = max(-20, min(total_adj, 20))  # -20~+20 범위 제한

    # 신뢰도별 이모지 및 설명
    CONF_EMOJI = {"high": "🔴", "mid": "🟡", "low": "⬜"}
    CONF_KOR   = {"high": "신뢰높음", "mid": "참고용", "low": "참고용"}

    summary_lines = []
    for p in patterns:
        ce  = CONF_EMOJI.get(p["confidence"], "⬜")
        ck  = CONF_KOR.get(p["confidence"], "참고용")
        adj = f"{int(p['score_adj'] or 0):+d}점" if p["score_adj"] != 0 else ""
        summary_lines.append(
            f"{ce} {p['label']} {adj} [{ck}]\n"
            f"     └ {p['detail']}"
        )

    summary = "\n".join(summary_lines) if summary_lines else ""

    result = {
        "patterns":  patterns,
        "total_adj": total_adj,
        "summary":   summary,
        "risk_flag": risk_flag,
        "ts":        time.time(),
    }
    _force_cache[code] = result
    return result

# ============================================================
# 🌍 지정학 이벤트 다중 주체 분석 (Claude API)
# ============================================================
_GEO_KEYWORDS = [
    # 전쟁/분쟁
    "전쟁","전투","공습","미사일","폭격","침공","분쟁","교전","충돌","군사",
    # 제재/경제
    "제재","봉쇄","관세","무역전쟁","수출통제","금수",
    # 외교
    "협상","협정","회담","정상회담","외교","단교","추방",
    # 주요 국가/지역
    "이란","러시아","중국","북한","이스라엘","팔레스타인","우크라이나",
    "대만","가자","중동","NATO","OPEC",
    # 에너지
    "유가","원유","석유","천연가스","LNG","OPEC","감산","증산",
]

# 지정학 이벤트 → 관련 섹터 자동 매핑
# 지정학 섹터 방향 화살표 (화살표만, 텍스트 없음)
_DIR_DISPLAY = {
    "상승": "🔺",   # 상향 (기존)
    "하락": "🔽",   # 하락(파란색) - Telegram은 글자 색상 불가, 이모지로 구현
    "중립": "▶",   # 중립
}

# 섹터명 → 관련 종목 매핑
# THEME_MAP + 추가 섹터별 대표 종목 (코드, 이름) 풀
_GEO_SECTOR_STOCKS: dict = {
    "방산":          [("012450","한화에어로스페이스"), ("047810","한국항공우주"), ("064350","현대로템"), ("042660","한화오션"), ("000970","중앙첨단소재")],
    "항공우주":      [("012450","한화에어로스페이스"), ("047810","한국항공우주"), ("272450","항공우주산업"), ("000670","영풍")],
    "정유":          [("010950","S-Oil"), ("078930","GS"), ("096770","SK이노베이션"), ("267250","HD현대"), ("004020","현대제철")],
    "에너지":        [("010950","S-Oil"), ("078930","GS"), ("034020","두산에너빌리티"), ("298040","효성중공업"), ("071970","STX중공업")],
    "화학":          [("051910","LG화학"), ("011170","롯데케미칼"), ("096770","SK이노베이션"), ("004000","롯데정밀화학"), ("006400","삼성SDI")],
    "반도체":        [("000660","SK하이닉스"), ("005930","삼성전자"), ("042700","한미반도체"), ("403870","HPSP"), ("357780","솔브레인")],
    "IT":            [("005930","삼성전자"), ("066570","LG전자"), ("035420","NAVER"), ("035720","카카오"), ("000660","SK하이닉스")],
    "전자":          [("005930","삼성전자"), ("066570","LG전자"), ("009150","삼성전기"), ("020150","율촌화학"), ("011070","LG이노텍")],
    "자동차":        [("005380","현대차"), ("000270","기아"), ("012330","현대모비스"), ("204320","만도"), ("010140","삼성중공업")],
    "조선":          [("042660","한화오션"), ("009540","HD한국조선해양"), ("010140","삼성중공업"), ("267250","HD현대")],
    "철강":          [("005490","POSCO홀딩스"), ("004020","현대제철"), ("001230","동국제강"), ("002220","한일철강")],
    "수출주":        [("005380","현대차"), ("000270","기아"), ("005930","삼성전자"), ("000660","SK하이닉스"), ("051910","LG화학")],
    "금융":          [("105560","KB금융"), ("055550","신한지주"), ("086790","하나금융지주"), ("316140","우리금융지주")],
    "금융·보험":     [("105560","KB금융"), ("055550","신한지주"), ("000810","삼성화재"), ("001450","현대해상"), ("086790","하나금융지주")],
    "보험":          [("000810","삼성화재"), ("001450","현대해상"), ("000370","한화손해보험"), ("005830","DB손해보험")],
    "은행":          [("105560","KB금융"), ("055550","신한지주"), ("086790","하나금융지주"), ("316140","우리금융지주"), ("024110","기업은행")],
    "증권":          [("005940","NH투자증권"), ("016360","삼성증권"), ("006800","미래에셋증권"), ("039490","키움증권"), ("001510","SK증권")],
    "해운·물류":     [("011200","HMM"), ("000120","CJ대한통운"), ("117930","한진"), ("006800","미래에셋증권")],
    "해운":          [("011200","HMM"), ("117930","한진"), ("005880","대한해운"), ("000480","조선내화")],
    "항공":          [("003490","대한항공"), ("020560","아시아나항공"), ("272450","제주항공")],
    "건설":          [("000720","현대건설"), ("047040","대우건설"), ("012630","HDC현대산업개발"), ("010780","아이에스동서")],
    "곡물":          [("007310","오뚜기"), ("003230","삼양식품"), ("097950","CJ제일제당"), ("271560","오리온")],
    "바이오":        [("207940","삼성바이오로직스"), ("068270","셀트리온"), ("196170","알테오젠"), ("009420","한올바이오파마")],
    "2차전지":       [("086520","에코프로"), ("247540","에코프로비엠"), ("006400","삼성SDI"), ("051910","LG화학"), ("373220","LG에너지솔루션")],
    "원전":          [("017800","현대엘리베이터"), ("071970","STX중공업"), ("298040","효성중공업"), ("034020","두산에너빌리티")],
    "디스플레이":    [("034220","LG디스플레이"), ("067160","아프리카TV"), ("028050","삼성SDI")],
    "반도체·디스플레이": [("000660","SK하이닉스"), ("005930","삼성전자"), ("034220","LG디스플레이"), ("042700","한미반도체")],
}

def _get_geo_sector_stocks(sector_name: str, max_n: int = 3) -> list:
    """
    섹터명으로 관련 종목 조회.
    _GEO_SECTOR_STOCKS 직접 매핑 + THEME_MAP 섹터 키워드 매칭.
    returns: [(code, name), ...]
    """
    # 1. 직접 매핑
    if sector_name in _GEO_SECTOR_STOCKS:
        return _GEO_SECTOR_STOCKS[sector_name][:max_n]

    # 2. 부분 매핑 (예: "에너지·정유" → "정유" 규칙 활용)
    for key, stocks in _GEO_SECTOR_STOCKS.items():
        if key in sector_name or sector_name in key:
            return stocks[:max_n]

    # 3. THEME_MAP 섹터 키워드 매칭
    for theme_key, theme_info in THEME_MAP.items():
        if sector_name in theme_info.get("sectors", []) or            any(s in sector_name for s in theme_info.get("sectors", [])):
            return theme_info["stocks"][:max_n]

    # 4. 동적 테마 매칭
    for tk, ti in _dynamic_theme_map.items():
        if sector_name in ti.get("sectors", []) or            any(s in sector_name for s in ti.get("sectors", [])):
            return [(s[0], s[1]) for s in ti.get("stocks", [])][:max_n]

    return []

def _get_geo_sector_history(sector_name: str, stock_list: list) -> str:
    """
    v37.0: 지정학 섹터 종목의 과거 신호 이력 조회.
    signal_log에서 같은 종목 + 같은 섹터의 완료된 신호를 찾아
    승률, 평균 수익률, 최근 사례를 반환.

    Parameters:
        sector_name: 섹터명 (예: "방산", "정유")
        stock_list:  [(code, name), ...] — _get_geo_sector_stocks 결과

    Returns:
        텔레그램 표시용 문자열 ("" = 이력 없음)
    """
    try:
        with open(SIGNAL_LOG_FILE, "r") as f:
            data = json.load(f)
    except:
        return ""

    if not data or not stock_list:
        return ""

    stock_codes = {code for code, name in stock_list}
    stock_names = {name for code, name in stock_list}

    # 1단계: 같은 종목 코드로 완료된 신호 찾기
    matched = []
    for log_key, rec in data.items():
        if rec.get("status") == "추적중":
            continue
        pnl = rec.get("pnl_pct", 0)
        if pnl == 0 and not rec.get("exit_price"):
            continue

        code = rec.get("code", "")
        name = rec.get("name", "")
        s_theme = rec.get("sector_theme", "")

        # 직접 종목 매칭 또는 같은 섹터 테마 매칭
        is_direct = code in stock_codes
        is_sector = (sector_name and s_theme and
                     (sector_name in s_theme or s_theme in sector_name))
        is_geo    = rec.get("feature_flags", {}).get("geo_active", False)

        if is_direct or (is_sector and is_geo):
            matched.append({
                "code":  code,
                "name":  name,
                "pnl":   round(pnl, 1),
                "date":  rec.get("detect_date", ""),
                "geo":   is_geo,
                "direct": is_direct,
            })

    if not matched:
        return ""

    # 통계 계산
    total  = len(matched)
    wins   = sum(1 for m in matched if m["pnl"] > 0)
    losses = sum(1 for m in matched if m["pnl"] <= 0)
    avg_pnl = round(sum(m["pnl"] for m in matched) / total, 1) if total else 0
    win_rate = round(wins / total * 100) if total else 0

    # 최근 사례 (최대 3건, 날짜 역순)
    recent = sorted(matched, key=lambda x: x["date"], reverse=True)[:3]

    # 포맷팅
    win_emoji = "🟢" if win_rate >= 60 else ("🟡" if win_rate >= 40 else "🔴")
    line1 = f"│  {win_emoji} 과거 유사: {total}건 중 {wins}건↑ ({win_rate}%) 평균{avg_pnl:+.1f}%"

    examples = []
    for r in recent:
        d_str = ""
        if r["date"] and len(r["date"]) == 8:
            d_str = f"({r['date'][4:6]}/{r['date'][6:8]})"
        pnl_str = f"{r['pnl']:+.1f}%"
        geo_mark = "🌍" if r["geo"] else ""
        examples.append(f"{_resolve_stock_name(r['code'], r.get('name',''))}{geo_mark} {pnl_str}{d_str}")

    line2 = "│     " + " | ".join(examples) if examples else ""

    result = line1
    if line2:
        result += "\n" + line2
    return result

_GEO_SECTOR_MAP = {
    "전쟁|전투|공습|미사일|폭격|침공|교전|충돌|군사": ["방산", "항공우주"],
    "이란|OPEC|유가|원유|석유|천연가스|LNG|감산|증산": ["정유", "에너지", "화학"],
    "러시아|우크라이나": ["방산", "에너지", "곡물"],
    "중국|대만|반도체|수출통제": ["반도체", "IT", "전자"],
    "제재|봉쇄|관세|무역전쟁|금수": ["수출주", "화학", "철강"],
    "이스라엘|팔레스타인|가자|중동": ["방산", "정유"],
    "북한": ["방산", "건설"],
}

_geo_cache: dict = {}  # keyword_hash → {result, ts}

def _strip_html(text: str) -> str:
    try:
        # 매우 단순한 HTML 제거 (RSS description에 종종 포함)
        import re as _re
        text = _re.sub(r"<[^>]+>", " ", text or "")
        text = _re.sub(r"\s+", " ", text).strip()
        return text
    except Exception:
        return (text or "").strip()

def _fetch_rss_headlines(url: str, max_items: int = 10) -> list:
    """RSS 피드에서 헤드라인 수집 (title + description 요약 포함)

    - RSS/Atom은 대개 XML이므로 HTML 파서로 파싱하면 bs4가 XMLParsedAsHTMLWarning 경고를 띄울 수 있음.
    - 운영 로그 노이즈를 줄이고 파싱 신뢰성을 올리기 위해 표준 XML 파서(ElementTree)를 우선 사용.
    - XML이 깨진(비정상) 소스는 최후에만 BeautifulSoup(html.parser)로 fallback.
    """
    try:
        resp = requests.get(url, timeout=12, headers=_random_ua())
        if resp.status_code != 200:
            return []

        xml_text = (resp.text or "").strip()
        if not xml_text:
            return []

        # 1) XML 우선 파싱 (경고/의존성 없이 안정적)
        try:
            root = ET.fromstring(xml_text)

            # RSS: <item>, Atom: <entry>
            items = root.findall(".//{*}item")
            if not items:
                items = root.findall(".//{*}entry")

            titles = []
            for it in items[:max_items]:
                # RSS
                t = it.find(".//{*}title")
                d = it.find(".//{*}description")

                # Atom (summary/content)
                if d is None:
                    d = it.find(".//{*}summary") or it.find(".//{*}content")

                title = _strip_html((t.text or "").strip()) if t is not None else ""
                desc  = _strip_html((d.text or "").strip()) if d is not None else ""
                if not title:
                    continue

                if desc and desc != title:
                    desc = desc[:140] + ("…" if len(desc) > 140 else "")
                    titles.append(f"{title} — {desc}")
                else:
                    titles.append(title)
            return titles
        except Exception:
            # 2) 최후 fallback: 정규식 기반 RSS 추출 (BeautifulSoup 사용 안 함)
            try:
                import re as _re
                items = _re.findall(r"<item[^>]*>.*?</item>", xml_text, flags=_re.I | _re.S)
                if not items:
                    # Atom <entry>
                    items = _re.findall(r"<entry[^>]*>.*?</entry>", xml_text, flags=_re.I | _re.S)

                titles = []
                for blk in items[:max_items]:
                    # title
                    mt = _re.search(r"<title[^>]*>(.*?)</title>", blk, flags=_re.I | _re.S)
                    md = _re.search(r"<description[^>]*>(.*?)</description>", blk, flags=_re.I | _re.S)
                    if md is None:
                        md = _re.search(r"<summary[^>]*>(.*?)</summary>", blk, flags=_re.I | _re.S)
                    if md is None:
                        md = _re.search(r"<content[^>]*>(.*?)</content>", blk, flags=_re.I | _re.S)

                    title_raw = (mt.group(1) if mt else "").strip()
                    desc_raw  = (md.group(1) if md else "").strip()
                    # CDATA 제거
                    title_raw = _re.sub(r"^<!\[CDATA\[|\]\]>$", "", title_raw).strip()
                    desc_raw  = _re.sub(r"^<!\[CDATA\[|\]\]>$", "", desc_raw).strip()

                    title = _strip_html(title_raw)
                    desc  = _strip_html(desc_raw)
                    if not title:
                        continue
                    if desc and desc != title:
                        desc = desc[:140] + ("…" if len(desc) > 140 else "")
                        titles.append(f"{title} — {desc}")
                    else:
                        titles.append(title)

                return titles
            except Exception:
                return []

    except:
        return []
def _fetch_gdelt_headlines(max_items: int = 25) -> list:
    """(옵션) GDELT DOC API에서 지정학/공급망 관련 헤드라인+요약 수집"""
    try:
        # GDELT DOC 2.0 API: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
        base = "https://api.gdeltproject.org/api/v2/doc/doc"
        q = (
            '(geopolitics OR war OR missile OR sanctions OR tariff OR "trade war" OR '
            '"Middle East" OR Iran OR Israel OR Gaza OR Ukraine OR Russia OR "South China Sea" OR '
            '"North Korea" OR "shipping" OR "Red Sea" OR "Hormuz")'
        )
        params = {
            "query": q,
            "mode": "ArtList",
            "format": "json",
            "maxrecords": str(max_items),
            # 한국 투자에 유리하게 최근성 강화
            "sort": "HybridRel",
        }
        resp = requests.get(base, params=params, timeout=12, headers=_random_ua())
        if resp.status_code != 200:
            return []
        js = resp.json()
        arts = js.get("articles") or []
        out = []
        for a in arts[:max_items]:
            title = (a.get("title") or "").strip()
            se = (a.get("seendate") or "")[:10]
            src = (a.get("sourceCountry") or a.get("source") or "").strip()
            sn  = (a.get("snippet") or "").strip()
            sn  = _strip_html(sn)[:140] + ("…" if len(_strip_html(sn)) > 140 else "")
            if title:
                tail = " — " + sn if sn else ""
                prefix = f"[{src}] " if src else ""
                datep = f"{se} " if se else ""
                out.append(f"{datep}{prefix}{title}{tail}")
        return out
    except Exception:
        return []

def _fetch_multi_source_headlines() -> dict:
    """
    국내외 다중 소스에서 헤드라인 수집.
    반환: {source_name: [headline, ...]}
    """
    sources = {
        # ── 해외 (지정학·경제 핵심) ──
        "BBC":        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "Al_Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
        "CNBC":       "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "Guardian":   "https://www.theguardian.com/world/rss",

        "DW_World":    "https://rss.dw.com/rdf/rss-en-world",
        "DefenseNews_Global": "https://www.defensenews.com/arc/outboundfeeds/rss/category/global/?outputType=xml",
        "NPR_World":   "https://feeds.npr.org/1004/rss.xml",
        "G뉴스_해운":   "https://news.google.com/rss/search?q=shipping+Red+Sea+Hormuz+freight&hl=en&gl=US&ceid=US:en",
        "G뉴스_원자재": "https://news.google.com/rss/search?q=gold+safe+haven+commodities&hl=en&gl=US&ceid=US:en",
        "G뉴스_환율":   "https://news.google.com/rss/search?q=dollar+yen+won+fx+geopolitics&hl=en&gl=US&ceid=US:en",
        "G뉴스_지정학": "https://news.google.com/rss/search?q=geopolitics+war+sanctions&hl=en&gl=US&ceid=US:en",
        "G뉴스_에너지": "https://news.google.com/rss/search?q=oil+price+OPEC+energy&hl=en&gl=US&ceid=US:en",
        "G뉴스_무역":   "https://news.google.com/rss/search?q=trade+war+tariff+sanctions&hl=en&gl=US&ceid=US:en",
        # ── 국내 (한국 증시 직결) ──
        "한경":       "https://www.hankyung.com/feed/economy",
        "매일경제":   "https://rss.mk.co.kr/economy.xml",
        "G뉴스_한국경제": "https://news.google.com/rss/search?q=한국+증시+경제&hl=ko&gl=KR&ceid=KR:ko",
        "G뉴스_유가":     "https://news.google.com/rss/search?q=유가+원유+중동&hl=ko&gl=KR&ceid=KR:ko",
        "G뉴스_반도체":   "https://news.google.com/rss/search?q=반도체+수출규제+미중&hl=ko&gl=KR&ceid=KR:ko",
    }
    results = {}
    errors  = []
    def _fetch_one(name, url):
        try:
            headlines = _fetch_rss_headlines(url, max_items=15)
            if headlines:
                results[name] = headlines
            else:
                errors.append(f"{name}:0건")
        except Exception as e:
            errors.append(f"{name}:{e}")

    # v37.0: ThreadPoolExecutor로 전환 (max_workers=6, 동시 연결 제한)
    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(_fetch_one, n, u): n for n, u in sources.items()}
        try:
            for f in as_completed(futures, timeout=20):
                pass  # _fetch_one이 결과를 results에 직접 저장
        except Exception:
            pass  # 타임아웃 시 수집된 것만 사용

    if errors:
        print(f"  ⚠️ RSS 수집 실패: {', '.join(errors)}")

    # 모두 실패 시 기존 fetch_all_news (국내) fallback
    if not results:
        domestic = fetch_all_news()
        if domestic:
            results["국내뉴스"] = domestic[:20]

    return results

def _detect_geo_keywords(headlines_flat: list) -> list:
    """헤드라인 목록에서 지정학 키워드 감지 → 감지된 키워드 반환"""
    detected = []
    for h in headlines_flat:
        for kw in _GEO_KEYWORDS:
            if kw in h and kw not in detected:
                detected.append(kw)
    return detected

def _map_geo_sectors(detected_kws: list) -> list:
    """감지된 키워드 → 관련 섹터 자동 매핑"""
    import re
    sectors = []
    for pattern, sec_list in _GEO_SECTOR_MAP.items():
        for kw in detected_kws:
            if re.search(pattern, kw):
                for s in sec_list:
                    if s not in sectors:
                        sectors.append(s)
    return sectors

def _build_fallback_sector_directions(detected_kws: list, sectors: list) -> list:
    """
    API 없을 때 감지 키워드 + 섹터 기반으로 기본 방향/이유 생성.
    전쟁/군사 → 방산 상승 / 정유·에너지 상승 / 나머지 하락 기본값.
    """
    # 키워드 패턴으로 이벤트 유형 추론
    war_kws    = {"전쟁","전투","공습","미사일","폭격","침공","교전","충돌","군사","핵","대피","동원","군비","방공"}
    oil_kws    = {"이란","OPEC","유가","원유","석유","천연가스","LNG","감산","증산","호르무즈","홍해","수에즈","해협"}
    trade_kws  = {"제재","관세","무역전쟁","금수","봉쇄","수출통제","블랙리스트","덤핑","규제","칩","반도체규제"}
    ship_kws   = {"홍해","수에즈","호르무즈","해운","운임","선박","컨테이너","항만","물류","해협","보험료"}
    fx_kws     = {"달러","환율","원달러","엔화","위안","통화","금리","채권","리스크오프"}
    metal_kws  = {"금","은","구리","니켈","리튬","원자재","귀금속"}
    grain_kws  = {"곡물","밀","옥수수","대두","비료","식량","흉작","수출금지"}
    power_kws  = {"전력","원전","원자력","우라늄","전기요금","가스발전","발전"}
    cyber_kws  = {"사이버","해킹","랜섬웨어","공격","통신","위성","GPS","전파교란"}
    kw_set     = set(detected_kws)

    is_war   = bool(kw_set & war_kws)
    is_oil   = bool(kw_set & oil_kws)
    is_trade = bool(kw_set & trade_kws)
    is_ship  = bool(kw_set & ship_kws)
    is_fx    = bool(kw_set & fx_kws)
    is_metal = bool(kw_set & metal_kws)
    is_grain = bool(kw_set & grain_kws)
    is_power = bool(kw_set & power_kws)
    is_cyber = bool(kw_set & cyber_kws)

    # 섹터별 기본 방향 규칙
    SECTOR_RULES = {
        "방산":      ("상승",  "군사 긴장 → 방위산업 수혜",          +8),
        "항공우주":  ("상승",  "지정학 위기 → 방산·항공 수요 증가",   +6),
        "정유":      ("상승",  "지정학 위기 → 유가 상승 수혜",        +6) if is_oil or is_war else ("중립", "유가 변동 제한적", 0),
        "에너지":    ("상승",  "원유·가스 가격 상승 기대",             +5) if is_oil or is_war else ("중립", "유가 변동 제한적", 0),
        "화학":      ("하락",  "원자재 비용 증가 → 마진 악화",        -5),
        "항공":      ("하락",  "유가 상승 → 연료비 부담",             -6),
        "자동차":    ("하락",  "원자재 비용 상승 + 소비심리 위축",    -4),
        "조선":      ("상승",  "방위산업 수주 기대",                   +4) if is_war else ("중립", "직접 영향 제한적", 0),
        "반도체":    ("하락",  "수출통제·공급망 불확실성",            -5) if is_trade else ("중립", "직접 영향 제한적", 0),
        "IT":        ("하락",  "무역제재 → 글로벌 수요 위축",        -4) if is_trade else ("중립", "직접 영향 제한적", 0),
        "수출주":    ("하락",  "무역전쟁 → 수출 타격",               -6) if is_trade else ("중립", "제한적", 0),
        "금융·보험": ("하락",  "불확실성 → 투자심리 위축",           -4),
        "철강":      ("하락",  "원자재 수급 불안 + 수요 둔화",       -3),
        "곡물":      ("상승",  "공급망 차질 → 식품 가격 상승",        +5),

        "해운·물류": ("상승",  "해상 리스크/우회운항 → 운임 상승 수혜",    +6) if is_ship else ("중립", "직접 영향 제한적", 0),
        "물류":      ("상승",  "공급망 차질 → 운임/창고 수요 증가",        +4) if is_ship else ("중립", "직접 영향 제한적", 0),
        "보험":      ("하락",  "사고/리스크 확대 → 손해율 악화 우려",      -3) if is_ship or is_war else ("중립","제한적",0),
        "원전·전력": ("상승",  "에너지 안보 이슈 → 원전/전력 투자 확대",    +5) if is_power or is_oil else ("중립", "제한적", 0),
        "우라늄":    ("상승",  "원전 확대 기대 → 우라늄 수요",            +5) if is_power else ("중립","제한적",0),
        "금·귀금속": ("상승",  "리스크오프 → 안전자산 선호",              +5) if (is_war or is_fx or is_metal) else ("중립","제한적",0),
        "달러·환율": ("상승",  "달러 강세/변동성 확대",                    +3) if is_fx else ("중립","제한적",0),
        "여행":      ("하락",  "불확실성/유가 상승 → 수요 둔화",          -4) if (is_war or is_oil) else ("중립","제한적",0),
        "통신·위성": ("상승",  "통신/위성 인프라 수요",                    +3) if is_cyber else ("중립","제한적",0),
        "사이버보안": ("상승",  "사이버 공격 증가 → 보안 수요 확대",       +6) if is_cyber else ("중립","제한적",0),

        "건설":      ("중립",  "국내 수요 변화 제한적",               0),
    }

    result = []
    for sec in sectors:
        # 섹터명 부분 매칭 (예: "에너지·정유" → "정유" 규칙 사용)
        matched_rule = None
        for key, rule in SECTOR_RULES.items():
            if key in sec or sec in key:
                matched_rule = rule
                break
        if matched_rule:
            direction, reason, score_adj = matched_rule
        else:
            direction, reason, score_adj = "중립", "영향 분석 중", 0

        result.append({
            "sector":    sec,
            "direction": direction,
            "reason":    reason,
            "score_adj": score_adj,
        })
    return result


def analyze_geopolitical_event(headlines_by_source: dict) -> dict:
    """
    Claude API로 다중 소스 주체별 입장 분석.
    각 소스의 헤드라인을 보내 → 주체/입장/불확실성/관련섹터 JSON 반환.
    반환: {
      entities: [{name, stance, reason}],  # 관련 주체별 입장
      uncertainty: "high"/"mid"/"low",     # 소스 간 입장 충돌 정도
      sectors: [섹터명],                   # 관련 섹터
      score_adj: int,                      # 신호 점수 보정
      summary: str,                        # 텔레그램 요약
      detected: bool
    }
    """
    # 지정학 키워드 감지 여부 먼저 체크
    all_headlines = [h for hl in headlines_by_source.values() for h in hl]
    detected_kws  = _detect_geo_keywords(all_headlines)

    if not detected_kws:
        return {"detected": False, "uncertainty": "low", "sectors": [],
                "score_adj": 0, "summary": "", "entities": []}

    # 캐시 키: 감지된 키워드 조합
    cache_key = ",".join(sorted(detected_kws[:5]))
    cached = _geo_cache.get(cache_key)
    if cached and time.time() - cached.get("ts", 0) < 3600:
        return cached

    # Claude API 호출
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        # API 키 없으면 키워드 기반 fallback (sector_directions도 생성)
        sectors   = _map_geo_sectors(detected_kws)
        score_adj = -5 if len(detected_kws) >= 3 else 0
        # 키워드로 기본 섹터 방향 추론
        sec_dirs_fb = _build_fallback_sector_directions(detected_kws, sectors)
        return {"detected": True, "uncertainty": "mid", "sectors": sectors,
                "sector_directions": sec_dirs_fb,
                "score_adj": score_adj, "summary": f"⚠️ 지정학 이벤트 감지: {', '.join(detected_kws[:3])}",
                "entities": [], "ts": time.time()}

    try:
        # 소스별 헤드라인 정리 (최대 10개씩)
        source_text = ""
        for src, hl_list in headlines_by_source.items():
            if hl_list:
                source_text += f"[{src}]\n" + "\n".join(f"- {h}" for h in hl_list[:8]) + "\n\n"

        prompt = f"""다음은 여러 언론 소스의 최신 헤드라인입니다.

{source_text}

감지된 지정학 키워드: {', '.join(detected_kws[:10])}

다음을 분석해서 JSON으로만 답하세요 (다른 텍스트 없이):

{{
  "entities": [
    {{"name": "주체명(국가/기업/기구)", "stance": "긍정/부정/중립", "reason": "한 줄 이유"}}
  ],
  "uncertainty": "high/mid/low",
  "uncertainty_reason": "소스 간 입장 충돌 여부",
  "sector_directions": [
    {{
      "sector": "한국 주식 섹터명",
      "direction": "상승/하락/중립",
      "reason": "한 줄 이유",
      "score_adj": -10~+10 사이 정수
    }}
  ],
  "score_adj": -15~+10 사이 정수 (전체 시장 불확실성 기준),
  "summary": "한국 투자자용 한 줄 요약"
}}

주의:
- uncertainty는 소스들이 서로 다른 입장을 보이면 high, 비슷하면 low
- sector_directions는 이 이슈로 인해 직접 영향받는 한국 섹터만 포함 (3~6개)
- direction은 해당 섹터 주가 방향 예측 (상승/하락/중립)
- score_adj는 섹터별 점수 보정값 (상승이면 양수, 하락이면 음수)"""

        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         api_key,
                "anthropic-version": "2024-10-22",
                "content-type":      "application/json",
            },
            json={
                "model":      "claude-haiku-4-5-20251001",
                "max_tokens": 1000,
                "messages":   [{"role": "user", "content": prompt}],
            },
            timeout=15
        )
        raw  = extract_ai_text(resp.json())
        # JSON 파싱
        raw  = raw.replace("```json","").replace("```","").strip()
        data = json.loads(raw)

        # sector_directions → sectors 리스트도 같이 추출
        sec_dirs = data.get("sector_directions", [])
        sectors  = [s["sector"] for s in sec_dirs] if sec_dirs else _map_geo_sectors(detected_kws)

        result = {
            "detected":          True,
            "entities":          data.get("entities", []),
            "uncertainty":       data.get("uncertainty", "mid"),
            "sectors":           sectors,
            "sector_directions": sec_dirs,   # [{sector, direction, reason, score_adj}]
            "score_adj":         max(-15, min(data.get("score_adj", 0), 10)),
            "summary":           data.get("summary", ""),
            "kws":               detected_kws[:5],
            "ts":                time.time(),
        }
        _geo_cache[cache_key] = result
        # [v37.10-all5] 섹터 방향을 점수 보정용 전역 상태로 반영
        try:
            bias = {}
            for sd in (sec_dirs or []):
                sec = sd.get("sector")
                d = sd.get("direction")
                if not sec or not d:
                    continue
                if d in ("up","bull","positive","상승"):
                    bias[sec] = int(sd.get("score_adj", 3) or 3)
                elif d in ("down","bear","negative","하락"):
                    bias[sec] = int(sd.get("score_adj", -3) or -3)
            # score_adj가 없는 섹터는 기본 +/-2
            GEO_SECTOR_BIAS.clear()
            GEO_SECTOR_BIAS.update(bias)
        except Exception:
            pass
        print(f"  🌍 지정학 분석: {result['uncertainty']} 불확실성 / 섹터: {result['sectors']}")
        return result

    except Exception as e:
        _log_error("analyze_geopolitical_event", e)
        # fallback
        sectors = _map_geo_sectors(detected_kws)
        sec_dirs_fb = _build_fallback_sector_directions(detected_kws, sectors)
        return {"detected": True, "uncertainty": "mid", "sectors": sectors,
                "sector_directions": sec_dirs_fb,
                "score_adj": -5, "summary": f"⚠️ 지정학 이벤트: {', '.join(detected_kws[:3])}",
                "entities": [], "ts": time.time()}

def run_geo_news_scan():
    """
    지정학 뉴스 스캔 (1시간마다).
    이벤트 감지 시 관련 섹터 알림 + 신호 점수 자동 보정 등록.
    """
    try:
        headlines_by_source = _fetch_multi_source_headlines()
        if not headlines_by_source:
            return

        geo = analyze_geopolitical_event(headlines_by_source)
        if not geo.get("detected"):
            return

        # 결과를 전역에 저장 (신호 포착 시 참조)
        _geo_event_state.update({
            "active":           True,
            "uncertainty":      geo["uncertainty"],
            "sectors":          geo["sectors"],
            "sector_directions":geo.get("sector_directions", []),
            "score_adj":        geo["score_adj"],
            "summary":          geo["summary"],
            "entities":         geo["entities"],
            "ts":               time.time(),
        })

        # 텔레그램 알림 (1시간 쿨다운)
        last_sent = _geo_event_state.get("last_sent_ts", 0)
        if time.time() - last_sent < 3600:
            return
        _geo_event_state["last_sent_ts"] = time.time()

        unc_emoji = {"high": "🔴", "mid": "🟠", "low": "🟢"}
        msg  = (f"🌍 <b>지정학 이벤트 감지</b>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"{unc_emoji.get(geo['uncertainty'],'🟠')} 불확실성: <b>{geo['uncertainty'].upper()}</b>\n\n")

        if geo.get("entities"):
            msg += "<b>주체별 입장</b>\n"
            for e in geo["entities"][:5]:
                stance_emoji = {"긍정":"🟢","부정":"🔴","중립":"🔵"}.get(e.get("stance","중립"),"🔵")
                msg += f"  {stance_emoji} {e.get('name','')} — {e.get('stance','')} ({e.get('reason','')})\n"
            msg += "\n"

        sec_dirs = geo.get("sector_directions", [])
        # sector_directions 없으면 sectors 기반으로 자동 생성 (fallback)
        if not sec_dirs and geo.get("sectors"):
            sec_dirs = _build_fallback_sector_directions(
                geo.get("kws", []) or _detect_geo_keywords(
                    [h for hl in headlines_by_source.values() for h in hl]
                ),
                geo["sectors"]
            )
        if sec_dirs:
            msg += "<b>📊 섹터별 영향</b>\n"
            for sd in sec_dirs:
                _dir   = sd.get("direction", "중립")
                _icon  = _DIR_DISPLAY.get(_dir, "▶")
                _adj   = int(sd.get("score_adj", 0) or 0)
                _adj_str = f"  <b>{_adj:+d}점</b>" if _adj != 0 else ""
                _sec   = sd.get("sector", "")
                # 관련 종목 조회
                _stocks = _get_geo_sector_stocks(_sec, max_n=3)
                _stk_str = "  ".join(f"<code>{n}</code>" for c,n in _stocks) if _stocks else ""
                # v37.0: 과거 유사 이벤트 이력 조회
                _hist_str = _get_geo_sector_history(_sec, _stocks) if _stocks else ""
                msg += (f"┌ {_icon} <b>{_sec}</b>{_adj_str}\n"
                        f"│  {sd.get('reason','')}\n"
                        + (f"│  📌 {_stk_str}\n" if _stk_str else "")
                        + (f"{_hist_str}\n" if _hist_str else "")
                        + "└─────────────\n")
            msg += "\n"
        elif geo.get("sectors"):
            msg += f"📊 관련 섹터: {', '.join(geo['sectors'])}\n"

        if geo.get("summary"):
            msg += f"\n💡 {geo['summary']}"

        send(msg)

    except Exception as e:
        _log_error("run_geo_news_scan", e)



# ============================================================
# 👤 개인 수급 맥락 분석
# ============================================================
def eval_retail_signal(code: str,
                       f_net: int, i_net: int, r_net: int,
                       cap_size: str = "unknown") -> dict:
    """
    "개인만 매수" 신호를 맥락에 따라 다르게 해석.

    고려 요소:
      ① 시장 국면 (bull/normal/bear/crash)
      ② 종목 5일 추세 (상승조정 vs 하락전환)
      ③ 종목 규모 (대형/중형/소형)

    반환:
      score_adj: int
      label: str
      detail: str
      confidence: str
    """
    # 개인 매수 + 기관/외국인 이탈 아니면 해당 없음
    if not (r_net > 0 and f_net < 0 and i_net < 0):
        return {}

    regime    = get_market_regime().get("mode", "normal")
    r_abs     = abs(r_net)

    # ─── 종목 5일 추세 계산 ───
    stock_trend = "unknown"
    try:
        daily  = get_daily_data(code, 10)
        closes = [int(d.get("stck_clpr", 0)) for d in daily if d.get("stck_clpr")]
        if len(closes) >= 6:
            chg_5d = (closes[-1] - closes[-6]) / closes[-6] * 100
            if   chg_5d >= 5.0:   stock_trend = "rally"      # 급등 후 조정
            elif chg_5d >= 1.0:   stock_trend = "uptrend"    # 상승 추세 중 조정
            elif chg_5d >= -3.0:  stock_trend = "sideways"   # 횡보/소폭 조정
            elif chg_5d >= -7.0:  stock_trend = "pullback"   # 의미 있는 조정
            else:                 stock_trend = "downtrend"   # 하락 추세
    except:
        pass

    # ─── 맥락 조합 판단 ───
    # CASE 1: bull/normal국면 + 대형/중형주 + 조정/횡보/급등후조정 중 개인 매수
    #         → 저점 분할매수일 가능성 높음 (삼성전자, SK하이닉스 사례)
    if (regime in ("bull", "normal")
            and cap_size in ("large", "mid")
            and stock_trend in ("uptrend", "pullback", "sideways", "rally")):
        label = ("💡 개인 저점 매수 (대/중형 조정)"
                 if stock_trend != "rally" else
                 "💡 개인 급등 후 조정 매수 (대/중형)")
        return {
            "score_adj":  +5,
            "label":      label,
            "detail":     (f"bull/normal 국면 + {cap_size}cap 조정 중 개인 +{r_abs:,}주 — "
                           f"기관 리밸런싱 매도 가능성, 단기 지지 효과 기대"),
            "confidence": "mid",
        }

    # CASE 2: bull국면 + 소형주 + 급등 후 개인 매수
    #         → 고점 추격 매수 (기관 물량 받아내는 개미)
    if (regime in ("bull", "normal")
            and cap_size == "small"
            and stock_trend in ("rally", "uptrend")):
        return {
            "score_adj":  -5,
            "label":      "⚠️ 개인 고점 추격 (소형 급등)",
            "detail":     (f"소형주 급등 후 개인 +{r_abs:,}주 — "
                           f"기관 차익실현 물량 받아내는 구도 가능성"),
            "confidence": "mid",
        }

    # CASE 2b: bull/normal국면 + 소형주 + 조정/횡보 중 → 판단 보류
    if (regime in ("bull", "normal")
            and cap_size == "small"
            and stock_trend in ("sideways", "pullback")):
        return {
            "score_adj":  0,
            "label":      "📊 소형주 개인 매수 (조정중, 판단 보류)",
            "detail":     (f"소형주 조정 구간 개인 +{r_abs:,}주 — "
                           f"기관+외국인 이탈 지속 여부 확인 필요"),
            "confidence": "low",
        }

    # CASE 3: bear/crash 국면 + 대형/중형주 → 낙폭과대 저점 가능성
    if regime in ("bear", "crash") and cap_size in ("large", "mid"):
        return {
            "score_adj":  0,
            "label":      "❓ 하락장 대형/중형주 개인 매수 (낙폭과대 판단 보류)",
            "detail":     (f"약세장에도 {cap_size}cap 개인 +{r_abs:,}주 — "
                           f"낙폭과대 저점 가능성 vs 추가하락 위험 공존 (판단 보류)"),
            "confidence": "low",
        }

    # CASE 4: bear/crash 국면 + 소형주 → 역방향 위험
    if regime in ("bear", "crash") and cap_size == "small":
        return {
            "score_adj":  -12,
            "label":      "🔴 개인만 매수 / 기관+외국인 이탈 (약세장+소형주)",
            "detail":     (f"약세장 소형주 + 외국인 {f_net:,}주 + 기관 {i_net:,}주 동시 매도 — "
                           f"개인 역방향 수급, 추가 하락 위험"),
            "confidence": "high",
        }

    # CASE 5: 하락 추세 중 개인 매수 (국면/규모 무관)
    if stock_trend == "downtrend":
        return {
            "score_adj":  -8,
            "label":      "⚠️ 하락추세 중 개인 역방향 매수",
            "detail":     (f"5일 추세 하락 중 개인 +{r_abs:,}주 — "
                           f"기관+외국인 이탈 지속 시 지지력 약화 우려"),
            "confidence": "mid",
        }

    # CASE 6: 그 외 (판단 보류)
    return {
        "score_adj":  0,
        "label":      "📊 개인 매수 (맥락 불분명)",
        "detail":     (f"개인 +{r_abs:,}주 / 기관+외국인 이탈 — "
                       f"국면:{regime}, 추세:{stock_trend}, 규모:{cap_size} — 판단 보류"),
        "confidence": "low",
    }

# ============================================================
# 📰 뉴스 심층 분석 (본문 크롤링 + Claude API)
# ============================================================
_deep_news_cache: dict = {}   # code → {result, ts}

# 심층 분석이 필요한 기업 이벤트 키워드
_CORP_EVENT_KEYWORDS = [
    "무상증자","유상증자","합병","분할","인수","자사주","배당",
    "실적","영업이익","순이익","매출","흑자","적자","전환",
    "상장폐지","거래정지","불성실공시","횡령","배임",
    "공급계약","수주","MOU","협약","허가","승인","임상","FDA",
]

def _fetch_article_body(url: str) -> str:
    """
    네이버 금융 뉴스 본문 크롤링.
    최대 600자 반환 (토큰 절약).
    """
    if not url:
        return ""
    try:
        resp = requests.get(url, headers=_random_ua(), timeout=8)
        soup = BeautifulSoup(resp.text, "html.parser")
        # 네이버 뉴스 본문 셀렉터
        body_el = (soup.select_one("div#news_read") or
                   soup.select_one("div.news_end") or
                   soup.select_one("div._article_body") or
                   soup.select_one("article"))
        if body_el:
            text = body_el.get_text(separator=" ", strip=True)
            # 광고/불필요 문구 제거
            text = text.replace("© 무단전재 및 재배포 금지","").strip()
            return text[:600]
    except:
        pass
    return ""

def analyze_news_deep(articles: list, stock_name: str, code: str = "") -> dict:
    """
    뉴스 기사 심층 분석 (Claude API).
    헤드라인 + 본문 기반으로 실질 호재/악재 판단.

    반환: {
      verdict: "실질호재" / "실질악재" / "표면호재실질악재" / "불확실" / "중립",
      score_adj: int (-15 ~ +15),
      reason: str,
      risk_points: [str],   # 본문에서 발견된 리스크
      key_event: str,       # 핵심 이벤트 유형
      confidence: "high"/"mid"/"low"
    }
    """
    if not articles:
        return {"verdict": "중립", "score_adj": 0, "reason": "", "risk_points": [],
                "key_event": "", "confidence": "low"}

    # 캐시 확인
    cache_key = f"{code}_{articles[0].get('title','')[:20]}"
    cached = _deep_news_cache.get(cache_key)
    if cached and time.time() - cached.get("ts", 0) < 3600:
        return cached

    # 기업 이벤트 키워드 감지 여부 확인
    all_titles = " ".join(a.get("title","") for a in articles)
    has_event  = any(kw in all_titles for kw in _CORP_EVENT_KEYWORDS)

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    # API 키 없거나 이벤트 없으면 → 기존 키워드 분석 fallback
    if not api_key or not has_event:
        sent = analyze_news_sentiment([a.get("title","") for a in articles], stock_name)
        if   sent["score"] >= 10: adj, verdict = +8,  "실질호재"
        elif sent["score"] >= 4:  adj, verdict = +4,  "실질호재"
        elif sent["score"] <= -10:adj, verdict = -10, "실질악재"
        elif sent["score"] <= -4: adj, verdict = -5,  "실질악재"
        else:                     adj, verdict = 0,   "중립"
        return {"verdict": verdict, "score_adj": adj, "reason": "키워드 분석",
                "risk_points": [], "key_event": "", "confidence": "low",
                "ts": time.time()}

    # 본문 크롤링 (최대 2건)
    articles_with_body = []
    for a in articles[:2]:
        body = _fetch_article_body(a.get("url",""))
        articles_with_body.append({
            "title": a.get("title",""),
            "body":  body or "(본문 없음)"
        })

    # Claude API 심층 분석
    try:
        article_text = ""
        for i, a in enumerate(articles_with_body, 1):
            article_text += f"[기사{i}] 제목: {a['title']}\n본문: {a['body']}\n\n"

        prompt = f"""다음은 한국 주식 종목 [{stock_name}]의 최신 뉴스 기사입니다.

{article_text}

투자자 관점에서 이 뉴스가 주가에 미치는 실질적 영향을 분석하고 JSON으로만 답하세요:

{{
  "verdict": "실질호재/실질악재/표면호재실질악재/표면악재실질호재/불확실/중립",
  "score_adj": -15~+15 사이 정수,
  "key_event": "핵심 이벤트 한 단어 (무상증자/유상증자/합병/수주/실적/등)",
  "reason": "판단 근거 한 줄",
  "risk_points": ["본문에서 발견된 리스크나 주의사항 (없으면 빈 배열)"],
  "confidence": "high/mid/low"
}}

판단 기준:
- 표면호재실질악재 예시: 무상증자(호재처럼 보이나 재원/재무상태 불량), 합병(합병비율 불리), 유상증자(대규모 희석)
- 표면악재실질호재 예시: 단기 실적 부진이나 구조조정 완료, 악재 선반영 후 저점
- score_adj는 실질 영향 기준 (표면호재실질악재면 음수)"""

        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         api_key,
                "anthropic-version": "2024-10-22",
                "content-type":      "application/json",
            },
            json={
                "model":      "claude-haiku-4-5-20251001",
                "max_tokens": 400,
                "messages":   [{"role": "user", "content": prompt}],
            },
            timeout=15
        )
        raw  = extract_ai_text(safe_json_response(resp))
        raw  = raw.replace("```json","").replace("```","").strip()
        try:
            data = json.loads(raw)
        except Exception:
            return {'verdict':'중립','score_adj':0,'reason':'(요약 실패)','risk_points':[],'key_event':'','confidence':'low'}

        result = {
            "verdict":     data.get("verdict", "중립"),
            "score_adj":   max(-15, min(data.get("score_adj", 0), 15)),
            "key_event":   data.get("key_event", ""),
            "reason":      data.get("reason", ""),
            "risk_points": data.get("risk_points", []),
            "confidence":  data.get("confidence", "mid"),
            "ts":          time.time(),
        }
        _deep_news_cache[cache_key] = result
        print(f"  📰 심층분석 [{stock_name}]: {result['verdict']} {int(result['score_adj'] or 0):+d}점")
        return result

    except Exception as e:
        _log_error(f"analyze_news_deep({stock_name})", e)
        # fallback
        sent = analyze_news_sentiment([a.get("title","") for a in articles], stock_name)
        adj  = 8 if sent["score"]>=10 else 4 if sent["score"]>=4 else -10 if sent["score"]<=-10 else -5 if sent["score"]<=-4 else 0
        return {"verdict": "중립", "score_adj": adj, "reason": "API 오류 — 키워드 fallback",
                "risk_points": [], "key_event": "", "confidence": "low", "ts": time.time()}

# ============================================================
# 📰 뉴스 감성 분석
# ============================================================
_POSITIVE_KEYWORDS = [
    "급등","상한가","신고가","돌파","수주","흑자","호실적","매수","상향","성장",
    "수출","계약","협약","투자유치","증가","개선","재개","허가","승인","선정",
    "외국인매수","기관매수","강세","반등","회복","수혜","테마"
]
_NEGATIVE_KEYWORDS = [
    "급락","하한가","신저가","하락","적자","손실","매도","하향","감소","악화",
    "소송","조사","제재","리콜","부도","파산","매물","공매도","외국인매도",
    "약세","폭락","위기","경고","주의","실망","불확실"
]


# ============================================================
# 📊 매물대/지지저항선 자동 계산 (Volume Profile)
# ============================================================
_vp_cache: dict = {}  # code → {levels, ts}

def calc_volume_profile(code: str, entry: int) -> dict:
    """
    일봉 데이터로 가격별 거래량 집계 → 매물대/지지저항선 계산.
    진입가 근처에 강한 저항선 있으면 감점, 지지선 위면 가중.
    반환: {score_adj: int, reason: str, support: int, resistance: int}
    """
    cached = _vp_cache.get(code)
    if cached and time.time() - cached.get("ts", 0) < 3600:
        return cached

    result = {"score_adj": 0, "reason": "", "support": 0, "resistance": 0, "ts": time.time()}
    try:
        items = get_daily_data(code, 60)
        if len(items) < 20 or not entry:
            return result

        # 가격 구간별 거래량 집계 (50개 구간)
        prices = [i["close"] for i in items if i.get("close")]
        vols   = [i["vol"]   for i in items if i.get("vol")]
        if not prices: return result

        price_min, price_max = min(prices), max(prices)
        if price_max == price_min: return result

        bucket_size = (price_max - price_min) / 50
        buckets     = {}
        for i, item in enumerate(items):
            if not item.get("close") or not item.get("vol"): continue
            bucket = int((item["close"] - price_min) / bucket_size)
            bucket = max(0, min(bucket, 49))
            buckets[bucket] = buckets.get(bucket, 0) + item["vol"]

        # 상위 10% 거래량 구간 → 매물대
        sorted_buckets = sorted(buckets.items(), key=lambda x: -x[1])
        top_n          = max(1, len(sorted_buckets) // 10)
        heavy_buckets  = [b for b, v in sorted_buckets[:top_n]]

        # 매물대 가격 계산
        heavy_prices = [price_min + (b + 0.5) * bucket_size for b in heavy_buckets]

        # 진입가 기준 ±10% 범위 내 매물대 찾기
        near_range    = entry * 0.10
        above_levels  = sorted([p for p in heavy_prices if entry < p <= entry + near_range])
        below_levels  = sorted([p for p in heavy_prices if entry - near_range <= p < entry], reverse=True)

        resistance = int(above_levels[0])  if above_levels else 0
        support    = int(below_levels[0])  if below_levels else 0

        score_adj = 0
        reasons   = []

        if resistance:
            gap_pct = (resistance - entry) / entry * 100
            if gap_pct < 3.0:
                score_adj -= 8
                reasons.append(f"🧱 진입가 +{gap_pct:.1f}%에 강한 저항선 ({resistance:,}원) -8점")
            elif gap_pct < 6.0:
                score_adj -= 3
                reasons.append(f"⚠️ 진입가 +{gap_pct:.1f}%에 저항선 ({resistance:,}원) -3점")

        if support:
            gap_pct = (entry - support) / entry * 100
            if gap_pct < 3.0:
                score_adj += 5
                reasons.append(f"✅ 진입가 -{gap_pct:.1f}%에 강한 지지선 ({support:,}원) +5점")

        result.update({
            "score_adj":  score_adj,
            "reason":     "  ".join(reasons),
            "support":    support,
            "resistance": resistance,
        })
        _vp_cache[code] = result
    except Exception as e:
        _log_error(f"calc_volume_profile({code})", e)

    return result

def analyze_news_sentiment(headlines: list, stock_name: str = "") -> dict:
    """
    뉴스 헤드라인 목록에서 감성 점수 계산.
    stock_name이 있으면 해당 종목 관련 헤드라인만 필터.
    반환: {score: -20~+20, label: str, pos: int, neg: int, matched: list}
    """
    if not headlines:
        return {"score": 0, "label": "중립", "pos": 0, "neg": 0, "matched": []}

    # 종목명 필터
    targets = [h for h in headlines if not stock_name or stock_name in h] if stock_name else headlines

    pos = sum(1 for h in targets for kw in _POSITIVE_KEYWORDS if kw in h)
    neg = sum(1 for h in targets for kw in _NEGATIVE_KEYWORDS if kw in h)

    # 정규화 (-20 ~ +20)
    total = pos + neg
    if total == 0:
        raw_score = 0
    else:
        raw_score = int((pos - neg) / total * 20)

    raw_score = max(-20, min(raw_score, 20))

    if   raw_score >= 10: label = "매우 긍정"
    elif raw_score >= 4:  label = "긍정"
    elif raw_score <= -10: label = "매우 부정"
    elif raw_score <= -4:  label = "부정"
    else:                  label = "중립"

    matched = [h for h in targets if
               any(kw in h for kw in _POSITIVE_KEYWORDS + _NEGATIVE_KEYWORDS)][:3]

    return {"score": raw_score, "label": label, "pos": pos, "neg": neg, "matched": matched}

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

    rising_lines = []
    for s in signal.get("rising", []):
        wsuf = _watch_suffix(s.get("code",""), safe_int(s.get("price", 0)))
        marker = '🟩' if s['change_rate'] > 0 else ('🟥' if s['change_rate'] < 0 else '⬜')
        rising_lines.append(
            f"  {marker} <b>{s['name']}</b> {s['change_rate']:+.1f}%"
            + (f" 🔊{s['volume_ratio']:.0f}x" if s.get("vol_on") else "")
            + (" 🚀" if s.get("surging") else "")
            + wsuf
        )
    rising_block = ("\n".join(rising_lines) + ("\n" if rising_lines else ""))

    not_yet_lines = []
    for s in signal.get("not_yet", []):
        wsuf = _watch_suffix(s.get("code",""), safe_int(s.get("price", 0)))
        marker = '🟩' if s['change_rate'] > 0 else ('🟥' if s['change_rate'] < 0 else '⬜')
        not_yet_lines.append(f"  {marker} {s['name']} {s['change_rate']:+.1f}%{wsuf}")
    not_yet_block = ("\n".join(not_yet_lines) + ("\n" if not_yet_lines else ""))
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

            # ── DART 공시 심층 분석 (기업 이벤트인 경우) ──
            dart_deep = None
            try:
                event_kws = ["무상증자","유상증자","합병","분할","인수","자사주","배당",
                             "흑자전환","적자전환","실적","수주","계약"]
                if any(kw in title for kw in event_kws):
                    fake_article = [{"title": title, "url": "", "time": ""}]
                    dart_deep = analyze_news_deep(fake_article, company, code)
            except: pass

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

            # 외국인·기관·개인 수급
            inv_text = ""
            try:
                inv   = get_investor_trend(code)
                f_net = inv.get("foreign_net",     0)
                i_net = inv.get("institution_net", 0)
                r_net = inv.get("retail_net",      0)
                # 3자 구도 표시
                if   f_net > 0 and i_net > 0 and r_net < 0:
                    inv_text = "\n💎 외국인+기관 매수 / 개인 매도 (최강 수급)"
                elif f_net > 0 and i_net > 0:
                    inv_text = "\n✅ 외국인+기관 동시 순매수"
                elif f_net > 0:
                    inv_text = "\n🟡 외국인 순매수"
                elif i_net > 0:
                    inv_text = "\n🟡 기관 순매수"
                elif r_net > 0 and f_net < 0 and i_net < 0:
                    # 맥락 분석
                    _re = eval_retail_signal(code, f_net, i_net, r_net,
                                            inv.get("cap_size","unknown") if hasattr(inv,"get") else "unknown")
                    if _re and _re.get("score_adj",0) >= 0:
                        inv_text = f"\n{_re['label']}"
                    else:
                        inv_text = "\n⚠️ 개인만 매수 / 기관+외국인 이탈 (맥락 주의)"
                elif f_net < 0 and i_net < 0:
                    inv_text = "\n🔴 외국인+기관 동시 순매도"
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
                    f"  📈 {_resolve_stock_name(r['code'], r.get('name',''))} {r['change_rate']:+.1f}%"
                    + (f" 🔊{r['volume_ratio']:.0f}x" if r.get("volume_ratio",0)>=2 else "") + "\n"
                    for r in rising[:4]
                ])
                for r in flat[:2]:
                    sector_block += f"  ➖ {_resolve_stock_name(r['code'], r.get('name',''))} {r['change_rate']:+.1f}%\n"
            elif theme:
                sector_block = f"\n━━━━━━━━━━━━━━━\n🏭 섹터 [{theme}]: 동업종 조회 중\n"

            # 심층 분석 블록
            deep_block = ""
            if dart_deep:
                verd = dart_deep.get("verdict","")
                adj  = dart_deep.get("score_adj", 0)
                rsn  = dart_deep.get("reason","")
                rps  = dart_deep.get("risk_points",[])
                if verd == "표면호재실질악재":
                    deep_block = f"\n━━━━━━━━━━━━━━━\n⚠️ <b>표면호재실질악재 경고</b>\n  {rsn}"
                    for rp in rps[:2]:
                        deep_block += f"\n  🔸 {rp}"
                elif verd == "표면악재실질호재":
                    deep_block = f"\n━━━━━━━━━━━━━━━\n💡 <b>역발상 매수 검토</b>\n  {rsn}"
                elif verd in ("실질호재","실질악재") and rsn:
                    v_emoji = "✅" if "호재" in verd else "❌"
                    deep_block = f"\n━━━━━━━━━━━━━━━\n{v_emoji} <b>{verd}</b>  {adj:+d}점\n  {rsn}"

            # v37.0: 과거 유사 공시 이력 조회
            dart_hist_block = ""
            try:
                dart_hist_block = get_dart_keyword_history(code, company, all_kw)
            except: pass

            send_with_chart_buttons(
                f"{emoji} <b>[공시+주가 연동]</b>  {tag}\n"
                f"🕐 {datetime.now().strftime('%H:%M:%S')}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"{'🔴' if is_risk else '🟡'} <b>{company}</b>  <code>{code}</code>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📌 {title}\n"
                f"🔑 키워드: {', '.join(all_kw)}"
                f"{deep_block}"
                f"{price_block}"
                f"{sector_block}"
                f"{stop_block}"
                f"{dart_hist_block}",
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

            # ── /geo — 지정학 분석 수동 실행 ──
            elif text == "/geo":
                send("🌍 지정학 뉴스 분석 중... (10~20초 소요)")
                def _run_geo():
                    try:
                        headlines_by_src = _fetch_multi_source_headlines()
                        if not headlines_by_src:
                            send("⚠️ 뉴스 소스 수집 실패 — 모든 RSS 접근 불가")
                            return
                        src_summary = "  ".join(f"{k}:{len(v)}건" for k,v in headlines_by_src.items())
                        send(f"📡 수집 완료 ({len(headlines_by_src)}개 소스)\n{src_summary}")
                        geo = analyze_geopolitical_event(headlines_by_src)
                        if not geo.get("detected"):
                            send("✅ 지정학 이벤트 없음 — 현재 안전 상태")
                            return
                        unc_emoji = {"high":"🔴","mid":"🟠","low":"🟢"}.get(geo.get("uncertainty","mid"),"🟠")
                        msg = (f"🌍 <b>지정학 분석 결과</b>\n"
                               f"━━━━━━━━━━━━━━━\n"
                               f"{unc_emoji} 불확실성: <b>{geo.get('uncertainty','?').upper()}</b>\n\n")
                        if geo.get("entities"):
                            msg += "<b>주체별 입장</b>\n"
                            for e in geo["entities"][:6]:
                                s_emoji = {"긍정":"🟢","부정":"🔴","중립":"🔵"}.get(e.get("stance","중립"),"🔵")
                                msg += f"  {s_emoji} {e.get('name','')} — {e.get('stance','')} ({e.get('reason','')})\n"
                            msg += "\n"
                        # /geo 핸들러 — sector_directions 없으면 fallback 생성
                        sec_dirs = geo.get("sector_directions", [])
                        if not sec_dirs and geo.get("sectors"):
                            _kws_fb = geo.get("kws", [])
                            sec_dirs = _build_fallback_sector_directions(_kws_fb, geo["sectors"])
                        if sec_dirs:
                            msg += "<b>📊 섹터별 영향</b>\n"
                            for sd in sec_dirs:
                                _dir2   = sd.get("direction", "중립")
                                _icon2  = _DIR_DISPLAY.get(_dir2, "▶")
                                _adj2   = int(sd.get("score_adj", 0) or 0)
                                _adj2_str = f"  <b>{_adj2:+d}점</b>" if _adj2 != 0 else ""
                                _sec2   = sd.get("sector", "")
                                _stocks2 = _get_geo_sector_stocks(_sec2, max_n=3)
                                _stk2_str = "  ".join(f"<code>{n}</code>" for c,n in _stocks2) if _stocks2 else ""
                                # v37.0: 과거 유사 이벤트 이력
                                _hist2_str = _get_geo_sector_history(_sec2, _stocks2) if _stocks2 else ""
                                msg += (f"┌ {_icon2} <b>{_sec2}</b>{_adj2_str}\n"
                                        f"│  {sd.get('reason','')}\n"
                                        + (f"│  📌 {_stk2_str}\n" if _stk2_str else "")
                                        + (f"{_hist2_str}\n" if _hist2_str else "")
                                        + "└─────────────\n")
                            msg += "\n"
                        elif geo.get("sectors"):
                            msg += f"📊 관련 섹터: {', '.join(geo['sectors'])}\n"
                        if geo.get("summary"):
                            msg += f"\n💡 {geo['summary']}"
                        _gadj = int(geo.get("score_adj", 0) or 0)
                        msg += f"\n\n전체 점수 보정: {_gadj:+d}점"
                        send(msg)
                    except Exception as e:
                        send(f"❌ 오류: {e}")
                threading.Thread(target=_run_geo, daemon=True).start()

            # ── /us — 미국 시장 현황 수동 조회 ──
            elif text == "/us":
                try:
                    _us_cache.clear()  # 캐시 무효화 → 강제 갱신
                    us = get_us_market_signals()
                    gap_emoji = {"gap_up":"⬆️ 갭상승 기대","flat":"➡️ 갭 없음","gap_down":"⬇️ 갭하락 주의"}
                    regime_kor = {"panic":"🔴 패닉","risk_off":"🟠 위험회피","neutral":"🔵 중립","risk_on":"🟢 위험선호"}
                    msg = (f"🌐 <b>미국 시장 현황</b>\n"
                           f"━━━━━━━━━━━━━━━\n"
                           f"나스닥선물: {us.get('nasdaq_chg',0):+.2f}%\n"
                           f"VIX 공포지수: {us.get('vix',0):.1f}\n"
                           f"달러인덱스: {us.get('dxy',0):.2f}\n"
                           f"시장 국면: {regime_kor.get(us.get('us_regime','neutral'),'🔵 중립')}\n"
                           f"갭 예측: {gap_emoji.get(us.get('gap_signal','flat'),'➡️')}\n"
                           f"점수 보정: {int(us.get('score_adj',0) or 0):+d}점")
                    send(msg)
                except Exception as e:
                    send(f"❌ 미국 시장 조회 오류: {e}")

            # ── /overnight — 오버나이트 모니터 수동 실행 ──
            elif text == "/overnight":
                send("🌙 오버나이트 모니터 수동 실행 중...")
                def _run_overnight():
                    try:
                        run_overnight_monitor()
                        # 추적 중 종목 위험도도 체크
                        send_overnight_risk_alerts()
                    except Exception as e:
                        send(f"❌ 오류: {e}")
                threading.Thread(target=_run_overnight, daemon=True).start()

            elif text.startswith("/test"):
                # /test — 봇 전체 기능 빠른 점검
                send(
                    f"🧪 <b>기능 점검</b>  {BOT_VERSION}\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"/us — 미국 시장 현황\n"
                    f"/geo — 지정학 뉴스 분석\n"
                    f"/overnight — 오버나이트 위험도\n"
                    f"/stats — 신호 통계\n"
                    f"/top — 오늘 TOP 5\n"
                    f"/nxt — NXT 동향"
                )

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

        _write_json_atomic(SIGNAL_LOG_FILE, data, indent=2)

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

        _write_json_atomic(SIGNAL_LOG_FILE, data, indent=2)

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
            _write_json_atomic(SIGNAL_LOG_FILE, sig_data, indent=2)

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
            _write_json_atomic(SIGNAL_LOG_FILE, sig_data, indent=2)
            matched_name = name_input

        if early_matched:
            _write_json_atomic(EARLY_LOG_FILE, early_data, indent=2)

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



# ============================================================
# 🌙 오버나이트 위험도 계산
# ============================================================
def calc_overnight_risk(code: str, name: str, entry: int, current_pnl: float) -> dict:
    """
    장 마감 후 보유 위험도 계산.
    미국 시장 방향 + 공매도 잔고 + VIX 조합.
    반환: {level: "high"/"mid"/"low", score: int, reason: str}
    """
    try:
        us         = get_us_market_signals()
        short_r    = get_short_sell_ratio(code)
        vix        = us.get("vix", 20)
        us_regime  = us.get("us_regime", "neutral")
        gap_signal = us.get("gap_signal", "flat")

        risk_score = 0
        reasons    = []

        # NXT 시간대 → 거래량 얇아서 변동성 추가
        nxt_only = is_nxt_open() and not is_market_open()
        if nxt_only:
            risk_score += 10; reasons.append("🔵 NXT 단독 시간대 (유동성 낮음)")

        if us_regime == "panic":
            risk_score += 40; reasons.append("🔴 미국 패닉장")
        elif us_regime == "risk_off":
            risk_score += 20; reasons.append("🟠 미국 위험회피")

        if vix >= 30:
            risk_score += 20; reasons.append(f"🔴 VIX {vix:.0f} (공포)")
        elif vix >= 25:
            risk_score += 10; reasons.append(f"🟠 VIX {vix:.0f} (불안)")

        if short_r >= 10:
            risk_score += 15; reasons.append(f"📉 공매도 {short_r:.1f}%")
        elif short_r >= 5:
            risk_score += 7; reasons.append(f"⚠️ 공매도 {short_r:.1f}%")

        if gap_signal == "gap_down":
            risk_score += 15; reasons.append("⬇️ 갭하락 가능성")

        if current_pnl > 5:
            risk_score -= 10; reasons.append(f"✅ 현재 +{current_pnl:.1f}% 수익 중")

        if   risk_score >= 50: level = "high"
        elif risk_score >= 25: level = "mid"
        else:                  level = "low"

        level_emoji = {"high": "🔴 위험", "mid": "🟡 주의", "low": "🟢 안전"}
        return {
            "level":  level,
            "score":  risk_score,
            "reason": f"{level_emoji[level]}  {'  '.join(reasons)}"
        }
    except:
        return {"level": "low", "score": 0, "reason": ""}

# ============================================================
# 🔄 테마 로테이션 감지
# ============================================================
_theme_rotation_cache: dict = {"ts": 0, "themes": {}}

def detect_theme_rotation() -> dict:
    """
    THEME_MAP 기반 테마별 평균 등락률 계산 → 강세/약세 테마 감지.
    1시간 캐시. 반환: {강한테마: [], 약한테마: [], ts}
    """
    if time.time() - _theme_rotation_cache["ts"] < 3600:
        return _theme_rotation_cache

    theme_scores = {}
    try:
        for theme_key, theme_info in list(THEME_MAP.items())[:10]:  # 상위 10개 테마
            stocks   = theme_info.get("stocks", [])[:5]  # 테마당 5개만
            chg_list = []
            for code, name in stocks:
                try:
                    cur = get_stock_price(code)
                    if cur and cur.get("change_rate") is not None:
                        chg_list.append(cur["change_rate"])
                    time.sleep(0.1)
                except: continue
            if chg_list:
                theme_scores[theme_key] = round(sum(chg_list) / len(chg_list), 2)

        sorted_themes = sorted(theme_scores.items(), key=lambda x: -x[1])
        strong = [(k, v) for k, v in sorted_themes if v >= 2.0][:3]
        weak   = [(k, v) for k, v in sorted_themes if v <= -1.5][:3]

        _theme_rotation_cache.update({
            "ts":      time.time(),
            "themes":  theme_scores,
            "strong":  strong,
            "weak":    weak,
        })
    except Exception as e:
        _log_error("detect_theme_rotation", e)

    return _theme_rotation_cache

# ============================================================
# 💸 놓친 수익 추적
# ============================================================
def get_missed_profit_summary() -> dict:
    """
    signal_log에서 미진입(actual_entry=False 또는 None) 건의
    이론 수익률 집계 → "놓친 수익" 통계.
    반환: {count, avg_pnl, total_pnl, best: dict}
    """
    try:
        data = {}
        try:
            with open(SIGNAL_LOG_FILE, "r") as f: data = json.load(f)
        except: pass

        missed = [v for v in data.values()
                  if v.get("actual_entry") in (False, None)
                  and v.get("status") in ("수익", "손실", "본전")
                  and v.get("pnl_pct") is not None]

        if not missed:
            return {"count": 0, "avg_pnl": 0.0, "total_pnl": 0.0, "best": None}

        pnls     = [v["pnl_pct"] for v in missed]
        avg_pnl  = round(sum(pnls) / len(pnls), 1)
        best_rec = max(missed, key=lambda x: x.get("pnl_pct", 0))

        return {
            "count":     len(missed),
            "avg_pnl":   avg_pnl,
            "total_pnl": round(sum(pnls), 1),
            "best":      best_rec,
        }
    except:
        return {"count": 0, "avg_pnl": 0.0, "total_pnl": 0.0, "best": None}

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

        # ── 놓친 수익 ──
        try:
            missed = get_missed_profit_summary()
            if missed["count"] >= 3:
                best  = missed.get("best") or {}
                b_str = f"  최고: {best.get('name','')} {best.get('pnl_pct',0):+.1f}%" if best else ""
                msg  += (f"💸 <b>놓친 수익</b>  {missed['count']}건  "
                         f"평균 {missed['avg_pnl']:+.1f}%  합계 {missed['total_pnl']:+.1f}%\n"
                         f"{b_str}\n"
                         f"━━━━━━━━━━━━━━━\n")
        except: pass

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
            "feat_w_geo":    "지정학 보정",
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
    # [v37.10-all5] 성과 기반 유니버스 자동 갱신(장 마감)
    update_universe_from_performance(days=int(os.getenv('UNIVERSE_PERF_DAYS','30') or '30'), max_codes=int(os.getenv('UNIVERSE_PERF_MAX','300') or '300'))
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

    # ── ⓪ 미국 시장 요약 + 갭 예측 + 오버나이트 요약 ──
    try:
        us = get_us_market_signals()
        if us.get("summary"):
            gap_emoji = {"gap_up":"⬆️ 갭상승 기대","flat":"➡️ 갭 없음","gap_down":"⬇️ 갭하락 주의"}
            msg += (f"\n🌐 <b>미국 시장</b>\n"
                    f"  {us['summary']}\n"
                    f"  {gap_emoji.get(us.get('gap_signal','flat'),'➡️')}\n")
        # 오버나이트 중 발생한 이벤트 요약
        overnight_lines = _overnight_state.get("summary_lines", [])
        if overnight_lines:
            msg += f"\n🌙 <b>오버나이트 이벤트</b>\n"
            for line in overnight_lines[-5:]:  # 최근 5개만
                msg += f"  {line}\n"
        _overnight_state["summary_lines"] = []  # 브리핑 후 초기화
    except: pass

    # ── ⓪-A 지정학 이벤트 요약 ──
    try:
        if _geo_event_state.get("active") and time.time() - _geo_event_state.get("ts",0) < 14400:
            geo_sum = _geo_event_state.get("summary","")
            geo_sec = _geo_event_state.get("sectors",[])
            geo_unc = _geo_event_state.get("uncertainty","low")
            unc_emoji = {"high":"🔴","mid":"🟠","low":"🟢"}.get(geo_unc,"🟠")
            msg += (f"\n🌍 <b>지정학 이벤트</b>  {unc_emoji} 불확실성 {geo_unc.upper()}\n"
                    f"  {geo_sum}\n"
                    f"  관련 섹터: {', '.join(geo_sec)}\n")
    except: pass

    # ── ⓪-B 테마 로테이션 ──
    try:
        rotation = detect_theme_rotation()
        strong = rotation.get("strong", [])
        weak   = rotation.get("weak", [])
        if strong or weak:
            msg += "\n🔄 <b>테마 로테이션</b>\n"
            for k, v in strong:
                msg += f"  🟢 {k} 강세 ({v:+.1f}%)\n"
            for k, v in weak:
                msg += f"  🔴 {k} 약세 ({v:+.1f}%)\n"
    except: pass

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
                    # v37.0: 동일 종목 과거 전적
                    _tr = get_stock_track_record(code, info.get("name",""))
                    if _tr:
                        msg += f"  {_tr}\n"
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

    # v37.0: 현재 시장 국면에서의 과거 신호 승률
    try:
        _cur_regime = get_market_regime()
        _r_hist = get_regime_history(_cur_regime)
        if _r_hist:
            regime_kor = {"crisis":"위기","risk_off":"위험회피","normal":"보통","bull":"강세","euphoria":"과열"}
            msg += f"\n📊 <b>시장 국면</b>: {regime_kor.get(_cur_regime, _cur_regime)}\n  {_r_hist}\n"
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

        # v37.0: 역대 대비 비교
        weekly_compare = ""
        try:
            weekly_compare = get_weekly_comparison(week_recs)
        except: pass

        send(
            f"📅 <b>주간 자동 리포트</b>\n"
            f"{this_mon[:4]}.{this_mon[4:6]}.{this_mon[6:]} ~ {this_fri[:4]}.{this_fri[4:6]}.{this_fri[6:]}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"{report_text}"
            f"{weekly_compare}"
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
        # ── 미국 시장 선행 지표 반영 ──
        try:
            us = get_us_market_signals()
            us_regime = us.get("us_regime", "neutral")
            # 미국 panic → 한국도 강제 crash
            if us_regime == "panic" and mode != "crash":
                mode = "crash"
            # 미국 risk_off → 한국 한 단계 보수적
            elif us_regime == "risk_off" and mode == "bull":
                mode = "normal"
            elif us_regime == "risk_off" and mode == "normal":
                mode = "bear"
            # 미국 risk_on + 한국 normal → bull 상향
            elif us_regime == "risk_on" and mode == "normal" and chg_5d >= 1.0:
                mode = "bull"
            _regime_cache["us_regime"]   = us_regime
            _regime_cache["us_summary"]  = us.get("summary", "")
            _regime_cache["gap_signal"]  = us.get("gap_signal", "flat")
        except: pass

        _dynamic["regime_mode"]       = mode
        _dynamic["regime_score_mult"] = mult_map[mode]
        _dynamic["regime_min_add"]    = add_map[mode]

    except Exception as e:
        _log_error("get_market_regime", e)

    return _regime_cache

def regime_label() -> str:
    r = get_market_regime()
    labels = {"bull":"🟢 상승장","normal":"🔵 보통장","bear":"🟠 하락장","crash":"🔴 급락장"}
    return labels.get(r.get("mode","normal"), "🔵 보통장")


# ============================================================
# 🌐 미국 시장 선행 지표 (Yahoo Finance — 인증 불필요)
# ============================================================
_us_cache: dict = {"ts": 0}  # 1시간 캐시
_geo_event_state: dict = {
    "active":        False,
    "uncertainty":   "low",
    "sectors":       [],
    "score_adj":     0,
    "summary":       "",
    "entities":      [],
    "ts":            0,
    "last_sent_ts":  0,
}


# ============================================================
# 📉 공매도 잔고 비율 + 외국인 연속 순매수
# ============================================================
_short_cache:   dict = {}  # code → {ratio, ts}
_foreign_cache: dict = {}  # code → {days, ts}


# ============================================================
# 📢 공시 전 이상 거래량 감지 (선매수 세력 포착)
# ============================================================
_pre_dart_cache: dict = {}  # code → {ts, detected}

def detect_pre_dart_volume(code: str, name: str) -> dict:
    """
    DART 공시 직전 이상 거래량 감지.
    최근 1시간 내 거래량이 5일 평균의 3배 이상이고,
    아직 공시가 없는 상태 → 선매수 세력 감지.
    반환: {detected: bool, vol_ratio: float, score_adj: int, reason: str}
    """
    cached = _pre_dart_cache.get(code)
    if cached and time.time() - cached.get("ts", 0) < 1800:
        return cached

    result = {"detected": False, "vol_ratio": 0.0, "score_adj": 0, "reason": "", "ts": time.time()}
    try:
        # 현재 거래량 비율 (Z-score 계산용)
        cur  = get_stock_price(code)
        if not cur:
            return result
        vol_ratio = cur.get("volume_ratio", 0)

        # 거래량 급증 (5일 평균 대비 5배 이상) 이면서 공시 없으면 의심
        if vol_ratio >= 5.0:
            # 최근 DART 공시 확인 (2시간 이내)
            today_str   = datetime.now().strftime("%Y%m%d")
            dart_list   = _fetch_dart_list(today_str) if DART_API_KEY else []
            recent_dart = [d for d in dart_list if d.get("stock_code") == code]

            if not recent_dart:
                # 공시 없는데 거래량 폭발 → 선매수 의심
                score_adj = 10 if vol_ratio >= 10 else 6
                reason    = f"🚨 공시 전 이상 거래량 {vol_ratio:.1f}배 — 선매수 감지 (+{score_adj}점)"
                result.update({"detected": True, "vol_ratio": vol_ratio,
                                "score_adj": score_adj, "reason": reason})
            else:
                # 공시 나온 후 거래량 → 일반 반응
                result.update({"detected": False, "vol_ratio": vol_ratio,
                                "score_adj": 3, "reason": f"📢 공시 후 거래량 반응 {vol_ratio:.1f}배"})

        _pre_dart_cache[code] = result
    except Exception as e:
        _log_error(f"detect_pre_dart_volume({code})", e)

    return result

def get_short_sell_ratio(code: str) -> float:
    """
    공매도 잔고 비율 조회 (KIS API 기반).
    반환: 0~100 (%) — 5% 이상이면 공매도 압력 높음
    """
    cached = _short_cache.get(code)
    if cached and time.time() - cached["ts"] < 3600:
        return cached["ratio"]
    try:
        token  = get_token()
        url    = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/quotations/inquire-short-balance"
        headers = {
            "Authorization": f"Bearer {token}",
            "appkey":    KIS_APP_KEY,
            "appsecret": KIS_APP_SECRET,
            "tr_id":     "SHSHORT030R",
            "Content-Type": "application/json; charset=utf-8",
        }
        params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
        resp  = requests.get(url, headers=headers, params=params, timeout=5)
        data  = resp.json()
        ratio = float(data.get("output", {}).get("ssts_rsqn_rate", 0) or 0)
        _short_cache[code] = {"ratio": ratio, "ts": time.time()}
        return ratio
    except:
        return 0.0

def _get_daily_investor_data(code: str) -> list:
    """
    KIS API: 일별 외국인/기관 순매수 데이터 (최근 20일).
    반환: [{date, foreign_net, institution_net}, ...]
    """
    try:
        end   = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        if _daily_trade_api_disabled_today():
            return None
        url   = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-trade"
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD":  code,
            "FID_INPUT_DATE_1": start,
            "FID_INPUT_DATE_2": end,
            "FID_PERIOD_DIV_CODE": "D",
        }
        data = _safe_get(url, "FHKST03010400", params)
        items = data.get("output2", []) if data else []
        result = sorted([{
            "date":            i.get("stck_bsop_date", ""),
            "foreign_net":     int(i.get("frgn_ntby_qty", 0) or 0),
            "institution_net": int(i.get("orgn_ntby_qty",  0) or 0),
        } for i in items if i.get("stck_bsop_date")], key=lambda x: x["date"])
        return result[-20:]
    except:
        return []

def get_foreign_consecutive_days(code: str) -> int:
    """
    외국인 연속 순매수/순매도일.
    양수: 연속 순매수일, 음수: 연속 순매도일
    KIS 일별 투자자 데이터 사용 (1시간 캐시)
    """
    cached = _foreign_cache.get(code)
    if cached and time.time() - cached.get("ts", 0) < 3600:
        return cached.get("days", 0)
    try:
        items = _get_daily_investor_data(code)
        days = 0; sign = None
        for item in reversed(items):
            f_net    = item.get("foreign_net", 0)
            cur_sign = 1 if f_net > 0 else (-1 if f_net < 0 else 0)
            if cur_sign == 0: break
            if sign is None: sign = cur_sign
            if cur_sign != sign: break
            days += 1
        result = days * (sign or 1)
        _foreign_cache[code] = {"days": result, "inst_days": 0, "ts": time.time()}
        # 기관도 같이 계산해서 캐시
        inst_days = 0; inst_sign = None
        for item in reversed(items):
            i_net    = item.get("institution_net", 0)
            cur_sign = 1 if i_net > 0 else (-1 if i_net < 0 else 0)
            if cur_sign == 0: break
            if inst_sign is None: inst_sign = cur_sign
            if cur_sign != inst_sign: break
            inst_days += 1
        _foreign_cache[code]["inst_days"] = inst_days * (inst_sign or 1)
        return result
    except:
        return 0

def get_institution_consecutive_days(code: str) -> int:
    """기관 연속 순매수/순매도일 (외국인 캐시 공유)"""
    cached = _foreign_cache.get(code)
    if cached and time.time() - cached.get("ts", 0) < 3600:
        return cached.get("inst_days", 0)
    get_foreign_consecutive_days(code)  # 캐시 갱신
    return _foreign_cache.get(code, {}).get("inst_days", 0)


def get_us_market_signals() -> dict:
    """
    나스닥 선물(NQ=F), VIX(^VIX), 달러인덱스(DX-Y.NYB) 조회.
    Yahoo Finance JSON API 사용 (무료, pip 설치 불필요).
    반환:
      nasdaq_chg  : 나스닥 선물 등락률 (%)
      vix         : VIX 공포지수
      dxy         : 달러인덱스
      us_regime   : "risk_on" / "neutral" / "risk_off" / "panic"
      gap_signal  : "gap_up" / "flat" / "gap_down"  (다음날 갭 예측)
      score_adj   : 신호 점수 보정값 (-15 ~ +10)
      summary     : 텔레그램 표시용 요약 문자열
    """
    if time.time() - _us_cache.get("ts", 0) < 3600:
        return _us_cache

    result = {
        "ts": time.time(), "nasdaq_chg": 0.0, "vix": 20.0,
        "dxy": 104.0, "us_regime": "neutral",
        "gap_signal": "flat", "score_adj": 0, "summary": ""
    }
    try:
        symbols = {"NQ=F": "nasdaq", "^VIX": "vix", "DX-Y.NYB": "dxy"}
        values  = {}
        for sym, key in symbols.items():
            try:
                url  = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=2d"
                resp = requests.get(url, timeout=8, headers=_random_ua())
                data = resp.json()
                meta = data["chart"]["result"][0]["meta"]
                prev = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
                prev_close = [c for c in prev if c is not None]
                cur_price  = meta.get("regularMarketPrice", 0)
                if key == "nasdaq" and prev_close:
                    values["nasdaq_chg"] = round((cur_price - prev_close[-1]) / prev_close[-1] * 100, 2)
                elif key == "vix":
                    values["vix"] = round(cur_price, 1)
                elif key == "dxy":
                    values["dxy"] = round(cur_price, 2)
                time.sleep(0.3)
            except: pass

        nasdaq_chg = values.get("nasdaq_chg", 0.0)
        vix        = values.get("vix", 20.0)
        dxy        = values.get("dxy", 104.0)

        # ── 미국 시장 국면 판단 ──
        if vix >= 35 or nasdaq_chg <= -3.0:
            us_regime  = "panic"
            score_adj  = -15
            gap_signal = "gap_down"
        elif vix >= 25 or nasdaq_chg <= -1.5:
            us_regime  = "risk_off"
            score_adj  = -8
            gap_signal = "gap_down" if nasdaq_chg <= -2.0 else "flat"
        elif vix <= 15 and nasdaq_chg >= 1.0:
            us_regime  = "risk_on"
            score_adj  = +8
            gap_signal = "gap_up"
        elif nasdaq_chg >= 0.5:
            us_regime  = "risk_on"
            score_adj  = +4
            gap_signal = "flat"
        else:
            us_regime  = "neutral"
            score_adj  = 0
            gap_signal = "flat"

        # ── 달러 강세 → 외국인 매도 압력 ──
        if dxy >= 107:
            score_adj -= 5  # 달러 강세: 외국인 매도 가능성

        # ── 요약 문자열 ──
        regime_emoji = {"panic":"🔴","risk_off":"🟠","neutral":"🔵","risk_on":"🟢"}
        gap_emoji    = {"gap_up":"⬆️","flat":"➡️","gap_down":"⬇️"}
        summary = (f"{regime_emoji.get(us_regime,'🔵')} 나스닥선물 {nasdaq_chg:+.1f}%  "
                   f"VIX {vix:.0f}  DXY {dxy:.1f}  "
                   f"갭예측 {gap_emoji.get(gap_signal,'➡️')} {gap_signal}")

        result.update({
            "ts": time.time(), "nasdaq_chg": nasdaq_chg, "vix": vix,
            "dxy": dxy, "us_regime": us_regime, "gap_signal": gap_signal,
            "score_adj": score_adj, "summary": summary
        })
        MARKET_REGIME.update(compute_market_regime(nasdaq_chg, vix, dxy))
        _us_cache.update(result)
        print(f"  🌐 미국 시장: {summary}")

    except Exception as e:
        _log_error("get_us_market_signals", e)

    return result

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
        _rm   = get_atr_regime_mult()
        _stop_pct   = max(0.05, 0.07 * _rm)
        _target_pct = max(0.08, 0.15 / _rm)
        stop   = int(entry * (1 - _stop_pct)   / 10) * 10
        target = int(entry * (1 + _target_pct) / 10) * 10
        return stop, target, round(_stop_pct*100,1), round(_target_pct*100,1), False

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
                    # 같은 섹터 내 max_same_sector 개수까지는 허용
                    same_sector_passed = sum(
                        1 for p in passed
                        if calc_real_sector_score(s["code"], p["code"], s["name"], p["name"]).get("score", 0) >= 50
                    )
                    _max_same = _dynamic.get("max_same_sector", 2)
                    if same_sector_passed >= _max_same:
                        excluded.add(peer["code"])
                        print(f"  🗂️ 실질섹터 중복 제외: {_resolve_stock_name(peer['code'], peer.get('name',''))} ({rs['label']}, {rs['score']}점, 섹터내 {same_sector_passed}/{_max_same})")
            except:
                pass

    if len(passed) < len(sorted_alerts):
        skipped = len(sorted_alerts) - len(passed)
        print(f"  🗂️ 포트폴리오 필터: {skipped}개 제외 ({regime}장, 최대 {max_total}개)")

    return passed

# v37.0: schedule lambda → 명명 함수 (에러 추적 가능)
def _on_market_open():
    """장 시작 시 초기화 — schedule에서 호출"""
    if is_holiday(): return
    _clear_all_cache()
    _overnight_state.update({"last_us_regime":"neutral","last_vix":20.0,
                              "alerted_regime":"","summary_lines":[]})
    reset_top_signals_daily()
    refresh_dynamic_candidates()
    send(f"🌅 <b>장 시작!</b>  {datetime.now().strftime('%Y-%m-%d')}\n"
         f"📂 이월: {len(_detected_stocks)}개  |  📡 전체 스캔 시작")

def run_scan():
    code = ""  # HOTFIX: prevent NameError in exception paths
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
                if is_scoring_only_instrument(s.get("code", ""), s.get("name", "")):
                    print(f"  ⏭ 점수전용 종목 제외: {s.get('name', s.get('code',''))}")
                    continue
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
        run_entry_defense_monitor()  # 🛡 장마감 손익 방어 가이드
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

    install_excepthook()
    update_dashboard(force=True)

    # Persistent storage init (코드 교체/배포에도 데이터/조건 보존)
    _migrate_legacy_files()
    _storage_diagnostics_once()

    _load_kr_holidays(datetime.now().year)

    # ── 공휴일/주말 → 종료 대신 대기 모드로 전환 ──
    if is_holiday():
        print(f"📅 오늘은 공휴일/주말 — 대기 모드로 실행")
        try:
            send(
                f"😴 <b>주말/공휴일 대기 모드</b>  {BOT_VERSION}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📡 스캔은 멈추고 명령어만 응답해요\n\n"
                f"사용 가능한 명령어:\n"
                f"/us — 미국 시장 현황\n"
                f"/geo — 지정학 뉴스 분석\n"
                f"/stats — 신호 통계\n"
                f"/list — 감시 종목 목록\n"
                f"/overnight — 오버나이트 위험도"
            )
        except: pass

        # 대기 모드: 텔레그램 명령어 + 오버나이트 모니터만 실행
        _strict_cleanup_legacy_entry_hits()
        load_carry_stocks()
        _load_dynamic_params()
        schedule.every(10).seconds.do(poll_telegram_commands)
        schedule.every(30).minutes.do(run_overnight_monitor)
        schedule.every(60).minutes.do(run_geo_news_scan)

        print("✅ 대기 모드 스케줄 등록 완료")
        while True:
            schedule.run_pending()
            time.sleep(1)

    _strict_cleanup_legacy_entry_hits()
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
        "• 뉴스 (6개 소스): <b>45초</b>\n"
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
    schedule.every(30).minutes.do(_prune_all_caches)  # v37.0: 캐시 메모리 관리
    schedule.every().day.at("07:30").do(send_preopen_watchlist)  # v37.9: 익개장 전 워치리스트 요약
    schedule.every().day.at("08:50").do(send_premarket_briefing)
    schedule.every(10).minutes.do(lambda: update_dashboard(force=False))
    # TOP 5: 10:00부터 장마감까지 1시간마다 자동 발송
    # KRX only 종목: ~15:30, NXT 상장 종목 포함 시: ~20:00
    for _top_hhmm in ["10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00"]:
        schedule.every().day.at(_top_hhmm).do(
            lambda: None if is_holiday() or not is_any_market_open() else send_top_signals()
        )
    schedule.every().day.at(MARKET_OPEN).do(_on_market_open)  # v37.0: 명명 함수
    schedule.every().day.at(MARKET_CLOSE).do(
        lambda: None if is_holiday() else on_market_close()
    )
    # 오버나이트 위험 알림 (15:10 — KRX 마감 20분 전, 매도 가능 시간)
    schedule.every().day.at("15:10").do(
        lambda: None if is_holiday() else send_overnight_risk_alerts()
    )
    # NXT 오버나이트 위험 알림 (19:40 — NXT 마감 20분 전, 매도 가능 시간)
    schedule.every().day.at("19:40").do(
        lambda: None if is_holiday() else send_overnight_risk_alerts()
    )
    # NXT 완전 마감 후 잔여 재진입 감시 초기화 + 결과 미입력 알림 (NXT 상장 종목용)
    schedule.every().day.at("20:05").do(
        lambda: (
            _reentry_watch.clear(),
            _send_pending_result_reminder(),   # NXT 마감 후 최종 미입력 알림
            print("🔵 NXT 마감(20:00) — 재진입 감시 전체 초기화")
        ) if not is_holiday() else None
    )
    # 오버나이트 모니터링 (30분마다 — 함수 내부에서 시간대 체크)
    schedule.every(30).minutes.do(run_overnight_monitor)
    # 지정학 뉴스 스캔 (1시간마다)
    schedule.every(60).minutes.do(run_geo_news_scan)

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