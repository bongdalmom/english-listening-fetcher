"""
영어 리스닝 자료 자동 수집 스크립트
------------------------------------------------
목적: 지정한 소스 페이지(예: BBC 6 Minute English)에서
      최신 에피소드의 오디오 URL과 스크립트(PDF) URL을 추출해
      result.json 파일로 저장한다.

실행 방법 (로컬 테스트):
    pip install -r requirements.txt
    python fetch.py

GitHub Actions에서는 매일 자동으로 이 스크립트를 실행하고,
결과 파일(result.json)을 저장소에 커밋한다.

주의: 아래 CSS 선택자는 예시입니다. 실제 대상 사이트의 HTML 구조를
      브라우저 개발자 도구(F12 → Elements 탭)로 확인한 뒤 맞춰서
      수정해야 합니다. 사이트 구조는 시간이 지나며 바뀔 수 있습니다.
"""

import json
import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

# 소스별 설정: 필요에 따라 항목 추가/수정
SOURCES = {
    "bbc_6min": {
        "url": "https://www.bbc.co.uk/learningenglish/english/features/6-minute-english",
        "base_url": "https://www.bbc.co.uk",
    },
    # 다른 소스를 추가하고 싶으면 여기에 항목을 추가하세요.
    # "nejm_podcast": {
    #     "url": "https://www.nejm.org/podcasts",
    #     "base_url": "https://www.nejm.org",
    # },
}

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; StudyBot/1.0)"}


def fetch_page(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def extract_latest_episode_link(soup: BeautifulSoup, base_url: str) -> str:
    """
    최신 에피소드의 상세 페이지 링크를 찾는다.
    실제 사이트 구조에 맞춰 선택자를 조정할 것.
    """
    episode_link_tag = soup.select_one("a.content-item__link, a[href*='ep-']")
    if not episode_link_tag:
        raise ValueError("에피소드 링크를 찾지 못했습니다. 선택자를 확인하세요.")

    episode_url = episode_link_tag.get("href", "")
    if episode_url.startswith("/"):
        episode_url = base_url + episode_url

    return episode_url


def extract_media_links(episode_url: str) -> dict:
    """
    에피소드 상세 페이지에서 오디오(mp3)와 스크립트(pdf) 링크를 추출한다.
    """
    soup = fetch_page(episode_url)

    audio_tag = soup.find("a", href=re.compile(r"\.mp3$"))
    pdf_tag = soup.find("a", href=re.compile(r"\.pdf$"))

    return {
        "episode_url": episode_url,
        "audio_url": audio_tag["href"] if audio_tag else None,
        "transcript_pdf_url": pdf_tag["href"] if pdf_tag else None,
    }


def fetch_source(source_key: str) -> dict:
    if source_key not in SOURCES:
        raise ValueError(f"알 수 없는 소스: {source_key}")

    config = SOURCES[source_key]
    list_soup = fetch_page(config["url"])
    episode_url = extract_latest_episode_link(list_soup, config["base_url"])
    return extract_media_links(episode_url)


def main():
    results = {}
    errors = {}

    for source_key in SOURCES:
        try:
            results[source_key] = fetch_source(source_key)
            print(f"[OK] {source_key}: {results[source_key]}")
        except Exception as e:
            errors[source_key] = str(e)
            print(f"[FAIL] {source_key}: {e}")

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "errors": errors,
    }

    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\nresult.json 저장 완료")


if __name__ == "__main__":
    main()
