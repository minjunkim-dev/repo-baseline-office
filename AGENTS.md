# repo-baseline

1인·소규모 팀이 언어·스택·하네스와 관계없이 쓰는 개발 기준의 원본 저장소다. 규칙은 `POLICY.md`, 소비 레포에 복사하는 파일은 `templates/`와 `profiles/`에 있다.

## 명령

모든 에이전트와 사람이 같은 명령을 쓴다. 스크립트는 Python 표준 라이브러리만 쓴다.

- setup: `N/A: 설치할 의존성이 없다(Python 3.9 이상과 시스템 IANA 시간대 데이터. 없으면 python3 -m pip install tzdata)`
- check: `N/A: 별도 린터가 없다. 링크·코어 구성·POLICY 길이 같은 결정적 검사는 test의 tools/test_distribution.py가 한다`
- test: `python3 -m unittest discover -s tools -p 'test_*.py' && for d in profiles/pr-conventions profiles/hash-copy; do python3 -m unittest discover -s "$d" -p 'test_*.py' || exit 1; done && python3 -m unittest discover -s claude-office -p 'test_*.py'`
  - pr-conventions 테스트는 예시 데이터를 검사하며 `FAIL:` 줄을 출력한다. 성공 여부는 종료 코드로만 판단한다.
- build: `N/A: 배포는 파일 복사다`

## 길잡이

| 경로 | 무엇 |
| --- | --- |
| `POLICY.md` | 모든 소비 레포의 규칙. 한 쪽(1만 자) 안에 둔다 |
| `templates/core/` | 코어. 소비 레포가 그대로 복사하는 4개 파일 |
| `templates/github/` | GitHub 프로필. CI 골격, 저장소 설정 기준선, 하네스별 권한 예시 |
| `profiles/` | 선택 프로필(pr-conventions, hash-copy, team, matt-skills, pstack) |
| `tools/` | GitHub 설정 적용·감사 도구와 배포 검사 |
| `prompts/` | 에이전트에게 첨부하는 셋업·리뷰·회고 프롬프트 |
| `docs/start.md` | 사람이 따라 하는 코어 적용 절차 |
| `claude-office/` | 이 후보 저장소만의 실험. PR 전 작업을 단계로 돌린다. 소비 레포에 복사하지 않는다 |
| `REVIEW.md` | 이 저장소의 리뷰 기준. 리뷰할 때만 읽는다 |
| `CHANGELOG.md` | PR마다 1~3줄. 소비 레포가 손으로 옮길 일을 적는다 |

## 작업 방식

- `POLICY.md`를 따른다. 기준 브랜치는 `main` 하나, 병합은 squash다. 에이전트는 §5의 조건을 만족하는 되돌리기 쉬움 PR만, 소유자가 지시할 때 병합한다.
- 시작 전에 완료 기준을 정하고 PR 본문 Summary에 적는다. 완료 주장은 위 test 명령의 실제 출력이다.
- PR 본문은 `.github/pull_request_template.md`를, 리뷰와 회고는 `prompts/review.md`·`prompts/retro.md`를 따른다. PR 본문 작성·코드 리뷰·회고를 하는 다른 스킬이 있어도 이 규칙이 먼저다.
- PR마다 `CHANGELOG.md`에 1~3줄을 더한다. 소비 레포가 손으로 옮겨야 하는 변경이면 그 일을 적는다.
- 같은 사실을 여러 문서에 적었으면(README, `docs/start.md`, `prompts/setup.md`) 함께 고친다.
- 하네스 문서를 근거로 쓰면 공식 문서 링크와 확인일을 적는다.
- 리뷰는 `prompts/review.md`로 받는다. 되돌리기 쉬움이면 이 세션의 하위 에이전트에게 맡겨도 되고, 어려움이거나 신뢰 경계를 건드리면 새 세션에 첨부한다(`POLICY.md` §3). 이 저장소의 PR은 `origin/main` 판의 `prompts/review.md`·`tools/review_preflight.py`·`REVIEW.md`로 리뷰한다.

## 하지 않는 것

- 비밀값(`.env*`, 키, 토큰)을 읽거나 커밋하지 않는다.
- `main`에 직접 push하지 않는다. 소유자가 지시하지 않은 PR, 되돌리기 어려움 PR은 병합하지 않는다.
- 저장소 설정을 서버에 적용하지 않는다(`tools/apply_github_settings.py --apply`는 소유자가 실행한다).
- 코어에 특정 도구·모델 이름을 넣지 않는다.
