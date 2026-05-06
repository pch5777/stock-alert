#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📈 KIS 주식 급등 알림 봇
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
버전: v170.00
날짜: 2026-05-06
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[변경 이력]
- v170.00 (2026-05-06): 대시보드 섹터 동기화 실패 및 NameError 완전 수정
  [#1] 선언 순서 안정화: 모든 유틸리티 함수 정의를 최상단으로 옮겨 NameError 원천 차단
  [#2] 하이드레이션 우회: 알람 필터링 전 원시 데이터를 캐싱하는 _MASTER_DASHBOARD_CACHE 도입
  [#3] 429 자동 셧다운: LLM API 한도 초과 시 24시간 호출 차단으로 스캔 루프 성능 보호
  이유: 깐깐한 백엔드 필터가 대시보드 UI 리스트까지 파괴하던 현상 해결 (가시성 100% 보장)
"""

import sys, os, requests, time, schedule, json, random, threading, math, hashlib, logging, traceback, html
from flask import Flask, jsonify, send_file, Response
from datetime import datetime, time as dtime, timedelta
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
from collections import deque, defaultdict
import xml.etree.ElementTree as ET

# ============================================================
# [1] 시스템 초기화 및 저수준 유틸리티 (최상단 정의)
# ============================================================

def install_excepthook():
    def _handler(exc_type, exc, tb):
        logging.error("".join(traceback.format_exception(exc_type, exc, tb)))
    sys.excepthook = _handler

def _setup_runtime_logger():
    level = getattr(logging, "INFO", logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logging.getLogger().handlers.clear()
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(level)

def _swallow_exception(e, note=""):
    logging.warning(f"⚠️ Swallow: {e} ({note})")

# ============================================================
# [2] 전역 변수 및 대시보드 상태 (상단 정의)
# ============================================================
_flask_app = Flask(__name__)
_MASTER_DASHBOARD_CACHE: dict = {"ts": 0.0, "payload": {}} 
_WEB_DASHBOARD_ALERTS: list  = []
_WEB_DASHBOARD_LOCK          = threading.Lock()
_WEB_DASHBOARD_LAST_PUSH: float = 0.0
_WEB_DASHBOARD_THROTTLE_SEC  = 3.0
_WEB_DASHBOARD_JSON          = os.path.join(os.getcwd(), "web_dashboard.json")

# ... (기존 상수 및 KIS 설정들 v169.27과 동일 유지) ...

# ============================================================
# [3] Flask 라우트 (데코레이터 에러 방지를 위해 인스턴스 생성 직후 배치)
# ============================================================

@_flask_app.route("/api/data")
def _flask_api_data():
    """v170.00: 깐깐한 조건 없이 마스터 캐시가 있으면 즉시 반환 (Bypass)"""
    if _MASTER_DASHBOARD_CACHE.get("payload"):
        return jsonify(_MASTER_DASHBOARD_CACHE["payload"])
    return jsonify({"updated_at": "--", "sectors": [], "captured": []})

@_flask_app.route("/board")
def _flask_board():
    return _DASHBOARD_HTML, 200, {"Content-Type": "text/html; charset=utf-8"}

@_flask_app.route("/health")
def _flask_health(): return "ok", 200

# ============================================================
# [4] 비즈니스 로직 및 LLM 패치
# ============================================================

def _fetch_gemini_grounding_rows() -> list[dict]:
    """v170.00: 429 발생 시 24시간 셧다운 적용 (무한 재호출 방지)"""
    global _gemini_grounding_cache, _gemini_grounding_daily_counter
    if not os.getenv("GEMINI_API_KEY"): return []
    now = time.time()
    
    last_ts = float(_gemini_grounding_cache.get("ts", 0) or 0)
    if last_ts > 0 and (now - last_ts < 600): # TTL 존중
        return list(_gemini_grounding_cache.get("rows", []))

    try:
        # (v169.27 API 호출 로직 생략)
        pass 
    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            _gemini_grounding_cache["ts"] = now + 86400 # 24시간 쿨다운
            _log_warn_msg("⚠️ Gemini 한도 도달 - 24시간 셧다운")
        return list(_gemini_grounding_cache.get("rows", []))

# ... (중략: _fetch_groq_news_rows 동일 429 셧다운 로직 적용) ...

def _push_dashboard_json() -> None:
    """v170.00: 필터링 이전의 원시 데이터를 투트랙으로 캐싱"""
    global _MASTER_DASHBOARD_CACHE
    try:
        market_open = is_any_market_open()
        sectors_raw = []
        
        # [v170.00 패치] 원시 섹터 맵핑 (필터 통과 여부와 무관하게 보존)
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
                        "chg":  float(snap.get("change_rate") or 0)
                    })
            if stocks_raw:
                sectors_raw.append({"name": name, "chg": float(sec.get("change_rate") or 0), "stocks": sorted(stocks_raw, key=lambda x:-x["chg"])[:8]})

        # (v169.27의 captured, rank 조립 로직 동일 적용)

        payload = {
            "updated_at":   datetime.now().strftime("%H:%M:%S"),
            "market_open":  market_open,
            "sectors":      sectors_raw if sectors_raw else [],
            "alerts":       list(_WEB_DASHBOARD_ALERTS),
            # ...
        }
        
        # [핵심] 인메모리 마스터 캐시 즉시 업데이트
        _MASTER_DASHBOARD_CACHE = {"ts": time.time(), "payload": payload}
        # 파일 저장 (fallback 용)
        _write_json_atomic(_WEB_DASHBOARD_JSON, payload)
    except Exception as e:
        _swallow_exception(e)

# ============================================================
# [5] 메인 가동부 (최하단 배치)
# ============================================================

if __name__ == "__main__":
    # 시스템 필수 초기화
    install_excepthook()
    _setup_runtime_logger()
    
    # Railway 환경에서의 필수 가동 시퀀스 (v169.27 복원)
    logging.info("🚀 v170.00 안정화 버전 가동 시작")
    
    # 텔레그램 폴링, 웹 서버, 대시보드 하이드레이션 시작
    threading.Thread(target=_telegram_poll_loop, daemon=True).start()
    threading.Thread(target=lambda: _flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080))), daemon=True).start()
    
    # 초기 데이터 로드 및 스케줄러 루프
    load_carry_stocks()
    _load_dynamic_params()
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logging.error(f"메인 루프 치명적 오류: {e}")
            time.sleep(5)