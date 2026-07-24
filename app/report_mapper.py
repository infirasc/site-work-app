"""Feature 2 — 리포트 데이터 매핑 (specs/feature-2-spec.md 구현)"""

import math

from calc_engine import REQUIRED_FIELDS

REFERENCE_FIELDS = [
    "주변실거래및감정평가시세_억원",
    "매물시세_억원",
    "공시지가시세대비가격_억원",
    "건물연식_준공연도",
    "총임대인수_명",
    "유동인구_명",
    "엘리베이터유무",
    "주차장_면",
]


def _display(value):
    if value is None:
        return "정보 없음"
    if isinstance(value, bool):
        return "있음" if value else "없음"
    return value


def _is_bad(value):
    if value is None:
        return True
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return True
    return False


# calc_engine이 "산출 어려움"으로 표시한 값(예: GDV가 0이라 Development Margin을
# 못 구한 경우)은 계산 실패가 아니라 의도된 대체 표시이므로 검증에서 막지 않음
def _is_calc_unavailable(value):
    return value == "산출 어려움"


def map_report(calc_result: dict, required_inputs: dict, reference_inputs: dict,
                address: str, report_date: str) -> dict:
    # 1. 매핑 전 검증
    errors = []

    if not calc_result.get("ok"):
        return {"ok": False, "errors": calc_result.get("errors", ["계산 결과가 없음"])}

    for field in REQUIRED_FIELDS:
        if _is_bad(required_inputs.get(field)):
            errors.append(f"{field}: 값이 비어있거나 계산 실패")

    for group in ("핵심지표", "중간값"):
        for key, value in calc_result[group].items():
            if _is_calc_unavailable(value):
                continue
            if _is_bad(value):
                errors.append(f"{key}: 계산값이 비어있거나 계산 실패")

    if errors:
        return {"ok": False, "errors": errors}

    # 2. 참고용 입력값 — 비어있으면 "정보 없음"
    ref = {field: _display(reference_inputs.get(field)) for field in REFERENCE_FIELDS}
    핵심 = calc_result["핵심지표"]
    중간 = calc_result["중간값"]

    # 3. 8개 섹션에 값 배치
    report = {
        "1_표지": {
            "주소지": address,
            "작성일": report_date,
        },
        "2_핵심지표요약": {
            "CapRate_퍼센트": 핵심["CapRate_퍼센트"],
            "용적률_퍼센트": 핵심["용적률_퍼센트"],
            "건폐율_퍼센트": 핵심["건폐율_퍼센트"],
            "DevelopmentProfit_억원": 핵심["DevelopmentProfit_억원"],
            "DevelopmentMargin_퍼센트": 핵심["DevelopmentMargin_퍼센트"],
        },
        "3_부동산개요": {
            "연면적_m2": required_inputs["연면적_m2"],
            "건축면적_m2": required_inputs["건축면적_m2"],
            "대지면적_m2": required_inputs["대지면적_m2"],
            "건물연식_준공연도": ref["건물연식_준공연도"],
            "용적률_퍼센트": 핵심["용적률_퍼센트"],
            "건폐율_퍼센트": 핵심["건폐율_퍼센트"],
        },
        "4_시세정보": {
            "주변실거래및감정평가시세_억원": ref["주변실거래및감정평가시세_억원"],
            "매물시세_억원": ref["매물시세_억원"],
            "공시지가시세대비가격_억원": ref["공시지가시세대비가격_억원"],
            "매입가능예상가격_억원": required_inputs["매입가능예상가격_억원"],
        },
        "5_임차현황": {
            "총임대인수_명": ref["총임대인수_명"],
            "총보증금_억원": required_inputs["총보증금_억원"],
            "총월임대료_억원": required_inputs["총월임대료_억원"],
            "총관리비_억원_연간": required_inputs["총관리비_억원_연간"],
        },
        "6_입지특성": {
            "유동인구_명": ref["유동인구_명"],
            "엘리베이터유무": ref["엘리베이터유무"],
            "주차장_면": ref["주차장_면"],
        },
        "7_수익성분석": {
            "NOI_억원": 중간["NOI_억원"],
            "CapRate_퍼센트": 핵심["CapRate_퍼센트"],
        },
        "8_개발사업성분석": {
            "TDC_억원": 중간["TDC_억원"],
            "GDV_억원": 중간["GDV_억원"],
            "DevelopmentProfit_억원": 핵심["DevelopmentProfit_억원"],
            "DevelopmentMargin_퍼센트": 핵심["DevelopmentMargin_퍼센트"],
        },
    }

    result = {"ok": True, "report": report}
    if "산출불가사유" in calc_result:
        result["산출불가사유"] = calc_result["산출불가사유"]
    return result
