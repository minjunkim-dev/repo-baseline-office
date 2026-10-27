# repo-baseline-office

`minjunkim-dev/repo-baseline`의 `1ddf420`을 복사한 후보 저장소다. 지금 정본은 그 저장소다. 이 저장소는 그 기준 위에 Claude Code 팀 운영(`claude-office/`)을 얹어 실제 개발에서 검증하는 곳이고, 검증되면 정본으로 바꾼다. `claude-office/`는 제품 복사 manifest에 들어 있지 않다.

정본으로 바꾸기 전까지 새 프로젝트 셋업과 `tools/apply_baseline.py` 실행은 원본에서 한다. 이 도구는 출처를 원본으로 적으므로, 여기서 실행하면 원본에 없는 커밋이 출처로 기록된다. 정본으로 바꿀 때 `tools/apply_baseline.py`의 출처 이름도 함께 바꾼다. 셋업 문서와 프롬프트는 원본과 같게 유지한다.

아래는 복사해 온 기준이다. 1인 개발 저장소의 GitHub 설정·CI를 같은 결과로 맞춘다.

## 구조

| 경로 | 역할 | 프로젝트로 복사 |
| --- | --- | --- |
| `POLICY.md` | 공통값과 허용 예외 | 아니요. 참조만 한다 |
| `prompts/github-repository-settings.md` | GitHub 서버 설정 절차 | 아니요. 에이전트 채팅에 첨부한다 |
| `prompts/pr-ci-setup.md` | 문서·CI·리뷰·병합 절차 | 아니요. 에이전트 채팅에 첨부한다 |
| `templates/dependabot.yml`, `templates/dependabot-ecosystem.yml` | Dependabot 설정 원본 | 예. manifest의 `ecosystems` 목록으로 `.github/dependabot.yml`을 생성한다 |
| `templates/repo-baseline.json` | 복사 목록(manifest) 시작점 | 예. `.github/repo-baseline.json`으로 둔다 |
| `scripts/` | 프로젝트에 그대로 복사하는 검사기와 테스트 | 예. 수정하지 않는다 |
| `tools/apply_baseline.py` | `scripts/`를 프로젝트에 복사하고 해시를 기록 | 아니요 |

`scripts/`의 파일과 생성한 `.github/dependabot.yml`은 프로젝트에서 직접 고치지 않는다. 이 저장소에서 고친 뒤 다시 적용한다.
프로젝트의 `scripts/check_repo_baseline.py`가 복사본이 기록된 해시와 다르면 CI를 실패시킨다.

## 새 프로젝트에 적용

1. `templates/repo-baseline.json`을 프로젝트의 `.github/repo-baseline.json`으로 복사한다.
2. `.github/dependabot.yml` 항목의 `ecosystems`에 GitHub Actions 외의 실제 생태계를 적는다. 예: `{"package-ecosystem": "cargo", "directory": "/services/api"}`.
3. 테스트를 다른 폴더에서 실행하면 `files`의 대상 경로를 바꾼다. 예: `"scripts/source-only/test_github_settings.py": {"source": "scripts/test_github_settings.py"}`.
4. 원본 `repo-baseline`에서 다음을 실행한다. 이 저장소가 정본이 된 뒤에는 이 저장소에서 실행한다.

   ```bash
   python3 tools/apply_baseline.py /path/to/project
   ```

5. 두 프롬프트를 같은 채팅에 첨부하고 순서대로 적용한다. [프로젝트 초기 설정과 일상 개발](docs/development-workflow.md)을 프로젝트 작업 문서에 연결하고 스킬의 tracker·도메인 설정(`triage`가 설치돼 있으면 라벨도)까지 확인한다.
6. 복사 파일 해시 검사와 테스트가 기존 필수 CI job에서 실행되는지 확인한다. [GitHub 설정 기준선과 기능 지원](docs/github-settings-profile.md)의 예외·결과 구분을 따른다.

## 에이전트에게 보낼 요청문

두 프롬프트(`prompts/github-repository-settings.md`, `prompts/pr-ci-setup.md`)를 첨부하고 아래 글을 함께 보낸다.

```text
첨부한 두 프롬프트(repo-baseline 버전)를 기준으로 이 프로젝트에 실제 적용하고 검증해줘.

같은 채팅에서 GitHub 초기 점검 → PR·CI/CD 셋업 → GitHub 최종 적용·검증 순서로 진행해. 중복 작업은 피하고 보류 항목까지 마무리해.
공통값은 repo-baseline의 POLICY.md와 templates를 따르고, 공통 검사기는 tools/apply_baseline.py로 복사해. 값을 새로 고르지 마.

1인 개발·별도 컨텍스트의 자체 리뷰를 기준으로 해. 공개 배포와 production 변경은 하지 마.

최종 독립 리뷰·필수 CI 후 위험별 병합 기준을 적용해. 권한·Secret·workflow·설정 변경은 `POLICY.md` §5의 외부 리뷰(공개 저장소는 CodeRabbit)도 받아. 한쪽 문은 사람이 최종 head를 승인하게 해. 완료 항목과 미확인 항목을 구분해 보고해.
```

## 기존 프로젝트를 다시 맞춤

1. 먼저 차이를 본다. 아무것도 쓰지 않는다.

   ```bash
   python3 tools/apply_baseline.py /path/to/project --check
   ```

