"""신규 기능 — GPT API로 문서를 사실/논리/누락/톤·형식 기준으로 검증(재작성 없음).

/cross-review 스킬의 1단계(GPT 검증)에서 호출하는 독립 모듈. 계산 엔진(Feature 1)·
리포트 매핑(Feature 2)·리포트 렌더링(Feature 3)과는 무관하며, 그 코드를 건드리지 않는다.

사용법:
    python3 practice/app/gpt_reviewer.py <검증할 파일 경로>
"""

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

PRACTICE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(PRACTICE_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

SYSTEM_PROMPT = """너는 문서를 꼼꼼하게 점검하는 검토자다. 아래 4가지 기준으로만 문제점을 찾아라.
문서를 고쳐 쓰거나 대안을 제시하지 마라 — 오직 문제 지적만 한다.

기준:
1. 사실: 숫자·이름·날짜·인용 중 근거 없이 지어낸 것으로 의심되는 부분
2. 논리: 주장과 근거가 맞지 않는 부분(앞뒤 모순, 근거 없는 결론 등)
3. 누락: 이 문서 성격상 꼭 있어야 하는데 빠진 내용
4. 톤·형식: 이 문서를 받을 사람 기준으로 어색하거나 부적절한 부분

출력 형식: 4개 기준별로 소제목을 나누고, 그 아래 지적사항을 번호 목록으로 적어라.
각 지적은 반드시 "어느 문장(원문 그대로 짧게 인용)인지"와 "왜 문제인지"를 한 줄씩, 아주 짧게 적어라.
문제가 없는 기준은 "특이사항 없음"이라고만 적어라. 과장하거나 없는 문제를 지어내지 마라."""


def review_text(content: str) -> str:
    """문서 본문을 받아 GPT의 4기준 검증 결과(마크다운 본문)를 반환한다."""
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
            {"role": "user", "content": content},
        ],
        temperature=0,
    )
    return response.choices[0].message.content.strip()


def main():
    if len(sys.argv) < 2:
        print("사용법: python3 practice/app/gpt_reviewer.py <검증할 파일 경로>")
        sys.exit(1)

    target_path = sys.argv[1]
    with open(target_path, encoding="utf-8") as f:
        content = f.read()

    review_body = review_text(content)

    target_dir = os.path.dirname(os.path.abspath(target_path))
    stem = os.path.splitext(os.path.basename(target_path))[0]
    out_path = os.path.join(target_dir, f"{stem}-gpt-review.md")

    output = f"""# GPT Review — {os.path.basename(target_path)}

- 점검 대상: `{target_path}`
- 점검 도구: OpenAI `gpt-4o-mini` (Chat Completions)
- 점검 기준: 사실 / 논리 / 누락 / 톤·형식 (문제점만 지적, 재작성 없음)

{review_body}
"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"저장 완료: {out_path}")


if __name__ == "__main__":
    main()
