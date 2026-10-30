# 매일 아티클 작성 규칙

매일 10시 35분 자동 작성 세션이 이 파일을 따릅니다. 규칙을 바꾸고 싶으면 이 파일을 고치면 됩니다.

## 무엇을 쓰나

`data/candidates/오늘날짜.json`(한국 시간)에서 3건을 골라 아티클로 씁니다.

| ID | 출처 | 고르는 곳 |
|---|---|---|
| NE1 | 네이버 뉴스 연예 | `naverNews` 중 query가 "연예"인 목록 |
| NE2 | 네이버 뉴스 경제 | `naverNews` 중 query가 "경제"인 목록 |
| NB1 | 네이버 블로그 상위 글 | `naverBlogs`의 키워드 중 하나 |

- 블로그에 쓸 만한 정보(날짜·숫자·방법)가 있는 기사를 고릅니다.
- 연예는 사생활 위주 기사(결혼·이혼·임신·열애·사건 피소)와 사망·사고 소식은 피합니다. 공연·방송·작품 정보 기사를 우선합니다.
- 전날 이미 쓴 주제(`data/` 이전 날짜 파일)는 다시 고르지 않습니다.
- NB1은 그 키워드의 상위 블로그 글 제목 구조를 참고해 제목을 정하고, `titleReason`에 어떤 글을 참고했는지 적습니다.

## 사실 확인

- 숫자·날짜·조건은 웹 검색으로 두 곳 이상의 보도에서 확인합니다.
- 확인하지 못한 내용은 지어내지 않고 `[확인 필요: 무엇을 확인할지]`로 표시합니다.
- 추측·과장·투자 권유 표현은 쓰지 않습니다. 경제·증시 글에는 `disclaimer`를 넣습니다.

## 글 형식 (Gemini 편집 프롬프트용 초안)

`data/2026-10-29.json`을 예시로 삼아 같은 구조로 씁니다.

- 본문(도입부·단락·표·FAQ·세 줄 요약)은 글마다 **4000자 이내**, 1,200~2,500자를 권장합니다.
- 제목 후보 5개, 하나에 `"recommended": true`, `titleReason`, 썸네일 문구 2줄.
- 소제목은 `❝ ❞`로 감쌉니다. 예: `"❝ 숫자로 먼저 보기 ❞"`
- 강조는 `<span style="color:#C8213A">빨강</span>`, `<span style="color:#1D5BCB">파랑</span>`만 씁니다.
- 가운데 정렬 단락은 `{"center": true, "text": "한 줄\n한 줄"}`로 씁니다.
- 이미지는 단락의 `image`에 넣고, 지시문은 `[Gemini 실행 지시: ...]` 형식으로 씁니다.
  - 캡처형: `"type": "url"`, `refUrl`에 접속할 주소, 열리지 않으면 같은 정보로 생성하고 '생성 이미지'라고 표시하라고 적습니다.
  - 생성형: `"type": "gen"`, 스타일·색감을 적고 실존 인물 얼굴·로고·글자는 넣지 말라고 적습니다.
  - 숫자 비교는 `"type": "chart"`와 `chart`(title, unit, bars, source)로 넣습니다.
- 표는 `table`(title, header, rows), FAQ 2개, `summary3`, `sources`(이름·URL), `hashtags` 5~7개, `checklist`(발행 전 확인할 것)를 넣습니다.

## 파일 저장

1. `data/오늘날짜.json`을 만듭니다. 이미 있으면 덮어쓰지 않고 멈춥니다.
   - `date`, `weekday`(한 글자), `updatedAt`, `ticker: []`, `method`, `notice`, `keywords`(NE1, NE2, NB1), `articles`
   - `keywords`의 `source`는 NE1·NE2가 `naverNews`, NB1이 `naverBlog`이고, `status`는 `article`입니다.
2. `python3 scripts/collect.py --index-only`로 날짜 목록을 갱신합니다.
3. `python3 -c "import json; json.load(open('data/오늘날짜.json'))"`로 JSON 형식을 확인합니다.
4. `main` 브랜치에 커밋하고 push합니다. 커밋 메시지: `오늘날짜 아티클 3건 (자동 작성)`
