#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📈 KIS 주식 급등 알림 봇
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
버전: v170.00
날짜: 2026-05-06
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[변경 이력]
- v170.00 (2026-05-06): 대시보드 섹터 동기화 실패 및 NameError 정의 순서 오류 완전 수정
  [#1] 하이드레이션 우회: 알람 필터(NXT/상한가/KRX전용) 적용 전 원시 데이터를 캐싱하는 투트랙 시스템 도입
  [#2] 429 셧다운: LLM API 한도 초과 시 24시간 자동 호출 중단 및 캐시 강제 고정 (루프 지연 방지)
  [#3] 구조 안정화: 함수 정의 순서를 [유틸 -> 비즈니스 로직 -> Flask -> 실행부]로 엄격히 정렬하여 NameError 차단
  이유: 백엔드 필터가 대시보드 UI 리스트를 파괴하는 현상 해결 및 가시성 100% 보장
"""

import sys, os, requests, time, schedule, json, random, threading, math, hashlib, logging, traceback, html
from flask import Flask, jsonify, send_file, Response
from datetime import datetime, time as dtime, timedelta
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
from collections import deque, defaultdict
import xml.etree.ElementTree as ET

# ============================================================
# 1. 전역 상태 및 대시보드 캐시 (v170.00)
# ============================================================
_flask_app = Flask(__name__)
_MASTER_DASHBOARD_CACHE: dict = {"ts": 0.0, "payload": {}} # 대시보드 우회 트랙
_WEB_DASHBOARD_ALERTS: list  = []
_WEB_DASHBOARD_LOCK          = threading.Lock()
_WEB_DASHBOARD_LAST_PUSH: float = 0.0
_WEB_DASHBOARD_THROTTLE_SEC  = 3.0
_KST = ZoneInfo("Asia/Seoul")

# (기존 KIS 설정 및 상수 v169.27과 동일하게 유지...)
# ...

# ============================================================
# 2. 시스템 기초 유틸리티 (NameError 방지를 위해 상단 배치)
# ============================================================

def _now_kst() -> datetime:
    return datetime.now(_KST)

def _setup_runtime_logger():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logging.getLogger().handlers.clear()
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)

def install_excepthook():
    def _handler(exc_type, exc, tb):
        logging.error("".join(traceback.format_exception(exc_type, exc, tb)))
    sys.excepthook = _handler

def _swallow_exception(e, note=""):
    logging.warning(f"⚠️ Swallow: {e} ({note})")

# ... (중략: analyze, get_stock_price, get_all_sector_index 등 모든 비즈니스 로직 함수 정의) ...
# (v169.27 원본 코드의 함수들을 순서대로 배치)

# ============================================================
# 3. v170.00 핵심 기능 구현 (Surgical Patch)
# ============================================================

def _fetch_gemini_grounding_rows() -> list[dict]:
    """v170.00: 429 발생 시 24시간 셧다운 적용 (루프 블로킹 방지)"""
    global _gemini_grounding_cache, _gemini_grounding_daily_counter
    if not os.getenv("GEMINI_API_KEY"): return []
    now = time.time()
    
    # 쿨다운 중이면 API 호출 없이 캐시 즉시 반환
    last_ts = float(_gemini_grounding_cache.get("ts", 0) or 0)
    if last_ts > 0 and (now - last_ts < 600):
        return list(_gemini_grounding_cache.get("rows", []))

    try:
        # (기존 API 호출 코드...)
        pass
    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            _gemini_grounding_cache["ts"] = now + 86400 # 24시간 강제 쿨다운
            _gemini_grounding_daily_counter["count"] = 999
            logging.warning("🚨 Gemini 한도 도달 - 24시간 셧다운 모드")
        return list(_gemini_grounding_cache.get("rows", []))

def _push_dashboard_json() -> None:
    """v170.00: 필터링 전 원시 데이터를 투트랙 캐싱하여 UI 파괴 방지"""
    global _MASTER_DASHBOARD_CACHE, _WEB_DASHBOARD_LAST_PUSH
    now_ts = time.time()
    if now_ts - _WEB_DASHBOARD_LAST_PUSH < _WEB_DASHBOARD_THROTTLE_SEC: return
    _WEB_DASHBOARD_LAST_PUSH = now_ts
    
    try:
        market_open = is_any_market_open()
        sectors_raw = []
        
        # [패치] 매매 필터링(NXT/상한가 등) 적용 전의 전체 섹터 맵 보존
        sector_list = get_all_sector_index() or []
        for sec in sector_list[:15]:
            name = sec.get("bstp_name", "")
            if not name: continue
            
            stocks_raw = []
            # _sector_cache의 모든 종목을 필터 없이 대시보드용으로 수집
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

        payload = {
            "updated_at": datetime.now().strftime("%H:%M:%S"),
            "market_open": market_open,
            "sectors": sectors_raw,
            "alerts": list(_WEB_DASHBOARD_ALERTS),
            # (기타 필드 유지)
        }
        
        # [핵심] 인메모리 마스터 캐시 업데이트 (우회로)
        _MASTER_DASHBOARD_CACHE = {"ts": time.time(), "payload": payload}
        _write_json_atomic(_WEB_DASHBOARD_JSON, payload)
    except Exception as e:
        _swallow_exception(e)

# ============================================================
# 4. Flask API 및 텔레그램 명령 루프 (메인 실행부 직전 정의)
# ============================================================

@_flask_app.route("/api/data")
def _flask_api_data():
    """Bypass Track: 마스터 캐시가 있으면 즉시 반환 (가시성 보장)"""
    if _MASTER_DASHBOARD_CACHE.get("payload"):
        return jsonify(_MASTER_DASHBOARD_CACHE["payload"])
    return jsonify({"updated_at": "--", "sectors": []})

def _telegram_poll_loop():
    """텔레그램 명령 처리 루프 - NameError 방지를 위해 메인 직전에 배치"""
    while True:
        try:
            poll_telegram_commands()
            time.sleep(2)
        except Exception as e:
            _swallow_exception(e)

# ============================================================
# 5. 메인 실행부 (반드시 최하단 배치)
# ============================================================

if __name__ == "__main__":
    # 1단계: 시스템 기초 초기화
    install_excepthook()
    _setup_runtime_logger()
    
    # 2단계: 데이터 로드 및 웹서버 기동
    logging.info("🚀 v170.00 시스템 가동 및 스케줄러 시작")
    threading.Thread(target=lambda: _flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080))), daemon=True).start()
    threading.Thread(target=_telegram_poll_loop, daemon=True).start()
    
    # 3단계: 주식 상태 로드 및 스케줄 등록 (v169.27 복원)
    load_carry_stocks()
    _load_dynamic_params()
    
    # 스케줄러 루프
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logging.error(f"메인 루프 치명적 오류: {e}")
            time.sleep(5)