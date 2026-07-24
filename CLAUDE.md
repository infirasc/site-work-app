# CLAUDE.md

이 파일은 이 저장소에서 작업할 때 Claude Code(claude.ai/code)에게 안내를 제공하는 문서입니다.

## 이 저장소는 무엇인가

부동산 개발 리포트 자동화 앱의 파이썬 프로토타입이며, 명세·샘플 입력·생성된 결과물·코드를 폴더별로 분리해둔 구조입니다. 루트는 이 "진짜 앱"(계산 엔진·리포트 매핑) 전용이고, 이 파이프라인과 무관한 연습용 OpenAI 기능들은 전부 `practice/` 아래에 따로 모여 있습니다 — 아래 [폴더 구조](#폴더-구조-내용-종류별로-분리)와 [OpenAI 기반 연습용 기능](#openai-기반-연습용-기능은-practice-아래에-분리) 참고. 빌드 시스템도, 패키지 매니페스트(requirements.txt / pyproject.toml)도, 테스트 스위트도 없습니다. 의존성은 시스템/사용자 파이썬에 직접 설치합니다 (`python3 -m pip install ...`) — 가상환경(virtualenv)은 없습니다.

## 실행 방법

- `python3 app/main.py` — Feature 1(calc_engine) → Feature 2(report_mapper) → Feature 3(report_renderer, 마크다운 렌더링)를 순서대로 실행합니다. `inputs/feature-2-sample-input.json`을 입력으로 쓰고, Feature 1·2 결과는 JSON으로, Feature 3 결과는 마크다운 줄글로 출력합니다. 중간 단계가 실패하면 그 자리에서 멈추고 필수/참고용 입력 항목 목록을 안내합니다.
- `streamlit run app/streamlit_app.py` — 터미널 없이 쓰는 웹 화면(MVP). 주소·작성일·필수 입력값 10개(참고용 8개는 선택)를 폼으로 입력받고 "리포트 생성" 버튼을 누르면 같은 3단계 파이프라인을 호출해 결과 영역에 마크다운 리포트를 보여주고 그 지점으로 자동 스크롤합니다. `main.py`와 완전히 독립적으로 같은 파이프라인을 호출할 뿐, 계산·매핑·렌더링 코드는 공유하고 재사용합니다(중복 구현 없음).
- `python3 practice/app/image_generator.py "설명 문구"` — OpenAI `gpt-image-1`로 이미지를 생성해 `practice/images/`에 PNG로 저장합니다. (부동산 파이프라인과 무관한 연습용 기능)
- `python3 practice/app/memo_categorizer.py` — `practice/memos/`의 모든 `.txt` 파일을 읽어 OpenAI(`gpt-4o-mini`, Chat Completions)에게 메모마다 한 단어짜리 카테고리를 물어보고, 파일명과 카테고리를 출력합니다. (연습용 기능)
- `python3 practice/app/todo_extractor.py [파일 경로]` — 요약/회의 메모 텍스트에서 '오늘 할 일'만 골라 보여줍니다. 경로 생략 시 기본 샘플 `practice/inputs/todo-extractor-sample-input.txt` 사용. (연습용 기능)
- `python3 practice/app/key_points_extractor.py [파일 경로]` — 리포트/요약 텍스트에서 핵심 항목만 골라 보여줍니다. 경로 생략 시 기본 샘플 `practice/outputs/weekly-report-2.md` 사용. (연습용 기능)
- `python3 practice/app/gpt_reviewer.py <파일 경로>` — 지정한 파일을 사실/논리/누락/톤·형식 4기준으로 검증해(재작성 없음) `<파일이름>-gpt-review.md`로 저장합니다. `/cross-review` 스킬의 1단계(GPT 검증)에서 사용. (연습용 기능)
- 린터, 포매터, 테스트 러너는 설정돼 있지 않습니다.

## 환경변수 / 비밀키

- `OPENAI_API_KEY`를 저장소 루트의 `.env`에 설정해야 합니다. `.env`는 `.gitignore`에 등록돼 있고, `.env.example`에 예상되는 형식이 적혀 있습니다.
- `practice/app/` 아래 5개 스크립트(`image_generator.py`, `memo_categorizer.py`, `todo_extractor.py`, `key_points_extractor.py`, `gpt_reviewer.py`)는 각자 `load_dotenv()`를 호출하고 `os.environ["OPENAI_API_KEY"]`를 각자 확인합니다 — 공용 설정/클라이언트 모듈은 없습니다. `practice/app/`로 옮겨졌어도 `.env`는 여전히 저장소 루트(즉 `practice/`의 상위 폴더) 것 하나만 읽습니다 — 각 스크립트는 `PRACTICE_ROOT`(자기 위치 기준)와 `PROJECT_ROOT`(그 상위, 진짜 루트)를 따로 계산해서 `.env`는 `PROJECT_ROOT`에서, 샘플 데이터는 `PRACTICE_ROOT`에서 찾습니다. 새로운 OpenAI 기반 기능을 추가할 때도 공용 클라이언트 모듈을 만들기보다 이 패턴을 그대로 따르세요.

## 폴더 구조 (내용 종류별로 분리)

**루트 — 진짜 앱 (부동산 리포트 자동화)**
- `app/` — 실행 코드는 `main.py`, `calc_engine.py`, `report_mapper.py`, `report_renderer.py`, `streamlit_app.py` 5개뿐입니다. `specs/`·`inputs/`에는 코드를 두지 않습니다 — 의도적으로 재정리한 구조이니 되돌리지 마세요.
- `specs/` — 기능 명세(`feature-N-spec.md`, 지금은 1~3)와 부동산 앱의 원 기획 문서(`real-estate-report-automation-pitch.md` → `-flow.md` → `-plan.md` 순으로 파생됨), 그리고 이 프로젝트가 최종적으로 이 주제로 확정되기까지의 검토 과정을 담은 `automation-candidates-comparison.md`. 새 기능 명세도 같은 구성(무엇을 · 입력 · 동작 · 출력 · 지금은 뺄 것)을 따르고, 파생 근거가 된 plan/flow 문서로 링크를 겁니다.
- `inputs/` — `app/main.py`가 쓰는 `feature-1-sample-input.json`, `feature-2-sample-input.json`. 전부 가상 데이터입니다.
- `.claude/skills/` — `anthropics/skills`에서 가져온 `document-skills`(docx/pdf/pptx/xlsx) 및 이 저장소 전용 스킬(devreport/organize/mascot/categorize/todos/highlights/weekly-summary). `app/`의 코드가 이 폴더를 불러다 쓰지는 않습니다.

**`practice/` — 부동산 파이프라인과 무관한 연습용 자료 (코드 포함)**
- `practice/app/` — `image_generator.py`, `memo_categorizer.py`, `todo_extractor.py`, `key_points_extractor.py`, `gpt_reviewer.py` (OpenAI 기반 연습용 기능 코드)
- `practice/memos/` — `memo_categorizer.py`가 읽는 메모 샘플
- `practice/inputs/` — `todo_extractor.py`의 샘플(`todo-extractor-sample-input.txt`, `-busy.txt`) + 그 외 실습용 원본 데이터(`d2_*`)
- `practice/outputs/` — `key_points_extractor.py`의 기본 샘플(`weekly-report-2.md`) + 실습으로 만든 산출물(`sales-report.docx/pdf`)
- `practice/images/` — `image_generator.py`의 출력 폴더
- `practice/organized/` — 이전 `/organize` 실습으로 카테고리별(feedback/ideas/meeting/research/todo)로 정리해둔 가상 메모. 어떤 코드도 읽지 않습니다.

기존에 있던 `inbox/`는 `organized/`와 내용이 중복되어 정리 과정에서 제거되었습니다.

## 아키텍처: 계산 → 리포트 매핑 → 렌더링 파이프라인

`specs/feature-1-spec.md`·`feature-2-spec.md`·`feature-3-spec.md`는 `app/main.py`가 처음부터 끝까지 실행하는 3단계 파이프라인을 정의합니다.

1. **`calc_engine.py` (Feature 1)** — `calculate(inputs: dict)`는 `REQUIRED_FIELDS`(연면적/건축면적/대지면적/총보증금/총월임대료/총관리비/매입가능예상가격/전월세환산이율/평당건축비/ExitCapRate, 총 10개 숫자 필드)를 기준으로 입력을 검증하고(빈 값·숫자 아님·**음수**·NaN/무한대·분모 0), 통과하면 NOI → Cap Rate, 용적률/건폐율, 공사비 → TDC → GDV → Development Profit → Development Margin을 계산합니다. 모든 연산은 `float`가 아니라 `decimal.Decimal`을 사용합니다(`Decimal(str(x))`로 변환) — 이는 의도된 설계로, 이진 부동소수점 반올림 오차(예: 1.835가 1.84가 아니라 1.83으로 반올림되는 문제)를 막기 위한 것입니다. 이 부분을 다시 float 연산으로 되돌리지 마세요. 반환값은 `{"ok": True, "핵심지표": {...}, "중간값": {...}}` 또는 `{"ok": False, "errors": [...]}`이며, 잘못된 입력에 대해 예외를 던지지 않습니다. **예외 — GDV가 0이 되는 경우(NOI가 0일 때)**: Development Margin은 0으로 나누기 예외를 던지는 대신 값 자리에 `"산출 어려움"`을 담고, 반환값에 `"산출불가사유": {필드명: 사유}`를 추가로 담습니다. 이 특수 문자열 값을 다시 float로 되돌리는 코드를 추가하지 마세요.
2. **`report_mapper.py` (Feature 2)** — `map_report(calc_result, required_inputs, reference_inputs, address, report_date)`는 `required_inputs`를 `calc_engine.REQUIRED_FIELDS` 기준으로 다시 검증합니다(따라서 호출하는 쪽은 실제 리포트에 표시되는 항목만이 아니라 10개 필드 전부를 넘겨야 합니다). 계산에는 안 쓰이는 참고용 8개 필드(`REFERENCE_FIELDS`) 중 비어있는 값은 `"정보 없음"`으로 대체하고, 이 모든 것을 8개 리포트 섹션(표지/핵심지표요약/부동산개요/시세정보/임차현황/입지특성/수익성분석/개발사업성분석)으로 조립합니다. `calc_result`에 `산출불가사유`가 있으면 그대로 반환값에 실어 다음 단계로 넘깁니다. Feature 1과 동일하게 `{"ok": bool, ...}` 규약을 따릅니다.
3. **`report_renderer.py` (Feature 3)** — `render_markdown(report_result, interpreter=None)`은 Feature 2의 8개 섹션 데이터를 마크다운 줄글로 바꿉니다. 값이 `"산출 어려움"`이면 그 사유를 각주 형태(`_(사유: ...)_`)로 덧붙이고, Development Margin에는 고정 구간 기준(0 이하 사업성없음/0~50 보통/50~100 권장/100 이상 매우추천) 라벨을 붙입니다. 이 라벨링 로직은 `interpret_margin()`에 분리돼 있고 `interpreter` 인자로 교체 가능하게 열어뒀습니다 — 나중에 AI 기반 코멘트 생성 기능을 붙일 자리이니, 새 해석 로직을 추가할 때는 이 함수를 확장하기보다 새 `interpreter`를 만들어 주입하는 방식을 따르세요.

세 단계 모두 검증 실패 시 예외를 던지는 대신 `{"ok": bool, ...}` 형태의 결과를 반환합니다 — 앞으로 파이프라인 단계(예: PDF 변환)를 추가할 때도, 사용자에게 보여줄 검증 오류에는 예외 대신 이 방식을 유지하세요. `app/main.py`도 같은 원칙을 따라, 입력 JSON 파일이 없거나 깨졌거나 최상위 키가 빠졌을 때 파이썬 예외를 그대로 노출하지 않고 `{"ok": False, "errors": [...]}`로 처리한 뒤 필수/참고용 입력 항목 전체 목록을 안내합니다(`_load_sample`, `_print_input_guide`).

**`streamlit_app.py` (웹 화면, MVP)** — 위 3단계 파이프라인을 그대로 호출하는 얇은 UI 레이어입니다. 새로운 계산·검증 로직을 담지 않고 `calculate`/`map_report`/`render_markdown`을 그대로 가져다 씁니다(중복 구현 금지). 입력 폼(주소·작성일·필수 10개·참고용 8개) → "리포트 생성" 버튼 → 결과 영역에 마크다운 리포트 표시 + 자동 스크롤 순서로 동작하며, `main.py`(터미널)와 독립적으로 같은 파이프라인을 호출하는 대체 진입점입니다. `streamlit run app/streamlit_app.py`로 실행합니다.

명세 기준으로 아직 안 만든 것: 웹 화면의 클릭-펼침 UI(예: "산출 어려움" 사유를 접었다 펼치는 인터랙션 — 지금은 각주 텍스트로만 표시)와 커스텀 HTML/CSS 디자인, PDF 변환, 전월세환산이율/평당건축비/ExitCapRate의 외부 자동조회(지금은 샘플 JSON으로 넘기는 수동 입력 대체값), 결과 저장/이력 조회, AI 기반 사업성 코멘트 생성(자리만 마련해둠).

## OpenAI 기반 연습용 기능은 practice/ 아래에 분리

`practice/app/image_generator.py`, `memo_categorizer.py`, `todo_extractor.py`, `key_points_extractor.py`, `gpt_reviewer.py` 5개는 위 계산/리포트 파이프라인과 무관하게 독립적으로 동작하는 연습용 기능입니다 — `calc_engine`이나 `report_mapper`를 import하지 않고, 파이프라인 쪽에서도 이들을 import하지 않습니다. 각각 자체적으로 `load_dotenv()`와 API 키 확인 로직을 갖춘 독립 스크립트이며, 코드와 샘플 데이터 모두 `practice/`에 있습니다(위 [폴더 구조](#폴더-구조-내용-종류별로-분리) 참고). 새로운 OpenAI 기반 연습용 기능을 추가할 때는, 기존 모듈을 확장하거나 공용 클라이언트 모듈을 만들기보다 `practice/app/`에 새 독립 모듈을 추가하는 이 저장소의 관례를 따르세요. 반대로 부동산 리포트 파이프라인 자체를 확장하는 기능이라면 `app/`에 두어야 합니다.

## 기획서 변경 시 기능 동기화 (질문 → 승인 후에만 반영)

`specs/real-estate-report-automation-pitch.md` · `-flow.md` · `-plan.md`(그리고 이 문서들에서 파생된 `feature-N-spec.md`)의 내용이 바뀐 것을 확인하면 — 사용자가 직접 고쳤든, 방금 Claude가 수정했든 — 그 변경이 `app/`의 실제 코드(`calc_engine.py`·`report_mapper.py`·`report_renderer.py` 등)에도 반영이 필요한지 검토한다.

- 반영이 필요해 보이면, 무엇을·왜 바꿔야 하는지 먼저 설명하고 **사용자에게 질문해서 명시적 승인을 받은 뒤에만** 코드를 수정한다. 먼저 물어보지 않고 코드를 바로 고치지 않는다.
- 승인을 받지 못하면 코드는 그대로 두고, 기획서와 코드가 어디서 어긋나 있는지만 짚어서 알려준다(예: `real-estate-report-automation-plan.md`의 "주변 신축 ROI" 방식과 `feature-1-spec.md`/`calc_engine.py`의 "Exit Cap Rate" 방식이 서로 다른 채 남아있던 사례처럼).
- 반대 방향(코드가 먼저 바뀌고 기획서가 뒤처진 경우)도 같은 규칙을 따른다 — 기획서를 고칠지도 먼저 질문하고 승인 후에만 반영한다.

## 작업 규칙

**절대 규칙** (예외 없이 지킬 것):
- 실명·실제 사내 자료는 절대 쓰지 않는다 — 연습·예시는 항상 가짜 데이터로.
- 할 일 목록은 항목을 하나도 빠짐없이 다 보여준다.
- 모든 답변의 맨 끝에 "★."를 붙인다.
- 기획서 변경에 따라 코드를(또는 그 반대로) 업데이트할 때는, 반드시 먼저 질문해서 승인을 받은 뒤에만 실행한다 — 자세한 내용은 [기획서 변경 시 기능 동기화](#기획서-변경-시-기능-동기화-질문-→-승인-후에만-반영) 참고.

**규칙 인덱스** (주제별 상세 규칙은 아래 파일 참고):
- [rules/tone.md](rules/tone.md) — 역할, 말투, 용어 설명 규칙
- [rules/format.md](rules/format.md) — 결과 형식, 제목, 표, 마무리 규칙
- [rules/constraints.md](rules/constraints.md) — 하지 말 것 규칙

**우선순위**: 규칙끼리 부딪히면 위 절대 규칙 → `rules/constraints.md` → `rules/format.md`·`rules/tone.md` 순으로 따른다.
