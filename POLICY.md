# 저장소 공통 정책

이 문서는 1인 개발 저장소에 공통으로 적용하는 값을 정한다.
프롬프트(`prompts/`)는 절차와 판단 기준을 정한다. 구체적인 값은 이 문서와 `templates/`를 따른다.
정책 버전은 이 저장소의 commit SHA다. 각 프로젝트는 `.github/repo-baseline.json`의 `source_commit`에 적용한 버전을 기록한다.

## 1. 값의 종류

| 종류 | 뜻 | 바꾸는 방법 |
| --- | --- | --- |
| GitHub 필수값 | GitHub가 요구하는 값 | 바꿀 수 없다 |
| 공통값 | 세 저장소에 같게 적용하는 운영 선택 | 이 저장소에서 바꾸고 모든 프로젝트에 다시 적용한다 |
| 허용 예외 | 프로젝트 사정으로 공통값과 다르게 두는 값 | 프로젝트 `docs/REPOSITORY_SETUP.md`에 이유와 함께 한 줄로 적는다 |

## 2. Dependabot

`tools/apply_baseline.py`가 `templates/dependabot.yml`과 manifest의 `ecosystems` 목록으로 `.github/dependabot.yml`을 생성한다. 생성한 파일의 해시를 manifest에 기록하므로, 프로젝트에서 값을 바꾸면 `check_repo_baseline.py`가 CI에서 실패한다. 생태계를 추가하려면 manifest의 `ecosystems`를 고치고 다시 적용한다.

| 항목 | 값 | 종류·근거 |
| --- | --- | --- |
| `schedule` | `weekly`, `wednesday`, `"10:00"`, `Asia/Seoul` | 공통값. 사용자 운영 선호. PR 생성 시각을 보장하지 않는다. |
| `labels` | `[dependencies]` | 공통값. 기본 생태계 라벨(`github_actions` 등)을 대체한다. |
| `commit-message` | `prefix: chore`, `include: scope` | 공통값. 제목은 `chore(deps): …` 또는 `chore(deps-dev): …`가 된다. |
| `open-pull-requests-limit` | 설정하지 않는다 | 공통값. GitHub 기본값 5를 쓴다. 업데이트 항목마다 따로 센다. GitHub 권장값은 없다. |
| `groups.codeql-action` | `patterns: ["github/codeql-action/*"]` | CodeQL advanced setup에서 Action을 SHA로 고정하면 필수. `init`과 `analyze`가 다른 버전이면 분석이 실패한다. |

- 보안 업데이트에는 GitHub의 고정 상한 10이 따로 적용된다. `open-pull-requests-limit`과 관계없다.
- Grouped security updates를 켠다(공통값). 계정 설정(새 저장소 자동 켜기)과 각 저장소 Settings → Advanced Security에서 켠다. 같은 패키지 관리자·디렉터리의 보안 수정을 PR 하나로 묶어 봇 PR 수를 줄인다. 묶음 안의 수정 하나가 빌드를 깨면 나머지도 함께 기다린다. `dependabot.yml`의 `groups`가 있으면 그 규칙이 우선한다.
  - REST API가 이 값을 돌려주지 않는다. `check_github_settings.py`로 감사할 수 없으므로 셋업 때 화면에서 확인한다.
- SHA로 고정한 Action에는 Dependabot alert가 생기지 않는다. 그래서 Action의 보안 수정은 정기 업데이트로만 들어온다. 봇 PR은 매주 처리한다.
- `groups`는 기본적으로 정기 업데이트에만 적용된다. SHA 고정 Action에는 보안 업데이트가 생기지 않으므로 지금 구조에서는 추가 설정이 필요 없다. 태그 고정으로 바꾸면 `applies-to: security-updates` 그룹을 검토한다.
- 허용 예외: 저장소의 Git 규칙이 scope를 기능 폴더 이름으로 정하면, 그 문서에 Dependabot `deps`·`deps-dev` 예외를 한 줄 적는다.

## 3. CodeQL

- 기본은 GitHub default setup이다. 빌드 명령이나 toolchain 지정이 필요할 때만 advanced setup을 쓴다.
  - default setup이면 `.github/repository-settings.json`에 `codeql.state: "configured"`를 두고 `codeql_workflow`·`codeql_main_source`는 넣지 않는다. 감사 도구가 두 경우를 구분한다.
