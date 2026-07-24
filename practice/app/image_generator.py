"""신규 기능 — AI 이미지 생성 및 저장.

짧은 설명(프롬프트)을 받아 OpenAI 이미지 생성 API(gpt-image-1)로 이미지를 만들고
images/ 폴더에 PNG 파일로 저장한다. 기존 계산 엔진(Feature 1)·리포트 매핑(Feature 2)
과는 독립된 별도 기능이며, 그 코드를 건드리지 않는다.

사용법:
    python3 practice/app/image_generator.py "내 서비스 마스코트 - 물방울 모양 귀여운 캐릭터"

필요 조건:
    - pip install openai (설치됨)
    - 환경변수 OPENAI_API_KEY 설정 필요 (export OPENAI_API_KEY=sk-...)
"""

import base64  # OpenAI가 돌려주는 base64 인코딩된 이미지 데이터를 실제 바이트로 디코딩하는 데 사용
import os  # 폴더 생성, 경로 조합, 환경변수(API 키) 읽기에 사용
import re  # 설명 문구를 파일명으로 쓸 수 있게 정리(슬러그화)하는 데 사용
import sys  # 커맨드라인 인자(sys.argv) 읽기, 오류 시 종료 코드 지정에 사용
from datetime import datetime  # 파일명에 붙일 생성 시각 타임스탬프 생성에 사용

from dotenv import load_dotenv  # 프로젝트 루트의 .env 파일을 읽어 환경변수로 등록해주는 라이브러리
from openai import OpenAI  # OpenAI 공식 SDK의 클라이언트 클래스

# 이 파일(practice/app/image_generator.py) 기준으로 practice/ 폴더와 프로젝트 최상위 폴더 경로를 계산
PRACTICE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(PRACTICE_ROOT)
# 생성된 이미지를 저장할 기본 폴더: <practice 폴더>/images
IMAGES_DIR = os.path.join(PRACTICE_ROOT, "images")

# 프로젝트 루트(practice/의 상위 폴더)의 .env 파일(OPENAI_API_KEY=... 한 줄)을 읽어 os.environ에 채워 넣음
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def _slugify(text: str, max_len: int = 40) -> str:
    """설명 문구를 파일명에 안전하게 쓸 수 있는 짧은 문자열로 바꾼다."""
    # 한글/영문/숫자가 아닌 문자(공백, 특수문자 등)는 전부 하이픈으로 치환
    slug = re.sub(r"[^0-9a-zA-Z가-힣]+", "-", text).strip("-")
    # 파일명이 너무 길어지지 않도록 자르고, 결과가 비어 있으면 기본값 사용
    return slug[:max_len] or "image"


def generate_image(description: str, out_dir: str = IMAGES_DIR) -> str:
    """설명 문구로 이미지를 생성해 out_dir에 PNG로 저장하고, 저장된 파일 경로를 반환한다."""
    # API 키는 코드에 직접 적지 않고 환경변수에서만 읽음 (보안)
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        # 키가 없으면 API를 호출하기 전에 바로 멈추고, 어떻게 해결하는지 안내
        raise RuntimeError(
            "OPENAI_API_KEY 환경변수가 설정되어 있지 않습니다. "
            "터미널에서 export OPENAI_API_KEY=sk-... 로 설정한 뒤 다시 실행하세요."
        )

    # 읽어온 키로 OpenAI API 클라이언트 생성
    client = OpenAI(api_key=api_key)

    # 이미지 생성 API 호출: 모델은 gpt-image-1, 결과 1장, 1024x1024 크기
    response = client.images.generate(
        model="gpt-image-1",
        prompt=description,
        size="1024x1024",
        n=1,
    )

    # 응답에는 이미지가 base64 문자열(response.data[0].b64_json)로 들어있음 → 실제 바이트로 디코딩
    image_bytes = base64.b64decode(response.data[0].b64_json)

    # 저장할 폴더가 없으면 생성 (이미 있으면 그냥 통과)
    os.makedirs(out_dir, exist_ok=True)
    # 같은 설명으로 여러 번 생성해도 파일이 안 겹치도록 타임스탬프를 파일명 앞에 붙임
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}-{_slugify(description)}.png"
    out_path = os.path.join(out_dir, filename)

    # 디코딩한 이미지 바이트를 PNG 파일로 저장 (바이너리 쓰기 모드)
    with open(out_path, "wb") as f:
        f.write(image_bytes)

    # 호출한 쪽(main 함수 등)이 결과 파일 위치를 알 수 있도록 경로를 반환
    return out_path


def main():
    # 커맨드라인에 설명 문구를 안 주고 실행하면 사용법을 알려주고 종료
    if len(sys.argv) < 2:
        print('사용법: python3 practice/app/image_generator.py "짧은 설명"')
        sys.exit(1)

    # sys.argv[0]은 스크립트 경로이므로 제외하고, 그 뒤 인자들을 공백으로 합쳐 설명 문구로 사용
    description = " ".join(sys.argv[1:])
    print(f"이미지 생성 중... (설명: {description})")
    # 실제 생성·저장 수행
    path = generate_image(description)
    print(f"저장 완료: {path}")


if __name__ == "__main__":
    # python3 app/image_generator.py로 직접 실행했을 때만 main()이 동작하도록 함
    # (다른 파일에서 이 모듈을 import할 때는 자동 실행되지 않게 하는 관용적 방식)
    main()
