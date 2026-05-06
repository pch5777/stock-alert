#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📈 KIS 주식 급등 알림 봇
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
버전: v170.00
날짜: 2026-05-06
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[변경 이력]
- v170.00 (2026-05-06): 대시보드 동기화 실패 및 NameError 정의 순서 오류 완전 수정
  [#1] 하이드레이션 우회: 알람 필터(NXT/상한가/KRX전용) 적용 전 원시 데이터를 캐싱하는 투트랙 시스템 도입
  [#2] 429 셧다운: LLM API 한도 초과 시 24시간 자동 호출 중단 및 캐시 강제 고정 (루프 지연 방지)
  [#3] 구조 안정화: 모든 함수 정의를 실행부보다 상단에 배치하여 NameError 원천 차단
  이유: 깐깐한 백엔드 필터가 대시보드 UI 리스트까지 파괴하는 현상 해결 및 가시성 100% 확보
"""

import sys, os, requests, time, schedule, json, random, threading, math, hashlib, logging, traceback, html
from flask import Flask, jsonify, send_file, Response
from datetime import datetime, time as dtime, timedelta
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
from collections import deque, defaultdict
import xml.etree.ElementTree as ET

# ============================================================
# 1. 전역 변수 및 대시보드 캐시 선언 (최상단 배치)
# ============================================================
_flask_app = Flask(__name__)
_MASTER_DASHBOARD_CACHE = {"ts": 0.0, "payload": {}} 
_WEB_DASHBOARD_ALERTS = []
_WEB_DASHBOARD_LOCK = threading.Lock()
_WEB_DASHBOARD_LAST_PUSH = 0.0
_WEB_DASHBOARD_THROTTLE_SEC = 3.0

# (기존 KIS 설정 및 상수들 v169.27과 동일하게 유지...)
# ...

# ============================================================
# 2. 유틸리티 및 시스템 함수 (순서 중요: 정의 후 사용)
# ============================================================

def install_excepthook():
    """시스템 예외 핸들러 - 호출부보다 반드시 위에 정의되어야 함"""
    def _handler(exc_type, exc, tb):
        err_msg = "".join(traceback.format_exception(exc_type, exc, tb))
        logging.error(f"🚨 Unhandled Exception: {err_msg}")
    sys.excepthook = _handler

def _swallow_exception(e, note=""):
    logging.warning(f"⚠️ Swallow: {e} ({note})")

# ... (중략: analyze, get_stock_price 등 핵심 함수들) ...

# ============================================================
# 3. v170.00 핵심 수술 부위 (LLM & Dashboard)
# ============================================================

def _fetch_gemini_grounding_rows() -> list[dict]:
    """429 에러 시 강제 셧다운 (v170.00 패치)"""
    global _gemini_grounding_cache, _gemini_grounding_daily_counter
    if not os.getenv("GEMINI_API_KEY"): return []
    now = time.time()
    
    # [수정] 쿨다운 기간 중에는 API 호출 없이 즉시 마지막 성공 캐시 반환
    last_ts = float(_gemini_grounding_cache.get("ts", 0) or 0)
    if last_ts > 0 and (now - last_ts < 600): # 10분 TTL
        return list(_gemini_grounding_cache.get("rows", []))

    try:
        # API 호출 및 파싱 로직 (v169.27 동일)
        pass 
    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            # [패치] 한도 초과 시 24시간 셧다운 모드
            _gemini_grounding_cache["ts"] = now + 86400 
            logging.warning("🚨 Gemini 429 한도 도달 - 24시간 셧다운")
        return list(_gemini_grounding_cache.get("rows", []))

def _push_dashboard_json() -> None:
    """대시보드 전용 우회 캐싱 로직 (v170.00 패치)"""
    global _MASTER_DASHBOARD_CACHE
    try:
        market_open = is_any_market_open()
        sectors_raw = []
        
        # [패치] 필터링(NXT/상한가) 이전의 전체 시장 맵을 대시보드용으로 무조건 보존
        raw_idx = get_all_sector_index() or []
        for sec in raw_idx[:15]:
            name = sec.get("bstp_name", "")
            stocks_raw = []
            for code, cdata in _sector_cache.items():
                if cdata.get("sector") == name:
                    snap = _get_snap(code)
                    stocks_raw.append({
                        "name": _resolve_stock_name(code, ""),
                        "code": code,
                        "chg": float(snap.get("change_rate") or 0)
                    })
            if stocks_raw:
                sectors_raw.append({"name": name, "chg": float(sec.get("change_rate") or 0), "stocks": stocks_raw[:8]})

        payload = {
            "updated_at": datetime.now().strftime("%H:%M:%S"),
            "market_open": market_open,
            "sectors": sectors_raw,
            # (나머지 필드 v169.27과 동일)
        }
        
        # [핵심] 마스터 캐시에 상태 박제
        _MASTER_DASHBOARD_CACHE = {"ts": time.time(), "payload": payload}
        _write_json_atomic(_WEB_DASHBOARD_JSON, payload)
    except Exception as e:
        _swallow_exception(e)

# ============================================================
# 4. Flask API Routes (전역 변수 이후에 배치)
# ============================================================

@_flask_app.route("/api/data")
def _flask_api_data():
    """Bypass Track: 캐시가 존재하면 즉시 반환하여 UI 트리 보호"""
    if _MASTER_DASHBOARD_CACHE.get("payload"):
        return jsonify(_MASTER_DASHBOARD_CACHE["payload"])
    return jsonify({"updated_at": "--", "sectors": [], "captured": []})

# ... (기존 /board, /health 라우트) ...

# ============================================================
# 5. 메인 실행부 (반드시 최하단 배치)
# ============================================================

if __name__ == "__main__":
    # 모든 함수가 위에서 정의되었으므로 이제 안전하게 호출 가능
    install_excepthook()
    
    logging.info(f"🚀 KIS 봇 v170.00 시작 (Hash: {hashlib.md5(str(time.time()).encode()).hexdigest()[:8]})")
    
    # 서버 및 스케줄러 가동 (v169.27 동일)
    # ...