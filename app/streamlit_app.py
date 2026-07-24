"""부동산 개발 리포트 자동화 — 터미널 없이 쓰는 웹 화면 (Streamlit).

기존 파이프라인(calc_engine.py → report_mapper.py → report_renderer.py)은
전혀 건드리지 않고, 그 위에 입력 폼 + 버튼 + 결과 화면(2칼럼 압축 뷰 + .md 다운로드)만 얹은 것이다.
main.py(터미널 실행용)와 이 파일은 서로 독립적으로 같은 파이프라인을 호출한다.

실행법:
    streamlit run app/streamlit_app.py
(라이트 테마 강제·입력창 배경색은 프로젝트 루트의 .streamlit/config.toml에서 설정함)
"""

import io
import os
import sys
from datetime import date

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from openai import OpenAI

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from calc_engine import REQUIRED_FIELDS, calculate
from report_mapper import REFERENCE_FIELDS, map_report
from report_renderer import interpret_margin, render_markdown

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# "Hyer Aviation" 스타일 가이드(DESIGN (2).md)에서 가져온 디자인 토큰.
# 187px 히어로 타이포·3D 제트 이미지 같은 브랜드 전용 요소는 이 폼 화면 성격과 안 맞아 빼고,
# 색상·타이포 굵기/자간·필 버튼·헤어라인 구분선·클레이 강조색 1곳(사업성 해석 배지)만 가져옴.
COLOR_DEEP_INK = "#000d10"
COLOR_PURE_WHITE = "#ffffff"
COLOR_COOL_ASH = "#8e8e95"
COLOR_PEBBLE = "#d5d3d4"
COLOR_CLAY_EMBER = "#bc7155"
COLOR_INPUT_FILL = "#f4f3f1"  # 기존 진한 배경 대신 쓰는 연한 입력창 색 (.streamlit/config.toml의 secondaryBackgroundColor와 동일)

