#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📈 KIS 주식 급등 알림 봇
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
버전: v170.00
날짜: 2026-05-06
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[변경 이력]
- v170.00 (2026-05-06): 대시보드 섹터 동기화 실패 및 런타임 NameError 완전 수정
  [#1] 선언 순서 교정: threading 및 Flask 인스턴스 위치를 최상단으로 이동 (NameError 해결)
  [#2] 대시보드 투트랙 하이드레이션: 알람 필터(NXT/상한가/KRX전용) 우회 전용 캐시 신설
  [#3] LLM API 방어: 429 발생 시 24시간 자동 셧다운 및 기존 캐시 강제 고정
  [#4] Flask API 우회: /api/data 요청 시 메모리 스냅샷 즉시 반환 (Bypass)
  이유: 백엔드 필터가 대시보드 UI를 파괴하는 현상 해결 및 API 한도 초과 시 루프 지연 방지
"""

import sys
import builtins
import hashlib
import logging
import traceback
import re as _re
import os, requests, time, schedule, json, random, threading, math
from flask import Flask as _Flask, jsonify as _jsonify, send_file as _send_file, Response as _FlaskResponse
from collections import deque, defaultdict
import xml.etree.ElementTree as ET
import html
from datetime import datetime, time as dtime, timedelta
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup

# [v170.00 핵심] Flask 인스턴스 및 대시보드 캐시를 상단에 배치하여 decorators 참조 에러 방지
_flask_app = _Flask(__name__)
_MASTER_DASHBOARD_CACHE: dict = {"ts": 0.0, "payload": {}} 
_WEB_DASHBOARD_ALERTS: list  = []
_WEB_DASHBOARD_LOCK          = threading.Lock()
_WEB_DASHBOARD_LAST_PUSH: float = 0.0
_WEB_DASHBOARD_THROTTLE_SEC  = 3.0

# ... (중략: SIG_LABELS, SIG_TITLES 등 기존 상수 및 유틸 함수 v169.27과 동일) ...

# ── Flask Routes (v170.00 선언 위치 최상단 이동) ──────────────────────────

@_flask_app.route("/api/data")
def _flask_api_data():
    """Bypass Track - 마스터 캐시가 있으면 깐깐한 조건 없이 즉시 반환"""
    if _MASTER_DASHBOARD_CACHE.get("payload"):
        return _jsonify(_MASTER_DASHBOARD_CACHE["payload"])
    return _jsonify({"updated_at": "--", "sectors": [], "captured": []})

@_flask_app.route("/board")
def _flask_board():
    return _DASHBOARD_HTML, 200, {"Content-Type": "text/html; charset=utf-8"}

@_flask_app.route("/health")
def _flask_health():
    return "ok", 200

# ... (중략: KIS API 연동, 지표 계산, 스캔 로직 v169.27과 동일) ...

def _fetch_gemini_grounding_rows() -> list[dict]:
    """v170.00: 429 에러 시 24시간 강제 셧다운 (무한 재호출 방지)"""
    global _gemini_grounding_cache, _gemini_grounding_daily_counter
    if not GEMINI_API_KEY: return []
    now = time.time()
    
    # [v170.00 패치] rows 존재 여부와 무관하게 ts 쿨다운 우선 존중
    last_ts = float(_gemini_grounding_cache.get("ts", 0) or 0)
    if last_ts > 0 and (now - last_ts < GEMINI_GROUNDING_CACHE_TTL_SEC):
        return list(_gemini_grounding_cache.get("rows", []))

    today = _now_kst().strftime("%Y-%m-%d")
    if _gemini_grounding_daily_counter.get("date") != today:
        _gemini_grounding_daily_counter = {"date": today, "count": 0}
    
    if _gemini_grounding_daily_counter.get("count", 0) >= GEMINI_GROUNDING_DAILY_LIMIT:
        return list(_gemini_grounding_cache.get("rows", []))

    try:
        # (기존 v169.27 API 호출 로직...)
        pass 
    except Exception as e:
        _is_quota_err = any(k in str(e) for k in ("429", "quota", "RESOURCE_EXHAUSTED"))
        if _is_quota_err:
            # [v170.00 패치] 한도 도달 시 24시간 셧다운 적용
            _gemini_grounding_daily_counter["count"] = GEMINI_GROUNDING_DAILY_LIMIT
            _gemini_grounding_cache["ts"] = now + 86400 
        else:
            _gemini_grounding_cache["ts"] = now
        return list(_gemini_grounding_cache.get("rows", []))

# ... (중략: _fetch_groq_news_rows 동일하게 429 셧다운 로직 적용) ...

def _push_dashboard_json() -> None:
    """v170.00: 웹 대시보드 JSON 원자적 갱신 (투트랙 하이드레이션 적용)"""
    global _WEB_DASHBOARD_LAST_PUSH, _MASTER_DASHBOARD_CACHE
    now_ts = time.time()
    if now_ts - _WEB_DASHBOARD_LAST_PUSH < _WEB_DASHBOARD_THROTTLE_SEC:
        return
    _WEB_DASHBOARD_LAST_PUSH = now_ts
    try:
        market_open = is_any_market_open()
        sectors_raw = []
        
        # [v170.00 패치] 알람 필터링 이전의 '무결성 섹터 데이터' 조립 (Visibility 100%)
        sector_list = get_all_sector_index() or []
        for sec in sector_list[:15]:
            name = sec.get("bstp_name", "")
            if not name: continue
            
            stocks_raw = []
            # _sector_cache의 모든 종목을 필터(NXT/상한가/KRX전용) 없이 대시보드용으로 수집
            for code, cdata in _sector_cache.items():
                if cdata.get("sector") == name:
                    snap = _get_snap(code)
                    stocks_raw.append({
                        "name": _resolve_stock_name(code, ""),
                        "code": code,
                        "chg":  float(snap.get("change_rate") or 0),
                        "vol":  _fmt_vol(safe_int(snap.get("today_vol") or 0)),
                        "amt":  _fmt_amt(safe_int(snap.get("acml_tr_pbmn") or 0)),
                    })
            
            if stocks_raw:
                sectors_raw.append({
                    "name": name, 
                    "chg":  float(sec.get("change_rate") or 0), 
                    "stocks": sorted(stocks_raw, key=lambda x:-x["chg"])[:8]
                })

        # Captured 종목 조립... (v169.27 로직 유지)

        payload = {
            "updated_at":   datetime.now().strftime("%H:%M:%S"),
            "market_open":  market_open,
            "sectors":      sectors_raw if sectors_raw else _WEB_DASHBOARD_PREMARKET_SECTORS,
            "captured":     [], # (기존 포착 로직)
            "alerts":       list(_WEB_DASHBOARD_ALERTS),
            "rank_date":    datetime.now().strftime("%m-%d %H:%M"),
        }
        
        # [핵심] 인메모리 마스터 캐시 즉시 갱신
        _MASTER_DASHBOARD_CACHE = {"ts": time.time(), "payload": payload}
        _write_json_atomic(_WEB_DASHBOARD_JSON, payload)
    except Exception as e:
        _swallow_exception(e)

# ... (이하 메인 루프 및 시스템 코드 v169.27과 동일) ...

if __name__ == "__main__":
    install_excepthook()
    # (v169.27 초기화 시퀀스 동일하게 유지)
    # ...