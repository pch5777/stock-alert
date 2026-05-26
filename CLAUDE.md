# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 0. 답변 형식 — 결론만

**모든 답변은 결론 한 문장으로 시작·종료한다. 사용자가 명시적으로 "근거 설명" 요청 시에만 확장.**

금지:
- "이유:", "근거:", "왜냐하면" 블록
- 코드 라인 인용 (line N 등) 답변 본문 첨부
- 시나리오 1/2/3 나열
- "추정", "가능성", "예상" 분석 다단계 전개
- "추가 확인 방법" 제안 (사용자가 묻지 않은 다음 단계)
- 마크다운 표/박스/헤더(##/###) 남발 — 결론은 한 문장이면 됨
- 코드/지침/스킬 설명도 결론 한 문장. 라인 인용/장문 금지

허용:
- 사용자가 "왜?", "근거 알려줘", "더 자세히" 요청 시 확장
- 위험·돌이킬 수 없는 작업 확인 시 (irreversible action) — 짧게 경고

이 규칙은 캐브맨 모드와 별개로 항상 적용. 캐브맨 모드 해제돼도 결론 우선 유지.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Backup Before Every Edit

**Before touching any file, save a timestamped backup. No exceptions.**

```bash
# stock_alert.py 수정 전 항상 실행
cp stock_alert.py stock_alert.py.bak_$(date +%Y%m%d_%H%M%S)
```

Rules:
- 백업은 수정 **전**에 만든다. 수정 후 백업은 의미 없다.
- 백업 파일명에 타임스탬프를 포함해 덮어쓰기를 방지한다.
- 패치가 잘못됐을 경우 즉시 백업에서 복원한다: `cp stock_alert.py.bak_YYYYMMDD_HHMMSS stock_alert.py`
- 오래된 백업(3개 초과)은 정리해도 된다: `ls -t stock_alert.py.bak_* | tail -n +4 | xargs rm -f`

**Why this exists:** Edit 도구가 파일 말미를 잘라낸 채 저장하는 버그가 발생했다. git이 없는 환경에서 원본을 복원할 방법이 없어 잘린 내용을 추정으로 복원해야 했다.

## 6. File Integrity After Every Edit

**After editing any file, run all three checks before submitting. No exceptions.**

```bash
# 반드시 세 명령을 분리해서 실행 — 한 줄로 합치면 출력이 섞여 잘림을 못 본다
wc -l <file>
tail -5 <file>
python3 -W error::SyntaxWarning -m py_compile <file> && echo "OK"
```

Rules:
- 수정 **전** 줄수를 기록한다. 수정 후 줄수가 줄어들면 **즉시 백업 복원** 후 재시도.
- `tail` 출력이 `echo OK`와 붙어나오면 잘림을 못 본다 — **반드시 분리 실행**.
- 변경 부분만 확인하는 것은 검증이 아니다. 파일 끝까지 확인해야 한다.
- 세 가지 모두 통과 전까지 배포하지 않는다.

**Why this exists:** Python str.replace() + 전체 파일 재저장 방식이 반복적으로 파일 끝을 잘랐다. tail과 SYNTAX OK를 한 줄로 실행해 출력이 붙어나와 잘림을 감지하지 못했고, 잘린 채로 배포되어 서비스가 다운됐다.

## 7. 파일 수정 방식 제한

**stock_alert.py 수정 시 Python str.replace() + 전체 파일 재저장 방식을 사용할 때는 반드시 아래를 지킨다.**

```python
# 필수: replace 후 즉시 줄수 검증
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
before_lines = content.count('\n')
content = content.replace(old, new, 1)
after_lines = content.count('\n')
# 줄수가 크게 줄면 저장하지 않는다
assert after_lines >= before_lines - 5, f"라인 급감 감지: {before_lines} → {after_lines}"
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
```

Rules:
- replace 결과가 'FAIL'이면 절대 저장하지 않는다.
- 저장 후 반드시 wc -l / tail -5 / py_compile 세 검증을 **분리 실행**한다.
- 사용자가 요청하지 않은 코드(필터, 리팩토링 등)를 임의로 추가하지 않는다.

## 8. 실전형 출력 강제 (No Vague Recommendations)

**제안·분석·시나리오·개선사항은 반드시 실전 매매 파라미터로 끝내라. 권고/권장/추천 같은 추상 표현 금지.**

금지되는 표현 예시:
- "보수적으로 진입" / "공격적으로 진입" / "모니터링 권장" / "관망 추천"
- "이 종목을 주목" / "신중하게 접근" / "유의해서 매매"
- "리스크 관리 필요" / "포지션 조절 권장"

반드시 포함되어야 할 실전 파라미터:
- **진입 종목** (코드/이름 명시)
- **진입 시점** (분 단위 또는 트리거 조건)
- **진입가** (구체 가격 또는 계산식)
- **손절가** (구체 가격 또는 진입가 대비 %)
- **익절가** (구체 가격 또는 진입가 대비 %, 분할 익절이면 단계별)
- **포지션 크기** (자본 대비 % 또는 금액)
- **취소/이탈 조건** (시나리오가 깨졌다고 판단할 명확한 기준)

진입하지 않는 종목도 "모니터링" 같은 모호한 단어 대신 다음 중 하나로 출력:
- **진입 금지 (이유: ...)** — 시나리오 추론 결과 진입 부적합
- **관찰만 (이유: ..., 트리거: ...)** — 특정 조건 충족 시 자동 재평가
- **시나리오 외 종목** — 후보 풀 밖이라 별도 처리 안 함

Rules:
- 사용자가 명시적으로 "분석만 해라"라고 한 경우를 제외하면 실전 파라미터까지 도출한다.
- 데이터가 부족해서 실전 파라미터를 만들 수 없으면, 추상 권고로 도망가지 말고 어떤 데이터가 추가로 필요한지 질문한다.
- 봇 출력(텔레그램 알람, 시나리오 파일, signal_log 등)도 동일 원칙 적용. 추상 표현을 출력 포맷에 넣지 않는다.
- 진단/리뷰 결과를 정리할 때도 "이 부분을 신중히 보세요" 식 표현 대신 "이 코드 라인 N을 X로 변경" 같은 구체 액션으로 끝낸다.

**Why this exists:** 봇 시나리오와 분석 결과가 추상 표현으로 끝나서 사용자가 실제로 무엇을 할지를 봇이 알려주지 못함. 실전 봇은 추상 권고가 아니라 실행 가능한 명령을 출력해야 한다.

## 9. 시나리오/재료수집 로직 가동 시점

**시나리오·재료수집·후보 풀 구성 로직은 장 마감 후에만 돌리지 않는다. 장중·장 마감 전·장 마감 후 세 시점 모두에서 작동해야 한다.**

작동 시점:
- **장중 (09:00~15:20):** 주기적(예: 15~30분) 가동. 장중 발생한 새 재료(공시/뉴스/외국인기관 매매 동향 등)를 반영해 시나리오 갱신.
- **장 마감 직전 (예: 15:00~15:30):** 종가매매를 위해 집중 가동. 그날 시장 흐름이 확정되는 시점에서 다음날 후보 풀 1차 구성.
- **장 마감 후 (16:00~22:00 등):** 결산 + 익일 후보 풀 최종 확정.

Rules:
- 사용자가 "종가매매" 또는 "장 마감 전 진입"을 요구하는 맥락이면, 시나리오 시스템 설계 시 장 마감 전 시점에서도 동일 로직이 동작 가능한지 반드시 확인한다.
- 시나리오를 장 마감 후에만 만드는 설계는 거부된다 — 그 경우 종가매매에 활용 불가.
- 시점별 입력 데이터가 다르므로 LLM 프롬프트와 점수 계산식도 시점별로 분기될 수 있다. 단일 함수로 강제하지 않는다.

**Why this exists:** 봇의 종가매매 로직(PRECLOSE_GAP_ENTRY 등)이 장 마감 후 후보 풀에만 의존해서, 정작 종가에 진입할 시점(장 마감 직전)에는 시나리오/재료 데이터가 부족한 상태. 종가매매가 무효화되는 구조적 결함.

## 10. 출력 검증 강제 (Output Verification Mandate)

**"정상", "작동 중", "결함 없음", "반영됨"이라고 판단하기 전에 반드시 출력단까지 확인한다.**

(a) 입력단(변수 셋업, 함수 진입, 라벨, grep 매칭) 확인만으로는 부족하다. 출력단(대시보드 표시, 텔레그램 알람, JSON 파일 내용, 사용자 캡처)이 기대값과 일치하는지 직접 비교한다.

(b) fallback / 대체 경로의 데이터 소스를 함수 본문까지 따라 내려가 확인한다. 함수 이름이 "NXT_fallback"이라도 내부에서 KRX API를 호출할 수 있다.

Rules:
- "변수에 NXT가 들어갔다 → NXT 데이터다" 같은 비약 금지.
- "로그에 라벨이 찍혔다 → 정상이다" 같은 비약 금지.
- "패치 grep 매칭됐다 → 사용자 화면에 반영됐다" 같은 비약 금지.
- 비교 가능한 외부 데이터(HTS 캡처/공식 API 응답)가 없으면 "검증 불가"라고 보고하고 사용자에게 그 데이터를 요청한다. 추정으로 "정상" 판정 금지.
- "정상" 판정 직전에 자가 점검을 텍스트로 출력: "검증 근거: 입력단=..., 출력단=..., 외부비교=...".

**Why this exists:** 2026-05-18 NXT 등락률 상위 사고. 입력 변수가 NXT로 셋업된 사실 하나로 출력이 NXT 데이터라고 단정 → 사용자 HTS 캡처 비교 단계에서 실제로는 KRX 종가 데이터가 표시되고 있던 사실이 드러남. 사용자가 캡처를 주지 않았다면 거짓 보고가 그대로 운영에 반영될 뻔함. 입력단 점검과 출력단 검증을 같은 단계로 묶지 말 것.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, clarifying questions come before implementation rather than after mistakes, and every edit has a recoverable backup.
