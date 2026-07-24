"""신규 기능 — 메모 자동 카테고리 분류.

memos/ 폴더의 각 메모(.txt)를 읽어 OpenAI 채팅 API로 어울리는 카테고리를 붙이고,
파일명·카테고리·메모 첫 줄을 함께 보여준다. 이미지 생성 기능(image_generator.py)과
같은 .env의 OPENAI_API_KEY를 그대로 사용한다. 기존 계산 엔진(Feature 1)·리포트
매핑(Feature 2)·이미지 생성 기능과는 독립된 별도 기능이며, 그 코드를 건드리지 않는다.

사용법:
    python3 practice/app/memo_categorizer.py
"""

import glob
import os

from dotenv import load_dotenv
from openai import OpenAI

PRACTICE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(PRACTICE_ROOT)
MEMOS_DIR = os.path.join(PRACTICE_ROOT, "memos")

# 프로젝트 루트(practice/의 상위 폴더)의 .env 파일(OPENAI_API_KEY=...)을 읽어 os.environ에 채워 넣음
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

SYSTEM_PROMPT = (
    "너는 사내 메모를 읽고 어울리는 카테고리를 붙이는 분류기다. "
    "카테고리는 2~6글자의 짧은 한국어 단어 하나로만 답한다 "
    "(예: 인사, 보안, 마케팅, 재무, 고객지원, 총무·시설 등 내용에 맞게 자유롭게 판단). "
    "카테고리 단어 외에 다른 설명은 절대 덧붙이지 않는다."
)


def categorize(memo_text: str) -> str:
    """메모 본문을 받아 GPT API로 짧은 카테고리 이름 하나를 받아 반환한다."""
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
            {"role": "user", "content": memo_text},
        ],
        temperature=0,
    )
    return response.choices[0].message.content.strip()


def main():
    if not os.path.isdir(MEMOS_DIR):
        print(f"{MEMOS_DIR} 폴더가 없습니다.")
        return

    # memos 폴더의 .txt 메모 파일을 이름순으로 모두 찾음
    filepaths = sorted(glob.glob(os.path.join(MEMOS_DIR, "*.txt")))
    if not filepaths:
        print("memos 폴더에 .txt 메모가 없습니다.")
        return

    print(f"총 {len(filepaths)}개 메모에 카테고리를 붙입니다...\n")

    for path in filepaths:
        with open(path, encoding="utf-8") as f:
            text = f.read()

        category = categorize(text)
        filename = os.path.basename(path)
        first_line = text.strip().splitlines()[0] if text.strip() else ""

        print(f"[{category}] {filename}")
        print(f"    {first_line}")
        print()


if __name__ == "__main__":
    main()
