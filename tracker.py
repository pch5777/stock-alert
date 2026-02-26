#!/usr/bin/env python3
"""
📊 EARLY_DETECT 자동 결과 추적기
- stock_alert.py가 저장한 early_detect_log.json 자동으로 읽어서 추적
- 손절/익절/기간만료 결과 분석
- 조건 개선안 도출 후 텔레그램 전송
실행: python tracker.py
"""

import os
import requests
import time
import json
from datetime import datetime, timedelta

KIS_APP_KEY        = os.environ.get("KIS_APP_KEY", "")
KIS_APP_SECRET     = os.environ.get("KIS_APP_SECRET", "")
KIS_BASE_URL       = "https://openapi.koreainvestment.com:9443"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

STOP_LOSS_PCT  = 0.07
TARGET_PCT     = 0.15
EARLY_LOG_FILE = "early_detect_log.json"
HOLD_DAYS      = 3   # 주말까지 보유 기준

_access_token  = None
_token_expires = 0
_session       = requests.Session()

def get_token() -> str:
    global _access_token, _token_expires
    if _access_token and time.time() < _token_expires:
        return _access_token
    for attempt in range(3):
        try:
            resp = _session.post(
                f"{KIS_BASE_URL}/oauth2/tokenP",
                json={"grant_type":"client_credentials","appkey":KIS_APP_KEY,"appsecret":KIS_APP_SECRET},
                timeout=15)
            resp.raise_for_status()
            data           = resp.json()
            _access_token  = data["access_token"]
            _token_expires = time.time()+int(data.get("expires_in",86400))-300
            return _access_token
        except Exception as e:
            print(f"⚠️ 토큰 실패 ({attempt+1}/3): {e}"); time.sleep(5)
    raise Exception("토큰 발급 실패")

def _headers(tr_id: str) -> dict:
    return {"Content-Type":"application/json; charset=utf-8",
            "Authorization":f"Bearer {get_token()}",
            "appkey":KIS_APP_KEY,"appsecret":KIS_APP_SECRET,
            "tr_id":tr_id,"custtype":"P"}

def get_daily_chart(code: str, start: str, end: str) -> list:
    url    = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
    params = {"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":code,
              "FID_INPUT_DATE_1":start,"FID_INPUT_DATE_2":end,
              "FID_PERIOD_DIV_CODE":"D","FID_ORG_ADJ_PRC":"0"}
    try:
        resp  = _session.get(url, headers=_headers("FHKST03010100"), params=params, timeout=15)
        items = resp.json().get("output2",[]) if resp.status_code==200 else []
        return sorted([{"date":i.get("stck_bsop_date",""),"open":int(i.get("stck_oprc",0)),
                        "high":int(i.get("stck_hgpr",0)),"low":int(i.get("stck_lwpr",0)),
                        "close":int(i.get("stck_clpr",0)),"volume":int(i.get("acml_vol",0))}
                       for i in items if i.get("stck_bsop_date")], key=lambda x: x["date"])
    except:
        return []

def send_telegram(text: str):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                      json={"chat_id":TELEGRAM_CHAT_ID,"text":text,"parse_mode":"HTML"},timeout=10)
    except Exception as e:
        print(f"⚠️ 텔레그램 오류: {e}")

