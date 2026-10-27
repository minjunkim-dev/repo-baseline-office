# 변경 기록

## 2026-10-27 — 사무실 인계를 커밋 기준으로

- 비교 실험에서 worker가 커밋하지 않은 채 넘겼는데, leader가 병합 요청이 가능하다고 보고했다. 병합할 head가 없는 상태였다.
- worker는 과제 브랜치에 커밋한 뒤 그 커밋에서 관문을 실행하고, `REPORT.md`에 커밋 SHA를 적는다. reviewer는 수정도 커밋하고 검수한 SHA와 수정 SHA를 적는다. leader는 브랜치의 현재 SHA가 검수 기록의 마지막 SHA와 같고 커밋하지 않은 변경이 없을 때만 병합을 요청한다.
- `run_gates.py`가 관문을 실행한 커밋 SHA를 보고에 적고, `claude-office/` 밖에 커밋하지 않은 변경이 있으면 실패한다. 이동한 파일은 양쪽 경로를 모두 보고, 로컬 설정과 관계없이 추적하지 않는 파일도 센다.
- reviewer가 수정을 커밋하면 그 커밋에서 관문을 다시 실행한다. leader는 `REPORT.md`의 관문 SHA도 현재 SHA와 같은지 확인한다.
- 공통 검사기·템플릿은 바뀌지 않아 소비 프로젝트 재적용은 필요 없다.

## 2026-10-27 — GitHub 설정 적용 도구

- `tools/apply_github_settings.py`를 추가했다. 프로젝트의 `.github/repository-settings.json`(감사 도구와 같은 기준선)을 읽어 다른 항목만 쓴다. 기본 실행은 현재 값과 기준값, 쓰기 요청을 출력만 하고, `--apply`는 쓴 뒤 다시 감사한다. 공개 여부·ruleset·workflow 파일과, 기준선 밖 설정이 켜진 브랜치 보호는 쓰지 않는다. 기준선 오류와 404 외의 조회 오류는 쓰기 전에 멈춘다.
- 새 프로젝트의 기준선 시작점 `templates/repository-settings.json`(채울 값은 `REPLACE`로 표시)과 이 저장소 자신의 `.github/repository-settings.json`을 두었다. 정책 값이 서로 어긋나면 `tools` 테스트가 실패한다.
- GitHub 설정 프롬프트 §3 표에 기준선이 이미 쓰던 값(기존 승인 무효화 On, 코드 소유자 리뷰 Off, 마지막 push 승인 Off, 브랜치 잠금 Off, Release 불변성 On)을 적었다.
- `scripts/check_github_settings.py`의 schema·저장소 이름·브랜치 검사를 `validate_target()`으로 분리했다. 동작은 같아 소비 프로젝트 재적용은 필요 없다. 다음에 다시 맞출 때 함께 복사된다.

## 2026-10-27 — Matt Pocock 스킬 사용법을 다시 적지 않음 (원본과 같게)

- 원본 `repo-baseline`과 같은 변경이다. 개발 절차 문서·PR/CI 셋업 프롬프트·POLICY는 원본과 바이트 단위로 같고, README는 같은 네 문장(일상 개발, 회고, 재적용 순서, 요청문의 외부 리뷰)을 바꿨다.
- 스킬의 단계는 설치된 원문대로 쓰고 시작점은 `/ask-matt`에 묻는다. 이 저장소에는 스킬이 정하지 않는 선택(`AGENTS.md`만 사용, `main` 경계, 리뷰·회고 정책)만 남긴다.
- 권한·Secret·workflow·저장소 설정·dependency 정책 PR의 추가 리뷰를 "다른 모델"에서 "작성자 세션 밖의 외부 리뷰"로 바꾸고, 공개 저장소는 CodeRabbit 무료 플랜으로 충족한다고 적었다. CodeRabbit은 참고용이며 필수 체크·자동 수정은 쓰지 않는다. GitHub 설정 프롬프트 §7도 CodeRabbit을 정리 대상에서 뺐다.
- CodeRabbit 리뷰 반영: 라벨 문서는 `triage`가 설치됐을 때만 완료 조건에 넣는다(셋업 스킬이 그때만 라벨 단계를 진행). Claude Code 플러그인에서는 `/mattpocock-skills:<이름>`처럼 플러그인 이름을 붙여 부른다.

