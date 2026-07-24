"""Feature 3 (MVP) — report_mapper.py의 결과를 사람이 읽는 마크다운 줄글로 렌더링.

웹 화면·PDF는 아직 없으므로(specs/feature-1-spec.md, feature-2-spec.md의 "지금은
뺄 것" 참고), 스펙이 말하는 "웹 화면에 리포트 렌더링" 단계를 우선 마크다운 줄글로
대신한다.
"""

MARGIN_KEY = "DevelopmentMargin_퍼센트"


def _interpret_margin_rule_based(margin):
    """Development Margin(%)을 고정 구간 기준으로 라벨링한다.

    기준: 0 이하 → 사업성 없음 / 100 이상 → 매우 추천 / 50~100 → 권장 / 그 사이(0 초과 50 미만) → 보통.
    "생성방식"을 별도 필드로 둔 이유: 나중에 이 자리를 규칙 기반 대신 AI가 생성한
    코멘트로 바꿔 끼울 수 있도록 여지를 남겨두기 위함(interpret_margin의 interpreter 인자 참고).
    """
    if not isinstance(margin, (int, float)) or isinstance(margin, bool):
        return {"라벨": "산출 어려움", "생성방식": "규칙 기반"}
    if margin <= 0:
        label = "사업성 없음"
    elif margin < 50:
        label = "보통"
    elif margin < 100:
        label = "권장"
    else:
        label = "매우 추천"
    return {"라벨": label, "생성방식": "규칙 기반(고정 구간)"}


def interpret_margin(margin, interpreter=None):
    """margin 해석 진입점. interpreter를 넘기면 규칙 기반 대신 그것을 쓴다(예: 향후 AI 코멘트 생성기)."""
    if interpreter is not None:
        return interpreter(margin)
    return _interpret_margin_rule_based(margin)


def _fmt(value, unit=""):
    """숫자면 단위를 붙이고, "산출 어려움"·"정보 없음" 같은 문자열이면 그대로 보여준다."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{value}{unit}"
    return str(value)


def render_markdown(report_result: dict, interpreter=None) -> str:
    """map_report()의 결과를 마크다운 문자열로 바꾼다. 실패 시에도 원본 오류를 그대로 보여준다."""
    if not report_result.get("ok"):
        lines = ["# 리포트를 만들 수 없음", ""]
        lines.extend(f"- {err}" for err in report_result.get("errors", []))
        return "\n".join(lines)

    report = report_result["report"]
    reasons = report_result.get("산출불가사유", {})

    cover = report["1_표지"]
    핵심 = report["2_핵심지표요약"]
    개요 = report["3_부동산개요"]
    시세 = report["4_시세정보"]
    임차 = report["5_임차현황"]
    입지 = report["6_입지특성"]
    수익 = report["7_수익성분석"]
    개발 = report["8_개발사업성분석"]

    margin_value = 핵심[MARGIN_KEY]
    margin_interp = interpret_margin(margin_value, interpreter)

    def note(field_key):
        return f" _(사유: {reasons[field_key]})_" if field_key in reasons else ""

    lines = [
        f"# 부동산 개발 리포트 — {cover['주소지']}",
        "",
        "## 1. 표지",
        f"- 주소지: {cover['주소지']}",
        f"- 작성일: {cover['작성일']}",
        "",
        "## 2. 핵심 지표 요약",
        f"- Cap Rate: {_fmt(핵심['CapRate_퍼센트'], '%')}",
        f"- 용적률: {_fmt(핵심['용적률_퍼센트'], '%')}",
        f"- 건폐율: {_fmt(핵심['건폐율_퍼센트'], '%')}",
        f"- Development Profit: {_fmt(핵심['DevelopmentProfit_억원'], '억원')}",
        f"- Development Margin: {_fmt(margin_value, '%')}{note(MARGIN_KEY)}",
        f"- 사업성 해석: **{margin_interp['라벨']}** _(산정방식: {margin_interp['생성방식']})_",
        "",
        "## 3. 부동산 개요",
        f"- 연면적 {_fmt(개요['연면적_m2'], 'm²')} · 건축면적 {_fmt(개요['건축면적_m2'], 'm²')} · 대지면적 {_fmt(개요['대지면적_m2'], 'm²')}",
        f"- 건물 연식(준공연도): {_fmt(개요['건물연식_준공연도'])}",
        f"- 용적률 {_fmt(개요['용적률_퍼센트'], '%')} · 건폐율 {_fmt(개요['건폐율_퍼센트'], '%')}",
        "",
        "## 4. 시세 정보",
        f"- 주변 실거래 및 감정평가 시세: {_fmt(시세['주변실거래및감정평가시세_억원'], '억원')}",
        f"- 매물 시세: {_fmt(시세['매물시세_억원'], '억원')}",
        f"- 공시지가 시세 대비 가격: {_fmt(시세['공시지가시세대비가격_억원'], '억원')}",
        f"- 매입가능예상가격: {_fmt(시세['매입가능예상가격_억원'], '억원')}",
        "",
        "## 5. 임차 현황",
        f"- 총 임대인 수: {_fmt(임차['총임대인수_명'], '명')}",
        f"- 총 보증금: {_fmt(임차['총보증금_억원'], '억원')} · 총 월임대료: {_fmt(임차['총월임대료_억원'], '억원')} · 총 관리비(연간): {_fmt(임차['총관리비_억원_연간'], '억원')}",
        "",
        "## 6. 입지 특성",
        f"- 유동인구: {_fmt(입지['유동인구_명'], '명')}",
        f"- 엘리베이터 유무: {_fmt(입지['엘리베이터유무'])}",
        f"- 주차장: {_fmt(입지['주차장_면'], '면')}",
        "",
        "## 7. 수익성 분석",
        f"- NOI: {_fmt(수익['NOI_억원'], '억원')}",
        f"- Cap Rate: {_fmt(수익['CapRate_퍼센트'], '%')}",
        "",
        "## 8. 개발 사업성 분석",
        f"- TDC(총개발비용): {_fmt(개발['TDC_억원'], '억원')}",
        f"- GDV(개발 후 가치): {_fmt(개발['GDV_억원'], '억원')}",
        f"- Development Profit: {_fmt(개발['DevelopmentProfit_억원'], '억원')}",
        f"- Development Margin: {_fmt(개발[MARGIN_KEY], '%')}{note(MARGIN_KEY)}",
        f"- 사업성 해석: **{margin_interp['라벨']}**",
        "",
    ]
    return "\n".join(lines)