- advanced setup에서 `.github/repository-settings.json`이 `codeql_main_source.sha`로 workflow blob을 고정하면, `codeql.yml`을 바꾸는 PR은 이 값도 함께 갱신한다.
  - `scripts/check_github_settings.py`의 `codeql_source_drift()`가 PR CI에서 두 가지를 검사한다: blob SHA 일치, 모든 `github/codeql-action/*` 단계의 commit 일치.
  - 갱신 값: `git hash-object .github/workflows/codeql.yml`.
  - 검사는 YAML 구조를 해석하지 않는다. 주석과 `run:` 같은 블록 본문을 뺀 모든 `github/codeql-action/` 참조를 모아 비교한다. 읽지 못하는 참조나 블록으로 쓴 `uses:`는 고정되지 않은 것으로 보고 실패한다.
  - 이 검사는 정직한 편집(Dependabot, 사람, 에이전트)의 실수를 막는다. 보안 경계가 아니다. 따옴표 안의 이스케이프(`\u0061`)나 줄 연결로 이름을 숨기는 표기는 해석하지 않는다. 그런 작성자는 검사기 파일도 고칠 수 있기 때문이다.
- 집계 `CodeQL` check는 분석이 실패해도 `neutral`일 수 있다. GitHub는 필수 check의 `neutral`을 통과로 본다. 분석 실패로 병합을 막으려면 분석 job 결과를 필수 게이트에 연결한다.

## 4. GitHub 서버 설정

- 목표값은 `prompts/github-repository-settings.md` §3·§5의 표를 따른다.
- 각 프로젝트는 기대값을 `.github/repository-settings.json`에 두고 `scripts/check_github_settings.py`로 읽기 전용 감사를 한다.
- 공통값은 `templates/repository-settings.json`에 있다. 서버 적용은 `tools/apply_github_settings.py`가 같은 기준선으로 계획을 먼저 보이고, 승인 후 `--apply`로 다른 항목만 쓴다.
- 기능 미지원·비해당은 근거를 기록한 명시적 예외만 허용한다. 형식과 LIMITED·DRIFT·UNVERIFIED 구분은 `docs/github-settings-profile.md`를 따른다. 조회 실패를 자동 예외로 바꾸지 않는다.
- 개인 계정에는 조직 단위 ruleset이 없다. 서버 설정은 저장소마다 적용하고 감사로 확인한다.

## 5. 리뷰와 병합

- 독립 리뷰는 작성자와 분리한 컨텍스트에서 Standards·Spec을 각각 실행한다. 권한·Secret·dependency·workflow 신뢰 경계 변경에는 Security를 추가한다.
- 외부 리뷰: 권한·Secret·workflow·저장소 설정·dependency 정책을 바꾸는 PR에는 작성자 세션 밖의 리뷰를 하나 더한다. 공개 저장소는 CodeRabbit 무료 플랜의 리뷰로 충족한다. CodeRabbit 리뷰를 받을 수 없는 비공개 저장소는 다른 모델의 리뷰를 받거나, 받지 못한 사실을 기록하고 사람 승인 여부를 위험 기준으로 판단한다. 그 외 PR은 선택이다.
- CodeRabbit은 참고용 리뷰다. 필수 체크로 두지 않는다. 지적은 확인해 맞는 것만 고치고, 스레드마다 반영 여부를 답한 뒤 해결한다. Autofix·수정안 바로 커밋·docstring·테스트 생성은 쓰지 않는다. 다시 리뷰가 필요하면 `@coderabbitai full review`를 쓴다.
- 병합 전에 PR 본문이 저장소 PR 양식을 따르는지 확인한다(관련 Issue 또는 생략 이유, 플래그 상태 등). Dependabot PR에는 사람용 양식을 강제하지 않는다.
- 다른 사람이나 봇의 PR 브랜치에 커밋을 추가하면 PR 댓글로 알린다. 추가 커밋은 최종 head 리뷰와 필수 CI를 다시 거친다.
- 병합 위험 기준은 `prompts/pr-ci-setup.md` §10을 따른다.

## 6. 회고

- 에이전트 환경 개선에는 Matt Pocock의 `retro`를 사용한다. 동명의 다른 회고 스킬로 대체하지 않는다.
- 회고는 사용자가 요청한 세션·PR을 대상으로 한다. 매 PR이나 일정에 따라 자동 실행하지 않는다. 제안을 먼저 보고하고 사용자가 선택한 개선만 반영한다.
- 실행 절차와 완료 조건은 `prompts/pr-ci-setup.md` §7을 따른다.

## 7. 프로젝트 스킬과 작업 진입

- 개발 절차는 Matt Pocock 스킬을 설치된 원문대로 쓴다. 이 저장소는 스킬의 단계를 다시 정하지 않는다. 초기 설정에서 이 기준이 고르는 것(`AGENTS.md`만 사용)과 `main`에 들어가는 경계는 `docs/development-workflow.md`를 따른다.