DESIGN_CSS = f"""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');

/* .stApp에만 걸어서 상속으로 퍼지게 함 — 아이콘 폰트(stIconMaterial)에는 안 번지도록 광범위 셀렉터는 피함 */
.stApp {{
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
    background-color: {COLOR_PURE_WHITE};
    color: {COLOR_DEEP_INK};
}}
div[data-testid="stIconMaterial"] {{
    font-family: 'Material Symbols Rounded' !important;
}}

/* 헤딩: 근흑색 + 볼드 + 타이트한 자간 (Hyer의 "무게 자체가 브랜드 목소리" 원칙) */
h1, h2, h3 {{
    color: {COLOR_DEEP_INK} !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}}
h2 {{
    border-top: 1px solid {COLOR_PEBBLE};
    padding-top: 28px !important;
    margin-top: 12px !important;
}}

/* 캡션(부제) 텍스트는 톤 다운된 애시 그레이 */
div[data-testid="stCaptionContainer"] p {{
    color: {COLOR_COOL_ASH} !important;
}}

/* 입력창 라벨(제목) — 라이트/다크 모드와 무관하게 항상 진하게 보이도록 강제 (전에 안 보이던 문제 수정) */
label[data-testid="stWidgetLabel"] p,
div[data-testid="stWidgetLabel"] p {{
    color: {COLOR_DEEP_INK} !important;
    font-weight: 600 !important;
    opacity: 1 !important;
}}

/* 기본(secondary) 버튼: 필 모양 + 헤어라인 테두리 */
button[data-testid="stBaseButton-secondary"] {{
    border-radius: 1000px !important;
    border: 1px solid {COLOR_DEEP_INK} !important;
    color: {COLOR_DEEP_INK} !important;
}}
/* 주요(primary) 버튼 = "리포트 생성": 근흑색 필 버튼 — Hyer의 Filled Dark Pill Button */
button[data-testid="stBaseButton-primary"] {{
    background-color: {COLOR_DEEP_INK} !important;
    border: none !important;
    border-radius: 1000px !important;
    color: {COLOR_PURE_WHITE} !important;
    font-weight: 700 !important;
    padding: 4px 28px !important;
}}
button[data-testid="stBaseButton-primary"]:hover {{
    background-color: #1a2a30 !important;
    color: {COLOR_PURE_WHITE} !important;
}}

/* 입력창: 진한 배경 대신 연한 배경 + 헤어라인 테두리, 그림자 없음 */
div[data-testid="stTextInput"] input,
div[data-baseweb="select"] > div {{
    background-color: {COLOR_INPUT_FILL} !important;
    border-radius: 4px !important;
    border: 1px solid {COLOR_PEBBLE} !important;
    box-shadow: none !important;
    color: {COLOR_DEEP_INK} !important;
}}
/* "주소" 칸처럼 readonly로 표시만 하는 입력창 — 직접 못 고친다는 걸 시각적으로도 알려줌 */
div[data-testid="stTextInput"] input[readonly] {{
    background-color: #ececea !important;
    cursor: default !important;
}}

/* 사업성 해석 배지 — Hyer의 "클레이 강조색은 페이지당 딱 한 곳" 원칙을 여기 하나에만 적용 */
.verdict-badge {{
    background-color: {COLOR_CLAY_EMBER};
    color: {COLOR_PURE_WHITE};
    border-radius: 4px;
    padding: 16px 20px;
    font-size: 18px;
    font-weight: 700;
    margin: 16px 0 4px 0;
}}
.verdict-badge .verdict-sub {{
    display: block;
    margin-top: 2px;
    font-size: 13px;
    font-weight: 400;
    opacity: 0.9;
}}
.verdict-reasons {{
    margin: 4px 0 16px 0;
    padding-left: 20px;
    font-size: 13px;
    color: {COLOR_COOL_ASH};
}}
.verdict-reasons li {{
    margin-bottom: 2px;
}}

/* 결과 리포트 — 왼쪽 사진 자리 + 오른쪽 단일 칼럼 리포트 본문 */
.report-title {{
    font-size: 26px;
    font-weight: 700;
    color: {COLOR_DEEP_INK};
    margin-bottom: 2px;
}}
.report-sub {{
    color: {COLOR_COOL_ASH};
    font-size: 14px;
    margin-bottom: 12px;
}}
.report-section-title {{
    font-weight: 700;
    font-size: 17px;
    color: {COLOR_DEEP_INK};
    border-top: 1px solid {COLOR_PEBBLE};
    padding-top: 10px;
    margin-top: 16px;
}}
.report-list {{
    margin: 6px 0 0 0;
    padding-left: 18px;
    font-size: 15px;
    line-height: 1.7;
}}
.report-list li {{
    margin-bottom: 3px;
}}
.report-list b {{
    font-size: 16px;
    font-weight: 700;
    color: {COLOR_DEEP_INK};
}}

/* 결과 화면 좌측 — AI 현장 사진(로드뷰 기반 렌더링) 자리. 아직 자동 생성 기능은
   없어서(specs 상 예정), 사람이 직접 올려서 보여줄 수 있는 자리만 마련해둔 것 */
.report-photo-slot {{
    height: 100%;
    min-height: 320px;
    border: 1px dashed {COLOR_PEBBLE};
    border-radius: 8px;
    background-color: {COLOR_INPUT_FILL};
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    color: {COLOR_COOL_ASH};
    font-size: 14px;
    line-height: 1.6;
    padding: 24px;
}}
.report-photo-slot .icon {{
    font-size: 40px;
    margin-bottom: 10px;
}}

/* 엑셀 분석 탭 — "눈에 띄는 항목" 카드 그리드 */
.notable-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 14px;
    margin: 8px 0 20px 0;
}}
.notable-card {{
    border: 1px solid {COLOR_PEBBLE};
    border-radius: 4px;
    padding: 14px 16px;
    background-color: {COLOR_PURE_WHITE};
}}
.notable-col-name {{
    font-size: 16px;
    font-weight: 700;
    color: {COLOR_DEEP_INK};
    margin-bottom: 8px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.notable-stat {{
    font-size: 13px;
    color: {COLOR_DEEP_INK};
    margin-bottom: 3px;
}}
.notable-stat b {{
    font-size: 17px;
    font-weight: 700;
    color: {COLOR_DEEP_INK};
    margin: 0 2px;
}}
.notable-row-ref {{
    font-size: 11px;
    color: {COLOR_COOL_ASH};
}}

/* 우측 하단 플로팅 챗봇 — 탭 바깥(최상위)에 둬서 어느 탭에 있든 항상 보이고,
   position: fixed라 스크롤해도 같은 자리에 그대로 떠 있음 */
.st-key-chatbot_fab {{
    position: fixed !important;
    bottom: 24px;
    right: 24px;
    z-index: 9999;
    width: fit-content !important;
    left: auto !important;
}}
.st-key-chatbot_fab .stButton button {{
    border-radius: 1000px !important;
}}
/* st.markdown으로 연 <div>는 위젯을 실제로 감싸지 못해서(각 st 호출이 별도 엘리먼트라
   여는 태그와 닫는 태그가 서로 다른 조각이 됨— 빈 <div></div>만 남는 버그였음),
   진짜로 감싸려면 st.container(key=...)를 하나 더 써야 한다. */
.st-key-chatbot_panel_box {{
    width: 340px;
    background-color: {COLOR_PURE_WHITE};
    border: 1px solid {COLOR_PEBBLE};
    border-radius: 12px;
    padding: 16px;
}}
.chatbot-panel-title {{
    font-size: 15px;
    font-weight: 700;
    color: {COLOR_DEEP_INK};
    margin-bottom: 8px;
}}
</style>
"""

