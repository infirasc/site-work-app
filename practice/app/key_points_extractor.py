"""신규 기능 — 결과(리포트/요약)에서 핵심 항목만 추출.

리포트나 요약 텍스트를 받아 그중 핵심 항목만 OpenAI 채팅 API로 골라 보여준다.
todo_extractor.py와 같은 패턴(독립 모듈, 같은 .env의 OPENAI_API_KEY)을 따르며,
기존 기능은 건드리지 않는다.

사용법:
    python3 practice/app/key_points_extractor.py                  # 기본 샘플(practice/outputs/weekly-report-2.md)로 실행
    python3 practice/app/key_points_extractor.py 다른/파일/경로.md   # 다른 텍스트로 실행
"""

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

PRACTICE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(PRACTICE_ROOT)
DEFAULT_SAMPLE_PATH = os.path.join(PRACTICE_ROOT, "outputs", "weekly-report-2.md")

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

SYSTEM_PROMPT = (
    "너는 리포트나 요약 텍스트에서 핵심 항목만 뽑아내는 도우미다. "
    "입력 텍스트를 읽고, 가장 중요한 핵심 항목만 짧은 번호 목록으로 정리해서 답한다. "
    "배경 설명, 세부 수치 나열, 부가 코멘트는 빼고 핵심만 남긴다. "
    "텍스트에 없는 내용은 절대 지어내지 않는다."
)


def extract_key_points(text: str) -> str:
    """텍스트를 받아 핵심 항목만 정리한 문자열을 반환한다."""
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
            {"role": "user", "content": text},
        ],
        temperature=0,
    )
    return response.choices[0].message.content.strip()


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SAMPLE_PATH
    with open(path, encoding="utf-8") as f:
        text = f.read()

    print(f"=== 핵심 항목만 추출 ({os.path.basename(path)}) ===")
    print(extract_key_points(text))


if __name__ == "__main__":
    main()
