# 변경 기록

리뷰 모델의 현행은 「2026-11-07 — 같은 패밀리의 다른 모델 예외」다. 그 아래 「2026-11-06 — 역할 분담: 클라우드 기본, 활성 로스터」의 같은 패밀리 문장은 그날의 기록이다. 그날 문장이 검사기 거절과 Opus·Sonnet 한정을 말한 것은 당시 문서이고, 사용자 승인 원문이 확인된 이전 합의는 아니다.

Dependabot 현행은 「2026-11-06 — Dependabot PR은 다른 PR과 같다」다. 그 아래 날짜의 pin 전용 면제 문장은 당시 기록이다. 승인 댓글 편집의 현행은 「2026-11-06 — 승인 댓글 편집 감지와 댓글 재실행을 줄인다」다. 게이트가 `review/independent`·`review/security`를 요구하던 문장은 「2026-11-06 — 게이트는 근거 표와 승인 댓글만 본다」로 대체되었다. 신뢰 경계 경로의 Security 근거는 「2026-11-06 — Security 근거는 경로로 정한다」다. P0·P1 칸과 본문 편집 뒤의 `review/gate`는 「2026-11-07 — 열린 P0·P1과 본문 편집」이다. 병합은 「2026-11-07 — 병합 직전에만 success를 올린다」다. Grok Bot을 필수 조율자로 적던 문장의 현행은 「2026-11-07 — Grok Bot은 선택 조율이다」다. 리뷰 범위와 근거 표와 승인 SHA를 구분하는 문장은 「2026-11-07 — 재개 원본과 세 조건의 구분」이다. 그 절은 최종 full의 의무를 고르지 않는다. 재개 원본을 GitHub Issue로만 적은 문장은 「2026-11-07 — 정본은 Linear와 GitHub로 나눈다」가 좁힌다. 주어와 정본 이름을 고친 문장은 「2026-11-07 — 오독되는 이름을 고친다」다. 그 절은 지적의 해소나 수용이 아니다. 읽기 자격과 준비 상태 GraphQL의 현행은 「2026-11-07 — 읽기는 개발자 gh, 서명은 앱 PEM」이다.

## 2026-11-08 — 이월한 문구를 정리한다