# (필드 키, 화면에 보여줄 라벨) — REQUIRED_FIELDS/REFERENCE_FIELDS와 어긋나면 바로 알아채도록 아래에서 검증함
REQUIRED_FIELD_META = [
    ("연면적_m2", "연면적 (m²)"),
    ("건축면적_m2", "건축면적 (m²)"),
    ("대지면적_m2", "대지면적 (m²)"),
    ("총보증금_억원", "총 보증금 (억원)"),
    ("총월임대료_억원", "총 월임대료 (억원)"),
    ("총관리비_억원_연간", "총 관리비 (억원, 연간)"),
    ("매입가능예상가격_억원", "매입가능예상가격 (억원)"),
    ("전월세환산이율_퍼센트", "전월세 환산이율 (%)"),
    ("평당건축비_억원", "평당 건축비 (억원)"),
    ("ExitCapRate_퍼센트", "Exit Cap Rate (%)"),
]

REFERENCE_FIELD_META = [
    ("주변실거래및감정평가시세_억원", "주변 실거래 및 감정평가 시세 (억원)", "number"),
    ("매물시세_억원", "매물 시세 (억원)", "number"),
    ("공시지가시세대비가격_억원", "공시지가 시세 대비 가격 (억원)", "number"),
    ("건물연식_준공연도", "건물 연식 (준공연도)", "number"),
    ("총임대인수_명", "총 임대인 수 (명)", "number"),
    ("유동인구_명", "유동인구 (명)", "number"),
    ("엘리베이터유무", "엘리베이터 유무", "bool"),
    ("주차장_면", "주차장 (면)", "number"),
]

assert {k for k, _ in REQUIRED_FIELD_META} == set(REQUIRED_FIELDS), "REQUIRED_FIELD_META가 calc_engine.REQUIRED_FIELDS와 어긋남"
assert {k for k, _, _ in REFERENCE_FIELD_META} == set(REFERENCE_FIELDS), "REFERENCE_FIELD_META가 report_mapper.REFERENCE_FIELDS와 어긋남"

# 카카오 우편번호(주소 검색) — 별도 입력칸/버튼 없이, 이 검색창 자체가 유일한 주소 입력 UI.
# 페이지에 항상 그려두고(토글 없음), 주소를 고르면 부모 문서(Streamlit 페이지)의 숨겨진
# "주소" input(hidden_address_bridge)을 JS로 직접 채우고 input/change 이벤트를 발생시켜
# React(Streamlit 프론트엔드)가 값 변경을 인식하게 만든다.
# 팝업(.open()) 대신 embed()를 쓰는 이유: 팝업 방식은 별도 창을 열고 그 창이 다시 opener
# 창으로 결과를 돌려주는 다단계 구조라 더 복잡하고 불안정함.
#
# components.html()이 아니라 components.v1.iframe(src=...)로 불러오는 이유:
# components.html()은 sandboxed iframe(sandbox="allow-scripts allow-same-origin ...")에
# 코드를 넣는데, 이 sandbox 제약 때문에 카카오 위젯 내부의 "검색결과 클릭 → 완료 신호"가
# 전달되지 않는 문제를 실제로 재현·확인했다(순수 HTML 페이지에서는 정상 동작, 같은 코드를
# components.html 안에 넣으면 검색은 되는데 클릭 완료(oncomplete)가 전혀 안 옴).
#
# Streamlit 자체 정적 파일 서빙(server.enableStaticServing, app/static/)은 로컬에서는
# 됐지만 Streamlit Community Cloud 배포본에서는 해당 경로가 빈 화면으로 떠서(확인됨) 못 쓴다.
# 대신 이 저장소의 GitHub Pages(docs/kakao_address_search.html)에 페이지를 올려두고,
# 그 실제 외부 URL을 iframe으로 불러온다 — 로컬/배포 환경 구분 없이 항상 동일하게 동작한다.
KAKAO_ADDRESS_SEARCH_URL = "https://infirasc.github.io/site-work-app/kakao_address_search.html"


def _parse_number(raw: str):
    """빈 문자열은 None(값 없음)으로, 그 외는 float 변환을 시도하고 실패하면 원본 문자열 그대로 둔다.

    숫자 변환 실패를 여기서 에러 처리하지 않는 이유: calc_engine.validate()가
    "숫자가 아님"을 이미 판단해주므로, 검증 로직을 이 화면에 중복으로 두지 않기 위함.
    """
    raw = raw.strip()
    if raw == "":
        return None
    try:
        return float(raw)
    except ValueError:
        return raw


def _fmt(value, unit=""):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{value}{unit}"
    return str(value)


# 엑셀 항목명 -> 필드 키. 라벨("연면적 (m²)")과 필드 키("연면적_m2") 둘 다 인식한다.
_REQUIRED_FIELD_LOOKUP = {}
for _field_key, _field_label in REQUIRED_FIELD_META:
    _REQUIRED_FIELD_LOOKUP[_field_key.strip()] = _field_key
    _REQUIRED_FIELD_LOOKUP[_field_label.strip()] = _field_key


def _build_required_fields_template_bytes() -> bytes:
    df = pd.DataFrame({
        "항목": [label for _, label in REQUIRED_FIELD_META],
        "값": ["" for _ in REQUIRED_FIELD_META],
    })
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


