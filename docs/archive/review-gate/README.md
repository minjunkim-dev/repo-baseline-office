# review-gate 프로필 (보관)

보관 문서다. 2026-11에 보관했다. 기본 GitHub 설정(workflow 토큰 읽기 전용, 클라우드 에이전트에 병합 권한 없음)이 이미 막는 것만 막고, 같은 OS 사용자로 도는 로컬 에이전트는 막지 못했다. 실제 App 흐름은 #66 이동 뒤 검증하지 않았다. `pr_author.py`는 `profiles/pr-conventions/`로 옮겼다. 아래 경로는 보관 전 기준이다이고, 이 폴더의 코드는 `pr_author.py`가 없어 그대로는 실행되지 않는다.

선택 프로필이다. 기본값은 브랜치 보호 + 필수 CI + 사람 병합이다(`docs/archive/redesign-2026-11.md` D2). 이 폴더는 그 위에 "승인 위조까지 막는" 게이트를 더한다.

## 언제 켜는가

- 에이전트나 workflow 토큰이 병합 조건을 스스로 채울 수 있다는 것이 걱정될 때. 하네스 거부 규칙은 습관이지 보안 경계가 아니다.
- 1인 레포에서 workflow·설정·게이트 파일을 바꾸는 PR에 소유자의 SHA 승인 댓글을 기계적으로 요구하고 싶을 때.
- 소유자 Mac에서 GitHub App(Commit statuses 쓰기) 하나와 Keychain PEM을 관리할 수 있을 때. 못 하면 켜지 않는다.

## 켜는 법

1. 소비 레포에 복사한다: `check_review_status.py`, `pr_author.py`, `test_review_status.py` → `scripts/`. `review-status.yml` → `.github/workflows/`.
2. 전용 GitHub App(권한: Commit statuses 쓰기, Metadata 읽기)을 만들고(옛 상세 절차: [docs/archive/review-gate-app-2026.md](../review-gate-app-2026.md)), 정수 `app_id`를 `.github/repository-settings.json`의 필수 체크 `review/gate`에 넣는다. 소유자 기기에서 `python3 <repo-baseline>/tools/apply_github_settings.py <project> --apply`로 적용한다.
3. 조직·엔터프라이즈 Actions 이벤트 정책이 있으면 `review-status-policy.json`과 `review_status_policy.py`로 `pull_request_target`이 허용되는지 확인한다.
4. 병합은 소유자 Mac의 이 저장소 깨끗한 `main`에서 `python3 -I profiles/review-gate/post_review_gate.py --repo <owner/name> --pr <N> --sha <head> --merge`로만 한다.

## 검사기가 보는 것

- PR 본문의 `Author: <도구> / <모델>` 한 줄. 도구 이름은 아무것이나 된다. 사람은 `사람 / 없음`.
- 마지막 `## Review` 섹션의 세 칸: `리뷰어`, `고친 것`, `남은 지적`(`templates/core/pull_request_template.md`). `리뷰어`가 비었거나 `미실행`이면 실패한다. `남은 지적`에 지적이 남아 있어도 실패하지 않는다.
- 1인 프로필에서 게이트 경로(`check_review_status.py`의 `ONE_WAY_PATHS`)를 바꾸면 소유자 댓글 `되돌리기 어려움 승인: <전체 head SHA>`.
- base가 기본 브랜치인지.

## 옮기면서 뺀 것 (2026-11, #66)

- 모델 패밀리 판정, 같은 패밀리 예외 블록, Codex·ChatGPT 이름 거부, 작성 도구 허용 목록. 다른 패밀리 리뷰는 권장이다(D3).
- 4축 근거 표(axis·model·effort·head SHA·P0·P1·P2). 대신 위 세 칸을 본다.
- 리뷰 기록과 head SHA의 연결. 이제 본문의 리뷰 기록은 특정 head를 가리키지 않는다. SHA에 묶이는 것은 소유자 승인 댓글뿐이다.
- 신뢰 경계 경로에서 Security 축을 요구하던 규칙. 소비 레포의 `.github/trust-boundary-paths`는 더 읽지 않는다.