## 2026-10-27 — 이 저장소에도 Dependabot 버전 업데이트 적용

- `.github/dependabot.yml`을 두었다. 생태계가 GitHub Actions뿐이라 `templates/dependabot.yml`을 그대로 쓴다. SHA로 고정한 `check.yml`의 action은 보안 알림이 생기지 않으므로 이 정기 업데이트로만 갱신된다(`POLICY.md` §2).
- 이 저장소에는 manifest가 없어 `apply_baseline.py`로 생성하지 않는다. 첫 줄을 사본이라는 설명으로 바꾸고, 나머지가 템플릿과 어긋나면 `tools` 테스트가 실패하게 했다.

## 2026-10-27 — 정본 경계와 제품 관문 보완

- README에 지금 정본은 원본 `repo-baseline`이고 셋업과 `apply_baseline.py` 실행은 원본에서 한다고 적었다. 여기서 실행하면 원본에 없는 커밋이 출처로 기록된다.
- 관문 테스트 칸이 과제 대상 저장소의 CI 명령을 실행하게 했다. 제품 worktree에는 이 저장소의 `tools/`가 없다.
- production은 세션에 자격 증명을 두지 않는 것으로 막고, `deploy.py`는 계획 도구임을 적었다.
- `run_gates.py`가 과제 폴더를 인자로 받는다. 셋업 문서 6단계와 PR/CI 셋업 프롬프트 §3은 원본과 같게 기존 `CLAUDE.md`를 `AGENTS.md`로 옮기게 했다.

## 2026-10-26 — 사무실 규칙을 AGENTS.md로 전환

- `claude-office/`의 공통 규칙과 역할 규칙을 `CLAUDE.md`에서 `AGENTS.md`로 옮겼다. 초기 설정도 스킬 블록을 `AGENTS.md`에 둔다.

## 2026-10-26 — 사무실 실험 복사본

- `repo-baseline` `1ddf420`을 이 저장소의 출발점으로 복사했다. 제품 적용 원본과 smallnext·BGLike·mobile-runtime은 바꾸지 않는다.
- `claude-office/`에 역할 폴더, 과제 INTENT, 관문 5칸, staging만 허용하는 배포 도구를 두었다. 기준 검사는 원본과 같은 unittest 명령을 호출한다.

## 2026-10-26 — 공개 저장소 전환

- 현재 파일·Git refs의 전체 이력·GitHub PR/댓글/실행 자료를 민감정보 점검한 뒤 public으로 전환했다. 기존 clone과 복사 기반 배포 방식은 유지한다.
- README에서 원본이 비공개라는 제약을 갱신했다. 공통 검사기·템플릿은 바뀌지 않아 소비 프로젝트 재적용은 필요 없다.

## 2026-10-26 — 초기 설정·작업 진입·원본 검증 보완

- 공식 Matt Pocock 초기 설정과 tracker·라벨·도메인 문서 연결을 추가했다. 작은 수정과 명세 → 의존성 티켓 → 준비된 작업 → 통합 검증 경로를 구분한다.
- 설정 검사기에 근거 있는 기능 미지원·비해당 예외와 LIMITED 결과를 추가했다. 기존 schema version 1은 유지하며, 예외가 없는 403·404·누락은 계속 검증 실패다.
- 원본 단위 테스트의 소비 프로젝트 의존성을 없앴다. 임시 Git 원본에서 실제 복사·프로젝트 테스트·출처·drift·복구·CodeQL pin 실패를 검사하고 읽기 전용 자체 CI에 연결했다.
- 복사본 해시 검사는 프로젝트 CI에서 별도 명령으로 실행한다. 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime. 기존 프로젝트·서버 설정은 이 변경으로 갱신되지 않는다.

## 2026-10-26 — 자체 리뷰와 선택적 회고

- 두 셋업 프롬프트·정책·README에서 Bugbot 전용 셋업·규칙 예산·서버 시험 요구를 제거했다. 자체 Standards·Spec 리뷰와 확실한 결함의 직접 수정·커밋을 기본으로 한다.
- 공통 manifest에서 Bugbot 검사기·테스트·규칙 목록을 제거하고 해당 원본 파일을 삭제했다. 기존 프로젝트의 CI 호출·manifest·복사본 정리 순서는 README의 전환 절차를 따른다. 고유 코딩 규칙은 보존한다.
- Matt Pocock `mattpocock-skills:retro`의 출처·사용자 요청·기록 기반 제안·선택한 개선의 반영·검증 절차를 추가했다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime. 서버 비활성화·계정 연결 해제와 기존 프로젝트 반영은 이 원본 변경으로 실행되지 않는다.

