"""신규 기능 — 요약 텍스트에서 '오늘 할 일'만 추출.

데일리 요약이나 회의 메모처럼 여러 종류의 내용이 섞인 텍스트에서,
그중 '오늘 해야 할 일'에 해당하는 항목만 OpenAI 채팅 API로 골라서 보여준다.
이미지 생성(image_generator.py), 메모 분류(memo_categorizer.py)와 마찬가지로
같은 .env의 OPENAI_API_KEY를 쓰는 독립 모듈이며, 계산 엔진(Feature 1)·리포트
매핑(Feature 2) 등 기존 기능은 건드리지 않는다.

사용법:
    python3 practice/app/todo_extractor.py                 # 기본 샘플 입력으로 실행
    python3 practice/app/todo_extractor.py 다른/파일/경로.txt  # 다른 텍스트로 실행
"""

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

PRACTICE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(PRACTICE_ROOT)
DEFAULT_SAMPLE_PATH = os.path.join(PRACTICE_ROOT, "inputs", "todo-extractor-sample-input.txt")

# 프로젝트 루트(practice/의 상위 폴더)의 .env 파일(OPENAI_API_KEY=...)을 읽어 os.environ에 채워 넣음
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

SYSTEM_PROMPT = (
    "너는 요약 텍스트에서 '오늘 할 일'만 뽑아내는 도우미다. "
    "입력된 텍스트를 읽고, 명시적으로 '오늘 할 일'이라고 적힌 항목뿐 아니라 "
    "회의 메모 등 다른 부분에 섞여 있어도 문맥상 오늘 해야 하는 일로 볼 수 있는 "
    "항목까지 모두 찾아 짧은 번호 목록으로 정리해서 답한다. "
    "오늘 일이 아닌 항목(진행 중인 이슈, 다음 주 일정 등)은 포함하지 않는다. "
    "텍스트에 없는 내용은 절대 지어내지 않는다. "
    "오늘 할 일이 하나도 없으면 '오늘 할 일 없음'이라고만 답한다."
)


def extract_todos(summary_text: str) -> str:
    """요약 텍스트를 받아 '오늘 할 일'만 정리한 문자열을 반환한다."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY 환경변수가 설정되어 있지 않습니다. "
            ".env 파일에 OPENAI_API_KEY=... 를 채워 넣은 뒤 다시 실행하세요."
        )

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": summary_text},
        ],
        temperature=0,
    )
    return response.choices[0].message.content.strip()


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SAMPLE_PATH
    with open(path, encoding="utf-8") as f:
        summary_text = f.read()

    print(f"=== 원본 요약 ({os.path.basename(path)}) ===")
    print(summary_text)

    print("=== 오늘 할 일만 추출 ===")
    print(extract_todos(summary_text))


if __name__ == "__main__":
    main()
