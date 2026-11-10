# review-gate 옛 운영 문서 (2026-11 재설계 전, 보관용)

현재 절차가 아니다. 섹션 번호와 경로는 옛 구조 기준이다. 현행은 [profiles/review-gate/README.md](../../profiles/review-gate/README.md).

아래는 옮기기 전의 운영 문서다. "근거 표"는 이제 위의 `## Review` 세 칸을 뜻한다. `tools/`·`scripts/` 경로는 소비 레포 배치다. 이 저장소에서는 `profiles/review-gate/`에 있다.

---

## review/gate 전용 GitHub App

이 문서는 `POLICY.md` §5의 승인 경계를 Mac에서 만드는 절차다. 이 저장소의 PR은 설계와 도구와 기대값만 둔다. 앱을 만들지 않고, branch protection을 쓰지 않고, status를 올리지 않고, 병합하지 않는다.

## 2026-11-06 합의와 이 문서의 역할

- 승인 경계는 항상 **commit status** `review/gate`이고, 브랜치 보호에 **전용 App의 정수 `app_id`로 고정**한다. (`github-actions` 15368으로는 그 필수 context를 충족하지 못하게 한다.)
- **1인·소규모 팀의 권장 일상 경로**는 **개발자 `gh`(읽기·병합) + Keychain의 앱 PEM(전용 앱 `review/gate` 서명) + 기본 브랜치 checkout의 `post_review_gate.py --merge`**다. 이 저장소의 핀은 `app_id` **5641238**이다. 읽기용 `GH_TOKEN`은 그 프로세스 안에서만 `gh auth token`으로 채운다. 스크립트는 `gh auth token`을 호출하지 않는다. 별도 읽기 PAT, `reviewgate` OS 계정, 봉인 트리(seal), 해시, sudoers, `git archive`는 **권장 일상 경로가 아니다**. 앱 설치 토큰은 status POST에만 쓰고 `gh`에 넘기지 않는다.
- 2026-11-06 문서 합의 당시에는 이 파일을 문서만 고쳤다. 그 뒤 검사기는 diff identity로 status를 이어받지 않게 됐고, 증거-in-gate로 `review/independent`·`review/security`를 게이트 조건에서 뺐다. `REPLACE` 자리표시자는 다른 저장소가 앱 ID를 채우기 전에만 남는다.
- repo-baseline의 기대값 `checks`에서 `Review status`(`app_id` 15368)를 뺐다. 남은 필수 체크는 Baseline checks 둘(`app_id` 15368)과 `review/gate`(`app_id` 5641238)다. workflow와 검사기는 남긴다. 그 변경은 증거-in-gate를 넣지 않았다. 그 뒤 검사기는 diff identity로 status를 이어받지 않게 됐고, 지금은 `review/independent`·`review/security`를 읽지 않는다. 근거 표와 승인 댓글로 판정한 뒤 `review/gate`만 올린다. Dependabot 버전 전용 예외는 없다. Dependabot PR도 근거 표가 필요하고, 1인 프로필에서 게이트 경로를 바꾸면 승인 댓글이 필요하다. 보호 적용은 병합 뒤 소유자가 한다. 이 문서는 필수 체크 목록을 바꾸지 않는다.

## 무엇을 고정하나

승인 경계는 commit status `review/gate`다. 체크 run이 아니다.

