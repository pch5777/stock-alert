#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📈 KIS 주식 급등 알림 봇
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
버전: v160.15
날짜: 2026-04-02
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[변경 이력]
- v160.15 (2026-04-03): run_scan 결측 재복구 큐 + 코드수정 요청 연동 + JSON 응답 안전화 — `run_scan` 후보가 이름/가격/신호/점수 결측으로 바로 버려지지 않도록 원인 코드를 남기는 재복구 큐를 추가하고, 다음 사이클에서 다시 복구를 시도한 뒤 끝까지 실패한 종목만 코드수정 요청 알림으로 넘기도록 정리했다. `run_scan alert 결측 스킵`은 즉시 폐기 대신 `missing_name/missing_price/missing_signal_type/missing_score/missing_sector` 사유를 쌓아 재시도하며, 공용 종목명/업종 fallback도 이 경로에서 함께 재사용한다. 또한 `safe_json_response()`는 문자열 직접 파싱으로 바꾸고, 주요 direct `resp.json()` 호출도 공용 helper로 통일해 `JSONDecodeError` 로그를 줄인다.
- v160.14 (2026-04-03): 종목명 공용 메타 fallback + 공용 업종 fallback으로 기타 섹터 대량탈락 완화 — `public_stock_meta.json` 캐시를 추가해 KRX 공개 종목 기본정보(종목명/업종)를 주기적으로 내려받아 코드→종목명/업종 fallback의 공용 소스로 사용하도록 정리했다. `_resolve_stock_name()`은 기존 KIS/NXT/runtime/cache 경로에 공용 메타 fallback을 더해 `459510`, `092790` 같은 코드형 노출을 줄이고, `get_theme_sector_stocks()`/`_hydrate_alert_sector_theme()`는 KIS `bstp_name`이 비거나 generic일 때 공용 업종과 동일업종 peer를 사용해 `기타` 섹터 잔류를 줄인다. 이로써 KIS 업종 404·빈 응답 구간에도 섹터 gate가 공용 업종 fallback을 먼저 시도하고, 이름/업종이 끝까지 안 채워진 경우만 마지막에 코드수정 알림 대상으로 남기도록 보강했다.
- v160.13 (2026-04-02): 종목명 강제 복구 + 예상 체결가 선계산/원인추적 + 일반 포착 알람 폭탄 억제 — 사용자 메인 알림 전에 종목명을 다중 캐시/KIS/NXT/public fallback으로 강제 복구하고, 끝까지 이름을 못 찾으면 외부 발송 대신 코드수정 요청 알림을 남기도록 정리했다. 또한 일반 포착은 예상 체결가(대표/계획/체결기반)가 비면 현재 호가·현재가 기반으로 즉시 보정하고, 그래도 계산이 안 되면 원인을 기록한 뒤 자동보정 실패 코드수정 알림으로 넘긴다. 마지막으로 동일 종목 일반 포착은 의미 있는 강화가 없으면 재알림 쿨다운으로 외부 폭탄을 막고, 외부알림 지연/내부감시 유지 로그도 별도 쿨다운을 둬 내부감시 로그와 사용자 체감 알림이 섞여 쏟아지지 않게 보강했다.
- v160.12 (2026-04-02): 비정상 상위 잠금 자동 복구 + 잠금 로그 숫자 노출 최소화 — `runtime_version_lock.json`에 `lock_kind=authoritative` 메타를 기록하고, 이 메타 없이 남은 구형 정수형 상위 잠금은 비정상 잠금으로 보고 자동 복구하도록 정리했다. 이로써 오류본에서 남은 특정 잠금 버전 숫자 노출과 잘못된 상위 잠금 차단을 줄인다. 문서/스모크도 최근 오류본 표기를 일반화해 다음 정상 버전 체계(`v160.x`)와 혼선이 생기지 않게 맞췄다.
- v160.11 (2026-04-02): v160.10 안정화 유지 + 눌림목 3종 재적용 + token 재발급 쿨다운/섹터 재보정/run_scan 결측 정리 — 직전 정상본 v160.10 위에 오류본에서 유효했던 눌림목 3종 포착 보강(갭상승 후 시가 회복, 박스권 상단 돌파·하단 지지, higher low + 거래대금 재유입)을 다시 얹었다. 동시에 KIS tokenP 403 `EGW00133`가 뜨면 1분 내 재발급 재시도를 중단하고 쿨다운을 기록해 같은 분 연속 발급을 막는다. run_scan은 섹터 gate 직전에 종목의 업종/테마를 한 번 더 재보정해 `기타` 쏠림을 줄이고, 시세·신호 결측 payload는 재복구 후에도 불완전하면 일반 포착에서 제거해 `+0.0% [] 0점 [C]` 로그가 반복되지 않게 했다. 또한 눌림목 결과 dict는 provisional grade를 먼저 채워 `눌림목 오류 (...): 'grade'`를 막는다.
- v160.10 (2026-04-02): timezone 잔여 naive/aware 정리 + 업종 fallback을 섹터명에 직접 반영 + run_scan 결측 payload 자동 복구 — `_signal_age_minutes_for_retry()`/`_sector_resend_relevance_ok()`/`confirm_bottom_and_signal()`의 문자열 시각 비교를 KST aware helper 기반으로 통일해 잔여 `offset-naive/aware` 오류를 더 줄였다. 또한 `get_theme_sector_stocks()`가 KIS 업종 fallback의 `bstp_name`을 그대로 `theme_name`으로 승격하도록 바꿔, `chgrate-pcls-100` 404나 테마맵 부재 시에도 반도체·건설 같은 업종명이 `기타업종`으로 뭉개져 섹터 제한에 무더기 탈락하던 문제를 줄였다. 마지막으로 run_scan 결측 payload는 live quote 병합과 `analyze()` 재평가를 한 번 더 시도해 `change_rate 0 / 빈 signal_type / 0점 C급`으로 흘러가던 포착 후보를 자동 복구한다.
- v160.9 (2026-04-02): NXT/KRX 익일 오픈 평가 시각 분리 — `PRECLOSE_GAP_ENTRY`의 익일 오픈 체크를 시장별로 분리해 NXT는 08:05, KRX는 09:05에 각각 평가하도록 수정했다. `update_preclose_gap_open_outcomes(stage=...)`가 signal별 stage를 읽어 해당 시장만 기록하고, 고우선 정리 메모도 `08:05/09:05`를 시장별로 다르게 표기한다. 또한 startup catch-up도 NXT 08:05 / KRX 09:05 기준으로 다시 확인해, NXT 종가베팅 후보를 KRX와 같은 시각에 늦게 평가하던 문제를 막았다.
- v160.8 (2026-04-02): NXT 19:20도 종가베팅 final confirm 동일 적용 — v160.7에서 KRX 15:18에만 붙였던 종가베팅 final confirm을 NXT 19:20에도 같은 기준으로 확장했다. 이제 NXT 선진입 후보도 `phase="final"`로 처리되어 전고/신고가 근접, 윗꼬리 부담, 거래대금 강도, higher low 조정, 외국인·기관 수급, 1분봉 20선 지지를 같은 축으로 다시 확인하고, 최종 점수 문턱과 안내 문구도 final 기준을 사용한다.
- v160.7 (2026-04-02): 종가베팅 final confirm + 전고/윗꼬리/눌림/수급 필터 + 익일 09:05 청산우선도 — 기존 `PRECLOSE_GAP_ENTRY` 구조는 유지한 채 KRX 14:45 1차 선별 뒤 15:18 최종 확정 스캔을 추가했다. 종가선진입 점수화에는 전고/신고가 근접, 윗꼬리 부담, 거래대금 강도, higher low 조정, 1분봉 20선 지지, 외국인·기관 수급 우호를 반영해 종가베팅형 후보를 더 보수적으로 재평가한다. 또한 `update_preclose_gap_open_outcomes()`는 익일 09:05 기록 시 갭상승·시초 약세 기준의 청산 우선도와 메모를 함께 남기고, 우선 정리 필요 종목은 묶음 안내로 정리한다.
- v160.6 (2026-04-02): 정규장 재료 prewatch 반응 완화 + 오전 NXT 저품질 후보 축소 — 하향추세 차단은 유지한 채 정규장에서는 강한 재료 seed의 prewatch 반응 기준을 `quality_score/headline_count` 기반으로 완화해 `뉴스 있지만 주가 반응 없음`으로 오래 묻히는 종목이 더 빨리 본스캔에 합류하도록 조정했다. 동시에 오전 NXT는 `_get_nxt_premarket_quality_gate()`를 추가해 0점/C급/진입가 미확정으로 반복 쌓이던 저품질 후보를 사전 제거하고, 장전 NXT 본스캔도 같은 gate를 통과한 후보만 돌도록 정리했다. 이로써 현대로템 같은 주봉·일봉 하향 추세 차단은 그대로 유지하면서도 정규장 진짜 재료 반응형과 오전 NXT 실행형 후보의 품질을 더 보수적으로 맞췄다.
- v160.5 (2026-04-02): 네이버 코스닥 상승/거래량 순위 URL 404 복구 — `_fetch_naver_rank()`를 코스피/코스닥 분리 경로(`*_kosdaq.naver`) 대신 공통 `sise_rise.naver`/`sise_quant.naver`에 `sosok=0/1` 파라미터를 붙여 요청하도록 바꿨다. 코스닥 direct path 404를 제거하고, 응답 인코딩도 `apparent_encoding`/`euc-kr` 기준으로 보정해 외부 fallback 품질을 유지했다. 또한 smoke test에 구형 `*_kosdaq.naver` URL 금지와 `sosok` 파라미터 기반 요청 검증을 추가했다.
- v160.4 (2026-04-02): v160.2 기능 보존 상태에서 startup 비동기 catch-up + datetime aware 정리 + 삭제방지 검증 강화 — `v160.2`의 stale runtime lock 복구/NXT·오픈 버스트/KPI cohort reset 보강을 그대로 유지한 채, `__main__` 시작부의 동기 `refresh_dynamic_candidates()` 호출과 즉시 스캔 실행을 제거하고 `_schedule_startup_scan_catchup()` 기반 비동기 catch-up으로 전환했다. 또한 carry/priority hint/minutes helper의 datetime 계산을 KST aware 기준으로 통일해 `can't subtract offset-naive and offset-aware datetimes` 잔여 오류를 줄였고, smoke test에는 직전 정상본 핵심 변경사항·변경이력 보존·삭제 금지 규칙 검증을 추가했다.
- v160.2 (2026-04-02): stale 상위 버전 락 복구 + 장전/NXT·오픈 버스트 + cohort reset 보강 — `runtime_version_lock.json`에 lease/heartbeat 개념을 추가해 죽은 상위 버전 락은 자동 복구하고, 살아 있는 상위 버전만 구버전 런타임을 차단하도록 정리했다. 또한 08:00~09:00 NXT 장전 버스트와 09:00~09:03 KRX 오픈 버스트를 추가해 `refresh_dynamic_candidates(force_rank=True)`·`run_material_first_scan()`·`run_scan()`를 더 촘촘히 돌리도록 보강했다. `compute_signal_kpi()` 경로는 현재 cohort 필터를 강제하고, `/reset_stats 확인`은 signal_log 백업 뒤 통계 시작 시각뿐 아니라 동적 파라미터 baseline·emergency state·연속 손익 카운터까지 함께 초기화한다. 마지막으로 동적 후보군 로그를 `KRX_seed/KRX_rank/NXT_seed/NXT_rank/material_prewatch` 기준으로 분리해 운영 판단이 바로 되도록 정리했다.
- v160.1 (2026-04-02): v151 기준 누락 기능 재적용 — `현재가<=진입가` 전 신호 공통 1차 진입가 도달 helper와 `/list`·`/watch` 도달 분류 보정, `+ 1차 진입가 도달` 표시를 복구했다. 또한 `EARLY_DETECT`/일반 포착 즉시 도달 연계, `trailing_active` 5일 시간초과 제외, 자동 추적 결과 `최대수익(MFE)` 표시, `send_market_leading_sector_update`용 `_parse_compact_datetime(value, time_value=None)` 및 KST aware 계산을 보강했다. 마지막으로 강한 뉴스테마/이슈 종목 direct 승격과 NXT 거래량 급감 guard 완화를 다시 연결했다.
- v160 (2026-04-02): 구조 버전별 성과 cohort 분리 + /reset_stats 명령 추가 — 큰 구조 변경은 정수 버전(v160, v161 …)으로 올리고 해당 버전이 곧 새로운 성과 cohort가 되도록 버전 체계를 정리했다. 같은 구조 안의 버그/경미 수정은 소수점 버전(v160.1, v160.2 …)을 쓰도록 helpers를 추가했고, signal_log 신규 레코드에 `bot_version`·`stats_cohort`를 저장한다. `/stats`는 이제 현재 cohort 기준으로만 승률을 계산하며, `/reset_stats 확인`은 signal_log를 백업한 뒤 현재 cohort의 통계 시작 시각만 초기화해 과거 기록은 보존하고 현재 구조 성과만 새로 측정한다.
- v159 (2026-04-02): NXT 거래량 급감 종료 완화 — `_get_entry_watch_volume_guard_profile()`를 추가해 장전/장후 NXT는 정규장과 다른 유예시간·재확인 횟수·거래량폭락 컷을 사용하도록 분리했다. `theme_chain`/`direct_news` 계열은 NXT에서 추가 유예를 주어 `거래량 급감` 즉시 종료를 완화했다.
- v158 (2026-04-02): 유실된 v152~v156 핵심 변경 복구 — 테마체인 direct 승격/실행형 진입가 보완, `현재가<=진입가` 즉시 1차도달 helper, `trailing_active` 5일 시간초과 제외, 자동 추적 결과 `최대수익(MFE)` 표시와 종료 경로 공통 `_apply_result_labels()` 호출을 다시 합쳐 넣었다.
- v157 (2026-04-02): `send_market_leading_sector_update` timezone hotfix — `_parse_compact_datetime(value, time_value=None)`와 `_has_recent_actionable_tracking_state()`를 KST aware 기준으로 정리해 `can't subtract offset-naive and offset-aware datetimes` 오류를 제거했다.
- v156 (2026-04-02): 강한 뉴스테마/이슈 종목 direct 승격 + compact datetime 파싱 보강 — 매우강함/강함 뉴스테마와 이슈 선감지 상위 반응 종목을 `_build_theme_chain_direct_candidate()` 기반 direct 실행형 후보로 승격하고, `entry_price/stop_loss/target_price`를 현재가 기준으로 보완했다. 동시에 `_parse_compact_datetime(value, time_value)` 경로를 확장해 `send_market_leading_sector_update`의 인자 불일치를 해결했다.
- v155 (2026-04-02): 테마 알림만 오고 종목 알림이 안 뜨던 마지막 게이트 완화 — `send_news_theme_alert()`와 `_dispatch_issue_prewatch_reacted()`에 테마체인 direct 승격을 연결하고, `theme_chain_force_hit`/`force_external_capture_alert` 후보는 `no_ask_liquidity` soft allow와 섹터 게이트에서 추가 여유를 받도록 정리했다.
- v154 (2026-04-02): 강한 뉴스테마/이슈 종목 승격 + 기타업종/no_ask 완화 — `_apply_theme_chain_capture_adjustment()`와 실행형 진입가 보완을 연결해 매우강함/강함 테마 종목이 near-A여도 종목 포착으로 더 잘 이어지게 보강했다. 동시에 `theme_chain_priority`가 붙은 종목은 `기타업종` 섹터 제한과 `no_ask_liquidity` soft gate에서 완화 혜택을 받게 조정했다.
- v153 (2026-04-02): 뉴스테마/이슈 선감지 near-A 승격 강화 + 추적 결과 MFE 표시 — 강한 뉴스테마/이슈 선감지 종목은 `_apply_theme_chain_capture_adjustment()`를 통해 점수·등급·실행형 진입가를 보강하고, 추적 결과 메시지에는 `최대수익(MFE)`를 함께 표시하도록 정리했다. 종료 경로 전반에 `_apply_result_labels()`를 연결해 학습 라벨을 일관되게 남기도록 보강했다.
- v152 (2026-04-02): `EARLY_DETECT` 즉시 1차 진입가 도달 + `trailing_active` 5일 강제종료 제외 — `현재가<=진입가`인 `EARLY_DETECT`는 포착 직후 바로 `1차 진입가 도달`로 이어지게 하고, 제목에 해당 상태를 반영했다. 목표가 도달 후 `trailing_active` 상태인 종목은 5일 `시간초과` 강제종료에서 제외하고, 결과 메시지와 학습 라벨에 `최대수익(MFE)`를 남기도록 정리했다.
- v151 (2026-04-01): 24시간 시나리오 수집 + 장후/장전 액션보드 연결 — 미국장·미국 이슈·환율·금리·유가·지정학·뉴스/옵션형 유튜브를 공통 시나리오 객체로 묶는 `collect_market_scenarios_24h()`와 `run_market_scenario_collection_cycle()`를 추가했다. 각 재료는 이벤트명·방향·원인·한국 상방/하방 섹터·한국 종목 후보까지 내려와 `premarket_action_board`와 `overnight_watchlist`를 동시에 갱신하고, 재료-first headline 입력에도 같은 시나리오 행을 주입한다. 또한 15:45/20:10 장후 알림은 하방 차단 요약에 더해 상·하방 핵심 시나리오와 한국 후보를 함께 보내고, 07:30/08:50 장전 알림은 기존 단순 워치리스트 대신 액션형 시나리오 보드 중심으로 재구성했으며, 본스캔에도 상방 시나리오 후보를 직접 우선 편입한다.
- v150 (2026-03-31): 상방/하방 재료 시나리오 강화 + 하방 재료 전구간 차단/알림 — 재료 엔진이 직접뉴스·테마동조·섹터확산·market flow·material-first 선감지가 겹칠수록 추가 가점을 더 크게 주도록 `재료 시나리오 결속` 보너스를 도입했다. 동시에 감사보고서 제출기한 연장신고/지연·감사의견·관리/상장폐지/거래정지·횡령/배임·회생류 하방 재료를 DART/뉴스/옵션형 유튜브 최근성 감시에서 시나리오로 묶어 후보 부트스트랩과 최종 진입 필터 양쪽에서 즉시 차단하고, 이미 걸린 entry/reentry/execution/preclose 감시도 `하방재료차단`으로 정리하며 즉시 알림과 장마감 묶음 요약을 함께 남기도록 확장했다.
- v149 (2026-03-31): run_scan `change_rate` 결측/requests GET reset hotfix — run_scan 후보/신호 중 일부가 `change_rate` 없이 흘러들어와 일반 포착 발송 단계에서 KeyError가 나던 문제를 바로잡았다. `run_scan` 정리 helper가 `change_rate`·`volume_ratio`·`score`·`price` 기본값을 강제하고, `_append_scan_alert()`도 동일 기본값을 채운 뒤 alert pipeline에 태우도록 보강해 결측 payload가 와도 스캔 전체가 중단되지 않는다. 또한 공통 `requests.get` 래퍼가 `ConnectionResetError` 계열 연결 재설정을 감지하면 전역 ERROR 누적 전에 1회 재시도하고, 재시도 실패 시 throttled warning으로만 남기도록 보강했다.
- v148 (2026-03-31): KRX 선진입 후보 catch-up NameError hotfix — `_collect_next_open_gap_candidate_codes()` 내부에서 gap 전용 helper 이름과 carry/signal_log 수집 경로가 어긋나던 문제를 바로잡아, `_push_watch_code` 미정의로 KRX 선진입 후보 catch-up이 중단되던 오류를 제거했다. 같은 함수의 pool 수집이 끝까지 진행되도록 정리해 장후반 선진입 후보 점검이 다시 정상 동작한다.
- v147 (2026-03-31): material prewatch 품질·중복·우선순위 보강 — material prewatch seed를 headline/반응 품질 점수로 거르고, 종목 단위 cooldown을 추가해 material-first와 price-first 사이의 중복 알림을 더 줄였다. 또한 active issue prewatch 후보는 breadth·seed 품질을 함께 확인한 뒤 본 스캔에 합류시키고, `material_first_priority_hit`를 sector gate 정렬에 반영해 실제 재료형 상위주가 같은 섹터 내에서 덜 밀리도록 조정했다.
- v146 (2026-03-31): 재료-first 독립 감시 파이프라인 추가 + material prewatch 후보를 본 스캔에 조기 합류 — 기존 `run_news_scan()`의 장중 전용 흐름을 `run_material_first_scan()`으로 확장해, 장중에는 뉴스/이슈 테마를 즉시 분석·발송하고 장마감 뒤·장전에는 관련 테마를 prewatch seed로 등록해 다음 실시간 구간까지 유지하도록 바꿨다. 또한 active issue prewatch 후보를 `run_scan()` 본류 초반에 별도 스캔해 가격-first 후보와 마지막 단계에서 합류시키고, 관련 스케줄도 price-first / material-first 두 파이프라인으로 분리했다.
- v145 (2026-03-31): 포착 후 탈락 종료 안내 + 텔레그램 포착 모니터 메뉴 추가 — 진입 전 `근거약화_신호강도약함`·`근거약화_거래량폭락`으로 감시에서 탈락한 종목은 사용자에게 `감시 종료 — 재포착 전 신규 진입 보류` 안내를 즉시 발송하도록 보강했다. 또한 `/watch` 명령과 메뉴 버튼을 추가해 `_entry_watch`에 남아 있는 현재 포착 모니터링 종목만 따로 조회할 수 있게 했고, intraday NXT confirm 3회는 세션 프로파일 표 값이 아니라 `EARLY_NXT_CONFIRM_COUNT=3` override가 최종 적용된다는 표현을 문서에도 유지했다.
- v144 (2026-03-31): run_scan code 결측 내성 강화 + intraday NXT confirm 문구 명확화 — run_scan 본류와 scan helper들이 `code` 없는 후보/신호를 만나도 즉시 중단하지 않고 건너뛰도록 정리했으며, `analyze()` 결과에 `code`가 빠진 경우 `seen_code`로 복구 후 alert pipeline에 태우도록 보강했다. 또한 malformed alert 정리 helper를 추가해 섹터/포트폴리오 필터 진입 전 `code` 결측을 제거하고, intraday NXT confirm 3회는 세션 프로파일 값이 아니라 `EARLY_NXT_CONFIRM_COUNT=3` override로 강제된다는 점을 changelog/문서에 명확히 남겼다.
- v143 (2026-03-31): EARLY/NXT 지속성·섹터 breadth 실확인 강화 — 상위주 공통 생존 조건과 오전 급락 포착 종목의 공통 붕괴 조건을 함께 반영해, NXT/조기포착에서 후속 거래량·호가 지속성과 실제 섹터 breadth를 더 강하게 확인하도록 조정했다. NXT 장전은 live hoga gate를 필수로 보고, intraday NXT는 confirm 3회와 persistence gate를 적용하며, `early_guard_external_delay_reason`이 NXT 점수 예외보다 우선한다. 또한 fake breakout은 돌파 유지 실패까지 포함해 진입 차단을 보강한다.
- v142 (2026-03-31): 하향 추세 조기포착 차단 강화 + 추세전환 예외 제한 허용 — 다중 타임프레임 하락 추세 판정을 더 보수적으로 강화하고, 일반적인 하향/비상승 구조의 EARLY_DETECT·SURGE류 포착을 더 일찍 차단하도록 조정했다. 대신 직접뉴스·강한 테마 동조·ORB/전고 돌파·quiet absorption·연속 재상승 같은 추세전환 토큰이 충분할 때만 제한적으로 예외 허용해 반전 초입 후보만 남긴다.
- v141 (2026-03-31): 장중 포착 확대 + 약화 기반 청산/가짜 돌파 가드 — session/focus scan limit를 18/30으로 높이고 strict 최소점수를 62로 낮췄으며, KRX EARLY_DETECT 외부허용을 74점 A + 진입가 확정 + 체결/호가 확인으로 완화했다. 동시에 tracking weakness 점수로 분할익절/트레일링 정리를 앞당기고, 거래량 기준 미달 + 윗꼬리 부담 돌파는 진입 단계에서 fake breakout으로 차단한다.
- v139 (2026-03-30): KIS 유량 절약형 quiet scan + 거래량 rank 30 우회 — quiet scan 후보 풀과 deep-fetch 대상을 분리하고 KIS 호가/체결/투자자 snapshot에 짧은 TTL 캐시·사이클 budget·rotate selection을 추가해 REST 호출량을 줄였으며, KRX 거래량 rank는 KIS 30건 응답 이후 rank/universe snapshot으로 보강해 실질 80 후보 폭을 유지하도록 조정.
- v138 (2026-03-30): quiet absorption 초기 매집 감지 추가 — KIS 호가/체결/투자자 + 기존 execution speed를 함께 써 뉴스 없는 조용한 선매집 seed를 market flow state로 등록하고, 같은 사이클의 analyze/익영업일 선진입 scoring에서 `quiet_absorption` 보너스를 리더 본주와 후속주 모두 활용하도록 확장.
- v137 (2026-03-30): 시장 자금 이동 시나리오 전역 엔진 + 종가선진입 실전형 전환 — 뉴스/리더 seed를 테마별 market flow state로 번역해 analyze/뉴스/야간워치/익영업일 선진입 scoring이 공통으로 참조하도록 연결하고, `PRECLOSE_GAP_ENTRY` 진입가를 눌림 대기형이 아닌 알림 시점 즉시 체결 가능한 현재가/매도1호가 기준으로 재설계.
- v136 (2026-03-30): 리더 조기포착 폭 확대 — KRX 거래량 rank 조회 폭을 30→80으로 넓히고 `get_volume_surge_stocks()`를 `_get_krx_volume_rank_count()` helper로 전환, 전역 `PRICE_SURGE_MIN`과 full-session `surge_min_change` 컷을 4%대 초반으로 정렬해 1번타자 seed가 sector leader follow에 더 빨리 등록되도록 조정.
- v135 (2026-03-30): 섹터 대장 후속 강제감시 추가 — 상한가/강한 급등 대장을 감지하면 동일 테마·동업종 peer를 3일간 영속 watch로 등록해 장중 스캔에 강제 편입하고, 후속 후보가 near-A일 때 A권에 더 잘 올라오도록 점수/정렬 보정을 연결.
- v134 (2026-03-30): KIS 토큰 캐시/403 진단 hotfix — tokenP 24시간 토큰을 프로세스 재시작 후에도 재사용하도록 영속 캐시를 추가하고, 403 발생 시 캐시 무효화·응답 본문 스니펫·실전/모의 및 재발급 힌트를 함께 남겨 동일일 재발급/권한 문제 추적을 쉽게 정리.
- v133 (2026-03-30): 일반 포착 1차도달 헤더/워치독 후보미스 hotfix — 일반 포착 제목의 `+ 1차 진입가 도달`을 명시적 도달 상태에서만 붙도록 바로잡고, NXT-only 구간 워치독이 KRX 상승랭킹을 근거로 `candidate_miss` 코드수정 요청을 오진하던 경로를 시장 기준 정렬로 차단.
- v132 (2026-03-30): A게이트 재설계 — B외부알림 신설 없이 near-A 상위 후보만 A권으로 제한 흡수하도록 일반 신호 A완화 기준을 확장하고, STRONG_BUY/장중 capture 계열의 직접재료·테마동조·수급 결합 신호를 실행형 A에 재편입.
- v131 (2026-03-30): intraday watchdog hotfix — 최초 외부알림 전 epoch 기준 침묵 분 표시를 부팅 기준으로 바로잡고, A전용 외부알림 정책을 코드오류처럼 오진하던 워치독/코드수정 요청 문구를 정책 기준에 맞게 정렬.
- v130 (2026-03-30): analyze hotfix — 누락된 `_apply_analyze_theme_context()`를 복구해 run_scan NameError를 차단하고, analyze 경로의 섹터 모멘텀·테마 동조·adaptive feedback·miss-theme breadth/NXT 장후 리더 보정을 다시 연결.
- v129 (2026-03-30): v128 정상본 기준 통합 hotfix — 일반 포착/재안내 제목의 1차 진입가 도달 상태 반영, 오전 NXT-only 구간 조기포착 본류 및 stage shadow 기록 추가, 전략 긴급 경고 stage 기반 dedupe, html import/overnight now NameError 수정.
- v128 (2026-03-30): fallback 안정화 hotfix — 미국시장/공매도/지정학/텔레그램 timeout 경로의 비JSON·빈응답·타임아웃을 throttled warning + 기본값 fallback으로 정리해 로그 노이즈와 과도한 예외 카운트를 축소.
- v127 (2026-03-29): XML RSS 파싱 hotfix — Element.find() 결과를 or 체인 truthiness로 평가하던 description/summary/content 선택 로직을 None 기준 순차 탐색으로 교체해 DeprecationWarning과 향후 동작 왜곡을 차단.
- v126 (2026-03-28): 시작 크래시 hotfix — load_carry_stocks()의 stale entry watch 정리 호출과 _purge_stale_entry_watch_hits() 시그니처를 동기화해 Railway 재시작 루프를 차단.
- v125 (2026-03-28): 최종 마감 배치 — raw print 대량 logger 치환 + state path helper 통합 + COMMON_THRESHOLD_3P0 상수화 + 스모크/회귀 검증 보강.
- v124 (2026-03-28): 남은 상위 함수/운영 로그 final cleanup — early-detect/preclose-gap/signal-log/analyze-result/RSS/Korea-ETF/carry/trailing 구조 정리 + sector/holiday/news theme raw print logger 치환.
- v123 (2026-03-28): 최종 cleanup batch — sector monitor / premarket risk / issue prewatch / universe update / weekly report / market regime / intraday watchdog 구조 정리 및 일부 raw print logger 치환.
- v122 (2026-03-28): 마지막 구조 마감 배치 — mid_pullback/entry-watch/multi-TF 구조 정리 + logger 보강.
  [#1] `_build_mid_pullback_base_context()`, `_score_mid_pullback_base_context()`, `_apply_mid_pullback_execution_grade()`, `_finalize_mid_pullback_analysis()`를 load/surge/window/volume/today, pattern/recovery/market/external, requirements/grade/penalty/reason, execution-plan/multi-TF/result-builder helper 구조로 분리.
       기존: mid_pullback 내부 상위 함수 4개가 각각 100줄 안팎이라 마지막 구조 마감 대상이었음.
       수정: `_find_mid_pullback_surge_anchor()`, `_build_mid_pullback_window()`, `_score_mid_pullback_primary_pattern()`, `_build_mid_pullback_execution_requirements()`, `_build_mid_pullback_result()` helper를 추가해 눌림목 분석 경로를 단계화.
  [#2] `_get_multi_tf_downtrend_context()`와 `_handle_entry_watch_reach_state()`를 daily/weekly/judge, strength-guard/sector-guard/block-reason helper 구조로 분리.
       기존: 다중 추세 차단과 진입 watch 도달 상태가 각각 100줄대 단일 본문이라 마지막 reach-state 정리 대상이었음.
       수정: `_calc_multi_tf_daily_context()`, `_calc_multi_tf_weekly_context()`, `_judge_multi_tf_downtrend()`, `_check_entry_watch_strength_guard()`, `_evaluate_entry_watch_sector_guard()`, `_handle_entry_watch_block_reason()` helper를 추가해 guard 판정을 짧게 유지.
- v121 (2026-03-28): 최종 마감 배치 — signal quality/intraday capture/retail context/KPI 재정리 + dynamic params logger 치환.
  [#1] `_apply_analyze_signal_quality()`를 relative-strength/investor/execution-speed/countertrend/indicator-failure helper 구조로 분리.
       기존: 투자주체·체결속도·역추세·보조지표·실패패턴이 100줄대 단일 함수에 섞여 수정 충돌 추적이 어려웠음.
       수정: `_apply_signal_quality_relative_strength()`, `_apply_signal_quality_investor_context()`, `_apply_signal_quality_execution_speed()`, `_apply_signal_quality_countertrend()`, `_apply_signal_quality_indicators_and_failures()` helper를 추가해 점수화 경로를 단계화.
  [#2] `_evaluate_intraday_capture_mode()`, `eval_retail_signal()`, `compute_signal_kpi()`를 각각 focus/detected/block summary, stock-trend/context-classify, load/group/bucket/loss helper 구조로 분리.
       기존: 장중 leader-followup 판정, 개인수급 컨텍스트 해석, KPI 계산이 각각 100줄 안팎의 단일 본문이라 2차 마감 대상이었음.
       수정: `_collect_intraday_capture_focus()`, `_collect_intraday_capture_detected_codes()`, `_classify_retail_signal_context()`, `_calc_signal_kpi()`, `_build_mid_pullback_bucket_kpi()` helper를 추가해 판정·집계 경로를 짧게 유지.
  [#3] `dynamic_params` 저장/복원 로그를 raw `print()` 대신 runtime logger wrapper로 치환해 비핫패스 로그 일관성을 강화.
- v120 (2026-03-28): 2차 마감 배치 — crossday/stale replay/result command/sector peer lookup 구조 정리.
  [#1] `_get_crossday_episode_context()`를 history/anchor/pullback/flag helper 구조로 분해해 전일 포함 연속 패턴 감지 경로를 단계화.
       기존: 힌트 조회, 일봉 anchor 탐색, 눌림·회복률 계산, prep/confirmed/near_upper 판정이 120줄대 단일 함수에 몰려 있었음.
       수정: `_load_crossday_episode_history()`, `_select_crossday_episode_anchor()`, `_calc_crossday_episode_pullback()`, `_build_crossday_episode_flags()` helper를 추가해 crossday episode 판정 경로를 분리.
  [#2] `_build_stale_replay_penalty_profile()`와 `_handle_result_command()`를 source/date-pressure/profile 및 parse/load/match/update/message helper 구조로 분해.
       기존: stale replay penalty 집계와 `/result` 수동 성과 기록이 각각 100줄대 단일 함수로 남아 있었고 상태 로드/갱신/메시지 조립이 한 본문에 섞여 있었음.
       수정: `_collect_stale_replay_date_pressure()`, `_collect_stale_replay_penalty_rows()`, `_build_stale_replay_penalty_payload()`, `_parse_result_command_payload()`, `_apply_result_signal_update()`, `_send_result_record_message()` helper를 추가해 상태 갱신과 메시지 경로를 단계화.
  [#3] `get_sector_stocks_from_kis()`를 base-context/candidate/peer/rank-fallback helper 구조로 분리해 섹터 peer 조회 경로를 정리.
       기존: 업종 조회, 후보 수집, peer 업종 확인, rank fallback이 한 함수에 묶여 수정 충돌과 예외 꼬리 추적이 어려웠음.
       수정: `_load_sector_stock_base_context()`, `_collect_sector_stock_candidates()`, `_collect_same_sector_peers_from_candidates()`, `_collect_same_sector_rank_fallback()` helper를 추가해 동업종 후보 조회 경로를 짧게 유지.
- v119 (2026-03-28): 최종 cleanup batch — analyze/bootstrap/sector momentum/overnight/market close/deep-news 정리 + logger/state helper 보강.
  [#1] `_bootstrap_analyze_context()`, `calc_sector_momentum()`, `run_overnight_monitor()`를 base/signal/liquidity/finalize 및 state/load/alert/render helper 구조로 분해하고 오버나이트 raw `print()`를 runtime logger로 치환.
       기존: 남아 있던 분석 부트스트랩/섹터 모멘텀/오버나이트 감시가 120줄대 단일 함수라 마지막 핵심 정리 단계가 미완료 상태였음.
       수정: `_build_bootstrap_analyze_base_context()`, `_passes_bootstrap_volume_liquidity_gate()`, `_calc_sector_momentum_score_bundle()`, `_apply_sector_leader_scores()`, `_collect_overnight_market_alerts()`, `_emit_overnight_monitor_logs()` 등으로 분리해 점수화·감시·요약 경로를 단계화.
  [#2] `run_daily_self_audit()`와 `on_market_close()`를 leader-load/detect/group/persist 및 reentry/carry/report/followup helper 구조로 재편하고 self-audit/market-close 상태 로드·저장 경로를 공통 helper로 정리.
       기존: 장마감 리포트와 self-audit가 긴 본문 + 중복 예외 꼬리 + raw print를 안고 있었음.
       수정: `_load_daily_self_audit_state()`, `_persist_daily_self_audit_entry()`, `_load_market_close_signal_state()`, `_build_market_close_*()` helper를 추가해 저장 경로와 메시지 조립을 분리하고 중복 꼬리를 제거.
  [#3] `analyze_news_deep()`를 cache/fallback/body/prompt/request/normalize helper 구조로 분해하고 심층분석 완료 로그를 runtime logger로 치환.
       기존: 본문 수집/프롬프트 생성/Claude 호출/JSON 정규화/오류 fallback이 100줄대 단일 함수에 묶여 있었음.
       수정: `_build_deep_news_prompt()`, `_request_deep_news_analysis()`, `_normalize_deep_news_result()`로 분리해 deep-news 경로를 짧게 유지하고 raw print 1건을 제거.
- v118 (2026-03-28): 잔여 고점수 후보/장후감지/조기포착/추적결과 알림 정리 — gap candidate/NXT postmarket/early detect/tracking result 구조 정리.
  [#1] `_score_next_open_gap_candidate()`를 context/basic-score/sector-history/market-risk/finalize helper 구조로 분리하고 rr<1.6 분기에서 남아 있던 dead `msg/item` 참조를 제거.
       기존: 점수화 함수 안에 장후반/NXT 기준 조회, 섹터·미국장·DART 반영, 진입계획 finalize가 모두 섞여 있어 유지보수와 런타임 안정성이 떨어졌음.
       수정: `_load_next_open_gap_candidate_context()`, `_score_next_open_gap_price_volume()`, `_apply_next_open_gap_sector_history()`, `_apply_next_open_gap_market_context()`, `_finalize_next_open_gap_candidate()` helper로 분리해 plan 계산과 점수 가중치를 단계화.
  [#2] `check_nxt_postmarket_detection()`과 `check_early_detection()`를 후보 context/스코어/뉴스·테마/finalize helper 구조로 분리.
       기존: NXT 장후 감지와 조기포착 경로가 각각 150줄 이상 단일 함수에 몰려 조정 충돌 위험이 남아 있었음.
       수정: `_build_nxt_postmarket_base_context()`, `_apply_nxt_postmarket_*()`, `_build_early_detection_candidate_context()`, `_passes_early_detection_hoga_gate()`, `_build_early_detection_entry_context()`, `_apply_early_detection_market_context()` 등으로 분리해 후보필터와 점수화/승격을 독립 검증 가능하게 정리.
  [#3] `_send_tracking_result()`를 header/cause/profit-guide/message/reentry-watch helper 구조로 분리하고 재진입 감시 등록 로그를 runtime logger로 치환.
       기존: 손절 원인 분석, 익절 가이드, 메시지 조립, 재진입 watch 등록이 한 함수에 섞여 있었고 `target` 선참조 위험과 raw `print()`가 남아 있었음.
       수정: `_build_tracking_result_*()` helper로 메시지 계산을 분리하고 `_register_tracking_reentry_watch_from_result()`로 저장·로그 경로를 정리해 추적결과 알림 안정성을 높임.
- v117 (2026-03-28): 잔여 상위 함수 대청소 — execution speed/auto tune context/theme context/US market/market leader 구조 정리.
  [#1] `get_execution_speed_metrics()`를 샘플수집/속도계산/최근성·호가/점수·finalize helper 구조로 분리.
       기존: execution speed 계산이 200줄대 단일 함수라 체결속도/눌림유지/호가 잔량 회귀를 추적하기 어려웠음.
       수정: `_collect_execution_speed_window_samples()`, `_collect_execution_speed_recent_profile()`, `_calc_execution_speed_score()`, `_finalize_execution_speed_metrics()` 등으로 분리해 미세체결·가속·freshness 점수 흐름을 단계화.
  [#2] `_auto_tune_apply_context_tuning()`와 `_apply_analyze_theme_context()`를 컨텍스트 섹션별 helper로 분해.
       기존: 시간대/오버나이트/실적리스크/geo 가중치와 테마 동조·확산·NXT·adaptive feedback이 각 160~200줄대 함수에 몰려 수정 충돌이 남아 있었음.
       수정: `_auto_tune_apply_*_context()`, `_apply_theme_*_context()` helper 구조로 나눠 자동조정과 테마 보정 경로를 독립적으로 점검할 수 있게 정리.
  [#3] `get_us_market_signals()`와 `_build_market_leading_sector_payload()`를 fetch/evaluate/render helper 구조로 재편하고 raw `print()`를 runtime logger로 치환.
       기존: 미국시장 fetch·국면판정·요약문 생성과 시장주도 섹터 후보·시세조회·렌더링이 각각 단일 함수에 묶여 있었음.
       수정: `_fetch_us_market_signal_values()`, `_evaluate_us_market_signal_result()`, `_build_market_leader_candidate_themes()`, `_maybe_build_market_leader_sector()`, `_render_market_leading_sector_payload()`로 분리해 로그 노이즈를 줄이고 구조를 단계화.
- v116 (2026-03-28): 대청소 배치 — premarket/geo/mid-pullback/NXT/send_alert 본체 분해 + dead-code 제거.
  [#1] `send_premarket_briefing()`를 거시/감시/공시·국면/NXT helper 구조로 분리해 장전 브리핑 조립을 단계화.
       기존: 미국/지정학/테마/감시종목/전일상한가/DART/국면/NXT 브리핑이 190줄대 단일 함수에 몰려 있었음.
       수정: `_build_premarket_macro_sections()`, `_build_premarket_watch_sections()`, `_build_premarket_dart_regime_sections()`, `_build_premarket_nxt_section()`으로 분리해 장전 브리핑 수정 충돌을 낮춤.
  [#2] `analyze_geopolitical_event()`를 cache/fallback/prompt/request/result-normalize helper 구조로 재편하고 raw `print()` fallback 로그를 runtime logger로 치환.
       기존: 캐시/프롬프트/Claude 호출/JSON 정규화/섹터 bias 반영/예외 fallback이 한 함수에 섞여 지정학 회귀 추적이 어려웠음.
       수정: `_build_geo_fallback_result()`, `_build_geo_analysis_prompt()`, `_request_geo_ai_analysis()`, `_normalize_geo_ai_result()`로 분리해 지정학 분석 경로를 단계화하고 raw print 3건을 제거.
  [#3] `run_mid_pullback_scan()`, `check_intraday_pullback_breakout()`, `check_nxt_preopen_detection()`를 후보 분석/점수화/실행 helper 구조로 대청소.
       기존: 눌림목 전체 스캔/장중 재상승 점수화/NXT 장전 감지가 각각 130~160줄대 단일 함수라 유지보수 충돌과 로직 누락 위험이 남아 있었음.
       수정: `_build_mid_pullback_scan_result()`, `_dispatch_mid_pullback_signal()`, `_build_intraday_pullback_context()`, `_score_intraday_pullback_signal()`, `_build_nxt_preopen_context()`, `_finalize_nxt_preopen_signal()` 등으로 분리해 실행 단계를 분명히 함.
  [#4] `send_alert()`에서 실제 상세 발송에 쓰이지 않던 dead code 계산 블록을 제거하고 compact/detail 경로만 남겨 경량화.
       기존: entry/indicator/position/pattern block를 길게 계산했지만 실제 상세 발송은 `_build_capture_focus_message()`만 사용해 dead code가 남아 있었음.
       수정: `_should_throttle_send_alert_signal()`, `_build_send_alert_visuals()`, `_build_send_alert_compact_text()` 중심으로 정리해 본체를 얇게 유지.
- v115 (2026-03-28): 구조 정리 9차 — entry_watch/일반포착 dispatch helper 분해 + plain except 잔여 경로 정리.
- v114 (2026-03-28): 구조 정리 8차 — analyze/geo/scan 시장·실행 컨텍스트 분해.
  [#1] `_apply_analyze_market_context()`를 미국/ETF/공매도/수급/뉴스/지정학/테마/실적 helper로 분리.
       기존: 시장·뉴스·지정학·실적 보정이 200줄대 단일 함수에 섞여 있어 점수 회귀 원인 추적이 어려웠음.
       수정: `_analyze_us_market_adjustment()`, `_analyze_news_context()`, `_apply_geo_sector_context()`, `_apply_earnings_risk_context()` 등 단계별 helper로 분리해 점수 보정 책임을 분명히 함.
  [#2] `run_geo_news_scan()`을 감지/상태저장/메시지조립/발송/야간워치/geo prewatch helper 구조로 분리.
       기존: 지정학 이벤트 감지부터 전역상태 저장, 메시지 조립, 야간 워치리스트, geo prewatch 등록이 160줄대 단일 함수에 몰려 있었음.
       수정: `_load_detected_geo_event()`, `_store_geo_event_state()`, `_build_geo_event_message()`, `_maybe_register_geo_issue_prewatch()` 등으로 나눠 흐름을 단순화.
  [#3] `run_scan()`을 runtime context/야간워치/KRX/NXT/rank·peer/조기포착/섹터게이트/후속훅 helper 구조로 분리.
       기존: 시장별 스캔과 알림 디스패치, 후속 감시 훅이 160줄대 단일 함수에 섞여 있어 장중 회귀 추적이 어려웠음.
       수정: `_build_scan_runtime_context()`, `_scan_krx_market_candidates()`, `_scan_rank_and_theme_candidates()`, `_dispatch_scan_alerts()`로 역할을 분리해 일반 포착 핫패스를 짧게 유지.
- v113 (2026-03-28): 구조 정리 7차 — tracking/DART batch 본문 분해 + trailing pnl 경로 안정화.
  [#1] `_run_tracking_results_batch()`를 record helper 구조로 재편.
       기존: orphan/가격조회/뉴스감시/분할익절/트레일링/결과확정이 400줄대 한 함수에 몰려 trailing 보조경로 회귀 추적이 어려웠음.
       수정: `_handle_tracking_orphan_record()`, `_get_tracking_runtime_price()`, `_run_tracking_record_watchdogs()`, `_maybe_send_tracking_partial_exit_guide()`, `_process_tracking_trailing_mode()`, `_handle_tracking_target_reached()`, `_finalize_tracking_exit_record()`, `_process_tracking_result_record()`로 분리.
  [#2] trailing 경로의 `pnl_now`를 공통 계산값으로 승격.
       기존: 뉴스감시 주기 미도달 시 trailing 수급이탈/오버나이트 위험 경로에서 `pnl_now`가 정의되지 않을 가능성이 있었음.
       수정: 가격 갱신 직후 공통 `pnl_now`를 계산해 trailing/경고 로직이 동일 값을 쓰도록 정리.
  [#3] `_run_dart_intraday_batch()`를 item context/helper 구조로 재편.
       기존: seen 처리/이벤트 판정/가격반응/지표수집/메시지조립/진입감시 등록이 300줄대 단일 함수에 몰려 DART 회귀 수정이 어려웠음.
       수정: `_build_dart_item_context()`, `_prepare_dart_event_context()`, `_load_dart_deep_analysis()`, `_fetch_dart_price_snapshot()`, `_passes_dart_reaction_gate()`, `_collect_dart_market_metrics()`, `_build_dart_message_blocks()`, `_register_dart_execution_watch()`, `_dispatch_dart_intraday_item()` 구조로 분리.
       수정: `rec_name = rec.get("name", code)`를 기준으로 관련 경로를 통일해 대표 레코드 메시지와 위험 경고가 안정적으로 동작하도록 보정.
- v111 (2026-03-28): 구조 정리 5차 — force/mid_pullback/signal_log/stats 분해 + mid pullback finalize 경로 복구.\n  [#1] `detect_force_pattern()`을 호가/매집/스마트머니/마감체결/계단거래량/간격매수 helper로 분리.\n       기존: 세력 패턴 6종이 300줄대 단일 함수에 섞여 있어 패턴별 조정과 회귀 점검이 어려웠음.\n       수정: `_detect_force_*` helper와 `_build_force_pattern_result()`로 나눠 패턴별 로직을 독립적으로 유지.\n  [#2] `analyze_mid_pullback()`를 base-context/scoring/finalize helper 구조로 분해하고, `_finalize_mid_pullback_signal()`가 실제로 적용되도록 unreachable return을 복구.\n       기존: 눌림목 분석이 270줄대 단일 함수였고, 최종 `result` 후처리 구문이 조기 return 뒤에 있어 실행되지 않았음.\n       수정: `_build_mid_pullback_base_context()`, `_score_mid_pullback_base_context()`, `_finalize_mid_pullback_analysis()`로 분리하고 finalize 경로를 정상화.\n  [#3] `save_signal_log()`를 context/representative-update/new-record helper 구조로 분해하고 저장 로그를 runtime logger wrapper로 통일.\n       기존: 대표 레코드 갱신과 신규 레코드 생성이 250줄대 단일 함수에 몰려 있었고 raw `print()`도 남아 있었음.\n       수정: `_build_signal_log_context()`, `_update_representative_signal_log_record()`, `_build_new_signal_log_record()`로 분리하고 `_log_info_msg/_log_error_msg`로 정리.\n  [#4] `_send_stats()`를 통계 컨텍스트/헤더/유형별/시간대·테마/KPI/시장·가중치 helper 구조로 재편.\n       기존: 통계 메시지 조립이 300줄대 단일 함수라 메시지 수정 시 충돌과 누락 위험이 컸음.\n       수정: `_build_signal_stats_context()`, `_build_signal_stats_header()`, `_append_signal_stats_*` helper로 섹션별 책임을 분리.\n\n- v110 (2026-03-28): 구조 정리 4차 — 추적/공시/진입감시 핫패스 분해 + entry alert helper 구조화.\n  [#1] `track_signal_results()`와 `run_dart_intraday()`를 짧은 오케스트레이션 함수로 재편하고 각 실행 사이클을 전용 helper로 분리.\n       기존: 추적 결과 판정과 DART 장중 처리 루프가 각각 300~400줄대 단일 함수라, 후속 수정 시 회귀 추적과 오류 격리가 어려웠음.\n       수정: `_run_tracking_results_cycle()` / `_run_dart_intraday_cycle()` helper로 실행 사이클을 분리해 핫패스 진입점을 짧게 유지.\n  [#2] `check_entry_watch()`를 만료/호가해결/극값갱신/도달처리/finalize helper 구조로 정리.\n       기존: 시장 스냅샷 해석, NXT 참고도달, 근거약화 차단, 진입불가 차단, 만료 아카이브가 한 함수에 섞여 있었음.\n       수정: `_handle_entry_watch_expiry`, `_resolve_entry_watch_quote`, `_update_entry_watch_intraday_extremes`, `_handle_entry_watch_reach_state`, `_process_entry_watch_item`, `_finalize_entry_watch_expired_items`로 역할을 분리.\n  [#3] `_send_entry_phase_alert()`를 컨텍스트 준비/1차 메시지/2차 메시지/최종 기록 helper로 분해.\n       기존: 진입도달 메시지 문맥 조립과 기록 반영이 한 함수에 몰려 있어 후속 메시지 변경 시 충돌 위험이 컸음.\n       수정: `_prepare_entry_phase_alert_context`, `_send_phase1_entry_alert_message`, `_send_phase2_entry_alert_message`, `_finalize_entry_phase_alert`로 분리하고 최종 도달 로그도 logger wrapper로 통일.\n\n- v109 (2026-03-28): 구조 정리 3차 — auto_tune / poll_telegram_commands 분해 + 텔레그램 명령 핸들러 모듈화.
  [#1] `auto_tune()` 400줄대 핫패스를 로드/스냅샷/긴급튜닝/신호유형/컨텍스트/KPI/최종저장 helper로 분리.
       기존: `analyze()`는 분해됐지만 `auto_tune()`는 여전히 초대형이라 조정 흐름 추적과 충돌 점검이 어려웠음.
       수정: `_auto_tune_*` helper로 단계별 책임을 분리하고, 리더 생략/무변경/중복알림 메시지도 logger wrapper 기준으로 통일.
  [#2] `poll_telegram_commands()`를 업데이트 수집/명령 추출/명령 디스패치 구조로 재편하고, `/status /list /week /daily /geo /us /overnight` 등을 전용 helper로 모듈화.
       기존: 텔레그램 명령 루프가 400줄대 단일 함수라 명령 추가·회귀 점검·예외 추적이 어려웠음.
       수정: `_poll_telegram_fetch_updates`, `_extract_telegram_command_payload`, `_dispatch_telegram_command`, `_handle_telegram_*` 계열로 분리해 핫패스를 짧게 유지.
- v108 (2026-03-28): 운영 정리 2차 — 비핫패스 로그 정리 + 추가 임계값 중앙화.
  [#1] storage/watchdog/preclose-gap/rank-fallback/NXT전환/추적결과 등 비핫패스 운영 함수의 raw `print()`를 runtime logger wrapper로 추가 치환.
       기존: 핵심 핫패스는 정리됐지만, 운영/보조 경로에는 `print()`가 남아 있어 로그 의도와 경고 레벨 표현이 다시 흐려질 수 있었음.
       수정: 비핫패스라도 운영적으로 자주 보는 경로는 `_log_info_msg/_log_warn_msg` 중심으로 통일해 raw `print()` 의존을 더 줄임.
  [#2] watchdog/preclose-gap/NXT전환/추적감시 관련 핵심 숫자를 상수로 끌어올려 재검증 기준을 추가 정리.
       기존: 3.0/30/1800/1.03/0.97/14:45~15:05/19:20~19:35 같은 기준이 함수 내부에 남아 있었음.
       수정: `WATCHDOG_RANK_*`, `PRECLOSE_GAP_*`, `TRACK_NEWS_WATCH_INTERVAL_SEC`, `NXT_SURGE_*` 상수로 중앙화해 운영 기준을 코드 상단에서 일관되게 읽게 맞춤.
- v107 (2026-03-28): 운영 정리 — 핵심 핫패스 runtime logger 명시화 + 핵심 임계값 상수화.
  [#1] `_runtime_log_message()` / `_log_info_msg()` / `_log_warn_msg()` / `_log_error_msg()` 추가.
       기존: 핵심 운영 핫패스가 `print()` 브리지에 많이 의존해 의도한 로그 레벨과 코드 표현이 흐렸음.
       수정: 핵심 스캔/알림/진입감시/지정학/DART 경로는 명시적 runtime logger wrapper를 우선 사용하도록 정리.
  [#2] `MIN_TRADABLE_SIGNAL_PRICE`, `GENERAL_GRADE_A_CUT/B_CUT`, `NXT_PREOPEN_*`, `ISSUE_PREWATCH_*`, `GEO_PREWATCH_*` 상수 추가.
       기존: 500/80/60/1.5/5.0 같은 핵심 임계값이 핫패스 여러 곳에 흩어져 있었음.
       수정: 실전 임계값을 설정 가능한 상수 블록으로 끌어올려 해석/튜닝/재검증 기준을 통일.
- v106 (2026-03-28): 구조수술 — analyze 분해 + 소형 상태파일 번들 통합 + 주요 상태 저장 원자화/공통화.
- v105 (2026-03-28): 무음 예외 보강 — plain except Exception 전면 구조화 로그 연결 + _swallow_exception 재귀 제거.
- v104 (2026-03-28): 지정학 실전형 보수화 — 방향 일치 근거 기반 노출/점수/프리워치 제한.
  [#1] `_collect_geo_sector_history_stats()` / `_get_geo_sector_evidence_map()` / `_find_geo_sector_evidence()` 추가.
       기존: `/geo`와 정기 지정학 메시지의 섹터별 점수는 과거 방향 일치가 약한 섹터까지 동일하게 나열돼, 표시 점수와 실제 주가 반응 체감이 자주 어긋났음.
       수정: 섹터별 과거 완료 신호를 방향 기준(상승/하락)으로 다시 집계해 `방향 일치율`, `방향 기대값`, `근거 등급(actionable/mixed/weak/insufficient)`을 계산하고 캐시하도록 정리.
  [#2] 지정학 메시지 표시를 `섹터별 영향` → `실전형 섹터 후보` 중심으로 보수화.
       기존: 내부 보정치 성격의 `+8점/-5점`이 외부 메시지에서는 실제 종목 기대수익처럼 읽히기 쉬웠고, 방향 일치 근거가 약한 섹터도 모두 노출됐음.
       수정: 외부 메시지에는 `내부보정` 문구를 명시하고, 과거 방향 일치 근거가 약한 섹터는 숨긴 뒤 숨김 개수만 요약해 정보성 잡음을 줄임.
  [#3] 지정학 섹터 보정과 prewatch를 근거 있는 섹터로 제한.
       기존: `GEO_SECTOR_BIAS`와 `sector_directions`는 근거 약한 섹터에도 그대로 반영돼, 점수 가감·섹터 모멘텀·geo prewatch가 실전성 약한 섹터까지 따라갈 수 있었음.
       수정: `analyze()`/`calc_sector_momentum()`/`run_geo_news_scan()`에서 `actionable` 근거가 확인된 섹터에만 지정학 점수 보정과 상승섹터 prewatch를 허용.
  [#4] 하락 섹터의 과거 유사 통계 해석을 방향 기준으로 교정.
       기존: 하락 섹터도 `몇 건↑` 기준으로 표시돼, 실제로는 하락 적중이 많아도 메시지 해석이 왜곡될 수 있었음.
       수정: 상승/하락 공통으로 `방향 일치`와 `방향 기대값`을 표시해, 하락 섹터도 하락 방향 적중 기준으로 읽히게 맞춤.
  이유: 사용자가 지정학 섹터 점수는 보이는데 실제 종목 반응이 약하다고 지적했고, 실전형 알림 품질 우선 원칙상 방향 일치 근거가 약한 섹터의 외부 노출과 내부 가점을 같이 보수화할 필요가 있었음.
  개선점: 지정학 메시지 해석력↑, 실전성 약한 섹터 노출↓, geo prewatch 잡음↓, 지정학 점수의 실전 적합도↑.
  주의점: 이번 버전은 지정학 섹터의 표시/보정/프리워치 기준을 조정한 것이다. 거래정지 체계, 눌림목 A전용 외부억제, 진입가/손절가/목표가 산식은 유지한다.
- v103 (2026-03-28): 운영 안전화 — 무음 예외 제거 + 구조화 로깅 + 상태파일 경고 + HTTP 호출 계층 보강.
  [#1] `logging` 기반 런타임 로거와 전역 `print` 래퍼를 추가.
       기존: `print()` 위주 운영이라 Railway 로그에서 INFO/WARN/ERROR 구분이 약했고, 일부 stderr/표준출력 혼합 시 원인 추적이 느렸음.
       수정: 표준 출력 기반 로거를 초기화하고 전역 `print`를 래핑해 기존 출력은 유지하면서도 INFO/WARNING/ERROR 레벨로 함께 남기게 정리.
  [#2] `_swallow_exception()`과 예외 억제 dedupe를 추가하고 `except Exception: pass` 류를 구조화 기록으로 교체.
       기존: 상태파일 저장/로드, 장전/장후 메시지, 보조 계산, 텔레그램 정리 등에서 예외가 조용히 묻혀 실제 장애 원인을 놓칠 수 있었음.
       수정: 예외를 무시해야 하는 경로도 함수명/라인/예외형을 남기고, 반복 동일 예외는 dedupe해 로그 폭주를 막음.
  [#3] `_read_json_unlocked()` / `_read_json_safe()`를 보강해 파일 부재는 조용히 통과하되 JSON 파손/로드 실패는 경고를 남기도록 수정.
       기존: 상태파일 손상·파싱 실패도 기본값으로 무음 초기화돼, 운영자가 어떤 파일이 깨졌는지 파악하기 어려웠음.
       수정: 실제 파일이 있는데 로드 실패한 경우에만 경고를 남기고 기본값 fallback을 유지.
  [#4] `requests.get/post` 전역 래퍼와 기본 timeout을 추가.
       기존: 직접 `requests.get/post` 호출은 timeout/실패 기록 정책이 제각각일 수 있었음.
       수정: 기본 timeout을 통일하고 실패 시 공통 로깅을 남기는 wrapper를 통해 직접 호출 경로의 운영 위험을 낮춤.
  [#5] 로컬 `_push` helper 3개를 역할별 이름으로 분리하고, 정적 smoke test 파일을 추가.
       기존: 서로 다른 함수 안의 로컬 `_push`가 반복돼 코드 읽기 혼선이 있었고, 무음 예외/중복 정의 같은 기본 회귀를 자동 확인하는 테스트가 없었음.
       수정: helper 명칭을 역할별로 분리하고, `v103_smoke_test.py`로 `except-pass`/중복 최상위 함수/버전 동기화 기본 검사를 추가.
  이유: 다른 AI 지적 중 실제 운영 리스크가 큰 항목은 무음 예외, 상태파일 무음 초기화, 로깅 부재, 직접 HTTP 호출의 불균일성이었고, 이를 먼저 한 번에 정리할 필요가 있었음.
  개선점: 장애 가시성↑, 상태파일 파손 추적력↑, 직접 HTTP 호출 안전성↑, 회귀 기본검사↑.
  주의점: 이번 버전은 진입가/손절가/목표가 산식이나 A전용 외부알림 정책을 바꾸지 않는 운영 안전화 버전이다.
- v102 (2026-03-27): 일반 눌림목 폐기 — 그냥 눌린 후보 제거 + 실전형 재상승/재테스트만 존치 + A 이외 외부알림 유지.
  [#1] `MID_PULLBACK_MIN/MAX`, `MID_PULLBACK_DAYS_MIN/MAX` 기본값을 재축소하고 `_is_disabled_general_mid_pullback()`를 추가.
       기존: 눌림목 후보군이 8~45% / 2~15일 범위로 너무 넓어, 그냥 눌린 일봉 추세형(`daily_trend`)도 반복 후보에 남을 수 있었음.
       수정: 기본 눌림 범위를 12~28% / 3~9일로 좁히고, `daily_trend` 일반 눌림목은 스캔 단계에서 바로 제외해 실전형 재상승/재테스트만 남김.
  [#2] `analyze_mid_pullback()`의 재상승 최소 게이트를 강화.
       기존: 당일 양봉 또는 거래량 회복 중 하나만 있어도 일봉 눌림목 후보가 살아남아, 약한 반등도 점수 누적으로 외부 A 직전까지 갈 여지가 있었음.
       수정: 일봉 눌림목은 당일 양봉 + 거래량 회복 + 20일선 회복/수급전환/상대강도 중 1개 이상을 기본 요구로 바꿔, 그냥 눌린 종목을 초기에 잘라냄.
  [#3] 눌림목 자동조정 범위를 실전형 기준으로 재고정.
       기존: 자동조정이 승률 회복 시 `mid_pullback_min`을 다시 8%까지 완화할 수 있어, 폐기한 일반 눌림목 구간이 재유입될 수 있었음.
       수정: 자동조정 하한/상한을 12~28% 안쪽으로 고정해, 구조적으로 제거한 일반 눌림목이 다시 살아나지 않게 제한.
  [#4] `run_mid_pullback_scan()`에 일반 눌림목 제외 분기 추가.
       기존: A전용 외부알림 정책은 있었지만, 일반 눌림목도 내부 기록/추적 대상으로 반복 순위에 오를 수 있었음.
       수정: `daily_trend` 일반 눌림목은 외부알림 이전 단계에서 스캔 제외하고, 실전형 `weekly_monthly_trend / gap_first_pullback / intraday_reclaim`만 알림 후보로 유지.
  이유: 외부 비교와 누적 성과 모두 일반 눌림목은 승률/손익이 약했고, 사용자는 정보성 눌림목보다 실전형 A 알림만 원했음.
  개선점: 그냥 눌린 종목 후보↓, 장초반 약한 눌림 재노출↓, 실전형 재상승/재테스트 밀도↑, A 이외 외부알림 집중도 유지.
  주의점: 이번 버전은 일반 눌림목을 꺼내는 구조 수정이다. `눌림목/A전용 외부억제`, 진입가/손절가/목표가 산식, 거래정지 체계는 그대로 유지.
- v101 (2026-03-27): 눌림목 재정렬 — 장초반 과신호 억제 + 실행 A게이트 재강화 + 공개 검증 패턴 확증 연동.
  [#1] `_get_mid_pullback_session_context()` / `_build_mid_pullback_global_context()` 추가.
       기존: 눌림목은 장초반 KRX와 장후/NXT를 같은 execution confirm 축으로 다뤄, 장초반 약한 반등도 A등급 후보로 과상향될 수 있었음.
       수정: KRX 장초반/정규장 일반/장후 NXT를 구분하는 세션 컨텍스트와, 눌림목 전용 공개 검증 패턴 컨텍스트(거래대금+고가 유지 / ORB / 전고 돌파 / 상한가 근접)를 별도로 계산.
  [#2] `_get_mid_pullback_execution_profile()` / `_apply_mid_pullback_execution_grade()` 재조정.
       기존: `MID_PULLBACK`은 B등급 고점수(95점↑)면 실행 A로 쉽게 승격되고, 장초반 intraday reclaim도 core 확증 1개 수준으로 외부 A에 도달할 수 있었음.
       수정: 장초반 KRX에서는 ORB/전고 돌파/고가 유지 같은 강한 패턴 확증이 없으면 A를 금지하고, intraday reclaim은 core 2개 이상을 요구하며, B→A 승격은 110점↑ + 강한 패턴 + core 2개 이상일 때만 허용.
  [#3] `analyze_mid_pullback()` / `check_intraday_pullback_breakout()` 반환 메타 보강.
       기존: 눌림목 결과에 당일 시가/고가/거래량과 turnaround 여부, 공개 패턴 컨텍스트가 충분히 남지 않아, 실행 보정이 가격 구조보다 점수 총합에 치우쳤음.
       수정: 당일 시가/고가/거래량/turnaround_confirmed/global_pattern_context를 함께 남겨 실행 A 여부가 실제 강세 구조를 기준으로 결정되게 정리.
  [#4] `v100`의 공개 검증 패턴 4종을 눌림목에도 선택적으로 재사용.
       기존: 공개 검증 패턴 4종은 일반 상승주 승격에는 반영됐지만, 눌림목은 별도 엔진이라 장초반 약한 반등과 강한 재상승을 충분히 구분하지 못했음.
       수정: 눌림목은 강한 ORB/전고 돌파/고가 유지/상한가 근접 선행이 동반될 때만 공격적으로 승격하고, 그렇지 않으면 내부추적/B등급으로 남기도록 보수화.
  이유: 실제 누적 성과 점검에서 눌림목 A가 B보다 약했고, 특히 KRX 장초반 눌림목이 계속 문제였으므로, 외부 A 알림을 강한 재상승형 위주로 다시 좁혀야 했음.
  개선점: 눌림목 장초반 과신호↓, 가짜 반등 A승격↓, 강한 재상승/고가 유지형 A품질↑, NXT 후반 재상승형 보존.
  주의점: `눌림목/A전용 외부억제`는 유지. 이번 수정은 눌림목 실행 A게이트와 점수 해석을 보수화하는 범위에 한정.
- v100 (2026-03-27): 패턴 검증 반영 — 거래대금+고가 유지 / ORB·전고 돌파 / 상한가 근접 선행 / 섹터 확산을 기존 신호 승격·가점·차단에 통합.
  [#1] `_get_recent_avg_trade_amount()` / `_get_recent_high_breakout_context()` / `_build_global_pattern_context()` 추가.
       기존: 공개 검증에서 남긴 핵심 패턴 4개를 코드가 직접 계산하지 않아, 거래대금 급증·고가 유지·전고 돌파·상한가 근접 선행을 기존 change_rate/volume_ratio 축으로만 우회 해석했음.
       수정: 최근 평균 거래대금 대비 value ratio, intraday 고가 유지율, 최근 N일 고점 돌파, opening range 돌파, 상한가 거리, 테마 breadth를 공통 패턴 컨텍스트로 계산하는 helper를 추가.
  [#2] `analyze()`에 패턴 기반 조기 승격/가점 연결.
       기존: `EARLY_DETECT/SURGE/NEAR_UPPER` 조기 승격은 cross-day와 전 시간대 profile 중심이라, 거래대금+고가 유지형/장초반 ORB/전고 돌파/상한가 근접 선행을 직접 반영한 승격은 부족했음.
       수정: 상한가 근접 선행형은 `NEAR_UPPER` 조기 승격, ORB·전고 돌파·거래대금+고가 유지형은 `EARLY_DETECT/SURGE` 조기 승격 및 가점으로 연결하고, 약한 섹터 breadth는 follow 가점을 보수화.
  [#3] `check_nxt_preopen_detection()` / `check_nxt_postmarket_detection()`에도 동일 패턴 보너스 연결.
       기존: NXT 장전·장후 전용 포착은 직접뉴스/섹터 모멘텀 위주라, 전 시간대 반영 원칙과 달리 거래대금+고가 유지·전고 돌파·상한가 근접 선행의 공통 패턴 점수가 제한적으로만 반영됐음.
       수정: NXT 장전·장후 신호에도 동일 패턴 helper를 연결해, 전 시간대(08:00~20:00)에서 공개 검증 패턴이 같은 기준으로 점수화되게 정리.
  [#4] 반환 payload와 A완화 support token에 패턴 메타 추가.
       기존: 로그/후속 판단에서 어떤 공개 검증 패턴이 발동했는지 바로 추적하기 어려웠음.
       수정: value ratio, high hold, recent high breakout, ORB, near-limit lead, theme expansion 메타를 payload에 남기고, A완화 support token에도 `고가 유지`, `ORB`, `전고 돌파`, `섹터 확산`을 반영.
  이유: 사용자가 요구한 것은 프로그램 구조와 별개로 공개 검증에서 남긴 패턴 4개를 실제 코드에 NXT 포함 전 시간대로 반영하는 것이었고, 기존 v99는 cross-day/시간대/profile 보정까지는 있었지만 패턴 4개가 직접 코드 엔진으로 고정돼 있지 않았음.
  개선점: 좋은 강세 종목 조기 승격↑, 상한가 근접 선행 포착↑, 장초반 ORB·전고 돌파 포착↑, 섹터 대장→후발 확산 확증↑, 약한 breadth follow 과가점↓.
  주의점: `눌림목/A전용 외부억제`, 진입가/손절가/목표가 산식, 거래정지 차단 체계는 유지. 이번 수정은 패턴 4개를 기존 신호 타입에 통합하는 범위에 한정.
- v99 (2026-03-27): 자동조정 불가 구조 문제의 텔레그램 코드수정 요청 알림 추가.
  [#1] `CODE_CHANGE_REQUEST_STATE_FILE`, `_send_code_change_request_alert()`, `_build_watchdog_code_change_request()` 추가.
       기존: 장중 워치독이 `candidate_miss`, `grade_suppressed` 같은 구조 문제를 감지해도 자가진단 메시지 안에만 섞여 보여, 자동조정 불가 코드수정 요청이 별도 행동 알림으로 남지 않았음.
       수정: 자동조정 불가 구조 문제를 별도 `🛠 [코드수정 요청]` 텔레그램 알림으로 보내고, 이슈키별 쿨다운 상태를 파일로 저장해 재시작 후에도 중복 발송을 억제.
  [#2] `run_intraday_watchdog()`에서 구조 문제 감지 시 전용 코드수정 요청 알림 연결.
       기존: `candidate_miss`/`grade_suppressed`는 변화 목록에 문구만 남고, 운영자가 일반 워치독 메시지에서 직접 추출해야 했음.
       수정: 주 차단 사유가 구조 문제이거나 자동 완화가 불가한 상태면 `원인/증상/추정 경로/점검 대상 함수`를 담은 코드수정 요청 알림을 별도로 발송.
  [#3] 문서 세트에 `자동조정 가능 vs 코드수정 요청` 운영 원칙 명시.
       기존: 자동조정 불가 항목을 텔레그램 요청으로 외부 통지하는 원칙이 대화에는 있었지만 기준 문서에는 충분히 고정돼 있지 않았음.
       수정: 포인터/핸드오프/시작 절차/운영 규칙에 `자동조정 불가 구조 문제는 코드수정 요청 알림 발송` 원칙을 명시.
  이유: 사용자가 원한 것은 "자동조정으로 못 고치는 부분은 프로그램이 텔레그램으로 코드수정 요청"하는 것이었고, 기존 구현은 제한적 워치독 경고 수준에 머물렀음.
  개선점: 자동조정 가능/불가 경계 명확화, 구조 문제 외부 요청 가시성↑, 재시작 후 중복 요청 억제↑.
  주의점: 이번 버전은 `candidate_miss`/`grade_suppressed` 등 워치독이 잡을 수 있는 구조 문제를 우선 대상으로 하며, 모든 전략 구조 문제를 자동 분류하는 범용 시스템은 아님.
- v98 (2026-03-27): 전 시간대(08:00~20:00) 초기 강세 내부포착→재상승 실행형 승격 강화 + SURGE/NEAR_UPPER 조기 승격의 시간대 확장.
  [#1] `_get_full_session_capture_stage()` / `_get_full_session_capture_profile()` / `_promote_signal_from_full_session_flow()` 추가.
       기존: 장초반(09:00~10:00) 거래량 완화와 cross-day 일부 승격만 있어, 좋은 상승 종목의 조기 포착 보정이 전체 장운영시간으로 이어지지 않았음.
       수정: NXT 장전·정규장 장초반·오전·오후·장후 NXT까지 08:00~20:00 전 시간대별로 서로 다른 승격 기준/거래량 완화/내부포착 강도를 적용.
  [#2] `analyze()`의 일반 포착 시작부를 시간대 확장 승격 체인으로 보강.
       기존: 절대 상승률(5%/25%/29%)과 장초반 거래량 완화 의존이 커, 오전 이후/장후 강세 재가속은 포착이 늦거나 후보 단계에서 멈출 수 있었음.
       수정: 전 시간대 profile을 읽어 `EARLY_DETECT`/`SURGE`/`NEAR_UPPER` 조기 승격을 허용하고, 그에 맞는 점수 보정과 시간대별 거래량 기준 완화를 연결.
  [#3] `check_early_detection()`를 전 시간대 profile 기준으로 보강.
       기존: `price_min`/`volume_min`/재확인 횟수가 사실상 장초반 중심으로만 움직여, 오후·장후 재가속/연속 패턴 포착이 둔감했음.
       수정: 시간대별 price/volume/confirm 기준을 읽어 초기 강세 내부포착을 전 시간대로 확장하고, 재상승 시 `SURGE`/`NEAR_UPPER` 승격이 가능하게 함.
  [#4] `_should_relax_general_a_threshold()`에 전 시간대 A완화 bonus 연동.
       기존: A완화 자격이 신호 속성 중심이라, 좋은 상승 종목이 시간대별 강세 profile을 반영해 A로 올라갈 여지가 충분치 않았음.
       수정: 전 시간대 profile의 `a_relax_bonus`를 반영해, 같은 질의 재가속 종목이면 시간대에 따라 A 자격을 조금 더 현실화.
  이유: 사용자가 요구한 “좋은 상승 종목을 더 빨리 잡는 구조를 장초반만이 아니라 전체 장운영시간에 적용”이 v97까지는 부분 반영 상태였음.
  개선점: 장전 NXT~정규장~장후 NXT까지 초기 강세 내부포착↑, 재상승 실행형 승격↑, 좋은 상승 종목의 SURGE/NEAR_UPPER 조기 인식↑.
  주의점: `눌림목/A전용 외부억제`는 이번에도 유지. 이번 수정은 일반 상승 종목의 전 시간대 포착 구조에만 한정.
- v97 (2026-03-27): 상한가 잠김/행동 불가 상한가류 일반 포착 차단 + UPPER_LIMIT soft allow 제거.
  [#1] `_detect_entry_block_reason()`의 상한가류 차단 기준을 강화.
       기존: `UPPER_LIMIT`/`NEAR_UPPER`는 `limit_up_locked`가 아니면 `no_ask_liquidity` soft allow 예외로 다시 살아날 수 있어, 상한가 잠김·행동 불가 종목이 일반 포착으로 나갈 수 있었음.
       수정: 상한가류(`UPPER_LIMIT`/`NEAR_UPPER`)는 `ask_qty<=0`면 `upper_limit_reached` 또는 `limit_up_locked`로 하드 차단되게 조정.
  [#2] `_should_soft_allow_no_ask_liquidity_general()`에서 `UPPER_LIMIT`/`NEAR_UPPER` soft allow 제거.
       기존: 거래량 폭발·급등 조건만 크면 `UPPER_LIMIT no_ask_liquidity soft allow`가 유지돼, 오르는 동안엔 조용하다가 상한가 잠김 시점에만 알림이 나갈 수 있었음.
       수정: `SURGE`/`STRONG_BUY`/`EARLY_DETECT` 등 관찰 우선형 신호만 soft allow를 유지하고, 상한가류는 행동 불가 상태면 일반 포착을 외부 발송하지 않음.
  [#3] 문서 세트(v97) 정합성 복구.
       기존: `v96` 코드 실물과 일부 문서에 `v95` 문구가 남아 기준 세트 정합성이 어긋나 있었음.
       수정: 코드 기준을 소스로 삼아 포인터/핸드오프/시작절차/운영규칙을 모두 `v97` 세트로 다시 동기화.
- v96 (2026-03-27): cross-day 연속 패턴 보강 + 초기 강세 내부포착→재상승 실행형 연결 + 일반 상승주 조기 SURGE 보강 + guard 반복알림 1회성 유지.
  [#1] `_get_crossday_episode_context()` / `_maybe_promote_signal_from_crossday_episode()` / `_should_require_execution_setup_from_crossday()` 추가.
       기존: 날짜 경계를 넘는 1차 상승→눌림→재상승 맥락이 일반 포착/조기포착 경로에서 분절적으로만 반영돼, 전날 급등 후 다음날 재가속 같은 케이스가 늦게 보이거나 실행 구조로 안정적으로 이어지지 못했음.
       수정: 최근 signal_log 힌트 + 최근 일봉 구조를 함께 읽어 cross-day 에피소드 맥락을 계산하고, 초기 강세는 내부포착으로 유지한 뒤 재상승 확인 시 `SURGE/NEAR_UPPER` 후보 자격과 실행 준비 상태를 함께 부여.
  [#2] `analyze()` / `check_early_detection()`에 cross-day 연속 패턴 로직 연결.
       기존: `SURGE/NEAR_UPPER`는 당일 상승률 절대기준 위주라, 전날 1차 상승 후 다음날 재상승 종목이 초기 단계에서 `SURGE`로 늦게 보이거나 아예 `EARLY_DETECT` 내부추적으로만 남을 수 있었음.
       수정: 연속 패턴이 확인되면 3%대 재가속도 `SURGE` 후보로, 23%대 강한 재가속은 `NEAR_UPPER` 후보로 조기 승격 가능하게 하고, 일반 포착 거래량 게이트도 cross-day 맥락에 한해 현실화.
  [#3] `save_signal_log()` / `register_entry_watch()` / `_notify_entry_guard_followup()`의 연속 패턴 메타·1회성 guard 상태 정리 보강.
       기존: 초기 강세 내부포착/재상승 실행 맥락과 guard 1회성 여부가 signal_log/active watch에 충분히 남지 않아, 다음 턴 기준 재진술과 실로그 확인 시 반영 여부 추적이 어려웠음.
       수정: `crossday_episode_*` / `execution_setup_required` / `entry_guard_alert_sent_once` 상태를 대표 레코드와 active watch에 함께 남겨, 연속 패턴과 guard 1회성 동작을 로그 기준으로 바로 추적 가능하게 정리.
- v95 (2026-03-27): 상승 종목 포착 회복용 다중 추세 필터 정상화 + 같은 watch의 guard 반복 외부알림 1회성화.
  [#1] `_get_multi_tf_downtrend_context()` / `_should_block_multi_tf_downtrend_capture()` 정상화.
       기존: 일봉/주봉이 둘 다 상승 추세가 아닐 때 거의 전부 `하향/비상승 추세`로 차단해, 강한 장중 상승 후보도 앞단에서 대량 탈락할 수 있었음.
       수정: 명확한 일봉·주봉 동반 하락 추세 또는 강한 단독 하락일 때만 차단하도록 되돌려, `v94`의 과차단을 완화.
  [#2] `_should_relax_general_a_threshold()` 보강.
       기존: `SURGE`/`NEAR_UPPER`가 강한 가격·거래량·상대강도 근거를 보여도 A 완화 게이트 진입이 제한적이어서, 실전형 상승 종목이 B에서 멈출 수 있었음.
       수정: 장중 강세 근거(거래량 이상 급증/상대강도/재상승/장중돌파 등)가 확인되면 일반 포착의 A 완화 자격을 더 현실적으로 부여.
  [#3] `_notify_entry_guard_followup()` 1회성 외부알림 가드 추가.
       기존: 같은 watch가 며칠 살아 있는 동안 `거래량 급감` 같은 guard 사유가 30분~60분 간격으로 반복 외부발송될 수 있었음.
       수정: 같은 watch의 guard 외부알림은 최초 1회만 보내고, 이후는 내부 기록만 유지하도록 변경.
- v94 (2026-03-27): DART 실행형 과관대 축소 + 다중 추세 필터 보수화.
  [#1] `_should_register_dart_execution_watch()` 추가.
       기존: `유상증자` 같은 DART_EVENT도 공시 제목+초반 상승만 맞으면 `register_entry_watch()`까지 열려,
       `기타업종`·체결 샘플 부족·하향/비상승 추세 종목이 실행형 진입감시로 오판될 수 있었음.
       수정: `DART_EVENT`/`DART_BUYBACK_CANCEL` 진입감시 등록 전 별도 게이트를 두어,
       (a) 주봉·일봉 동시 상승 추세 미충족,
       (b) `유상증자` + `기타업종`/체결 샘플 부족,
       (c) 체결속도 샘플 부족 + 테마 미확인 조합이면 실행형 진입감시를 차단.
  [#2] `_get_multi_tf_downtrend_context()` / `_should_block_multi_tf_downtrend_capture()` 보수화.
       기존: 일봉 2개 + 주봉 2개 이상일 때만 `하락 추세`로 막아, 사용자가 보기엔 하향/비상승 종목도 포착을 통과할 수 있었음.
       수정: 일봉/주봉이 **둘 다 상승 추세**일 때만 통과시키고, 둘 중 하나라도 상승 추세가 아니면 `하향 추세`로 간주해 차단하도록 강화.
  [#3] `run_dart_intraday()` DART 실행형 등록 전에 위 게이트 연결.
       기존: 정보성 DART 알림과 실행형 진입감시 등록이 사실상 같은 기준으로 열려, 피노류 종목이 진입가 감시까지 갈 수 있었음.
       수정: 정보성 공시 알림은 유지하되, 실행형 `entry_watch` 등록만 별도 보수 기준으로 제한.
- v93 (2026-03-27): 정규장 초반 일반 포착 보정 — 09:00~10:00 일반 포착 거래량 기준을 강한 상승 종목에 한해 현실화.
  [#1] `_relax_opening_general_required_volume()` 추가.
       기존: 정규장 초반(09:00~10:00) `get_effective_volume_ratio()`가 `SURGE` 9.1배, `NEAR_UPPER` 6.5배처럼 과하게 높아 실제 상승 종목도 일반 포착 단계에서 탈락할 수 있었음.
       수정: 정규장 초반 `SURGE`/`NEAR_UPPER`/`UPPER_LIMIT` 일반 포착은 상승률 강도에 따라 요구 거래량 배수를 보수적으로 완화해, 실제 강세 종목이 일반 포착 단계까지는 올라올 수 있게 조정.
  [#2] `analyze()`에 opening-volume relax 연결 및 로그 사유 추가.
       기존: 일반 포착 부족이 `눌림목/A전용 외부억제` 이전 단계의 거래량 게이트에서 이미 발생해도 원인 확인이 어려웠음.
       수정: 완화가 적용되면 사유를 남겨 오늘 같은 실제 상승 종목 미포착 원인을 재점검하기 쉽게 정리.
- v92 (2026-03-27): 거래정지 오판 축소 — DART halt 영속 저장을 엄격화하고 실시간 정상 거래 시 자동 해제.
  [#1] `_is_trade_resume_title()`, `_is_trade_halt_title()`, `_should_persist_trade_halt_title()` 추가.
       기존: 제목에 `거래정지`/`매매정지`만 들어가면 `기간변경`, `정지및정지해제`, 과거 이력도 halt 리스크/영속 상태로 오인될 수 있었음.
       수정: 직접 거래정지 제목만 halt로 인정하고, `정지해제/재개`, `기간변경`, `정지및정지해제` 같은 복합·정보성 제목은 영속 halt 저장 대상에서 제외.
  [#2] `_has_explicit_halt_market_flag()`, `_is_live_trading_normal()`, `_maybe_clear_false_trading_halt()` 추가.
       기존: DART 기반 영속 halt가 살아 있으면 정상 거래 중 종목도 `[포착 취소 — 거래정지]`로 오발송될 수 있었음.
       수정: 장중 현재가/호가/거래량이 정상이고 KIS 정지 플래그가 없으면 DART 기반 영속 halt를 자동 해제하고 관련 캐시도 함께 정리.
  [#3] `check_dart_risk()`, `_is_trading_halt()`, `run_dart_intraday()`에 위 엄격화 로직 연결.
       기존: 과거/복합 거래정지 제목도 `is_risk=True`와 영속 halt 저장으로 이어질 수 있었음.
       수정: same-day 직접 거래정지 제목만 리스크/영속 halt로 인정하고, 장중 실시간 정상 거래가 확인되면 DART halt보다 실제 거래 상태를 우선.
  이유: 에코플라스틱·태림포장처럼 정상 거래 중인 종목이 DART 제목 매칭만으로 거래정지 오판돼 포착 취소되던 문제 제거가 우선이었기 때문.
  개선점: 정상 거래 종목 거래정지 오발송↓, stale/복합 DART 제목 오판↓, 실제 KIS 정지 플래그 우선도↑.
  주의점: 실제 거래정지 종목은 KIS 플래그나 same-day 직접 거래정지 공시가 잡히면 계속 차단된다.
- v91 (2026-03-26): entry_hit 후속알림 통합 억제 — phase2/보류/취소를 종목 단위 공통 쿨다운으로 묶음.
  [#1] `ENTRY_FOLLOWUP_ALERT_COOLDOWN_SEC`, `_is_entry_followup_actionable_transition()`,
       `_should_send_entry_followup_alert()`, `_mark_entry_followup_alert_sent()` 추가.
       같은 `entry_hit` watch에서 `[2차 진입 판단]`과 `[진입 보류/취소 사유]`를 각각 따로 보지 않고,
       종목 단위 후속행동 알림으로 묶어 최근 60분 내 재발송을 보수적으로 차단.
  [#2] `_notify_entry_guard_followup()`에 위 통합 쿨다운을 연결.
       같은 이유뿐 아니라 다른 보류 사유라도 최근 후속알림이 있었다면 외부 발송을 생략하고 내부 모니터링만 유지.
  [#3] `_dispatch_general_alert_signal()`의 phase2 강화판단에도 위 통합 쿨다운을 연결.
       단, 최근 보류/금지 알림 뒤에 `가능`으로 바뀌는 경우는 행동 전환이므로 예외적으로 즉시 발송 허용.
  이유: 한올바이오파마처럼 `진입 보류/취소`와 `[2차 진입 판단]`이 서로 교차하며 짧은 시간 반복돼,
       v90의 동일사유/동일판단 억제만으로는 사용자 체감 개선이 거의 없던 문제 보완.
  개선점: 동일 종목 후속알림 묶음↓, phase2↔보류 교차 반복↓, 행동 가능한 상태 전환(`가능`)만 선별 노출↑.
  주의점: 거래정지 같은 별도 고위험 경보는 이번 통합 억제 대상이 아니며, 이번 수정은 entry_hit 이후 후속알림 정리에 한정.
- v90 (2026-03-26): entry_hit 이후 반복 알림 억제 — 눌림목 재알림 차단 + phase2/보류 중복발송 축소.
  [#1] `ENTRY_GUARD_SAME_REASON_COOLDOWN_SEC`, `PHASE2_UPGRADE_ALERT_COOLDOWN_SEC`,
       `_find_existing_entry_hit_watch()`, `_should_send_phase2_upgrade_alert()`, `_mark_phase2_upgrade_alert_sent()` 추가.
       같은 entry_hit watch에서 동일 사유의 `진입 보류/취소` 알림은 30분 쿨다운으로 재발송을 억제하고,
       동일 강화 신호타입+동일 판단결과의 `[2차 진입 판단]`은 30분 내 중복 발송하지 않도록 제한.
  [#2] `run_mid_pullback_scan()`의 외부 발송 직전에 기존 `entry_hit/entry_hit_locked` watch 존재 여부를 재확인하도록 보강.
       이미 1차 진입가 도달 후 모니터링 중인 종목은 반복 `[눌림목 진입 신호]`를 생략하고 내부 기록만 유지.
  [#3] `_dispatch_general_alert_signal()`의 신호 강화 phase2 트리거에 중복 억제 상태 저장을 연결.
       `MID_PULLBACK→SURGE/STRONG_BUY` 같은 강화가 연속 감지돼도 같은 판단(가능/보류/금지)이면 짧은 시간 재발송을 막음.
  이유: 한올바이오파마처럼 같은 종목이 `진입 보류/취소` → `눌림목 진입 신호` → `[2차 진입 판단]` → `진입 보류/취소`로
       짧은 간격 반복 발송돼 행동 가능한 알림 품질을 해치던 문제 축소.
  개선점: 동일 종목 반복 알림↓, entry_hit 이후 상태 전이 메시지 정합성↑, 사용자 알림 보수성↑.
  주의점: 다른 사유로 상태가 실제 변경되면 알림은 계속 가능. 이번 수정은 동일 사유·동일 판단 반복 억제에 한정.
- v89 (2026-03-26): 거래정지 공시 외부알림 범위 축소 — 실진입 종목만 발송.
  [#1] `_should_send_tracking_dart_alert()` 신규 추가.
       추적중 종목의 DART 위험공시 외부알림은 `actual_entry=True`인 실제 진입 종목에만 허용.
       미진입/미확정 종목은 내부 추적·기록만 유지하고 텔레그램 발송은 억제.
  [#2] `update_signal_results()`의 보유 종목 뉴스/공시 실시간 감시 경로에서 거래정지/악재 공시 발송 조건 축소.
       기존: `추적중` 레코드면 실진입 여부와 무관하게 `[거래정지 공시 감지]` / `[거래정지 — 호재성 공시 사유]` / `[보유 종목 악재 공시 감지]` 발송 가능.
       수정: 실제 진입(`actual_entry=True`) 레코드에만 외부 발송, 그 외는 `내부기록만` 로그로 남김.
  이유: 거래정지 공시는 정보성일 수 있어도 재개 전 매매 불가이며, 미진입 종목에 대한 외부알림은 행동 불가능 알림이 되기 쉬움.
  개선점: 거래정지 정보성 과알림↓, 실제 행동 가능한 포지션 리스크 알림 집중도↑.
  주의점: DART 위험공시 탐지/내부기록 자체는 유지. 이번 수정은 외부 발송 범위 축소에 한정.
- v88 (2026-03-26): 거래정지 영속 차단 추가 — 재시작 후 재포착 방지.
  [#1] `TRADING_HALT_STATE_FILE`, `_load_trading_halt_state()`, `_save_trading_halt_state()`,
       `_mark_trading_halt_state()`, `_clear_trading_halt_state()` 신규 추가.
       거래정지 종목을 JSON 상태로 저장/복원해 프로세스 재시작 후에도 차단 상태를 유지.
  [#2] `_is_trading_halt()`가 영속 halt 상태를 우선 확인하도록 보강.
       KIS 플래그 또는 DART 거래정지 캐시 적중 시 영속 상태도 함께 갱신.
  [#3] `check_dart_risk()` / `run_dart_intraday()`에 거래정지/거래재개 상태 동기화 추가.
       거래정지 공시를 보면 halt state 저장, 거래재개/매매재개 공시를 보면 즉시 해제.
  [#4] 봇 시작 시 `_load_trading_halt_state()`를 먼저 복원하도록 시작 순서 보강.
       이전 런타임에서 이미 `[포착 취소 — 거래정지]` 처리된 종목이 재시작 직후 다시 포착되지 않게 함.
  이유: 스피어처럼 거래정지 취소 이력이 있는 종목이 v87 재시작 후 DART/KIS 캐시 공백 구간에서 다시 포착·진입감시 등록되는 문제 차단.
  개선점: 재시작 후 거래정지 재포착↓, 포착→몇 분 뒤 거래정지 취소 재발↓, 행동 가능한 알림 품질↑.
  주의점: 거래재개 해제는 DART `거래재개/매매재개/거래정지해제/매매정지해제` 공시 확인 시에만 자동 해제.
- v87 (2026-03-26): 거래정지 취소 메시지 정합화 — 포착시각/NXT가격/재개문구/사유표시 수정.
  [#1] `_get_trading_halt_reason_label()` 신규 함수 추가.
       DART 거래정지 캐시/재조회 결과의 실제 공시 제목을 우선 사용하고, 없으면 `주권매매거래정지`로 fallback.
  [#2] `_notify_trading_halt_cancel()` 메시지 정리.
       기존: `감지`에 발송시각(now) 표기, NXT 라벨만 있고 실제 NXT 가격 미표시,
            `재상장 시 재포착 대기`, 사유 고정 문자열 출력.
       수정: `원신호 | 포착`에는 watch의 원포착 시각 표시, `거래정지 확인` 시각 분리,
            NXT 기준이면 실제 NXT 현재가 표시, `거래재개 시 재포착 대기`로 문구 수정,
            사유는 DART 실제 제목 우선 노출.
  [#3] `check_entry_watch()`의 거래정지 취소 알림 호출부가 현재 가격 dict(`cur`)를 함께 전달하도록 보강.
  이유: `[포착 취소 — 거래정지]` 메시지에서 시각 의미가 틀리고, NXT 기준 가격 숫자가 빠지며,
       `재상장` 문구와 고정 사유가 실제 사용자 해석을 흐리던 문제 수정.
  개선점: 거래정지 취소 메시지 해석력↑, NXT 기준 가격 행동 판단력↑, 공시 사유 가독성↑.
  주의점: 거래정지 판정 로직 자체는 변경 없음. 이번 수정은 사용자 메시지 정합화에 한정.
- v86 (2026-03-26): UPPER_LIMIT 신호 no_ask_liquidity soft allow 추가.
  [#1] `_should_soft_allow_no_ask_liquidity_general()`의 신호타입 허용 목록에 `UPPER_LIMIT` 추가.
       기존: SURGE/STRONG_BUY/EARLY_DETECT/NEAR_UPPER만 soft allow 검토 → UPPER_LIMIT 전량 차단.
       수정: UPPER_LIMIT + vol_ratio≥5.0 + change_rate≥15% 조건 충족 시 soft allow 통과.
  이유: 대영포장처럼 이슈+거래량 폭발로 상한가 간 종목이 신호타입만으로 알림 없이 차단됨.
  개선점: 거래량 폭발 UPPER_LIMIT 알림↑, 단순 상한가 고착 차단 유지.
  진입 체인: analyze() → _dispatch_general_alert_signal() 연결 확인 (변경 없음).
  주의점: UPPER_LIMIT soft allow는 vol_ratio≥5.0 + change_rate≥15% 조건 충족 시만 통과.
- v85 (2026-03-26): 코스닥 상승률 외부소스 추가 — KIS API 404 시 코스닥 누락 방지.
  [#1] `_fetch_naver_rank()`에 코스닥 URL 추가.
       기존: `sise_rise.naver` (코스피만) → 수정: 코스피 + `sise_rise_kosdaq.naver` (코스닥) 순차 시도 후 합산.
  [#2] `_fetch_daum_rank()`에 코스닥 API 추가.
       기존: KOSPI만 → 수정: KOSPI + KOSDAQ 순차 호출 후 합산.
  이유: KIS chgrate-pcls-100 API가 404로 막힐 때 fallback이 코스피만 스캔해
       오늘 에코프로(+23%), 레인보우로보틱스(+27%) 등 코스닥 급등주를 전량 누락.
  개선점: KIS API 불통 시 코스닥 급등주 포착률↑.
  진입 체인: analyze() → _dispatch_general_alert_signal() 연결 확인 (변경 없음).
  주의점: 네이버/다음 스크래핑 실패 시 기존 universe fallback으로 자동 복귀.
- v84 (2026-03-26): 레짐별 진입가 감시 만료 기간 차등 적용 + 상방이탈 즉시만료.
  [#1] `_get_expire_days_by_regime()` 신규 함수 추가.
       레짐(bull/normal/bear/crash) + 신호유형(SURGE/기타)별로 만료 일수를 다르게 설정.
       bull: SURGE 1일 / PULLBACK 2일, normal: SURGE 2일 / PULLBACK 3일,
       bear: SURGE 3일 / PULLBACK 4일, crash: SURGE 1일 / PULLBACK 2일.
  [#2] `register_entry_watch()`에서 `expire_ts` 계산 시 `_get_expire_days_by_regime()` 호출.
       기존 `MAX_CARRY_DAYS` 고정값 대신 레짐+신호유형 기반 동적 만료 일수 적용.
  [#3] `register_entry_watch()`에서 진입가 대비 현재가 상방이탈(bull +6% / normal +8% / bear +10% / crash +5%) 시 즉시만료.
       이미 기회가 지난 신호를 감시 목록에서 빠르게 제거해 유효 신호 집중도↑.
  이유: 레짐과 무관하게 3일 고정 만료로 인해 죽은 신호가 감시 목록에 누적되던 문제.
  개선점: 감시 목록 유효 신호 집중도↑, bull장 오래된 신호 빠른 정리↑, 진입가 도달률↑.
  진입 체인: analyze() → _dispatch_general_alert_signal() 연결 확인 (변경 없음).
  주의점: MAX_CARRY_DAYS 상수는 유지 (다른 carry 로직에서 참조 중). entry_hit 종목은 만료 대상 아님.
- v83 (2026-03-26): 외부 소스 다변화 + 장중 워치독 자가진단.
  [#1] `_fetch_naver_rank()` / `_fetch_daum_rank()` / `_fetch_external_rank_top()` 신설.
       KIS API 불통 시 네이버→다음→유니버스 순으로 자동 전환.
       `_rank_api_fallback()`에 외부 소스 합산 연결.
  [#2] `run_intraday_watchdog()` 신설 — 15분마다 실행.
       ① 외부 소스 상승 종목 5개↑ + ② 30분 침묵 → 차단 사유 자동 집계.
       주 차단 사유별 파라미터 완화 + 30분 후 자동 복원.
       코드 구조 문제(candidate_miss, grade_suppressed) 감지 시 수정 권고 텔레그램 발송.
  [#3] `send_alert()`에 `_last_external_alert_ts` 갱신 추가 (워치독 침묵 판정용).
  이유: KIS API fallback만 의존하는 단일 소스 구조 + 장중 침묵을 감지·대응하는 로직 부재.
  개선점: 데이터 소스 다변화↑, 장중 차단 자가진단↑, 코드 구조 문제 조기 발견↑.
  주의점: 워치독 완화는 임시방편. grade_suppressed/candidate_miss는 코드 수정이 근본 해결.
- v82 (2026-03-26): 동시보유 제한 완전 제거.
  [#1] `_apply_position_limit_after_priority()` → 항상 전체 통과 (3줄로 대체).
       기존: v62~v80까지 9회 수정에도 stale entry_hit 오카운트 반복 → A급 포착 전량 차단.
       수정: 함수 내부 차단 로직 전체 제거, sorted_alerts 즉시 반환.
  이유: 실진입은 사용자 수동 결정이므로 봇 단계 차단 불필요. 로직 복잡도 대비 효과 0.
  개선점: 동시보유 오카운트로 인한 포착 차단 완전 해소. 섹터 중복 제거·max_total 제한은 유지.
  주의점: filter_portfolio_signals()의 섹터 dedup·max_total 제한은 그대로 동작.
- v81 (2026-03-26): 진입 체인 미연결 2개 수정 — 뉴스 테마 + 지정학 prewatch.
  [#1] `send_news_theme_alert()` 수정 — rising 종목 A급 진입 체인 연결.
       기존: send(msg) 발송 후 종료 → 알테오젠 +10.9% 감지해도 진입 체인 없음.
       수정: rising 종목 각각 analyze() → grade==A + entry_price>0 이면
             _dispatch_general_alert_signal() 호출 → 진입가 알람 발송.
             A급 미달은 내부 기록만 (수칙 #14/#16).
       진입 체인: analyze() → _dispatch_general_alert_signal() 연결 확인.
  [#2] `run_geo_news_scan()` 수정 — prewatch 등록 후 check_issue_prewatch() 연결.
       기존: _news_issue_prewatch 등록만 하고 check_issue_prewatch() 미호출
             → prewatch 종목이 주가 반응해도 감지 불가.
       수정: geo prewatch 등록 직후 check_issue_prewatch() 즉시 1회 호출
             → 이미 반응 중인 섹터 종목 즉시 A급 판정 가능.
       진입 체인: check_issue_prewatch() → analyze() → _dispatch_general_alert_signal() 연결 확인.
  이유: 뉴스+주가 연동 "매우강함" 알람 발송돼도 진입 알람 없는 구조 발견.
       geo prewatch 등록만 하고 체크 루프 미연결 구조 발견.
  개선점: 뉴스 테마 상승 종목 A급이면 즉시 진입 알람 연결.
  주의점: rising 종목이 A급 미달이면 기존과 동일하게 정보 알람만. max_positions=1 유지.
- v80 (2026-03-26): 동시보유 오카운트 완전 수정 + 최대낙폭 표시 버그 수정 + 거래정지 오판 수정.
  [#1] 시작 시 stale entry_hit 정리 순서 수정.
       기존 v79: load_carry_stocks() 안에서 _purge_stale_entry_watch_hits() 호출
                → 이후 _load_entry_watch_active()가 파일에서 entry_watch 재적재
                → stale이 다시 메모리에 올라와 purge 효과 없음.
       수정: _load_entry_watch_active() 호출 직후에 _purge_stale_entry_watch_hits() 이동.
       load_carry_stocks()의 호출도 제거 (중복 방지).
  [#2] 최대낙폭 표시 버그 수정.
       기존: mdd = (min_p - entry) / entry * 100 → min_p > entry이면 양수 출력 → "최대낙폭: +7.5%" 혼란.
       수정: mdd > 0이면 "낙폭 없음 🟢 (진입 후 우상향)"으로 표시. 음수일 때만 숫자 표시.
  [#3] 거래정지 오판 수정 — 과거 공시 날짜 기반 거래정지 영구 판정 해소.
       기존: check_dart_risk() 5일 내 거래정지 공시 존재 → ts=0 → 영구 거래정지 판정.
       수정 A: 공시 접수일(rcept_dt)이 오늘이면 ts=0 유지, 과거 날짜면 ts=now (10분 재조회).
       수정 B: "거래재개"/"매매재개" 키워드 감지 시 is_risk=False override.
  이유: v79 배포 후에도 동시보유 5/1 오카운트 지속 (순서 버그).
       최대낙폭 +7.5% 혼란 표시. 광전자/신라젠 거래정지 오판 알람.
  개선점: 재시작 직후 stale 완전 제거 → NXT/KRX 포착 즉시 정상화.
  주의점: #1은 시작 순서만 변경. 실제 정리 로직(_purge_stale_entry_watch_hits) 자체는 그대로.
- v79 (2026-03-26): 동시보유 오카운트 영구 수정 — 재시작 직후 stale entry_hit 차단.
  [#1] `load_carry_stocks()` 수정 — 시작 시 `_purge_stale_entry_watch_hits()` 즉시 호출.
       기존: 30분 스케줄에만 연결 → 재시작 직후 스캔 시 stale entry_hit 5개가
             "보유 중"으로 오카운트 → 전체 NXT 후보 차단.
       수정: purge_orphan_tracking() 직후 _purge_stale_entry_watch_hits() 추가 호출.
  [#2] `_is_actionable_entry_watch()` 수정 — detect_date 날짜 검증 추가.
       entry_hit=True 이지만 detect_date가 오늘 이전이고 signal_log에 매칭 rec 없으면
       stale로 판단 → actionable 제외.
       기존: latest_rec=None 이면 entry_hit만 보고 무조건 actionable 처리.
       수정: latest_rec=None + detect_date 어제 이전 → False 반환.
  이유: 로그상 "동시보유 제한: 5/1종목 보유 중" 반복으로 NXT 오전 상승 종목 전량 차단.
       _purge_stale_entry_watch_hits()가 30분 스케줄에만 있어 재시작 직후 미동작.
  개선점: 재시작 직후 즉시 stale 정리 → NXT 포착 차단 해소.
  주의점: 실제 entry_hit 된 당일 종목은 영향 없음. 과거 날짜 stale만 제거.
  진입 체인: analyze() → _dispatch_general_alert_signal() 연결 확인 (변경 없음).
- v78 (2026-03-26): 이슈 기능 6종 개선 — 이슈 선감지→주가반응 알람 체인 신설.
  [#1] `_news_issue_prewatch` 전역 딕트 신설.
       이슈 뉴스 감지 후 주가 미반응 종목을 스킵하지 않고 prewatch 등록.
       TTL: 14400초(4시간), 쿨다운 후 자동 소멸.
  [#2] `analyze_news_theme()` 수정 — 스킵 → prewatch 등록으로 변경.
       기존: rising_stocks 없으면 완전 스킵.
       수정: rising_stocks 없으면 not_yet 종목을 _news_issue_prewatch에 보관.
  [#3] `check_issue_prewatch()` 신설.
       prewatch 종목 주가 1.5%↑ AND 거래량 1.5x 이상 시:
       ① analyze() 호출 → grade==A + entry_price>0 이면 _dispatch_general_alert_signal() 진입 체인 연결 (진입가 알람 발송).
       ② A급 미달 이면 [이슈 선감지] 정보 알람만 발송 (진입 불가).
       발송 후 해당 theme prewatch 소멸, _news_prewatch_fired로 중복 차단.
  [#4] `run_news_scan()` 수정 — check_issue_prewatch() 연결.
  [#5] `run_geo_news_scan()` 수정 — geo 이슈 감지 시 영향 섹터 종목 prewatch 등록.
  [#6] `analyze_geopolitical_event()` fallback 캐시 TTL 7200초(2배)로 연장.
       기존: 빈 응답 시 캐시 저장은 하지만 TTL이 정상과 동일 → 반복 API 호출.
       수정: fallback 결과 캐시 TTL 키에 "fb_" 프리픽스 + ts 갱신으로 재호출 억제.
  [#7] `run_dart_intraday()` 자사주소각 판단 고도화.
       기존: _is_buyback_cancel 시 0.5% 기준만으로 알람.
       수정: analyze_news_deep 결과 score_adj < -3이면 내부 기록만 (알람 발송 차단).
       이유: "적당한 자사주소각"이 주가에 실질 영향 없는 경우 과알림 방지.
  이유: 이슈 뉴스 감지 후 주가 미반응 → 완전 스킵(1,287회) 문제 해소.
       이슈 선발견 후 주가 변동 시 즉시 알람 체인 완성.
  개선점: 이슈 조기 포착↑, 지정학 API 반복 fallback 로그↓, 자사주 과알림↓.
  주의점: prewatch 알람은 신호 등급 없이 [이슈 선감지] 단독 발송. max_positions=1 유지.
- v77 (2026-03-25): v76 거래정지 판별 버그 수정 + 공시 사유 구분.
  [#1] `_is_trading_halt()` ts=0 자기모순 버그 수정.
       기존: check_dart_risk에서 거래정지 확정 시 ts=0 설정 → _is_trading_halt에서 ts>=today_start 체크 → 0>=오늘00시=False → 판별 무효.
       수정: ts=0이면 거래정지 확정 마커로 보고 무조건 True 처리. ts>0이면 당일 조회분만 인정.
  [#2] 보유종목 공시 알림 사유 구분.
       기존: 거래정지 사유가 계약/수주 등 호재성이어도 [악재 공시] + "즉시 매도 검토 권장" 발송.
       수정: 호재성 사유(계약/수주/공급 등) → [거래정지 — 호재성 공시 사유] + "재개 후 진입 판단".
             순수 거래정지 → [거래정지 공시 감지] + "재개일 확인 필요".
             횡령/파산 등 악재 → [보유 종목 악재 공시 감지] + "즉시 매도 검토 권장".
  이유: v76 배포 후 ts=0 버그로 거래정지 차단이 여전히 무효였고, 단일판매공급계약 공시가 악재로 표시됨.
  개선점: 거래정지 즉시 차단 실제 동작, 사용자 행동 지침 정확도↑.
- v76 (2026-03-25): 거래정지 종목 즉시 차단 — entry_watch 만료 + 포착 억제.
  [#1] `get_nxt_stock_price()`에 vi_cls_code/raw_status_code 거래정지 플래그 필드 추가.
  [#2] `_is_trading_halt()` 헬퍼 신설 — KIS API 플래그 + DART 캐시 거래정지 키워드 통합 판별.
       호가 소멸 기반 판별은 장마감 후 오판 유발로 제거.
  [#3] `_notify_trading_halt_cancel()` 신설 — [포착 취소 — 거래정지] 알림 1회 발송.
  [#4] `check_entry_watch()` KRX/NXT 분기 직후 거래정지 판별 → 즉시 만료 + 취소 알림.
  [#5] `_dispatch_general_alert_signal()` send_alert 직전 거래정지 판별 → 포착 알림 억제.
  [#6] `check_dart_risk()` 거래정지/매매정지 키워드 히트 시 캐시 ts=0 (확정 마커).
  이유: 스피어(347700) 14:45 거래정지 후 반복 포착/알림 발송 — KIS API 마지막 가격 그대로 반환, DART 캐시 10분 TTL 문제.
  개선점: 거래정지 종목 포착 차단, entry_watch 즉시 만료, 취소 알림 1회 발송.
- v75 (2026-03-25): entry_hit 종목 재포착 시 신호 강도 방향 기반 분기 — 강화→phase2 트리거 / 약화→내부 기록.
  [#1] `_dispatch_general_alert_signal()`에 entry_hit=True watch 존재 시 분기 로직 추가.
       강화(눌림목→급등/상한가 등): [포착 알림] 차단 + [2차 진입 판단] 메시지 발송.
       약화(급등→눌림목 등): [포착 알림] 차단 + 내부 signal_log 기록만 유지.
       동일 신호 타입 재포착: 약화와 동일하게 처리 (기존 watch 보호).
  [#2] `register_entry_watch()`의 v74 신호 타입 변경 리셋 로직 제거 — v75 분기로 대체돼 불필요.
       `_notify_entry_guard_followup()` notify_count < 1 차단(v74 #2)은 유지.
  이유: 같은 종목에 서로 다른 신호가 겹칠 때 사용자에게 맥락 없는 [포착 알림]이 가거나,
        entry_hit 상태가 꼬여 [보류/취소 사유]가 오발송되던 근본 원인 해소.
  신호 강도 순위: MID_PULLBACK/ENTRY_POINT(1) < EARLY_DETECT(2) < SURGE(3) < NEAR_UPPER(4) < UPPER_LIMIT/STRONG_BUY(5).
  개선점: [포착]→[도달]→[보류/취소] 순서 보장, 강화 모멘텀 phase2 자동 연결, 약화 시 기존 포지션 보호.
  주의점: max_positions=1 유지. entry_hit 없는 첫 포착은 기존 흐름 그대로.
- v74 (2026-03-25): 미통지 상태 보류 알림 차단.
  [#1] `_notify_entry_guard_followup()`에 notify_count < 1 차단 가드 추가.
       진입가 도달 알림(notify_count≥1)을 한 번이라도 보낸 후에만 보류/취소 알림 발송.
  이유: 재시작으로 entry_hit가 복원된 상태에서 사용자가 도달 알림을 못 받았음에도 보류 알림이 먼저 오는 문제 해소.
  개선점: 맥락 없는 보류 알림 제거.
  주의점: v75 도입으로 근본 원인이 해소됐으나 안전망으로 유지.
  [#1] `register_entry_watch()`에서 기존 entry_hit=True watch의 신호 타입이 새 신호와 다를 때(예: MID_PULLBACK→SURGE) entry_hit를 리셋하고 새 신호 기준으로 watch를 갱신.
       기존: 신호 타입 무관하게 entry_hit=True면 무조건 갱신 생략 → 사용자는 새 [급등 감지] 알림을 받았지만 진입가 도달 알림 없이 곧바로 보류 알림 수신.
       수정: 신호 타입 변경 시 entry_hit/notify_count/entry_guard 관련 필드를 초기화해 새 신호 기준으로 도달 감시 재시작.
  [#2] `_notify_entry_guard_followup()`에 notify_count < 1 차단 가드 추가.
       기존: entry_hit=True면 notify_count=0이어도 보류 알림 발송 → 사용자 입장에서 맥락 없는 알림.
       수정: 진입가 도달 알림(notify_count≥1)을 한 번이라도 보낸 후에만 보류/취소 알림 발송.
  이유: 재시작·재포착으로 entry_hit가 복원·승계된 상태에서 사용자가 도달 알림을 못 받았음에도 보류 알림이 먼저 오는 문제 해소.
  개선점: [급등 감지]→[진입가 도달]→[보류/취소] 순서 보장, 맥락 없는 보류 알림 제거.
  주의점: 동일 신호 타입 재포착 시 entry_hit 유지 로직은 그대로임.
- v73 (2026-03-25): 일반 눌림목 진입 신호의 상단 가격 문구를 대표진입가 기준으로 정합화.
  [#1] `register_entry_watch()`가 대표 진입가 가드 적용 후 값을 원본 signal 스냅샷(`s["entry_price"]`)에도 되돌려 쓰도록 동기화.
       기존: watch에는 guard 후 대표진입가가 저장돼도, 직후 발송되는 `[눌림목 진입 신호]` 메시지는 포착 시점 snapshot 값을 그대로 써 상단 가격표시가 watch 기준과 어긋날 수 있었음.
       수정: register 직후 signal snapshot에도 동일 대표진입가를 반영해, 이후 메시지/보조 로직이 같은 가격 기준을 사용하도록 맞춤.
  [#2] `send_mid_pullback_alert()`가 `MID_PULLBACK`/`ENTRY_POINT` 일반 메시지 상단 보조가격 라벨을 `예상진입가`가 아니라 `대표진입가`로 override.
       기존: 현재가와 동일 가격이어도 `[눌림목 진입 신호]` 상단에 `예상진입가`가 찍혀, 이미 엔진이 확정한 대표 진입 기준을 사용자 입장에서 오해하기 쉬웠음.
       수정: 일반 눌림목 메시지는 상단에 `대표진입가`를 직접 표기하고, 통합 메시지의 `도달가` override와도 역할이 구분되게 정리.
  이유: 눌림목 계열은 포착 단계에서도 실제 감시/행동 기준이 대표진입가이므로, 상단 가격 라벨이 `예상`으로 보이면 메시지 해석이 흔들릴 수 있었음.
  개선점: 일반 눌림목 메시지 해석력↑, 포착/감시 기준 정합성↑, `현재가=예상진입가` 표시 혼선↓.
  주의점: 다른 신호 타입의 상단 `예상진입가` 표기는 유지되며, 이번 수정은 눌림목 계열 일반 메시지에만 한정됨.
- v72 (2026-03-25): 눌림목 포착+1차 진입 통합 메시지의 상단 가격 라벨을 예상진입가→도달가로 정합화.
  [#1] `_format_capture_secondary_price_line()`를 추가하고 `_build_capture_focus_price_line()`에 상단 보조가격 override 경로를 연결.
       기존: 포착 공통 블록을 재사용하는 구조라, 이미 `1차 진입가 도달`이 확정된 통합 메시지 상단에도 `예상진입가`가 그대로 노출됐음.
       수정: 메시지별 override가 있으면 동일 포맷으로 `도달가` 등 실제 의미에 맞는 라벨/가격을 표시하고, 없으면 기존 `예상진입가` 경로를 그대로 유지.
  [#2] `_build_integrated_pullback_phase1_message()`가 통합 메시지 상단에 `도달가`를 주입하도록 보강.
       기존: `[눌림목 포착 + 1차 진입가 도달]` 메시지에서 상단은 `예상진입가`, 하단은 `대표진입가/도달` 맥락이라 같은 메시지 안에서 표현 기준이 엇갈렸음.
       수정: 통합 메시지에서는 실제 `entry_hit_price`(없으면 해당 시점 현재가)를 사용해 `도달가`를 표기하고, 순수 포착 메시지의 `예상진입가` 표기는 유지.
  이유: 사용자는 이미 1차 도달이 확정된 통합 메시지에서 행동 기준이 아니라 실제 도달 가격을 바로 읽어야 하며, `예상진입가` 표기는 오해를 만들 수 있었음.
  개선점: 통합 메시지 가격 해석력↑, 포착/도달 문구 정합성↑, 동일 메시지 내 중복 혼선↓.
  주의점: 일반 포착 메시지의 `예상진입가`는 유지되며, 이번 수정은 통합 메시지 상단 라벨에만 한정됨.
- v71 (2026-03-25): 종목포착 핵심 3대 차단 해소 — 눌림목 A기준 확장 + 동시보유 오카운트 장중 정리 + NXT A급 호가차단 완화.
  [#1] `_apply_mid_pullback_execution_grade()`에 B등급 고점수 → A승격 조건 추가.
       기존: 98~129점 B등급도 `grade == "A"` 조건 불충족으로 외부알림 전량 차단.
       수정: `pattern_grade == "B"` + `pattern_score >= 95` + `total_count >= req_b` → `execution_grade = "A"` 승격.
       이유: 스킬 7조 — A등급이 왜 포착→발송 못 가는지로만 진단. 고점수 B는 A기준 확장으로 해소.
       개선점: 쏠리드 98점·DMS 98점·셀바스AI 129점 눌림목 외부알림 통과.
       주의점: 95점 미만 B등급은 기존 억제 유지.
  [#2] `_purge_stale_entry_watch_hits()` 추가 → `clean_expired_cache()`(30분 주기)에 연결.
       기존: 재시작 시에만 stale hit 정리 → 장중 유령 entry_hit 23~26개가 동시보유로 오카운트돼 신규 포착 전량 차단.
       수정: 30분마다 `_is_actionable_entry_watch()` 재검증해 stale hit 즉시 제거 + `_save_entry_watch_active()` 동기화.
       이유: 로그 전 구간 `동시보유 제한: 23/1~26/1`이 지속되며 신규 10~12개씩 억제.
       개선점: 장중 position_limit 오카운트 해소 → A급 포착 통과율↑.
       주의점: 실보유(`_is_actionable_entry_watch()` 통과)는 제거 대상 아님. 보유 제한 자체는 유지.
  [#4] `_send_entry_phase_alert()` 내 `_get_split_entry_rule` → `_get_entry_split_rule` 오타 수정 (핫픽스).
       기존: 함수명 단어 순서 오타로 B→A 승격 후 처음 진입가 도달 경로가 실행되면 NameError 크래시.
       수정: 올바른 기존 함수명 `_get_entry_split_rule`으로 교정.
       이유: v70부터 잠재된 버그였으나 v71 #1 수정으로 쏠리드가 A급 통과해 해당 경로 최초 실행됨.
       기존: NXT no_ask_liquidity 시 복합조건만 허용 → SURGE A급 85점도 호가 없으면 전량 차단.
       수정: NXT + A급 + score >= 85 + change_rate >= 5.0 → 호가 무관 soft allow 통과.
       이유: 고점수 A급 NXT 포착은 호가가 얇아도 관찰 우선 알림이 나가야 사용자 대응 가능.
       개선점: NXT A급 SURGE/STRONG_BUY의 no_ask_liquidity 차단↓.
       주의점: KRX 기존 조건 유지. NXT도 A급 85점↑ 미달 시 기존 로직.
- v70 (2026-03-25): 눌림목 대표진입가 선동기화 + 현재가<=대표진입가 통합 메시지 + 포착/행동 가격 기준 일치.
  [#1] `run_mid_pullback_scan()`의 순서를 `save_signal_log() → register_entry_watch() → 즉시 1차 통합판정 → 포착 발송`으로 재정렬하고,
       `_maybe_send_immediate_entry_hit_from_signal(..., merge_capture_phase1=True)`를 연결.
       기존: 눌림목 포착 메시지가 대표 진입가 가드 적용 전 `예상진입가`를 보여줘, 실제 watch 진입가/즉시 1차 판단 기준과 어긋날 수 있었음.
       수정: 눌림목은 저장/감시 등록으로 대표 진입가 가드를 먼저 공유한 뒤 메시지를 보내, 포착 메시지의 `예상진입가`와 실제 watch 진입가가 동일 기준으로 맞춰짐.
  [#2] `_build_integrated_pullback_phase1_message()`를 추가하고 `_send_entry_phase_alert()`가 `merge_capture_phase1=True`일 때 통합 메시지를 발송하도록 보강.
       기존: 포착 시점에 `현재가<=예상진입가`여도 `종목포착`과 `1차 진입가 도달`이 분리되어, 사용자 기준으론 같은 말을 두 번 하거나 오히려 개선이 안 된 것처럼 보였음.
       수정: 눌림목에서 현재가가 대표 진입가 이하이면 `눌림목 포착 + 1차 진입가 도달`을 하나의 메시지로 보내고, 그 안에 대표진입가/손절가/목표가/권장 진입비중을 함께 표기.
  [#3] 통합 메시지 미발동 시에도 `send_mid_pullback_alert()`는 guard 적용 후의 `entry_price`/`planned_entry_price`를 기준으로 메시지를 구성하도록 정렬.
       기존: 같은 종목이라도 포착 메시지의 예상진입가와 추후 1차 판단 기준이 달라 사용자 신뢰가 떨어질 수 있었음.
       수정: 눌림목 포착/감시/즉시 1차가 같은 대표 진입가 체계를 공유해 메시지 해석과 내부 행동 기준이 일치.
  이유: 사용자는 `좋은 종목 포착 → 진입가 알림 → 진입` 흐름을 기대하되, 포착 시점에 이미 대표 진입가 이하라면 하나의 행동 가능한 메시지에서 가격정보를 모두 보고 싶어 했음.
  개선점: 눌림목 메시지 정합성↑, `현재가=예상진입가` 혼선↓, 통합 행동 메시지 해석력↑.
  주의점: 비A급 외부알림 확대는 하지 않으며, 통합 메시지는 `MID_PULLBACK`/`ENTRY_POINT`의 현재가<=대표진입가 케이스에서만 발동함.
- v69 (2026-03-25): 눌림목 즉시 1차 진입 연동 + 도달 후 취소/보류 사유 사용자 통지 + entry_hit 모니터링 유지.
  [#1] `register_entry_watch()`가 watch key를 반환하고 `_maybe_send_immediate_entry_hit_from_signal()` / `_send_entry_phase_alert()`를 추가해,
       눌림목 포착 시 현재가가 대표 진입가 이하인 경우 포착 직후 같은 루프에서 1차 진입가 도달 알림까지 즉시 연동.
       기존: 눌림목 포착 메시지에 `현재가=예상진입가`가 찍혀도 `check_entry_watch()` 다음 루프까지는 별도 행동 알림이 없어 사용자 체감이 어긋났음.
       수정: MID_PULLBACK/ENTRY_POINT는 포착 직후 대표 진입가 도달 여부를 한 번 더 확인해, 차단 사유가 없으면 즉시 1차 행동 메시지를 발송.
  [#2] `_notify_entry_guard_followup()` / `_record_entry_guard_followup()`를 추가하고 `check_entry_watch()`에 post-hit guard 분기를 연결.
       기존: 1차 진입가 도달 후 신호강도 약화·거래량 폭락·섹터 약세·진입불가가 생겨도 사용자에겐 빠른 취소/보류 통지가 없었고, 일부 경로는 watch가 바로 만료될 수 있었음.
       수정: 이미 `entry_hit`된 종목에서 취소/보류 사유가 발생하면 `진입 보류/취소 사유` 메시지를 1회 빠르게 발송하고, 내부 모니터링은 계속 유지.
  [#3] `notify_count>=2` 이후에도 `entry_hit` watch는 알림횟수만료로 즉시 제거하지 않도록 조정.
       기존: 1차/2차 알림 뒤 재접근 시 watch가 조기 제거돼 후속 보류/취소나 장마감 리스크 추적이 끊길 수 있었음.
       수정: entry_hit/locked watch는 만료/상승이탈 전까지 active를 유지해 후속 내부 추적과 가이드가 이어지게 함.
  이유: 사용자는 `좋은 종목 포착 → 진입가 알림 → 진입` 흐름을 기대했고, 이미 1차 진입했을 가능성이 있으므로 이후 취소/보류 사유도 빠르게 알아야 했음.
  개선점: 눌림목 포착-행동 연결력↑, entry_hit 이후 취소/보류 가시성↑, 내부 모니터링 연속성↑.
  주의점: 비A급 외부알림 확대는 하지 않으며, 취소/보류 알림은 entry_hit 이후 동일 사유 중복 발송을 억제함.
- v68 (2026-03-25): 조건부 2종목 허용 + 포착 메시지 예상진입가(엔진 재사용) 표기.
  [#1] `_should_allow_conditional_second_position()` / `_extract_tracking_sector_theme()`를 추가하고
       `_apply_position_limit_after_priority()`에 조건부 extra slot 1개를 연결.
       기존: `max_positions=1`이라 실제 진입 완료 종목이 1개만 있어도 정규장 신규 A급 후보가 전부 동일하게 막혔음.
       수정: 정규장 KRX + 기존 실보유 1개 + 신규 후보 A등급/점수 85점↑ + 비동일섹터 + 예상진입가 존재일 때만
       1개 추가 허용(실질 2종목). NXT/비A/동일섹터/섹터미상은 그대로 차단.
  [#2] `_select_capture_expected_entry_price()` / `_format_capture_expected_entry_line()`를 추가하고
       `_build_capture_focus_price_line()`이 포착 메시지에 `예상진입가`를 함께 표기하도록 수정.
       기존: 포착 메시지는 현재가만 보여서 대기 진입 가격대를 바로 판단하기 어려웠음.
       수정: 단순 현재가 비율계산이 아니라 기존 엔진이 이미 산출한 `entry_price` / `planned_entry_price` /
       `execution_hint_entry_price`만 재사용해 `예상진입가`를 표시.
  이유: 사용자는 비A급 확대가 아니라 A급 행동 알림 품질을 원했고, 동시에 포착 단계에서도 엔진 기준 예상 진입대를 바로 확인하길 원했음.
  개선점: 정규장 A급 이원화 대응력↑, 동시보유 완전삭제 없이 기회손실↓, 포착 메시지 행동 해석력↑.
  주의점: 동시보유 제한 기본 철학은 유지되며, 조건부 2종목은 정규장 A급·비동일섹터일 때만 허용. `예상진입가`는 엔진 재사용값만 표기하고 단순 추정치는 만들지 않음.
- v67 (2026-03-25): active entry_hit 정합성 정리 + NXT 장전 EARLY_DETECT 허용 강화 + 종목명 복구 보강.
  [#1] `_load_entry_watch_active()` / `_collect_actionable_position_limit_codes()`에
       `_is_actionable_entry_watch()` 검증을 연결.
       기존: signal_log strict cleanup으로 `entry_hit`가 초기화돼도 `entry_watch_active.json`의 오래된
       `entry_hit`/`entry_hit_locked`가 그대로 복원되면 동시보유가 23~24개로 다시 부풀 수 있었음.
       수정: 최신 signal_log active 상태와 불일치하는 hit watch는 로드시 자동 제외/정리하고,
       position_limit 계산도 동일 검증을 공유해 stale hit가 실보유로 카운트되지 않게 함.
  [#2] `_should_delay_external_general_capture()`에 `_is_signal_nxt_premarket_hint()`를 추가.
       기존: EARLY_DETECT 외부알림 허용이 현재 시각 helper에만 의존해, 장전 NXT 재평가/재시작/시간대 흔들림 시
       08시대 A급 신호도 `외부알림 지연`으로 남을 수 있었음.
       수정: NXT market + detect_time/detected_at이 08시대인 신호도 장전 힌트로 인정해
       70점↑ A/B급 EARLY_DETECT는 즉시 외부알림 허용.
  [#3] `_resolve_stock_name()` / `_build_capture_focus_message()` / `check_entry_watch()` name 복구 강화.
       기존: `010170`처럼 코드만 name_hint로 들어오면 이를 유효 종목명으로 오인해 `010170  010170` 메시지가 발생.
       수정: 코드형/숫자형 placeholder name은 무효 처리하고, KRX/NXT 현재가·runtime watch·signal_log 순으로 재복구.
       진입가 감시 루프와 메시지 빌더에서도 발송 직전 종목명을 다시 정규화.
  이유: 3/25 실로그 기준 핵심 병목은 (1) position_limit stale hit 재오카운트, (2) NXT 장전 A급 EARLY_DETECT
       외부알림 누락, (3) 종목명 placeholder 노출이었음.
  개선점: 동시보유 23/1 재발↓, 오전 NXT A급 포착 외부알림 복구↑, `010170` 코드노출 메시지↓.
  주의점: 동시보유 제한 자체는 유지(max_positions=1). 비A급 외부알림 확대는 하지 않음.
- v66 (2026-03-25): 동시보유 오카운트 근본 수정 + EARLY_DETECT 외부알림 조건부 허용 + NXT 장전 최적화.
  [#1] `_get_carry_position_context()` fallback 경로 근본 차단.
       기존: `_collect_actionable_position_limit_codes()`가 빈 set(= 보유 0건)을 반환하면
       Python의 falsy 판정으로 `_detected_stocks` fallback에 진입 → stale 23~24개가 보유로 오카운트.
       수정: 빈 set도 즉시 반환(= 보유 0건). fallback은 actionable 수집 자체 예외 시에만 동작하며
       그마저도 entry_hit 확인 후에만 카운트.
  [#2] `_should_delay_external_general_capture()` EARLY_DETECT 외부알림 조건부 허용.
       기존: EARLY_DETECT면 무조건 외부알림 지연 → NXT 08:00~08:59 포착 전량 miss.
       수정: NXT 장전 + 70점↑ + A/B등급 → 즉시 알림. KRX에서도 80점↑ A등급 + 진입가 확정 → 허용.
  [#3] `get_effective_volume_ratio()` NXT 장전(08시) / 장후 초반(15시) 시간대 보정 추가.
       NXT 장전은 유동성이 적어 거래량 배수가 과대 산출되므로 time_adj=0.7로 기준 완화.
       SURGE 기준: 7.0 × 0.7 = 4.9배 (기존 6.3배에서 하향).
  [#4] `is_strict_time()` NXT 장전 08:00~08:10 엄격 해제.
       NXT 장전은 선포착 기회 시간이므로 min_score_strict(66) 대신 min_score_normal(56) 적용.
  [#5] `_is_nxt_premarket_window()` 헬퍼 함수 신설 (08:00~08:59, NXT open + KRX closed).
  [#6] `analyze()` → `check_liquidity()` 상한가(UPPER_LIMIT/NEAR_UPPER) 면제.
       상한가는 매도호가(ask_qty)=0이 정상인데, 기존 코드는 이를 유동성 없음으로 판정.
       정규장 우리로(상한가) 포착→즉시 차단(no_ask_liquidity)이 이 버그 때문이었음.
  [#7] `calc_surge_escape_pct()` 상승이탈 기준 상향: 최소5→8%, 최대15→25%.
       급등장에서 와이어블(+20.4%), SK이터닉스(+17.6%)가 너무 일찍 상승이탈 판정.
  [#8] `REGIME_PARAMS` pullback_ratio 전 레짐 완화 + `ENTRY_PULLBACK_RATIO` 0.4→0.3.
       bull 0.35→0.25, normal 0.40→0.30, bear 0.50→0.40, crash 0.55→0.50.
       진입가가 현재가에 더 가까워져 상승이탈 확률↓, 진입가 도달 확률↑.
  이유: 3/25 오전 NXT 로그 분석 결과 아이티엠반도체(+26.7%), 미래에셋생명(+17.8%) 등 강세주를
       전혀 포착하지 못한 핵심 원인이 (1) 동시보유 24/1 오카운트로 전면 차단, (2) EARLY_DETECT
       무조건 외부알림 지연, (3) NXT 장전 거래량 기준 과다의 3중 병목이었음.
  개선점: 동시보유 오카운트 0건 정상화↑, NXT 장전 A/B급 즉시 알림↑, 거래량 기준 현실화↑,
       상한가 유동성 오차단↓, 상승이탈 조기 판정↓, 진입가 도달 확률↑.
  주의점: 동시보유 제한 자체는 유지(max_positions=1). 실제 entry_hit 종목만 보유로 카운트.
       pullback_ratio 완화로 진입가가 현재가에 가까워지므로 손절 시 손실폭도 약간 커질 수 있음.
- v65 (2026-03-24): 동시보유 제한 actionable 기준 재정의 — entry_hit 기반 실보유만 카운트.
  [#1] `_collect_actionable_position_limit_codes()`를 재작성.
       기존: _entry_watch의 active/watching/pending 전체 + _detected_stocks 오늘/직전 → 23~24개 카운트.
       수정: entry_hit(진입가 도달 확정) 또는 confirmed(체결 확정)된 종목만 "보유"로 카운트.
       만료된 entry_watch(expire_ts 경과)는 즉시 제외.
       아직 진입가에 도달하지 않은 "대기 중" 감시는 보유가 아니므로 제외.
  [#2] carry_stocks.json 기반 fallback도 signal_log entry_hit 확인 후에만 카운트.
  이유: max_positions=1인데 stale entry_watch 23~24개가 "보유"로 오판되어
       모든 신규 포착이 position_limit에 걸려 진입가 도달 0건 발생.
       포착 13건(A등급) + 감시등록 12건은 정상인데 filter_portfolio_signals에서 전부 억제.
  개선점: 실제 보유(entry_hit) 기준 position_limit↑, 신규 리더 진입 기회↑, stale 오판↓.
  주의점: 진입가 대기 중인 종목은 보유로 카운트하지 않음.
       실투자 시 실제 체결된 종목만 제한에 반영되어야 하므로 이 방향이 올바름.
- v64 (2026-03-24): watch→reach 회복 + 근접 진입가 도달 자동완화 + v63 실반영 보정.
  [#1] `CAPTURE_FUNNEL_FILE` / `_record_capture_funnel_event()` / `_get_capture_funnel_summary()` / `_get_capture_watch_recovery_state()`를 실제 코드에 추가해,
       `saved -> watch -> reached` 전환율을 일자별로 집계하고 같은 날 `saved`/`watch`는 충분한데 `reached`가 0건이면 recovery 모드가 자동으로 켜지도록 수정.
  [#2] `_get_dynamic_entry_reach_slack_pct()`와 `check_entry_watch()`를 보강해,
       recovery 모드의 strong/A 후보는 진입가 상단 최대 1.2% 이내를 `근접 진입가 도달`로 인정하고 메시지에 `회복모드 근접도달 허용` 문구를 남기도록 수정.
  [#3] `_select_representative_entry_price()`를 보강해, recovery 모드에서는 고점추격방지 신호라도 `경과 1일` / `미도달 1회` / `괴리 6%` 이상이면 대표 진입가 상향 갱신을 조기 허용하도록 완화.
  [#4] `_should_keep_internal_watch_on_no_ask_liquidity()` / `_persist_blocked_capture_watch()`를 추가하고
       일반 포착/눌림목의 `no_ask_liquidity` 차단 경로에 연결해, 외부 체결 차단이어도 선행형/near-A 후보는 내부 `signal_log` / `entry_watch`를 유지하도록 실제 반영.
  이유: 최신 로그상 종목 포착과 `진입가 감시 등록`은 회복됐지만 `진입가 도달`이 0건이었고, v63 변경 이력에 적힌 일부 복구 경로가 실파일에는 실제 함수로 반영되지 않은 구간이 있었음.
  개선점: `watch→reach` 회복↑, strong/A 후보 근접도달 포착↑, 대표 진입가 갱신 지연↓, `no_ask_liquidity` 후보 내부감시 지속↑.
  주의점: A전용 외부알림 정책은 유지하며, recovery 모드 완화는 같은 날 `saved/watch`가 충분하고 `reached`가 무너진 경우에만 제한 발동한다.
- v63 (2026-03-24): saved→watch 전환 회복 + no_ask_liquidity 내부감시 유지 + actionable position_limit 실반영.
  [#1] `_collect_actionable_position_limit_codes()` / `_get_capture_watch_recovery_state()`를 추가해,
       `position_limit`가 `_detected_stocks` 전체가 아니라 `entry_watch` / `execution_setup_watch` / 최근 active signal_log 중심으로 계산되도록 수정하고,
       같은 날 `saved→watch` 전환율이 급락하면 자동 recovery 모드가 켜지도록 보강.
  [#2] `_persist_blocked_capture_watch()` / `_should_keep_internal_watch_on_no_ask_liquidity()` / `_promote_internal_capture_watch()`를 연결해,
       `no_ask_liquidity`나 A전용 외부억제로 외부 알림이 막혀도 선행형/near-A 후보는 내부 `signal_log` / `entry_watch` / `execution_setup_watch` 경로를 유지하도록 수정.
  [#3] `save_signal_log()` / `register_entry_watch()` / `check_entry_watch()`에 capture funnel 기록을 연결해
       저장→감시→도달 전환율을 자동 집계하고, watch 비율이 무너지면 shadow 로그와 함께 회복 모드가 발동되도록 추가.
  [#4] v62의 `analyze_mid_pullback()` `sector_info` / `sentiment` 초기화와 `sector_info` payload 반환을 그대로 유지해,
       saved→watch 복구 수정 과정에서 눌림목 `NameError` 복구가 다시 빠지는 회귀를 차단.
  이유: 최근 로그상 진입가 알림 0건의 핵심은 raw 포착 0건보다 `saved→watch` 전환 붕괴, `no_ask_liquidity` 조기차단,
       그리고 `position_limit`가 실제 행동 가능한 감시보다 넓게 계산돼 신규 후보를 먼저 죽이는 구조였음.
  개선점: saved→watch 전환율↑, no_ask_liquidity 후보 내부감시 유지↑, actionable 동시보유 제한 정확도↑, 눌림목 회귀 오류 방지↑.
  주의점: A전용 외부알림은 유지하며, 자동 recovery는 최근 저장 건수가 충분히 쌓였을 때만 제한 발동한다.
- v62 (2026-03-24): 동시보유 제한 actionable 기준 재정의 + stale 추적 과잉억제 완화.
  [#1] `_collect_actionable_position_limit_codes()`를 추가해, `position_limit` 계산 시 단순 `_detected_stocks`/carry 전체가 아니라
       실제 `entry_watch` / `execution_setup_watch` / 최근 active signal_log로 이어진 행동 가능한 코드만 우선 집계하도록 수정.
  [#2] `_get_carry_position_context()`를 위 actionable 코드 우선 구조로 바꿔, 재시작 후 `signal_log`/carry에 남은 다수의 추적중 종목 때문에
       `19/1종목 보유 중`처럼 신규 후보가 전부 억제되는 문제를 완화.
  [#3] entry_watch가 아직 비어 있어도 오늘/직전 영업일의 실제 행동 후보(`entry_price>0` 또는 `execution_setup_required`)만 제한적으로 반영하도록 보강.
  이유: 최근 로그상 진입가 알림 0건의 직접 병목은 `MID_PULLBACK` 예외보다도, stale/비행동성 추적 잔존이 동시보유 제한을 과하게 점유해
       선행형 A후보와 신규 리더가 position_limit에서 먼저 잘리는 구조였음.
  개선점: 동시보유 제한의 stale 억제↓, 신규 리더 포착 경로↑, 진입가 알림 연결 가능성↑.
  주의점: 동시보유 제한 자체는 유지하며, 실제 행동 가능한 감시(entry_watch/execution_setup/recent active signal)만 점유로 간주한다.
- v61 (2026-03-24): 섹터 후행화 + near-A 내부감시 자동승격 + 눌림목 NameError 복구.
  [#1] `_has_recent_actionable_tracking_state()` / `_should_promote_internal_capture_watch()` / `_promote_internal_capture_watch()`를 추가해,
       외부 A전용 억제로 바로 안 나가더라도 테마/직접뉴스/체결속도/장중 miss 확증이 붙은 near-A 후보는 자동으로 `signal_log` / `entry_watch` /
       `execution_setup_watch`에 내부 승격되도록 수정.
  [#2] `_dispatch_general_alert_signal()` / `run_mid_pullback_scan()`의 외부억제 경로에 위 내부승격을 연결해,
       섹터 seed 단계에서 보인 종목이 A 직전 단계에서 그냥 사라지지 않고 진입가 감시까지 이어지도록 보강.
  [#3] `_build_market_leading_sector_payload()`에 actionable tracking gate를 추가해,
       `entry_watch` / `execution_setup_watch` / 최근 `signal_log`로 연결된 종목이 한 개도 없는 테마는 사용자용 `[시장 주도 섹터]` 메시지에서 제외하고,
       노출되는 leader/follower도 행동 경로에 걸린 종목 중심으로 재구성하도록 수정.
  [#4] `analyze_mid_pullback()` 시작부에 `sector_info = {}` / `sentiment = {}` 기본값을 먼저 선언하고,
       `MID_PULLBACK` downtrend gate의 `signal_meta`와 반환 payload에 `sector_info`를 일관되게 싣도록 정리해,
       반복 발생한 `⚠️ 눌림목 오류 (...): name 'sector_info' is not defined`를 제거.
  이유: 섹터는 종목 포착 후 강화를 위한 보조 근거여야 하는데 기존 v60까지는 섹터 seed/요약 레이어가 종목 행동 경로보다 먼저 발화할 수 있었고,
       v61 작업 중에는 `analyze_mid_pullback()` 지역 변수 초기화 순서까지 어긋나 눌림목 스캔 예외 탈락이 추가로 발생했음.
  개선점: 종목 raw 포착→내부감시→A승격→섹터 강화 순서 일관성↑, near-A 후보의 진입가 감시 연결↑, 눌림목 예외 탈락↓.
  주의점: 외부 A전용 정책은 유지하며, 내부 자동승격은 테마/체결/장중 miss 확증이 충분한 후보에만 제한적으로 적용된다.
- v60 (2026-03-24): 선행형 A후보 자동확장 + ENTRY_POINT A등급 복구.
  [#1] `intraday_capture_mode.json`과 `_get_intraday_capture_mode()` / `_get_dynamic_general_a_relax_signal_types()` /
       `_get_dynamic_relaxable_no_chase_signal_types()`를 추가해,
       장중 상승 상위 리더 대비 포착률이 낮고 miss가 누적되면 `MID_PULLBACK` / `ENTRY_POINT`를 A완화·진입가 경과완화 대상에 자동 편입하도록 수정.
  [#2] `_should_bypass_mid_pullback_downtrend_block()` / `_count_intraday_leader_follow_confirmations()`를 추가해,
       선행형 후보가 직접뉴스·재상승·장중돌파·상대강도·거래량 회복 등 확증을 갖춘 경우에는
       장중 자동확장 모드에서 과도한 주봉·일봉 동반 하락추세 차단을 제한적으로 우회하도록 보강.
  [#3] `_finalize_mid_pullback_signal()` / `_get_mid_pullback_bucket_thresholds()`를 보강해,
       자동확장 모드에서는 `MID_PULLBACK`의 패턴 A컷과 실행확증 요구치를 제한적으로 완화하고 이유를 `reasons`에 남기도록 수정.
  [#4] `check_pullback_signals()`가 `ENTRY_POINT`에 `grade` / `execution_grade` / `pattern_grade`를 직접 부여하도록 고쳐,
       진입구간 신호가 등급 누락 때문에 `A전용 외부알림`에서 기본 `C`로 눌리던 문제를 차단.
  이유: 선행형 A후보를 찾는 구조로 바꾸려면 장중 miss 패턴을 프로그램이 스스로 감지해 A승격 경로를 자동으로 넓혀야 하고,
       진입가 알림은 `ENTRY_POINT` 등급 누락 같은 핫패스 오류 없이 바로 행동 단계로 이어져야 함.
  개선점: 장중 선행형 A후보 자동확장↑, 진입가 알림 복구↑, 과도한 하락추세 일괄차단 완화↑.
  주의점: A전용 정책은 유지하며, 자동확장은 KRX 장중 miss가 누적된 경우에만 제한적으로 켜지고 일정 시간 뒤 자동 해제된다.
- v59 (2026-03-24): stale carry 활성보유 오판 차단 + carry 로드 정리 강화.
  [#1] `_parse_compact_datetime()` / `_build_latest_tracking_by_code()` / `_is_active_carry_snapshot()` / `_sanitize_carry_snapshot_map()` 추가.
       carry snapshot을 단순 dict 개수로 세지 않고, 고아·만료·stale 추적 여부까지 반영해 실제 활성 carry만 남기도록 정리.
  [#2] `save_carry_stocks()` / `load_carry_stocks()`를 강화해, 시작 시 carry 파일을 signal_log 기준으로 먼저 정리하고
       stale carry는 복원·재저장하지 않도록 수정. 정리된 항목은 carry 파일에 즉시 재기록.
  [#3] `_get_carry_position_context()`를 `_detected_stocks` 우선 + carry sanitize fallback 구조로 바꿔
       `36/1종목 보유 중`처럼 잔존 carry를 실제 보유로 오인해 정규장 포착이 전부 막히는 문제를 차단.
  [#4] 출력 파일은 전부 plain UTF-8로 재생성해 BOM(EF BB BF) 재유입을 방지.
  이유: 동시보유 제한은 유지해야 하지만 stale carry를 실제 보유로 잘못 세면 신규 리더가 전부 억제돼
       정규장 포착 품질과 행동 가능 알림이 동시에 무너짐.
  개선점: 활성 carry count 정확도↑, 정규장 포착 복구↑, stale carry 잔존 억제↑.
  주의점: 실제 활성 추적중 종목은 여전히 동시보유 제한 대상이며, 이번 수정은 stale carry 오판만 제거한다.
- v58 (2026-03-24): 상승이탈 후속 추적 + BOM 제거.
  [#1] `_track_escape_aftermath()` 추가: 당일 상승이탈 종목의 장마감 시점 현재가를 조회해
       "진입했더라면 얼마나 벌었을까"(escape_aftermath_pct)를 signal_log에 자동 기록.
       run_daily_self_audit() KRX/NXT 양쪽에서 호출.
  [#2] `_refine_pullback_ratio_from_escape()` 추가: 후속 추적 데이터 기반 entry_pullback_ratio 정밀 조정.
       이탈 후 +10% 이상 계속 오른 비율이 60% 이상이면 진입가 완화,
       이탈 후 되돌림 40% 이상이면 현재 설정 유지.
  [#3] UTF-8 BOM(EF BB BF) 제거.
  이유: 상승이탈 23건(일주일 로그)이 이후 얼마나 더 올랐는지 추적하지 않으면
       entry_pullback_ratio 자동 완화가 "더 완화해야 하는지 / 이미 적절한지" 판단 불가.
  개선점: 상승이탈 후속 데이터 축적↑, entry_pullback_ratio 정밀 조정↑, BOM 혼선 제거.
  주의점: 후속 추적은 self-audit 시점(장마감)에 1회 실행. 장중에는 실행 안 됨.
       정밀 조정은 최근 20건 기준, 5건 미만이면 조정하지 않음 (데이터 부족 방어).
- v57 (2026-03-24): 포착 외부알림 행동단계 지연 + NXT 내부포착/감시 보존.
  [#1] `_should_delay_external_general_capture()` / `_persist_general_capture_without_external()` / `_has_pending_capture_watch()`를 추가해,
       일반 포착 신호가 행동 가능 단계 전이면 외부알림만 지연하고 `save_signal_log()` / `register_entry_watch()` 내부 파이프라인은 유지하도록 수정.
  [#2] `_dispatch_general_alert_signal()`에 위 지연 로직을 연결해,
       `EARLY_DETECT`는 즉시 텔레그램 포착 알림 대신 내부 추적·진입감시로만 넘기고 이후 `체결확정`/`진입가 도달` 단계에서만 외부 행동 알림이 나가게 정리.
  [#3] `execution_setup_required` 또는 `entry_price` 미확정 일반 포착도 같은 규칙으로 외부 발송을 늦춰,
       “진입시키지도 않을 종목 포착 알림”이 사용자 채널에 먼저 노출되는 문제를 줄임.
  이유: 사용자 원칙상 외부 알림은 정보 전달이 아니라 수익으로 이어지는 행동 신호여야 하는데,
       v56까지는 NXT/조기포착 복구 과정에서 `EARLY_DETECT`가 즉시 외부로 노출돼 실행 단계 전 정보성 알림처럼 보일 수 있었음.
  개선점: 외부 알림의 행동 가능성↑, 조기포착/NXT 내부 포착·감시 유지, 정보성 포착 스팸↓.
  주의점: 이번 변경은 외부 노출 시점만 늦추는 것이며, `EARLY_DETECT` 포착 자체와 signal_log/entry_watch 등록은 유지된다.
- v56 (2026-03-24): NXT 포착 외부알림 복구 — 장전/장후 NXT helper에 grade 부여.
  [#1] `_derive_general_signal_grade()`를 추가해, `SURGE` / `EARLY_DETECT` 계열이 `analyze()`와 동일한 A게이트 완화 규칙으로
       score→grade를 계산하도록 공용화.
  [#2] `check_nxt_preopen_detection()` / `check_nxt_postmarket_detection()`가 helper 반환 신호에
       `grade` / `execution_grade` / `pattern_grade` / `position`을 함께 싣도록 수정.
  [#3] 이로써 NXT helper 신호가 점수는 80점대인데도 `grade` 누락으로 `C등급 외부알림 억제(A전용)`에 걸려
       내부기록만 남던 문제를 차단.
  이유: 실로그에서 `삼성전자`, `DL이앤씨`, `삼성E&A`가 `84점 [C]`, `85점 [C]`로 찍혀 NXT 포착 자체는 있었지만
       외부알림 단계에서 grade 미기재 신호가 기본값 `C`로 해석되고 있었음.
  개선점: NXT 장전/장후 선포착의 실제 외부알림 복구, A전용 억제 오탐↓, signal_log/entry_watch 등급 일관성↑.
  주의점: 이번 수정은 NXT helper의 grade 누락 보정이며, 실제 A조건은 기존 `GENERAL_A_RELAX_SIGNAL_TYPES` / A게이트 규칙을 그대로 따른다.
- v55 (2026-03-24): 고아 추적 만료 전파 보강 + 장전/오버나이트 stale 재노출 차단.
  [#1] `_get_tracking_elapsed_days()` / `_is_tracking_display_expired()` / `_iter_signal_log_records()`를 추가해,
       `TRACK_MAX_DAYS`를 이미 넘긴 추적중 레코드와 고아 레코드를 장전/오버나이트 조회 단계에서 즉시 제외하도록 정리.
  [#2] `save_carry_stocks()` / `load_carry_stocks()` / `build_next_open_watchlist()`를 보강해,
       entry/stop/target이 비어 있는 carry·signal_log 잔존 종목이 `watchlist_next_open.json`과 재시작 복원 경로로 다시 살아나지 않도록 수정.
  [#3] `send_preopen_watchlist()`가 저장된 `overnight_risk_last.json` 문자열을 재사용하지 않고
       `_build_overnight_risk_alert_message()`로 현재 유효 추적 종목 기준 오버나이트 리스크를 다시 계산하도록 변경.
  [#4] `purge_orphan_tracking()`가 고아 만료 후 `_detected_stocks` / `_entry_watch` / `_execution_setup_watch`와
       익개장 워치리스트 캐시까지 함께 정리해, 고아 종목이 저장 파일·런타임 상태를 통해 재등장하는 문제를 막음.
  이유: v54 기준 고아 만료는 `signal_log` 중심으로만 반영돼 `carry_stocks`, `watchlist_next_open`, 장전 재사용 메시지 경로에 남은 종목이
       익개장 전 워치리스트와 오버나이트 위험 알림에 다시 나타날 수 있었음.
  개선점: 고아/stale 종목 재등장↓, 장전 워치리스트/오버나이트 요약 정확성↑, 재시작 후 잔존 추적 복원 오류↓.
  주의점: `TRACK_MAX_DAYS`를 넘긴 추적중 종목은 장전/야간 표시에서 먼저 제외되며, 최종 결과 기록은 기존처럼 `track_signal_results()`가 장중 가격으로 확정한다.
- v54 (2026-03-23): KIS REST 전역 호출 제한기 추가.
  [#1] `KIS_REST_LIMIT_PER_SEC` / `KIS_TOKEN_LIMIT_PER_SEC` / `_wait_for_kis_rest_slot()`를 추가해,
       실전 REST 호출을 전역 1초 윈도우에서 내부 상한(default 14건/초)으로 평탄화하고 토큰 발급도 1건/초로 별도 제한하도록 수정.
  [#2] `get_token()`과 `_safe_get()`의 실제 KIS REST 호출 직전에 동일 limiter를 연결해,
       재시도·403 재발급·동시 스캔이 겹쳐도 순간 burst가 공식 한도에 근접하지 않도록 보강.
  [#3] `SCAN_INTERVAL` 주석과 limiter 진단 카운터를 정리해,
       스캔 주기 자체가 아니라 전역 REST gate가 호출 한도 보호의 1차 장치임을 코드 해석상 명확히 반영.
  이유: 실전투자 REST는 최신 공지 기준 1초당 20건으로 관리되며, 기존 v53은 평균 주기만 보수적으로 잡고 순간 burst를 제어하지 못해
       장중/장마감/NXT 후처리 겹침 구간에서 호출 한도 안전 설계를 보장하기 어려웠음.
  개선점: 실전 REST burst 리스크↓, 장마감 self-audit/auto_tune 유지한 채 순간 호출 평탄화↑, 호출 한도 관련 운영 안전성↑.
  주의점: 내부 상한은 단일 프로세스 기준 기본 14건/초이며, 동일 appkey를 다른 프로세스·수동 조회와 병행하면 환경변수로 더 낮춰 운영하는 것이 안전함.
- v53 (2026-03-23): 동시보유 제한 후단 이동 + 신규 리더 선평가/후제한.
  [#1] `_get_carry_position_context()` / `_apply_position_limit_after_priority()`를 추가해,
       `filter_portfolio_signals()`가 신규/기존 신호를 먼저 `stale quota`·리더 우선 정렬로 평가한 뒤에만
       max_positions 기반 동시보유 제한을 적용하도록 순서를 재배치.
  [#2] 보유 한도 초과 시 잘리는 신규 후보는 `position_limit` shadow 기록에
       `priority_rank` / `leader_priority_hit` / `stale_pullback_hit` / `stale_replay_penalty_hit`를 함께 남기도록 보강.
  [#3] 동시보유 제한 로그를 `평가 후 신규 n개 억제` 형태로 바꿔, 신규 리더를 먼저 선별한 뒤 행동 가능 단계에서만 잘랐는지
       운영 로그에서 바로 확인 가능하게 정리.
  이유: v52까지는 `filter_portfolio_signals()` 초반의 max_positions 차단이 stale 눌림목 quota·리더 우선 정렬보다 먼저 실행돼,
       좋은 신규 리더도 보유 중이라는 이유만으로 선평가 없이 잘리는 구조적 모순이 남아 있었음.
  개선점: 신규 리더 선평가/기록↑, 동시보유 제한의 과잉 억제 체감↓, position_limit self-audit 해석력↑.
  주의점: 실제 외부 알림은 기존처럼 보유 한도 이후 행동 가능한 후보만 남기며, 이번 변경은 동시보유 제한을 제거하는 것이 아니라 적용 순서를 후단으로 내리는 보정임.
- v52 (2026-03-23): 오후 NXT-only 리더 포착 보강.
  [#1] `_is_nxt_postmarket_only_window()` / `_collect_nxt_postmarket_candidates()` / `check_nxt_postmarket_detection()`를 추가해,
       15:40 이후 KRX 종료·NXT 단독 시간대에 현대힘스형 장후 리더를 별도 helper로 선포착하고 일반 급등 스캔 이전에 후보화하도록 수정.
  [#2] `get_nxt_surge_stocks()`의 NXT volume-rank 조회 수를 시간대별로 조정하고, `refresh_dynamic_candidates()` / `run_scan()`에서
       장후 NXT-only일 때 랭킹 후보를 선택적으로 더 넓게 스캔해 후보군이 20개 상한에 갇히지 않도록 보강.
  [#3] `_calc_nxt_postmarket_leader_bonus()` / `_should_soft_allow_no_ask_liquidity_general()` / `_sector_gate_sort_key()`에
       `nxt_post_leader_hit`을 연결해 장후 NXT 리더 후보는 점수·정렬·유동성 soft allow에서 우선권을 더 받게 정리.
  이유: 현대힘스처럼 정규장에 잠잠하다가 오후 NXT-only에서만 +10% 안팎으로 강해지는 종목은 기존 `v51` 구조에선 후보군 20개·보수 파라미터·오후 전용 helper 부재 때문에 쉽게 누락될 수 있었음.
  개선점: 오후 NXT-only 리더 포착률↑, 장후 후보군 미포함 miss↓, 리더 후보 `no_ask_liquidity` 과차단↓.
  주의점: 장후 NXT helper는 15:40 이후 KRX 종료 구간에서만 작동하며, 장후 breadth·테마·직접뉴스가 모두 약한 종목까지 무리하게 끌어올리지는 않음.
- v51 (2026-03-23): 미사용 상수 `ENTRY_TOLERANCE_PCT` 제거.
  [#1] 실제 참조가 없는 `ENTRY_TOLERANCE_PCT = 2.0` 정의를 삭제해, 공통 진입 허용 구간 로직이 살아 있는 것처럼 보이던 혼선을 제거.
  이유: 현재 v50 기준 포착/도달/진입감시 경로 어디에서도 해당 상수를 읽지 않아 동작 영향은 없고, 코드 해석만 혼동시켰음.
  개선점: 미사용 상수 혼선 제거, 진입 허용 규칙 해석 명확화.
  주의점: 실제 진입 허용 판정 로직은 기존 경로를 그대로 사용하며, 이번 변경은 동작 변경이 아닌 미사용 상수 정리임.
- v50 (2026-03-23): 주봉·일봉 동반 하락 추세 종목 포착 차단.
  [#1] `_get_multi_tf_downtrend_context()` / `_should_block_multi_tf_downtrend_capture()`를 추가해,
       최근 20일·8주 수익률, 20일선/60일선, 일봉·주봉 lower-high를 함께 보고 주봉·일봉 동반 하락 추세를 보수적으로 판정하도록 수정.
  [#2] `analyze()` / `check_early_detection()` / `check_nxt_preopen_detection()` / `analyze_mid_pullback()` / `check_pullback_signals()`에
       동일 차단 로직을 연결해 `SURGE`/`EARLY_DETECT`/`NEAR_UPPER`뿐 아니라 `MID_PULLBACK`/`ENTRY_POINT`도 큰 하락 추세면 포착 단계에서 기본 제외되도록 정리.
  [#3] `_log_suppressed_alert()`에 20일 수익률/8주 수익률/일봉·주봉 하락 플래그를 남기게 해,
       인베니아처럼 주봉·일봉이 함께 눌리는 종목이 왜 차단됐는지 내부 학습 로그로 추적 가능하게 보강.
  이유: stale 재노출 감점과 breadth 보정이 있어도 주봉·일봉 동반 하락 추세 종목이 `MID_PULLBACK`/`ENTRY_POINT` 경로에서 다시 살아날 여지가 남아 있었고,
       관리종목/거래정지 위험으로 이어지는 종목을 큰 줄기에서 선제 배제할 필요가 있었음.
  개선점: 하락 추세 종목 포착률↓, 인베니아류 역추세 포착 차단↑, 신규 주도주 슬롯 확보↑.
  주의점: 직접뉴스/테마주도 강세라도 주봉·일봉 동반 하락 추세 판정이면 기본 차단하며, 해당 차단은 내부 suppressed 로그에만 남고 외부 알림은 발송되지 않음.
- v49 (2026-03-23): 반복 miss 테마 신규 리더 가산 + stale 테마 breadth 정밀 감점.
  [#1] `_collect_theme_feedback_candidates()` / `_calc_miss_theme_leader_bonus()` / `_get_theme_breadth_hint()`를 추가해,
       self-audit에서 반복 miss된 테마의 신규 리더/동조 강세 종목을 다음날 동적 후보군에 제한적으로 재편입하고, 강한 리더면 추가 점수와 우선권을 부여하도록 수정.
  [#2] `_calc_stale_replay_penalty()`에 stale 테마 breadth(상승 종목 비율/평균 상승률/리더 강도)를 연결해,
       breadth가 약한 stale 테마는 감점을 더 강하게 하고 breadth가 살아 있는 테마는 감점을 일부 완화하도록 보강.
  [#3] `refresh_dynamic_candidates()` / `analyze()` / `_sector_gate_sort_key()` / `_should_soft_allow_no_ask_liquidity_general()`에
       `miss_theme_leader_hit`과 theme feedback 후보를 연결해, 전일 반복 miss된 테마의 신규 강세 리더가 후보군·점수·정렬·soft allow에서 더 앞서도록 정리.
  이유: v48까지 stale 재노출 감점은 강화됐지만, self-audit에서 반복 miss된 테마의 신규 리더를 장중에 충분히 밀어주지 못했고,
       stale 테마 감점도 breadth 강도와 무관하게 작동해 살아 있는 테마까지 과하게 눌릴 여지가 있었음.
  개선점: 반복 miss 테마 신규 리더 포착률↑, 테마 기반 후보 보강↑, stale 테마 과감점↓/약한 stale 테마 정밀 감점↑.
  주의점: theme feedback 후보와 가산점은 직접뉴스/테마동조/강한 급등형에만 제한 적용되며, `MID_PULLBACK`/`ENTRY_POINT`를 신규 리더처럼 승격시키지는 않음.
- v48 (2026-03-23): stale quota + self-audit 연동 재노출 감점 보정.
  [#1] `stale_replay_penalty.json`과 `_build_stale_replay_penalty_profile()` / `load_stale_replay_penalty_profile()`를 추가해,
       `stale_pullback_quota`/`stale_replay_penalty` shadow 기록과 장마감 self-audit miss 압력을 묶어 반복적인 stale 재노출 종목·테마 감점 프로필을 생성하도록 수정.
  [#2] `_calc_stale_replay_penalty()`를 추가하고 `_annotate_signal_priority()`에 연결해,
       `MID_PULLBACK` / `ENTRY_POINT`가 장중 repeatedly stale로 판정된 코드/테마면 점수를 추가 감점하고 강한 경우 `stale_pullback_hit`으로 승격되게 보강.
  [#3] `_apply_stale_pullback_quota()` / `filter_portfolio_signals()` / `run_mid_pullback_scan()` / `_sector_gate_sort_key()`에
       `stale_replay_penalty_hit`을 연결해 신규 리더가 존재할 때 stale 재노출이 반복되는 눌림목이 더 뒤로 밀리거나 shadow 기록으로 전환되도록 정리.
  이유: v47까지 stale quota와 신규 리더 우선권은 들어갔지만, self-audit에서 반복 확인된 stale 재노출 종목/테마가 다음날 장중 점수/정렬에 더 강하게 감점되지 않아 같은 종목이 다시 앞줄에 설 여지가 남아 있었음.
  개선점: stale 재노출 반복 감점↑, 신규 리더 우선권 체감↑, shadow/self-audit 기반 장중 보정 연속성↑.
  주의점: 직접뉴스/테마주도/강한 급등처럼 신규 리더 근거가 충분한 경우는 감점을 제한하며, stale 눌림목을 전면 차단하지는 않음.
- v47 (2026-03-23): stale 눌림목 quota 축소 + 신규 리더 우선권 연결.
  [#1] `_load_tracking_priority_hints()` / `_annotate_signal_priority()`를 추가해 대표 추적 로그의 최초 포착 시각과 최근 상태를 읽고,
       `MID_PULLBACK` / `ENTRY_POINT`가 오래된 재포착인지(stale)와 당일 신규 리더 우선권 대상인지(leader priority)를 공통 표기하도록 수정.
  [#2] `_apply_stale_pullback_quota()`를 추가해 같은 스캔 사이클에 신규 리더가 존재하면 stale 눌림목/재포착 신호 수를 제한하고,
       초과분은 `shadow_capture`로 남기되 외부 알림 우선순위에서는 뒤로 밀리게 정리.
  [#3] `filter_portfolio_signals()` / `run_mid_pullback_scan()` / `_sector_gate_sort_key()`에 leader priority / stale penalty를 연결해
       기존 `ENTRY_POINT`/`MID_PULLBACK` 재노출보다 신규 강세주/테마 리더가 먼저 통과되도록 보강.
  이유: 주간 로그/CSV 분석 결과 상승 리더 miss의 본질 중 하나가 stale 눌림목 재노출이 신규 강세주보다 앞서 알림 슬롯과 우선순위를 차지하는 구조에 있었음.
  개선점: stale 재노출 과다↓, 신규 리더 우선 통과↑, self-audit/adaptive feedback 효과 체감↑.
  주의점: 눌림목 신호를 제거하지는 않으며, 대표 재상승·직접뉴스·테마 동조형처럼 신규 리더 근거가 충분한 경우는 stale quota에서 제외.
- v46 (2026-03-23): self-audit 결과 기반 다음날 자동 피드백 연결.
  [#1] `adaptive_capture_feedback.json`과 `_build_adaptive_capture_feedback()` / `load_adaptive_capture_feedback()`를 추가해,
       장마감 self-audit의 누락 종목·테마·차단 사유를 다음 거래일 후보군/점수/필터 보정에 재사용하도록 수정.
  [#2] `refresh_dynamic_candidates()`에 최근 miss 상위 종목 재편입 후보 수집을 연결하고,
       `analyze()`에는 feedback priority code/theme 가산점을 추가해 전일 장마감 상승주 miss가 다음날 `기타`에 묻지 않도록 보강.
  [#3] `no_ask_liquidity` soft 허용과 섹터 게이트 정렬에도 feedback bias를 연결해,
       전일 self-audit에서 반복 차단된 리더형 종목이 다음날 동일 이유로 재차 잘리는 문제를 완화.
  이유: 주간 CSV 분석 결과 miss의 본질이 개별 조건값보다 장마감 결과와 프로그램 결과의 차이를 다음날 로직에 반영하지 못하는 구조에 있었음.
       self-audit/shadow-capture를 기록만 하지 말고 실제 후보·점수·차단 완화에 연결해야 개선 효과가 누적됨.
  개선점: 전일 miss 리더 후보 재편입↑, 테마 동조·개별 리더 보정 누적↑, no_ask_liquidity/후보미포착 재발 방지↑.
  주의점: feedback 가산은 제한적으로만 적용되며, `MID_PULLBACK` / `ENTRY_POINT` stale 재노출을 우대하지 않도록 점수 상한과 신호군 제한을 둠.
- v45 (2026-03-23): 운영 버전 잠금 + 장마감 self-audit + shadow-capture 추가.
  [#1] `runtime_version_lock.json` 기반 운영 버전 잠금을 추가해 공유 볼륨에 더 최신 버전이 기록돼 있으면 구버전 런타임이
       스캔/알림을 자동 중단하도록 수정. 같은 날 구버전/신버전이 섞여 실제 miss 원인 분석이 흔들리던 문제를 줄이기 위한 보강이다.
  [#2] `run_daily_self_audit()`를 추가해 장마감 상승 상위 종목과 실제 포착/차단/제한 억제 결과를 자동 비교하고
       `daily_self_audit.json`에 저장한 뒤 텔레그램 요약을 발송하도록 수정.
  [#3] `position_limit`/`sector_limit`/`no_ask_liquidity`/`A전용 외부억제` 같은 누락 사유를 `shadow_captures.json`에
       남기도록 연결해, 외부 알림이 막혀도 self-audit과 다음날 로직 보정에 쓸 내부 학습 데이터는 유지되게 정리.
  이유: 주간 로그 분석 결과 강세주 miss의 본질이 단일 조건값보다 운영 버전 혼선 + 동시보유 제한/유동성 차단 같은 구조적 누락에 가까웠고,
       장마감 결과와 프로그램 결과를 자동 비교하는 피드백 루프가 필요했다.
  개선점: 구버전 혼선↓, 누락 사유 가시성↑, 장마감 결과 기반 다음 수정 효율↑.
  주의점: 이번 버전은 stale 눌림목 quota 대수술보다 운영 잠금·self-audit·shadow 기록을 먼저 넣는 최소 보강이다.
- v44 (2026-03-23): 테마 동조 강세주 후보 확장 + 실시간 테마 주도 보강.
  [#1] `_collect_theme_peer_follow_candidates()`를 추가해 상한가/급등 seed 종목의 동일 테마 peer를 실시간 시세로 재확인한 뒤,
       강한 동조 상승 종목을 후보군에 즉시 편입하도록 수정. 삼륭물산처럼 테마 주도주 peer인데 랭킹/NXT 후보에서 밀리던 종목의
       스캔 누락을 줄이기 위한 보강이다.
  [#2] `_get_theme_drive_hint()`와 `THEME_DRIVE_*` 규칙을 추가해 직접뉴스가 약해도 테마 leader·breadth·flow가 강하면
       `sector_info.theme`을 보존/승격하고 점수에 `테마 동조강세` 보너스를 반영하도록 정리.
  [#3] A게이트 완화 판정에 `테마 동조강세` 근거를 반영해, 강한 테마 주도 구간의 `SURGE` / `EARLY_DETECT` / `NEAR_UPPER`가
       `기타`로 눌리거나 B에 머무는 문제를 완화.
  이유: 삼륭물산처럼 개별 공시보다 테마 전체 강세로 상한가에 가는 종목은 직접뉴스/신규이슈만으로는 늦거나 누락될 수 있었음.
       테마 leader의 동조 확산을 실시간 후보군과 점수에 같이 반영해야 효율적으로 놓침을 줄일 수 있음.
  개선점: 테마 동조주 포착률↑, 상한가/주도주 peer 누락↓, `기타업종` 잔류 감소↑, A 후보 선별력↑.
  주의점: `MID_PULLBACK` / `ENTRY_POINT` 보수 정책은 유지하며, theme peer 편입은 강한 seed/동조 흐름이 확인될 때만 제한적으로 동작.
- v43 (2026-03-23): 비실전형 알림 진입가 제거 + 포착/행동 알림 용어 분리.
  [#1] 일반 포착 상세/컴팩트 메시지에서 `_build_capture_focus_price_line()`과 compact header를 정리해,
       실전형이 아닌 포착 알림은 `현재가`만 보여주고 `진입가`·`목표진입`·가격 괴리 문구를 제거하도록 수정.
  [#2] `[익영업일 갭상승 선진입 후보]`, `[손절 후 재진입 후보]`처럼 아직 실행 확정 전인 후보형 알림은
       진입가/손절가/목표가 블록을 제거하고 `실제 진입가는 도달/확정 알림에서만 제공` 문구로 역할을 분리.
  [#3] 비실전형 포착 사유 필터에서도 `진입가` 문구를 제외해, 텔레그램에서 `진입가 확인 → 도달 확인 → 진입` 흐름이
       오직 실전형 알림에만 대응되도록 정리.
  이유: 사용자가 텔레그램에서 `종목 포착 → 진입가 확인 → 진입가 도달 알림 → 진입` 순서로 활용하므로,
       실전형이 아닌 포착/후보 알림에 `진입가`가 노출되면 행동 기준을 오염시켜 해석 혼선을 유발했음.
  개선점: `진입가` 용어 신뢰도↑, 포착 알림과 행동 알림 역할 분리↑, 비실전형 가격 오해↓.
  주의점: 초기 포착/후보 알림은 여전히 참고용이며, 실제 진입 가격은 도달/확정 알림에서만 확인한다.
- v41.103 (2026-03-23): 신규 이슈 자동 테마화 보강 — 사전 용어 없이도 강세 이슈를 섹터/점수에 반영.
  [#1] `EMERGENT_*` 규칙과 `_infer_emergent_issue_theme()` / `_register_emergent_issue_theme()`를 추가해
       종목별 뉴스 헤드라인에서 반복되는 핵심어를 자동 추출하고, 기존 직접뉴스 키워드에 없더라도
       `신규이슈·{핵심어}` 형태의 내부 테마로 승격하도록 수정.
  [#2] `analyze()` / `check_nxt_preopen_detection()`에 신규 이슈 fallback을 연결해,
       직접뉴스 테마가 비어도 강한 흐름 + 반복 헤드라인이 있으면 `sector_info.theme`과 점수에 즉시 반영되게 정리.
  [#3] 자동 추출된 이슈 테마는 `_dynamic_theme_map`에 저장해 이후 동적 후보군/섹터 모멘텀/시장 주도 섹터에도
       연동되도록 연결하고, A 완화 판정에서도 `신규이슈 자동감지` 근거를 의미 있는 테마로 해석하게 보강.
  이유: 한텍처럼 기존 사전에 없는 표현의 이슈가 뉴스·수급으로 먼저 강해질 때, 수동 키워드 추가 전까지 `기타`에 묻어
       강한 종목이 누락되는 문제가 있었음.
  개선점: 새 이슈 자동 테마화↑, `기타` 잔류 감소↑, NXT→정규장 연속 강세주의 A 후보 반영력↑.
  주의점: 신규 이슈 자동감지는 반복 헤드라인 기반이라 너무 일반적인 단어는 제외하며, `MID_PULLBACK` / `ENTRY_POINT` 보수 정책은 유지.
- v41.102 (2026-03-23): A전용 외부알림 전환 + 한텍형 리더 승격 보강 + 코드 위생 정리.
  [#1] 일반 포착/눌림목 신규 외부알림을 A등급 전용으로 전환하고, B/C는 내부 기록만 남기도록 정리.
       `_dispatch_general_alert_signal()` / `run_mid_pullback_scan()`에 내부전용 억제 경로를 추가해
       B/C 반복 외부알림을 줄이되, 추후 A 상향 재평가는 유지.
  [#2] `GENERAL_A_RELAX_SIGNAL_TYPES` / `_should_relax_general_a_threshold()`를 추가해
       `SURGE` / `EARLY_DETECT` / `NEAR_UPPER`는 강한 흐름·의미 있는 테마·NXT 연속성 조건에서
       A 문턱을 선택 완화하도록 수정.
  [#3] `DIRECT_NEWS_THEME_RULES`에 LNG·플랜트·에너지설비·열교환기 계열 직접뉴스 승격 규칙을 추가하고,
       `check_nxt_preopen_detection()`에도 직접뉴스/섹터 보강을 연결해 한텍형 종목이 `기타`에 묻히지 않도록 정리.
  [#4] 미사용 함수 `_gather_news_stock_candidates()` / `_is_news_reason_for_ui()` / `_is_sector_reason_for_ui()`를 제거하고,
       점수 표기용 `_signed_repl` 로컬 중복을 공용 helper로 통합.
  이유: 실제 행동 가능한 알림은 A등급 중심인데 B/C 외부알림이 많았고, LNG·수주·에너지설비형 리더가
       직접 승격 부족으로 `기타`에 묻히는 반면 stale 눌림목은 상대적으로 자주 노출되는 문제가 있었음.
  개선점: 외부 알림 품질↑, 한텍형 리더 승격력↑, `기타` 병목 완화↑, 코드 혼선↓.
  주의점: `MID_PULLBACK` / `ENTRY_POINT`는 A 문턱 완화 대상에서 제외하며, B/C는 외부알림 없이 내부 로그/재평가만 유지.
- v41.101 (2026-03-23): 급등/조기포착 계열 고점추격방지 경과 완화 복구.
  [#1] `RELAXABLE_NO_CHASE_ENTRY_SIGNAL_TYPES`를 추가해 `SURGE` / `EARLY_DETECT` / `NEAR_UPPER`에만
       경과 완화 로직을 다시 연결하고, `MID_PULLBACK` / `ENTRY_POINT`는 기존 고점추격방지 고정 정책을 유지.
  [#2] `_select_representative_entry_price()` / `_apply_entry_price_guard()`에 `detect_date` / `miss_count`를 복구해
       최초 포착 2일 경과, 미도달 3회 이상, 괴리율 15% 이상 중 하나면 상향 진입가 갱신을 허용하도록 수정.
  [#3] 대표 진입가 재동기화 및 진입감시 재등록 경로에서 `first_detect_date` / `miss_count`를 함께 넘기고,
       `_entry_watch`에 `first_detect_date`를 보존해 재포착 누적 시간이 끊기지 않도록 정리.
  이유: `SURGE` 계열은 고점추격방지를 너무 오래 고정하면 현재 시장과 동떨어진 진입가가 유지돼 실질 진입 기회를 놓칠 수 있었음.
  개선점: 급등 재포착 현실성↑, 오래된 대표 진입가 갱신 가능성↑, SURGE 계열 행동 가능성↑.
  주의점: 눌림목 계열(`MID_PULLBACK`, `ENTRY_POINT`)은 동일 완화에서 제외해 기존 보수성을 유지.
- v41.100 (2026-03-23): 오전 NXT 장전 선포착 호출 복구.
  [#1] `check_nxt_preopen_detection()`를 분리해 08:00~08:59 NXT 장전 선포착 조건을 별도 helper로 정리.
  [#2] `run_scan()`에서 `nxt_open and not krx_open` 구간에도 해당 helper를 호출하도록 연결해,
       정규장 시작 전에도 장전 NXT 선포착 신호가 실제로 평가되게 수정.
  [#3] 기존 `check_early_detection()`는 KRX 장중 조기포착을 유지하되, 장전 NXT 선포착 helper를 재사용하도록 정리.
  이유: 오전 NXT-only 구간에서는 후보 수집은 되고 있었지만 장전 선포착 호출 경로가 막혀 실제 신호가 전부 사라지고 있었음.
  개선점: 오전 NXT 선포착 복구↑, 장전 후보 포착 연속성↑, KRX 개장 전 알림 공백 감소↑.
  주의점: 이번 버전은 장전 NXT 선포착 호출 경로만 복구하며 기존 점수식/일반 장중 스캔 구조는 유지.
- v41.99 (2026-03-23): 상승이탈 기반 진입가 자동완화 + 손실 누적 시 보수 복원 가드 추가.
  [#1] `_signal_feedback_sort_key()` / `_auto_tune_entry_pullback_ratio_feedback()`를 추가해
       최근 `진입미달` 중 `상승이탈` 비중이 높으면 `entry_pullback_ratio`를 자동 완화하도록 연결.
  [#2] 자동 완화 이후 최근 완료건 승률/평균손익/손절 비중이 악화되면
       `entry_pullback_ratio`를 기준값 쪽으로 복원하고 `min_score_normal`, `atr_stop_mult`를 함께 보수화.
  [#3] `check_entry_watch()`의 `기간만료` 기반 진입가 비율 완화 직후 `_save_dynamic_params()`를 호출해
       재시작 후에도 즉시 반영되도록 정리.
  이유: `상승이탈`이 많을 때 진입가 완화가 자동으로 따라가야 하고, 그 결과 손실이 누적되면
       다시 기준을 되돌리는 보완 장치가 함께 돌아야 운영 리스크를 줄일 수 있었음.
  개선점: 진입미달 적응력↑, 자동완화 이후 손실 방어력↑, 재시작 후 파라미터 일관성↑.
  주의점: 이번 버전은 `entry_pullback_ratio` 피드백 루프를 추가하며 기존 신호/알림 구조는 유지.
- v41.98 (2026-03-23): 주말/공휴일 대기 모드에서 평일 자동 전환 복구.
  [#1] `_run_holiday_standby_until_trading_day()`를 추가해 주말/공휴일에 시작한 프로세스가
       자정 이후 평일로 바뀌면 대기 모드를 빠져나와 평일 스케줄을 다시 등록하도록 수정.
  [#2] 공휴일/주말 분기에서 기존 무한 대기 루프를 helper 호출로 교체하고,
       평일 전환 시 `schedule.clear()` 후 정상 초기화 흐름으로 이어지도록 정리.
  이유: 주말에 켜 둔 봇이 월요일이 되어도 대기 모드에 머물러 07:30 장전 메시지를 놓칠 수 있었음.
  개선점: 주말→평일 자동 복귀 안정성↑, 07:30/08:30/08:50 장전 메시지 연속성↑.
  주의점: 주말/공휴일에는 기존처럼 대기 모드를 유지하며, 평일 전환 시에만 자동 복귀함.
- v41.97 (2026-03-21): `/list` 진입가 옆에 현재가 대비 괴리율 표시 추가.
  [#1] `_format_watch_list_entry_vs_current()`를 추가해 현재가가 있을 때 `진입가` 라인 옆에
       `현재가 대비 +/-%`를 일관된 부호 규칙으로 표시하도록 정리.
  [#2] `/list`의 `진입가 감시중 종목` / `목표가 추적중 종목`에서 `🎯 진입가` 표시에
       `(<현재가 대비 ±x.x%>)`를 함께 붙이도록 수정.
  이유: `/list`에서 현재가와 진입가를 눈으로 다시 계산해야 해 대기 거리와 체결 후 위치를 즉시 판단하기 어려웠음.
  개선점: 진입 괴리 해석 속도↑, `/list` 실전 판단력↑.
  주의점: 표시 계층만 보강하며 진입/알림 정책은 변경하지 않음.
- v41.96 (2026-03-21): `/list` 감시 종목 현황에 종목별 현재가 표시 추가.
  [#1] `_get_watch_list_current_price()`를 추가해 `/list`에서 종목별 현재가를 KRX/NXT 상태에 맞게 조회하고,
       `last_price/current_price`가 있으면 fallback으로 재사용하도록 정리.
  [#2] `감시 종목 현황`의 `진입가 감시중 종목` / `목표가 추적중 종목` / 보조 감시종목 라인에
       `📍 현재가`를 함께 표시하도록 정리.
  이유: `/list` 메시지에 진입가·목표가·손절가만 있고 현재가가 없어, 감시 종목별 대기 거리와 현재 위치를 즉시 판단하기 어려웠음.
  개선점: 감시 종목 현황 해석력↑, 수동 점검 속도↑.
  주의점: 이번 버전은 `/list` 표시 계층만 보강하며 진입/알림 정책은 변경하지 않음.
- v41.95 (2026-03-21): crash logger 실복구 + `/stats` 실진입 눌림목 bucket 진단 추가.
  [#1] `install_excepthook()`의 crash log 저장을 `traceback.format_exception(exc_type, exc, tb)` 기반으로 수정해
       실제 미처리 예외 traceback이 파일에 그대로 남도록 복구.
  [#2] `compute_signal_kpi(completed, pnl_field=...)`로 확장하고 `_send_stats()`에
       `actual_entry=True` + `actual_pnl` 완료건 기준 `🪙 실진입 눌림목 bucket` 섹션을 추가.
       bucket별 승률 / 평균손익 / 손익비 / 기대수익 / 실행등급 분포를 함께 표시.
  이유: 실진입 관점에서 어떤 눌림목 bucket이 실제 돈이 되는지 바로 확인할 수 있어야 하고,
       crash file에 `NoneType: None`만 남는 상태는 정상본으로 둘 수 없었음.
  개선점: 예외 추적력↑, 실진입 bucket 해석력↑.
  주의점: 이번 버전은 진입/알림 정책을 바꾸지 않고 진단/기록 계층만 보강.
- v41.94 (2026-03-21): 지정학 신규/복합 섹터 동적 흡수 + 관련 종목 매핑 확장.
  [#1] `_normalize_geo_sector_name()` / `_split_geo_sector_tokens()` / `_derive_geo_sector_stocks()` /
       `_remember_geo_sector_candidates()`를 추가.
       AI가 반환한 신규/복합 지정학 섹터명을 분해·정규화해 `_GEO_SECTOR_STOCKS`, `THEME_MAP`, `_dynamic_theme_map`,
       reason 문장 안 직접 언급 종목명까지 함께 탐색해 관련 종목 후보를 유도.
  [#2] `analyze_geopolitical_event()` 성공/실패 fallback 경로에서 `sector_directions`를 동적 테마로 저장해,
       같은 날 반복되는 신규 섹터명도 `📌 관련 종목`과 과거 유사 이력 조회에 더 잘 연결되도록 정리.
  이유: 지정학 분석은 AI가 새 섹터명을 만들 수 있는데, 기존 종목 매핑은 고정 섹터명 위주라 연결력이 약했음.
  개선점: 지정학 신규 섹터 종목 연결력↑, `/geo`/정기 지정학 메시지 해석력↑.
  주의점: 지정학 점수식/방향 규칙은 바꾸지 않고 종목 연결층만 확장.
- v41.93 (2026-03-21): `/stats` 눌림목 bucket 진단 추가.
  [#1] `compute_signal_kpi()`에 `by_mid_pullback_bucket` 집계를 추가해
       `weekly_monthly_trend / daily_trend / gap_first_pullback / intraday_reclaim` bucket별
       승률 / 평균손익 / 기대수익 / 손익비 / 실행등급 분포를 계산.
  [#2] `_send_stats()`에 `🧪 눌림목 bucket 진단` 섹션을 추가해,
       bucket별 표본·성과·고성과/저성과 bucket 요약을 바로 확인할 수 있게 정리.
  이유: 내부 자동교정은 bucket 기준으로 돌고 있었지만, 운영자가 `/stats`에서 어떤 bucket이 실제로 좋은지 바로 보기 어려웠음.
  개선점: 눌림목 유형별 운영 판단력↑, auto_tune 해석력↑.
  주의점: 이번 버전은 신호 계산식이 아니라 진단 출력 계층 보강.
- v41.92 (2026-03-21): crash logger/코드 위생 정리.
  [#1] `_map_geo_sectors()`가 함수 내부 `import re` 대신 전역 `_re`를 사용하도록 정리.
  [#2] crash logger 정합성 복구를 위한 기반 정리.
  이유: changelog에 적힌 정리 상태와 실코드가 어긋나 있었음.
  개선점: 코드 위생↑.
  주의점: 기능 변화는 크지 않으며 이후 정합성 복구 버전의 전단계 성격.
- v41.91 (2026-03-21): 변경이력 정합성 복원 + v41.89/v41.90 누락 기능 재적용.
  [#1] changelog를 `v41.88 → v41.89 → v41.90 → v41.91` 순으로 복원하고,
       `00_BASELINE_POINTER.txt` / `01_HANDOFF.md` / `02_START_CHAT_UTF8_BOM.md`를 현재 기준과 다시 동기화.
  [#2] `_get_effective_change_rate()`를 추가하고 `_detect_entry_block_reason()`를 확장해,
       `MID_PULLBACK`/`ENTRY_POINT` 계열은 상한가 잠김뿐 아니라 상한가 도달 자체도 `upper_limit_reached`로 차단.
       KIS `change_rate`와 `prev_close` 대비 실계산 등락률 중 보수적인 값을 함께 사용.
  [#3] `_register_nxt_surge_to_krx_watch()`의 외부 텔레그램 전환 알림을 제거하고 내부 로그만 유지.
       대신 `register_entry_watch()` / `_load_entry_watch_active()`에 `entry_price_at_detect` / `execution_grade_at_detect` / `pattern_grade_at_detect`를 저장하고,
       `check_entry_watch()`의 `[1차 진입가 도달]`에 `_format_nxt_transition_delta_block()`을 연결해 `등급 변화`, `진입가 조정(+/-%)`을 조건부 표시.
  이유: v41.88부터 시작한 수정 대화 기준으로는 `v41.89`/`v41.90` 이력이 빠져 있었고,
       실제 코드에도 상한가 도달 차단과 NXT 중간알림 정리/1차 도달 변화표시가 누락된 상태였음.
  개선점: 변경이력 스킵 복원↑, 눌림목 상한가 오알림 차단↑, NXT 전환 중간알림 소음↓, 1차 진입가 도달 해석력↑.
  주의점: 이번 버전은 기존 `v41.90` 구조(눌림목 4분류 + pattern/execution grade + auto_tune)를 유지한 채 누락분을 복원한 통합 정합성 버전.
- v41.90 (2026-03-21): 눌림목 4분류 + 유형별 실행 A게이트 + 자동교정 루프 추가.
  [#1] `_classify_mid_pullback_setup()` / `_finalize_mid_pullback_signal()`를 추가해 `MID_PULLBACK`을
       `월·주 추세형 / 일봉 추세형 / 갭 후 첫 눌림형 / 분봉 재개형`으로 분류하고,
       `pattern_grade`(재포착 기준)와 `execution_grade`(표시/실행 기준)를 함께 저장.
  [#2] `_apply_mid_pullback_execution_grade()`에 유형별 A조건과 KRX/NXT 장마감 근접 보수 게이트를 연결.
       섹터/재상승/장중돌파/수급전환/상대강도/거래량Z/거래량회복/당일양봉 등을 합산해
       실행 확증이 부족하면 `A→B/C`, `B→C`로 하향.
  [#3] `run_mid_pullback_scan()` / `_register_nxt_surge_to_krx_watch()` / `save_signal_log()` / `register_entry_watch()`를
       `pattern_grade`/`execution_grade`/`mid_pullback_bucket` 기준으로 정리하고,
       `_mid_pullback_alert_history`도 `{ts, pattern_grade, execution_grade, grade}` 형태로 확장.
  [#4] `auto_tune()`에 눌림목 유형별 A게이트 자동교정을 추가.
       최근 결과를 보고 `mid_pullback_bucket_a_confirm_min`, `mid_pullback_bucket_b_confirm_min`,
       `mid_pullback_close_window_min_krx`, `mid_pullback_close_window_min_nxt`, `mid_pullback_close_gate_level`을 장마감 후 자동 조정.
  이유: 눌림목은 월·주·일·분 구조가 다른데 기존 로직은 하나의 A/B/C로만 판단해
       `A등급(최우선)` 과대평가와 태웅형 재포착 요구를 동시에 만족시키기 어려웠음.
  개선점: 태웅형 raw 상향 재포착은 유지하면서도 유형·시간대별로 실행 A를 자동 보수화.
  주의점: 이번 버전은 점수식 전체 교체가 아니라 `MID_PULLBACK` 해석/실행 계층과 자동교정 루프를 추가한 구조화 버전.
- v41.89 (2026-03-20): 눌림목 상한가 도달/잠김 진입 차단 보강.
  [#1] `_get_effective_change_rate()`를 도입해 KIS `change_rate`뿐 아니라 `prev_close` 대비 실계산 등락률을 함께 반영.
  [#2] `_detect_entry_block_reason()`를 확장해 `MID_PULLBACK`/`ENTRY_POINT` 계열은 상한가 잠김(`limit_up_locked`)뿐 아니라
       상한가 도달 자체(`upper_limit_reached`)도 진입불가로 차단하고, `no_ask_liquidity` soft 허용은 기존 예외 조건에서만 유지.
  [#3] `run_mid_pullback_scan()` / `check_entry_watch()`의 진입가 도달 직전 차단 경로가 위 기준을 공통 사용하도록 정리.
  이유: 태웅·태광 같은 사례에서 `현재가=진입가`지만 이미 상한가 또는 실질 체결 곤란 상태인 종목이 눌림목 진입 신호로 노출되는 문제가 있었음.
  개선점: 눌림목 상한가 오알림↓, 실진입 가능성 기준 일관성↑.
  주의점: 일반 급등 포착 신호를 광범위하게 막는 것이 아니라, `MID_PULLBACK`/`ENTRY_POINT` 계열 진입 차단에만 보수 강화.
- v41.88 (2026-03-20): 눌림목 등급 상향 시 쿨다운 리셋 + NXT→KRX 전환 등급 재평가.
  [#1] `run_mid_pullback_scan()` 쿨다운(24h) 내라도 등급이 상향(예: B→A)되면 리셋하여 재알림.
       `_mid_pullback_alert_history`를 `{ts, grade}` 형태로 변경해 이전 등급 추적.
       쿨다운 내 분석을 1회 실행하되, 등급 동일/하향이면 기존 쿨다운 유지.
  [#2] `_register_nxt_surge_to_krx_watch()`에서 NXT→KRX 전환 시 grade/score 재계산.
       `analyze_mid_pullback()` / `check_intraday_pullback_breakout()` 재호출로 최신 등급 반영.
       등급 상향 시 눌림목 쿨다운도 리셋하여 재알림 경로 열림.
       텔레그램 전환 알림에 등급 표시 추가.
  이유: 태웅 사례 — 전날 B등급 포착 후 다음날 NXT에서 상승 지속했으나
       24시간 쿨다운 + NXT전환 등급 미갱신으로 A등급 재알림 불가 → 진입 기회 놓침.
  개선점: 상승 지속 종목 등급 상향 시 적극 진입 유도↑, NXT전환 등급 정확성↑.
  주의점: 쿨다운 내 등급 확인을 위한 추가 분석 1회 발생 (API 호출 소폭 증가).
       등급 동일/하향 시에는 기존 쿨다운 그대로 유지.
- v41.87 (2026-03-20): 메시지 아이콘 3색 체계 통일 (🔴좋음/🟡보통/🔵나쁨).
  [#1] 전체 메시지 아이콘을 3색 신호등 체계로 통일.
       🔴=좋음(상승/수익/강함/매수), 🟡=보통(보합/경계/관망), 🔵=나쁨(하락/손실/약함/매도).
  [#2] 기존 매핑: 🟢(좋음)→🔴, 🔴(나쁨)→🔵, 🟡 유지, 🟠→맥락별 🟡 또는 🔵.
  [#3] NXT 시장 표시(기존 🔵)를 좋음/보통/나쁨 규칙에 통일.
       NXT 매수/강세→🔴, NXT 매도/둔화→🔵, NXT 시스템 라벨→📡.
  [#4] 변환 범위: 코드 영역 155줄, docstring/changelog/주석은 미변경.
  이유: 색상별 의미가 혼재(🔴=나쁨, 🟢=좋음, 🔵=NXT 등)되어 모바일에서 즉시 판단 어려움.
  개선점: 아이콘만으로 좋음/보통/나쁨 즉시 인식↑, NXT 표시 일관성↑.
  주의점: 내부 점수 계산/로직은 변경 없음. 표시(UI) 계층만 수정.
       ✅/⚠️/🚨/💡/🎯 등 기능별 아이콘은 기존 유지.
- v41.86 (2026-03-20): 고아 추적 종목 자동 만료 시스템 도입.
  [#1] `_is_orphan_tracking()` / `_get_valid_tracking()` / `purge_orphan_tracking()` 신규.
       entry/stop/target이 모두 0인 채 "추적중"으로 남은 종목(고아)을 판별·필터·일괄 만료.
       TRACK_MAX_DAYS(5일) 경과 시 "시간초과/고아추적_자동만료"로 강제 종료.
  [#2] 코드 전체에서 "추적중" 목록 조회 7곳에 `_get_valid_tracking()` / `_is_orphan_tracking()` 적용.
       적용 대상: send_overnight_risk_alerts, _send_pending_result_reminder,
       poll_telegram_commands(/weekly, /daily), _send_stats, on_market_close,
       _build_premarket_risk_payload.
  [#3] 봇 시작 시 `purge_orphan_tracking(notify=True)` 자동 호출로 기존 고아 일괄 정리.
  [#4] track_signal_results() 내부에도 고아 감지 시 만료 처리 추가 (장중 실시간 정리).
  이유: 스피어 등 entry/stop/target 미설정 종목이 "추적중"으로 영구 잔류하여
       오버나이트 위험 알림·장전 메시지·장마감 성과에 며칠째 반복 노출.
  개선점: 고아 종목 자동 정리↑, 오버나이트/장전/장마감 메시지 품질↑, 추적 목록 정확성↑.
  주의점: 고아 만료 대상은 entry/stop/target 모두 0인 경우에만 적용.
       만료된 레코드는 status="시간초과"로 변경되어 TRACK_ACTIVE_STATUSES에서 제외 →
       같은 종목이 이후 다시 포착되면 새 레코드로 정상 등록됨 (신규 포착 차단 없음).
- v41.85 (2026-03-20): 미정의 상수 3건 NameError 수정 + 코드 위생 정리.
  [#1] `_exec_speed_cache` 모듈 레벨 선언 누락 수정 → 메인 루프 NameError 해소.
  [#2] `MAX_TELEGRAM_BACKUPS = 5` 상수 추가 → 백업 스케줄 NameError 해소.
  [#3] `KRX_TIME_PARAMS` dict 추가 → get_market_params NameError 방지.
  [#4] 미사용 함수 23개 제거 (303줄 감축).
  [#5] `import re` 중복 import 통합 + 함수 내부 재선언 3곳 제거.
  [#6] Changelog v41.58 이전 이력을 한 줄 요약으로 대체 (수칙 16).
- v41.84 (2026-03-19): 파일 I/O 안전화 + 캐시 정리 + 섹터 개선 + NXT/KRX 명확화.
  [#1] safe_json_load()/safe_json_dump() 함수 추가: with 문 자동화로 "Too many open files" 방지.
  [#2] clean_expired_cache()/reset_daily_caches() 추가: TTL 기반 캐시 정리로 OOM 방지.
  [#3] get_theme_sector_stocks() BREAK 제거: 다중 테마 지원.
  [#4] get_active_market_type()/get_market_params() 추가: NXT/KRX 우선순위 명확화.
  개선점: 파일 안정성↑, 메모리 안정성↑, 섹터 정확성↑.
- v41.83 (2026-03-19): 진입 근거 재검증 + 거래량 동적 기준 + 유동성/수급/DART 메타 보강 + 바닥 재상승 보조판정.
  [#1] `check_entry_watch()`에 `_record_entry_dropped()`/`should_skip_expiration_for_dart_watch()`를 연결해,
       진입가 도달 시점에 신호강도 재약화·거래량 급감(포착 대비 50%↓)이면 내부 기록 후 감시 종료하도록 보강.
       DART 기반 워치는 `shareholder_confirmation_date`가 남아 있으면 근거 재검증 탈락을 면제.
  [#2] `get_effective_volume_ratio()`/`check_liquidity()`를 추가해 `analyze()`의 거래량 기준을 신호유형×시간대별 동적으로 적용하고,
       호가 유동성이 빈약한 종목은 포착 전 보수적으로 차단하도록 정리.
  [#3] `analyze()`에 체결속도 강도, 외국인/기관 부호 전환, 직접뉴스×신호유형, 공매도 저비중(+5) 가점을 통합하고,
       외국인+기관 동시 순매수 가점은 +30으로 상향. 이동평균 정배열 기준은 `5일선>20일선`으로 완화.
  [#4] `register_entry_watch()`와 active watch 복원 경로에 `signal_strength_at_detect`/`execution_speed_at_detect`/
       `pullback_ratio_at_register`/`volume_ratio_at_detect`/`dart_reliability_score`/`shareholder_confirmation_date`/
       `low_price_time` 등 메타데이터를 저장해 후속 판정 근거를 보존.
  [#5] 약한 신호는 이전 사용자 지시대로 `관찰 전용`을 유지하고, 1차 행동 알림 대신 `정책제외`로 내부 기록 후 종료.
       추가로 `confirm_bottom_and_signal()` 보조판정을 붙여 1차 도달 시 바닥 확인/재상승 후보를 짧게 후속 안내.
  이유: 1차 도달 후 근거가 이미 약화된 종목·유동성 부족 종목을 늦게 알리는 문제를 줄이고,
       KIS 실시간 데이터 기준으로 포착 품질과 후속 판단 근거를 한 단계 더 보수적으로 맞추기 위해.
  개선점: 포착 품질↑, 진입 도달 후 탈락 사유 추적↑, DART 워치 보존력↑, 장중/NXT 공통 판단 일관성↑.
  주의점: 바닥 재상승 판정은 보조 메시지이며 기존 1차/2차 구조를 대체하지 않는다. DART 보호는 `shareholder_confirmation_date`가 실제 저장된 건에만 적용된다.
- v41.80 (2026-03-19): 신호 강도 판정 버그 수정 + 동시보유 제한 실적용 + 2차 금지 시 API 절약.
  [#1] register_entry_watch()에 grade/score 저장 추가.
       기존: _entry_watch dict에 grade/score 미저장 → _classify_signal_strength()가 항상
       기본값 "B"/0으로 읽어 score<50 → "약한" 고정 → 1차 비중 25%, 2차 항상 금지.
       수정: s.get("grade")/s.get("score")를 저장해 실제 등급·점수 기반 강도 판정.
  [#2] filter_portfolio_signals()에 max_positions 기반 동시 보유 제한 강제 추가.
       carry_stocks.json에서 현재 보유 종목 수 확인 → max_positions(1) 이상이면
       기존 보유 종목 재진입 신호만 허용, 신규 종목 포착 억제.
  [#3] check_entry_watch() 2차 알림에서 phase2_allowed=False(약한 신호)일 때
       _judge_phase2_entry() 호출 스킵 → 섹터 종목 5개 현재가 조회 절약.
       즉시 "금지" 판정 + 사유 메시지 발송.
  이유: [#1]은 분할진입 비중 규칙의 핵심 전제(신호 강도 분류)가 작동하지 않던 버그.
       [#2]는 1종목 집중 전략이 선언만 되고 실제 필터에서 강제되지 않던 구조적 누락.
       [#3]은 불필요 API 호출 절약으로 KIS API 분당 호출 한도 보호.
  개선점: A등급 강한 신호 → 1차 45%/2차 30% 정상 적용↑, 동시보유 1종목 실제 강제↑,
       약한 신호 2차 알림 시 API 호출 5회 절약↑.
  주의점: carry_stocks.json이 비어있거나 없으면 carry_count=0으로 안전 처리.
       기존 보유 종목 코드와 같은 종목의 재포착 신호는 제한 없이 통과.
- v41.79 (2026-03-18): 점수 라벨 2글자 통일 — 전송 직전 공통 후처리로 시장 주도 섹터/뉴스/리스크/랭킹 요약까지 점수-only 표현 제거.
  [#1] `_score_delta_impact_label()`을 `대가/중가/소가/소감/중감/대감` 기준으로 축약하고, `_signal_total_score_label()`도 `최상/강함/양호/보통/약함/위험` 2글자 체계로 통일.
  [#2] `_risk_total_score_label()` / `_decorate_ui_score_line()` / `_decorate_ui_score_text()`를 추가해, `send()`/`edit_message()`뿐 아니라 `_tg_request()`를 타는 직접 전송 메시지의 `±N점`, `N점` 표현에 짧은 해석 라벨을 공통 적용.
  [#3] 포착 메시지뿐 아니라 `시장 주도 섹터`, `뉴스 요약`, `장전 리스크 평가`, `랭킹/요약` 경로까지 점수-only 표현이 남지 않도록 전송 경로를 단일 후처리 구조로 정리.
  이유: 포착 메시지 일부만 점수 라벨이 붙고 다른 알림은 숫자만 남아 있어, 사용자가 `좋은 점수인지/나쁜 점수인지`를 메시지별로 다르게 해석해야 했기 때문.
  개선점: 전 메시지 점수 해석 일관성↑, 모바일 가독성↑, 시장 주도 섹터/리스크 메시지 판단 속도↑.
  주의점: 내부 점수 계산식은 그대로이고, 이번 변경은 전송 직전 표시 해석 통일에 한정된다.
- v41.78 (2026-03-18): v41.77 중간작업 4종 완성 — DART자사주·야간워치리스트·브리핑·테마발굴 연결.
  [#1] run_dart_intraday() 자사주소각 change_rate 기준 1.0%→0.5% 완화 + 진입감시 즉시 등록.
       DART_BUYBACK_CANCEL 신호타입으로 register_entry_watch/save_signal_log 자동 호출.
  [#2] run_geo_news_scan()/run_overnight_monitor()에서 야간 시간대 뉴스 수집 시
       _extract_overnight_event_keywords()→_build_overnight_watchlist() 자동 연결.
  [#3] _build_premarket_risk_payload()/send_premarket_briefing()에 야간 이벤트 워치리스트 블록 추가.
       _format_overnight_watchlist_block()으로 이벤트별 수혜 종목 표시.
  [#4] run_scan()에서 장 시작 시 overnight_watchlist 종목을 동적 후보군으로 우선 스캔.
       _dispatch_general_alert_signal()에서 change_rate≥5% 포착 시 _discover_new_theme_from_surge() 호출.
  이유: v41.77에서 함수 정의만 완료, 실제 호출 경로 미연결 → 4가지 기능 모두 작동 불가 상태였음.
  개선점: DART 자사주소각 즉시포착↑, 야간이벤트→워치리스트 자동생성↑, 장전 브리핑 정보량↑, 신규테마 자동발굴↑.
  주의점: 야간 워치리스트 종목은 장 시작 시 우선 스캔되나 analyze 점수 미달 시 알림 안 됨(보수적).
- v41.77 (2026-03-18): 테마 자동발굴·NXT추적전환·DART자사주강화·야간워치리스트 자동화 4종 통합.
  [#1] _discover_new_theme_from_surge() 신규: 급등 종목 발생 시 뉴스 키워드 추출 →
       동일 키워드 종목 동반상승 여부 확인 → dynamic_themes.json 자동 저장·적용.
       _auto_reinforce_dynamic_theme()로 기존 동적 테마 성과 반영 강도 자동 조정.
       장중 급등 포착 시 auto_update_theme() 호출 경로에 자동 발굴 엔진 연결.
  [#2] _is_krx_vi_reference_mode() 판정 후 reference_only → 차단 대신
       _register_nxt_surge_to_krx_watch()로 정규장 추적 대상으로 전환 등록.
       NXT에서 선행 급등한 종목을 KRX 정규장 개시 시 자동 감시 대상에 올림.
  [#3] DART_KEYWORDS["강함"]에 "자사주취득","자사주소각","주식소각" 추가.
       run_dart_intraday()에서 자사주소각 공시 감지 시 change_rate 기준 완화(0.5% 이상)
       + 진입감시 즉시 등록 경로 추가. DART_URGENT_KEYWORDS에 "자사주소각","주식소각" 추가.
  [#4] _extract_overnight_event_keywords() 신규: 야간 뉴스에서 GTC/FOMC/실적발표/지정학
       이벤트 키워드 자동 추출 → 관련 국내 종목 매핑 → overnight_watchlist.json 저장.
       _build_premarket_risk_payload() / send_premarket_briefing()에서 워치리스트 로드 →
       장전 브리핑에 "야간 이벤트 수혜 종목" 섹션 자동 포함.
       run_scan()에서 overnight_watchlist 종목을 동적 후보군에 우선 편입.
  이유: 오늘(3/18) 원전/건설·밸류업·방산 종목들이 뉴스 재료가 있었음에도
       하드코딩 테마 미등록·NXT 차단·DART 기준 미달·야간이벤트 미연동으로 포착 실패.
       수동 추가가 아닌 자동 발굴·자동 등록 구조로 전환.
  개선점: 신규 테마 누락↓, NXT 선행상승 종목 정규장 연결↑, 자사주소각 즉시포착↑,
       야간 이벤트 수혜종목 장전 선반영↑.
  주의점: 동적 테마는 당일 유효. overnight_watchlist는 매일 장전 갱신.
       NXT 추적 전환은 KRX 정규장 개시 후 실제 호가 확인까지 보수적으로 유지.
- v41.76 (2026-03-18): 포착 메시지에 현재가/진입가 복원 + 텔레그램 전송 안정화 — 표시 보강과 운영 타임아웃 완화 동시 반영.
  [#1] `_build_capture_focus_price_line()`를 추가해, 일반 포착/눌림목 핵심 메시지 상단에 `현재가`, `진입가`, `현재가가 진입가보다 얼마나 위/아래인지`를 함께 표시하도록 정리.
  [#2] `_build_capture_focus_message()`가 위 가격 라인을 핵심 사유 블록보다 먼저 노출하도록 조정해, 사용자가 `진입가 도달` 알림 전에도 대기 거리를 바로 읽을 수 있게 개선.
  [#3] 전역 `import re`를 명시해, 점수 해석 정규식 초기화 구간에서 `NameError: re`가 발생하지 않도록 정리.
  [#4] 텔레그램 공용 HTTP 헬퍼와 요청별 타임아웃/쿨다운 로그를 추가하고, `sendMessage`, `getUpdates`, `sendDocument`, `deleteMessage`, `answerCallbackQuery` 경로를 공용 헬퍼로 통합해 `Read timed out (10s)` 반복 오류를 완화.
  이유: 메시지 단순화 이후 `현재가`와 `진입가`가 빠져 대기 거리를 판단하기 어려웠고, 동시에 텔레그램 전송 타임아웃이 반복돼 운영 안정성을 해쳤기 때문.
  개선점: 진입 대기 거리 해석 속도↑, 포착 직후 행동 판단력↑, 텔레그램 전송 안정성↑, 동일 오류 로그 폭주↓.
  주의점: 내부 진입가/손절가 계산식은 그대로이며, 텔레그램 전송 실패를 100% 제거하는 것이 아니라 네트워크 지연에 더 보수적으로 대응하도록 완화한 것이다.
- v41.75 (2026-03-18): 점수 해석 라벨 추가 — 사용자 메시지에서 점수의 좋고 나쁨을 바로 읽히게 개선.
  [#1] `_score_delta_impact_label()` / `_signal_total_score_label()` / `_decorate_capture_reason_line()`를 추가해, 포착 메시지의 `+30점`, `-8점` 같은 점수에 `강한 가점/감점`, `약한 가점/감점` 해석 라벨을 함께 표기.
  [#2] `_build_capture_focus_reasons()` / `_build_capture_focus_sector_block()`에 위 라벨을 연결해, 거래량·수급·지지선·섹터 보너스 같은 점수 항목이 숫자만 보이지 않도록 정리.
  [#3] `send_alert()` 컴팩트 모드의 총점 표시에 `_signal_total_score_label()`을 붙여, 총점이 `강함/양호/보통/약함` 중 어느 수준인지 즉시 보이게 개선.
  이유: 사용자 메시지에 점수만 있으면 숫자의 상대적 의미를 알기 어려워, 알림을 받아도 좋은지 나쁜지 해석 시간이 걸렸기 때문.
  개선점: 모바일 가독성↑, 점수 해석 속도↑, 행동 판단 속도↑.
  주의점: 내부 점수 계산식은 그대로이며, 이번 변경은 표시 해석 보강에 한정된다.
- v41.74 (2026-03-18): 전 시간대 실시간 랭킹 후보군 강화 — 08:00~10:00은 강하게, 이후 장중은 보수적으로 후보군/직접스캔 보강.
  [#1] 실시간 랭킹 유니버스 스냅샷(`_get_universe_rank_snapshot`)과 랭킹 후보 수집(`_collect_market_rank_candidates`)을 추가해,
       상승률·상승 거래량·상승 거래대금 상위 종목의 합집합을 KRX/NXT 시장별로 후보군에 반영하도록 정리.
  [#2] 장중 시간대를 `focus(08:00~10:00)` / `session(그 외 장중)`으로 나눠, 장초반은 상위 50(부족 시 100)·짧은 TTL,
       이후는 상위 30·긴 TTL로 운영하는 `시간대 가중형 랭킹 후보군` 구조를 추가.
  [#3] `refresh_dynamic_candidates()`가 기존 거래량/상한가/NXT 급등 후보 외에 실시간 랭킹 후보군을 함께 흡수하도록 확장하고,
       `get_all_scan_candidates()`/`run_scan()`도 동일 랭킹 후보를 직접 참고해 장중 강세주가 동적 후보군 갱신 주기를 기다리지 않도록 보강.
  [#4] `run_scan()`에 시장별 랭킹 직접 스캔 보강을 추가하되, 장초반은 강하게(기본 24개/시장), 이후는 보수적으로(기본 12개/시장) 제한해
       무작정 종목 수만 늘리지 않고 상위권 진입 종목을 우선 확인하도록 정리.
  이유: 오늘 로그처럼 장초반뿐 아니라 장중 전반에서 실제로 순위가 올라오는 종목을 후보군이 늦게 반영하거나,
       기존 거래량/상한가 스캔만으로는 상승 가능 종목을 충분히 넓게 보지 못하는 문제가 있었기 때문.
  개선점: 실시간 강세주 후보 반영 속도↑, 랭킹 기반 누락↓, NXT 포함 장중 전반의 순위 상승 종목 대응력↑.
  주의점: 장중 전 시간대에 랭킹 후보를 보되, 08:00~10:00만 가장 강하게 반영하며 이후 시간대는 과열 추격을 막기 위해 보수적으로 제한한다.
- v41.73 (2026-03-18): 장초반 강세주 누락 완화 — no_ask_liquidity 차단 완화 + 뉴스→종목 직접 승격.
  [#1] `run_scan()`의 일반 포착 경로에서 `no_ask_liquidity`를 무조건 차단하지 않고, 직접뉴스/강한 점수/거래량·섹터 근거가 충분한 경우
       관찰 우선 soft 허용으로 통과시키는 `_should_soft_allow_no_ask_liquidity_general()`과 공용 발송 헬퍼를 추가.
  [#2] `run_news_scan()`에 `뉴스→종목 직접 승격` 경로를 추가해, 테마 반응이 약해도 뉴스에 종목명이 직접 언급되고 장중 가격·거래량 반응이 붙는 종목은
       일반 포착으로 재분석 후 바로 알림/추적까지 이어지도록 정리.
  [#3] `analyze_news_theme()`는 기존 테마 알림을 유지하되, 실제 강세주 승격은 `run_news_scan()`의 종목 직결 경로가 보완하도록 역할을 분리.
  이유: 오늘 로그처럼 장초반 강세주를 이미 감지했는데도 `no_ask_liquidity`로 반복 차단되거나, 뉴스가 테마 반응 부족을 이유로 종목 승격까지 막혀
       실제 주도주를 놓치는 문제가 컸기 때문.
  개선점: 장초반 강세주 생존율↑, 뉴스 언급 종목의 직접 승격력↑, 테마가 늦게 붙는 주도주의 누락↓.
  주의점: soft 허용은 여전히 상한가 잠김(`limit_up_locked`)에는 적용되지 않으며, 뉴스 승격도 가격·거래량 반응이 붙은 종목만 제한적으로 통과한다.
- v41.72 (2026-03-18): 중복 정의 정리 + 기준 파일 동기화 — 최신 정상본 기준으로 코드 블록 단일화.
  [#1] `send_alert()`와 뉴스/섹터 요약 헬퍼 묶음(`_find_cached_deep_news_result`~`_sector_block`)의 동일 중복 정의 2세트를 1세트로 정리.
  [#2] `start_sector_monitor()` 내부 로컬 `_watch_suffix()` 중복 정의를 제거하고 전역 `_watch_suffix()`만 사용하도록 정리.
  [#3] 최신 정상본 기준을 `stock_alert.py`로 다시 동기화하고 `00_BASELINE_POINTER.txt` / `01_HANDOFF.md`를 현재 버전에 맞게 갱신.
  이유: 같은 함수/헬퍼가 여러 번 정의되면 파이썬에서는 나중 정의가 이름을 다시 바인딩해 앞선 정의를 덮어쓰므로, 즉시 문법 오류는 없어도 유지보수와 기준 판정 혼선이 커지기 때문.
  개선점: 기준 파일 단일성↑, 이후 수정 시 덮어쓰기 혼선↓, 함수 수정 누락 리스크↓.
  주의점: 이번 버전은 로직 확장보다 중복 제거와 기준 동기화에 초점을 둔 안정화 버전이다.
- v41.71 (2026-03-18): 버전업 기준본(v41.67)에 누락된 최신 운용 개선 재적용 — v41.68~v41.70 병합.
  [#1] `v41.67` 자동 백업 일 1회 제한 + 텔레그램 최근 5개 유지 로직은 그대로 유지.
  [#2] `v41.68` 재상승 포착(`resurge_mode`) + `no_ask_liquidity` soft 예외 + 대표 진입가 상향 추격 방지 로직을 다시 반영.
  [#3] `v41.69` 눌림목 C등급 실알림 억제/내부기록 유지 + 직접뉴스/재상승 예외 허용을 다시 반영.
  [#4] `v41.70` 포착 메시지 핵심정보 중심 슬림화 포맷을 다시 반영.
  이유: 사용자가 외부에서 버전업한 최신 기준 파일에 최근 반영했던 핵심 개선이 빠져 있어, 기준 파일을 최신 상태로 다시 동기화할 필요가 있었기 때문.
  개선점: 백업 정책 유지, 재상승형 누락 완화, 눌림목 잡음 알림 감소, 포착 메시지 가독성 복원.
  주의점: 이번 버전은 최신 업로드본을 기준으로 최근 누락 개선을 재적용한 병합본이다.
- v41.70 (2026-03-17): 포착 메시지 핵심정보 중심 슬림화 — 중복/내부점수 설명 제거.
  [#1] `_is_capture_focus_reason()` / `_build_capture_focus_reasons()` / `_build_capture_focus_sector_block()` / `_build_capture_focus_message()`를 추가.
       포착 메시지에서 사용자가 실제로 보려는 핵심 항목(등락률, 거래량, 핵심 수급, NXT 수급, 진입 지지선, 체결흐름, 체결속도, 섹터 모멘텀)만 남기도록 정리.
  [#2] 일반 포착 상세 메시지(`send_alert` → `_send_alert_detail`)를 핵심정보 중심 포맷으로 단순화.
       학습보정, 점수 산식, 보조지표, 포지션 가이드, 뉴스 요약, 장황한 부가설명은 기본 포착 메시지에서 제거.
  [#3] `send_mid_pullback_alert()`도 동일한 핵심정보 포맷을 사용하도록 맞춰, 포착 유형이 달라도 사용자 시야에 들어오는 정보 구조를 통일.
  이유: 포착 메시지에 사용자 행동과 직접 관련 없는 중복 설명·내부 점수 문구가 많아 모바일에서 핵심 판단 정보가 묻히고 있었기 때문.
  개선점: 메시지 길이↓, 핵심 판단속도↑, 중복 정보↓, 포착 유형 간 UI 일관성↑.
  주의점: 뉴스 요약/보조지표/포지션 가이드 등 상세 정보는 기본 포착 메시지에서 빠지며, 내부 점수 계산 로직은 그대로 유지된다.
- v41.69 (2026-03-17): 눌림목 C등급 실알림 억제 — 내부 기록 유지 + 재상승/직접뉴스 예외 허용.
  [#1] `run_mid_pullback_scan()`에 `MID_PULLBACK` C등급 실알림 억제 로직을 추가.
       기본은 텔레그램 발송과 진입감시 등록을 생략하고, `save_signal_log()`만 유지해 내부 추적·학습 데이터는 남기도록 정리.
  [#2] `_should_suppress_mid_pullback_c_alert()` / `_enrich_mid_pullback_direct_news()`를 추가.
       C등급이어도 `resurge_mode` 또는 직접뉴스 테마가 있으면 예외 허용해, 신세계I&C·폴라리스AI류 재상승 초입은 막지 않도록 보강.
  [#3] C등급 억제 시에도 동일 쿨다운을 적용해 반복 내부 저장/반복 평가로 인한 잡음 누적을 완화.
  이유: 눌림목 C등급은 행동성보다 참고성 비중이 큰데도 현재는 텔레그램 알림과 진입감시까지 모두 진행돼 메시지 수가 늘었기 때문.
  개선점: 눌림목 저품질 알림 수↓, 내부 학습 데이터 유지, 재상승/직접뉴스형 초기 신호 보존.
  주의점: C등급 눌림목은 기본적으로 외부 알림과 진입감시에서 제외되며, 예외 허용은 `resurge_mode`/직접뉴스 테마에 한정된다.
- v41.68 (2026-03-17): 재상승 포착 보강 + no_ask_liquidity 예외 완화 + 고점 추격식 진입가 갱신 방지.
  [#1] `check_intraday_pullback_breakout()`에 재상승(resurge) 판정을 추가.
       깊은 눌림(기본 15% 이상) 이후 당일 거래량 재유입 + 눌림 회복률 + 저점 대비 반등률을 함께 봐서,
       완전 돌파 전이어도 재상승 초입을 `MID_PULLBACK`으로 포착 가능하게 보강.
  [#2] 재상승형은 현재가 추격 대신 소폭 눌림 기준 진입가를 계산하도록 `_calc_resurge_entry_price()` 추가.
       재상승 감지 시 `resurge_mode`, `pullback_reclaim_ratio`, `entry_soft_block_allowed` 메타를 저장.
  [#3] `run_mid_pullback_scan()` / `check_entry_watch()`에 `no_ask_liquidity` 소프트 예외를 추가.
       직접뉴스/재상승형 `MID_PULLBACK`은 완전 억제 대신 경고를 남기고 추적을 유지해, 상한가 직전 빈 호가로 인한 전면 누락을 완화.
  [#4] 대표 진입가 갱신은 `_select_representative_entry_price()`로 통일.
       `SURGE`/`EARLY_DETECT`/`NEAR_UPPER`/`MID_PULLBACK`/`ENTRY_POINT`는 미체결 상태에서 더 높은 진입가로 덮어쓰지 않고,
       더 낮아질 때만 하향 갱신하도록 보수화.
  [#5] `save_signal_log()` / `register_entry_watch()`가 위 대표 진입가 정책을 공유하고,
       선택된 진입가에 맞춰 손절가·목표가를 재계산하도록 정리.
  이유: 신세계I&C처럼 눌림목 재상승형이 `no_ask_liquidity`로 통째로 사라지거나,
       폴라리스AI류가 재포착 시 대표 진입가가 상향돼 꼭대기 추격처럼 보이는 문제를 줄이기 위함.
  개선점: 깊은 눌림 뒤 재상승 포착률↑, 상한가 근처 빈 호가 전면 누락↓, 고점 추격식 진입가 갱신↓.
  주의점: `no_ask_liquidity` 완화는 `MID_PULLBACK` 재상승/직접뉴스 계열에만 제한 적용되며,
       `limit_up_locked`는 여전히 차단된다.
- v41.67 (2026-03-17): 체결속도 최근성/가속도 보강 — 평균치 편향 완화 + 2차 진입 판단 해석력 개선.
  [#1] `_record_execution_snapshot()`에 `elapsed_sec` / `trade_value_per_sec` 저장을 추가해, 스냅샷 간격 차이로 같은 체결대금이 과대·과소평가되지 않도록 정리.
  [#2] `get_execution_speed_metrics()`에 `recent_trade_value_per_sec`, `prior_trade_value_per_sec`, `acceleration_ratio`, `freshness_score`, `last_active_age_sec`, `flow_state`를 추가해 최근 체결 가속/둔화와 마지막 유효체결 최근성을 함께 평가하도록 확장.
  [#3] 체결속도 점수에 `pace_score`(초당 체결대금), `freshness_bonus`, `accel_bonus`, `stale_penalty`를 반영해 평균 체결대금만 높고 최근 흐름이 죽은 종목의 과대평가를 완화.
  [#4] `_entry_execution_judgement()`를 보강해 최근 유효체결이 오래 끊긴 경우 보류로 낮추고, 예비판단이어도 최근성이 좋은 경우는 '체결 살아있음' 참고 문구를 구분 표시.
  [#5] `_entry_execution_status_block()` / `_judge_phase2_entry()` / `_apply_execution_speed_to_signal()`에 `가속/유지/둔화`, `최근 유효체결 n초 전` 표기를 추가해 메시지 해석력을 높임.
  이유: 기존 체결속도는 평균 체결대금 중심이라 최근 체결이 급약화됐는데도 과거 큰 체결 몇 건 때문에 점수가 유지되거나, 반대로 방금 가속이 붙은 종목이 샘플 부족으로 평평하게 보이는 문제가 있었기 때문.
  개선점: 최근 체결흐름 반영↑, 느려진 종목 과대평가↓, 가속 종목 해석력↑, 2차 진입 판단 품질↑.
  주의점: 체결속도는 여전히 보조지표이며, 실제 진입 차단이 아니라 포착/진입 판단 보강 용도다.
- v41.66 (2026-03-17): 진입가 도달 1차/2차 분할진입 구조 + 자금관리 규칙 코드화 + 1종목 집중.
  [#1] check_entry_watch()의 3회 반복 알림을 1차(초기진입)+2차(추가진입 판단) 2단계 분리 구조로 변경.
       1차: 신호강도별 권장비중(강한 45%/보통 35%/약한 25%) + 손절가 + 목표가 + 체결속도.
       2차: 눌림유지/체결속도/손절여유/섹터모멘텀 4개 조건 평가 → 가능/보류/금지 판정.
       추가비중 + 누적비중 + 평균단가 예상 표시.
  [#2] _classify_signal_strength() 신규: 등급(A/B/C)+체결속도+점수 기반 '강한/보통/약한' 분류.
  [#3] ENTRY_SPLIT_RULES 테이블 + _get_entry_split_rule() 신규: 신호강도별 분할비중 규칙.
       강한: 1차45%/2차30%/여유25%, 보통: 35%/25%/40%, 약한: 25%/0%(2차금지)/75%.
  [#4] _judge_phase2_entry() 신규: 2차 추가진입 가능 여부를 4개 조건으로 판정.
       ① 눌림유지 ② 체결속도 악화 없음 ③ 손절가 여유 ④ 섹터 모멘텀 유지.
       fail 2개↑=금지, 1개=보류, 0개=가능.
  [#5] REGIME_PARAMS max_positions 전체 1종목으로 변경 (소액 집중 전략).
  [#6] calc_position_size() 확장: 1종목 집중 + phase1_pct/phase2_pct/strength 반환 추가.
  [#7] track_signal_results() 손절가 도달 메시지에 "포지션 정리 신호" 감축/청산 가이드 추가.
       추가매수 금지, 보유분 즉시 정리, 재진입은 새 포착 기준으로만.
  이유: 투자금 10만원 소액으로 연 30% 이상 수익률을 빠르게 달성하려면 1종목에 집중하고
       수수료 등 제반비용을 최소화하며 분할진입으로 리스크를 관리해야 하기 때문.
  개선점: 진입 알림이 행동 가능한 비중 정보 포함↑, 2차 추가진입 판단 자동화↑,
       1종목 집중으로 분산 손실↓, 손절 시 명확한 정리 가이드↑.
  주의점: 2차 알림은 약한 신호 시 자동 금지됨. 기존 3회 반복은 2회(1차+2차)로 축소.
       max_positions=1이므로 동시 보유 종목 제한 강화됨.
- v41.65 (2026-03-17): 신규 이슈주 묻힘 완화 — 직접뉴스 테마 보강 + 섹터 게이트 정렬/판정 수정.
  [#1] `THEME_MAP`에 `AI인프라`, `공공안전AI` 테마를 추가해 신세계I&C(035510) / 폴라리스AI(039980) 같은
       직접 이슈 종목이 `기타`에 묻히지 않고 뉴스 스캔·테마 분류에 바로 연결되도록 보강.
  [#2] `DIRECT_NEWS_THEME_RULES`와 `_infer_direct_news_theme()`를 추가해, 종목 개별 뉴스 헤드라인에서
       데이터센터·소버린AI·AXON·안티드론·오픈AI/BAA 같은 직접 재료를 읽어 테마/보너스를 보강.
  [#3] `analyze()` / `check_early_detection()`에 직접뉴스 테마 보강을 연결해, 기존 `기타업종` 종목도
       강한 개별 이슈가 있으면 `sector_theme`와 점수에 반영되도록 정리.
  [#4] `run_scan()`의 섹터 제한 전에 점수·직접뉴스·비기타 우선 정렬을 추가하고, 섹터 판정을
       `sector_theme` 우선 → `sector_info.theme` fallback으로 교정. `기타` 버킷은 4개까지 완화.
  이유: 오늘 신세계I&C는 직접뉴스가 있었는데 정적 테마에 연결되지 못했고, 폴라리스AI는 실제 후보군에 있었지만
       `기타` 5번째로 밀려 늦게 알림이 갔기 때문. 직접뉴스가 있는 강한 종목을 먼저 통과시키되,
       무분별한 알림 증가는 막기 위해 `기타`만 제한적으로 완화했다.
  개선점: 개별 재료주 뉴스 연동력↑, `기타` 버킷 병목↓, 강한 종목의 늦은 통과/누락↓.
  주의점: 직접뉴스 테마는 키워드 기반 보강이므로, 전혀 새로운 유형의 이슈는 여전히 `기타`로 남을 수 있다.
- v41.64 (2026-03-17): NXT 전용 파라미터 분리 — 시간대별 4단계 차등 적용.
  [#1] NXT_TIME_PARAMS 테이블 추가: pre(08~09)/overlap(09~15:30)/post_early(15:30~17)/post_late(17~20)
       각 시간대별 score_mult/min_add/cooldown_mult/stop_mult/target_mult/position_mult 정의.
  [#2] get_nxt_time_slot()/get_nxt_params() 헬퍼 함수 추가.
  [#3] analyze()에 NXT 시간대별 최소점수 보정 + 점수 배율 적용.
  [#4] calc_dynamic_stop_target()에 NXT 시간대별 손절/목표 배수 세분화.
  [#5] calc_position_size()에 NXT 시간대별 포지션 비중 배수 세분화.
  [#6] get_regime_cooldown()에 NXT 시간대별 쿨다운 배수 적용.
  이유: 스킬의 "NXT 전용 전략" 강화 영역 실제 반영. NXT 08~09 장전은 유동성 매우 낮아
       보수적으로, 15:30~17 장후 초반은 적당히, 17~20 야간은 가장 보수적으로 자동 전환.
  개선점: NXT 4개 시간대 × 6개 파라미터 = 24개 조합이 자동 적용.
  주의점: KRX+NXT 겹치는 09~15:30은 overlap으로 보정 없음 (기존과 동일).
- v41.63 (2026-03-17): signal_log 피드백 루프 강화 — 포착→진입→결과 파이프라인 KPI 자동 분석.
  [#1] compute_signal_kpi() 신규 함수: signal_log 기반 승률/손익비/기대수익 KPI 자동 계산.
       신호유형별·레짐별·시간대별 세분화 KPI를 dict로 반환.
  [#2] _check_strategy_health() 신규 함수: KPI 기반 전략 건강도 자동 판정.
       승률<35% 또는 손익비<1.0이면 해당 신호유형 자동 기준 강화 제안.
       연속 손절 5회 이상이면 긴급 경고 발송.
  [#3] auto_tune()에 피드백 루프 통합: 장마감 후 compute_signal_kpi() → _check_strategy_health()
       → 조건 자동 조정 또는 사용자 알림 경로 추가.
  [#4] /stats 명령 강화: 기존 통계에 KPI 요약 (승률/손익비/기대수익) 추가 표시.
  이유: 스킬의 "signal_log 백테스트 기준" 강화 영역 실제 반영.
       포착→진입→결과 파이프라인에 자동 피드백 루프를 구축하여 전략 자기 최적화 가속.
  개선점: 수익률 30% 목표 달성을 위한 자동 전략 조정 루프 완성.
  주의점: KPI 계산은 최소 10건 이상 완료 데이터 필요. 미달 시 "데이터 부족" 표시.
- v41.62 (2026-03-17): 동적 손절선 고도화 — 신호유형별·변동성별 차등 적용.
  [#1] calc_stop_target → calc_dynamic_stop_target 위임으로 통합.
       기존 9곳의 레거시 호출부가 자동으로 레짐+신호유형+변동성 고도화 적용.
  [#2] calc_dynamic_stop_target에 SIGNAL_STOP_PARAMS(신호유형별 손절·익절 배수)
       + 종목 ATR 변동성 구간(저/중/고) 보정 추가.
  [#3] calc_trailing_stop에 변동성 구간 기반 트레일링 폭 자동 조정.
       저변동 종목은 타이트, 고변동 종목은 여유 있게.
  [#4] SIGNAL_STOP_PARAMS 테이블 추가 (8개 신호유형별 손절·익절 배수 정의).
  이유: 스킬의 "종목별 변동성 기반 동적 손절선" 강화 영역 실제 반영.
  개선점: 신호유형별 손절·익절 차등 + 변동성 구간 자동 조절로 손익비 개선.
  주의점: calc_stop_target 시그니처에 signal_type 옵션 파라미터 추가 (기본값 None → 하위호환).
- v41.61 (2026-03-16): 시장 레짐별 전략 전환 강화 — 6개 영역 통합 업그레이드.
  [#1] get_market_regime()에 레짐별 파라미터 대응표(REGIME_PARAMS) 통합 반환 추가.
  [#2] calc_partial_exit_min_pct()에 레짐별 분할 청산 트리거 차등 적용.
  [#3] analyze() 내 진입가 계산 시 레짐별 ENTRY_PULLBACK_RATIO 동적 조정.
  [#4] ALERT_COOLDOWN을 get_regime_cooldown() 함수로 대체.
  [#5] 레짐 전환 시 텔레그램 1회 알림 발송 (_notify_regime_change).
  [#6] calc_overnight_risk()에 한국 시장 레짐 반영 (bear/crash +15/+25점).
  이유: 스킬의 "시장 레짐별 전략 전환" 강화 영역을 코드에 실제 반영.
  개선점: 레짐 전환 시 6개 파라미터가 동시에 연동되어 일관된 전략 대응 가능.
  주의점: 기존 ALERT_COOLDOWN 참조 → get_regime_cooldown()으로 대체됨.
- v41.60 (2026-03-16): 원본 v41.59 기준 야간 모니터링/장전 브리핑 핫픽스 적용.
  [#1] 수정 기준 파일을 사용자 업로드 원본(v41.59)으로 재정렬해, v41.56~v41.59 기능 누락 없이 최신 로직 위에 핫픽스가 얹히도록 정리.
  [#2] 20:10 `sys.exit(0)` 자동 종료 스케줄을 제거하고 야간 모니터링 모드 전환 로그만 남기도록 변경.
  [#3] `run_overnight_monitor()`의 시간 판정을 KST 기준 `20:10~07:30` 비교로 교정해 21:00~23:59 누락을 해소.
  [#4] `_build_premarket_risk_payload()`가 파일 기반 지정학/오버나이트 상태(`_get_effective_geo_state`, `_get_effective_overnight_lines`)를 직접 읽어 07:30 메시지에 `야간 이슈 요약`을 안정적으로 반영하도록 보강.
  [#5] `send_premarket_briefing()`도 동일한 파일 기반 상태를 읽어 재시작/버퍼 비움 이후에도 08:50 브리핑에 야간 이벤트를 안정적으로 반영하도록 보강.
  이유: 장마감 후에도 봇을 살려 두고 지정학/해외시장/야간 이슈를 계속 모니터링해 다음날 장전 메시지에 빠짐없이 반영하기 위함.
- v41.59 (2026-03-13): 시작 배너를 leader 승계 시점에도 1회 발송하도록 보강.
  [#1] `_send_startup_banner_once()` helper와 `_STARTUP_BANNER_SENT` 상태를 추가해, 기존처럼 부팅 순간 leader일 때뿐 아니라
       passive로 시작한 replica가 나중에 leader 락을 승계했을 때도 시작 배너를 정확히 1회 발송하도록 정리.
  [#2] `_leader_job()`에서 이전 runtime leader 상태를 보고 `passive → leader` 전환이 감지되면 스케줄 작업 실행 전에
       시작 배너 전송 helper를 먼저 호출하도록 연결.
  [#3] 메인 진입부의 시작 배너 문자열은 helper로 통합해, 부팅 직후 leader 획득과 이후 leader 승계가 같은 메시지 포맷을 사용하도록 정리.
  이유: 현재 구조에서는 부팅 순간 `_try_acquire_leader_lock()`이 실패하면 이후 실제 leader가 되어도 시작 배너가 다시 전송되지 않아
       `🤖 주식 급등 알림 봇 ON` 메시지가 누락될 수 있었기 때문.
  개선점: Railway 다중 replica 환경에서 시작 배너 누락↓, leader 승계 가시성↑, 메시지 포맷 일관성↑.
  주의점: 시작 배너는 프로세스당 1회만 발송되며, leader 재획득이 반복돼도 중복 발송되지 않음.
- v39.4 ~ v41.58: 이전 이력 생략 (운영 로그/백업 기준으로 관리).
[후속 AI 인계 메모]
- 목적: 이 섹션은 모델이 바뀌어도 다음 수정 AI가 바로 이해하도록 남기는 내부 인수인계 기록이다.
- v40.1 DART 호환 포인트:
  - _scan_recent_dart_materials()는 아직 _lookup_name_by_code(code)를 호출한다.
  - _lookup_name_by_code()는 레거시 호출 호환용 래퍼이며, 실제 종목명 복구는 _resolve_stock_name()이 담당한다.
  - 따라서 신규 코드에서는 _resolve_stock_name() 사용을 우선하되, 기존 호출부를 한 번에 정리하기 전까지는 _lookup_name_by_code()를 제거하지 말 것.
- v40.1 운영 알림 포인트:
  - run_overnight_monitor(): alerts가 있어도 텔레그램 send(msg)를 하지 않는다. 내부 요약/로그만 유지하는 설계다.
  - run_geo_news_scan(): is_any_market_open()일 때만 발송하며, _geo_event_state['last_sent_msg']와 동일한 내용이면 재발송하지 않는다.
  - update_dashboard(force=False): 함수 시작부에서 is_any_market_open()이 아니면 즉시 return 한다.
- v40.8 메시지/UI 포인트:
  - send_alert(), send_mid_pullback_alert()는 핵심 사유 → 진입 박스 → 섹터 블록 → 뉴스 요약 → 경고/보조 블록 순서로 정렬된 기준 버전이다.
  - 별도 news_block_for_alert() 후속 텔레그램은 더 이상 기본 호출되지 않는다. 뉴스는 포착 메시지 내부 `📰 뉴스 요약` 블록에서 본다.
  - analyze() 경로는 news_analysis/news_articles payload를 함께 싣고, 조기포착/눌림목처럼 사전 계산이 없는 경로는 `_build_news_summary_block(..., allow_fetch=True)`가 헤드라인 기반 빠른 요약을 붙인다.
  - UI 중복 제거는 표시 단계에서만 수행한다. reasons 원본은 학습/로그용으로 유지되므로, 점수 계산 또는 save_signal_log()쪽 로직과 혼동하지 말 것.
- v40.6 섹터 재안내 포인트:
  - alert-origin(start_sector_monitor(..., from_alert=True)) 경로는 더 이상 별도 [종목 섹터 모니터링] 텔레그램을 보내지 않는다.
  - 처음 포착 때 sector_info가 요약/동반상승 기준으로 비어 있던 종목만 재안내 후보가 된다.
  - 재안내 제목은 🔁 [섹터 미반영 종목 재안내]로 고정되며, 본문은 기존 포착 메시지 전체 + 새 섹터 블록이다.
  - 재안내는 포착 후 30분 이내, 진입 의미 유지, 원신호 훼손 없음, 진입가 도달 후 한참 경과하지 않음, 섹터 요약/동반상승 확보를 모두 만족할 때만 1회 허용된다.
- v40.4 메시지 표기 포인트:
  - [진입가 도달!]은 섹터 모멘텀만 추가된 기준 버전이다. 진입가 도달가/시각 상세는 넣지 않는다.
  - [분할 청산 타이밍], [자동 추적 결과]는 진입가 + 도달시각만 표시한다.
  - [목표가 도달 → 트레일링 모드]만 진입가 + 도달가 + 도달시각을 모두 표시한다.
  - v40.3에서 넓게 넣었던 진입가 도달 상세 표기안은 폐기되었으므로, 후속 수정 기준 버전은 v40.4로 본다.
- 추가 수정 시 필수 기록 규칙:
  - 버전(Version) 반드시 변경.
  - 파일 내부 변경 이력(이 상단 docstring) 반드시 갱신.
  - 외부 변경 이력 문서와 의미가 어긋나지 않게 유지.
  - 다음 AI가 이해할 수 있도록 '수정 함수/수정 이유/영향/주의점/호환 포인트'를 함께 기록.
- 실무 주의:
  - 불필요한 사용자 알림 추가보다, 행동 가능한 알림 품질과 중복 축소를 우선한다.
  - '근접' 같은 모호한 표현보다 실제 도달/실제 충족 기준을 우선한다.
  - 오류 수정은 오류본 덧패치보다 마지막 안정본 기준 재수정을 우선한다.
[참고]
- 더 오래된 변경 이력은 운영 로그/백업 기준으로 관리.
"""
# 공용 신호 라벨/표현 (v38.3: 복원 — v38.2에서 누락되어 NameError 유발)
SIG_LABELS = {
    "UPPER_LIMIT": "상한가", "NEAR_UPPER": "상한가근접", "SURGE": "급등",
    "EARLY_DETECT": "조기포착", "MID_PULLBACK": "눌림목",
    "ENTRY_POINT": "눌림목", "STRONG_BUY": "강력매수",
    "PRECLOSE_GAP_ENTRY": "종가선진입",
}
SIG_TITLES = {
    "UPPER_LIMIT": "상한가 감지", "NEAR_UPPER": "상한가 근접",
    "SURGE": "급등 감지", "EARLY_DETECT": "★ 조기 포착 - 선진입 기회 ★",
    "MID_PULLBACK": "눌림목 진입 신호", "ENTRY_POINT": "★ 눌림목 진입 시점 ★",
    "STRONG_BUY": "강력 매수 신호",
    "PRECLOSE_GAP_ENTRY": "★ 익영업일 갭상승 실전 선진입 ★",
}
def get_signal_label(signal_type: str, default: str = "") -> str:
    return SIG_LABELS.get(str(signal_type or ""), default or str(signal_type or ""))
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
import builtins
import hashlib
import logging
import traceback
import re as _re  # docstring 파싱 등 초기화 단계 사용
re = _re            # 이후 코드에서 re.xxx 사용 호환
# === Regime label localization (Korean) ===
# v40.0: 4단계 통일 — crash/bear/normal/bull (한글: 급락장/약세장/보통장/강세장)
REGIME_KO_MAP = {
    "risk_on": "강세장",
    "bull": "강세장",
    "neutral": "보통장",
    "normal": "보통장",
    "risk_off": "약세장",
    "bear": "약세장",
    "panic": "급락장",
    "crash": "급락장",
    "unknown": "보통장",
}
def regime_label_ko(label: str) -> str:
    try:
        return REGIME_KO_MAP.get((label or "").strip().lower(), "보통장")
    except Exception as e:
        _swallow_exception(e)  # v105 structured silent-exception log
        return "보통장"
# --- Global state defaults (to prevent NameError at runtime) ---
GEO_SECTOR_BIAS: dict = {}
# MARKET_REGIME: 176줄에서 1회만 선언 (v38.3: 중복 제거)
# --- HOTFIX: safe response JSON parsing (prevents JSONDecodeError / empty responses) ---
def safe_json_response(resp):
    """Return parsed JSON safely; invalid/empty/HTML bodies become {} without JSONDecodeError noise."""
    try:
        txt = (getattr(resp, "text", "") or "")
        if not txt or not txt.strip():
            return {}
        txt = txt.strip()
        ct = str((getattr(resp, "headers", {}) or {}).get("Content-Type", "") or "").lower()
        if txt.startswith("<"):
            return {}
        if "json" not in ct and not txt.startswith("{") and not txt.startswith("["):
            return {}
        try:
            parsed = json.loads(txt)
            return parsed if isinstance(parsed, (dict, list)) else {}
        except Exception:
            return {}
    except Exception:
        return {}

    return {"krx_open": krx_open, "nxt_open": nxt_open, "strict_tag": strict_tag, "mkt_tag": mkt_tag}
def _normalize_scan_signal_code(payload: dict | None = None, fallback_code: str | None = None) -> str:
    code = normalize_stock_code((payload or {}).get("code", ""))
    if code:
        return code
    return normalize_stock_code(fallback_code or "")
RUN_SCAN_REPAIR_RETRY_SEC = int(os.getenv("RUN_SCAN_REPAIR_RETRY_SEC", "35") or "35")
RUN_SCAN_REPAIR_MAX_ATTEMPTS = int(os.getenv("RUN_SCAN_REPAIR_MAX_ATTEMPTS", "3") or "3")
RUN_SCAN_REPAIR_ALERT_AFTER = int(os.getenv("RUN_SCAN_REPAIR_ALERT_AFTER", "2") or "2")
_run_scan_repair_queue: dict[str, dict] = {}

def _build_run_scan_missing_reasons(payload: dict | None = None) -> list[str]:
    item = payload if isinstance(payload, dict) else {}
    reasons = []
    code = _normalize_scan_signal_code(item)
    if not code:
        return ["missing_code"]
    if _looks_like_placeholder_stock_name(code, str(item.get("name", "") or "")):
        reasons.append("missing_name")
    if safe_int(item.get("price", 0), 0) <= 0 and max(
        safe_int(item.get("ask_price", 0), 0),
        safe_int(item.get("bid_price", 0), 0),
        safe_int(item.get("entry_price", 0), 0),
        safe_int(item.get("planned_entry_price", 0), 0),
        safe_int(item.get("execution_hint_entry_price", 0), 0),
        safe_int(item.get("prev_close", 0), 0),
        safe_int(item.get("open", 0), 0),
    ) <= 0:
        reasons.append("missing_price")
    if not str(item.get("signal_type") or "").strip():
        reasons.append("missing_signal_type")
    if safe_int(item.get("score", 0), 0) <= 0:
        reasons.append("missing_score")
    sector_theme = str(item.get("sector_theme") or (item.get("sector_info") or {}).get("theme") or "")
    if _is_generic_sector_theme(sector_theme):
        reasons.append("missing_sector")
    if _needs_run_scan_payload_repair(item):
        reasons.append("needs_repair")
    uniq=[]
    seen=set()
    for r in reasons:
        if r in seen:
            continue
        seen.add(r)
        uniq.append(r)
    return uniq

def _queue_run_scan_repair(item: dict | None = None, *, reasons: list[str] | None = None, stage: str = "") -> bool:
    payload = dict(item or {})
    code = _normalize_scan_signal_code(payload)
    if not code:
        return False
    now_ts = time.time()
    rec = _run_scan_repair_queue.get(code) if isinstance(_run_scan_repair_queue.get(code), dict) else {}
    rec["code"] = code
    rec["payload"] = payload
    rec["first_ts"] = float(rec.get("first_ts") or now_ts)
    rec["last_ts"] = now_ts
    rec["next_ts"] = float(rec.get("next_ts") or (now_ts + RUN_SCAN_REPAIR_RETRY_SEC))
    rec["attempts"] = int(rec.get("attempts") or 0)
    rec["alerted"] = bool(rec.get("alerted"))
    rec["stage"] = str(stage or rec.get("stage") or "")
    rec["reasons"] = list(reasons or _build_run_scan_missing_reasons(payload))
    _run_scan_repair_queue[code] = rec
    return True

def _emit_run_scan_code_change_request(rec: dict | None = None) -> bool:
    rec = rec if isinstance(rec, dict) else {}
    code = _normalize_scan_signal_code(rec.get("payload") or {}, fallback_code=rec.get("code"))
    if not code:
        return False
    payload = rec.get("payload") if isinstance(rec.get("payload"), dict) else {}
    name = str(payload.get("name", "") or "").strip()
    reasons = list(rec.get("reasons") or [])
    lines = [
        "🛠 [코드수정 요청] run_scan 결측 복구 실패",
        f"• 종목: {name or code} ({code})",
        f"• 누적 재시도: {int(rec.get('attempts') or 0)}회",
        f"• 미복구 사유: {', '.join(reasons) if reasons else 'unknown'}",
        "• 점검 대상: _repair_run_scan_payload / _coerce_run_scan_signal_defaults / _append_scan_alert",
    ]
    return _send_code_change_request_alert(f"run_scan_incomplete:{code}", lines, cooldown_min=180)

def _drain_run_scan_repair_queue(alerts: list, seen: set) -> None:
    if not _run_scan_repair_queue:
        return
    now_ts = time.time()
    due_codes = [code for code, rec in list(_run_scan_repair_queue.items()) if isinstance(rec, dict) and float(rec.get("next_ts") or 0.0) <= now_ts]
    for code in due_codes[:30]:
        rec = _run_scan_repair_queue.pop(code, None)
        if not isinstance(rec, dict):
            continue
        payload = rec.get("payload") if isinstance(rec.get("payload"), dict) else {"code": code}
        repaired = _coerce_run_scan_signal_defaults(payload, fallback_code=code)
        if bool(repaired.get("_scan_payload_incomplete")):
            rec["payload"] = repaired
            rec["attempts"] = int(rec.get("attempts") or 0) + 1
            rec["reasons"] = _build_run_scan_missing_reasons(repaired)
            rec["next_ts"] = now_ts + RUN_SCAN_REPAIR_RETRY_SEC
            _run_scan_repair_queue[code] = rec
            if rec["attempts"] >= RUN_SCAN_REPAIR_ALERT_AFTER and not bool(rec.get("alerted")):
                rec["alerted"] = bool(_emit_run_scan_code_change_request(rec))
                _run_scan_repair_queue[code] = rec
            continue
        _append_scan_alert(alerts, seen, repaired, hist_key=code, seen_code=code)

def _needs_run_scan_payload_repair(payload: dict | None = None) -> bool:
    item = payload if isinstance(payload, dict) else {}
    code = _normalize_scan_signal_code(item)
    if not code:
        return False
    signal_type = str(item.get("signal_type") or "").strip().upper()
    score = safe_int(item.get("score", 0), 0)
    change_rate = safe_float(item.get("change_rate", 0.0), 0.0)
    volume_ratio = safe_float(item.get("volume_ratio", 0.0), 0.0)
    return signal_type in ("", "UNKNOWN") or score <= 0 or (abs(change_rate) < 0.01 and volume_ratio <= 0.0)

def _build_fallback_scan_signal_type(item: dict) -> str:
    signal_type = str(item.get("signal_type") or "").strip().upper()
    if signal_type not in ("", "UNKNOWN"):
        return signal_type
    change_rate = safe_float(item.get("change_rate", 0.0), 0.0)
    volume_ratio = safe_float(item.get("volume_ratio", 0.0), 0.0)
    joined = " ".join([str(item.get("desc") or ""), str(item.get("theme_desc") or ""), " ".join(map(str, item.get("reasons") or []))]).upper()
    has_live = safe_int(item.get("price", 0), 0) > 0 and bool(str(item.get("name", "") or "").strip())
    if change_rate >= UPPER_LIMIT_THRESHOLD:
        return "NEAR_UPPER"
    if change_rate >= max(PRICE_SURGE_MIN, 4.0) or volume_ratio >= max(3.0, COMMON_THRESHOLD_3P0):
        return "SURGE"
    if change_rate >= max(0.8, _early_price_min_dynamic) and volume_ratio >= max(1.2, _early_volume_min_dynamic * 0.7):
        return "EARLY_DETECT"
    if any(token in joined for token in ("MID_PULLBACK", "재상승", "시가회복", "박스돌파", "박스지지")):
        return "MID_PULLBACK"
    if has_live and any(token in joined for token in ("랭킹후보", "자동편입", "NXT장후리더", "THEME_FEEDBACK", "ADAPTIVE_FEEDBACK", "PREWATCH", "리더")):
        return "EARLY_DETECT"
    if has_live and (bool(item.get("direct_news_hit")) or bool(item.get("theme_chain_force_hit")) or bool(item.get("material_first_priority_hit"))):
        return "EARLY_DETECT"
    return ""

def _build_fallback_scan_score(item: dict, signal_type: str = "") -> int:
    score = safe_int(item.get("score", 0), 0)
    if score > 0:
        return score
    change_rate = safe_float(item.get("change_rate", 0.0), 0.0)
    volume_ratio = safe_float(item.get("volume_ratio", 0.0), 0.0)
    sig = str(signal_type or item.get("signal_type") or "").upper()
    has_live = safe_int(item.get("price", 0), 0) > 0 and bool(str(item.get("name", "") or "").strip())
    meaningful_theme = not _is_generic_sector_theme(str(item.get("sector_theme") or (item.get("sector_info") or {}).get("theme") or ""))
    base = 0
    if sig == "UPPER_LIMIT":
        base = 90
    elif sig == "NEAR_UPPER":
        base = 82
    elif sig == "SURGE":
        base = 62
    elif sig == "MID_PULLBACK":
        base = 58
    elif sig == "EARLY_DETECT":
        base = 54
    elif has_live and (meaningful_theme or bool(item.get("direct_news_hit")) or bool(item.get("material_first_priority_hit"))):
        base = 46
    base += min(18, max(0, int(abs(change_rate) * 1.4)))
    base += min(14, max(0, int(volume_ratio * 2.5)))
    if has_live and str(item.get("market", "") or "").upper() == "NXT":
        base += 2
    return max(0, min(99, base))

def _repair_run_scan_payload(payload: dict | None = None, fallback_code: str | None = None) -> dict:
    item = dict(payload or {})
    code = _normalize_scan_signal_code(item, fallback_code=fallback_code)
    if not code:
        return item
    item["code"] = code
    market = "NXT" if str(item.get("market", "") or "").upper() == "NXT" else "KRX"
    if _needs_run_scan_payload_repair(item):
        try:
            quote = get_nxt_stock_price(code) if market == "NXT" else get_stock_price(code)
        except Exception as e:
            _swallow_exception(e)
            quote = {}
        if isinstance(quote, dict) and quote.get("price"):
            for key in ("name", "price", "change_rate", "volume_ratio", "today_vol", "market", "open", "prev_close", "ask_qty", "bid_qty", "ask_price", "bid_price", "bstp_code", "bstp_name"):
                if quote.get(key) not in (None, "", 0):
                    item[key] = quote.get(key)
        item["change_rate"] = _get_effective_change_rate(item, safe_int(item.get("price", 0), 0))
        try:
            analyzed = analyze(item)
        except Exception as e:
            _swallow_exception(e)
            analyzed = {}
        if isinstance(analyzed, dict) and _normalize_scan_signal_code(analyzed, fallback_code=code) == code:
            merged = dict(item)
            merged.update(analyzed)
            if item.get("market") and not merged.get("market"):
                merged["market"] = item.get("market")
            merged_reasons = list(item.get("reasons") or []) + list(analyzed.get("reasons") or [])
            if merged_reasons:
                uniq = []
                seen_reason = set()
                for reason in merged_reasons:
                    key = str(reason)
                    if key in seen_reason:
                        continue
                    seen_reason.add(key)
                    uniq.append(reason)
                merged["reasons"] = uniq
            item = merged
    public_meta = _get_public_stock_meta(code)
    if not str(item.get("name") or "").strip() or _looks_like_placeholder_stock_name(code, str(item.get("name") or "")):
        public_name = str((public_meta or {}).get("name", "") or "").strip()
        item["name"] = _resolve_stock_name(code, public_name or item.get("name", ""))
    if safe_int(item.get("price", 0), 0) <= 0:
        for price_key in ("ask_price", "bid_price", "entry_price", "planned_entry_price", "execution_hint_entry_price", "open", "prev_close"):
            candidate = safe_int(item.get(price_key, 0), 0)
            if candidate > 0:
                item["price"] = candidate
                break
    bstp_name = str(item.get("bstp_name") or (item.get("sector_info") or {}).get("bstp_name") or "").strip()
    public_sector = _normalize_public_sector_name((public_meta or {}).get("sector", ""))
    sector_info = item.get("sector_info") if isinstance(item.get("sector_info"), dict) else {}
    if not bstp_name and public_sector and not _is_generic_sector_theme(public_sector):
        bstp_name = public_sector
    if bstp_name and not _is_generic_sector_theme(bstp_name):
        sector_info["theme"] = str(sector_info.get("theme") or bstp_name) if _is_generic_sector_theme(str(sector_info.get("theme") or "")) else str(sector_info.get("theme") or "")
        sector_info["bstp_name"] = bstp_name
        item["sector_info"] = sector_info
        if _is_generic_sector_theme(str(item.get("sector_theme") or "")):
            item["sector_theme"] = sector_info.get("theme", bstp_name)
    signal_type = _build_fallback_scan_signal_type(item)
    if signal_type and str(item.get("signal_type") or "").strip().upper() in ("", "UNKNOWN"):
        item["signal_type"] = signal_type
    if safe_int(item.get("score", 0), 0) <= 0:
        item["score"] = _build_fallback_scan_score(item, signal_type=str(item.get("signal_type") or signal_type or ""))
    if not str(item.get("grade") or item.get("execution_grade") or "").strip():
        score = safe_int(item.get("score", 0), 0)
        grade = "A" if score >= 80 else "B" if score >= 60 else "C"
        item["grade"] = grade
        item["execution_grade"] = grade
    missing_reasons = _build_run_scan_missing_reasons(item)
    item["_scan_payload_incomplete"] = bool([r for r in missing_reasons if r != "needs_repair"])
    item["_scan_payload_missing_reasons"] = [r for r in missing_reasons if r != "needs_repair"]
    if item["_scan_payload_incomplete"]:
        item.setdefault("reasons", []).append(f"⚠️ 결측 재복구 대기 ({', '.join(item['_scan_payload_missing_reasons'])})")
    return item

def _coerce_run_scan_signal_defaults(payload: dict | None = None, fallback_code: str | None = None) -> dict:
    item = _repair_run_scan_payload(payload, fallback_code=fallback_code)
    code = _normalize_scan_signal_code(item, fallback_code=fallback_code)
    if code:
        item["code"] = code
    item["change_rate"] = safe_float(item.get("change_rate", 0.0), 0.0)
    item["volume_ratio"] = safe_float(item.get("volume_ratio", 0.0), 0.0)
    item["score"] = safe_int(item.get("score", 0), 0)
    item["price"] = safe_int(item.get("price", 0), 0)
    item["today_vol"] = safe_int(item.get("today_vol", 0), 0)
    item["entry_price"] = safe_int(item.get("entry_price", 0), 0)
    item["planned_entry_price"] = safe_int(item.get("planned_entry_price", item.get("entry_price", 0)), 0)
    item["execution_hint_entry_price"] = safe_int(item.get("execution_hint_entry_price", 0), 0)
    item["stop_loss"] = safe_int(item.get("stop_loss", 0), 0)
    item["target_price"] = safe_int(item.get("target_price", 0), 0)
    item["market"] = str(item.get("market", "") or "")
    item["grade"] = str(item.get("execution_grade") or item.get("grade") or "C").upper()
    item["execution_grade"] = str(item.get("execution_grade") or item.get("grade") or item["grade"] or "C").upper()
    if "signal_type" not in item or item.get("signal_type") is None:
        item["signal_type"] = ""
    if "name" not in item or item.get("name") is None:
        item["name"] = ""
    if "reasons" not in item or not isinstance(item.get("reasons"), list):
        item["reasons"] = list(item.get("reasons") or []) if item.get("reasons") else []
    if "detected_at" not in item or item.get("detected_at") in (None, ""):
        item["detected_at"] = _now_kst()
    return item
def _sanitize_run_scan_alerts(alerts: list, stage: str = "") -> list:
    cleaned = []
    dropped = 0
    for item in list(alerts or []):
        if not isinstance(item, dict):
            dropped += 1
            continue
        code = _normalize_scan_signal_code(item)
        if not code:
            dropped += 1
            _log_warn_msg(f"⚠️ run_scan code 누락 제거{(' [' + stage + ']') if stage else ''}: {item.get('name', '') or item.get('signal_type', '') or 'unknown'}")
            continue
        item = _coerce_run_scan_signal_defaults(item, fallback_code=code)
        if bool(item.get("_scan_payload_incomplete")):
            dropped += 1
            _queue_run_scan_repair(item, reasons=item.get("_scan_payload_missing_reasons") or [], stage=stage)
            _log_warn_msg(f"⚠️ run_scan 결측 재복구 큐 등록{(' [' + stage + ']') if stage else ''}: {item.get('name', code) or code} ({', '.join(item.get('_scan_payload_missing_reasons') or [])})")
            continue
        cleaned.append(item)
    if dropped > 0:
        _log_warn_msg(f"⚠️ run_scan malformed alert {dropped}건 제거{(' [' + stage + ']') if stage else ''}")
    return cleaned

def _append_scan_alert(alerts: list, seen: set, result: dict, *, hist_key: str | None = None, seen_code: str | None = None) -> None:
    if not isinstance(result, dict):
        return
    normalized_seen_code = normalize_stock_code(seen_code or "")
    result_code = _normalize_scan_signal_code(result, fallback_code=normalized_seen_code)
    if not result_code:
        _log_warn_msg(f"⚠️ run_scan alert code 누락 스킵: {result.get('name', '') or result.get('signal_type', '') or 'unknown'}")
        return
    result = _coerce_run_scan_signal_defaults(result, fallback_code=result_code)
    if bool(result.get("_scan_payload_incomplete")):
        _queue_run_scan_repair(result, reasons=result.get("_scan_payload_missing_reasons") or [], stage="append")
        _log_warn_msg(f"⚠️ run_scan alert 결측 재복구 대기: {result.get('name', result_code) or result_code} ({', '.join(result.get('_scan_payload_missing_reasons') or [])})")
        return
    resolved_hist_key = hist_key or (f"NXT_{result_code}" if result.get("market") == "NXT" else result_code)
    if time.time() - _alert_history.get(resolved_hist_key, 0) <= get_regime_cooldown():
        return
    alerts.append(result)
    seen.add(normalized_seen_code or result_code)
def _scan_overnight_watchlist_candidates(alerts: list, seen: set, krx_open: bool) -> None:
    try:
        if not (_overnight_watchlist and krx_open):
            return
        for wl_code, wl_info in list(_overnight_watchlist.items())[:10]:
            if wl_code in seen:
                continue
            try:
                cur = get_stock_price(wl_code)
                if cur and cur.get("price", 0) > 0:
                    wl_stock = {
                        "code": wl_code,
                        "name": wl_info.get("name", ""),
                        "price": cur["price"],
                        "change_rate": cur.get("change_rate", 0),
                        "volume_ratio": cur.get("volume_ratio", 0),
                        "today_vol": cur.get("today_vol", 0),
                        "_overnight_event": wl_info.get("event", ""),
                    }
                    _append_scan_alert(alerts, seen, analyze(wl_stock), hist_key=wl_code, seen_code=wl_code)
                time.sleep(0.1)
            except Exception as e:
                _swallow_exception(e)
                continue
    except Exception as _e:
        _log_warn_msg(f"  ⚠️ 야간 워치리스트 우선 스캔 오류: {_e}")
def _scan_scenario_action_board_candidates(alerts: list, seen: set, krx_open: bool) -> None:
    try:
        if not krx_open:
            return
        board = _load_premarket_action_board()
        if not board.get("items"):
            return
        scanned = 0
        for item in list(board.get("items", []) or []):
            if str(item.get("direction", "")) != "up":
                continue
            for cand in list(item.get("kr_stock_candidates_long", []) or [])[:3]:
                code = normalize_stock_code(cand.get("code"))
                if not code or code in seen:
                    continue
                cur = get_stock_price(code)
                if not cur or not cur.get("price", 0):
                    continue
                stock = {
                    "code": code,
                    "name": _resolve_stock_name(code, cand.get("name", "")),
                    "price": cur.get("price", 0),
                    "change_rate": cur.get("change_rate", 0),
                    "volume_ratio": cur.get("volume_ratio", 0),
                    "today_vol": cur.get("today_vol", 0),
                    "scenario_event": item.get("event_name", ""),
                }
                result = analyze(stock)
                if isinstance(result, dict):
                    result = dict(result)
                    result.setdefault("reasons", []).append(f"🧭 24H 시나리오 후보: {str(item.get('event_name','') or '')[:24]}")
                _append_scan_alert(alerts, seen, result, hist_key=code, seen_code=code)
                scanned += 1
                if scanned >= SCENARIO_SCAN_LIMIT:
                    return
                time.sleep(0.1)
    except Exception as e:
        _log_warn_msg(f"  ⚠️ 시나리오 액션보드 우선 스캔 오류: {e}")


def _scan_issue_prewatch_candidates(alerts: list, seen: set) -> None:
    if not _news_issue_prewatch or not is_any_market_open():
        return
    now = time.time()
    expired_keys = []
    for theme_key, pw in list(_news_issue_prewatch.items())[:MATERIAL_PREWATCH_SCAN_LIMIT]:
        if _should_expire_issue_prewatch(theme_key, pw, now):
            expired_keys.append(theme_key)
            continue
        try:
            pw = dict(pw)
            pw.setdefault("theme_key", theme_key)
            reacted = _collect_issue_prewatch_reacted(pw.get("stocks", []), pw)
            if not reacted:
                continue
            summary = _summarize_material_reaction(reacted, pw)
            if not summary.get("passes"):
                continue
            reacted_sorted = sorted(reacted, key=lambda item: _material_reacted_priority_score(item, pw, summary), reverse=True)
            dispatched_codes = set()
            for item in reacted_sorted[:ISSUE_PREWATCH_REACT_LIMIT]:
                code = normalize_stock_code(item.get("code", ""))
                if not code or code in seen or _is_material_first_stock_cooldown(code, theme_key):
                    continue
                result = analyze(item)
                if not isinstance(result, dict):
                    continue
                if result.get("grade") != "A" or int(result.get("entry_price", 0) or 0) <= 0:
                    continue
                result = dict(result)
                result.setdefault("reasons", []).append(f"👁 재료-first prewatch: {str(pw.get('theme_desc', '') or '')[:30]}")
                result["material_first_hint"] = True
                result["material_first_priority_hit"] = bool(summary.get("strong"))
                result["material_first_theme"] = theme_key
                result["material_first_seed_score"] = summary.get("seed_score", 0)
                result["material_first_reacted_cnt"] = summary.get("reacted_cnt", 0)
                _append_scan_alert(alerts, seen, result, hist_key=code, seen_code=code)
                _mark_material_first_stock_alerted(code, theme_key)
                dispatched_codes.add(code)
            if dispatched_codes:
                _news_prewatch_fired[theme_key] = now
                expired_keys.append(theme_key)
                _log_info_msg(f"  👁 재료-first prewatch→본스캔 합류: [{theme_key}] {len(dispatched_codes)}종목")
        except Exception as e:
            _log_error("_scan_issue_prewatch_candidates", e)
    for key in expired_keys:
        _news_issue_prewatch.pop(key, None)


def _scan_krx_market_candidates(alerts: list, seen: set) -> None:
    today_date = datetime.now().strftime("%Y%m%d")
    for stock in get_upper_limit_stocks():
        code = normalize_stock_code(stock.get("code", ""))
        if not code:
            _log_warn_msg("⚠️ run_scan upper_limit 후보 code 누락 스킵")
            continue
        stock = dict(stock)
        stock["code"] = code
        _register_sector_leader_follow_seed(stock)
        if code in seen:
            continue
        _ul_rec = _upper_limit_day_alerted.get(code)
        if _ul_rec and _ul_rec.get("date") == today_date:
            cr = stock.get("change_rate", 0)
            if cr >= 29.0:
                continue
            _upper_limit_day_alerted.pop(code, None)
        r = analyze(stock)
        result_code = _normalize_scan_signal_code(r, fallback_code=code) if isinstance(r, dict) else ""
        if isinstance(r, dict) and r.get("signal_type") in ("UPPER_LIMIT", "NEAR_UPPER") and result_code:
            _upper_limit_day_alerted[result_code] = {"date": today_date, "alerted": True}
        _append_scan_alert(alerts, seen, r, seen_code=code)
    for stock in get_volume_surge_stocks():
        code = normalize_stock_code(stock.get("code", ""))
        if not code:
            _log_warn_msg("⚠️ run_scan volume_surge 후보 code 누락 스킵")
            continue
        stock = dict(stock)
        stock["code"] = code
        _register_sector_leader_follow_seed(stock)
        if code in seen:
            continue
        _append_scan_alert(alerts, seen, analyze(stock), seen_code=code)
def _scan_nxt_market_candidates(alerts: list, seen: set) -> None:
    for stock in get_nxt_surge_stocks():
        code = normalize_stock_code(stock.get("code", ""))
        if not code:
            _log_warn_msg("⚠️ run_scan NXT 후보 code 누락 스킵")
            continue
        stock = dict(stock)
        stock["code"] = code
        _register_sector_leader_follow_seed(stock)
        if code in seen:
            continue
        if _is_nxt_premarket_window():
            gate = stock.get("_nxt_premarket_gate") if isinstance(stock.get("_nxt_premarket_gate"), dict) else _get_nxt_premarket_quality_gate(stock)
            if not gate.get("allow"):
                continue
            stock["_nxt_premarket_gate"] = gate
        r = analyze(stock)
        if isinstance(r, dict):
            r["market"] = "NXT"
        hist_code = _normalize_scan_signal_code(r, fallback_code=code) if isinstance(r, dict) else code
        _append_scan_alert(alerts, seen, r, hist_key=f"NXT_{hist_code}", seen_code=code)
def _collect_quiet_absorption_scan_pool(existing_codes: set | None = None) -> list[dict]:
    scan_limit = max(2, int(MARKET_FLOW_QUIET_SCAN_LIMIT_PER_MARKET or 2))
    pool: list[dict] = []
    seen = set(existing_codes or set())
    for stock in get_market_rank_focus_stocks(scan_limit_per_market=scan_limit):
        code = normalize_stock_code(stock.get("code", ""))
        if not code or code in seen:
            continue
        change_rate = safe_float(stock.get("change_rate", 0.0), 0.0)
        volume_ratio = safe_float(stock.get("volume_ratio", 0.0), 0.0)
        if change_rate < MARKET_FLOW_QUIET_MIN_CHANGE or change_rate > MARKET_FLOW_QUIET_MAX_CHANGE:
            continue
        if volume_ratio <= 0 or volume_ratio > MARKET_FLOW_QUIET_MAX_VOLUME_RATIO:
            continue
        seen.add(code)
        pool.append(stock)
    return pool
def _slice_quiet_absorption_scan_pool(pool: list[dict]) -> list[dict]:
    if not pool:
        return []
    deep_limit = max(1, int(MARKET_FLOW_QUIET_DEEP_FETCH_LIMIT or 1))
    if len(pool) <= deep_limit:
        return pool
    cursor = int(_quiet_scan_cursor.get("all", 0) or 0) % len(pool)
    selected = [pool[(cursor + idx) % len(pool)] for idx in range(deep_limit)]
    _quiet_scan_cursor["all"] = (cursor + deep_limit) % len(pool)
    return selected
def _scan_quiet_absorption_candidates(alerts: list, seen: set) -> None:
    pool = _slice_quiet_absorption_scan_pool(_collect_quiet_absorption_scan_pool(existing_codes=seen))
    if not pool:
        return
    _reset_quiet_scan_cycle_state()
    for stock in pool:
        code = normalize_stock_code(stock.get("code", ""))
        if not code:
            continue
        registered = _register_quiet_absorption_seed(stock, source="quiet_absorption_scan")
        if not registered or code in seen:
            continue
        analyzed = analyze(stock)
        if isinstance(analyzed, dict):
            analyzed.setdefault("reasons", []).append("🪙 뉴스 전 조용한 선매집 초기감지")
        _append_scan_alert(alerts, seen, analyzed, seen_code=code)
    skipped = int(_quiet_scan_cycle_state.get("skipped_budget", 0) or 0)
    if skipped > 0:
        _log_info_msg(f"  ⏭ quiet scan budget 절약: snapshot 생략 {skipped}건")
def _scan_rank_and_theme_candidates(alerts: list, seen: set) -> None:
    _rank_scan_limit = NXT_POSTMARKET_EXTRA_RANK_LIMIT if _is_nxt_postmarket_only_window() else None
    for stock in get_market_rank_focus_stocks(scan_limit_per_market=_rank_scan_limit):
        code = stock.get("code")
        if not code or code in seen:
            continue
        _append_scan_alert(alerts, seen, analyze(stock), seen_code=code)
    for stock in _collect_theme_peer_follow_candidates(existing_codes=seen):
        code = stock.get("code")
        if not code or code in seen:
            continue
        _append_scan_alert(alerts, seen, analyze(stock), seen_code=code)
def _scan_sector_leader_follow_candidates(alerts: list, seen: set) -> None:
    for stock in _collect_sector_leader_follow_candidates(existing_codes=seen):
        code = stock.get("code")
        if not code or code in seen:
            continue
        _append_scan_alert(alerts, seen, analyze(stock), seen_code=code)
def _scan_early_pullback_candidates(alerts: list, seen: set, krx_open: bool, nxt_open: bool) -> None:
    if krx_open:
        for s in check_early_detection():
            code = _normalize_scan_signal_code(s)
            if not code:
                _log_warn_msg("⚠️ run_scan EARLY_DETECT 결과 code 누락 스킵")
                continue
            hist_key = f"NXT_{code}" if s.get("market") == "NXT" else code
            if code not in seen:
                _append_scan_alert(alerts, seen, s, hist_key=hist_key, seen_code=code)
        for s in check_pullback_signals():
            code = _normalize_scan_signal_code(s)
            if not code:
                _log_warn_msg("⚠️ run_scan pullback 결과 code 누락 스킵")
                continue
            if s.get("code") != code:
                s = dict(s)
                s["code"] = code
            if code not in seen and code not in _mid_pullback_alert_history:
                alerts.append(s)
                seen.add(code)
    elif nxt_open:
        for s in check_nxt_intraday_early_detection(existing_codes=seen):
            code = _normalize_scan_signal_code(s)
            if not code:
                _log_warn_msg("⚠️ run_scan NXT intraday EARLY 결과 code 누락 스킵")
                continue
            if code not in seen:
                _append_scan_alert(alerts, seen, s, hist_key=f"NXT_{code}", seen_code=code)
        for s in check_nxt_preopen_detection(existing_codes=seen):
            code = _normalize_scan_signal_code(s)
            if not code:
                _log_warn_msg("⚠️ run_scan NXT preopen 결과 code 누락 스킵")
                continue
            if code not in seen:
                _append_scan_alert(alerts, seen, s, hist_key=f"NXT_{code}", seen_code=code)
        for s in check_nxt_postmarket_detection(existing_codes=seen):
            code = _normalize_scan_signal_code(s)
            if not code:
                _log_warn_msg("⚠️ run_scan NXT postmarket 결과 code 누락 스킵")
                continue
            if code not in seen:
                _append_scan_alert(alerts, seen, s, hist_key=f"NXT_{code}", seen_code=code)
def _apply_scan_sector_gate(alerts: list) -> list:
    alerts = sorted(alerts, key=_sector_gate_sort_key, reverse=True)
    max_signals_per_sector = 3
    max_signals_misc = 4
    sector_counts = {}
    filtered_alerts = []
    for s in alerts:
        sec = _hydrate_alert_sector_theme(s, force_lookup=True)
        if not str(s.get("name") or "").strip() and s.get("code"):
            s["name"] = _resolve_stock_name(s.get("code"), s.get("name", ""))
        sec_limit = max_signals_misc if sec == "기타" else max_signals_per_sector
        if s.get("theme_chain_force_hit") or s.get("force_external_capture_alert") or s.get("material_first_priority_hit") or s.get("direct_news_hit"):
            sec_limit += 2
        sector_counts[sec] = sector_counts.get(sec, 0) + 1
        if sector_counts[sec] <= sec_limit:
            if not s.get("sector_theme") and sec != "기타":
                s["sector_theme"] = sec
            filtered_alerts.append(s)
        else:
            _record_shadow_capture(s.get("code", ""), s.get("name", s.get("code", "")), "sector_limit", s.get("signal_type", ""), stage="sector_gate", extra={"sector": sec, "score": s.get("score", 0), "change_rate": s.get("change_rate", 0)})
            _log_info_msg(f"  ⏭ 섹터 제한({sec} {sector_counts[sec]}번째): {s.get('name','')} 생략")
    return filtered_alerts
def _dispatch_scan_alerts(alerts: list) -> None:
    if not alerts:
        _log_info_msg("  → 조건 충족 없음")
        return
    _log_info_msg(f"  → {len(alerts)}개 감지! [{regime_label()}]")
    for s in alerts:
        if is_scoring_only_instrument(s.get("code", ""), s.get("name", "")):
            _log_info_msg(f"  ⏭ 점수전용 종목 제외: {s.get('name', s.get('code',''))}")
            continue
        is_nxt = s.get("market") == "NXT"
        hist_key = f"NXT_{s['code']}" if is_nxt else s["code"]
        _dispatch_general_alert_signal(s, hist_key=hist_key, source_label="일반 포착")
def _run_scan_followup_hooks() -> None:
    check_execution_setup_watch()
    _tick_exec_speed_prewarm()
    check_entry_watch()
    check_preclose_gap_entry_watch()
    run_entry_defense_monitor()
    check_reentry_watch()
    track_signal_results()
def run_price_first_scan() -> None:
    run_scan()


def run_scan():
    code = ""
    ctx = _build_scan_runtime_context()
    if not ctx:
        return
    _log_info_msg(f"\n[{datetime.now().strftime('%H:%M:%S')}] 스캔{ctx['strict_tag']} [{ctx['mkt_tag']}]...")
    try:
        _ensure_dynamic_candidates_fresh()
        alerts, seen = [], set()
        _scan_overnight_watchlist_candidates(alerts, seen, ctx["krx_open"])
        _scan_scenario_action_board_candidates(alerts, seen, ctx["krx_open"])
        _scan_issue_prewatch_candidates(alerts, seen)
        if ctx["krx_open"]:
            _scan_krx_market_candidates(alerts, seen)
        if ctx["nxt_open"]:
            _scan_nxt_market_candidates(alerts, seen)
        _scan_quiet_absorption_candidates(alerts, seen)
        _scan_rank_and_theme_candidates(alerts, seen)
        _scan_sector_leader_follow_candidates(alerts, seen)
        _scan_early_pullback_candidates(alerts, seen, ctx["krx_open"], ctx["nxt_open"])
        _drain_run_scan_repair_queue(alerts, seen)
        alerts = _sanitize_run_scan_alerts(alerts, stage="pre_sector_gate")
        alerts = _apply_scan_sector_gate(alerts)
        alerts = _sanitize_run_scan_alerts(alerts, stage="pre_portfolio_filter")
        alerts = filter_portfolio_signals(alerts)
        alerts = _sanitize_run_scan_alerts(alerts, stage="pre_dispatch")
        _dispatch_scan_alerts(alerts)
        _run_scan_followup_hooks()
    except Exception as e:
        _log_error("run_scan", e, critical=True)
# ============================================================
# 🚀 실행
# ============================================================
def _get_code_hash() -> str:
    """v38.3-D3: 현재 실행 코드의 SHA256 해시 (8자리)"""
    try:
        with open(os.path.abspath(__file__), "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:8]
    except Exception as e:
        _swallow_exception(e)  # v105 structured silent-exception log
        return "unknown"
if __name__ == "__main__":
    _log_info_msg("="*55)
    _log_info_msg(f"📈 KIS 주식 급등 알림 봇 {BOT_VERSION} 시작")
    _log_info_msg(f"   업데이트: {BOT_DATE}")
    _log_info_msg("="*55)
    install_excepthook()
    update_dashboard(force=True)
    # Persistent storage init (코드 교체/배포에도 데이터/조건 보존)
    _migrate_legacy_files()
    _storage_diagnostics_once()
    _load_kr_holidays(datetime.now().year)
    try:
        threading.Thread(target=_telegram_poll_loop, daemon=True).start()
        _log_info_msg(f"✅ 텔레그램 폴링 전용 루프 시작 ({TELEGRAM_POLL_INTERVAL}s)")
    except Exception as e:
        _log_warn_msg(f"⚠️ 텔레그램 폴링 루프 시작 실패: {e}")
    # ── 공휴일/주말 → 종료 대신 대기 모드로 전환 ──
    if is_holiday():
        _log_info_msg(f"📅 오늘은 공휴일/주말 — 대기 모드로 실행")
        if _try_acquire_leader_lock():
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
            except Exception as e:
                _swallow_exception(e)
        # 대기 모드: 텔레그램 명령어 + 오버나이트 모니터만 실행
        _strict_cleanup_legacy_entry_hits()
        load_carry_stocks()
        _load_trading_halt_state()
        _load_entry_watch_active()
        # v80 #1: _load_entry_watch_active() 이후 즉시 stale 정리 (순서가 핵심)
        try:
            _phits = _purge_stale_entry_watch_hits()
            if _phits:
                _log_info_msg(f"🗑 봇 시작 시 stale entry_hit {_phits}건 정리")
        except Exception as _pe:
            _log_warn_msg(f"⚠️ stale entry_hit 정리 오류: {_pe}")
        _load_preclose_gap_entry_watch()
        _load_reentry_watch()
        _load_execution_setup_watch()
        migrate_signal_log_pnl_fields()
        _load_sector_leader_follow_state()
        _load_market_flow_state()
        _load_dynamic_params()
        schedule.every(30).minutes.do(_leader_job(run_overnight_monitor))
        schedule.every(60).minutes.do(_leader_job(run_geo_news_scan))
        _run_holiday_standby_until_trading_day()
    _strict_cleanup_legacy_entry_hits()
    load_carry_stocks()
    _load_trading_halt_state()
    _load_entry_watch_active()
    # v80 #1: _load_entry_watch_active() 이후 즉시 stale 정리 (순서가 핵심)
    try:
        _phits = _purge_stale_entry_watch_hits()
        if _phits:
            _log_info_msg(f"🗑 봇 시작 시 stale entry_hit {_phits}건 정리")
    except Exception as _pe:
        _log_warn_msg(f"⚠️ stale entry_hit 정리 오류: {_pe}")
    _load_preclose_gap_entry_watch()
    _load_reentry_watch()
    _load_execution_setup_watch()
    migrate_signal_log_pnl_fields()
    load_tracker_feedback()
    load_dynamic_themes()
    _load_sector_leader_follow_state()
    _load_market_flow_state()
    load_adaptive_capture_feedback()
    load_stale_replay_penalty_profile()
    _load_dynamic_params()          # ★ 재시작 후 조정된 파라미터 복원
    if _try_acquire_leader_lock():
        if _enforce_runtime_version_lock(notify=True):
            _send_startup_banner_once()
    else:
        _log_info_msg("⏸ 현재 replica는 passive 모드 — 리더 락 획득 전까지 스캔/알림 실행 안 함")
    schedule.every(SCAN_INTERVAL).seconds.do(_leader_job(run_price_first_scan))
    schedule.every(NXT_PREMARKET_BURST_INTERVAL_SEC).seconds.do(_leader_job(_run_nxt_premarket_burst_scan))
    schedule.every(KRX_OPEN_BURST_INTERVAL_SEC).seconds.do(_leader_job(_run_krx_open_burst_scan))
    schedule.every(NEWS_SCAN_INTERVAL).seconds.do(_leader_job(run_material_first_scan))
    schedule.every(DART_INTERVAL).seconds.do(_leader_job(run_dart_intraday))
    schedule.every(MID_PULLBACK_SCAN_INTERVAL).seconds.do(_leader_job(run_mid_pullback_scan))
    schedule.every(5).minutes.do(_leader_job(lambda: send_market_leading_sector_update(force=False)))
    # INFO 참고 알림은 사용자 발송하지 않음
    schedule.every(30).minutes.do(clean_expired_cache)  # [v41.84]
    schedule.every().day.at("05:00").do(reset_daily_caches)  # [v41.84]
    schedule.every(30).minutes.do(_leader_job(_prune_all_caches))
    schedule.every().day.at("07:30").do(_send_preopen_watchlist_once)  # v37.9: 익개장 전 워치리스트 요약
    schedule.every().day.at("07:30").do(_send_premarket_risk_assessment_once)  # 장전 리스크 평가 full
    schedule.every().day.at("08:30").do(_send_premarket_risk_update_once)  # 변화 있을 때만 짧은 업데이트
    schedule.every().day.at("08:50").do(_leader_job(send_premarket_briefing))
    schedule.every().day.at(PRECLOSE_GAP_OPEN_EVAL_TIME_NXT).do(_leader_job(
        lambda: None if is_holiday() else update_preclose_gap_open_outcomes(stage="nxt")
    ))
    schedule.every().day.at(PRECLOSE_GAP_OPEN_EVAL_TIME_KRX).do(_leader_job(
        lambda: None if is_holiday() else update_preclose_gap_open_outcomes(stage="krx")
    ))
    schedule.every().day.at("14:45").do(_leader_job(
        lambda: None if is_holiday() else send_next_open_gap_alert(stage="krx", phase="initial")
    ))
    schedule.every().day.at("15:18").do(_leader_job(
        lambda: None if is_holiday() else send_next_open_gap_alert(stage="krx", phase="final")
    ))
    schedule.every().day.at("19:20").do(_leader_job(
        lambda: None if is_holiday() else send_next_open_gap_alert(stage="nxt", phase="final")
    ))
    schedule.every(10).minutes.do(_leader_job(lambda: update_dashboard(force=False)))
    schedule.every(15).minutes.do(_leader_job(run_intraday_watchdog))  # v83: 장중 워치독
    schedule.every().day.at("15:45").do(_leader_job(lambda: None if is_holiday() else _send_market_scenario_digest()))
    schedule.every().day.at("20:10").do(_leader_job(lambda: None if is_holiday() else _send_market_scenario_digest(force=True)))
    # TOP 5: 10:00부터 장마감까지 1시간마다 자동 발송
    # KRX only 종목: ~15:30, NXT 상장 종목 포함 시: ~20:00
    for _top_hhmm in ["10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00"]:
        schedule.every().day.at(_top_hhmm).do(_leader_job(
            lambda: None if is_holiday() or not is_any_market_open() else send_top_signals()
        ))
    schedule.every().day.at(MARKET_OPEN).do(_leader_job(_on_market_open))  # v37.0: 명명 함수
    schedule.every().day.at(MARKET_CLOSE).do(_leader_job(
        lambda: None if is_holiday() else on_market_close()
    ))
    # 오버나이트 위험 알림 (15:10 — KRX 마감 20분 전, 매도 가능 시간)
    schedule.every().day.at("15:10").do(_leader_job(
        lambda: None if is_holiday() else send_overnight_risk_alerts()
    ))
    # NXT 오버나이트 위험 알림 (19:40 — NXT 마감 20분 전, 매도 가능 시간)
    schedule.every().day.at("19:40").do(_leader_job(
        lambda: None if is_holiday() else send_overnight_risk_alerts()
    ))
    # NXT 완전 마감 후 잔여 재진입 감시 초기화 + 결과 미입력 알림 (NXT 상장 종목용)
    schedule.every().day.at("20:05").do(_leader_job(
        lambda: (
            run_daily_self_audit(stage="nxt"),
            _clear_reentry_watch_all(),
            _send_pending_result_reminder(),   # NXT 마감 후 최종 미입력 알림
            _log_info_msg("📡 NXT 마감(20:00) — 재진입 감시 전체 초기화")
        ) if not is_holiday() else None
    ))
    # 24시간 시나리오 수집 (20분마다)
    schedule.every(20).minutes.do(_leader_job(run_market_scenario_collection_cycle))
    # 오버나이트 모니터링 (30분마다 — 함수 내부에서 시간대 체크)
    schedule.every(30).minutes.do(_leader_job(run_overnight_monitor))
    # 지정학 뉴스 스캔 (1시간마다)
    schedule.every(60).minutes.do(_leader_job(run_geo_news_scan))
    # 평일만 백업 (장 운영일에만)
    schedule.every(BACKUP_INTERVAL_H).hours.do(_leader_job(
        lambda: run_auto_backup(notify=False) if not is_holiday() else None
    ))
    # v41.60: 20:10 자동 종료 제거 — 장마감 후에도 야간 모니터링 지속,
    # 지정학/해외시장 이슈를 누적해 다음날 07:30/08:50 브리핑에 반영.
    schedule.every().day.at("20:10").do(_leader_job(
        lambda:
            _log_info_msg("🌙 20:10 이후 야간 모니터링 모드 전환 — 프로세스 유지")
        if not is_holiday() else None
    ))
    # v39.3: 시작 시 07:30/08:30 장전 메시지 놓침 보완 (leader/passive와 무관하게 날짜별 1회 보장)
    _now = datetime.now()
    if not is_holiday():
        if dtime(7, 30) <= _now.time() <= dtime(9, 0):
            try:
                _log_info_msg("📋 시작 시 장전 브리핑 보완 발송")
                _send_preopen_watchlist_once()
            except Exception as e:
                _log_warn_msg(f"⚠️ 장전 브리핑 보완 실패: {e}")
        if dtime(7, 30) <= _now.time() < dtime(8, 30):
            try:
                _log_info_msg("🛡 시작 시 장전 리스크 평가 보완 발송")
                _send_premarket_risk_assessment_once()
            except Exception as e:
                _log_warn_msg(f"⚠️ 장전 리스크 평가 보완 실패: {e}")
        elif dtime(8, 30) <= _now.time() < dtime(8, 45):
            try:
                _log_info_msg("🔄 시작 시 장전 리스크 업데이트 보완 발송")
                _send_premarket_risk_update_once()
            except Exception as e:
                _log_warn_msg(f"⚠️ 장전 리스크 업데이트 보완 실패: {e}")
    _maybe_run_preclose_gap_alert_catchup()
    _schedule_startup_scan_catchup()
    while True:
        try:
            schedule.run_pending(); time.sleep(1)
        except Exception as e:
            _log_warn_msg(f"⚠️ 메인 루프 오류: {e}"); time.sleep(5)
