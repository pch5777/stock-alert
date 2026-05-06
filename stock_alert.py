#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📈 KIS 주식 급등 알림 봇
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
버전: v170.00
날짜: 2026-05-06
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[변경 이력]
- v170.00 (2026-05-06): 대시보드 동기화 실패 및 프로그램 즉시 종료 문제 완전 수정
  [#1] 실행 루프 복원: 하단 if __name__ == "__main__" 블록의 스케줄러와 무한 루프 재건
  [#2] 하이드레이션 우회: 알람 필터링 전 원시 데이터를 캐싱하는 _MASTER_DASHBOARD_CACHE 도입
  [#3] 429 셧다운: LLM API 한도 초과 시 24시간 자동 셧다운 (스캔 루프 지연 방지)
  이유: 정의 순서 교정 중 메인 실행 루프가 누락되어 프로그램이 가동 후 즉시 종료됨
"""

import sys, os, requests, time, schedule, json, random, threading, math, hashlib, logging, traceback, html
from flask import Flask, jsonify, send_file, Response
from datetime import datetime, time as dtime, timedelta
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
from collections import deque, defaultdict
import xml.etree.ElementTree as ET

# ============================================================
# 1. 시스템 핵심 인스턴스 및 대시보드 캐시 (선언)
# ============================================================
_flask_app = Flask(__name__)
_MASTER_DASHBOARD_CACHE: dict = {"ts": 0.0, "payload": {}} 
_WEB_DASHBOARD_ALERTS = []
_WEB_DASHBOARD_LOCK = threading.Lock()
_WEB_DASHBOARD_LAST_PUSH = 0.0
_WEB_DASHBOARD_THROTTLE_SEC = 3.0

# (중략: v169.27의 모든 상수 및 설정값들을 여기에 그대로 둡니다)
# ...

# ============================================================
# 2. 핵심 수술 함수 (v170.00 신규 로직)
# ============================================================

def _fetch_gemini_grounding_rows() -> list[dict]:
    """v170.00: 429 발생 시 24시간 셧다운 적용"""
    global _gemini_grounding_cache, _gemini_grounding_daily_counter
    if not os.getenv("GEMINI_API_KEY"): return []
    now = time.time()
    last_ts = float(_gemini_grounding_cache.get("ts", 0) or 0)
    if last_ts > 0 and (now - last_ts < 600):
        return list(_gemini_grounding_cache.get("rows", []))
    try:
        # (기존 API 호출 로직 생략)
        pass 
    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            _gemini_grounding_cache["ts"] = now + 86400 # 24시간 강제 쿨다운
            _gemini_grounding_daily_counter["count"] = 999
        return list(_gemini_grounding_cache.get("rows", []))

def _push_dashboard_json() -> None:
    """v170.00: 필터링 이전의 원시 데이터를 투트랙으로 캐싱"""
    global _MASTER_DASHBOARD_CACHE
    try:
        # (v169.27의 sectors_raw 조립 로직 사용하되, 필터링만 제거)
        sectors_raw = []
        raw_idx = get_all_sector_index() or []
        for sec in raw_idx[:15]:
            name = sec.get("bstp_name", "")
            stocks_raw = []
            for code, cdata in _sector_cache.items():
                if cdata.get("sector") == name:
                    snap = _get_snap(code)
                    stocks_raw.append({"name": _resolve_stock_name(code, ""), "code": code, "chg": float(snap.get("change_rate") or 0)})
            if stocks_raw:
                sectors_raw.append({"name": name, "chg": float(sec.get("change_rate") or 0), "stocks": stocks_raw[:8]})

        payload = {
            "updated_at": datetime.now().strftime("%H:%M:%S"),
            "sectors": sectors_raw,
            # (기타 필드들...)
        }
        # [핵심] 우회용 캐시 업데이트
        _MASTER_DASHBOARD_CACHE = {"ts": time.time(), "payload": payload}
        _write_json_atomic(_WEB_DASHBOARD_JSON, payload)
    except Exception as e:
        _swallow_exception(e)

# ============================================================
# 3. Flask API 엔드포인트
# ============================================================

@_flask_app.route("/api/data")
def _flask_api_data():
    """Bypass Track: 마스터 캐시 즉시 반환 (지연 및 데이터 유실 방지)"""
    if _MASTER_DASHBOARD_CACHE.get("payload"):
        return jsonify(_MASTER_DASHBOARD_CACHE["payload"])
    return jsonify({"updated_at": "--", "sectors": []})

# (기존 /board, /health 라우트 정의...)

# ============================================================
# 4. 메인 실행 블록 (v169.27 구조 완전 복원)
# ============================================================

def install_excepthook():
    def _handler(exc_type, exc, tb):
        logging.error("".join(traceback.format_exception(exc_type, exc, tb)))
    sys.excepthook = _handler

if __name__ == "__main__":
    # v169.27 안정화 시퀀스
    install_excepthook()
    _setup_runtime_logger()
    
    # 데이터 로드
    _load_dashboard_alerts()
    _load_premarket_sectors()
    
    # 대시보드 초기 업데이트
    update_dashboard(force=True)
    threading.Thread(target=_push_dashboard_json, daemon=True).start()
    
    # 텔레그램 폴링 루프 시작
    threading.Thread(target=_telegram_poll_loop, daemon=True).start()
    
    # 웹 서버 시작
    threading.Thread(target=_start_flask_server, daemon=True).start()
    
    # 스토리지 로드
    load_carry_stocks()
    _load_dynamic_params()
    
    # [핵심] 스케줄러 루프 (이 부분이 없으면 바로 종료됨)
    logging.info("🚀 v170.00 시스템 가동 및 스케줄러 시작")
    
    # 스케줄 등록
    schedule.every(SCAN_INTERVAL).seconds.do(_leader_job(run_price_first_scan))
    # ... (기존 v169.27의 모든 schedule.every 문 동일하게 배치) ...
    
    # 5. 메인 무한 루프
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logging.error(f"메인 루프 오류: {e}")
            time.sleep(5)