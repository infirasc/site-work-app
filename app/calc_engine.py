"""Feature 1 — 핵심 지표 계산 엔진 (specs/feature-1-spec.md 구현)"""

import math
from decimal import Decimal, ROUND_HALF_UP

REQUIRED_FIELDS = [
    "연면적_m2",
    "건축면적_m2",
    "대지면적_m2",
    "총보증금_억원",
    "총월임대료_억원",
    "총관리비_억원_연간",
    "매입가능예상가격_억원",
    "전월세환산이율_퍼센트",
    "평당건축비_억원",
    "ExitCapRate_퍼센트",
]

# 나눗셈 분모로 쓰이는 항목 — 0이면 정지
ZERO_DENOMINATOR_FIELDS = ["대지면적_m2", "매입가능예상가격_억원", "ExitCapRate_퍼센트"]


def _is_bad_number(v):
    return isinstance(v, float) and (math.isnan(v) or math.isinf(v))


def validate(inputs: dict) -> list[str]:
    errors = []
    for field in REQUIRED_FIELDS:
        value = inputs.get(field)
        if value is None:
            errors.append(f"{field}: 값이 비어 있음")
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(f"{field}: 숫자가 아님")
            continue
        if _is_bad_number(value):
            errors.append(f"{field}: 계산불가한 값(NaN/무한대)")
            continue
        if value < 0:
            errors.append(f"{field}: 음수는 입력할 수 없음")
            continue
        if field in ZERO_DENOMINATOR_FIELDS and value == 0:
            errors.append(f"{field}: 0은 허용되지 않음 (나눗셈 분모)")
    return errors


def _d(value) -> Decimal:
    # str(value)를 거쳐 변환해 이진 부동소수점 오차(예: 0.1+0.2 != 0.3)가
    # 계산에 섞여 들어가지 않도록 함 — 입력값 그대로의 십진수로 취급
    return Decimal(str(value))


def _round2(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


# 검증된(0이 아님이 보장된) 입력값끼리의 나눗셈과 달리, 계산 중간에 나온 값(GDV 등)이
# 우연히 0이 되는 경우가 있음 — 이때는 예외를 던지지 않고 "산출 어려움" + 사유로 대체함
def _safe_div(numerator: Decimal, denominator: Decimal, reason: str):
    if denominator == 0:
        return None, reason
    return numerator / denominator, None


def calculate(inputs: dict) -> dict:
    errors = validate(inputs)
    if errors:
        return {"ok": False, "errors": errors}

    총월임대료 = _d(inputs["총월임대료_억원"])
    총보증금 = _d(inputs["총보증금_억원"])
    환산이율 = _d(inputs["전월세환산이율_퍼센트"]) / Decimal(100)
    총관리비 = _d(inputs["총관리비_억원_연간"])
    매입가 = _d(inputs["매입가능예상가격_억원"])
    연면적 = _d(inputs["연면적_m2"])
    건축면적 = _d(inputs["건축면적_m2"])
    대지면적 = _d(inputs["대지면적_m2"])
    평당건축비 = _d(inputs["평당건축비_억원"])
    exit_cap = _d(inputs["ExitCapRate_퍼센트"]) / Decimal(100)

    noi = (총월임대료 * 12) + (총보증금 * 환산이율) - 총관리비
    cap_rate = noi / 매입가 * 100
    용적률 = 연면적 / 대지면적 * 100
    건폐율 = 건축면적 / 대지면적 * 100
    공사비 = 연면적 * 평당건축비
    tdc = 매입가 + 공사비
    gdv = noi / exit_cap
    profit = gdv - tdc

    # GDV가 0이면(NOI가 0인 경우 등) Development Margin을 계산할 수 없음 —
    # 계산을 멈추지 않고 넘어가되, 값 대신 "산출 어려움"과 사유를 반환함
    margin_raw, margin_reason = _safe_div(
        profit, gdv, "GDV(개발 후 가치)가 0이라 Development Margin을 계산할 수 없음 (NOI가 0이면 GDV도 0이 됨)"
    )

    result = {
        "ok": True,
        "핵심지표": {
            "CapRate_퍼센트": _round2(cap_rate),
            "용적률_퍼센트": _round2(용적률),
            "건폐율_퍼센트": _round2(건폐율),
            "DevelopmentProfit_억원": _round2(profit),
            "DevelopmentMargin_퍼센트": _round2(margin_raw * 100) if margin_raw is not None else "산출 어려움",
        },
        "중간값": {
            "NOI_억원": _round2(noi),
            "공사비_억원": _round2(공사비),
            "TDC_억원": _round2(tdc),
            "GDV_억원": _round2(gdv),
        },
    }
    if margin_reason is not None:
        result["산출불가사유"] = {"DevelopmentMargin_퍼센트": margin_reason}
    return result