def _apply_excel_to_required_fields(uploaded_file):
    """엑셀(1열: 항목명, 2열: 값, 1행은 머리글)을 읽어 필수 입력값 위젯의 session_state를 채운다.

    호출 시점이 중요하다 — 해당 required_<field> text_input 위젯이 이번 실행에서
    아직 생성되기 전이어야 한다(위젯 생성 후에는 그 키로 session_state를 재대입할 수 없음).
    """
    label_by_field = dict(REQUIRED_FIELD_META)
    try:
        df = pd.read_excel(uploaded_file)
    except Exception:
        return [], [], "엑셀 파일을 읽을 수 없습니다. .xlsx 또는 .xls 형식인지 확인해주세요."

    if df.shape[1] < 2:
        return [], [], "엑셀에 항목·값, 두 개의 열이 필요합니다."

    filled_labels = []
    unmatched_names = []
    for _, row in df.iloc[:, :2].iterrows():
        raw_name, raw_value = row.iloc[0], row.iloc[1]
        if pd.isna(raw_name) or pd.isna(raw_value):
            continue
        field = _REQUIRED_FIELD_LOOKUP.get(str(raw_name).strip())
        if field is None:
            unmatched_names.append(str(raw_name).strip())
            continue
        if isinstance(raw_value, float) and raw_value.is_integer():
            value_str = str(int(raw_value))
        else:
            value_str = str(raw_value).strip()
        st.session_state[f"required_{field}"] = value_str
        filled_labels.append(label_by_field[field])
    return filled_labels, unmatched_names, None


def _verdict_reasons(핵심: dict, 중간: dict, verdict: dict, calc_unavailable_reason: str | None) -> list[str]:
    """사업성 해석 라벨이 왜 그렇게 나왔는지, 있는 숫자를 근거로 짧게 나열한다.

    별도 AI 호출 없이 이미 계산된 값(핵심지표/중간값)만으로 규칙 기반 이유를 만든다 —
    report_renderer.interpret_margin()과 같은 "규칙 기반" 원칙을 유지하기 위함.
    """
    margin = 핵심["DevelopmentMargin_퍼센트"]
    if not isinstance(margin, (int, float)):
        return [calc_unavailable_reason] if calc_unavailable_reason else ["계산값이 없어 해석 근거를 만들 수 없음"]

    profit = 핵심["DevelopmentProfit_억원"]
    cap_rate = 핵심["CapRate_퍼센트"]
    return [
        f"Development Margin이 {margin}%로 '{verdict['라벨']}' 구간(기준: 0 이하/0~50/50~100/100 이상)에 해당함",
        f"Development Profit이 {profit}억원으로 {'적자' if profit < 0 else '흑자'}임",
        f"Cap Rate는 {cap_rate}%로, 매입가 대비 연간 수익률 수준임",
    ]