카나리 E(2026-11-06, PR #39)는 필수 체크 `Review status`가 `app_id` 15368일 때, `checks: write`인 workflow의 `GITHUB_TOKEN`이 같은 이름의 체크 run을 success로 올리면 그 run도 앱 15368이고 최신 conclusion이 필수 조건을 통과시킨다는 것을 보였다. Actions 잡과 위조 run이 같은 종류의 객체이고 같은 앱이다.

전용 앱은 Commit statuses 쓰기와 Metadata 읽기만 가진다. Checks 권한이 없으므로 체크 run을 만들지 못한다. 브랜치 보호는 `{"context": "review/gate", "app_id": <그 앱의 정수 ID>}`로 고정한다. workflow 토큰이 같은 context로 commit status나 체크 run을 올려도 그 객체의 앱은 15368이다. 게시는 201일 수 있다. 그 객체는 필수 조건이 아니다.

`Review status` workflow는 증거 검사로 남긴다. 근거 표와, 필요할 때의 승인 댓글을 읽고 없으면 실패한다. `review/independent`와 `review/security`는 읽지 않는다. `review/gate`를 쓰지 않는다. 필수 목록에는 두지 않는다. 그 초록색은 승인 경계가 아니다. 15368은 같은 이름의 체크 run을 위조할 수 있다. 스크립트는 그 체크의 conclusion을 읽지 않는다.

`strict`는 true다. 새 head에는 `review/gate`가 없다. 인자 SHA가 열린 PR의 현재 head와 다르면 스크립트는 올리지 않는다. 조회 실패, 키가 0600 일반 파일이 아님, `GITHUB_ACTIONS`가 설정됨은 아무것도 올리지 않는다. 근거가 실패하면 그 SHA에 `failure`를 올려 이 앱이 이전에 올린 success를 지운다. success는 `--merge`만 올린다. `--merge`가 없는 실행은 근거가 통과하면 `pending`을 올려 이전 success를 지우고, 실패하면 `failure`를 올린다. `--merge`는 다른 필수 체크와 리뷰 스레드를 본 뒤에만 success를 올리고, 파싱된 작성 기록·표·승인 댓글이 그대로인지 다시 읽은 다음 개발자 `gh`로 squash 병합한다. description의 digest는 그 스냅샷의 표식이다. GitHub는 병합 때 digest를 다시 검사하지 않는다. 검사·게시·재검사·병합은 한 트랜잭션이 아니다. 본문 편집이 재검사와 겹치거나, success 뒤에 프로세스가 죽으면 success가 남을 수 있다. 그 경우 `--merge` 없이 다시 실행해 pending 또는 failure로 지운다. 사람이 `gh pr merge`로 직접 병합하지 않는다. auto-merge는 예약하지 않는다. 절대적인 신선도 보장이 아니다. 본문 편집을 받는 새 webhook이나 앱 권한은 두지 않는다. 닫힌 PR, head 불일치, 기본 브랜치가 아닌 base에는 올리지 않는다.

Dependabot PR은 다른 PR과 같은 근거다. 브랜치 보호는 작성자별로 빼지 못하므로 `review/gate`는 그 PR에도 필요하다. 버전·해시·Action SHA만 바꾼 diff여도 스크립트는 `--merge`에서만, 근거 표가 있을 때 success를 올린다. 1인 프로필에서 게이트 경로면 소유자 SHA 댓글도 있어야 한다. 팀 프로필은 그 댓글을 요구하지 않고 `POLICY.md` §9의 사람 승인이다. `--merge`가 없으면 success를 올리지 않는다. `review/independent`와 `review/security`는 없어도 success다. 자동 성공 경로는 없다. 2026-11-04의 pin 전용 면제(주 버전만 승인, `uses:` pin 모양, web-flow 커밋터, 숨은 줄바꿈)는 쓰지 않는다.

검사기와 이 게이트는 `review/independent`와 `review/security`를 읽지 않는다. 없어도, failure여도, `[bot]`이 올렸어도 게이트는 그 이유로 실패하지 않는다. 앱은 `review/gate`만 올린다. 승인 댓글의 작성자가 `[bot]`이면 그 댓글은 승인이 아니다.

합의(증거-in-gate, 2026-11-06 Adopt-with-tweak): 게이트는 별도 필수 `review/independent`·`review/security` status에 의존하지 않는다. PR 본문의 리뷰 기록(`## Review` 세 칸)과, 필요할 때의 하드도어 승인 댓글로 판정한 뒤 `review/gate`만 올린다. 그 둘의 status는 참고로 남길 수 있다.

## 권장: 개발자 gh(읽기·병합) + Keychain(앱 PEM) + 기본 브랜치 checkout

1인·소규모 팀에서는 **에이전트가 읽을 수 있는 홈에 0600 PEM을 두지 않는다.** 앱 private key는 **개발자 macOS Keychain**에 넣고, 게이트를 올릴 때만 짧은 생명의 임시 파일로 꺼낸다. Keychain은 PEM을 **디스크에 남기지 않게** 하려는 저장소일 뿐이며, 기본 설정만으로 Touch ID나 하드웨어 보안 모듈 수준을 보장하지 않는다. `security`로 항목을 꺼낼 때(특히 `-w`) 자격·프롬프트 정책은 환경·항목 종류에 따라 다르다.

**같은 macOS 사용자(같은 UID)에서 돌아가는 에이전트는 개발자 세션과 격리되지 않는다.** 예전 레거시 경로의 별도 `reviewgate` OS 계정·sudoers 분리와 달리, 이 권장 경로는 **프로세스·권한 분리가 없다**. 에이전트가 해당 사용자로 실행 중이면 Keychain 항목을 읽거나 임시 PEM을 스캔할 수 있는지(항목 ACL·파일 타이밍)를 별도로 가정하지 않는다.

### 무엇을 쓰나 (현재 코드와 맞춤)

`profiles/review-gate/post_review_gate.py`는 환경 변수 `GH_TOKEN`이 비어 있으면 `review gate refused: GH_TOKEN must be set for reads`로 끝난다. 권장 일상 경로는 그 값을 **이 프로세스 안에서만** `gh auth token`으로 채운다. 스크립트는 `gh auth token`을 호출하지 않고, 토큰이 다른 계정의 것인지 검사하지 않는다. 개발자 토큰은 읽기 전용으로 좁혀져 있지 않다. 그 한계는 남는다. 별도 읽기 PAT를 발급하는 절차는 권장 경로에 없다.

같은 `GH_TOKEN`으로 두 종류의 읽기를 한다.

- **REST GET** (`Reader`): pull request, diff, 커밋, 승인 댓글의 `created_at`·`updated_at`. 승인 댓글의 편집 여부는 GraphQL `lastEditedAt`을 보지 않고 `updated_at`이 `created_at`과 같은지로만 본다.
- **GraphQL CheckRun** (`fetch_readiness`, `POST /graphql`): `--merge`와 `--merge`인 `--dry-run`의 준비 상태. 필수 체크, 리뷰 스레드, `reviewDecision`이다. 승인 댓글 편집 판정은 이 쿼리가 아니다.

`gh` 자식(로그인 확인과 `gh pr merge`)에는 `GH_TOKEN`을 넘기지 않는다. 병합은 개발자 `gh` 로그인이다. 앱 설치 토큰은 status POST에만 쓰고 `gh`에 넘기지 않는다. 설치 엔드포인트는 앱 JWT(PEM)다.

- **근거 표**: PR 본문이다. 두 프로필 모두 필요하다.
- **사람 승인**: 1인 프로필에서 게이트 경로를 바꾸면 소유자 댓글 `되돌리기 어려움 승인: <전체 SHA>`가 더 필요하다. 팀 프로필은 그 댓글을 요구하지 않고 `POLICY.md` §9의 사람 승인이다. `review/independent`와 `review/security`를 참고로 남길 때만 개발자 `gh`로 status를 올린다. 게이트 조건이 아니다.
- **쓰기(`review/gate` POST)**: Keychain에서 꺼낸 PEM 경로를 `REVIEW_GATE_APP_KEY`에 둔다. `REVIEW_GATE_APP_ID`는 전용 앱의 양의 정수다. 이 저장소의 핀은 **5641238**이다. 헬퍼는 그 정수를 소스에 박아 두지 않고, 서명은 환경 변수를, 필수 체크의 앱 id는 기본 브랜치 `.github/repository-settings.json`을 읽는다. 둘은 같은 앱이어야 한다. `post_review_gate.py`는 **기본 브랜치(또는 검증한 릴리스)의 깨끗한 트리**에서 실행한다. **검토 중인 PR head의 워크스페이스에서는 실행하지 않는다.**

### 체크아웃

게이트 스크립트는 같은 폴더의 `check_review_status.py`와 `pr_author.py`를 가져온다. **파일 한두 개만 복사하면 실패**한다. 고정 디렉터리의 clone(예: `$HOME/src/repo-baseline-gate`)에서 **`main`의 깨끗한 트리**로 맞춘 뒤 실행한다.

```bash
GATE_TREE="$HOME/src/repo-baseline-gate"   # PR head 워크스페이스가 아님
cd "$GATE_TREE" || exit 1
git fetch origin main
# 작업 트리가 깨끗한지 확인 — 로컬 커밋·수정이 있으면 게이트 스크립트가 읽는 검사기와 어긋날 수 있다
if [ -n "$(git status --porcelain)" ]; then
  echo "GATE_TREE has local changes; fix or use a fresh tree" >&2
  exit 1
fi
git reset --hard "origin/main"
```

대안: 검증한 **`main`의 전체 SHA**를 알고 있다면 `git fetch origin <SHA>` 후 `git reset --hard <SHA>`로 고정하거나, 깨끗한 디렉터리에 `git archive <SHA> ... | tar -x`로 풀어 쓴다.

### 승인 시 Mac에서 하는 일 (권장 흐름)

소유자가 직접 한다. 에이전트 셸이 아니다.

1. **검토한 head SHA를 변수에 고정**한다(아래 `SHA`). PR이 갱신되면 다시 읽어 바꾼다.
2. `review/independent`와 `review/security`는 올리지 않아도 된다. 참고로 남기려면 **개발 계정 `gh api`**로 그 `SHA`에 올린다. 앱은 올리지 않는다.
3. **1인 프로필이고 되돌리기 어려움(PR)일 때만**: PR 댓글 `되돌리기 어려움 승인: <SHA>` (한 줄, 위와 **동일한** 전체 SHA). 편집하지 말고 새 댓글을 단다(`POLICY.md` §10). 댓글은 `Review status`를 자동으로 다시 돌리지 않는다. 프로필은 기준 브랜치 `AGENTS.md`의 한 줄 `프로필: 팀`이다. 그 줄이 없으면 1인이고, 이 단계 다음의 게이트 실행은 게이트 경로와 함께 그 줄을 더하거나 빼는 diff, 그 diff를 읽지 못하는 경우, 이름을 바꿔 head의 `AGENTS.md`에 그 줄이 생기는 경우, 파일 목록이 300개 이상이거나 diff가 너무 큰 경우에도 그 댓글을 검사한다. 그 밖의 게이트 경로 밖 되돌리기 어려움은 검사기가 댓글을 보지 않으므로, 소유자가 이 댓글을 남긴 뒤에만 병합한다. 되돌리기 쉬움이면 이 댓글은 필요 없다. 그 밖의 검사 조건은 `POLICY.md` §5를 따른다. **팀 프로필**은 이 SHA 댓글을 요구하지 않는다. 사람 승인은 `POLICY.md` §9다.
4. 위 **체크아웃**으로 `GATE_TREE`를 깨끗이 맞춘다.
5. Keychain에서 PEM을 임시 파일로 꺼낸다. 읽기 `GH_TOKEN`은 그 서브셸에서만 `gh auth token`으로 채운다. `--dry-run` 후 실제 실행한다.

```bash
set -euo pipefail
REPO="minjunkim-dev/repo-baseline"
PR="<번호>"
# 리뷰를 마친 head — PR이 바뀌었는지 확인할 때까지 이 값을 고정해 쓴다
SHA="<검토를 마친 head의 전체 40자 SHA>"
GATE_TREE="$HOME/src/repo-baseline-gate"

cd "$GATE_TREE"
git fetch origin main
if [ -n "$(git status --porcelain)" ]; then
  echo "GATE_TREE has local changes" >&2
  exit 1
fi
git reset --hard origin/main

# 참고 status를 개발자 gh 로그인으로 올리기 전에 ambient 토큰을 비운다
unset GH_TOKEN GITHUB_TOKEN

# 2: 참고 status는 선택이다. 게이트는 이 명령을 요구하지 않는다.
# gh api "repos/${REPO}/statuses/${SHA}" -f state=success -f context=review/independent \
#   -f description="<도구> <모델> 지적 <수>"
# gh api "repos/${REPO}/statuses/${SHA}" -f state=success -f context=review/security ...

# 3: 1인 프로필 + 되돌리기 어려움(PR)일 때만
# gh pr comment "$PR" --repo "$REPO" --body "되돌리기 어려움 승인: ${SHA}"

# 5: 게이트 — 개발자 gh 읽기 토큰(이 서브셸만) + 설치 토큰 발급용 PEM
# PEM과 토큰 값은 GH_TOKEN 문자열에 섞지 않는다. 스크립트는 gh auth token을 호출하지 않는다.
(
  set -euo pipefail
  KEY=$(mktemp -t review-gate-key)
  chmod 0600 "$KEY"
  trap 'rm -f "$KEY"' EXIT
  security find-generic-password -a "$USER" -s review-gate-app-key -w > "$KEY"
  export REVIEW_GATE_APP_KEY="$KEY"
  # repo-baseline의 핀. 다른 저장소는 그 저장소 설정의 양의 정수.
  export REVIEW_GATE_APP_ID="5641238"
  # 상속된 REVIEW_GATE_API를 비운 뒤에 개발자 토큰을 넣는다. 남아 있으면 첫 읽기가 그 주소로 토큰을 보낸다. 비우면 기본 주소는 https://api.github.com 이다.
  unset REVIEW_GATE_API
  export GH_TOKEN="$(gh auth token)"
  cd "$GATE_TREE"
  set +e
  dry=$(python3 -I profiles/review-gate/post_review_gate.py --repo "$REPO" --pr "$PR" --sha "$SHA" --dry-run)
  set -e
  printf '%s\n' "$dry"
  kind=$(printf '%s\n' "$dry" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read().splitlines()[-1])["kind"])')
  if [ "$kind" = failure ]; then
    python3 -I profiles/review-gate/post_review_gate.py --repo "$REPO" --pr "$PR" --sha "$SHA"
  elif [ "$kind" = success ]; then
    # success를 올리고 그 SHA로 squash 병합한다. 개발자 gh 로그인이 되어 있어야 한다.
    # 이 서브셸의 GH_TOKEN은 읽기에만 쓴다. 스크립트가 gh pr merge에는 넘기지 않는다.
    python3 -I profiles/review-gate/post_review_gate.py --repo "$REPO" --pr "$PR" --sha "$SHA" --merge
  else
    echo "review gate not posted: $kind" >&2
    exit 1
  fi
)
# 서브셸이 끝나면 GH_TOKEN·임시 PEM이 이 셸에 남지 않는다
```

예시는 `--dry-run`에 `--merge`를 붙이지 않는다. 그 실행은 근거(REST)만 읽고 GraphQL CheckRun 준비 상태는 보지 않는다. 준비 상태(필수 체크, 리뷰 스레드, `reviewDecision`)는 다음 `--merge`가 읽는다. `--dry-run --merge`를 쓰면 그때 GraphQL도 읽지만 이 예시는 그렇게 하지 않는다. `--dry-run`은 근거를 읽고 올릴 판정만 출력한다. **설치 토큰은 만들지 않고**, commit status POST도 병합도 하지 않는다. 표준 출력의 마지막 줄은 JSON이다. `kind`가 `failure`이면 `--merge` 없이 다시 실행해 그 SHA에 failure를 올린다. `kind`가 `success`이면 `--merge`로 실행한다. 그 명령만 success를 올리고, 바로 그 SHA를 `--squash --match-head-commit`으로 병합한다. `--merge`가 없는 실실행은 success를 올리지 않는다. 근거가 통과하면 pending이다. `set -e`만 두면 dry-run의 종료 코드 1이 그 갱신을 건너뛴다. `skip`과 `unverified`는 POST하지 않는다. auto-merge가 걸려 있으면 `--merge`는 거부한다. `gh pr merge <번호> --repo <저장소> --disable-auto`로 끈 뒤에 다시 실행한다. `--auto`와 `--admin`은 쓰지 않는다.

남은 위험: 읽기, success 게시, 재검사, 병합은 원자적이지 않다. 재검사 직전에 본문이 바뀌면 그 변화를 놓칠 수 있다. SIGINT, SIGTERM, SIGHUP, SIGQUIT, 그리고 응답을 읽지 못한 POST는 success가 올라갔을 수 있어 failure로 지우려고 한다. 그 failure 게시는 한 번이다. 게시가 실패하면 success가 남을 수 있으니 그 SHA의 `review/gate`를 확인한다. openssl 서명은 다른 세션이라 터미널이 이 프로세스 그룹에 보낸 그 신호로 죽지 않는다. 병합 중 그 신호는 gh를 끊는다. 정리에 들어갈 때, defer를 켜기 전이나 켜는 줄에서 신호가 나도 failure 게시와 이전 핸들러 복원은 계속된다. 그 게시는 원자적이지 않다. 병합 명령의 종료 코드만으로는 병합 여부를 정하지 않고 PR을 다시 읽는다. 확인할 수 없으면 success를 지운다. SIGKILL, 전원 손실, 응답 자체가 없는 네트워크 단절은 지우지 못한다. 같은 Mac 사용자로 키에 닿는 주체는 신뢰 경계다. `--merge` 없는 실행이 옛 success를 pending 또는 failure로 바꾸는 것은, 그 SHA가 아직 열린 PR의 head이고 조회가 성공할 때뿐이다. head가 옮겨졌거나, PR이 닫혔거나, 그 조회가 실패하면 옛 success는 지워지지 않는다. 그 SHA로 브랜치를 되돌리기 전에는 사람이 `gh pr merge`를 실행하지 말고 auto-merge를 켜지 않는다. 설정 파일의 `app_id`는 양의 정수다. `-1`은 앱을 고정하지 않으므로 `--merge`가 거절한다. `review/gate`의 핀을 풀지 않는다. 이것은 절대적인 신선도 보장이 아니다.

스크립트는 저장소 밖 0600 파일만 키로 받는다. symlink, 저장소 안의 경로, 다른 모드는 거부한다. `GITHUB_ACTIONS`가 있으면 거부한다.

### Keychain에 넣기

**PEM 내용을 명령 줄 argv로 넣지 않는다** (`-w "$(cat file.pem)"`는 프로세스 목록에 노출될 수 있다).

**멀티라인 PEM 저장(필수):** Apple `security add-generic-password`의 `-w` **대화형 입력은 보통 getpass() 한 줄**이라, **첫 개행에서 끊긴다**. 그러면 Keychain에는 `-----BEGIN … PRIVATE KEY-----` 한 줄만 들어가고, 나중에 `openssl` 서명이 실패한다. **앱 PEM은 아래 둘 중 하나로만 저장한다.**

1. **권장 — Keychain Access.app:** “password” / generic 항목을 만들거나 수정하고, **값 필드에 PEM 전체**(BEGIN~END, 줄 바꿈 포함)를 붙여 넣는다. 서비스 이름 예: `review-gate-app-key`, 계정은 본인 Mac 계정.
2. **임시 파일 → GUI:** 다운로드한 PEM을 **0600** 잠시 파일에만 둔 뒤, **Keychain Access에 붙여 넣고 즉시 파일을 지운다.** PEM을 **셸 argv나 `$(cat …)`로 `security`에 넘기지 않는다.**

`security` 한 줄 CLI만으로 멀티라인 비밀을 안전하게 넣는 공식 경로가 없으면, **GUI가 필수**다. **대화형 `security … -w`(인자 없음)로 PEM 전체를 넣는 방법은 쓰지 않는다.**

**꺼내기:** `security find-generic-password -a "$USER" -s review-gate-app-key -w`는 저장한 **전체 문자열**(멀티라인 PEM)을 stdout에 내므로, 위 스니펫처럼 **임시 0600 파일**로 리다이렉트해 `REVIEW_GATE_APP_KEY`에 쓴다.

권장 경로는 읽기 PAT를 Keychain에 따로 두지 않는다. 읽기는 개발자 `gh` 자격이다. 예전에 만들어 둔 `review-gate-read-token` 항목이 있어도 이 문서는 그 항목을 지우지 않는다. 일상 실행은 그 항목을 읽지 않는다.

다운로드한 원본 PEM은 Keychain에 넣은 뒤 **디스크에서 지운다.** 개발 홈에 서 있는 `review-gate.pem`을 두지 않는다.

## 앱 만들기

소유자가 브라우저에서 한다. 이 절차를 Actions나 클라우드 에이전트에 맡기지 않는다.

1. GitHub 개인 계정에서 GitHub App을 등록한다. [앱 등록](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app). 이름 예: `repo-baseline-review-gate`. Homepage URL은 `https://github.com/minjunkim-dev/repo-baseline`이면 된다.
2. Webhook은 끈다. Active를 끄면 Webhook URL이 필요 없다.
3. 권한은 저장소의 **Commit statuses: Read and write**, **Metadata: Read**(앱의 기본값)만 켠다. Checks, Contents, Pull requests, Administration, Actions는 끄다. 계정 권한은 비운다.
4. 설치 위치는 Only on this account. 설치가 끝나면 App ID(정수의 앱 ID, 설치 ID가 아니다)를 앱 설정 페이지에서 적는다.
5. Private key는 브라우저에서 생성한다. **PEM 내용은 Keychain으로만 옮기고**, 에이전트가 읽는 홈·저장소·클라우드 경로에 남기지 않는다.

## 설치하는 저장소

앱 하나에 저장소만 고른다. 다음 넷만 설치한다.

| 저장소 |
| --- |
| `minjunkim-dev/repo-baseline` |
| `minjunkim-dev/smallnext` |
| `minjunkim-dev/BGLike` |
| `minjunkim-dev/mobile-runtime` |

다른 저장소, 조직 전체, 계정의 모든 저장소에는 설치하지 않는다. 새 저장소를 더할 때는 이 표를 먼저 고친다.

확인: 버린 브랜치에 열린 Draft PR을 만든다. 본문에 리뷰 근거를 채우지 않는다. 위 Keychain 흐름으로, `--dry-run` 없이 그 PR의 현재 head에 `failure`를 올린다. 앱 이름으로 보이는지 본 뒤 PR을 닫는다. 기본 브랜치와, 리뷰 근거가 있는 PR에는 이 확인을 하지 않는다. head가 아닌 SHA에는 스크립트가 올리지 않는다.

## 기준선에 App ID 넣기

소비 프로젝트의 `.github/repository-settings.json`에는 `review/gate`의 `app_id`를 **전용 앱의 정수**로 둔다. 이 저장소(repo-baseline)의 기록은 **`5641238`**이다. `templates/repository-settings.json`을 채울 때는 아직 앱이 없으면 자리표시자를 쓰고, **정수로 바꾸기 전에는** `tools/apply_github_settings.py`가 조회 전에 멈춘다.

`tools/apply_github_settings.py`는 값이 `REPLACE`로 시작하면 조회 전에 멈춘다. `tools/check_github_settings.py`도 그 문자열인 동안 `validate_profile`이 실패해 UNVERIFIED로 끝난다. 0, -1, 15368은 `review/gate`의 `app_id`로 통과하지 않는다. 적용 도구와 `validate_profile`이 둘 다 거절한다. 정수가 된 뒤에만 계획을 본다.

```bash
python3 tools/apply_github_settings.py .
```

소비 프로젝트가 `review/gate`를 처음 넣을 때는 `DIFF`에 그 `app_id`가 전용 앱 정수로 가는지만 확인한 뒤, 소유자가 승인하고 `--apply`한다. repo-baseline은 이미 5641238이다. 기대값에서 `Review status`를 뺀 뒤의 적용 DIFF는 그 한 항목을 빼는 것이다. Baseline checks와 `review/gate` 5641238은 남긴다. 이 문서는 `--apply`를 실행하지 않는다. smallnext, BGLike, mobile-runtime은 각자 기준선 PR에서 `review/gate`를 더하고, `Review status`가 필수로 있으면 그 PR에서 뺀다. 그 PR도 보호를 적용하지 않는다. 적용은 각 저장소에서 소유자가 Mac으로 한다. repo-baseline의 E 재시험 음성 결과(PR #47, 위조와 소유자 status가 병합을 BLOCKED로 남김)는 Issue #32 댓글에 있다. 전용 앱 success로 병합이 열리는 대조는 그 댓글에서 미실행이다. 이 문서는 그 셋의 보호를 적용하지 않는다.

### 적용 전후

2026-11-06에 각 저장소 `main`의 `.github/repository-settings.json`을 읽었다. 서버의 branch protection은 이 환경의 토큰으로 조회하지 못했다(403). 카나리 E는 repo-baseline의 서버 보호가 `Review status`를 15368에 고정하고 있었음을 보였다. 아래 오른쪽 열은 기준선 파일의 계획이다. 아직 서버에 쓰지 않았다. `strict`는 네 저장소 모두 true이고 유지한다. 기존 체크는 빼지 않는다.

| 저장소 | 적용 전 필수 context (`app_id`) | 적용 후 |
| --- | --- | --- |
| repo-baseline | `Baseline checks (Python 3.11)` 15368, `Baseline checks (Python 3.13)` 15368, `Review status` 15368 | 왼쪽을 유지하고 `review/gate`를 전용 앱 ID에 추가 |
| smallnext | `PR conventions` 15368, `Repository hygiene` 15368, `Project checks` 15368, `Review status` 15368 | 왼쪽을 유지하고 `review/gate`를 전용 앱 ID에 추가 |
| BGLike | `policy / PR conventions and scope` 15368, `smoke` 15368, `CI` 15368, `Review status` 15368 | 왼쪽을 유지하고 `review/gate`를 전용 앱 ID에 추가 |
| mobile-runtime | `CI` 15368, `Review status` 15368 | 왼쪽을 유지하고 `review/gate`를 전용 앱 ID에 추가 |

위 표는 `review/gate`를 더하던 때의 계획이다. 카나리 E 재시험(Issue #32, PR #47) 뒤 repo-baseline의 기대값은 `Review status`를 뺀다. 남은 필수 context는 `Baseline checks (Python 3.11)` 15368, `Baseline checks (Python 3.13)` 15368, `review/gate` 5641238이다. 서버 적용은 이 변경이 하지 않는다. 병합 뒤 소유자가 계획을 보고 `--apply`한다. 그 DIFF는 `Review status` 한 항목을 빼는 것이다. smallnext, BGLike, mobile-runtime의 표는 이 변경이 바꾸지 않는다.

## 키 교체와 폐기

앱 ID는 키를 바꿔도 그대로다. 보호의 `app_id`는 키 교체만으로 바꾸지 않는다.

교체: 앱 설정에서 새 private key를 만든다. Keychain의 `review-gate-app-key` 항목을 갱신한다. 위 확인과 같이, 근거가 없는 열린 Draft PR의 현재 head에 `failure`를 올려 새 키가 동작하는지 본다. 동작하면 그 경로를 남기고, 그 다음에 앱 설정에서 이전 키를 지운다. 이전 키로 만든 installation token은 만료된다. 이미 올라가 있는 status는 지워지지 않는다.

폐기: 게이트를 올리는 일을 멈춘다. Keychain 항목을 지운다. GitHub에서 키를 지우고, 필요하면 앱 설치를 제거한다. 설치를 빼면 새 `review/gate`를 올리지 못한다. 필수 체크로 남아 있으면 병합은 막힌다. 그것이 실패 닫힘이다. 보호에서 `review/gate`를 빼려면 기준선의 정수를 유지한 채 그 항목을 삭제한 별도 PR을 병합하고, 소유자가 계획을 본 뒤 적용한다. 15368이 `review/gate`를 충족하게 바꾸지 않는다.

## Mac Studio와 팀

서버가 생기기 전에는 키를 Mac에만 둔다. 서버가 생기면 같은 앱과 같은 앱 ID를 유지한 채 pem만 옮긴다.

1. Mac Studio의 게이트 계정 홈에 `0700` 디렉터리와 **또는** 동등한 HSM·Keychain 정책을 둔다. 개발용 Mac, Grok Bot의 컴퓨터, 저장소에는 두지 않는다. 옮긴 뒤 이전 위치의 재사용 가능한 PEM을 지운다.
2. 올리는 주체는 소유자다. 스크립트는 서버에서 돌릴 수 있으나, **키 재사용 자격 증명은 에이전트와 공유하지 않는다.**
3. `review/independent`와 `review/security`는 게이트 조건이 아니다. 참고로 남긴다면 사람 계정의 `gh`로 올린다. 팀 프로필에서는 그 PR을 구현하지 않은 사람이 남긴다. 앱이 그 둘을 대신 올리지 않는다.
4. `AGENTS.md`의 `프로필: 팀`과 승인 수·CODEOWNERS 변경은 `POLICY.md` §9다. 그 설정 쓰기는 소유자 승인 뒤에 `tools/apply_github_settings.py`로 한다. 키 이전과 한 PR에 섞지 않는다.
5. 되돌리기: 서버에서 올리기를 멈추고 키를 Mac의 안전한 저장소로 되돌린다. 앱 ID가 같으면 보호 규칙은 그대로다.

## 카나리 E 재시험

자리표시자를 정수로 바꾸고 repo-baseline에 보호를 적용한 뒤에만 한다. 이 설계 PR에서는 하지 않는다. 시험 workflow를 `main`에 병합하지 않는다. 시험 PR은 닫는다.

1. 버린 브랜치에 다음 workflow만 둔 PR을 연다. 이름은 시험용이다. `pull_request`에서만 돈다.

```yaml
name: canary-e-retest
on:
  pull_request:
permissions:
  checks: write
  statuses: write
jobs:
  forge:
    runs-on: ubuntu-24.04
    steps:
      - name: Post the gate name with the workflow token
        env:
          GH_TOKEN: ${{ github.token }}
          SHA: ${{ github.event.pull_request.head.sha }}
          REPO: ${{ github.repository }}
        run: |
          set -euo pipefail
          gh api "repos/${REPO}/statuses/${SHA}" -f state=success -f context=review/gate -f description=canary-e-retest
          gh api "repos/${REPO}/check-runs" -f name=review/gate -f head_sha="${SHA}" -f status=completed -f conclusion=success -f started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)" -f completed_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

2. 통과 조건. 두 API가 201이어도 된다. 체크 run의 앱은 15368이다. status의 작성자는 `github-actions[bot]`이다. 그 PR의 필수 체크 `review/gate`는 충족되지 않는다. GraphQL에서 그 15368 객체의 `isRequired`는 거짓이거나, 필수 context `review/gate`는 전용 앱의 success가 생기기 전까지 대기다. 병합 가능이 아니다.
3. 대조. 소유자가 증거 조건을 만족하는 그 head에 Mac 스크립트로 `review/gate` success를 올린 뒤에만 그 필수 context가 충족된다. 그 다음 workflow를 다시 돌려 같은 이름으로 success를 올려도, 15368 객체가 전용 앱의 필수 조건을 지우지 않는다. 전용 앱이 그 SHA에 failure를 올리면 필수 조건은 다시 실패다.
4. workflow 파일을 지우는 커밋을 넣지 않고 PR을 닫는다. `main`에 `checks: write`로 `review/gate`를 올리는 workflow를 두지 않는다.
5. 결과를 Issue #32 댓글 하나에 적는다. 시각, PR 번호, 위조 run의 앱 ID, 필수 체크가 충족되지 않았다는 문장, 전용 앱 success 뒤의 대조를 적는다. 그 댓글이 없으면 smallnext, BGLike, mobile-runtime의 적용은 멈춘다.

---

## 레거시(선택): reviewgate UID·봉인·sudoers·git archive·별도 읽기 PAT

다음은 **이전에 문서화했던 강한 분리**다. 별도 macOS 사용자 `reviewgate`, 홈의 0600 PEM, 봉인 디렉터리(`review-gate-seal`), `sudoers`로 허용한 래퍼만 실행, `git archive`로 봉인 트리 갱신, 해시 대조, 별도 읽기 전용 PAT다. **1인·소규모 팀의 권장 일상 경로가 아니다.** 그 절차를 여기서 다시 적지 않는다. 세부 셸 예시와 해시 절차는 이 문서의 이전 버전(git 기록)을 본다.

핵심 경고는 그대로다: 스크립트는 Keychain을 직접 읽지 않는다. `REVIEW_GATE_APP_KEY`는 일반 파일 경로다. **개발 UID와 같은 홈에서 에이전트가 돌면**, 임시 PEM이 있는 순간 키가 노출될 수 있다. 레거시 배치는 그 분리를 sudo·별도 홈으로 풀었다. Keychain 권장 경로는 **PEM을 에이전트가 읽는 홈에 두지 않는 것**이 첫 목표다.
