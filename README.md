# 키워드 데스크 (무료 버전)

블로그에 쓸 인기 검색어 후보를 매일 자동으로 모으고, Claude 채팅에서 받은 아티클을 날짜별로 보여주는 홈페이지입니다. GitHub Pages와 GitHub Actions만 써서 비용이 들지 않습니다.

> 이 사이트는 주소를 아는 누구나 볼 수 있습니다. 검색엔진에 색인하지 말라는 설정(robots.txt, noindex)은 넣었지만 강제력은 없습니다.

## 무엇이 자동이고 무엇이 수동인가

| 작업 | 방식 |
|---|---|
| 구글 트렌드 한국 인기 검색어 수집 | 자동 (매일 오전 7시) |
| 연합뉴스 연예 기사 목록 수집 (최신순) | 자동 (매일 오전 7시) |
| 경제 뉴스 제목 수집 (코스피·증시·환율) | 자동 (매일 오전 7시) |
| 네이버 뉴스 수집 (영화·드라마·연예·경제) | 자동 (매일 오전 10시 30분) |
| 네이버 블로그 상위 글 (구글 트렌드 상위 3개 + data/blog-request.txt) | 자동 (매일 오전 10시 30분) |
| 날짜 목록 갱신 | 자동 (글 파일을 올릴 때마다) |
| 네이버 데이터랩 인기 검색어 | 수동 (data/naver-request.txt에 직접 적기) |
| 키워드 분석·아티클 작성 | 수동 (Claude 채팅에 요청) |
| 아티클 파일 올리기 | 수동 (GitHub 웹에서 드래그) |

## 처음 한 번 설정

1. GitHub에서 공개(Public) 저장소를 새로 만듭니다.
2. 이 폴더의 파일을 모두 올립니다. 점으로 시작하는 `.github` 폴더와 `.nojekyll` 파일도 꼭 함께 올려야 합니다. 웹에서 숨김 폴더가 안 올라가면 "Add file > Create new file"로 `.github/workflows/collect.yml` 경로를 직접 만들어 내용을 붙여 넣으세요.
3. Settings > Pages: Source "Deploy from a branch", Branch `main`, 폴더 `/ (root)` 선택 후 저장.
4. Settings > Actions > General > Workflow permissions: "Read and write permissions" 선택 후 저장.
5. Actions 탭 > "키워드 수집" > "Run workflow"로 한 번 직접 실행해 봅니다. 성공하면 `data/candidates/오늘날짜.json`이 생깁니다.
6. 몇 분 뒤 `https://<아이디>.github.io/<저장소이름>/`에서 확인합니다.

## 매일 쓰는 순서

1. 홈페이지의 "자동 수집 후보"에서 키워드를 고릅니다.
2. Claude 채팅에 "이 키워드로 글 써줘: ○○, ○○"라고 요청하고 `YYYY-MM-DD.json` 파일을 받습니다.
3. 저장소의 `data` 폴더에 그 파일을 올립니다. 날짜 목록은 자동으로 갱신됩니다.
4. 사진은 `images/YYYY-MM-DD/글ID-단락ID.jpg`로 올리면 해당 단락에 붙습니다.

## 수집이 실패했을 때

- 홈페이지의 "자동 수집 후보" 화면 위쪽에 실패 이유가 표시됩니다.
- 구글 트렌드 RSS와 구글 뉴스 RSS는 구글이 형식이나 주소를 바꾸면 멈출 수 있습니다. 그때는 Claude에게 오류 문구를 보여주고 수정을 요청하세요.
- 연합뉴스 연예는 RSS(`YNA_ENT_RSS`)가 실패하면 구글 뉴스에서 연합뉴스 기사만 골라 옵니다. 어느 경로로 받았는지는 화면의 칸 제목 옆 괄호에 표시됩니다.
- 네이버 뉴스·블로그는 NAVER API HUB 키가 필요합니다. 저장소 Settings > Secrets and variables > Actions에 `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`으로 저장합니다. 네이버 뉴스 검색어는 `scripts/collect.py`의 `NAVER_NEWS_QUERIES` 줄에서 바꿀 수 있습니다.
- 뉴스 검색어는 `scripts/collect.py`의 `NEWS_QUERIES` 줄에서 바꿀 수 있습니다.

## 폴더 구조

- `index.html` : 홈페이지
- `data/YYYY-MM-DD.json` : 그날의 키워드 분석과 글
- `data/candidates/YYYY-MM-DD.json` : 자동 수집된 후보
- `data/index.json` : 날짜 목록 (자동 생성, 직접 고칠 필요 없음)
- `data/naver-request.txt` : 네이버 데이터랩 키워드 메모
- `data/blog-request.txt` : 네이버 블로그 상위 글을 보고 싶은 키워드
- `scripts/collect.py` : 수집 스크립트
- `.github/workflows/collect.yml` : 자동 실행 설정