def _build_compact_report_html(report: dict, verdict: dict, reasons: list[str]) -> str:
    """리포트 8개 섹션을 2칼럼 HTML로 압축해, 웹에서 한 화면에 들어오도록 만든다."""
    cover = report["1_표지"]
    핵심 = report["2_핵심지표요약"]
    개요 = report["3_부동산개요"]
    시세 = report["4_시세정보"]
    임차 = report["5_임차현황"]
    입지 = report["6_입지특성"]
    수익 = report["7_수익성분석"]
    개발 = report["8_개발사업성분석"]

    reasons_html = "".join(f"<li>{r}</li>" for r in reasons)

    def b(value, unit=""):
        return f"<b>{_fmt(value, unit)}</b>"

    body = f"""
    <div class="report-section-title">1. 표지</div>
    <ul class="report-list">
        <li>주소지: {cover['주소지']}</li>
        <li>작성일: {cover['작성일']}</li>
    </ul>
    <div class="report-section-title">2. 핵심 지표 요약</div>
    <ul class="report-list">
        <li>Cap Rate: {b(핵심['CapRate_퍼센트'], '%')}</li>
        <li>용적률: {b(핵심['용적률_퍼센트'], '%')}</li>
        <li>건폐율: {b(핵심['건폐율_퍼센트'], '%')}</li>
        <li>Development Profit: {b(핵심['DevelopmentProfit_억원'], '억원')}</li>
        <li>Development Margin: {b(핵심['DevelopmentMargin_퍼센트'], '%')}</li>
    </ul>
    <div class="report-section-title">3. 부동산 개요</div>
    <ul class="report-list">
        <li>연면적 {_fmt(개요['연면적_m2'], 'm²')} · 건축면적 {_fmt(개요['건축면적_m2'], 'm²')} · 대지면적 {_fmt(개요['대지면적_m2'], 'm²')}</li>
        <li>건물 연식(준공연도): {_fmt(개요['건물연식_준공연도'])}</li>
        <li>용적률 {_fmt(개요['용적률_퍼센트'], '%')} · 건폐율 {_fmt(개요['건폐율_퍼센트'], '%')}</li>
    </ul>
    <div class="report-section-title">4. 시세 정보</div>
    <ul class="report-list">
        <li>주변 실거래·감정평가 시세: {_fmt(시세['주변실거래및감정평가시세_억원'], '억원')}</li>
        <li>매물 시세: {_fmt(시세['매물시세_억원'], '억원')}</li>
        <li>공시지가 시세 대비 가격: {_fmt(시세['공시지가시세대비가격_억원'], '억원')}</li>
        <li>매입가능예상가격: {_fmt(시세['매입가능예상가격_억원'], '억원')}</li>
    </ul>
    <div class="report-section-title">5. 임차 현황</div>
    <ul class="report-list">
        <li>총 임대인 수: {_fmt(임차['총임대인수_명'], '명')}</li>
        <li>총 보증금: {_fmt(임차['총보증금_억원'], '억원')}</li>
        <li>총 월임대료: {_fmt(임차['총월임대료_억원'], '억원')} · 총 관리비(연간): {_fmt(임차['총관리비_억원_연간'], '억원')}</li>
    </ul>
    <div class="report-section-title">6. 입지 특성</div>
    <ul class="report-list">
        <li>유동인구: {_fmt(입지['유동인구_명'], '명')}</li>
        <li>엘리베이터 유무: {_fmt(입지['엘리베이터유무'])}</li>
        <li>주차장: {_fmt(입지['주차장_면'], '면')}</li>
    </ul>
    <div class="report-section-title">7. 수익성 분석</div>
    <ul class="report-list">
        <li>NOI: {b(수익['NOI_억원'], '억원')}</li>
        <li>Cap Rate: {b(수익['CapRate_퍼센트'], '%')}</li>
    </ul>
    <div class="report-section-title">8. 개발 사업성 분석</div>
    <ul class="report-list">
        <li>TDC(총개발비용): {b(개발['TDC_억원'], '억원')}</li>
        <li>GDV(개발 후 가치): {b(개발['GDV_억원'], '억원')}</li>
        <li>Development Profit: {b(개발['DevelopmentProfit_억원'], '억원')}</li>
        <li>Development Margin: {b(개발['DevelopmentMargin_퍼센트'], '%')}</li>
    </ul>
    """

    return f"""
    <div>
        <div class="report-title">부동산 개발 리포트 — {cover['주소지']}</div>
        <div class="report-sub">작성일: {cover['작성일']}</div>
        <div class="verdict-badge">사업성 해석: {verdict['라벨']}
            <span class="verdict-sub">산정방식: {verdict['생성방식']}</span>
        </div>
        <ul class="verdict-reasons">{reasons_html}</ul>
        {body}
    </div>
    """


# 우측 하단 플로팅 챗봇 — 방문자가 "이 서비스가 뭔지" 물어보면, 이 저장소의 기획서
# (pitch/flow/plan)와 CLAUDE.md를 읽어서 그 내용을 근거로 GPT가 답한다. 사용자가 서비스
# 설명을 따로 안 줘도 되게, 문서를 그대로 시스템 프롬프트에 실어 보낸다.
CHATBOT_CONTEXT_FILES = [
    "specs/real-estate-report-automation-pitch.md",
    "specs/real-estate-report-automation-flow.md",
    "specs/real-estate-report-automation-plan.md",
    "specs/feature-1-spec.md",
    "specs/feature-2-spec.md",
    "specs/feature-3-spec.md",
    "CLAUDE.md",
]


@st.cache_resource(show_spinner=False)
def _load_chatbot_context() -> str:
    parts = []
    for rel_path in CHATBOT_CONTEXT_FILES:
        full_path = os.path.join(PROJECT_ROOT, rel_path)
        try:
            with open(full_path, encoding="utf-8") as f:
                parts.append(f"=== {rel_path} ===\n{f.read()}")
        except OSError:
            continue
    return "\n\n".join(parts)


def _get_openai_api_key() -> str | None:
    """로컬(.env → os.environ)과 Streamlit Community Cloud(secrets) 양쪽에서 다 동작하게.

    배포 환경에는 .env 파일이 올라가지 않으므로(.gitignore), Streamlit Cloud의
    "Secrets" 설정(st.secrets)에 넣은 값도 확인한다. 로컬에서는 os.environ이 이미
    채워져 있어 그대로 쓰고, 없을 때만 st.secrets를 본다.
    """
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    try:
        return st.secrets["OPENAI_API_KEY"]
    except Exception:
        return None


def _chatbot_reply(history: list) -> str:
    api_key = _get_openai_api_key()
    if not api_key:
        return "OPENAI_API_KEY가 설정되어 있지 않아 답변할 수 없습니다. (.env 또는 Streamlit Secrets 확인)"

    system_prompt = (
        "너는 이 웹 서비스(아래 문서에 설명된 부동산 개발 리포트 자동화 앱)를 소개하는 "
        "방문자 응대 챗봇이다. 아래는 이 서비스의 기획서와 개발 가이드 문서 전문이다. "
        "이 내용만을 근거로 방문자의 질문에 친절하고 간결하게 한국어로 답하라. "
        "문서에 없는 내용은 지어내지 말고 모른다고 답하라.\n\n" + _load_chatbot_context()
    )
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}] + history,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"답변을 만드는 중 오류가 발생했습니다: {e}"