- 문구만 바꾼다. 검사기, 스크립트, 게이트 도구, `app_id` 5641238, 필수 체크, 동작 서술은 바꾸지 않는다.
- `docs/development-workflow.md`: 리뷰 패밀리는 다른 것이 기본이고 다른 패밀리를 쓸 수 없을 때만 같은 패밀리 예외라고 맞춘다. 최종·이전 작성 패밀리를 모두 뺀 뒤 모델을 고르고, Opus가 사용 한도이면 Sonnet이 첫 리뷰라는 기존 한도 대체 문단을 연결한다. `prompts/pr-ci-setup.md` §5의 가벼운 경로 문장도 같게 맞춘다.
- 「Grok Bot은 선택 조율이다」 절의 같은 패밀리 서술에 「유효한 예외 기록은 제외」와 「Opus 한도 대체」를 잇고, 「같은 패밀리의 다른 모델 예외」 절에 정책 변경 문장을 더한다(PR #60에서 빠진 정정).
- 다시 적용할 프로젝트: 없음. 이 변경은 복사하는 파일을 바꾸지 않는다.

## 2026-11-08 — 비공개 보안 권고 보고 안내(PR #55)

- 루트 `SECURITY.md`를 더한다. 취약점은 공개 이슈가 아니라 이 저장소의 비공개 security advisory로 보고한다. 이 저장소 자신의 안내이고 코어 복사 목록 밖이다.
- 다시 적용할 프로젝트: 없음.

## 2026-11-07 — 읽기는 개발자 gh, 서명은 앱 PEM

- 권장 일상 경로: 개발자 `gh`가 읽기와 squash 병합을 한다. Keychain의 앱 PEM이 전용 앱 `review/gate`를 서명한다. 이 저장소의 핀은 `app_id` 5641238이다. 별도 읽기 PAT, `reviewgate` UID, 봉인, 해시, sudoers, `git archive`는 권장 경로가 아니다.
- `tools/post_review_gate.py`는 `GH_TOKEN`이 비어 있으면 거절한다. 거부 문장은 `GH_TOKEN must be set for reads`다. 권장 경로는 그 값을 그 프로세스 안에서만 `gh auth token`으로 채운다. 스크립트는 `gh auth token`을 호출하지 않고, 토큰이 다른 계정인지 검사하지 않는다. 개발자 토큰은 읽기 전용으로 좁혀져 있지 않다. `gh pr merge` 자식에는 `GH_TOKEN`을 넘기지 않는다. 앱 설치 토큰은 status POST에만 쓴다.
- 근거·diff·승인 댓글 시각은 REST GET이다. 승인 댓글 편집은 `updated_at`이 `created_at`과 같은지이고 GraphQL `lastEditedAt`이 아니다. `--merge`의 준비 상태(필수 체크, 리뷰 스레드, `reviewDecision`)는 같은 토큰의 GraphQL CheckRun이다. 예시 `--dry-run`은 `--merge`가 아니라서 그 GraphQL을 보지 않는다.
- `--merge`의 SHA 고정 squash, 파싱된 작성 기록·표·승인 댓글의 재검사, 풀리지 않은 스레드, 양의 정수 앱 핀, 본문 경주·SIGKILL·전원·응답 없는 네트워크는 그대로다. 신호 핸들러와 P2 파서는 이 변경이 건드리지 않는다.
- 1인 프로필의 게이트 경로는 소유자 SHA 댓글이다. 팀 프로필은 그 댓글을 요구하지 않고 `POLICY.md` §9의 사람 승인이다. 검사기 동작은 바꾸지 않았다.
- 헬퍼의 병합·핀·재검사 동작은 바꾸지 않았다. 빈 `GH_TOKEN` 거절은 그대로다.

## 2026-11-07 — 오독되는 이름을 고친다

- Linear는 내부 업무의 정본이다. Issue #61은 저장소 결정 기록이다. 같은 말이 아니다.

## 2026-11-07 — 정본은 Linear와 GitHub로 나눈다

- 바로 아래 절은 재개 원본을 GitHub Issue, PR 본문, 근거 표, 저장소 밖 리뷰 산출물로 적었다. 그 문장은 그 커밋의 기록이다. 내부 업무, 요구, 수락 기준, 우선순위, 결정의 정본은 Linear다. Issue #61은 그 요청의 저장소 결정 기록이다. 내부 업무의 정본이 아니다. 코드, PR, 리뷰, CI 근거는 GitHub다. GitHub Issue는 이미 있는 기록의 참조이거나 외부 제보다. 같은 내부 업무를 GitHub Issue로 새로 만들지 않는다.
- 읽은 원본은 [Linear 운영원칙](https://linear.app/swiftyee/document/업무-운영원칙-lineargithub-및-역할승인-경계-2f8f93d02c1b), [SWI-5](https://linear.app/swiftyee/issue/SWI-5), [SWI-6](https://linear.app/swiftyee/issue/SWI-6)이다. 그 문서가 적은 Linear–GitHub 자동 연동 미확인과, 단독 재개 시험 미실행을 실행 완료로 바꾸지 않는다. 필수 연동, 새 API, 기존 Issue 이관·폐쇄, 설정 변경은 없다.
- 검사기의 `Refs #N` 요구는 그대로다. 번호가 없는 새 내부 업무와 그 요구가 겹치면 사람이 정한다. 이 절은 그 번호를 면제하지 않는다.

## 2026-11-07 — 재개 원본과 세 조건의 구분

- 정본은 2026-11-07 사용자 요청 t100·t104와, 같은 날의 필요성 사전검증 둘이다. 그 검증은 3단계 등급, 표현만 변경의 독립 검토 면제, 최종 full 의무의 선택을 시행하지 않았다. 이 절도 그 선택을 현행으로 넣지 않는다.
- 재개 원본은 GitHub Issue, PR 본문, 근거 표, 저장소 밖 리뷰 산출물이다. Claude Code 단독과 Cursor 단독이 그 기록으로 잇는다. 단독 도구는 작성 모델의 자기 검토 면제가 아니다. 독립 검토를 못 하면 `미실행`이다. 한도가 소진된 모델은 다시 실행하지 않는다. 패밀리 규칙과 검사기는 바꾸지 않는다.
- `prompts/pr-ci-setup.md` §5의 두 문장(전체 한 번 뒤 delta, 최종 전체 diff)은 그대로 두고, 리뷰 범위·현 head 근거 표·정확 SHA 승인을 서로 다른 조건으로 적는다. 원 full과 delta와 통합 확인으로 충분한지, 최종 별도 full이 필수인지는 미적용 결정안이다.

## 2026-11-07 — Grok Bot은 선택 조율이다

- 정본은 2026-11-07 19:12 KST 사용자 요청(t46~t50)이다. 그 이전 합의 원문을 확인한 기록이 아니다. 결정 기록은 Issue #61이다. Issue #58에는 기존 본문을 유지한 채 포인터만 덧붙인다. #59와 PR #60은 다른 결정이다.
- 접수·Issue·작업 분해·배정·CI와 리뷰 추적·근거 확인·보고는 사람 또는 선택 조율자다. Grok Bot은 그 선택 보조다. Claude Code 단독과 Cursor 단독으로 개발을 끝까지 한다.
- 플랫폼 단독은 같은 모델의 자기 승인이 아니다. 구현 에이전트와 리뷰 에이전트, 다른 패밀리, 필수 테스트, 독립 리뷰, 소유자 승인, 게이트, 정확한 head SHA는 유지한다. Matt 스파인과 pstack 배치는 그대로다. 검사기, 스크립트, 설치, 인증, 결제, 보호, `review/gate` `app_id` 5641238은 바꾸지 않는다. 현행 main의 검사기는 같은 패밀리 리뷰를 거절한다(유효한 `같은 패밀리 예외:` 기록은 제외).
- 단독 경로는 구현 경로다. 리뷰는 작성 패밀리와 다른 패밀리가 하는 것이 기본이다. Claude Code로 쓰면 Claude 밖(Composer·Grok), Cursor의 Composer·Grok으로 쓴 되돌리기 어려움은 첫 버그 찾기·Security에 Opus가 필요하다(Opus가 사용 한도이면 Sonnet으로 대체한다). 한 도구만으로 독립 리뷰까지 끝난다고 적지 않는다.
- 같은 패밀리의 다른 모델·다른 에이전트 예외는 PR #60으로 병합됐다(Issue #59). 이 절의 표현은 그 예외를 전제로 한다. 다른 패밀리를 쓸 수 없을 때만 쓰고, 근거 표에 `같은 패밀리 예외:` 블록이 있어야 한다.
- 고친 파일: `README.md`, `POLICY.md`, `docs/development-workflow.md`, `prompts/pr-ci-setup.md`. `docs/review-gate-app.md`의 키 보관 금지 위치(Grok Bot의 컴퓨터)는 필수 경로 문장이 아니라 그대로 둔다.

## 2026-11-07 — 같은 패밀리의 다른 모델 예외

- 이 변경은 정책 변경이다. 「리뷰 패밀리는 작성 패밀리와 항상 달라야 한다」를 「다른 것이 기본이고, 다른 패밀리를 쓸 수 없을 때만 같은 패밀리의 다른 모델·다른 에이전트 예외」로 바꾸고, 「Haiku는 리뷰에 쓰지 않는다」를 지운다. 정책 불변이 아니다.
- 합의 정본은 2026-11-07 18:21 KST 사용자의 직접 승인이다. 18:22 KST에 이슈와 문서에 남기기로 했다. 결정 기록은 Issue #59다. #58의 본문은 바꾸지 않는다.
- 기본은 리뷰 패밀리가 작성 패밀리와 다른 것이다. 다른 패밀리를 쓸 수 없을 때만 같은 패밀리의 다른 모델이 독립 리뷰를 한다. 구현 에이전트와 리뷰 에이전트는 달라야 한다. 같은 모델은 불가하다. Opus·Sonnet만의 예외는 두지 않는다. Haiku를 일괄 금지하지 않고, Security와 어려운 버그 찾기는 Haiku로 통과하지 않는다. 적합한 다른 모델이 없으면 `미실행`으로 기다린다.
- `scripts/check_review_status.py`는 `같은 패밀리 예외:` 블록의 문자열만 본다. 다른 패밀리 행은 블록 없이 통과한다. 이유, 검토 SHA, 에이전트 증빙, 작성·리뷰 모델이 빠지거나 같으면 실패한다. 가용성은 추정하지 않고, 에이전트 식별은 조회하지 않는다. 소유자 승인, 필수 축, P0·P1, 표의 head SHA, `result`는 그대로다.
- `tools/post_review_gate.py`의 스냅샷에 그 블록을 넣는다. 블록을 고치면 병합 직전 재읽기가 달라진다. success를 올리는 조건, auto-merge, `review/gate`의 `app_id` 5641238, 필수 체크는 바꾸지 않는다. 이 변경은 branch protection을 쓰지 않고 status를 올리지 않는다.
- 비목표: 게이트 면제, 구독·플랫폼 확대, Gemini·GPT를 활성 로스터에 넣기, PR #57 head `251d34933ae2c26b1cfb3f04c99729409ab6b160`의 수정. 이 PR이 병합되기 전에 다른 PR이 이 예외로 게이트를 통과했다고 말하지 않는다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime. 병합 뒤 `scripts/check_review_status.py`와 `scripts/test_review_status.py`를 `tools/apply_baseline.py`로 다시 복사한다. `tools/post_review_gate.py`는 복사하지 않는다. 그 복사는 이 변경이 실행하지 않는다.

## 2026-11-07 — 병합 직전에만 success를 올린다

- `tools/post_review_gate.py`: `--merge`가 없는 실행은 success를 올리지 않는다. 근거가 통과하면 pending이고, 실패하면 failure다. `--dry-run`은 읽기만 한다. `--merge`는 준비된 PR, 걸려 있지 않은 auto-merge, `review/gate` 외의 필수 체크, 풀리지 않은 리뷰 스레드를 확인한 뒤에만 success를 올리고, 파싱된 작성 기록·표·승인 댓글을 다시 읽은 다음 개발자 `gh`로 `--squash --match-head-commit` 병합한다. `isRequired`는 pull request 번호가 있어야 한다. 필수 체크의 이름과 앱은 기본 브랜치의 `.github/repository-settings.json`이다. PR head의 그 파일은 쓰지 않는다. 시도의 순서는 시작 시각이고, 같은 시각에 결과가 갈리면 실패로 닫는다. success를 올리려 한 뒤의 예외와 SIGINT·SIGTERM·SIGHUP·SIGQUIT는 failure 게시가 끝날 때까지 미룬다. openssl 서명은 다른 세션이라 터미널이 이 프로세스 그룹에 보낸 신호로 죽지 않는다. 병합 중 그 신호는 gh를 끊는다. 정리에 들어갈 때, defer를 켜기 전이나 켜는 줄에서 신호가 나도 failure 게시와 이전 핸들러 복원은 계속된다. 그 게시는 한 번이고 원자적이지 않다. SIGKILL은 잡지 못한다. 지원하는 앱 id는 양의 정수다. `-1`은 고정이 아니라서 거절한다. 병합 여부는 종료 코드가 아니라 PR을 다시 읽어 정한다. 정리가 실패하면 그 실패를 숨기지 않는다. `gh`와 `openssl`에는 허용한 환경 변수만 넘긴다. 앱 설치 토큰은 `gh`에 넘기지 않는다. 그 문장의 `GH_TOKEN`은 개발자 `gh auth token`이 아니다는 위 「읽기는 개발자 gh, 서명은 앱 PEM」로 대체되었다. 병합 제약 자체는 이 절이 현행이다. `Review status` workflow는 `review/gate`를 올리지 않는다.
- 남은 위험: 검사·게시·재검사·병합은 원자적이지 않다. 본문 편집이 재검사와 겹칠 수 있다. success 뒤의 SIGKILL·전원 손실·네트워크 단절은 success를 남긴다. 같은 Mac 사용자와 키는 신뢰 경계다. 그 SHA가 아직 열린 PR의 head이고 조회가 성공할 때만 `--merge` 없이 다시 실행해 지울 수 있다. head가 바뀌거나, PR이 닫히거나, 조회가 실패하면 옛 success는 지워지지 않는다. failure 정리는 한 번뿐이고, 그 게시가 실패하면 success가 남을 수 있다. 사람이 `gh pr merge`만 실행하지 않는다. auto-merge는 예약하지 않는다. 절대적인 신선도 보장이 아니다. description의 digest는 감사 표식이고 GitHub가 병합 때 다시 검사하지 않는다.
- 필수 체크와 `review/gate` `app_id` 5641238, 앱 권한은 바꾸지 않는다. webhook을 더하지 않는다.

## 2026-11-07 — 열린 P0·P1과 본문 편집

- 근거 표의 P0와 P1은 아직 수정·기각·한계 수용으로 끝나지 않은 수다. 끝난 지적과, Security가 아닌 범위 밖 Pre-existing은 그 칸에 넣지 않고 표 아래에 적는다. 칸이 0보다 크면 실패다. 기각 문장이나 한계 수용 문장은 그 수를 지우지 않는다. P2가 0보다 커도 그 칸만으로는 실패하지 않는다.
- 본문 편집이 `review/gate`를 자동으로 지우지는 않는다. `Review status`의 `edited` 재실행은 필수 체크가 아니고 그 status를 올리지 않는다. success를 누가 올리는지는 위 「병합 직전에만 success를 올린다」가 정한다. 본문 편집을 받는 새 webhook이나 앱 권한은 없다.
- Dependabot의 `scripts/workflow_policy.py` 본문 건너뜀은 근거 표의 작성 기록을 빼지 않는다. 버전 전용 예외는 없다.
- 필수 체크와 `review/gate` `app_id` 5641238은 바꾸지 않는다.

## 2026-11-07 — 호출 이름과 변경 기록 시점을 구분한다

- 「시작 범위는 PR 양식 하나와 참조 계약이다」의 메타 이슈 문장은 그 절을 쓴 시점의 기록이라고 고쳤다. 현재 링크는 「실행 추적은 이슈 58이다」다.
- `docs/start.md`: `/ask-matt` 같은 짧은 이름은 순서다. Claude Code 플러그인의 호출은 `docs/development-workflow.md`의 `/mattpocock-skills:ask-matt`다. 설치는 그 문서의 「처음 한 번」이고 코어가 하지 않는다. `vendor/mattpocock-skills/matt-code-review/`는 리뷰 스킬 원본이고 전체 manifest만 복사한다.

## 2026-11-07 — 실행 추적은 이슈 58이다

- README와 `docs/start.md`는 [이슈 #58](https://github.com/minjunkim-dev/repo-baseline/issues/58)만 연결한다. 열린 이슈 목록은 그 이슈가 정본이다. 이 저장소 문서는 시작 절차의 정본이고 그 목록을 복사하지 않는다. 이슈를 새로 만들거나 닫지 않는다.

## 2026-11-07 — 시작 범위는 PR 양식 하나와 참조 계약이다

- `docs/start.md`, README, `docs/development-workflow.md`, `prompts/pr-ci-setup.md`: 코어가 복사하는 파일은 `.github/pull_request_template.md` 하나다. Matt 절차, `POLICY.md`, 명령 네 칸은 설치가 아니라 참조다. format·lint·type·test·build는 대상 스택이거나 `N/A`와 이유다. 포매터와 새 의존성은 스택 선택 없이 넣지 않는다. 예제는 POSIX `sh`와 Git clone이다. Git이 없는 환경과 POSIX 셸이 없는 Windows는 지원 범위가 아니다.
- 이 원본의 독립 패밀리 리뷰, 라운드 상한 3, `review/gate`, `POLICY.md` §10은 코어 복사가 약하게 하지 않는다. 외부 리뷰와 스레드 규칙은 §5 그대로다.
- 이 절을 쓴 시점에는 메타 이슈 URL이 없어 README에 링크를 만들지 않았다. 그 문장은 그때의 기록이다. 현재 링크는 위 「2026-11-07 — 실행 추적은 이슈 58이다」가 정한다. 필수 체크와 workflow의 3.11·3.13 job, `review/gate` `app_id` 5641238은 이 절에서 바꾸지 않았다.

## 2026-11-07 — Python 3.15 검사를 필수 목록 밖에 더한다

- `.github/workflows/check.yml`: `Baseline checks (Python 3.11)`과 `Baseline checks (Python 3.13)`은 그 minor로 unittest를 계속 실행한다. 새 버전으로 바꿔 성공을 위장하지 않는다. job `Baseline checks`를 더한다. `python-version`은 `3.15`이고 `check-latest: true`다. `3.x`, prerelease, free-threaded는 쓰지 않는다. 이 job은 필수 체크가 아니다.
- 선택 이유: 2026-11-07에 Python 개발자 가이드와 python.org 다운로드는 3.15를 bugfix, 최신 patch 3.15.2(2026-10-25)로 적는다. 3.14.10도 bugfix다. 3.13·3.11은 security다. 3.16은 pre-release다. 공식 LTS는 없다. 개인 도구 CI의 한 minor는 가장 최근 stable bugfix인 3.15다. `actions/python-versions` manifest에서 3.15.2는 `stable: true`이고 3.15.0-rc.3은 `stable: false`다.
- `.github/repository-settings.json`의 필수 체크는 바꾸지 않는다. `review/gate` `app_id` 5641238도 바꾸지 않는다. 서버 보호는 적용하지 않는다.
- `scripts/test_workflow_policy.py`: 깊이 제한을 넘는 JSON은 여전히 종료 코드 1과 `FAIL`이다. 3.15에서는 `RecursionError` 대신 객체·flags 형식 거부로 끝날 수 있다. `scripts/workflow_policy.py`는 바꾸지 않는다. 소비 프로젝트에 다시 적용하지는 않는다.
- 남은 순서: 이 bridge가 `main`에 있고 새 job이 성공한 뒤, 별도 승인으로 live 필수 context를 `Baseline checks`와 `review/gate`로 바꾼다. 그 적용과 readback 다음에야 옛 matrix를 빼는 PR을 낸다. 그 전에 옛 job을 지우면 보호가 없는 context를 기다린다.

## 2026-11-07 — 언어와 무관한 시작과 코어 복사 목록

- `docs/start.md`: 새 프로젝트의 공통 순서. 완료 기준은 Matt spec·ticket이다. `eval.md`를 요구하지 않는다. 검증자와 리뷰어를 나눈다. 명령 네 칸은 프로젝트 스택이고, 없으면 `N/A`다. 리뷰 라운드 상한 3은 유지한다. 병합 큐·단계 배포·상시 감시는 선택이다.
- `templates/repo-baseline.core.json`: PR 본문 양식만 복사한다. Python 검사기와 그 테스트는 넣지 않는다. `templates/repo-baseline.json` 전체는 GitHub·검사기 프로필로 남는다. 기존 manifest를 코어 파일로 바꾸지 않는다.
- 기본 시작 명령은 `cp`와 대상 스택의 검사다. 그 명령은 Python이 아니다. 해시 복사, 정책 검사, 게이트 서명은 Python 도구로 남고 기본 명령에 넣지 않는다. Python 3.11·3.13 matrix는 `.github/workflows/check.yml`의 이 저장소 도구 CI로 유지한다. 그 workflow와 `.github/repository-settings.json`의 필수 체크는 바꾸지 않는다. 새 프로젝트에 그 job 이름을 복사하지 않는다. 두 버전을 고른 이유나 지원 계약 문서는 이 저장소에 없다.
- 게이트 파일, `.github/repository-settings.json`, `review/gate` `app_id` 5641238, 검사기 동작은 바꾸지 않는다. 서버 설정과 앱은 적용하지 않는다.
- 다시 적용: 새 프로젝트만 코어 목록으로 시작할 수 있다. smallnext, BGLike, mobile-runtime은 기존 manifest를 유지한다. 이 변경은 그 저장소에 복사할 검사기 변경이 없다.

## 2026-11-06 — Security 근거는 경로로 정한다

- `scripts/check_review_status.py`: 공통 경로, 의존성 파일 이름, 기준 브랜치의 `.github/trust-boundary-paths`에 걸리면 Security 칸의 `해당 없음`은 실패다. compare가 목록을 주지 않거나 경로 이름이 없으면 실패다. 그 파일 읽기가 404가 아닌 오류면 확인 불가다. 버그 찾기의 `해당 없음`은 그대로다. `review/independent`와 `review/security` status는 읽지 않는다.
- 근거 표의 HTML 주석은 Author 줄과 표 둘 다 보기 전에 뺀다. 닫히지 않은 주석은 실패다. 모델을 적은 행은 P0·P1·P2가 정수여야 하고, P0나 P1이 0보다 크면 실패다. P2가 0보다 커도 그 칸만으로는 실패하지 않는다. effort가 비어 있으면 실패다. `result`가 `fail`, `failed`, `failure`, `실패`이면 실패다.
- `review/independent`와 `review/security` 상수 이름은 검사기에서 뺐다. status는 advisory다. 필수 체크와 `review/gate` `app_id` 5641238은 바꾸지 않는다. Dependabot 면제는 없다. 승인 댓글의 REST 시각 비교는 그대로다.

## 2026-11-06 — 게이트는 근거 표와 승인 댓글만 본다

- `scripts/check_review_status.py`와 `tools/post_review_gate.py`: `review/independent`와 `review/security`를 읽지 않는다. 없거나 failure여도 게이트는 그 이유로 실패하지 않는다. 성공 조건은 PR 본문 근거 표와, 1인 프로필에서 게이트 경로를 바꾼 head의 승인 댓글이다. Dependabot PR도 그 표와 승인 댓글을 다른 PR과 같이 요구한다. pin 전용 면제는 없다. 표의 축은 Standards, Spec, 버그 찾기, Security다. 모델이거나, 그 축이 허용하는 `해당 없음:`이어야 한다. Standards와 Spec은 `해당 없음`으로 비우지 않는다. 앱은 `review/gate`만 올린다. 소유자는 그 두 status를 참고로 남겨도 된다.
- 승인 댓글 규칙은 앞 절 그대로다. REST `updated_at`이 `created_at`과 같은 문자열일 때만 인정한다. 같은 초 편집은 구분하지 않는다. GraphQL `lastEditedAt`은 보지 않는다. 댓글은 `Review status`나 `review/gate`를 자동으로 다시 돌리지 않는다.
- 품질 기준은 status와 별개다. Standards·Spec의 기본은 Composer이고, 버그 찾기와 Security의 기본은 Opus다. 리뷰 패밀리는 작성 패밀리와 다르다(`docs/development-workflow.md`).
- `.github/repository-settings.json`의 필수 체크는 바꾸지 않는다. Baseline checks (Python 3.11), Baseline checks (Python 3.13), `review/gate`(`app_id` 5641238)다. `Review status`는 필수 목록에 없다. 이 변경은 branch protection을 쓰지 않고 commit status를 올리지 않는다. 카나리 E는 다시 열지 않는다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime. `scripts/check_review_status.py`와 `scripts/test_review_status.py`를 `tools/apply_baseline.py`로 다시 복사한다. `tools/post_review_gate.py`는 복사하지 않는다.

## 2026-11-06 — Dependabot PR은 다른 PR과 같다

- 합의(2026-11-06, Dependabot=normal): 2026-11-04의 pin 전용 Dependabot 면제를 거둔다. `scripts/check_review_status.py`는 버전·해시 줄 비교, `uses:` pin 모양, web-flow 커밋터, 주 버전 판정으로 `review/independent`·`review/security`·근거 표·승인 댓글을 빼지 않는다. Dependabot PR도 근거 표와 승인 댓글을 다른 PR과 같이 요구한다. 이 문장이 적던 `review/security` status 요구는 위 「Security 근거는 경로로 정한다」에서 근거 표의 Security 모델로 바뀌었다. status는 advisory다. 신뢰 경계 경로의 Security `해당 없음`은 실패다. 게이트 경로면 사람 승인 댓글이 필요하다. `tools/post_review_gate.py`는 그 diff만으로 success를 올리지 않는다. 자동 성공 경로는 없다.
- `scripts/workflow_policy.py`가 Dependabot의 본문 절과 72자를 넘는 제목을 건너뛰는 것은 그대로다. 그 건너뜀은 근거 표와 하드도어 승인 댓글을 대신하지 않는다.
- `POLICY.md`, README, `docs/review-gate-app.md`, `docs/development-workflow.md`, `docs/github-settings-profile.md`, `prompts/pr-ci-setup.md`, `prompts/github-repository-settings.md`, `prompts/weekly-check.md`는 이 규칙으로 고쳤다. §5 승인 댓글 문단의 `review/security`·`review/independent` 면제 문장도 뺐다. 작성자로 그 status를 빼지 않고, Action 주 버전이나 `uses:` pin 모양으로도 빼지 않는다. `외부 리뷰` 불릿이 앞 문단에 붙어 있던 줄바꿈을 되돌렸다. `docs/development-workflow.md`의 리뷰·수정 불릿, `prompts/pr-ci-setup.md`의 5번, `POLICY.md` §9의 GitHub auto-merge 불릿도 같은 방식으로 줄을 나눴다. 게이트 경로 문장은 그 경로를 바꾸면 승인 댓글이 필요하다고 적는다.
- `.github/repository-settings.json`의 필수 체크는 바꾸지 않는다. `strict`와 `review/gate` `app_id` 5641238은 그대로다. 이 변경은 branch protection을 쓰지 않고 status를 올리지 않는다. 카나리 E는 다시 열지 않는다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime. `scripts/check_review_status.py`와 `scripts/test_review_status.py`를 `tools/apply_baseline.py`로 다시 복사한다. `tools/post_review_gate.py`는 복사하지 않는다. 소유자가 repo-baseline에서 `--repo`로 실행한다.

## 2026-11-06 — 승인 댓글 편집 감지와 댓글 재실행을 줄인다

- `scripts/check_review_status.py`: 승인 댓글은 REST `updated_at`이 `created_at`과 같은 문자열일 때만 인정한다. GraphQL `lastEditedAt`·`includesCreatedEdit`는 보지 않는다. REST 시각은 초 단위라 같은 초 편집은 구분하지 않는다. 하드 도어의 SHA 전체 댓글 요구는 그대로다. 댓글을 고치지 말고 새 댓글을 단다.
- `templates/review-status.yml`과 `.github/workflows/review-status.yml`: `issue_comment` 트리거와 재실행 job을 뺐다. `scripts/rerun_review_status.py`는 삭제했다. 승인 댓글은 `Review status`와 `review/gate`를 자동으로 다시 돌리지 않는다. 새 댓글 뒤에 그 head의 `Review status`를 직접 다시 돌리거나 `tools/post_review_gate.py`로 게이트를 다시 올린다.
- `tools/post_review_gate.py`: 승인 댓글은 REST GET으로 읽는다. 승인 댓글 편집 판정에 `POST /graphql`은 쓰지 않는다. `--merge` 준비 상태의 CheckRun GraphQL은 「2026-11-07 — 읽기는 개발자 gh, 서명은 앱 PEM」이다.
- 이벤트 정책 템플릿은 `issue_comment` 허용을 남겨 둔다. 그 허용은 구독이 아니다. 필수 체크와 `.github/repository-settings.json`은 바꾸지 않는다. 이 변경은 branch protection을 쓰지 않는다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime. `scripts/check_review_status.py`, `scripts/test_review_status.py`를 `tools/apply_baseline.py`로 다시 복사한다. `templates/review-status.yml`을 `.github/workflows/review-status.yml`로 다시 복사한다. 소비 저장소의 `scripts/rerun_review_status.py`는 지운다. `tools/post_review_gate.py`는 복사하지 않는다. 카나리 E는 다시 열지 않는다. `.github/repository-settings.json`의 필수 체크는 그대로다.

## 2026-11-06 — 트렁크와 선택적 피처 플래그

- `docs/development-workflow.md`: 트렁크를 적었다. 기준 브랜치는 `main` 하나다. 작업 브랜치는 짧다. 병합은 squash만이고 병합하면 브랜치를 지운다. GitFlow의 `develop` 브랜치와 `release` 브랜치는 두지 않는다. 끝나지 않은 작업은 꺼진 피처 플래그로 `main`에 둔다.
- `POLICY.md` §4·§5, `prompts/github-repository-settings.md`, `prompts/pr-ci-setup.md`, README: 플래그 파일 검사는 `.github/workflow-policy.json`의 `feature_flags`로 저장소마다 고른다. 이 저장소는 `false`다. 그 검사는 이 저장소의 필수 체크가 아니다. `.github/workflow-policy.json`이 없으면 기본 경로 `config/feature-flags.json`을 읽는다. 그 레지스트리가 없으면 검사는 실패한다. `feature_flags`가 `false`이거나 `null`이면 읽기를 건너뛴다. 문자열 경로면 그 파일을 본다. `apply_baseline.py`가 복사하지 않는 것은 `.github/workflow-policy.json`이다. `config/feature-flags.json`도 `templates/repo-baseline.json`에 없어 복사하지 않는다. 서버 보호와 `.github/repository-settings.json`은 이 변경이 쓰지 않는다.

## 2026-11-06 — Review status는 이전 SHA의 success를 이어받지 않는다

- `scripts/check_review_status.py`: 새 head에는 그 SHA의 `review/independent`·`review/security` success가 있어야 한다. diff identity, 변경 후 blob id, 기준 브랜치 갱신, force-push 이전 head는 근거가 아니다. 같은 SHA에서 다른 작성자의 최신 status를 실패로 보는 규칙과 승인 댓글·근거 표는 그대로다.
- `tools/post_review_gate.py`: 게이트 읽기는 force-push 이력과 diff를 더 이상 검사기에 넘기지 않는다. `review/gate`는 그 SHA의 status만 본다. 필수 체크 목록과 보호 적용은 바꾸지 않는다.
- `POLICY.md`, `docs/review-gate-app.md`, `docs/development-workflow.md`, `prompts/pr-ci-setup.md`, `prompts/github-repository-settings.md`: 이어받기 설명을 이 규칙에 맞춘다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime. `scripts/check_review_status.py`와 `scripts/test_review_status.py`를 `tools/apply_baseline.py`로 다시 복사한다. `tools/post_review_gate.py`는 복사하지 않는다. 이 변경은 branch protection을 쓰지 않고, `.github/repository-settings.json`의 필수 체크를 바꾸지 않는다.

## 2026-11-06 — 필수 체크에서 Review status를 뺀다

- `.github/repository-settings.json`: `protection.required_status_checks.checks`에서 `{"context": "Review status", "app_id": 15368}`을 뺐다. `Baseline checks (Python 3.11)`, `Baseline checks (Python 3.13)`(`app_id` 15368)와 `{"context": "review/gate", "app_id": 5641238}`는 그대로다. `strict`는 true다. `Review status` workflow와 `scripts/check_review_status.py`는 증거 검사로 남는다. 이 파일은 기대값이다. 이 변경은 branch protection을 쓰지 않는다. 병합 뒤 소유자가 Mac에서 `tools/apply_github_settings.py`로 적용한다. 카나리 E 재시험(PR #47, Issue #32)은 Actions 15368의 위조와 소유자 status가 병합을 BLOCKED로 남긴 기록이다.
- `POLICY.md`, README, `docs/github-settings-profile.md`, `docs/development-workflow.md`, `docs/review-gate-app.md`, 셋업 프롬프트는 이 저장소의 필수 체크 목록에서 `Review status`를 뺐다.
- `apply_baseline.py`는 `.github/repository-settings.json`을 복사하지 않는다. smallnext, BGLike, mobile-runtime의 기준선은 이 변경이 바꾸지 않는다.

## 2026-11-06 — 게이트 문서: Keychain 우선·합의(문서만)

- 과거 문서. 별도 읽기 토큰을 권장 경로로 둔 문장은 「2026-11-07 — 읽기는 개발자 gh, 서명은 앱 PEM」로 대체되었다. 그때 `docs/review-gate-app.md`는 1인·소규모 팀의 **권장 경로**를 **개발자 macOS Keychain의 앱 PEM**(실행 시에만 임시 파일로 꺼냄) + **개발자 `gh`로 증거 status** + **`GH_TOKEN` 게이트 전용 읽기 토큰(`tools/post_review_gate.py` 현행)** + **기본 브랜치의 깨끗한 checkout에서 `post_review_gate.py`**로 다시 썼다. **unset GH_TOKEN**과 “별도 읽기 토큰 불필요”는 코드와 어긋나서 뺐다. 체크아웃은 `git status --porcelain`·`git reset --hard origin/main`(또는 핀 SHA)로 고정. 같은 **UID 에이전트**와의 격리 한계·Keychain 과장 없음·PEM을 argv에 넣지 않는 설명을 추가했다. **멀티라인 PEM**은 `security -w` 대화형 한 줄 입력에 맞지 않으므로 **Keychain Access GUI**(또는 0600 파일→GUI)만 권장하고, 대화형 `-w`로 PEM 붙여넣기는 금지했다. **게이트 `GH_TOKEN` 스코프**는 `Reader`의 REST·GraphQL 호출에 맞춘다. 증거 `gh api` 전에 **`unset GH_TOKEN GITHUB_TOKEN`**. 예전 **reviewgate 전용 UID·봉인(seal)·sudoers·git archive** 중심 절차는 **레거시(선택)**로 남겼다.
- `prompts/pr-ci-setup.md`, `docs/development-workflow.md`: 권장 경로를 위와 맞추고 **봉인 사본** 문장을 **레거시**로 표시했다.
- `POLICY.md` §5·§9, `README.md`, `docs/github-settings-profile.md`: repo-baseline의 `review/gate` `app_id` 기록이 **5641238**(#44)이므로, `REPLACE:<APP_ID>`는 **다른 저장소·채우기 전**의 자리표시자로만 쓴다고 고쳤다. 합의의 나머지(증거-in-gate·Dependabot·편집 댓글 규칙·코드 삭제 순서)는 **후속 PR**이다. Python 게이트 로직·`.github/repository-settings.json` 필수 목록 변경은 이 PR에 없다.

## 2026-11-06 — 역할 분담: 클라우드 기본, 활성 로스터

- `docs/development-workflow.md` 역할 분담. 코드는 Claude Code와 Cursor가 쓴다. Grok Bot은 쓰지 않는다. 기본 머신은 클라우드다. Claude Code는 `claude --cloud` 또는 claude.ai/code이고, Cursor는 클라우드 에이전트다. Mac은 시뮬레이터·Xcode·실기기·Keychain·장기 비밀(`gh`, review-gate pem, Claude 로그인)만이다. 장기 비밀은 Cursor AWS VM, Claude Anthropic VM, Grok Bot 공유 컴퓨터에 두지 않는다. 넘기기는 양방향이다. Mac의 Cursor IDE도 작성 경로다. 같은 모델의 사용량은 로컬과 클라우드가 같다.
- 구독은 Claude Code Pro와 X 구독 $30(Cursor, Grok Bot)뿐이다. Cursor 선불 크레딧으로 고르는 Cursor 호스트 Claude, GPT, Codex, Gemini는 활성 로스터가 아니다. GPT는 Cursor 안에서 그 크레딧으로만 고를 수 있고, 이 소유자는 쓰지 않는다.
- 작성 모델: Haiku는 트리아지·초안·작은 문서, Sonnet은 일상 구현, Opus는 어려운 설계·구현, Grok은 무거운 구현, Composer는 작은 수정·테스트·문서다. effort는 제품 기본값만 쓰고 설정에서 고정하지 않는다. 근거 허용 값에는 `설정 없음`이 그대로다.
- 비밀이 없는 작업을 정보가 부족하다는 이유로 Cursor 클라우드만 고르거나 작성 모델을 Grok으로 고정하지 않는다. Claude 클라우드와 Cursor 클라우드 에이전트 둘 다 유효하다.
- 리뷰 패밀리는 작성 패밀리와 다르다. 활성 리뷰 패밀리는 Composer, Grok, Claude다. 인식 표의 Gemini·GPT 행은 CI 별칭으로 남고 활성 후보는 아니다. 되돌리기 쉬움은 다른 패밀리 모델 하나로 Standards·Spec·버그 찾기를 본다. 되돌리기 어려움의 첫 버그 찾기는 작성 패밀리가 Claude가 아니면 Opus다. Security는 신뢰 경계를 건드리거나 사람이 요청할 때 본다. 첫 모델이 Opus이면 수정 뒤 델타는 Sonnet 한 번이다. 그 밖의 델타와 한도 대기는 아래 줄이다. Opus와 Gemini를 한 쌍으로 요구하지 않는다. 작성 패밀리가 Claude뿐이면 Standards·Spec은 Composer다. 이전에 Composer가 있으면 아래 줄이다. Composer가 부족하면 델타는 Grok 한 번이고 근거에 적는다. 한도 대체 순서는 Opus, Sonnet, Composer, Grok이다.
- Matt 스파인(`/ask-matt` 다음 `/grill-with-docs`, `/to-spec`, `/to-tickets`, `/implement`. Standards·Spec은 `/matt-code-review`. pstack은 `interrogate`, `blast-radius`, `create-verification-skill`, `correct`만)은 그대로다. 이 절은 누가·어디서·어느 모델인지만 정한다.
- `POLICY.md`는 작성 주체를 이 절로 넘기고 있어 고치지 않았다. 게이트 파일과 CI workflow는 안 바꿨다.
- 같은 도구가 모델을 바꿔 커밋해도 `이전 작성 모델`에 이름을 모두 적는다. 검사기는 그 줄만 패밀리에 넣는다. 사람이 이전 작성자이면 `이전 작성 모델`에 `없음`을 넣지 않는다. 사람은 어느 PR에든 Security를 더 요청할 수 있다. 첫 패스·델타·한도 대체는 최종 작성과 `이전 작성 모델`의 패밀리를 모두 뺀다. 이전에 Composer가 있고 마지막이 Claude이면 Composer는 건너뛰고 Grok이다. 델타 전에 고친 diff의 신뢰 경계를 다시 본다. 수정이 외부 입력이나 권한을 더하면 첫 패스가 `해당 없음`이어도 Security를 연다. Opus가 한도라 첫 모델이 Sonnet이면 델타는 그 다음 다른 패밀리다. Composer가 부족하면 델타는 Grok 한 번이다. 다른 패밀리를 우선한다. 한도로 다른 패밀리가 없으면 먼저 기다린다. 같은 패밀리의 다른 모델은 마지막 수단이고, 그 쌍은 Opus와 Sonnet뿐이다. 같은 모델이 그 축을 다시 보는 것은 금지다. 검사기는 그 마지막 수단도 거절하므로 병합은 다른 패밀리를 기다린다.

## 2026-11-06 — 게이트 sudo는 래퍼 파일을 직접 실행한다

- 승인 명령은 `sudo -u reviewgate -H /Users/reviewgate/.config/repo-baseline/review-gate-run`이다. `env`를 끼우면 sudo가 `/usr/bin/env`를 실행하고 허용 목록이 거절한다. 규칙은 `sudo visudo -f /etc/sudoers.d/review-gate`로 두고 모드는 `0440`이다. 그 목록은 비관리자 개발 계정에 적용된다. `admin`은 암호 장벽이다(`docs/review-gate-app.md`).

## 2026-11-06 — 게이트 키를 reviewgate 세션으로 받고 sudo는 래퍼만 허용한다

- pem은 `reviewgate` 브라우저로 받는다. 개발 홈을 경유하지 않는다. `/Users/Shared`를 쓸 때만 개발 `~/Downloads` 원본과 Shared 원본을 각자 지운다(`docs/review-gate-app.md`).
- 두 번째 배치의 봉인 트리는 `root:wheel`이다. 개발 UID가 소유하면 해시 검사는 의미가 없다. 그 임시 파일이 있는 동안 같은 UID의 에이전트는 키를 읽는다.
- `sudo -u reviewgate bash -s`는 쓰지 않는다. 비관리자 개발 계정의 sudoers는 `review-gate-run`만 허용하고 `NOPASSWD`는 없다. `admin`은 암호 장벽이다. `timestamp_timeout=0`이다. 에이전트 셸에서 sudo하지 않는다. sudo가 있으면 같은 UID 에이전트가 pem을 읽는다.
- `git archive`는 개발 UID로 한다. `sudo git`은 쓰지 않는다. Keychain 배치의 `GH_TOKEN`은 서브셸 안 명령에만 둔다. `rm -P`는 APFS에서 덮어쓰기를 보장하지 않는다. 해시는 `/usr/bin/shasum -a 256`이다.

## 2026-11-06 — 게이트 키는 reviewgate 홈의 일반 파일이거나 Keychain에서 꺼낸 임시 파일이다

- 스크립트는 Keychain을 읽지 않는다. `REVIEW_GATE_APP_KEY`는 봉인 트리 밖의 `0600` 일반 파일이다. 첫 배치는 개발 UID와 다른 `reviewgate` 홈이다. 같은 UID의 Keychain은 실행할 때마다 임시 파일로 꺼내 쓰고 지운다. 개발 `$HOME`의 pem과 섞지 않는다. 그 임시 파일이 있는 동안 같은 UID의 에이전트로부터 키를 지키지 않는다(`docs/review-gate-app.md`).

## 2026-11-06 — 이름 변경은 버전 전용이 아니고 게이트는 봉인 사본으로 실행한다

- 과거 동작. 2026-11-06 「Dependabot PR은 다른 PR과 같다」로 대체되었다. 그때 `only_versions`는 `previous_filename`이 있거나 `status`가 `modified`가 아니면 거절했다. 워크플로 밖으로 pin만 바꿔 이름을 옮겨도 Dependabot 면제가 아니었다.
- 과거 배치. 봉인 트리와 게이트 계정 읽기 토큰은 권장 일상 경로가 아니다. 현행은 「2026-11-07 — 읽기는 개발자 gh, 서명은 앱 PEM」이다. 그때는 게이트 실행을 체크아웃이 아니라고 적었고, 봉인 트리는 `tools/post_review_gate.py`, `scripts/check_review_status.py`, `scripts/pr_author.py`이며 `python3 -I`로 돌렸다. `GH_TOKEN`은 게이트 계정의 읽기 전용 토큰이라고 적었다.

## 2026-11-06 — review/gate 앱 ID와 봇 근거, 버전 전용 diff

- `review/gate`의 `app_id`는 0보다 큰 정수이고 15368이 아니어야 한다. `scripts/check_github_settings.py`와 `tools/apply_github_settings.py`가 같은 조건으로 거절한다. 0, -1, 15368은 통과하지 않는다.
- `[bot]`으로 끝나는 로그인의 `review/independent`와 `review/security`는 1인·팀 모두 실패다. 승인 댓글의 `[bot]` 작성자는 승인이 아니다. 팀 프로필은 그 댓글을 요구하지 않으므로, 그 댓글이 팀 검사를 실패로 만들지는 않는다. 팀 프로필이 사람 작성자를 보지 않는 것은 그대로다.
- 과거 동작. 2026-11-06 「Dependabot PR은 다른 PR과 같다」로 대체되었다. 그때 버전 전용 판정은 `\n`으로만 줄을 나눴다. `\r`, 다른 제어 문자, U+2028, U+2029가 있으면 버전 전용이 아니었다. 신뢰 경계의 workflow는 `uses:`의 40자 SHA 또는 `v` 태그 pin만 버전 전용이었다. Dependabot처럼 보이는 커밋을 REST나 web-flow로 만드는 쪽은 카나리 전이었다(`docs/review-gate-app.md`).
- `tools/apply_github_settings.py`와 `docs/review-gate-app.md`를 공통 경로와 게이트 경로에 넣었다.

## 2026-11-06 — review/gate는 전용 GitHub App만 충족한다

과거 동작. 이 절의 `scripts/rerun_review_status.py` 복사는 2026-11-06 「승인 댓글 편집 감지와 댓글 재실행을 줄인다」로 대체되었다.

- 카나리 E(PR #39)는 필수 체크 `Review status`(`app_id` 15368)를 workflow 토큰의 같은 이름 체크 run으로 위조할 수 있음을 보였다. 승인 경계는 commit status `review/gate`다. 전용 앱은 Commit statuses 쓰기와 Metadata 읽기만 가지고, 키는 `reviewgate` 홈의 0600 일반 파일이거나, 같은 UID Keychain에서 그 실행만 꺼낸 임시 파일이다. 개발 홈의 서 있는 pem이 아니다. `Review status` job은 증거 검사로 남고 `review/gate`를 쓰지 않는다. `strict`는 true다.
- `tools/post_review_gate.py`가 그 SHA의 근거를 확인하고 앱 설치 토큰으로 `review/gate`만 올린다. `--dry-run`은 POST하지 않는다. `GITHUB_ACTIONS`에서는 거부한다. Dependabot 버전 전용 예외는 그때 검사기와 같았다. 그 예외는 과거 동작이고, 2026-11-06 「Dependabot PR은 다른 PR과 같다」로 대체되었다. 테스트는 모의 HTTP다.
- repo-baseline의 `.github/repository-settings.json`은 `review/gate`의 `app_id`를 **5641238**로 기록한다(#44). 다른 프로젝트나 채우기 전에는 `REPLACE:<APP_ID>`가 남을 수 있고, 그동안 적용 도구는 조회 전에 멈춘다. 이 변경은 branch protection을 쓰지 않는다. 저장소별 적용 전후와 앱 등록·키 교체·E 재시험은 `docs/review-gate-app.md`다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime. 그때 `scripts/check_review_status.py`와 `scripts/rerun_review_status.py`를 `tools/apply_baseline.py`로 다시 복사했다. `scripts/rerun_review_status.py` 복사는 과거 동작이고, 2026-11-06 「승인 댓글 편집 감지와 댓글 재실행을 줄인다」로 대체되었다. `templates/review-status.yml`의 주석도 `.github/workflows/review-status.yml`로 다시 복사했다. `tools/post_review_gate.py`는 복사하지 않았다. 소유자가 repo-baseline에서 `--repo`로 실행했다. `.github/repository-settings.json`의 `review/gate` 한 줄은 각 저장소 PR에서 기존 체크와 `strict: true`를 유지한 채 더했다. E 재시험 기록이 Issue #32에 있기 전에는 그 셋을 적용하지 않았다.

## 2026-11-06 — feature flag 파일 오류는 FAIL로 보고한다

- `scripts/workflow_policy.py`: feature flag 파일을 읽다 `UnicodeDecodeError`나 `RecursionError`가 나면 traceback으로 끝나지 않는다. `FAIL: Feature flags:`를 출력하고 종료 코드 1로 끝난다. 설정 파일의 `RecursionError`도 `FAIL: workflow policy config:`로 끝난다. 이전에도 프로세스는 0이 아니어서 검사는 통과하지 않았다. 통과하는 트리와 symlink 거부는 그대로다. `--root`가 없으면 검사기 옆 트리를 읽고, symlink는 파일로 세지 않는다. (#26)
- `scripts/test_workflow_policy.py`: `--root` 없이 symlink `AGENTS.md`와 symlink flag 파일을 거절하는 동작을 고정한다. 잘못된 UTF-8과 깊이 제한을 넘는 JSON도 `--root`가 있을 때와 없을 때 FAIL로 본다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime. `scripts/workflow_policy.py`와 `scripts/test_workflow_policy.py`를 `tools/apply_baseline.py`로 다시 복사한다. 스크립트 해시는 적용할 때 `.github/repo-baseline.json`에 다시 기록된다. 바뀐 복사 파일의 sha256은 이 변경의 PR 본문에 있다.

## 2026-11-05 — 1인 프로필은 다른 계정의 리뷰 status와 편집된 승인 댓글을 받지 않는다

과거 동작. GraphQL `lastEditedAt` 편집 감지와 `issue_comment` 재실행은 2026-11-06 「승인 댓글 편집 감지와 댓글 재실행을 줄인다」로 대체되었다.

- `scripts/check_review_status.py`: 1인 프로필에서 `review/independent`와 `review/security`는 `creator.login`이 저장소 소유자이거나 `STATUS_ACTORS`에 있을 때만 success다. `STATUS_ACTORS`는 `scripts/check_review_status.py`의 설정이고 지금은 비어 있다. 서버 앱의 로그인은 이 저장소에서 넣은 뒤 다시 복사한다. 소비 프로젝트의 복사본을 직접 고치지 않는다. 다른 작성자(`github-actions[bot]` 포함)의 status는 실패다. 없는 status로 보지 않는다. 목록은 `commits/{sha}/statuses`이고 최신순이다. context마다 첫 항목을 쓴다. combined status에는 `creator`가 없어 쓰지 않는다. 이어받기 해시는 diff와 바뀐 파일의 변경 후 blob id 전체다. `index` 줄의 축약 SHA는 쓰지 않는다. id는 바뀐 경로의 상위 디렉터리 tree만 읽는다. 다른 gitlink는 열지 않고, 바뀐 경로가 gitlink이면 그 커밋 id를 넣는다. 잘리거나 읽지 못하면 이어받지 않는다. 같은 경로의 `diff --git` 헤더는 가운데에서 자른다. `svc b/package.json`의 ` b/`를 구분자로 쓰지 않는다. 경로가 다르면 `rename to`·`copy to`를 읽고, 없으면 이어받지 않는다. 삭제·이름 변경·바이너리를 본다. `@@`의 함수 이름은 남긴다. 이름이 없는 파일은 그 헤더만으로 구분되지 않고, blob id가 그 이동을 가른다. 기준 브랜치가 다른 파일만 바꾸면 이어받는다. 같은 파일을 바꾸면 줄만 밀려도 다시 리뷰받는다. YAML, JSON, 같은 함수 안의 이동, CR을 넣은 줄도 이어받지 않는다. `prompts/pr-ci-setup.md`의 이어받기 문장도 같다. 이어받기의 이전 SHA도 같다. 팀 프로필은 작성자를 보지 않는다. (#34)
- 과거 동작. 2026-11-06 「승인 댓글 편집 감지와 댓글 재실행을 줄인다」로 대체되었다. 그때 승인 댓글은 `updated_at`이 `created_at`과 같은 문자열이고 GraphQL `lastEditedAt`이 null이며 `includesCreatedEdit`가 아닐 때만 인정했다. 편집한 댓글은 무효였고 새 댓글을 달았다. REST 시각은 초 단위라 같은 초 편집은 두 문자열이 같았다. 그 편집은 `lastEditedAt`으로 거절했다. `scripts/rerun_review_status.py`는 `created`·`edited`·`deleted`에서 검사기를 다시 돌렸다. 실행 목록을 읽지 못하면 그 head에 실패하는 `Review status` 체크를 남겼다. 편집 이벤트의 `comment.user`는 처음 작성자였고, 다른 계정이 소유자 댓글을 고쳐도 재실행되었으며 그 댓글은 승인이 아니었다.
- `scripts/test_review_status.py`의 임시 git 저장소는 전역·시스템 git 설정을 읽지 않는다. `commit.gpgsign`과 `diff.noprefix`가 픽스처 커밋과 `diff --git a/` 헤더를 바꾸지 않는다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime. 그때 `scripts/check_review_status.py`, `scripts/test_review_status.py`, `scripts/rerun_review_status.py`를 `tools/apply_baseline.py`로 다시 복사했다. `scripts/rerun_review_status.py` 복사는 과거 동작이고, 2026-11-06 「승인 댓글 편집 감지와 댓글 재실행을 줄인다」로 대체되었다. `templates/review-status.yml`의 주석도 `.github/workflows/review-status.yml`로 다시 복사했다. workflow 파일은 manifest 해시 대상이 아니었다. 스크립트 해시는 적용할 때 `.github/repo-baseline.json`에 다시 기록되었다. 바뀐 복사 파일의 sha256은 이 변경의 PR 본문에 있었다.

## 2026-11-05 — Review status를 필수 체크로 기록한다

- `.github/repository-settings.json`: `protection.required_status_checks.checks`에 `{"context": "Review status", "app_id": 15368}`을 더했다. `strict`는 true다. 기존 `Baseline checks (Python 3.11)`, `Baseline checks (Python 3.13)`는 그대로다. context는 `templates/review-status.yml`과 `.github/workflows/review-status.yml`의 job 이름 `Review status`와 같다. PR #31의 체크 이름도 `Review status`다. 이슈 #32.
- 이 파일은 기대값이다. 이 변경은 branch protection을 쓰지 않는다. 병합 뒤 소유자가 Mac에서 `tools/apply_github_settings.py`로 적용한다.
- 과거 동작. 2026-11-06 「Dependabot PR은 다른 PR과 같다」로 대체되었다. 그때 적용되면 Dependabot 버전 전용 PR을 뺀 모든 PR(되돌리기 쉬움 포함)에 `review/independent`가 필요했다. 1인 프로필에서 status는 소유자만 올린다는 규칙이다. 에이전트가 status를 올리는 것은 금지지만 GitHub가 기술적으로 막지는 않는다. 그 시점의 검사기는 status 작성자를 확인하지 않았고, 확인은 #34에서 고친다.
- `POLICY.md` §5·§9·§10, README, `docs/development-workflow.md`, `docs/github-settings-profile.md`, 셋업 프롬프트와 재적용 절차는 위 사실을 적는다. `templates/repository-settings.json`의 자리표시자는 그대로다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime. `apply_baseline.py`는 `.github/repository-settings.json`을 복사하지 않는다. repo-baseline에 보호 규칙을 적용하고, 카나리 시험(같은 이름 체크 위장, 이전 실패 run이 남은 head의 병합 가능 여부)을 통과하고, status 작성자·편집된 승인 댓글 검사기 수정이 병합·재적용된 뒤에 각 저장소가 별도 PR로 같은 체크를 적는다. 카나리 결과는 Issue #32 댓글 하나에 적는다. 그 기록이 없으면 멈춘다. 그 세 저장소도 기본 브랜치에 workflow가 있고 job이 한 번 성공한 뒤에 적는다. 그 PR도 branch protection을 쓰지 않는다. 적용은 각 저장소에서 소유자가 Mac으로 한다. Dependabot 예외 카나리는 과거 동작이고, 2026-11-06 「Dependabot PR은 다른 PR과 같다」로 대체되었다.

## 2026-11-05 — 결정 분류 이름을 되돌리기 어려움·되돌리기 쉬움으로 바꾼다

- 한쪽 문(one-way door: 되돌리기 어려운 결정)은 되돌리기 어려움, 양쪽 문(two-way door: 되돌리기 쉬운 결정)은 되돌리기 쉬움이다. 필드 이름은 `Door:`로 둔다. 절 이름 `문 판정`은 그대로다. (#29)
- PR 본문 값은 `Door: 되돌리기 쉬움` 또는 `Door: 되돌리기 어려움`이다. 1인 프로필 승인 댓글은 `되돌리기 어려움 승인: <head의 전체 SHA>`다. 댓글 첫 줄의 그 접두사와 40자 SHA만 인정한다.
- 옛 `Door: 양쪽 문`·`Door: 한쪽 문`과 옛 댓글 `한쪽 문 승인: <sha>`는 deprecated다. `scripts/workflow_policy.py`와 `scripts/check_review_status.py`가 같은 의미로 받는다. 다른 철자, 다른 필드 이름, SHA가 다른 댓글은 통과하지 않는다. `scripts/rerun_review_status.py`는 댓글 본문을 읽지 않고 그 검사기를 다시 돌렸으므로 옛 접두사도 같은 경로로 통과했다. 그 재실행은 과거 동작이고, 2026-11-06 「승인 댓글 편집 감지와 댓글 재실행을 줄인다」로 대체되었다. 제거는 #30이다.
- 아래 날짜의 기록에 나오던 옛 이름은 이 이름으로 바꿔 적었다. 그 날짜의 검사기가 받던 문자열은 위 옛 값이다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime. 바뀐 복사 파일의 sha256은 이 변경의 PR 본문에 있다.

## 2026-11-05 — 기본 브랜치가 아닌 base로 리뷰 게이트를 통과하지 못한다

과거 동작. 아래 `scripts/rerun_review_status.py`의 `issue_comment` 재실행은 2026-11-06 「승인 댓글 편집 감지와 댓글 재실행을 줄인다」로 대체되었다. base가 기본 브랜치가 아니면 통과하지 못하는 규칙은 그대로다.

- `templates/review-status.yml`: `pull_request_target`은 `branches: [main]`만 본다. 다른 base에서는 Review status가 돌지 않는다. 검사기 코드는 계속 기본 브랜치 것이고 PR 코드는 실행하지 않는다.
- `scripts/check_review_status.py`: 이 PR의 `base.ref`가 저장소 `default_branch`와 다르면 실패한다. 이벤트 `BASE_SHA`는 `compare(BASE_SHA...default_branch)`의 status가 `ahead` 또는 `identical`일 때만 그 브랜치 위에 있다고 본다. 재실행은 옛 payload를 남기므로, 사이드 base로 통과했던 run을 main으로 옮긴 뒤 재실행해도 통과하지 않는다. 둘 중 하나를 읽지 못하면 확인되지 않은 것으로 실패한다. 실패 이름은 `review/base-branch`다. commit status가 아니다. 다른 base의 PR은 통과 근거가 아니다. `missing()`은 그 PR 번호만 본다.
- `scripts/rerun_review_status.py`(과거 동작. 2026-11-06 「승인 댓글 편집 감지와 댓글 재실행을 줄인다」로 대체되었다): 그때 `issue_comment`에는 브랜치 필터가 없었다. PR base가 기본 브랜치가 아니면 체크를 게시하지 않고 끝냈다. 같은 head의 main PR을 거짓 실패로 만들지 않았다.
- `templates/pr-policy.yml`: `pull_request`도 `branches: [main]`만 본다. `pull_request`는 PR의 workflow를 쓰므로 필터를 지운 PR은 이 검사를 다시 돌릴 수 있다. PR conventions만으로는 게이트가 아니다. workflow 변경은 필수 체크가 된 Review status가 막는다.
- `branches: [main]`은 리터럴이다. repo-baseline, smallnext, BGLike, mobile-runtime의 기본 브랜치는 `main`이다. 기본 브랜치가 `main`이 아니면 workflow의 `branches`를 그 이름으로 맞춘다.
- `scripts/test_workflow_policy.py`: `--root`의 빈 경로, 절대 경로, 상위(`..`) 경로 거부를 다시 검사한다. `scripts/workflow_policy.py`의 거부 동작은 그대로다.
- 다시 적용할 프로젝트: smallnext, BGLike, mobile-runtime. 그때 `templates/review-status.yml`을 `.github/workflows/review-status.yml`로, `templates/pr-policy.yml`을 `.github/workflows/pr-policy.yml`로 복사했다. `scripts/check_review_status.py`, `scripts/test_review_status.py`, `scripts/rerun_review_status.py`, `scripts/test_workflow_policy.py`는 `tools/apply_baseline.py`로 다시 복사했다. `scripts/rerun_review_status.py` 복사는 과거 동작이고, 2026-11-06 「승인 댓글 편집 감지와 댓글 재실행을 줄인다」로 대체되었다. workflow 파일은 manifest 해시 대상이 아니었다. 스크립트 해시는 적용할 때 `.github/repo-baseline.json`에 다시 기록되었다.

## 2026-11-05 — 리뷰는 패밀리가 다르면 된다

- `docs/development-workflow.md` 역할 분담: 필수 조건은 리뷰 패밀리가 작성 패밀리와 다른 것이다. 플랫폼은 보지 않는다. Claude는 Opus와 Sonnet을 한 패밀리로 두고, Cursor 안의 Claude도 Claude다. Grok이 쓴 PR은 Composer, Gemini, Claude, GPT가 볼 수 있다. Claude가 쓴 PR은 Grok, Composer, Gemini, GPT가 볼 수 있다.
- 되돌리기 쉬움은 Standards·Spec·버그 찾기를 다른 패밀리 모델 하나로 한다. Security는 신뢰 경계만. 되돌리기 어려움(CI, 게이트, 보안 경계)의 버그 찾기·Security는 지금 쓸 수 있는 가장 강한 다른 패밀리다. 가능하면 패밀리 둘이다. 작성 패밀리가 Grok일 때의 예는 Opus와 Gemini다.
- 가장 강한 모델이 한도면 다음 다른 패밀리를 쓰고 근거에 적는다. 병합을 그 한도로 멈추지 않는다. 되돌리기 어려움의 더 강한 모델 재리뷰는 후속 Issue이고, 할지는 소유자가 정한다.
- 작성 기본은 Grok(Cursor 클라우드 에이전트)이고 리뷰 기본은 Claude다. Claude Code로 직접 만든 PR의 기본 리뷰는 Cursor 모델이다.
- CI는 패밀리가 같으면 실패한다. 그 검사는 #25가 넣는다. 관리자(Grok Bot)는 모델 이름, 지적 수, P1 기각 이유가 사실인지를 본다.
- `POLICY.md` §5·§10과 셋업 프롬프트 §5의 모델 문장은 이 규칙을 가리킨다. Claude 리뷰를 필수로 두던 문장은 뺐다. 게이트 파일과 CI workflow는 안 바꿨다.

## 2026-11-05 — PR 본문과 리뷰 근거 표를 검사

과거 동작. 이 절의 「댓글 재실행은 그대로다」는 2026-11-06 「승인 댓글 편집 감지와 댓글 재실행을 줄인다」로 대체되었다.

- `scripts/workflow_policy.py`: smallnext의 PR 제목·브랜치·이슈 링크 검사를 이 저장소의 원본으로 둔다. `feat`/`fix`/`refactor`/`perf`/`test`/`revert`는 `Refs`/`Closes`/`Fixes`/`Resolves #N`이 필요하다. 설명은 소문자 라틴 또는 한글로 시작한다. 본문에 `## Summary`, `## Evidence`, `## Merge Danger`, `Door:`(`되돌리기 쉬움` 또는 `되돌리기 어려움`), 작성 기록(`Author: <tool> / <model>` 또는 `작성 도구`/`작성 모델`)이 있어야 한다. tool은 `Claude Code`, `Cursor`, `Cursor 클라우드 에이전트`, `사람`이다. Dependabot은 본문 절 검사만 면제한다. `AGENTS.md`와 feature flag 검사는 기본으로 켜 두고 `.github/workflow-policy.json`으로 끈다. 설정 파일이 없으면 smallnext와 같다. 이 저장소는 그 둘을 끄고 `cursor` 브랜치를 허용한다. 본문은 파싱만 한다.
- `templates/pr-policy.yml`: `pull_request`의 opened, edited, synchronize, reopened, ready_for_review에서 돈다. 스크립트와 `.github/workflow-policy.json`은 base에 파일이 있으면 base에서 읽고, 없을 때만 PR 쪽을 실행한다. 그 예외는 검사기를 처음 넣는 PR뿐이다. base의 검사기가 `--root`를 모르면 job은 실패한다. 그 검사기는 PR 트리를 보지 못한다. `AGENTS.md`, `CLAUDE.md`, feature flag는 `--root`로 PR 트리를 읽고 실행하지 않는다. `pull_request_target`은 쓰지 않는다. `Review status`도 `ready_for_review`에 다시 돈다. 그 두 스크립트와 `.github/workflow-policy.json`은 공통 경로이자 되돌리기 어려움이다.
- `scripts/pr_author.py`: 작성 기록 파서는 이 파일 하나다. `workflow_policy.py`와 `check_review_status.py`가 가져온다. 둘 다 `scripts/`로 복사된다.
- `scripts/check_review_status.py`: 리뷰 근거 표에 Standards, Spec, 버그 찾기, Security가 있고, 모델이 비어 있지 않으며, head SHA가 그 실행의 head 전체 40자와 같고, P0·P1이 정수인지 본다. 리뷰 모델과 작성 모델의 패밀리가 같으면 실패다. Opus와 Sonnet은 Claude다. Grok, Composer, Gemini, GPT는 각각 한 패밀리다. 플랫폼은 보지 않는다. 표에 없는 이름은 실패다. 근거 표가 여러 개면 마지막 표를 본다. 버그 찾기와 Security의 `해당 없음: <이유>`는 P0·P1·P2가 0일 때 통과한다. `미실행`은 실패다. 실패 이름은 `review/evidence`다. commit status가 아니다. Dependabot 작성자는 그때 이 표 검사에서 뺐다. 그 면제는 과거 동작이고, 2026-11-06 「Dependabot PR은 다른 PR과 같다」로 대체되었다. 본문을 고치면 이미 있는 `edited`로 다시 돌았다. #21의 댓글 재실행은 그때 그대로였다. 그 재실행은 과거 동작이고, 2026-11-06 「승인 댓글 편집 감지와 댓글 재실행을 줄인다」로 대체되었다. 댓글 본문은 읽지 않았고, PR 본문도 실행하지 않는다.
- 다시 적용할 프로젝트: Smallnext·BGLike·Runstir. `scripts/workflow_policy.py`, `scripts/pr_author.py`, `scripts/test_workflow_policy.py`, `scripts/check_review_status.py`, `scripts/test_review_status.py`를 `tools/apply_baseline.py`로 복사한다. 양식과 `templates/pr-policy.yml`도 다시 복사한다. smallnext는 설정 파일을 두지 않으면 `AGENTS.md`와 feature flag 검사가 유지된다. 본문 절 검사는 새로 실패할 수 있다.

## 2026-11-05 — PR 본문 양식

- `.github/pull_request_template.md`: Summary, Evidence, Merge Danger, `Author: <tool> / <model>`, 리뷰 근거 표를 둔다. 축은 Standards, Spec, 버그 찾기, Security다. tool은 Claude Code, Cursor, Cursor 클라우드 에이전트, 사람이다. `작성 도구`와 `작성 모델` 두 줄도 같은 기록이다. 검사기는 아직 이 양식을 강제하지 않는다.
- `templates/repo-baseline.json`이 그 파일을 `.github/pull_request_template.md`로 복사한다.
- 다시 적용할 프로젝트: Smallnext·BGLike·Runstir. `tools/apply_baseline.py`로 양식을 복사한다.

## 2026-11-05 — 작성 도구와 리뷰 모델

- `docs/development-workflow.md` 역할 분담: 구독은 Claude Code와 X 구독(Cursor, Grok Bot)뿐이다. 별도의 GPT·Codex 구독은 없다. Cursor 안의 GPT는 쓸 수 있다. PR을 쓰는 도구는 로컬·비밀·대화로 따라가는 작업이면 Claude Code(Mac)이고, 이슈 하나로 클라우드에서 끝까지 검사되면 Cursor 클라우드 에이전트다. 애매하면 Cursor 클라우드 에이전트이고, 로컬·비밀에서 막히면 Claude Code로 넘긴다. PR 본문에 작성 도구와 작성 모델을 적는다.
- 당시 규칙(그 커밋 당시의 현행은 「리뷰는 패밀리가 다르면 된다」였고, 그 절이 아래 두 문장을 바꿨다. 이 파일 맨 위의 현행은 2026-11-06 절이다): 리뷰 모델을 작성 도구의 반대쪽으로 두었고, 약한 모델만으로 끝나면 병합 가능이 아니라고 적었다.
- 근거 표의 열은 축, 모델, effort, head SHA, P0, P1, P2다. P0·P1은 수정, 기각, 또는 소유자가 한계로 수용한다.
- `POLICY.md` §5·§10과 셋업 프롬프트 §5: 모델·effort·근거 표·P0·P1 처리는 위 절을 따른다. 예전의 되돌리기 쉬움 `low`·되돌리기 어려움 `high` 깊이 문장은 뺐다. 게이트 파일과 CI workflow는 안 바꿨다. 소비 프로젝트 재적용은 필요 없다.

## 2026-11-05 — 이벤트 정책 glob과 승인 댓글 재실행

과거 동작. 승인 댓글 재실행은 2026-11-06 「승인 댓글 편집 감지와 댓글 재실행을 줄인다」로 대체되었다. 이벤트 정책 glob 분류는 그 절의 기록이다.

- README의 이벤트 정책 판별은 `workflow_path` glob을 본다. `*`는 `/`를 넘지 않고 `**`는 넘는다. 그 파일에 맞는 glob이 `pull_request_target`만 허용하면 설치를 멈추고 POST하지 않는다. 패턴을 판별할 수 없어도 POST하지 않는다.
- `templates/review-status.yml`(과거 동작. 2026-11-06 「승인 댓글 편집 감지와 댓글 재실행을 줄인다」로 대체되었다): 그때 소유자 승인 댓글이 생기거나, 수정되거나, 삭제되면 그 head의 `pull_request_target` 실행을 `head_sha`로 찾았다. 목록의 `pull_requests`는 비어 있을 수 있어 그 배열의 head만 보면 이전 실행을 고를 수 있었다. 최근 50개로 끊지 않고 페이지당 100개, 최대 20페이지까지 찾았다. 실행을 끝까지 찾지 못하면 그 head에 실패하는 `Review status` 체크를 남겨 이전 성공이 최신 결과가 아니게 했다. `review/independent`와 `review/security`는 쓰지 않았다. 재실행 job은 기본 브랜치만 checkout하고 댓글 본문을 읽지 않았다. 권한에 `checks: write`가 더해졌다.
- `scripts/check_review_status.py`: `review/independent`와 `review/security`는 열린 PR의 현재 파일·커밋 목록이 아니라 그 head의 `compare`로 정한다. 이전 head는 커밋 시각과 force-push 시각으로 정렬해, 더 최근 failure를 건너뛰고 이전 success를 잇지 않는다. 같은 head의 status 목록은 가장 최근 상태가 앞선다. `uses:` 줄의 주 버전은 `# vN`·`@vN`만 보고, 해시 안의 숫자는 주 버전이 아니다. 버전 표식이 없는 pin은 주 버전을 모르는 것으로 본다.
- 댓글 재실행은 run의 `head_sha`만 골랐다. `pull_requests[].head.sha`는 현재 head로 바뀔 수 있어 이전 실행을 다시 돌리지 않았다. 그 재실행은 과거 동작이고, 2026-11-06 「승인 댓글 편집 감지와 댓글 재실행을 줄인다」로 대체되었다.
- 다시 적용할 프로젝트: Smallnext·BGLike·Runstir. 그때 workflow 템플릿을 `.github/workflows/review-status.yml`로 다시 복사했다. `scripts/check_review_status.py`, `scripts/test_review_status.py`, `scripts/rerun_review_status.py`를 `tools/apply_baseline.py`로 다시 복사했다. `scripts/rerun_review_status.py` 복사는 과거 동작이고, 2026-11-06 「승인 댓글 편집 감지와 댓글 재실행을 줄인다」로 대체되었다. 이벤트 정책 조회는 이 저장소 루트의 `tools/review_status_policy.py`를 썼다.

## 2026-11-04 — 동결 전 역할과 리뷰 기록

- `docs/development-workflow.md`: Grok Bot은 코드를 쓰지 않고 접수·추적·근거 확인·보고를 맡는다. 코드는 Claude Code(Mac)와 Cursor 클라우드 에이전트가 쓴다. 1인 프로필의 `review/independent`·`review/security`는 소유자가 남긴다. 서버 절차 전에는 Mac의 `gh`이고, 마치면 서버의 앱이다. 구현 에이전트와 `Review status` workflow는 쓰지 않는다. Cursor·Codex의 버그 찾기와 Security는 실제 PR로 확인하기 전까지 미확인이다. 템플릿과 검사기는 안 바뀌어 소비 프로젝트 재적용은 필요 없다.

## 2026-11-04 — Review status workflow 설치

- `.github/workflows/review-status.yml`: `templates/review-status.yml`을 그대로 복사했다. 다른 workflow와 합치지 않았고 이벤트를 더하지 않았다. 필수 체크 등록은 이 병합 뒤 소유자 승인으로 따로 한다. 템플릿은 안 바뀌어 소비 프로젝트 재적용은 필요 없다.

## 2026-11-04 — 되돌리기 어려움 승인 댓글을 검사기가 요구

과거 동작. `issue_comment`로 Review status를 다시 돌리던 절차는 2026-11-06 「승인 댓글 편집 감지와 댓글 재실행을 줄인다」로 대체되었다. SHA가 박힌 승인 댓글 요구는 남았다.

- `scripts/check_review_status.py`: 1인 프로필에서 §10 표의 게이트 경로를 바꾼 PR은 저장소 소유자의 이슈 댓글 `되돌리기 어려움 승인: <현재 head의 전체 SHA>`가 있어야 `Review status`가 통과한다. 실패 이름은 `review/owner-approval`이다. commit status로 올리지 않는다. 그 이름의 status가 있어도 댓글을 대신하지 않는다. 다른 SHA, 다른 작성자, 댓글 없음은 실패다. 새 head는 이전 댓글을 잇지 않는다. 되돌리기 쉬움은 통과했다. Dependabot 버전 전용 예외도 그때는 통과했다. 그 예외는 과거 동작이고, 2026-11-06 「Dependabot PR은 다른 PR과 같다」로 대체되었다. 파일 목록이 잘리면 댓글을 요구한다. 기준 브랜치 `AGENTS.md`의 한 줄이 `프로필: 팀`이면 팀 프로필이라 이 댓글을 요구하지 않는다. 그 줄을 더하거나 빼는 diff는 기준 브랜치가 아직 1인이면 댓글을 요구한다. 판정은 그 head의 `compare`로 하고, 열린 PR의 최신 파일 목록으로 하지 않는다. 주 버전과 표 밖의 되돌리기 어려움은 판정하지 않는다.
- `templates/review-status.yml`(과거 동작. 2026-11-06 「승인 댓글 편집 감지와 댓글 재실행을 줄인다」로 대체되었다): 그때 `issue_comment`의 생성·수정·삭제가 열린 PR의 댓글이고 작성자가 저장소 소유자이면, PR 코드를 checkout하지 않고 댓글 본문을 실행하지 않은 채 그 head의 `pull_request_target` 실행을 다시 돌렸다. 다른 사람의 댓글은 다시 돌리지 않았다. 같은 PR의 이전 재실행은 취소했다. `issue_comment` 실행은 PR 체크가 아니었다. 평가하는 job의 권한은 읽기였다. 재실행 job만 `actions: write`였다.
- 승인 댓글의 첫 줄은 CRLF여도 SHA를 읽는다.
- 과거 동작. 2026-11-06 「Dependabot PR은 다른 PR과 같다」로 대체되었다. 그때 게이트 경로의 Action 주 버전 변경과, `# vN`·`@vN`이 없어 주 번호를 모르는 `uses:`는 승인 댓글 예외가 아니었다. 리뷰 status 면제는 그때 그대로였다.
- 댓글 재실행은 `pull_request_target` 실행을 head SHA로 찾지 않았다. 그 이벤트는 실행을 base 커밋에 적었다. 실행의 `pull_requests`에서 PR 번호와 head SHA가 같은 것만 다시 돌렸다. 그 재실행은 과거 동작이고, 2026-11-06 「승인 댓글 편집 감지와 댓글 재실행을 줄인다」로 대체되었다.
- 1인 승인 댓글의 작성자는 저장소 `owner.login`이다. 재실행도 그때는 그 로그인만 보았다. 그 재실행은 과거 동작이고, 2026-11-06 「승인 댓글 편집 감지와 댓글 재실행을 줄인다」로 대체되었다. 조직 소유 저장소는 그 로그인이 조직 이름이라 1인 프로필을 쓰지 않고 팀 프로필을 쓴다.- 이벤트 정책 분류는 `workflow_path.exclude`에 `review-status.yml`이 있으면 그 정책을 대상으로 보지 않는다.
- `templates/review-status-policy.json`: 허용 이벤트는 `issue_comment`와 `pull_request_target`뿐이다.
- `POLICY.md` §9: 이 저장소도 `Review status`를 둔다. 예전 게이트 예외 문장은 뺐다. 순서는 이벤트 정책, workflow 파일, 그 다음 필수 체크 `Review status`다. 검사기를 바꾸는 PR은 정책·workflow 설치·필수 체크 등록을 하지 않는다.
- `POLICY.md` §10: 1인 승인 댓글은 필수 체크 `Review status`가 검사한다.
- 다시 적용할 프로젝트: Smallnext·BGLike·Runstir. `scripts/check_review_status.py`와 `scripts/test_review_status.py`를 `tools/apply_baseline.py`로 다시 복사한다. workflow 템플릿은 프로젝트의 `.github/workflows/review-status.yml`로 다시 복사한다. 그 파일을 병합하기 전에 이벤트 정책을 두 이벤트로 고친다. `pull_request_target`만 허용하는 정책이 있으면 PUT으로 고치고, 그 위에 POST로 더하지 않는다.

## 2026-11-04 — Issue #13 후속

- 주간 점검: 되돌리기 어려움 승인 댓글의 `updated_at`이 병합 시각보다 늦으면 병합 뒤에 고친 것으로 보고 승인으로 세지 않는다.
- 과거 동작. 2026-11-06 「Dependabot PR은 다른 PR과 같다」로 대체되었다. 그때 Dependabot 버전 전용 면제는 받은 커밋 수가 PR의 `commits`와 같을 때만 주었다. 250개 상한으로 목록이 잘리면 면제하지 않았다.
- 이어받기 테스트 가운데 상태·diff를 보려는 경우는 `force_pushes=[]`로 이력을 읽은 뒤 그 경로까지 간다.
- `POLICY.md` §5: 한 라운드는 작성자의 수정 push 한 번이고, 그 push의 CodeRabbit 증분 리뷰는 같은 라운드다. check가 SKIPPED이거나 `Review paused`이면 외부 리뷰는 끝나지 않아 `@coderabbitai full review`를 요청한다. 이미 리뷰된 PR들의 충돌만 main에서 푼 head는 소유자가 재리뷰 없이 승인할 수 있다. 상한에 닿으면 남은 CodeRabbit 지적은 답하고 해결한 뒤 후속 Issue에 적고, 병합 뒤 후속 PR에서 고친다. 상한을 넘는 라운드는 소유자만 승인한다.
- 다시 적용할 프로젝트: Smallnext·BGLike·Runstir. `scripts/check_review_status.py`와 `scripts/test_review_status.py`를 `tools/apply_baseline.py`로 다시 복사한다.

## 2026-11-04 — 문 판정, 이벤트 정책 절차, 리뷰 호출

- `POLICY.md` §10(새 절): 문 판정의 단일 기준. 판정 질문은 "망가지면 사용자가 무엇을 잃나"다. Matt `/pr`의 되돌리기 비용 문장은 원문 그대로 두고(vendor에는 `matt-code-review`만 있다) Door 값만 이 절을 따른다. CI workflow와 리뷰 게이트 파일(`.github/workflows/**`, `templates/review-status.yml`, `scripts/check_review_status.py`, `templates/review-status-policy.json`, repository-settings)은 되돌리기 어려움이다. Security 리뷰만으로 병합하지 않는다. Dependabot의 버전·해시·Action SHA만 바꾼 PR은 그때 그 경로여도 사람 되돌리기 어려움 승인에서 뺐다(§5와 같은 버전 전용 조건). 주 버전 변경(버전 주석·태그의 첫 숫자, 모르면 되돌리기 어려움)과 `scripts/check_review_status.py` 변경(작성자 무관)은 그때 그 승인에서 빼지 않았다. 그 면제는 과거 동작이고, 2026-11-06 「Dependabot PR은 다른 PR과 같다」로 대체되었다. 1인 프로필의 되돌리기 어려움 승인은 저장소 소유자의 PR 댓글 `되돌리기 어려움 승인: <head sha>`로 남긴 뒤에만 `--match-head-commit`으로 병합한다. auto-merge는 §9 ②를 마친 프로젝트의 되돌리기 쉬움 가운데 외부 리뷰 대상이 아닌 PR만 예약한다.
- `POLICY.md` §5: 병합 전에 달린 CodeRabbit 스레드는 PR 종류와 관계없이 답하고 해결한다. 병합 뒤에 달린 지적은 후속 PR로 처리한다. 외부 리뷰 대상 PR은 auto-merge를 예약하지 않는다. `interrogate` 같은 추가 의견은 외부 리뷰로 세지 않는다. Standards·Spec은 `/matt-code-review`만 부르고, `/implement` 안의 `code-review`는 `review/independent`로 세지 않는다.
- `POLICY.md` §9: 이 저장소는 `Review status` 게이트의 예외다. 검사기 원본을 바꾸는 PR은 §10의 되돌리기 어려움으로 사람이 최종 head를 승인한다. 소비 프로젝트의 ①②는 그대로다.
- README 새 프로젝트 절차: 공개 저장소는 `review-status.yml`을 병합하기 전에 `templates/review-status-policy.json`으로 Actions 이벤트 정책을 만든다. 정책 조회가 실패하면 만들지 않는다. 주간 점검의 1인 되돌리기 어려움 승인 댓글은 모든 페이지를 보고, 팀 프로필의 리뷰도 모든 페이지를 본다. 병합 시각보다 늦은 승인 댓글·리뷰는 세지 않는다.
- `docs/development-workflow.md`: `disable-model-invocation: true`인 Matt 스킬은 사용자가 실행한다. PR 담당자(Dependabot 주간 처리, CodeRabbit 대기, 병합 뒤 후속)를 정의했다. 필수 리뷰는 Claude Code에서 돌린다.
- 셋업 프롬프트 §5: 최종 전체 diff 리뷰를 건너뛰는 조건은 전체 diff로 리뷰한 SHA가 현재 head와 같을 때뿐이다. 바뀐 diff만 본 SHA는 그 조건에 들어가지 않는다. `/matt-code-review`에는 고정점(PR base SHA), spec 위치(Issue 또는 없음), 기준 브랜치의 표준 문서 경로를 넘긴다.
- 문서만 바뀌어 소비 프로젝트 재적용은 필요 없다.

## 2026-11-04 — 같은 diff의 리뷰 status 이어받기

- `scripts/check_review_status.py`: 새 head에 그 context가 없고 diff identity가 이미 `success`인 status와 같으면 `Review status`가 그 status로 통과한다. 기준 브랜치 갱신만이 아니다. 커밋 목록이나 force-push 이력을 읽지 못하면 이어받지 않는다. 받은 커밋 수가 PR의 `commits`보다 적거나, force-push 이전 SHA가 없으면 이어받지 않는다. identity는 경로, 파일 모드, rename·copy, 추가·삭제한 줄, 바이너리 blob SHA다. 줄 번호는 보지 않는다. hunk의 주변 줄은 #34에서부터 해시에 넣는다. 그 줄이 달라지면 이어받지 않는다. 공백이 다르거나 diff를 읽지 못하면 이어받지 않는다. 이 head에 `failure`가 있으면 이전 성공으로 덮지 않는다. rebase로 커밋 목록에서 빠진 SHA는 pull request의 force-push 이전 head에서 찾는다. `git patch-id`는 공백을 지워서 쓰지 않았다. 이어받기는 절차 기록이고 보안 경계가 아니다. 이 검사기는 주 버전과 문 유형을 판정하지 않는다.
- 과거 동작. 2026-11-06 「Dependabot PR은 다른 PR과 같다」로 대체되었다. 그때 Dependabot이 버전·해시·Action SHA만 바꾼 PR은 `review/independent`도 면제했다. 조건은 기존 `review/security` 예외와 같았다. 이 면제는 리뷰 status(`review/security`, `review/independent`)와 외부 리뷰를 뺐다. 그 head에 리뷰 status가 있으면 `success`여야 했다. 사람 되돌리기 어려움 승인은 빼지 않았다. 주 버전 변경과 `scripts/check_review_status.py` 변경은 그 승인에서 빼지 않았다.
- `POLICY.md` §8·`prompts/weekly-check.md`: 공개 저장소에 `review-status.yml`이 있으면 Actions 이벤트 정책이 그 파일의 `pull_request_target`만 허용하는지 본다.
- 다시 적용할 프로젝트: Smallnext·BGLike·Runstir. `tools/apply_baseline.py`로 `scripts/check_review_status.py`와 `scripts/test_review_status.py`를 다시 복사한다. 각 프로젝트의 ②(필수 체크) 전에는 이 검사기가 기본 브랜치에 있어야 이어받기가 동작한다.

## 2026-11-04 — 1인·팀 프로필, 리뷰 기록, 도구 층

- `POLICY.md` §9(새 절): 1인(기본)과 팀(2~6명) 프로필. 팀 프로필은 GitHub 필수 승인 1명·코드 소유자 리뷰·마지막 push 승인을 켜고 `templates/CODEOWNERS`로 신뢰 경계 경로의 소유자를 둔다. PR 책임자(에이전트를 시킨 사람 포함)와 에이전트·봇의 승인은 세지 않는다. 에이전트는 PR을 승인하지 않는다. 가벼운 승인 경로는 두지 않는다. 되돌리기 쉬움은 승인·CI·리뷰 뒤 에이전트가, 되돌리기 어려움은 승인한 사람이나 PR 책임자가 병합한다. 조직 소유 저장소의 ruleset(조직 ruleset은 Team·Enterprise)·merge queue·우회 목록 지원 범위와 비공개 팀 저장소의 CodeRabbit 비용을 공식 문서로 확인해 적었다. 프로젝트는 `AGENTS.md`에 프로필을 한 줄로 적는다.
- `POLICY.md` §5: 리뷰 표에 "언제"·외부 리뷰·정기 Security 감사(Cloudflare `security-audit`)·회고를 넣었다. 버그 찾기는 코드가 바뀐 PR에만 한다. 문서·신뢰 경계가 아닌 설정만 바꾸는 되돌리기 쉬움은 Standards·Spec 하나만 받는다(가벼운 경로). 역할마다 결정적 검사와 LLM 리뷰를 하나씩만 둔다. 공통 신뢰 경계 경로에 `.github/actions/**`, `.github/dependabot.yml`, `.github/dependabot.yaml`, `.github/CODEOWNERS`, `.github/repo-baseline.json`, `.github/trust-boundary-paths`, `scripts/check_*.py`, `.claude/settings.json`, `.claude/hooks/**`, `.claude/agents/**`, `.claude/commands/**`, `.agents/skills/**`, `.claude/skills/**`, `.mcp.json`을 더했다. `tools/test_distribution.py`가 POLICY·CODEOWNERS·검사기의 목록이 같은지 본다. 앞으로 baseline을 다시 적용하는 PR은 Security 리뷰 대상이다.
- 리뷰 기록(두 프로필): 리뷰를 마치면 리뷰한 head SHA에 commit status(`review/independent`, Security를 실행했으면 `review/security`)를 남긴다. 새 `Review status` CI job(`scripts/check_review_status.py`, `templates/review-status.yml`)이 바뀐 파일 경로로 필요한 status를 정하고 그 head에 없으면 실패한다. `pull_request_target`으로 기본 브랜치의 코드만 실행하므로(PR 대상이 다른 브랜치여도 같다) PR이 이 job의 코드를 고칠 수 없다. 같은 이름의 job을 더하는 경우는 Security 리뷰에서 본다. 내용 기준은 리뷰어 판단으로 남긴다. Dependabot 예외는 그때 `POLICY.md` §5대로 적용했다. 이름에 붙은 숫자는 버전으로 보지 않아, 패키지 이름을 바꾸는 줄과 npm·yarn lockfile의 `resolved` URL은 Security 리뷰를 받았다. 그 예외는 과거 동작이고, 2026-11-06 「Dependabot PR은 다른 PR과 같다」로 대체되었다. 두 단계로 도입한다. ① job을 두고 에이전트가 status를 남기기 시작하고 ② 프로젝트마다 승인받아 필수 체크로 등록한다. **1인 프로필의 기본값이 바뀐다**: ② 이후 필수 체크가 하나(`Review status`) 더 생긴다. 같은 계정의 status는 사람과 에이전트를 구분하지 못하는 절차 기록이다. CodeRabbit은 외부 리뷰 대상 PR에서만 기다린다.
- GitHub auto-merge: ②를 마친 프로젝트의 되돌리기 쉬움에만 쓴다. revert 없는 기간은 조건으로 두지 않는다. 주간 점검의 hotfix 비율은 참고용이다.
- 셋업 프롬프트 §5: 마지막으로 리뷰한 head SHA가 그대로면 최종 전체 diff 리뷰를 다시 하지 않는다. 기준 브랜치 갱신만으로 head가 바뀌면 그 뒤 바뀐 diff만 재리뷰하고 새 SHA에 status를 남긴다.
- 도구 층(`POLICY.md` §7, `docs/development-workflow.md`): 저장소·계정·로컬 층으로 나눴다. 리뷰 관문 스킬은 저장소에 커밋한다. `vendor/mattpocock-skills/matt-code-review`(Matt Pocock `code-review` v1.3.2, MIT, 이름만 `matt-code-review`로 바꿈. 내장 `/code-review`와 겹치지 않게)를 manifest대로 `.agents/skills/`와 `.claude/skills/`에 복사한다. `@AGENTS.md` 한 줄만 있는 `CLAUDE.md`를 허용한다(내용 복제는 계속 금지).
- `templates/claude-settings.json`(두 프로필 공통): `.env` 읽기를 막고, 로컬 편의로 Matt Pocock 플러그인을 태그로 고정해 켠다. 설정 파일은 지침 파일이 아니다.
- `scripts/check_repo_baseline.py`: 커밋한 `.mcp.json`의 `env`·`headers` 값은 `${VAR}` 참조만 허용한다(앞의 `Bearer `·`Basic `·`Token `은 허용). `${VAR:-기본값}`과 고정값은 실패한다. 비밀이 아닌 고정값도 환경 변수로 옮긴다.
- `POLICY.md` §8·주간 점검: `Review status`가 성공하지 않은 병합 PR, 정기 감사 지연, 마켓플레이스 태그가 가리키는 commit의 변경을 표시한다.
- 다시 적용할 프로젝트: Smallnext·BGLike·Runstir.
  1. `.github/repo-baseline.json`에 `templates/repo-baseline.json`의 `matt-code-review` 여섯 항목과 `scripts/check_review_status.py`·`scripts/test_review_status.py`를 더하고 `tools/apply_baseline.py`로 다시 적용한다.
  2. `.claude/settings.json`을 `templates/claude-settings.json`으로 둔다. 기존 파일이 있으면 합친다. `.mcp.json`이 있으면 `env`·`headers` 값을 기본값 없는 `${VAR}` 참조로 바꾼다(앞의 `Bearer ` 등은 허용).
  3. `AGENTS.md`에 프로필 한 줄(1인)을 적는다. `@AGENTS.md` 한 줄만 있는 `CLAUDE.md`(Smallnext·BGLike)는 그대로 둔다. 프로젝트 신뢰 경계 경로를 `.github/trust-boundary-paths`에 적는다. 기존 프로젝트 리뷰 문서의 경로를 옮기고 문서에서 연결한다.
  4. 공개 저장소는 먼저 `templates/review-status-policy.json`으로 Actions 이벤트 정책을 만든다. 없으면 2026-12-02부터 job이 막힌다(`POLICY.md` §9). 그 뒤 `templates/review-status.yml`을 별도 파일 `.github/workflows/review-status.yml`로 두어 병합하고(기본 브랜치에 있어야 돈다. 다른 이벤트를 더하면 정책이 막는다) 에이전트가 리뷰 status를 남기기 시작한다.
  5. 실제 PR에서 status 없이 job의 실패를, status를 남기고 다시 돌려 성공을 확인한 뒤 프로젝트마다 승인받아 `.github/repository-settings.json`의 `checks`에 `Review status`(`app_id: 15368`)를 더하고 `tools/apply_github_settings.py`로 등록한다. 그 뒤부터 되돌리기 쉬움에 auto-merge를 쓸 수 있다.

## 2026-11-03 — 리뷰 수렴과 위험 판정

- 근거: [How the Claude Code team does code review](https://claude.dev/blog/solving-code-review-at-anthropic/)(2026-10-15).
- 셋업 프롬프트 §5: 수정 뒤의 재리뷰 라운드는 바뀐 diff만 보고(병합 전 최종 head 전체 리뷰는 유지), 지적은 결함 유형으로 남기고 반복하지 않는다. 스타일만의 지적은 버리고, P0/P1/P2에 더해 Pre-existing을 표시한다. 라운드 상한(`POLICY.md` §5, 3)을 넘으면 접근 방식을 다시 검토해 사용자에게 보고한다.
- 셋업 프롬프트 §6: 리뷰 근거는 `file:line`, 보고는 지적 개수로 시작한다. 리뷰 문서에 영역별 실패 정의·P2 상한·건너뛸 경로·사용자가 승인한 "배운 규칙"을 둔다.
- 셋업 프롬프트 §10·§5, `POLICY.md` §5, README 요청문: 위험 등급은 변경 내용으로 정하고 판정 질문("망가지면 사용자가 무엇을 잃나")을 적었다. 위험 변경에도 외부 리뷰를 받는다. 같은 모델의 별도 컨텍스트 리뷰는 외부 리뷰로 세지 않는다.
- `POLICY.md` §5·셋업 프롬프트 §5: 리뷰는 Standards·Spec·버그 찾기를 실행하고 신뢰 경계 변경에 Security를 더한다. 도구는 POLICY §5 표에 둔다. Standards·Spec은 Matt Pocock `code-review`, 버그 찾기는 내장 `/code-review`(되돌리기 쉬움 `low`, 되돌리기 어려움·위험 변경 `high`), Security는 내장 `/security-review`(열린 지적이 있으면 병합하지 않음).
- `POLICY.md` §5: 신뢰 경계 변경을 한 곳에 정의했다. 작성자 판단이 아니라 diff의 공통 경로·프로젝트 경로·내용 기준으로 정하고, 애매하면 신뢰 경계로 본다. POLICY와 셋업 프롬프트에서 서로 달랐던 목록을 이 정의로 바꿨다. PR 본문 Merge Danger에 걸린 기준을 적는다. Dependabot이 버전·해시·Action SHA만 바꾼 PR은 그때 경로 기준의 유일한 예외로 신뢰 경계로 보지 않았다(다른 줄이 바뀌거나 다른 사람이 커밋을 더하면 예외가 아니었다). 그 예외는 과거 동작이고, 2026-11-06 「Dependabot PR은 다른 PR과 같다」로 대체되었다. 신뢰 경계 변경은 Security 리뷰 대상일 뿐이고, 사람 승인이 필요한 위험 변경은 셋업 프롬프트 §10으로 따로 판정한다(§10의 "신뢰 경계"는 "권한을 넓히는 변경"으로 좁혔다).
- 문서만 바뀌어 소비 프로젝트 재적용은 필요 없다.

## 2026-11-03 — 개선 반영 순서와 pstack 배치

- `POLICY.md` §6: 개선은 코드 구조·타입 → 결정적 검사 → 지침 → 사람 리뷰 순으로 가장 앞 단계에 반영한다. revert·hotfix PR 본문에 원래 PR과 놓친 단계를 적고 회고 후보로 둔다.
- `POLICY.md` §7·`docs/development-workflow.md`: pstack 스킬을 제안할 단계(`create-verification-skill`, `blast-radius`, `interrogate`, `correct`)와 쓰지 않을 중복을 적었다. 검증 스킬은 `AGENTS.md`만 쓰는 규칙의 유일한 예외로 셋업 프롬프트 §3에 적었다.
- 문서만 바뀌어 소비 프로젝트 재적용은 필요 없다.

## 2026-11-03 — 주간 점검

- `POLICY.md` §8·`prompts/weekly-check.md`: 선택적 주간 읽기 전용 점검을 추가했다. 기간과 기준값은 §8 표에 둔다.
- 문서만 바뀌어 소비 프로젝트 재적용은 필요 없다.

## 2026-10-27 — GitHub 설정 적용 도구

- `tools/apply_github_settings.py`를 추가했다. 프로젝트의 `.github/repository-settings.json`(감사 도구와 같은 기준선)을 읽어 다른 항목만 쓴다. 기본 실행은 현재 값과 기준값, 쓰기 요청을 출력만 하고, `--apply`는 쓴 뒤 다시 감사한다. 공개 여부·ruleset·workflow 파일과, 기준선 밖 설정이 켜진 브랜치 보호는 쓰지 않는다. 기준선 오류와 404 외의 조회 오류는 쓰기 전에 멈춘다.
- 새 프로젝트의 기준선 시작점 `templates/repository-settings.json`(채울 값은 `REPLACE`로 표시)과 이 저장소 자신의 `.github/repository-settings.json`을 두었다. 정책 값이 서로 어긋나면 `tools` 테스트가 실패한다.
- GitHub 설정 프롬프트 §3 표에 기준선이 이미 쓰던 값(기존 승인 무효화 On, 코드 소유자 리뷰 Off, 마지막 push 승인 Off, 브랜치 잠금 Off, Release 불변성 On)을 적었다.
- `scripts/check_github_settings.py`의 schema·저장소 이름·브랜치 검사를 `validate_target()`으로 분리했다. 동작은 같아 소비 프로젝트 재적용은 필요 없다. 다음에 다시 맞출 때 함께 복사된다.

## 2026-10-27 — Matt Pocock 스킬 사용법을 다시 적지 않음

- 개발 절차 문서·PR/CI 셋업 프롬프트·POLICY·README에서 스킬의 단계(셋업 세부, 작업 크기별 진입 표, 명세→티켓→구현, 스킬 선택, retro 단계)를 옮겨 적던 부분을 뺐다. 옮겨 적은 내용이 원문과 어긋나 있었다(원문은 변경마다 grilling을 권하지만 문서는 불확실할 때만으로 바꿔 적음). 스킬은 설치된 원문대로 쓰고, 시작점은 `/ask-matt`에 묻는다.
- 남긴 것은 스킬이 정하지 않는 이 기준의 선택이다. `AGENTS.md`만 쓰기(셋업 스킬 전에 `CLAUDE.md`를 옮김), 모든 변경은 PR·필수 CI·위험별 병합(셋업 프롬프트 §10), 리뷰 정책(§5), 회고 정책(§6).
- README의 재적용 순서를 고쳤다. squash 병합과 병합 후 브랜치 삭제를 쓰므로 PR을 병합한 뒤 최신 `main`에서 적용한다.
- 공통 검사기·템플릿은 바뀌지 않아 소비 프로젝트 재적용은 필요 없다.
- 권한·Secret·workflow·저장소 설정·dependency 정책 PR의 추가 리뷰를 "다른 모델"에서 "작성자 세션 밖의 외부 리뷰"로 바꾸고, 공개 저장소는 CodeRabbit 무료 플랜으로 충족한다고 적었다. CodeRabbit은 참고용이며 필수 체크·자동 수정은 쓰지 않는다. GitHub 설정 프롬프트 §7도 CodeRabbit을 정리 대상에서 뺐다.
- CodeRabbit 리뷰 반영: 라벨 문서는 `triage`가 설치됐을 때만 완료 조건에 넣는다(셋업 스킬이 그때만 라벨 단계를 진행). Claude Code 플러그인에서는 `/mattpocock-skills:<이름>`처럼 플러그인 이름을 붙여 부른다.

## 2026-10-27 — 이 저장소에도 Dependabot 버전 업데이트 적용

- `.github/dependabot.yml`을 두었다. 생태계가 GitHub Actions뿐이라 `templates/dependabot.yml`을 그대로 쓴다. SHA로 고정한 `check.yml`의 action은 보안 알림이 생기지 않으므로 이 정기 업데이트로만 갱신된다(`POLICY.md` §2).
- 이 저장소에는 manifest가 없어 `apply_baseline.py`로 생성하지 않는다. 첫 줄을 사본이라는 설명으로 바꾸고, 나머지가 템플릿과 어긋나면 `tools` 테스트가 실패하게 했다.

## 2026-10-27 — 지침 파일을 AGENTS.md로 통일

- 초기 설정 6단계가 `## Agent skills` 블록을 `AGENTS.md`에만 둔다. 파일이 없으면 만든다. PR/CI 셋업 프롬프트 §3도 canonical 파일 선택 대신 `AGENTS.md`로 정리하게 맞췄다.
- 공통 검사기·템플릿은 바뀌지 않아 소비 프로젝트 재적용은 필요 없다. 기존 프로젝트의 `CLAUDE.md`는 다시 맞출 때 고유 규칙을 `AGENTS.md`로 옮기고 지운다.

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
