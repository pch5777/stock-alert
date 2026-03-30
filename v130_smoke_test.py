#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
import io
import re
import tokenize
from pathlib import Path

BASE = Path('/mnt/data')
SRC = BASE / 'v130_stock_alert.py'
PREV_SRC = BASE / 'v128_stock_alert.py'
POINTER = BASE / 'v130_00_BASELINE_POINTER.txt'
HANDOFF = BASE / 'v130_01_HANDOFF.md'
START = BASE / 'v130_02_START_CHAT_UTF8_BOM.md'
RULES = BASE / 'v130_04_BASELINE_OPERATING_RULES.md'


def _src_text() -> str:
    return SRC.read_text(encoding='utf-8')


def _parse_tree() -> ast.AST:
    return ast.parse(_src_text())


def _function_span(tree: ast.AST, name: str) -> int:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            end = max(getattr(n, 'end_lineno', node.lineno) for n in ast.walk(node))
            return end - node.lineno + 1
    raise AssertionError(f'function not found: {name}')


def _helper_names(tree: ast.AST) -> set[str]:
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def _all_function_spans(tree: ast.AST) -> dict[str, int]:
    out = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            end = max(getattr(n, 'end_lineno', node.lineno) for n in ast.walk(node))
            out[node.name] = end - node.lineno + 1
    return out


def _raw_3_tokens(text: str) -> int:
    return sum(1 for tok in tokenize.generate_tokens(io.StringIO(text).readline) if tok.type == tokenize.NUMBER and tok.string == '3.0')


def test_header_version_sync() -> None:
    src = _src_text()
    assert '버전: v130' in src
    assert 'current_version: v130' in POINTER.read_text(encoding='utf-8')
    assert '기준 버전: `v130`' in HANDOFF.read_text(encoding='utf-8')
    assert '현재 기준 세트는 `v130`' in START.read_text(encoding='utf-8')


def test_no_plain_except_exception_ast() -> None:
    tree = _parse_tree()
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type and isinstance(node.type, ast.Name) and node.type.id == 'Exception':
            assert node.name is not None, f'plain except Exception remains at line {node.lineno}'


def test_swallow_exception_no_self_recursion() -> None:
    tree = _parse_tree()
    fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == '_swallow_exception')
    calls = [node.lineno for node in ast.walk(fn) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == '_swallow_exception']
    assert not calls, f'_swallow_exception self-call remains: {calls}'


def test_no_top_level_duplicate_function_defs() -> None:
    tree = _parse_tree()
    names = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
    dupes = sorted({name for name in names if names.count(name) > 1})
    assert not dupes, f'duplicate top-level defs: {dupes}'


def test_no_actual_print_calls_ast() -> None:
    tree = _parse_tree()
    lines = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'print']
    assert not lines, f'actual print() call remains: {lines[:10]}'


def test_no_direct_json_state_join() -> None:
    text = _src_text()
    assert re.search(r'os\.path\.join\(DATA_DIR,\s*"[^"\n]+\.json"\)', text) is None
    assert re.search(r"os\.path\.join\(DATA_DIR,\s*'[^'\n]+\.json'\)", text) is None


def test_state_path_helper_present() -> None:
    names = _helper_names(_parse_tree())
    assert '_state_path' in names
    assert _src_text().count('_state_path(') >= 30


def test_raw_3_token_reduced_to_common_constant() -> None:
    text = _src_text()
    assert 'COMMON_THRESHOLD_3P0 = 3.0' in text
    assert _raw_3_tokens(text) <= 1


def test_v128_startup_hotfix_signature() -> None:
    src = _src_text()
    assert 'def _purge_stale_entry_watch_hits(notify: bool = False) -> int:' in src
    assert '_purge_stale_entry_watch_hits(notify=True)' in src


def test_v128_fallback_helpers_present() -> None:
    src = _src_text()
    names = _helper_names(_parse_tree())
    assert '_warn_throttled_once' in names
    assert 'safe_json_response(resp)' in src
    assert 'telegram_api_timeout' in src


def test_v128_fallback_hotfix_paths() -> None:
    src = _src_text()
    assert '_warn_throttled_once("geo_api_empty_response"' in src
    assert '_warn_throttled_once("geo_api_blank_text"' in src
    assert '_warn_throttled_once(f"short_sell_ratio:{code}"' in src
    assert '_warn_throttled_once("us_market_invalid_json"' in src


def test_v128_finish_batch_spans() -> None:
    tree = _parse_tree()
    assert _function_span(tree, '_fetch_us_market_signal_values') < 40
    assert _function_span(tree, 'get_short_sell_ratio') < 30
    assert _function_span(tree, 'analyze_geopolitical_event') < 30
    assert _function_span(tree, '_requests_get_with_defaults') < 15


def test_no_function_over_200_lines() -> None:
    spans = _all_function_spans(_parse_tree())
    over = {name: span for name, span in spans.items() if span > 200}
    assert not over, f'200+ functions remain: {over}'


def test_print_count_not_increased() -> None:
    assert _src_text().count('print(') <= PREV_SRC.read_text(encoding='utf-8').count('print(')


def test_bom_absent() -> None:
    bom = bytes([0xEF, 0xBB, 0xBF])
    for path in [SRC, POINTER, HANDOFF, START, RULES, BASE / 'v130_smoke_test.py']:
        assert not path.read_bytes().startswith(bom), f'BOM present: {path.name}'

def test_v130_first_entry_reached_header_logic() -> None:
    src = _src_text()
    assert '_apply_first_entry_reached_header_line' in src
    assert '+ 1차 진입가 도달' in src
    assert '_is_general_capture_first_entry_reached' in src


def test_v130_nxt_early_detection_path() -> None:
    src = _src_text()
    assert 'def check_nxt_intraday_early_detection' in src
    assert '_record_nxt_intraday_candidate_stage' in src
    assert '_scan_early_pullback_candidates' in src and 'check_nxt_intraday_early_detection(existing_codes=seen)' in src


def test_v130_html_import_present() -> None:
    src = _src_text()
    assert 'import html' in src


def test_v130_emergency_alert_stage_dedupe() -> None:
    src = _src_text()
    assert 'last_emergency_alert_stage' in src
    assert 'last_emergency_alert_hash' in src
    assert 'def _build_emergency_tuning_alert' in src
    assert '_auto_tune_apply_emergency_tuning(completed, tune_state, changes, notify=notify)' in src

if __name__ == '__main__':
    for name, fn in sorted(globals().items()):
        if name.startswith('test_') and callable(fn):
            fn()
    print('v130 smoke ok')