st.set_page_config(page_title="부동산 개발 리포트 자동화", page_icon="🏢", layout="wide")
st.markdown(DESIGN_CSS, unsafe_allow_html=True)
st.title("🏢 부동산 개발 리포트 자동화")
st.caption("주소와 매물 정보를 입력하고 리포트를 생성하세요. (연습용 가상 데이터로만 사용하세요)")

# 최상위 탭: 기존 "부동산 개발 리포트" 기능 전체(입력→생성→결과, 원래의 단일 화면
# 흐름 그대로 — 안쪽을 다시 3개 탭으로 쪼갰던 걸 되돌림)를 한 탭에 담고,
# 새로 추가하는 "거래가격 엑셀분석"을 옆 탭에 둔다.
tab_realestate, tab_excel = st.tabs(["부동산 개발 리포트", "거래가격 엑셀분석"])

with tab_realestate:
    st.header("1. 입력")

    # 카카오 검색을 먼저 보여주고, "주소" 입력칸은 그 아래에 결과 표시용(읽기 전용)으로 둔다.
    # 주소가 채워지면 검색창을 아예 안 그려서 빈 여백이 안 남게 함.
    # 다시 찾고 싶으면 버튼으로 입력값을 비우고 재실행 -> 다음 줄에서 다시 검색창이 열림.
    # 주의: st.session_state["address_input"]은 이 위젯이 이미 만들어진 뒤에는 직접 대입할 수
    # 없음(StreamlitAPIException) — 위젯이 아직 만들어지기 전인 지금(카카오 검색을 위쪽에
    # 두면서 위젯 생성보다 먼저 오게 된 지점)이나 on_click 콜백 안에서 바꿔야 한다.
    def _reset_address_input():
        st.session_state["address_input"] = ""

    _current_address = st.session_state.get("address_input", "")

    # "주소" 입력칸: 카카오 검색 결과만 채워지는 결과 표시 칸. 직접 타이핑은 못 하도록
    # JS로 readonly 속성을 붙인다(disabled는 안 됨 — disabled면 JS의 input.focus()도 막혀서
    # 카카오 자동 채움 자체가 안 되므로, 타이핑만 막고 스크립트로는 값을 넣을 수 있는
    # readonly를 씀).
    if not _current_address:
        # 검색/선택 전: 카카오 검색창을 원래 위치(맨 위) 그대로 두고, 그 아래에 주소 칸.
        components.iframe(src=KAKAO_ADDRESS_SEARCH_URL, height=480)
        address = st.text_input(
            "주소",
            placeholder="위 카카오 주소 검색에서 골라주세요 (직접 입력 불가)",
            key="address_input",
        )
    else:
        # 선택 후: 검색창 대신 주소 칸 오른쪽에 "다른 주소로 입력" 버튼을 붙임.
        addr_col, addr_btn_col = st.columns([4, 1])
        with addr_col:
            address = st.text_input(
                "주소",
                placeholder="위 카카오 주소 검색에서 골라주세요 (직접 입력 불가)",
                key="address_input",
            )
        with addr_btn_col:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)  # 라벨 높이만큼 내려서 입력창과 줄 맞춤
            st.button("다른 주소로 입력", on_click=_reset_address_input)
    components.html(
        """
        <script>
        // Streamlit이 이 시점에 아직 "주소" input을 다 그리지 않았을 수도 있어서,
        // 없으면 짧은 간격으로 최대 3초까지 다시 찾아본다.
        (function tryMarkReadonly(attemptsLeft) {
          var input = window.parent.document.querySelector("input[aria-label='주소']");
          if (input) {
            input.setAttribute('readonly', 'readonly');
            return;
          }
          if (attemptsLeft > 0) {
            setTimeout(function () { tryMarkReadonly(attemptsLeft - 1); }, 150);
          }
        })(20);
        </script>
        """,
        height=0,
    )

    st.subheader("필수 입력값 (10개, 계산에 반드시 필요)")

    upload_col, template_col = st.columns([3, 1])
    with upload_col:
        uploaded_excel = st.file_uploader(
            "엑셀 파일로 한 번에 채우기 (선택)",
            type=["xlsx", "xls"],
            key="required_excel_upload",
            help="1행은 머리글(항목/값), 2행부터 항목명(라벨 또는 필드명)과 값을 적어주세요. "
            "오른쪽 '엑셀 템플릿 다운로드'를 참고하세요.",
        )
    with template_col:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)  # 라벨 높이만큼 내려서 업로드 칸과 줄 맞춤
        st.download_button(
            "엑셀 템플릿 다운로드",
            data=_build_required_fields_template_bytes(),
            file_name="필수입력값_템플릿.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    if uploaded_excel is not None:
        _excel_id = f"{uploaded_excel.name}:{uploaded_excel.size}"
        if st.session_state.get("_required_excel_id") != _excel_id:
            filled, unmatched, error = _apply_excel_to_required_fields(uploaded_excel)
            st.session_state["_required_excel_id"] = _excel_id
            st.session_state["_required_excel_result"] = (filled, unmatched, error)
    else:
        st.session_state.pop("_required_excel_id", None)
        st.session_state.pop("_required_excel_result", None)

    _excel_result = st.session_state.get("_required_excel_result")
    if _excel_result:
        _filled, _unmatched, _error = _excel_result
        if _error:
            st.error(_error)
        else:
            if _filled:
                st.success(f"엑셀에서 {len(_filled)}개 항목을 채웠습니다: {', '.join(_filled)}")
            if _unmatched:
                st.warning(f"인식하지 못한 항목(직접 입력해주세요): {', '.join(_unmatched)}")

    required_raw = {}
    cols = st.columns(2)
    for i, (field, label) in enumerate(REQUIRED_FIELD_META):
        with cols[i % 2]:
            required_raw[field] = st.text_input(label, key=f"required_{field}")

    with st.expander("참고용 입력값 (8개, 선택 — 비워두면 리포트에 '정보 없음'으로 표시됨)"):
        reference_raw = {}
        ref_cols = st.columns(2)
        for i, (field, label, kind) in enumerate(REFERENCE_FIELD_META):
            with ref_cols[i % 2]:
                if kind == "bool":
                    choice = st.selectbox(label, ["(선택 안 함)", "있음", "없음"], key=f"reference_{field}")
                    reference_raw[field] = {"(선택 안 함)": None, "있음": True, "없음": False}[choice]
                else:
                    reference_raw[field] = _parse_number(st.text_input(label, key=f"reference_{field}"))

    st.header("2. 리포트 생성")
    submitted = st.button("리포트 생성", type="primary")

    if submitted:
        calc_inputs = {field: _parse_number(required_raw[field]) for field, _ in REQUIRED_FIELD_META}
        calc_result = calculate(calc_inputs)

        if not calc_result.get("ok"):
            st.session_state["report_html"] = None
            st.session_state["report_markdown"] = None
            st.session_state["errors"] = calc_result["errors"]
            st.session_state["do_scroll"] = False
        else:
            report_result = map_report(
                calc_result=calc_result,
                required_inputs=calc_inputs,
                reference_inputs=reference_raw,
                address=address or "(주소 미입력)",
                report_date=date.today().strftime("%Y-%m-%d"),
            )
            if not report_result.get("ok"):
                st.session_state["report_html"] = None
                st.session_state["report_markdown"] = None
                st.session_state["errors"] = report_result["errors"]
                st.session_state["do_scroll"] = False
            else:
                핵심 = report_result["report"]["2_핵심지표요약"]
                중간 = calc_result["중간값"]
                calc_unavailable_reason = calc_result.get("산출불가사유", {}).get("DevelopmentMargin_퍼센트")
                verdict = interpret_margin(핵심["DevelopmentMargin_퍼센트"])
                reasons = _verdict_reasons(핵심, 중간, verdict, calc_unavailable_reason)

                st.session_state["report_html"] = _build_compact_report_html(report_result["report"], verdict, reasons)
                st.session_state["report_markdown"] = render_markdown(report_result)
                st.session_state["errors"] = None
                st.session_state["do_scroll"] = True

    header_col, download_col = st.columns([5, 1])
    with header_col:
        st.header("3. 결과", anchor="report")
    with download_col:
        if st.session_state.get("report_markdown"):
            st.download_button(
                "내려받기.md",
                data=st.session_state["report_markdown"],
                file_name="리포트.md",
                mime="text/markdown",
            )

    if st.session_state.get("errors"):
        st.error("다음 항목을 확인해주세요:")
        for err in st.session_state["errors"]:
            st.markdown(f"- {err}")

    if st.session_state.get("report_html"):
        photo_col, content_col = st.columns([2, 3])
        with photo_col:
            site_image = st.file_uploader(
                "AI 현장 사진 (선택 — 로드뷰 기반 렌더링 이미지)",
                type=["png", "jpg", "jpeg"],
                key="site_image_upload",
            )
            if site_image is not None:
                st.image(site_image, use_container_width=True)
            else:
                st.markdown(
                    '<div class="report-photo-slot"><div class="icon">🏢</div>'
                    "AI 현장 사진 자리<br>주소 로드뷰 기반 렌더링 사진(준비 중)</div>",
                    unsafe_allow_html=True,
                )
        with content_col:
            st.markdown(st.session_state["report_html"], unsafe_allow_html=True)

    if st.session_state.get("do_scroll"):
        st.session_state["do_scroll"] = False
        components.html(
            """
            <script>
            var target = window.parent.document.querySelector('h1#report, h2#report, h3#report');
            if (target) { target.scrollIntoView({behavior: 'smooth', block: 'start'}); }
            </script>
            """,
            height=0,
        )

with tab_excel:
    st.header("거래가격 엑셀분석")
    st.caption("엑셀 파일(.xlsx/.xls)을 올리면 행/열 수, 열별 합계·평균 같은 기본 통계와 그래프를 보여줍니다.")

    uploaded_file = st.file_uploader("엑셀 파일을 끌어다 놓거나 선택하세요", type=["xlsx", "xls"])

    if uploaded_file is None:
        st.info("엑셀 파일을 올리면 분석 결과가 여기에 표시됩니다.")
    else:
        try:
            excel_df = pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"엑셀 파일을 읽는 중 문제가 발생했습니다: {e}")
        else:
            numeric_df = excel_df.select_dtypes(include="number")

            st.markdown(f"**행 수**: {len(excel_df)}개 · **열 수**: {len(excel_df.columns)}개")

            if numeric_df.empty:
                st.info("숫자로 된 열이 없어서 합계·평균 같은 통계는 계산할 수 없습니다.")
            else:
                st.subheader("열별 합계 그래프")
                st.bar_chart(numeric_df.sum())

                st.subheader("눈에 띄는 항목")
                # 각 카드를 들여쓰기 없는 한 줄 문자열로 만든다 — 여러 줄로 인덴트를 주면
                # 마크다운이 4칸 이상 들여쓰기를 코드블록으로 오해해서 HTML이 그대로
                # 글자로 노출되는 문제가 있었음(첫 카드만 정상, 이후 카드부터 깨짐).
                card_parts = []
                for col in numeric_df.columns:
                    max_idx = numeric_df[col].idxmax()
                    min_idx = numeric_df[col].idxmin()
                    card_parts.append(
                        f'<div class="notable-card">'
                        f'<div class="notable-col-name">{col}</div>'
                        f'<div class="notable-stat">최댓값 <b>{numeric_df[col].max():,.1f}</b> '
                        f'<span class="notable-row-ref">(행 {max_idx + 1})</span></div>'
                        f'<div class="notable-stat">최솟값 <b>{numeric_df[col].min():,.1f}</b> '
                        f'<span class="notable-row-ref">(행 {min_idx + 1})</span></div>'
                        f'</div>'
                    )
                cards_html = '<div class="notable-grid">' + "".join(card_parts) + "</div>"
                st.markdown(cards_html, unsafe_allow_html=True)

                st.subheader("열별 기본 통계 (숫자 열만)")
                summary = pd.DataFrame(
                    {
                        "합계": numeric_df.sum(),
                        "평균": numeric_df.mean().round(2),
                        "최소": numeric_df.min(),
                        "최대": numeric_df.max(),
                    }
                )
                st.dataframe(summary, use_container_width=True)

            st.subheader("데이터 미리보기")
            st.dataframe(excel_df.head(20), use_container_width=True)