2. 다른 파일이 프로젝트의 의도된 변경이면 이 저장소로 옮긴다. 의도하지 않은 drift면 다시 적용한다.
3. 적용한 결과를 PR로 올리고 프로젝트의 리뷰·CI·병합 기준을 따른다.

## 일상 개발 시작

개발 절차는 Matt Pocock 스킬을 그대로 쓴다. 어떤 스킬로 시작할지는 `/ask-matt`에 묻는다. 처음 셋업과 이 기준이 더하는 `main` 경계는 [프로젝트 초기 설정과 일상 개발](docs/development-workflow.md)을 따른다.

## 자체 리뷰와 회고

기본 흐름은 구현 → 자동 검사 → 별도 Standards·Spec 리뷰 → 확실한 결함 수정·커밋 → 최종 변경의 리뷰·검사 → 위험별 병합이다. 상세 기준은 `prompts/pr-ci-setup.md` §5·§6을 따른다.

같은 실수나 탐색·도구 사용 문제가 있었던 작업은 Matt Pocock의 `retro`에 대상 세션·PR을 지정해 돌아본다. 사용자가 고른 개선만 반영하며 자동 정기 실행은 하지 않는다. 같은 프롬프트 §7을 따른다.

## 기존 리뷰 서비스 구성에서 전환

기존 프로젝트에 이 버전을 적용하기 전에 다음을 확인한다. `apply_baseline.py`는 기존 manifest를 읽으므로, 아래 정리 없이 실행하면 삭제된 원본을 찾지 못한다. 파일 삭제와 문서 이동은 프로젝트별 PR로 검토한다.

1. 이전 `.cursor/BUGBOT.md`에만 있는 고유 기준을 코딩 규칙·도메인 원문으로 옮긴다. 자체 리뷰 문서의 자료 선택 표에 연결하고, 내용이 보존된 요약 파일만 제거한다. 개인·전역 규칙은 유지한다.
2. 기존 CI·검사 명령에서 `check_bugbot_rules.py`·`test_bugbot_rules.py` 호출을 제거한다. 다른 빌드·테스트·보안 검사와 보호는 유지한다. trusted base의 기존 검사가 전환을 막으면 기존 정책으로 통과할 수 있는 전환 PR을 먼저 준비한다.
3. `.github/repo-baseline.json`에서 `source`가 `scripts/check_bugbot_rules.py` 또는 `scripts/test_bugbot_rules.py`인 항목과 `bugbot_rules` 키를 제거한다. 해당 복사 파일도 내용과 실제 위치를 확인한 뒤 제거한다.
4. 남은 파일의 차이를 `tools/apply_baseline.py /path/to/project --check`로 확인하고 다시 적용한다. 실제 프로젝트 CI에서 남은 공통 검사·자체 리뷰를 검증한다.

서버 서비스 비활성화와 GitHub App·계정 연결 해제는 저장소 파일 갱신과 별개다. 관련 서버 기능의 사용 여부와 영향 범위를 확인하고 승인된 변경만 수행한다.

## 이 저장소를 바꿀 때

1. `scripts/`, `templates/`, `tools/`를 바꾸면 테스트를 실행한다.

   ```bash
   python3 -m unittest discover -s scripts -p 'test_*.py'
   python3 -m unittest discover -s tools -p 'test_*.py'
   ```

   원본 단위 테스트는 합성 fixture를 사용한다. 도구 테스트는 깨끗한 임시 Git 원본을 만들고 default·advanced·미지원 설정의 프로젝트에 실제 복사한 뒤 테스트·출처 SHA·해시 drift·재적용·CodeQL pin 실패를 검사한다. 개인 프로젝트·GitHub 인증·네트워크는 필요 없다. 자체 CI는 같은 명령을 Python 3.11·3.13에서 실행한다. 실제 서버 감사·지원 여부·스킬 실행은 이 테스트의 검증 범위 밖이다.

2. 변경을 PR로 올려 `main`에 병합한 뒤, 최신 `main`을 받아 각 프로젝트에 다시 적용하고 프로젝트별 PR을 올린다. `apply_baseline.py`는 commit하지 않은 변경이 있으면 멈춘다. 병합 전 브랜치에서 적용하면 squash 병합 뒤 `main`에 없는 커밋이 출처로 기록된다.
3. `CHANGELOG.md`에 바뀐 점과 다시 적용할 프로젝트를 적는다.

## 적용 중인 프로젝트

| 프로젝트 | 저장소 |
| --- | --- |
| Smallnext | `minjunkim-dev/smallnext` |
| BGLike | `minjunkim-dev/BGLike` |
| Runstir | `minjunkim-dev/mobile-runtime` |

## 제약

- 이 저장소는 public이다. 파일을 복사해서 쓰므로 적용 대상 프로젝트의 공개 여부와 관계없이 쓸 수 있다.
- 프로젝트 CI는 이 저장소에 접근하지 않는다. 처음 적용하거나 갱신할 때 이 저장소를 clone한다. 공개 원본이므로 읽기 인증은 필요 없다.
- `apply_baseline.py`는 이 저장소에서 추적하는 일반 파일만 복사한다. 프로젝트 밖을 가리키는 경로와 symlink는 거부한다.
- 다른 저장소의 workflow가 이 저장소를 `uses:`로 참조하지 않는다. 소비 프로젝트의 CI는 복사본과 기록한 해시만으로 검증하며 원본 접근에 의존하지 않는다.
- Secret 값은 이 저장소에 두지 않는다.
