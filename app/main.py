"""feature-2-spec.md 기준 실행 확인용 스크립트.

inputs/feature-2-sample-input.json을 읽어 Feature 1(계산 엔진) →
Feature 2(리포트 데이터 매핑) → Feature 3(마크다운 리포트 렌더링)을
순서대로 실행하고 각 단계의 결과를 출력한다.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from calc_engine import REQUIRED_FIELDS, calculate
from report_mapper import REFERENCE_FIELDS, map_report
from report_renderer import render_markdown

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_INPUT_PATH = os.path.join(PROJECT_ROOT, "inputs", "feature-2-sample-input.json")

REQUIRED_TOP_LEVEL_KEYS = ["주소", "작성일", "필수_입력값", "참고용_입력값", "계산용_외부값_수동입력_대체"]


def _load_sample(path: str) -> dict:
    """입력 파일을 읽어 JSON으로 파싱하고 최상위 구조를 확인한다.

    파일이 없거나 JSON이 깨지거나 최상위 키가 빠져도 예외를 그대로 던지지 않고
    calc_engine/report_mapper와 같은 {"ok": bool, ...} 형태로 반환한다 — main.py의
    입력 로딩 단계도 나머지 파이프라인과 동일한 실패 규약을 따르게 하기 위함.
    """
    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
    except OSError as e:
        return {"ok": False, "errors": [f"입력 파일을 찾을 수 없음: {path}"], "원본오류": str(e)}

    try:
        sample = json.loads(raw)
    except json.JSONDecodeError as e:
        return {"ok": False, "errors": ["입력 파일의 JSON 형식이 올바르지 않음"], "원본오류": str(e)}

    missing = [key for key in REQUIRED_TOP_LEVEL_KEYS if key not in sample]
    if missing:
        return {"ok": False, "errors": [f"입력 파일에 다음 항목이 없음: {', '.join(missing)}"]}

    return {"ok": True, "sample": sample}


def _print_input_guide():
    """오류 발생 시, 무엇을 채워 넣어야 하는지 필수/참고용 입력 항목을 그대로 보여준다."""
    print("\n### 다음 입력값들을 확인해서 다시 넣어주세요")
    print(f"필수 입력값 ({len(REQUIRED_FIELDS)}개, 비거나 잘못되면 계산이 멈춤):")
    for field in REQUIRED_FIELDS:
        print(f"  - {field}")
    print(f"참고용 입력값 ({len(REFERENCE_FIELDS)}개, 비어도 진행되며 '정보 없음'으로 표시됨):")
    for field in REFERENCE_FIELDS:
        print(f"  - {field}")


def main():
    loaded = _load_sample(SAMPLE_INPUT_PATH)
    if not loaded["ok"]:
        print("=== 입력 파일 확인 실패 ===")
        for err in loaded["errors"]:
            print(f"- {err}")
        if "원본오류" in loaded:
            print(f"(원본 오류: {loaded['원본오류']})")
        _print_input_guide()
        return

    sample = loaded["sample"]

    required_inputs = sample["필수_입력값"]
    external_values = {
        k: v for k, v in sample["계산용_외부값_수동입력_대체"].items() if not k.startswith("_")
    }
    reference_inputs = {
        k: v for k, v in sample["참고용_입력값"].items() if not k.startswith("_")
    }

    calc_inputs = {**required_inputs, **external_values}

    print("=== Feature 1: 계산 엔진 실행 ===")
    calc_result = calculate(calc_inputs)
    print(json.dumps(calc_result, ensure_ascii=False, indent=2))
    if not calc_result.get("ok"):
        _print_input_guide()
        return

    print("\n=== Feature 2: 리포트 데이터 매핑 실행 ===")
    report_result = map_report(
        calc_result=calc_result,
        # feature-2-spec.md: "Feature 1이 이미 검증한 필수 입력값"에는
        # 계산용 외부값(전월세환산이율·평당건축비·ExitCapRate)도 포함됨
        required_inputs=calc_inputs,
        reference_inputs=reference_inputs,
        address=sample["주소"],
        report_date=sample["작성일"],
    )
    print(json.dumps(report_result, ensure_ascii=False, indent=2))
    if not report_result.get("ok"):
        _print_input_guide()
        return

    print("\n=== Feature 3: 리포트 렌더링 (마크다운) ===")
    print(render_markdown(report_result))


if __name__ == "__main__":
    main()