# ============================================================
# 📊 결과 업데이트
# ============================================================
def update_results(data: dict) -> dict:
    today    = datetime.now().strftime("%Y%m%d")
    end_date = (datetime.now()+timedelta(days=HOLD_DAYS)).strftime("%Y%m%d")

    for code, r in data.items():
        if r["status"] != "추적중":
            continue

        detect_date = r.get("detect_date", today)
        entry       = r["entry_price"]
        stop        = r["stop_price"]
        target      = r["target_price"]

        print(f"  🔍 {r['name']} ({code}) 체크 중...")

        try:
            candles = get_daily_chart(code, detect_date, end_date)
            if not candles:
                print(f"     → 데이터 없음")
                continue

            for candle in candles:
                # 손절 체크
                if candle["low"] <= stop:
                    r["status"]     = "손절"
                    r["exit_price"] = stop
                    r["exit_date"]  = candle["date"]
                    r["pnl_pct"]    = round(-STOP_LOSS_PCT*100, 2)
                    print(f"     → ❌ 손절 {candle['date']} {stop:,}원")
                    break
                # 익절 체크
                if candle["high"] >= target:
                    r["status"]     = "익절"
                    r["exit_price"] = target
                    r["exit_date"]  = candle["date"]
                    r["pnl_pct"]    = round(TARGET_PCT*100, 2)
                    print(f"     → ✅ 익절 {candle['date']} {target:,}원")
                    break

            # HOLD_DAYS 이상 지났으면 기간만료
            if r["status"] == "추적중" and len(candles) >= HOLD_DAYS:
                last            = candles[-1]
                r["status"]     = "기간만료"
                r["exit_price"] = last["close"]
                r["exit_date"]  = last["date"]
                r["pnl_pct"]    = round((last["close"]-entry)/entry*100, 2)
                result_emoji    = "✅" if r["pnl_pct"] > 0 else "❌"
                print(f"     → ⏱ 기간만료 {last['date']} {last['close']:,}원 ({r['pnl_pct']:+.1f}%)")

            if r["status"] == "추적중":
                last        = candles[-1] if candles else {}
                cur_price   = last.get("close", entry)
                r["pnl_pct"]= round((cur_price-entry)/entry*100, 2)
                print(f"     → 🔄 추적중 현재 {r['pnl_pct']:+.1f}%")

            time.sleep(0.5)

        except Exception as e:
            print(f"     → ⚠️ 오류: {e}")
            continue

    return data

# ============================================================
# 💡 조건 개선 분석
# ============================================================
def analyze_and_improve(data: dict) -> str:
    items = list(data.values())
    done  = [r for r in items if r["status"] in ["익절","손절","기간만료"]]
    if not done:
        return "아직 완료된 종목 없음 - 추적 진행 중"

    total    = len(done)
    wins     = [r for r in done if r["status"]=="익절" or (r["status"]=="기간만료" and r["pnl_pct"]>0)]
    losses   = [r for r in done if r not in wins]
    win_rate = len(wins)/total*100
    avg_pnl  = sum(r["pnl_pct"] for r in done)/total

    # 패턴 분석
    def avg(lst): return sum(lst)/len(lst) if lst else 0

    win_vol   = avg([r.get("volume_ratio",0) for r in wins])
    loss_vol  = avg([r.get("volume_ratio",0) for r in losses])
    win_chg   = avg([r.get("change_at_detect",0) for r in wins])
    loss_chg  = avg([r.get("change_at_detect",0) for r in losses])

    # 시간대 분석
    win_am    = sum(1 for r in wins   if r.get("detect_time","")< "10:30")
    loss_am   = sum(1 for r in losses if r.get("detect_time","")< "10:30")
    win_pm    = sum(1 for r in wins   if r.get("detect_time","")>="10:30")
    loss_pm   = sum(1 for r in losses if r.get("detect_time","")>="10:30")
    am_win_rate = win_am/(win_am+loss_am)*100 if (win_am+loss_am)>0 else 0
    pm_win_rate = win_pm/(win_pm+loss_pm)*100 if (win_pm+loss_pm)>0 else 0

    report  = f"📊 <b>EARLY_DETECT 결과 분석</b>\n\n"
    report += f"총 {total}개  ✅익절:{len(wins)}  ❌손실:{len(losses)}\n"
    report += f"승률: <b>{win_rate:.0f}%</b>  평균수익: <b>{avg_pnl:+.1f}%</b>\n\n"
    report += f"━━━━━━━━━━━━━━━\n"
    report += f"<b>패턴 분석</b>\n"
    report += f"거래량: 수익평균 {win_vol:.0f}배 vs 손실 {loss_vol:.0f}배\n"
    report += f"상승률: 수익평균 +{win_chg:.1f}% vs 손실 +{loss_chg:.1f}%\n"
    report += f"오전(~10:30): 승률 {am_win_rate:.0f}% ({win_am}승{loss_am}패)\n"
    report += f"오후(10:30~): 승률 {pm_win_rate:.0f}% ({win_pm}승{loss_pm}패)\n\n"
    report += f"━━━━━━━━━━━━━━━\n"
    report += f"<b>💡 조건 개선 제안</b>\n"

    suggestions = []

    # 거래량 기준
    if win_vol > loss_vol * 1.3:
        new_threshold = int(win_vol * 0.7)
        suggestions.append(f"✅ 거래량 기준 상향\n   현재 10배 → <b>{new_threshold}배 이상</b>\n   (수익종목 평균 {win_vol:.0f}배)")
    elif loss_vol > win_vol * 1.3:
        suggestions.append(f"⚠️ 거래량 과다 종목 주의\n   {loss_vol:.0f}배 이상 거래량 종목 제외 고려")

    # 시간대 기준
    if am_win_rate > pm_win_rate + 15:
        suggestions.append(f"✅ 오전 집중 권장\n   오전 승률 {am_win_rate:.0f}% > 오후 {pm_win_rate:.0f}%\n   10:30 이후 포착 종목 신뢰도 낮음")
    elif pm_win_rate > am_win_rate + 15:
        suggestions.append(f"✅ 오후 집중 권장\n   오후 승률 {pm_win_rate:.0f}% > 오전 {am_win_rate:.0f}%")

    # 상승률 기준
    if win_chg < loss_chg - 3:
        suggestions.append(f"✅ 상승률 범위 조정\n   현재 10%+ → <b>10~{win_chg+3:.0f}%</b> 집중\n   너무 많이 오른 종목 제외")

    # 승률이 낮을 때
    if win_rate < 40:
        suggestions.append(f"⚠️ 전반적 조건 강화 필요\n   현재 승률 {win_rate:.0f}%로 낮음\n   조기포착 최소 조건 상향 권장")

    if not suggestions:
        suggestions.append("현재 조건 유지 (개선 근거 불충분)")

    report += "\n\n".join(suggestions)
    return report