## 2026-10-18 — Grouped security updates

- `POLICY.md` §2: Grouped security updates를 공통값으로 켠다. 계정 기본값과 smallnext·BGLike·mobile-runtime에 적용했다. API로 감사할 수 없어 화면 확인 항목으로 남긴다.

## 2026-10-18 — Dependabot 설정 생성·추적

- `.github/dependabot.yml`을 `templates/dependabot.yml`과 `templates/dependabot-ecosystem.yml`로 생성한다. 프로젝트별 생태계는 manifest의 `ecosystems`에 적는다.
- 생성한 파일도 해시로 추적한다. 프로젝트에서 Dependabot 값을 바꾸면 CI가 실패한다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.

## 2026-10-18 — 독립 리뷰 6차 반영

- `check_github_settings.py`: `github/codeql-action` 이름을 대소문자 구분 없이 찾는다. GitHub는 owner/repo 이름의 대소문자를 구분하지 않는다.
- 이스케이프·줄 연결로 이름을 숨기는 표기는 보류했다. 후속 Issue로 추적한다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.

## 2026-10-18 — 독립 리뷰 5차 반영

- `check_github_settings.py`: 따옴표 밖의 `#`만 주석으로 지운다. 블록 경계를 블록을 가진 키의 열로 계산한다. 따옴표 안의 `: |`는 블록 헤더로 보지 않는다.
- 남은 한계(이스케이프·줄 연결로 이름 숨기기)는 위협 모델 밖으로 `POLICY.md` §3에 기록했다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.

## 2026-10-18 — 독립 리뷰 4차 반영

- `check_github_settings.py`: step 구조 해석을 없앴다. 주석과 블록 본문을 뺀 모든 `github/codeql-action/` 참조를 비교한다. 단독 `-`, 여러 줄 flow 표기로도 참조를 숨길 수 없다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.

## 2026-10-18 — 독립 리뷰 3차 반영

- `check_github_settings.py`: step 수준에서 읽지 못한 `github/codeql-action/` 표기는 실패로 처리한다(fail-closed). `-   name:`처럼 공백이 많은 목록 표기도 읽는다.
- `test_apply_baseline.py`: 테스트가 직접 만든 임시 폴더만 지운다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.

## 2026-10-18 — 독립 리뷰 2차 반영

- `apply_baseline.py`: `git --literal-pathspecs`로 추적 여부를 확인한다. `:(exclude)…` 같은 이름이 다른 파일과 매칭되지 않는다.
- `check_github_settings.py`: step 단위 `uses:` 키만 읽는다. `run:` 블록 본문과 `with:` 입력은 무시한다. 접힌 값은 고정으로 보지 않는다.
- `test_github_settings.py`: CodeQL 테스트가 프로젝트의 setup 종류와 무관한 fixture를 쓴다. default setup 프로젝트에서도 통과한다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.

## 2026-10-18 — 독립 리뷰 반영

- `apply_baseline.py`: 추적된 저장소 내부 파일만 원본으로 허용한다. manifest와 대상의 symlink·외부 경로를 거부한다.
- `check_github_settings.py`: CodeQL 참조를 실제 `uses:` 줄에서만 읽는다. 대소문자를 정규화하고 태그 참조도 불일치로 본다. default setup 기준선을 지원한다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.

## 2026-10-18 — 첫 버전

- 세 프로젝트(smallnext, BGLike, mobile-runtime)의 공통 검사기를 모았다.
  - `check_github_settings.py`: CodeQL `init`·`analyze` commit 불일치 검사를 추가했다.
  - `check_bugbot_rules.py`: 필수 규칙 목록을 `.github/repo-baseline.json`의 `bugbot_rules`에서 읽는다.
  - `check_repo_baseline.py`: 복사본 해시 검사를 새로 추가했다.
- Dependabot 공통값을 `POLICY.md`와 `templates/dependabot.yml`에 고정했다. 상한은 GitHub 기본값 5를 쓴다.
- 프롬프트 v4를 v5로 고쳤다. 값은 이 저장소를 참조한다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime.