# ── 우측 하단 플로팅 챗봇 (탭 밖, 최상위) ──────────────────────────────────
# tab_realestate/tab_excel의 with 블록 "안"에 두면 안 보이는 탭에서는 같이 숨겨지므로
# (Streamlit이 비활성 탭 내용도 DOM에는 그리되 숨기는 방식이라), 반드시 탭 바깥에 둬야
# 어느 탭에 있든 항상 떠 있는다.
if "chatbot_open" not in st.session_state:
    st.session_state["chatbot_open"] = False
if "chatbot_history" not in st.session_state:
    st.session_state["chatbot_history"] = []

with st.container(key="chatbot_fab"):
    if not st.session_state["chatbot_open"]:
        if st.button("💬", key="chatbot_open_btn", help="서비스에 대해 물어보기"):
            st.session_state["chatbot_open"] = True
            st.rerun()
    else:
        with st.container(key="chatbot_panel_box"):
            title_col, close_col = st.columns([4, 1])
            with title_col:
                st.markdown('<div class="chatbot-panel-title">🏢 서비스 문의 챗봇</div>', unsafe_allow_html=True)
            with close_col:
                if st.button("✕", key="chatbot_close_btn"):
                    st.session_state["chatbot_open"] = False
                    st.rerun()

            history_box = st.container(height=260)
            with history_box:
                if not st.session_state["chatbot_history"]:
                    st.caption("이 서비스가 무엇을 하는지, 어떻게 쓰는지 무엇이든 물어보세요.")
                for msg in st.session_state["chatbot_history"]:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

            with st.form(key="chatbot_form", clear_on_submit=True):
                user_text = st.text_input(
                    "메시지",
                    key="chatbot_text",
                    label_visibility="collapsed",
                    placeholder="무엇이든 물어보세요",
                )
                chat_submitted = st.form_submit_button("전송")

            if chat_submitted and user_text.strip():
                st.session_state["chatbot_history"].append({"role": "user", "content": user_text.strip()})
                with st.spinner("답변 생성 중..."):
                    reply = _chatbot_reply(st.session_state["chatbot_history"])
                st.session_state["chatbot_history"].append({"role": "assistant", "content": reply})
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