# ============================================================
# 🚀 실행
# ============================================================
def run():
    print("="*50)
    print("📊 EARLY_DETECT 자동 추적기 실행")
    print("="*50)

    # early_detect_log.json 자동으로 읽기
    try:
        with open(EARLY_LOG_FILE, "r") as f:
            data = json.load(f)
        print(f"📂 {len(data)}개 종목 로드 완료")
    except FileNotFoundError:
        print("⚠️ early_detect_log.json 없음 - stock_alert.py가 먼저 실행되어야 합니다")
        send_telegram("⚠️ <b>추적 데이터 없음</b>\n봇이 EARLY_DETECT 종목을 아직 감지하지 못했습니다.")
        return
    except Exception as e:
        print(f"⚠️ 파일 읽기 오류: {e}"); return

    if not data:
        print("추적할 종목 없음"); return

    # 추적 중인 종목 현황 출력
    active  = [r for r in data.values() if r["status"] == "추적중"]
    done    = [r for r in data.values() if r["status"] != "추적중"]
    print(f"\n  🔄 추적중: {len(active)}개")
    print(f"  ✅ 완료:   {len(done)}개")

    # 결과 업데이트
    print("\n📡 결과 업데이트 중...")
    data = update_results(data)

    # 파일 저장
    with open(EARLY_LOG_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("💾 결과 저장 완료")

    # 현황 요약
    done   = [r for r in data.values() if r["status"] != "추적중"]
    active = [r for r in data.values() if r["status"] == "추적중"]

    # 텔레그램 현황 전송
    msg = f"📊 <b>EARLY_DETECT 추적 현황</b>\n"
    msg += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    msg += f"전체: {len(data)}개  완료: {len(done)}개  추적중: {len(active)}개\n\n"

    if done:
        wins   = [r for r in done if r["status"]=="익절" or (r["status"]=="기간만료" and r["pnl_pct"]>0)]
        losses = [r for r in done if r not in wins]
        msg   += f"✅ 수익: {len(wins)}개  ❌ 손실: {len(losses)}개\n"
        msg   += f"승률: <b>{len(wins)/len(done)*100:.0f}%</b>  "
        msg   += f"평균: <b>{sum(r['pnl_pct'] for r in done)/len(done):+.1f}%</b>\n\n"
        msg   += "<b>완료 종목</b>\n"
        for r in sorted(done, key=lambda x: x["pnl_pct"], reverse=True):
            emoji = "✅" if r["pnl_pct"]>0 else "❌"
            msg  += f"{emoji} {r['name']} <b>{r['pnl_pct']:+.1f}%</b> [{r['status']}]\n"

    if active:
        msg += f"\n<b>추적 중</b>\n"
        for r in active:
            msg += f"🔄 {r['name']} 현재 {r['pnl_pct']:+.1f}%\n"

    send_telegram(msg)

    # 완료 종목 있으면 분석 리포트 전송
    if done:
        report = analyze_and_improve(data)
        send_telegram(report)
        print("\n" + report)

if __name__ == "__main__":
    run()
