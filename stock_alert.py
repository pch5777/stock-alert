#!/usr/bin/env python3
"""
📈 KIS 주식 급등 알림 봇 v7
① 조기 포착 강화 (상한가 전 선진입)
② DART 공시 분석 (장 마감 후)
③ 뉴스 테마 연동 분석 (섹터 동반 급등 예측)
④ 감지 종목 장 마감까지 눌림목 체크 + 이월
"""

import os
import re
import requests
import time
import schedule
import json
from datetime import datetime, time as dtime, timedelta
from bs4 import BeautifulSoup

# ============================================================
# ⚙️ 환경변수
# ============================================================
KIS_APP_KEY        = os.environ.get("KIS_APP_KEY", "")
KIS_APP_SECRET     = os.environ.get("KIS_APP_SECRET", "")
KIS_ACCOUNT_NO     = os.environ.get("KIS_ACCOUNT_NO", "")
KIS_BASE_URL       = "https://openapi.koreainvestment.com:9443"
DART_API_KEY       = os.environ.get("DART_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

# ============================================================
# 📊 스캔 조건
# ============================================================
VOLUME_SURGE_RATIO    = 5.0
PRICE_SURGE_MIN       = 5.0
UPPER_LIMIT_THRESHOLD = 25.0
EARLY_PRICE_MIN       = 10.0
EARLY_VOLUME_MIN      = 10.0
EARLY_HOGA_RATIO      = 3.0
EARLY_CONFIRM_COUNT   = 2
SCAN_INTERVAL         = 60
ALERT_COOLDOWN        = 1800
NEWS_SCAN_INTERVAL    = 300    # 뉴스 5분마다 스캔
MARKET_OPEN           = "09:00"
MARKET_CLOSE          = "15:30"
ENTRY_PULLBACK_RATIO  = 0.4
STOP_LOSS_PCT         = 0.07
TARGET_PCT            = 0.15
PULLBACK_CHECK_AFTER  = 30
PULLBACK_MIN          = 25.0
PULLBACK_MAX          = 55.0
MAX_CARRY_DAYS        = 3
CARRY_FILE            = "carry_stocks.json"

# ============================================================
# 🗞️ 테마 섹터 맵
# 키워드 감지 시 관련 종목 코드 매핑
# ============================================================
THEME_MAP = {
    "밸류업": {
        "desc": "밸류업 프로그램",
        "sectors": ["증권", "은행", "보험", "금융"],
        "stocks": [
            ("001510", "SK증권"), ("001290", "상상인증권"), ("003490", "대한항공"),
            ("005940", "NH투자증권"), ("016360", "삼성증권"), ("006800", "미래에셋증권"),
            ("039490", "키움증권"), ("000270", "기아"), ("005380", "현대차"),
        ],
    },
    "자사주소각": {
        "desc": "자사주 소각/배당 확대",
        "sectors": ["전 섹터"],
        "stocks": [],  # 동적으로 같은 섹터 종목 추가
    },
    "금리인하": {
        "desc": "금리 인하 기대감",
        "sectors": ["증권", "부동산", "리츠"],
        "stocks": [
            ("001510", "SK증권"), ("005940", "NH투자증권"), ("016360", "삼성증권"),
        ],
    },
    "AI반도체": {
        "desc": "AI/반도체 테마",
        "sectors": ["반도체", "AI", "HBM"],
        "stocks": [
            ("000660", "SK하이닉스"), ("005930", "삼성전자"), ("042700", "한미반도체"),
            ("403870", "HPSP"), ("357780", "솔브레인"), ("336370", "솔브레인홀딩스"),
        ],
    },
    "2차전지": {
        "desc": "2차전지/배터리 테마",
        "sectors": ["배터리", "양극재", "전해질"],
        "stocks": [
            ("086520", "에코프로"), ("247540", "에코프로비엠"), ("006400", "삼성SDI"),
            ("051910", "LG화학"), ("373220", "LG에너지솔루션"), ("003670", "포스코퓨처엠"),
        ],
    },
    "바이오": {
        "desc": "바이오/제약 테마",
        "sectors": ["바이오", "임상", "FDA", "신약"],
        "stocks": [
            ("207940", "삼성바이오로직스"), ("068270", "셀트리온"), ("196170", "알테오젠"),
            ("009420", "한올바이오파마"), ("084990", "헬릭스미스"),
        ],
    },
    "방산": {
        "desc": "방위산업/방산 테마",
        "sectors": ["방산", "방위", "무기"],
        "stocks": [
            ("012450", "한화에어로스페이스"), ("047810", "한국항공우주"), ("064350", "현대로템"),
            ("000760", "이수화학"), ("042660", "한화오션"),
        ],
    },
    "원전": {
        "desc": "원자력/원전 테마",
        "sectors": ["원전", "원자력", "SMR"],
        "stocks": [
            ("017800", "현대엘리베이터"), ("071970", "STX중공업"), ("298040", "효성중공업"),
            ("012630", "HDC"), ("082920", "비츠로셀"),
        ],
    },
    "수주": {
        "desc": "대규모 수주/계약",
        "sectors": ["조선", "건설", "방산"],
        "stocks": [
            ("042660", "한화오션"), ("009540", "HD한국조선해양"), ("010140", "삼성중공업"),
            ("047050", "포스코인터내셔널"),
        ],
    },
}

# 뉴스 감지 쿨다운 (같은 테마 중복 알림 방지, 4시간)
_news_alert_history = {}
_early_cache        = {}

# ============================================================
# 💾 이월 종목 저장/복원
# ============================================================
def save_carry_stocks():
    try:
        data = {}
        for code, info in _detected_stocks.items():
            data[code] = {
                "name":        info["name"],
                "high_price":  info["high_price"],
                "entry_price": info["entry_price"],
                "stop_loss":   info["stop_loss"],
                "target_price":info["target_price"],
                "detected_at": info["detected_at"].strftime("%Y%m%d%H%M%S"),
                "carry_day":   info.get("carry_day", 0),
            }
        with open(CARRY_FILE, "w") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ 이월 저장 실패: {e}")

def load_carry_stocks():
    try:
        with open(CARRY_FILE, "r") as f:
            data = json.load(f)
        for code, info in data.items():
            carry_day = info.get("carry_day", 0)
            if carry_day >= MAX_CARRY_DAYS:
                continue
            _detected_stocks[code] = {
                "name":        info["name"],
                "high_price":  info["high_price"],
                "entry_price": info["entry_price"],
                "stop_loss":   info["stop_loss"],
                "target_price":info["target_price"],
                "detected_at": datetime.strptime(info["detected_at"], "%Y%m%d%H%M%S"),
                "carry_day":   carry_day,
            }
        if _detected_stocks:
            print(f"📂 이월 종목 {len(_detected_stocks)}개 복원")
            send(f"📂 <b>이월 종목 복원</b>\n" +
                 "\n".join([f"• {v['name']} ({k})" for k, v in _detected_stocks.items()]) +
                 "\n\n눌림목 체크 재개")
    except:
        pass

# ============================================================
# 🔐 KIS API
# ============================================================
_access_token  = None
_token_expires = 0
_session       = requests.Session()
_session.headers.update({"User-Agent": "Mozilla/5.0"})

def get_token(retry: int = 3) -> str:
    global _access_token, _token_expires
    if _access_token and time.time() < _token_expires:
        return _access_token
    _access_token = None
    for attempt in range(retry):
        try:
            resp = _session.post(
                f"{KIS_BASE_URL}/oauth2/tokenP",
                json={"grant_type": "client_credentials",
                      "appkey": KIS_APP_KEY, "appsecret": KIS_APP_SECRET},
                timeout=15
            )
            resp.raise_for_status()
            data           = resp.json()
            _access_token  = data["access_token"]
            _token_expires = time.time() + int(data.get("expires_in", 86400)) - 300
            print(f"✅ KIS 토큰 발급 완료 ({datetime.now().strftime('%H:%M:%S')})")
            return _access_token
        except Exception as e:
            print(f"⚠️ 토큰 발급 실패 ({attempt+1}/{retry}): {e}")
            time.sleep(5 * (attempt + 1))
    raise Exception("❌ KIS 토큰 발급 최종 실패")

def _headers(tr_id: str) -> dict:
    return {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {get_token()}",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET,
        "tr_id": tr_id,
        "custtype": "P",
    }

def _safe_get(url: str, tr_id: str, params: dict) -> dict:
    try:
        resp = _session.get(url, headers=_headers(tr_id), params=params, timeout=15)
        if resp.status_code == 403:
            global _access_token
            _access_token = None
            resp = _session.get(url, headers=_headers(tr_id), params=params, timeout=15)
        return resp.json() if resp.status_code == 200 else {}
    except Exception as e:
        print(f"⚠️ API 호출 오류 ({tr_id}): {e}")
        return {}

def get_stock_price(code: str) -> dict:
    url    = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
    data   = _safe_get(url, "FHKST01010100", params)
    o      = data.get("output", {})
    price  = int(o.get("stck_prpr", 0))
    if not price:
        return {}
    return {
        "code":        code,
        "name":        o.get("hts_kor_isnm", ""),
        "price":       price,
        "change_rate": float(o.get("prdy_ctrt", 0)),
        "volume_ratio":float(o.get("vol_tnrt", 0)),
        "high":        int(o.get("stck_hgpr", 0)),
        "ask_qty":     int(o.get("askp_rsqn1", 0)),
        "bid_qty":     int(o.get("bidp_rsqn1", 0)),
    }

def get_upper_limit_stocks() -> list:
    url    = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/chgrate-pcls-100"
    params = {
        "FID_COND_MRKT_DIV_CODE": "J", "FID_COND_SCR_DIV_CODE": "20170",
        "FID_INPUT_ISCD": "0000", "FID_RANK_SORT_CLS_CODE": "0",
        "FID_INPUT_CNT_1": "30", "FID_PRC_CLS_CODE": "0",
        "FID_INPUT_PRICE_1": "1000", "FID_INPUT_PRICE_2": "",
        "FID_VOL_CNT": "100000", "FID_TRGT_CLS_CODE": "0",
        "FID_TRGT_EXLS_CLS_CODE": "0", "FID_DIV_CLS_CODE": "0",
        "FID_RSFL_RATE1": "5", "FID_RSFL_RATE2": "",
    }
    data  = _safe_get(url, "FHPST01700000", params)
    items = data.get("output", [])
    return [{"code": i.get("mksc_shrn_iscd",""), "name": i.get("hts_kor_isnm",""),
             "price": int(i.get("stck_prpr",0)), "change_rate": float(i.get("prdy_ctrt",0)),
             "volume_ratio": float(i.get("vol_inrt",0) or 0)} for i in items if i.get("mksc_shrn_iscd")]

def get_volume_surge_stocks() -> list:
    url    = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/volume-rank"
    params = {
        "FID_COND_MRKT_DIV_CODE": "J", "FID_COND_SCR_DIV_CODE": "20171",
        "FID_INPUT_ISCD": "0000", "FID_DIV_CLS_CODE": "0",
        "FID_BLNG_CLS_CODE": "0", "FID_TRGT_CLS_CODE": "111111111",
        "FID_TRGT_EXLS_CLS_CODE": "000000", "FID_INPUT_PRICE_1": "1000",
        "FID_INPUT_PRICE_2": "", "FID_VOL_CNT": "30", "FID_INPUT_DATE_1": "",
    }
    data  = _safe_get(url, "FHPST01710000", params)
    items = data.get("output", [])
    return [{"code": i.get("mksc_shrn_iscd",""), "name": i.get("hts_kor_isnm",""),
             "price": int(i.get("stck_prpr",0)), "change_rate": float(i.get("prdy_ctrt",0)),
             "volume_ratio": float(i.get("vol_inrt",0) or 0)} for i in items if i.get("mksc_shrn_iscd")]

def get_investor_trend(code: str) -> dict:
    url    = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-investor"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
    data   = _safe_get(url, "FHKST01010900", params)
    output = data.get("output", [])
    if not output:
        return {}
    return {"foreign_net": int(output[0].get("frgn_ntby_qty", 0)),
            "institution_net": int(output[0].get("orgn_ntby_qty", 0))}

# ============================================================
# 🗞️ 뉴스 테마 연동 분석
# ============================================================
def fetch_naver_news() -> list:
    """네이버 금융 뉴스 크롤링"""
    try:
        url  = "https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258"
        resp = requests.get(url, timeout=10,
                            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        soup = BeautifulSoup(resp.text, "html.parser")
        news = []
        for item in soup.select(".realtimeNewsList .newsList li"):
            title_tag = item.select_one("a")
            if title_tag:
                news.append(title_tag.get_text(strip=True))
        return news[:30]
    except Exception as e:
        print(f"⚠️ 뉴스 크롤링 오류: {e}")
        return []

def fetch_naver_news_search(keyword: str) -> list:
    """네이버 뉴스 키워드 검색"""
    try:
        url  = f"https://search.naver.com/search.naver?where=news&query={requests.utils.quote(keyword)}&sort=1"
        resp = requests.get(url, timeout=10,
                            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        soup  = BeautifulSoup(resp.text, "html.parser")
        titles = [t.get_text(strip=True) for t in soup.select(".news_tit")]
        return titles[:10]
    except:
        return []

def analyze_news_theme() -> list:
    """
    뉴스 키워드 감지 → 관련 섹터 종목 미리 알림
    5분마다 실행
    """
    signals = []
    now     = datetime.now()

    # 실시간 뉴스 수집
    headlines = fetch_naver_news()
    if not headlines:
        return []

    print(f"  📰 뉴스 {len(headlines)}건 분석 중...")

    for theme_key, theme_info in THEME_MAP.items():
        # 쿨다운 체크 (4시간)
        last_alert = _news_alert_history.get(theme_key, 0)
        if time.time() - last_alert < 14400:
            continue

        # 헤드라인에서 테마 키워드 감지
        matched_headlines = []
        for headline in headlines:
            if theme_key in headline:
                matched_headlines.append(headline)
            # 추가 키워드도 체크
            for sector in theme_info["sectors"]:
                if sector in headline and theme_key in headline:
                    matched_headlines.append(headline)

        if not matched_headlines:
            continue

        # 관련 종목 현재가 체크
        related_stocks = []
        for code, name in theme_info["stocks"]:
            try:
                cur = get_stock_price(code)
                if cur and cur.get("price", 0) > 0:
                    related_stocks.append({
                        "code":        code,
                        "name":        name,
                        "price":       cur["price"],
                        "change_rate": cur["change_rate"],
                    })
                time.sleep(0.2)
            except:
                continue

        if not related_stocks:
            continue

        # 이미 급등 중인 종목 제외, 아직 안 오른 종목 우선
        not_yet_surged = [s for s in related_stocks if s["change_rate"] < 5.0]
        already_surged = [s for s in related_stocks if s["change_rate"] >= 5.0]

        _news_alert_history[theme_key] = time.time()

        signals.append({
            "theme_key":      theme_key,
            "theme_desc":     theme_info["desc"],
            "matched":        matched_headlines[0][:50],
            "not_yet":        not_yet_surged[:5],
            "already_surged": already_surged[:3],
        })

        print(f"  🗞️ 테마 감지: {theme_key} → 관련주 {len(related_stocks)}개")

    return signals

def send_news_theme_alert(signal: dict):
    """테마 연동 알림 발송"""
    now = datetime.now().strftime("%H:%M:%S")

    not_yet_text = ""
    for s in signal["not_yet"]:
        not_yet_text += f"  • <b>{s['name']}</b> ({s['code']}) 현재 {s['change_rate']:+.1f}%\n"

    surged_text = ""
    for s in signal["already_surged"]:
        surged_text += f"  • {s['name']} 이미 {s['change_rate']:+.1f}% 상승 중\n"

    msg = (
        f"🗞️ <b>[테마 연동 알림]</b>\n"
        f"🕐 {now}\n\n"
        f"📌 <b>{signal['theme_desc']}</b> 테마 뉴스 감지!\n"
        f"💬 \"{signal['matched']}...\"\n\n"
        f"━━━━━━━━━━━━━━━\n"
    )

    if signal["not_yet"]:
        msg += f"🎯 <b>아직 안 오른 관련주 (선진입 기회)</b>\n{not_yet_text}\n"

    if signal["already_surged"]:
        msg += f"🔥 <b>이미 상승 중인 관련주</b>\n{surged_text}\n"

    msg += (
        f"━━━━━━━━━━━━━━━\n"
        f"⚡️ 관련주 중 거래량 급증 종목 집중 모니터링\n"
        f"⚠️ 투자 판단은 본인 책임입니다"
    )

    send(msg)

# ============================================================
# 📋 DART 공시 분석
# ============================================================
DART_KEYWORDS = {
    "매우강함": ["수주", "계약체결", "공급계약", "수출계약", "임상", "FDA", "허가", "신약", "인수", "합병", "흑자전환"],
    "강함":     ["특허", "기술이전", "MOU", "업무협약", "증설", "공장", "설비투자", "자사주", "배당"],
    "보통":     ["신규사업", "진출", "개발완료", "수상", "선정"],
}

def analyze_dart_disclosures():
    if not DART_API_KEY:
        return
    print("\n📋 DART 공시 분석 시작...")
    today = datetime.now().strftime("%Y%m%d")
    try:
        items = []
        for ptype in ["A", "B"]:
            resp  = requests.get(
                "https://opendart.fss.or.kr/api/list.json",
                params={"crtfc_key": DART_API_KEY, "bgn_de": today, "end_de": today,
                        "pblntf_ty": ptype, "page_count": 100},
                timeout=15
            )
            items += resp.json().get("list", [])

        scored = []
        for item in items:
            title   = item.get("report_nm", "")
            company = item.get("corp_name", "")
            code    = item.get("stock_code", "")
            if not code:
                continue
            score, matched, strength = 0, [], ""
            for level, keywords in DART_KEYWORDS.items():
                for kw in keywords:
                    if kw in title:
                        score += {"매우강함": 30, "강함": 20, "보통": 10}[level]
                        matched.append(kw)
                        strength = level
            if score >= 30 and matched:
                scored.append({"code": code, "company": company, "title": title,
                                "score": score, "matched": matched, "strength": strength})

        scored.sort(key=lambda x: x["score"], reverse=True)
        top = scored[:5]

        if not top:
            send("📋 <b>오늘 주목할 공시 없음</b>"); return

        msg  = f"📋 <b>내일 주목 종목 - DART 공시 분석</b>\n"
        msg += f"🗓 {today[:4]}.{today[4:6]}.{today[6:]} 장 마감 후\n"
        msg += "━━━━━━━━━━━━━━━\n\n"
        for i, item in enumerate(top, 1):
            emoji = {"매우강함": "🔴", "강함": "🟡", "보통": "🟢"}.get(item["strength"], "⚪")
            msg  += (f"{i}. {emoji} <b>{item['company']}</b> ({item['code']})\n"
                     f"   📌 {item['title']}\n"
                     f"   🔑 {', '.join(item['matched'])}\n"
                     f"   ⭐ 급등 가능성: {item['score']}점\n\n")
        msg += "━━━━━━━━━━━━━━━\n⚠️ 내일 장 시작 전 확인 후 진입 판단"
        send(msg)
        print(f"  → 주목 공시 {len(top)}개 완료")
    except Exception as e:
        print(f"⚠️ DART 분석 오류: {e}")

# ============================================================
# 🔍 조기 포착 강화
# ============================================================
def check_early_detection() -> list:
    signals    = []
    candidates = get_volume_surge_stocks()

    for stock in candidates:
        code        = stock.get("code", "")
        change_rate = stock.get("change_rate", 0)
        vol_ratio   = stock.get("volume_ratio", 0)
        price       = stock.get("price", 0)

        if not code or price < 500:
            continue
        if change_rate >= UPPER_LIMIT_THRESHOLD:
            continue
        if change_rate < EARLY_PRICE_MIN or vol_ratio < EARLY_VOLUME_MIN:
            continue

        try:
            detail  = get_stock_price(code)
            bid_qty = detail.get("bid_qty", 0)
            ask_qty = detail.get("ask_qty", 0)
            if ask_qty > 0 and bid_qty / ask_qty < EARLY_HOGA_RATIO:
                continue
        except:
            continue

        now   = datetime.now()
        cache = _early_cache.get(code)

        if cache is None:
            _early_cache[code] = {"count": 1, "last_price": price, "last_time": now}
            continue

        elapsed = (now - cache["last_time"]).seconds
        if 50 <= elapsed <= 180:
            if price >= cache["last_price"]:
                cache["count"]      += 1
                cache["last_price"]  = price
                cache["last_time"]   = now
            else:
                _early_cache[code] = {"count": 1, "last_price": price, "last_time": now}
                continue
        else:
            _early_cache[code] = {"count": 1, "last_price": price, "last_time": now}
            continue

        if cache["count"] < EARLY_CONFIRM_COUNT:
            continue

        del _early_cache[code]

        open_est   = price / (1 + change_rate / 100)
        entry      = int((price - (price - open_est) * ENTRY_PULLBACK_RATIO) / 10) * 10
        stop       = int(entry * (1 - STOP_LOSS_PCT) / 10) * 10
        target     = int(entry * (1 + TARGET_PCT) / 10) * 10
        hoga_text  = f"{bid_qty/ask_qty:.1f}배" if ask_qty > 0 else "압도적"

        signals.append({
            "code": code, "name": stock.get("name", code), "price": price,
            "change_rate": change_rate, "volume_ratio": vol_ratio,
            "signal_type": "EARLY_DETECT", "score": 85,
            "entry_price": entry, "stop_loss": stop, "target_price": target,
            "reasons": [
                f"🔍 조기 포착! (상한가 전 선진입 기회)",
                f"📈 현재 +{change_rate:.1f}% 상승 중",
                f"💥 거래량 {vol_ratio:.0f}배 폭발",
                f"📊 매수잔량 매도잔량 대비 {hoga_text}",
                f"✅ 2분 연속 상승 확인",
            ],
            "detected_at": now,
        })

    return signals

# ============================================================
# 🕐 시간 유틸
# ============================================================
def is_market_open() -> bool:
    now = datetime.now().time()
    o   = dtime(*map(int, MARKET_OPEN.split(":")))
    c   = dtime(*map(int, MARKET_CLOSE.split(":")))
    return o <= now <= c

def minutes_since(dt: datetime) -> int:
    return int((datetime.now() - dt).total_seconds() // 60)

# ============================================================
# 📊 메인 스캐너
# ============================================================
_alert_history    = {}
_detected_stocks  = {}
_pullback_history = {}

def analyze(stock: dict) -> dict:
    code        = stock.get("code", "")
    change_rate = stock.get("change_rate", 0)
    vol_ratio   = stock.get("volume_ratio", 0)
    price       = stock.get("price", 0)
    if not code or price < 500:
        return {}

    score, reasons, signal_type = 0, [], None

    if change_rate >= 29.0:
        score += 40; reasons.append("🚨 상한가 도달!"); signal_type = "UPPER_LIMIT"
    elif change_rate >= UPPER_LIMIT_THRESHOLD:
        score += 25; reasons.append(f"🔥 상한가 근접 (+{change_rate:.1f}%)"); signal_type = "NEAR_UPPER"
    elif change_rate >= PRICE_SURGE_MIN:
        score += 15; reasons.append(f"📈 급등 +{change_rate:.1f}%"); signal_type = "SURGE"
    else:
        return {}

    if vol_ratio >= VOLUME_SURGE_RATIO * 2:
        score += 30; reasons.append(f"💥 거래량 {vol_ratio:.0f}배 폭발!")
    elif vol_ratio >= VOLUME_SURGE_RATIO:
        score += 20; reasons.append(f"📊 거래량 {vol_ratio:.0f}배 급증")

    if score >= 25:
        try:
            inv   = get_investor_trend(code)
            f_net = inv.get("foreign_net", 0)
            i_net = inv.get("institution_net", 0)
            if f_net > 0 and i_net > 0:
                score += 25; signal_type = "STRONG_BUY"; reasons.append("✅ 외국인+기관 동시 순매수")
            elif f_net > 0:
                score += 10; reasons.append("🟡 외국인 순매수")
            elif i_net > 0:
                score += 10; reasons.append("🟡 기관 순매수")
        except:
            pass

    if score < 60:
        return {}

    open_est = price / (1 + change_rate / 100)
    entry    = int((price - (price - open_est) * ENTRY_PULLBACK_RATIO) / 10) * 10
    stop     = int(entry * (1 - STOP_LOSS_PCT) / 10) * 10
    target   = int(entry * (1 + TARGET_PCT) / 10) * 10

    return {"code": code, "name": stock.get("name", code), "price": price,
            "change_rate": change_rate, "volume_ratio": vol_ratio,
            "signal_type": signal_type, "score": score,
            "entry_price": entry, "stop_loss": stop, "target_price": target,
            "reasons": reasons, "detected_at": datetime.now()}

def check_pullback_signals() -> list:
    signals = []
    for code, info in list(_detected_stocks.items()):
        detected_at = info.get("detected_at")
        if not detected_at or minutes_since(detected_at) < PULLBACK_CHECK_AFTER:
            continue
        if time.time() - _pullback_history.get(code, 0) < 1800:
            continue
        try:
            cur   = get_stock_price(code)
            high  = info.get("high_price", 0)
            price = cur.get("price", 0)
            if not price or not high:
                continue
            if price > high:
                _detected_stocks[code]["high_price"] = price
                continue
            pullback = (high - price) / high * 100
            elapsed  = minutes_since(detected_at)
            carry    = info.get("carry_day", 0)
            if PULLBACK_MIN <= pullback <= PULLBACK_MAX:
                entry = price
                stop  = int(entry * (1 - STOP_LOSS_PCT) / 10) * 10
                tgt   = int(entry * (1 + TARGET_PCT) / 10) * 10
                carry_text = f" (이월 {carry}일차)" if carry > 0 else ""
                signals.append({
                    "code": code, "name": cur.get("name", code), "price": price,
                    "change_rate": cur.get("change_rate", 0), "volume_ratio": 0,
                    "signal_type": "ENTRY_POINT", "score": 95,
                    "entry_price": entry, "stop_loss": stop, "target_price": tgt,
                    "reasons": [
                        f"🎯 눌림목 진입 시점{carry_text}",
                        f"📌 고점 {high:,}원 → 현재 {price:,}원 (-{pullback:.1f}%)",
                        f"⏱ 급등 감지 후 {elapsed}분 경과",
                    ],
                    "detected_at": detected_at,
                })
                _pullback_history[code] = time.time()
        except:
            continue
    return signals

def on_market_close():
    carry_list = []
    for code, info in list(_detected_stocks.items()):
        carry_day = info.get("carry_day", 0)
        if carry_day >= MAX_CARRY_DAYS:
            del _detected_stocks[code]; continue
        _detected_stocks[code]["carry_day"]   = carry_day + 1
        _detected_stocks[code]["detected_at"] = datetime.now()
        carry_list.append(f"• {info['name']} ({code}) - {carry_day+1}일차")
    save_carry_stocks()

    msg = (f"🔔 <b>장 마감</b>  {datetime.now().strftime('%Y-%m-%d')}\n"
           f"오늘 감지 종목: <b>{len(_detected_stocks)}개</b>\n")
    if carry_list:
        msg += f"\n📂 <b>이월 종목 ({len(carry_list)}개)</b>\n" + "\n".join(carry_list)
        msg += "\n\n내일 장 시작부터 눌림목 재체크"
    send(msg)
    analyze_dart_disclosures()

def run_news_scan():
    """뉴스 테마 스캔 (5분마다)"""
    if not is_market_open():
        return
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 뉴스 테마 스캔...", flush=True)
    try:
        for signal in analyze_news_theme():
            send_news_theme_alert(signal)
    except Exception as e:
        print(f"⚠️ 뉴스 스캔 오류: {e}")

def run_scan():
    if not is_market_open():
        return
    now = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{now}] 스캔 중...", flush=True)
    try:
        alerts, seen = [], set()

        for stock in get_upper_limit_stocks():
            if stock["code"] in seen: continue
            r = analyze(stock)
            if r and time.time() - _alert_history.get(r["code"], 0) > ALERT_COOLDOWN:
                alerts.append(r); seen.add(r["code"])

        for stock in get_volume_surge_stocks():
            if stock["code"] in seen: continue
            r = analyze(stock)
            if r and time.time() - _alert_history.get(r["code"], 0) > ALERT_COOLDOWN:
                alerts.append(r); seen.add(r["code"])

        for s in check_early_detection():
            if s["code"] not in seen and time.time() - _alert_history.get(s["code"], 0) > ALERT_COOLDOWN:
                alerts.append(s); seen.add(s["code"])

        for s in check_pullback_signals():
            if s["code"] not in seen:
                alerts.append(s); seen.add(s["code"])

        alerts.sort(key=lambda x: x["score"], reverse=True)

        if not alerts:
            print("  → 조건 충족 종목 없음"); return

        print(f"  → {len(alerts)}개 감지!")
        for s in alerts:
            print(f"  ✓ {s['name']} +{s['change_rate']:.1f}% [{s['signal_type']}] {s['score']}점")
            send_alert(s)
            _alert_history[s["code"]] = time.time()
            if s["signal_type"] != "ENTRY_POINT":
                if s["code"] not in _detected_stocks:
                    _detected_stocks[s["code"]] = {
                        "name":        s["name"],
                        "high_price":  s["price"],
                        "entry_price": s["entry_price"],
                        "stop_loss":   s["stop_loss"],
                        "target_price":s["target_price"],
                        "detected_at": s["detected_at"],
                        "carry_day":   0,
                    }
                elif s["price"] > _detected_stocks[s["code"]]["high_price"]:
                    _detected_stocks[s["code"]]["high_price"] = s["price"]
            time.sleep(1)

    except Exception as e:
        print(f"⚠️ 스캔 오류 (다음 스캔에서 재시도): {e}")

# ============================================================
# 📨 텔레그램
# ============================================================
def send(text: str):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10
        )
    except Exception as e:
        print(f"⚠️ 텔레그램 오류: {e}")

def send_alert(s: dict):
    emoji = {"UPPER_LIMIT":"🚨","NEAR_UPPER":"🔥","STRONG_BUY":"💎",
             "SURGE":"📈","ENTRY_POINT":"🎯","EARLY_DETECT":"🔍"}.get(s["signal_type"], "📊")
    title = {"UPPER_LIMIT":"상한가 감지","NEAR_UPPER":"상한가 근접",
             "STRONG_BUY":"강력 매수 신호","SURGE":"급등 감지",
             "ENTRY_POINT":"★ 눌림목 진입 시점 ★",
             "EARLY_DETECT":"★ 조기 포착 - 상한가 전 선진입 ★"}.get(s["signal_type"], "급등 감지")
    stars   = "★" * min(int(s["score"] / 20), 5)
    reasons = "\n".join(s["reasons"])
    now     = datetime.now().strftime("%H:%M:%S")

    if s["signal_type"] == "ENTRY_POINT":
        entry_msg = (f"⚡️ <b>지금 눌림목 진입 구간!</b>\n"
                     f"🎯 진입가: <b>{s['entry_price']:,}원</b>\n   (분할 매수 추천)")
    elif s["signal_type"] == "EARLY_DETECT":
        entry_msg = (f"⚡️ <b>지금 바로 진입 고려!</b>\n"
                     f"📈 상한가 도달 전 선진입 기회\n"
                     f"🎯 목표 진입가: <b>{s['entry_price']:,}원</b>")
    else:
        detected_at   = s.get("detected_at", datetime.now())
        elapsed       = minutes_since(detected_at)
        pullback_time = (detected_at + timedelta(minutes=PULLBACK_CHECK_AFTER)).strftime("%H:%M")
        if elapsed < PULLBACK_CHECK_AFTER:
            wait = PULLBACK_CHECK_AFTER - elapsed
            entry_msg = (f"⏰ <b>눌림목 대기 중</b> ({wait}분 후 체크 시작)\n"
                         f"🕐 {pullback_time} 부터 장 마감까지 눌림목 체크\n"
                         f"🎯 목표 진입가: <b>{s['entry_price']:,}원</b>")
        else:
            entry_msg = (f"📡 <b>눌림목 실시간 체크 중</b>\n"
                         f"🎯 목표 진입가: <b>{s['entry_price']:,}원</b>\n"
                         f"   (고점 대비 25~55% 되돌림 시 즉시 알림)")

    send(
        f"{emoji} <b>[{title}]</b>\n"
        f"<b>{s['name']}</b>  {s['code']}\n"
        f"🕐 {now}\n\n"
        f"💰 현재가: <b>{s['price']:,}원</b>  (<b>+{s['change_rate']:.1f}%</b>)\n"
        f"⭐ 신호강도: {stars} ({s['score']}점)\n\n"
        f"━━━━━━━━━━━━━━━\n{reasons}\n━━━━━━━━━━━━━━━\n\n"
        f"{entry_msg}\n\n"
        f"🛡 손절가: <b>{s['stop_loss']:,}원</b>  (-7%)\n"
        f"🏆 목표가: <b>{s['target_price']:,}원</b>  (+15%)\n\n"
        f"⚠️ 투자 판단은 본인 책임입니다"
    )

# ============================================================
# 🚀 실행
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("📈 KIS 주식 급등 알림 봇 v7 시작")
    print("=" * 50)

    load_carry_stocks()

    send("🤖 <b>주식 급등 알림 봇 ON (v7)</b>\n\n"
         "✅ 한국투자증권 API 연결\n"
         "📡 실시간 스캔 (1분 주기)\n\n"
         "<b>전체 기능</b>\n"
         "🔍 조기 포착: 상한가 전 선진입\n"
         "🗞️ 뉴스 테마 연동: 5분마다 섹터 분석\n"
         "   (밸류업/AI반도체/2차전지/바이오/방산 등)\n"
         "📋 DART 공시: 매일 15:35 분석\n"
         "🎯 눌림목: 장 마감까지 실시간 체크\n"
         f"📂 미발생 시 최대 {MAX_CARRY_DAYS}일 이월")

    schedule.every(SCAN_INTERVAL).seconds.do(run_scan)
    schedule.every(NEWS_SCAN_INTERVAL).seconds.do(run_news_scan)
    schedule.every().day.at(MARKET_OPEN).do(
        lambda: send(f"🌅 <b>장 시작!</b>  {datetime.now().strftime('%Y-%m-%d')}\n"
                     f"📂 이월 종목: {len(_detected_stocks)}개\n📡 스캔 중..."))
    schedule.every().day.at(MARKET_CLOSE).do(on_market_close)

    run_scan()
    run_news_scan()

    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ 메인 루프 오류 (계속 실행): {e}")
            time.sleep(5)
