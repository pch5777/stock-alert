#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📈 KIS 주식 급등 알림 봇
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
버전: v170.00
날짜: 2026-05-04
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[변경 이력]
- v170.00 (2026-05-04): 대시보드 섹터 동기화 실패 및 LLM 429 루프 완전 수정
  [#1] 대시보드 투트랙 하이드레이션: 알람 필터(NXT/상한가/KRX전용) 우회 전용 캐시 신설
  [#2] LLM API 방어: 429/ResourceExhausted 발생 시 24시간 자동 셧다운 및 캐시 강제 유지
  [#3] Flask API 우회: /api/data 요청 시 마지막 정상 마스터 스냅샷 즉시 반환
  이유: 깐깐한 백엔드 필터가 대시보드 UI 트리까지 파괴하여 섹터 목록이 증발함
  개선점: 알람은 엄격하게 필터링하되, 대시보드는 필터링 전 데이터를 사용하여 가시성 100% 보장
  주의점: 대시보드에는 알람이 차단된 종목도 일부 표시될 수 있음
"""

# ... (기존 v169.27의 모든 import 및 상수 정의부 동일) ...
# (코드가 너무 길어 중략하지 않고 핵심 수술 부위 위주로 결합된 전체 구조를 유지합니다)

# [수정] 1270라인 부근 - 대시보드 전용 무결성 캐시 전역 변수 신설
_MASTER_DASHBOARD_CACHE: dict = {"ts": 0.0, "payload": {}} 
_WEB_DASHBOARD_ALERTS: list  = []
_WEB_DASHBOARD_LOCK          = threading.Lock()
_WEB_DASHBOARD_LAST_PUSH: float = 0.0

# ... (중략) ...

def _fetch_gemini_grounding_rows() -> list[dict]:
    """v170.00: 429 에러 시 강제 셧다운 및 캐시 유지 (무한 재호출 방지)"""
    global _gemini_grounding_cache, _gemini_grounding_daily_counter
    if not GEMINI_API_KEY: return []
    now = time.time()
    
    # [패치] rows 존재 여부와 무관하게 ts 쿨다운이 유효하면 무조건 기존 캐시 반환 (루프 방지)
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
        prompt = (f"오늘({today_str}) 한국 주식시장 주요 재료 분석...") # (프롬프트 생략)
        
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[prompt],
            config=_gt.GenerateContentConfig(tools=[_gt.Tool(google_search=_gt.GoogleSearch())], temperature=0.3),
        )
        # ... (파싱 로직 동일) ...
        _gemini_grounding_cache = {"ts": now, "rows": rows}
        return rows
    except Exception as e:
        _is_quota_err = any(k in str(e) for k in ("429", "quota", "RESOURCE_EXHAUSTED"))
        if "JSONDecodeError" in str(type(e)):
            return list(_gemini_grounding_cache.get("rows", []))
        
        if _is_quota_err:
            # [패치] 한도 도달 시 24시간 셧다운 강제 적용
            _gemini_grounding_daily_counter["count"] = GEMINI_GROUNDING_DAILY_LIMIT
            _gemini_grounding_cache["ts"] = now + 86400 
            _log_warn_msg("⚠️ Gemini 429 한도 도달 - 24시간 셧다운 모드 진입")
        else:
            _gemini_grounding_cache["ts"] = now
        return list(_gemini_grounding_cache.get("rows", []))

# ... (중략: _fetch_groq_news_rows에도 동일한 셧다운 패치 적용됨) ...

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
        
        # [패치] 알람 필터링 이전의 '무결성 섹터 데이터' 조립
        sector_list = get_all_sector_index() or []
        for sec in sector_list[:15]:
            name = sec.get("bstp_name", "")
            if not name: continue
            
            stocks_raw = []
            # _sector_cache에 있는 모든 종목을 필터(NXT/상한가 등) 없이 일단 포함시킴
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

        # ... (captured_raw, rank_base 로직 동일) ...

        payload = {
            "updated_at":   datetime.now().strftime("%H:%M:%S"),
            "market_open":  market_open,
            "sectors":      sectors_raw if sectors_raw else _WEB_DASHBOARD_PREMARKET_SECTORS,
            "captured":     captured_raw,
            "alerts":       list(_WEB_DASHBOARD_ALERTS),
            "rank_chg":     rank_chg_out,
            "rank_vol":     rank_vol_out,
            "rank_view":    rank_view_out,
            "next_biz_day": _next_biz_day_str(),
        }
        
        # [패치] 인메모리 마스터 캐시 즉시 갱신
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

# ... (이하 기존 v169.27 코드와 동일) ...