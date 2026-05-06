#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📈 KIS 주식 급등 알림 봇
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
버전: v170.01
날짜: 2026-05-06
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[변경 이력]
- v170.01 (2026-05-06): 긴급 패치 - NameError: 'threading' is not defined 수정
  이유: v170.00에서 신설된 전역 락(Lock) 변수가 import 구문보다 상단에 배치됨
  수정: 변수 선언 위치를 import threading 이후(기존 전역변수 구역)로 조정

- v170.00 (2026-05-04): 대시보드 섹터 동기화 실패 및 LLM 429 루프 완전 수정
  [#1] 대시보드 투트랙 하이드레이션: 알람 필터(NXT/상한가/KRX전용) 우회 전용 캐시 신설
  [#2] LLM API 방어: 429/ResourceExhausted 발생 시 24시간 자동 셧다운 및 캐시 강제 유지
  [#3] Flask API 우회: /api/data 요청 시 마지막 정상 마스터 스냅샷 즉시 반환
"""

import sys
import builtins
import hashlib
import logging
import traceback
import re as _re
import os, requests, time, schedule, json, random, threading, math # threading 여기 있습니다.

# ... (중략: 기존 v169.27의 모든 상수 정의부 동일) ...

# ============================================================
# 🔒 Thread Safety & Global Dashboard State (v170.01 위치 조정)
# ============================================================
_file_lock  = threading.Lock()
_state_lock = threading.Lock()
_cache_lock = threading.Lock()
_kis_rate_lock = threading.Lock()
_WEB_DASHBOARD_LOCK = threading.Lock() # 안전한 위치로 이동됨

# [v170.00] 대시보드 전용 무결성 캐시 (Bypass Track)
_MASTER_DASHBOARD_CACHE: dict = {"ts": 0.0, "payload": {}} 

# ... (중략) ...

def _fetch_gemini_grounding_rows() -> list[dict]:
    """v170.00: 429 에러 시 강제 셧다운 및 캐시 유지"""
    global _gemini_grounding_cache, _gemini_grounding_daily_counter
    if not GEMINI_API_KEY: return []
    now = time.time()
    
    last_ts = float(_gemini_grounding_cache.get("ts", 0) or 0)
    if last_ts > 0 and (now - last_ts < GEMINI_GROUNDING_CACHE_TTL_SEC):
        return list(_gemini_grounding_cache.get("rows", []))

    today = _now_kst().strftime("%Y-%m-%d")
    if _gemini_grounding_daily_counter.get("date") != today:
        _gemini_grounding_daily_counter = {"date": today, "count": 0}
    
    if _gemini_grounding_daily_counter.get("count", 0) >= GEMINI_GROUNDING_DAILY_LIMIT:
        return list(_gemini_grounding_cache.get("rows", []))

    try:
        from google import genai as _genai
        from google.genai import types as _gt
        client = _genai.Client(api_key=GEMINI_API_KEY)
        today_str = _now_kst().strftime("%Y년 %m월 %d일")
        prompt = "오늘 한국 주식시장 주요 재료 분석..." 
        
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[prompt],
            config=_gt.GenerateContentConfig(tools=[_gt.Tool(google_search=_gt.GoogleSearch())], temperature=0.3),
        )
        # 파싱 로직...
        rows = [] # (기존 파싱 로직 적용)
        _gemini_grounding_cache = {"ts": now, "rows": rows}
        return rows
    except Exception as e:
        _is_quota_err = any(k in str(e) for k in ("429", "quota", "RESOURCE_EXHAUSTED"))
        if _is_quota_err:
            _gemini_grounding_daily_counter["count"] = GEMINI_GROUNDING_DAILY_LIMIT
            _gemini_grounding_cache["ts"] = now + 86400 
        else:
            _gemini_grounding_cache["ts"] = now
        return list(_gemini_grounding_cache.get("rows", []))

# ... (중략) ...

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
        
        # [v170.00] 알람 필터링 이전의 '무결성 섹터 데이터' 조립
        sector_list = get_all_sector_index() or []
        for sec in sector_list[:15]:
            name = sec.get("bstp_name", "")
            if not name: continue
            
            stocks_raw = []
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

        # Captured, Ranking 로직...
        payload = {
            "updated_at":   datetime.now().strftime("%H:%M:%S"),
            "market_open":  market_open,
            "sectors":      sectors_raw if sectors_raw else _WEB_DASHBOARD_PREMARKET_SECTORS,
            "captured":     [], # (기존 포착 로직 적용)
            "alerts":       list(_WEB_DASHBOARD_ALERTS),
            "rank_date":    datetime.now().strftime("%m-%d %H:%M"),
        }
        
        # 마스터 캐시 업데이트
        _MASTER_DASHBOARD_CACHE = {"ts": time.time(), "payload": payload}
        _write_json_atomic(_WEB_DASHBOARD_JSON, payload)
    except Exception as e:
        _swallow_exception(e)

@_flask_app.route("/api/data")
def _flask_api_data():
    """v170.00: Bypass Track - 마스터 캐시 즉시 반환"""
    if _MASTER_DASHBOARD_CACHE.get("payload"):
        return _jsonify(_MASTER_DASHBOARD_CACHE["payload"])
    
    try:
        if os.path.exists(_WEB_DASHBOARD_JSON):
            with open(_WEB_DASHBOARD_JSON, "r", encoding="utf-8") as f:
                return _FlaskResponse(f.read(), mimetype="application/json")
    except Exception: pass
    return _jsonify({"updated_at": "--", "sectors": [], "captured": []})

# ... (이하 기존 코드 동일) ...