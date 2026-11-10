# 변경 기록

항목당 1~3줄. 재설계 전 기록은 [docs/archive/CHANGELOG-2026.md](docs/archive/CHANGELOG-2026.md)에 있다.

## 2026-11 — 재설계 이후

- (repo-baseline-office) `claude --version`이 30초 안에 끝나지 않거나 실행되지 않으면 엔진이 `BLOCKED.md`를 쓰고 멈춘다. 전에는 엔진이 그대로 멈추거나 traceback으로 끝났다. 소비 레포가 옮길 일은 없다.
- (repo-baseline-office) 엔진이 작업자를 띄우기 전에 `claude --version`을 확인한다. 2.1.257 미만이거나 판을 읽지 못하면 `BLOCKED.md`를 쓰고 멈춘다. 낮은 판은 `blockReadsOutsideWorkingDirectories`를 말없이 무시한다. 소비 레포가 옮길 일은 없다.
- (repo-baseline-office) 작업자의 읽기를 과제 폴더와 office 체크아웃으로 좁혔다(`--add-dir`, `blockReadsOutsideWorkingDirectories`). 전에는 `Read`와 `cat`이 홈의 자격 증명 파일을 읽을 수 있었다. 리뷰 단계의 `git fetch*`를 `git fetch origin` 한 형태로 좁혔다. 전에는 `--upload-pa=<명령>`으로 명령이 실행됐다. 인자에 절대 경로·`~`·`..` 경로·따옴표·`$`가 든 `git diff`를 거부한다. `git diff`는 `--no-index` 없이도 저장소 밖 파일을 읽는다. commit 허용을 `commit -m ...` 형태로 좁히고 `--pathspec-from-file`과 `git difftool`을 거부한다. 작업자는 `commit -am`을 쓰지 못한다. Claude Code 2.1.257 이상이 필요하다. 소비 레포가 옮길 일은 없다.
- (repo-baseline-office) `claude-office/HANDOFF.md`의 상태를 맞췄다. PR #10은 병합됐고, 끝난 이슈 #11~#13을 남은 일 표에서 뺐다. 소비 레포가 옮길 일은 없다.
- (repo-baseline-office) 리뷰할 PR이 office 저장소 자신의 PR이면(다른 저장소의 PR임이 `pr.txt`와 origin으로 확실하지 않으면) 엔진이 리뷰 단계를 띄우기 전에 office 체크아웃 전체가 `origin/main`과 같은지 확인한다. 다르거나 커밋하지 않은 변경이 있으면 `BLOCKED.md`를 쓰고 멈춘다. 소비 레포가 옮길 일은 없다.
- (repo-baseline-office) leader 세션으로 실제 제품 과제(smallnext PR #389)를 돌려 leader 규칙을 고쳤다. 방향을 고르기 전에는 등록하지 않고, `--base origin/main`으로 등록하고, `INTENT.md`를 채운 뒤에만 `run`을 돌린다. 작업자가 `.mise.toml`을 고치지 못하게 했다. 소비 레포가 옮길 일은 없다.
- (repo-baseline-office) office 리뷰 단계를 실제 PR(#17)로 돌려 막힌 곳을 고쳤다. 리뷰 전 확인은 office 체크아웃의 스크립트를 경로로 돌리고 PR URL만 받는다. 리뷰 작업자가 PR 본문 Review 칸을 올리는 명령을 지시서에 적었다. 구현·리뷰 단계에 `git rev-parse`와 절대 경로 `git status`를 허용했다. 소비 레포가 옮길 일은 없다.
- (repo-baseline-office) `engine.py`의 `run`·`approve`가 과제 폴더, `task.json`, `state.json`(`approve`만)이 없으면 traceback 대신 stderr 한 줄과 종료 코드 2로 끝난다. 소비 레포가 옮길 일은 없다.
- (repo-baseline-office) 기준 파일을 원본 `c3f6d56`과 같게 맞췄다. `claude-office/`를 다시 짰다. 상주 세션은 leader 하나다. 작업자는 `pipeline/engine.py`가 `stages.json`대로 `hc` 터미널에 단계마다 띄운다. 설계 승인은 `design.md` 해시에 묶었다. 원본과 겹치던 관문·MEMORY·HANDBOOK·reviewer 규칙은 지웠다. 소비 레포가 옮길 일은 없다.
- `POLICY.md` §5: 확인 규칙이 없는 하네스는 병합을 막아 두고 그 하네스로는 에이전트 병합을 쓰지 않는다. 전에는 소유자가 막는 규칙을 빼고 쓸 수 있다고 적어, 같은 줄의 "병합에 확인을 받는다"와 어긋났다. 소비 레포는 POLICY를 링크로 따르므로 옮길 일은 없다. 그런 하네스에서 막는 규칙을 뺀 소비 레포는 다시 넣는다.
- 에이전트 권한 예시의 Cursor 절: Cursor가 셸 명령을 묻지 않는다고 보므로 deny를 빼고 병합하는 길을 지웠다. Cursor로는 POLICY §5의 에이전트 병합을 쓰지 않는다. 브랜치 보호와 필수 CI가 소유자 `gh` 병합을 막지 못한다는 맨 위 문단과 맞췄다. 소비 레포가 옮길 일은 없다.
- matt-skills의 `check_skills.py --harness claude`가 `~/.claude/settings.json`에서 끈 플러그인의 캐시 사본을 세지 않는다. 전에는 리뷰어가 부를 수 없는 사본을 찾았다고 출력할 수 있었다. 소비 레포가 옮길 일은 없다.
- 「어디에 두는가」에 5번 기준을 더했다: 공식 문서에 없는 하네스 동작에는 기대지 않고 없다고 본다. 이에 따라 에이전트 권한 예시·pstack·matt-skills 문서의 "미확인"을 "문서에 없다. 없다고 본다"와 대신할 장치로 바꿨다. 리뷰 봇은 기본으로 쓰지 않는다고 적었다. Claude 프로젝트 스레드용 `@AGENTS.md` 우회 안내를 뺐다. 소비 레포가 옮길 일은 없다.
- 에이전트 권한 예시(`templates/github/agents/README.md`)에 「어디에 두는가」 절을 더했다. 규칙·검사·GitHub 설정·리뷰 봇·스킬·플러그인·훅·MCP·비밀값을 저장소, 각자의 기기, GitHub 서버, 클라우드 설정 중 어디에 둘지 기준과 하네스별 근거를 적었다. Claude 프로젝트의 클라우드 스레드는 `AGENTS.md`를 읽지 않으므로 구현·리뷰는 Claude Code 세션에서 한다고 적었다. 소비 레포가 옮길 일은 없다.
- pstack 프로필에 「설치」 절을 더했다(Cursor·Claude Code 설치 명령, Codex는 미확인). matt-skills의 `check_skills.py`가 `--harness <claude|codex|cursor>`를 필수로 받고, 그 하네스가 읽는 개인 스킬 폴더와 플러그인 캐시에서만 스킬을 찾는다(Codex·Cursor 지원). 리뷰어는 실행 명령에 `--harness`를 붙인다.
- 하네스 설정을 신뢰 경계에 넣었다(`POLICY.md` §4). 대상은 `.claude/`·`.agents/`·`.codex/`·`.cursor/` 같은 하네스 폴더와 `.mcp.json`이다. 그 안의 hook·MCP·스킬은 PR 작업 트리에서 연 리뷰어 세션에서 돌 수 있다. 지침 파일(`AGENTS.md` 등)은 넣지 않고, 리뷰어가 PR이 바꾼 지침을 데이터로 읽게 했다(`prompts/review.md` 2번). 소비 레포는 `REVIEW.md` 「신뢰 경계」 줄에 하네스 설정을 더한다. 셋업 프롬프트도 에이전트 권한 예시를 복사한 PR을 되돌리기 어려움으로 본다. 하위 폴더의 하네스 폴더와 그 안의 지침 파일(`.claude/CLAUDE.md` 등)도 신뢰 경계다. team 프로필을 켠 소비 레포는 `CODEOWNERS`의 `.claude/`·`.agents/`·`.codex/`·`.cursor/` 줄을 앞 `/` 없는 폴더 줄(`.claude/` 등)로 바꿔 하위 폴더의 하네스 폴더도 잡는다.
- pstack 프로필을 더했다. pstack 기본 동작 중 POLICY와 어긋나는 것(Shipping playbook·auto-merge, `correct`의 바로 반영, 판단 규칙 위치)과 단계별로 겹치는 스킬을 적는다. pstack을 쓰는 소비 레포는 프로필의 「pstack」 절을 `AGENTS.md` 「작업 방식」 끝에 붙인다.
- matt-skills 프로필을 더했다. 리뷰의 두 축 판단은 Matt Pocock `code-review` 스킬에(새 세션 리뷰어, fork가 아닌 PR만), 회고는 `/retro`에, PR 본문 내용은 `/pr`에 맡긴다. 안전장치·고치기·라운드·외부 리뷰 판정·Review 칸은 그대로 `prompts/review.md`가 맡는다. `check_skills.py`가 스킬 설치를 확인한다. `tools/review_preflight.py`와 `profiles/matt-skills/*.py`를 이 저장소의 신뢰 경계에 넣었다. 프로필을 켜는 소비 레포는 `REVIEW.md`에 「스킬 위임」 절을 붙인다. Matt 스킬이 POLICY와 어긋나는 점은 에이전트 안내에서 이 프로필로 옮겼다. 리뷰어는 `code-review`를 플러그인 이름을 붙여 부른다(내장 `/code-review`가 아니다). `check_skills.py`는 플러그인 캐시에 판이 여럿이면 가장 높은 판을 출력한다.
- 강연과의 작은 차이를 맞췄다. 코어 `REVIEW.md`에 「코딩 기준」 칸을 더했다(판단이 필요한 작성 규칙만, diff가 건드린 줄에만, P2). 리뷰의 Standards 축이 이 칸도 본다. PR 템플릿 Summary에 선택 줄 「그림」(Mermaid·의사 코드·파일 트리)을 더했다. 회고가 프롬프트·스킬 파일도 지울 대상으로 보고, 선택으로 세션 기록에서 길잡이·도구·정보 접근을 제안하며, 테스트가 구현에 묶이는 지적이 반복되면 구조 개선을 제안한다. 에이전트 안내에 깊은 모듈 스킬(`/improve-codebase-architecture`)을 적었다. 이 저장소 `REVIEW.md`에서 테스트가 이미 막는 행(1만 자, 60줄)을 지웠다. 소비 레포는 `REVIEW.md`에 「코딩 기준」 절을, PR 템플릿에 「그림」 줄을 옮긴다.
- 리뷰를 Spec(완료 기준)과 Standards(`REVIEW.md`) 두 축으로 따로 보게 했다(`POLICY.md` §3, `prompts/review.md` 할 일 1번). 한 축의 지적이 다른 축을 가리지 않게 보고도 축마다 나눈다. 완료 기준이 없거나 모호하면 "Spec 미확인"으로 남긴다. scope creep은 Spec 축에서 본다. 코어 `AGENTS.md`에 PR 본문·리뷰·회고는 이 저장소의 템플릿과 프롬프트가 다른 스킬보다 먼저라는 줄을 더했다. 같은 일을 하는 스킬(예: PR 본문 작성 스킬)이 저절로 불려 `완료 기준:`·Review 칸이 빠지는 것을 막는다. 소비 레포는 이 한 줄을 「작업 방식」에 옮긴다.
- 되돌리기 쉬움 PR은 구현 세션이 띄운 하위 에이전트가 리뷰해도 되게 했다(`POLICY.md` §3). 하위 에이전트에게는 로컬 repo-baseline 클론의 `prompts/review.md` 경로와 PR 링크만 주고, 구현 세션은 리뷰가 끝날 때까지 push하지 않으며 리뷰 결과를 고치지 않는다. 되돌리기 어려움이거나 신뢰 경계를 건드리면 지금처럼 새 세션이 리뷰한다. 소비 레포는 코어 `AGENTS.md` 「작업 방식」의 리뷰 줄을 새 문장으로 바꾼다. `templates/github/agents/README.md`를 복사해 뒀으면 `/code-review` 항목도 바꾼다.
- 하위 에이전트 리뷰어는 구현 대화를 물려받지 않아야 하고 PR마다 하나다. 2라운드부터는 그 리뷰어를 이어 쓰거나 새 세션이 한다. 하위 에이전트 리뷰어는 받은 지시 원문을 Review 칸 「받은 지시」에 적는다. repo-baseline 자신의 PR은 `origin/main` 판의 리뷰 프롬프트·스크립트·`REVIEW.md`로 리뷰한다. 구현 세션은 리뷰가 끝날 때까지 작업 트리도 고치지 않는다. 소비 레포는 코어 `AGENTS.md`의 리뷰 줄을 새 문장으로 바꾼다.
- 리뷰 프롬프트의 `.env*` 이름 확인·base와 head 받기·head SHA 확인을 `tools/review_preflight.py`로 옮겼다. 프롬프트는 이 스크립트를 돌리고 종료 코드로 멈출지 정한다. 소비 레포는 손으로 옮길 것이 없다. 리뷰하는 기기에 repo-baseline 클론과 Python 3.9 이상이 있어야 한다.
- pr-conventions의 `protected_paths` 설정 키를 지웠다. 이 키는 검사만 하고 막는 데 쓰이지 않았다(읽던 review-gate 테스트는 재설계 때 없어졌다). `workflow_policy.py`를 새로 복사하는 소비 레포는 같은 PR에서 `.github/workflow-policy.json`의 `protected_paths`를 지운다. 남겨 두면 알 수 없는 키로 실패한다.
- hash-copy의 `apply_baseline.py`가 `.git/` 안을 가리키는 대상 경로를 거부한다. 실행 권한이 있는 hook을 덮어쓰면 권한이 남아 복사한 파일이 실행될 수 있었다. 소비 레포는 손으로 옮길 것이 없다.
- 리뷰 프롬프트가 fork PR은 `gh pr checkout`하지 않고 check·test도 로컬에서 돌리지 않게 했다. 전에는 fork PR을 연 사람이 정한 테스트 코드와 `AGENTS.md` 명령이 소유자 `gh` 로그인이 있는 기기에서 돌았다. fork PR은 `refs/pull/<번호>/head`를 받아 git으로만 읽고, 검사는 승인된 CI 결과로 본다. PR이 workflow·테스트·검사 명령을 바꿨거나 체크가 끝나지 않았거나 SHA가 다르면 "검사 미확인"으로 적는다. 소비 레포는 손으로 옮길 것이 없다.
- 코어 `AGENTS.md`에 `POLICY.md` §8 작업 추적 규칙(원본은 한 곳, 공개 이슈와 트래커를 함께 쓰면 트래커가 원본, PR에 작업 ID)과 §7의 공개 이슈 금지 줄을 옮겼다. 소비 레포에는 `POLICY.md`가 없어 셋업 뒤 에이전트가 이 규칙을 볼 수 없었다. GitHub 프로필에 `SECURITY.md` 템플릿을 더했다. 소비 레포는 이 세 줄(「작업 방식」 한 줄, 「하지 않는 것」 두 줄)을 `AGENTS.md`에 옮기고, GitHub이면 `SECURITY.md`를 복사해 `OWNER/REPO`를 채운다(이미 `.github/`·`docs/`에 있으면 그 파일에 합친다). 비공개 저장소는 보고 링크 대신 소유자에게 비공개로 연락할 경로를 적는다.
- `.github/workflows/check.yml`과 `templates/github/ci.yml`에 `concurrency`를 더했다. PR에 새로 push하면 같은 PR의 이전 실행을 취소한다. PR이 아닌 실행은 `github.run_id`로 group을 따로 둔다. `cancel-in-progress`만 끄면 main에서 대기 중인 실행이 새 실행에 밀려 취소되기 때문이다. CI 템플릿에 의존성 캐시는 setup 액션의 `cache:` 옵션(lockfile 해시가 키)을 쓰라는 주석을 더했다. 소비 레포는 원하면 `concurrency` 블록을 자기 `ci.yml`에 손으로 옮긴다.
- 리뷰 프롬프트의 `.env*` 이름 확인을 커밋마다도 하게 했다(`git log --no-renames --name-only --cc`). PR 안에서 `.env`를 더한 뒤 이름을 바꾸면 세 점 diff에는 새 이름만 남아 확인을 지났다. 소비 레포는 손으로 옮길 것이 없다.
- 리뷰 프롬프트 5번이 외부 리뷰 지적을 요약 댓글 본문(보안·위험 항목)에서도 찾게 했다. 리뷰 봇마다 head 체크가 completed이고 리뷰 완료라고 쓸 때(체크가 없으면 요약 댓글에 진행 중 표시가 없고 리뷰 범위가 지금 head까지일 때)만 외부 리뷰가 끝난 것으로 본다. 전에는 봇이 리뷰 객체 없이 요약 댓글만 고치면 리뷰어가 끝남을 알아보지 못했고, 요약 댓글에만 있던 지적은 판정하지 않고 지나갔다(PR 103). 소비 레포는 손으로 옮길 것이 없다.

- 리뷰 프롬프트가 diff 본문을 보기 전에 `git diff --name-only --no-renames`로 파일 이름부터 보게 했다. 걸리면 본문을 열지 않고 "리뷰 미완(비밀값 파일)"으로 보고하고 끝낸다. `.env.example`은 걸리지 않는다. 전에는 `sub/.env`를 다른 이름으로 바꾸면 pathspec을 지나 내용이 diff에 보였다. 이름 확인 전에 base와 head를 `git fetch`로 새로 받는다. 외부 리뷰 판정 전의 재확인도 `gh pr diff` 대신 이 두 단계를 다시 한다. 소비 레포는 손으로 옮길 것이 없다.
- 리뷰 프롬프트의 diff 명령에 `':!**/.env*'`를 더했다. `':!.env*'`만으로는 루트의 `.env*`만 빠지고 하위 폴더의 `.env` 내용이 diff로 보였다. 외부 리뷰 전 `.env*` 확인도 하위 폴더를 본다고 적었다. 소비 레포는 손으로 옮길 것이 없다.
- `AGENTS.md` test 칸의 파이프 예시가 로그를 저장소 밖(`${TMPDIR:-/tmp}`)에 쓰게 했다. 전에는 저장소 루트에 `test.log`를 만들었고, 이 파일은 무시 목록에 없었다. 소비 레포가 옮길 일은 없다.
- 외부 리뷰(예: 리뷰 봇)를 참고 자료로 정했다. 그 지적은 다른 컨텍스트 리뷰어가 판정하고, 받아들인 것만 병합 조건의 P0·P1로 센다. 판정하지 않은 외부 리뷰 지적이 있으면 병합하지 않는다. 전에는 봇이 단 심각도가 그대로 에이전트 병합을 막았다. `prompts/review.md`에 외부 리뷰 입력·판정 단계·보고 줄을 더했다. 변경분에 `.env*` 파일이 있으면 외부 리뷰를 읽지 않고, 판정 단계에서 댓글을 다시 받기 전에도 이 확인을 다시 한다. 소비 레포는 `AGENTS.md`의 병합 줄을 손으로 옮긴다.
- 회고 프롬프트에 `AGENTS.md`와 `REVIEW.md` 「배운 규칙」에서 지울 규칙(서로 어긋남, 검사가 이미 막음, 과정만 시키는 지시)을 찾는 단계를 더했다. `POLICY.md` §6에도 같은 줄을 더했다. 규칙을 더하는 길만 있었다. 소비 레포는 손으로 옮길 것이 없다.
- 첫 PR 확인의 `.env` 검사를 `grep`에서 `git check-ignore`로 바꿨다. `.gitignore`에 `!.env` 예외 줄이 있거나 `.env`가 이미 커밋돼 있어도 `grep`은 통과했다.
- `POLICY.md`에 작업 추적 절(§8)을 더했다. 원본 트래커는 하나, 공개 이슈는 연동으로 가져온다. 트래커가 없으면 건너뛴다. §7에 취약점 제보는 비공개 경로로 받는다는 줄을 더했다. pr-conventions 프로필은 `#N`과 함께 트래커 ID(`Fixes ENG-123`)도 이슈 연결로 받는다.
- GitHub 설정 기준선에 `private_vulnerability_reporting`(비공개 취약점 보고)을 필수 항목으로 더했다. 규칙만 있고 켜는 설정이 없었다. 소비 레포는 기준선에 이 키를 더해야 검사가 통과한다. 비공개 저장소처럼 기능이 없으면 예외로 적는다.
- 회고 프롬프트에 되돌림마다 놓친 층(check·test·리뷰·사람)을 적는 단계를 더했다. `REVIEW.md` 예시 표에 완료 기준 밖을 바꾸는 변경을 실패로 보는 행을 더했다. 소비 레포는 원하면 이 행을 손으로 옮긴다.
- 에이전트 권한 안내에 플러그인은 켤 때와 끌 때를 비교해 고른다는 기준과, Matt 스킬의 기본 동작 중 POLICY와 어긋나는 3가지(같은 세션 리뷰, 세션 단위 회고, PR 본문 양식)를 적었다.
- 리뷰 프롬프트 `prompts/review.md`를 더하고 `POLICY.md` §3·README·첫 PR 안내에서 이었다. 구현 세션이 띄운 하위 에이전트는 다른 컨텍스트가 아니라고 적었다. 리뷰를 어떻게 띄우는지 적은 곳이 없었다.
- pr-conventions의 `reject_claude_md` 기본값을 `false`로 바꿨다. 코어가 `CLAUDE.md`(`@AGENTS.md` 한 줄)를 배포하므로 기본값이 코어와 충돌했다. 대신 `CLAUDE.md`가 있으면 `@AGENTS.md` 한 줄이어야 한다. 둘 다 있으면 Claude Code는 기본 설정에서 `CLAUDE.md`를 읽고, `AGENTS.md`는 그 안의 `@AGENTS.md`로 불러올 때만 함께 읽는다. `CLAUDE.md`를 계속 거부하려면 `.github/workflow-policy.json`에 `"reject_claude_md": true`를 둔다.
- team 프로필 `CODEOWNERS`에서 쓰이지 않는 경로 `/.github/trust-boundary-paths`(보관한 review-gate)와 `/tools/apply_github_settings.py`(소비 레포에 복사하지 않음)를 지웠다.
- 코어에서 `CLAUDE.md`를 뺐다(파일 5개 → 4개). Claude Code가 `CLAUDE.md`가 없으면 `AGENTS.md`를 읽게 되어, `AGENTS.md` 하나로 Claude Code·Codex·Cursor가 같은 지침을 읽는다. 둘 다 있으면 Claude Code는 기본 설정에서 `CLAUDE.md`만 읽으므로, 소비 레포는 `CLAUDE.md`를 지운다(`@AGENTS.md` 한 줄이면 남겨도 pr-conventions를 통과한다). 지우기 전에 `CLAUDE.local.md`·`.claude/CLAUDE.md`와 상위 폴더 `CLAUDE.md`가 없는지 본다. 있으면 Claude Code가 `AGENTS.md`를 읽지 않는다. 개인용 `CLAUDE.local.md`도 `AGENTS.md` 읽기를 끈다는 점을 agents README에 적었다.
- 이 저장소에도 루트 `AGENTS.md`(명령 4칸, 길잡이)와 `REVIEW.md`(이 저장소의 실패 기준)를 두었다. `prompts/review.md`가 기대하는 파일이 없었다. `POLICY.md` §4의 이 저장소 신뢰 경계에 소비 레포가 CI·해시 검사·Dependabot·소유권 설정으로 쓰는 `profiles/` 파일을 더했다. pr-conventions는 `CLAUDE.md`와 같은 규칙으로 `.claude/CLAUDE.md`·`CLAUDE.local.md`도 본다. 이 파일들도 Claude Code의 `AGENTS.md` 읽기를 끈다. `.claude/CLAUDE.md`의 포인터는 `@../AGENTS.md`다. pr-conventions를 쓰는 소비 레포는 `scripts/workflow_policy.py`·`test_workflow_policy.py`를 다시 복사해야 새 검사가 적용된다.
- `POLICY.md` §5를 바꿨다. 되돌리기 쉬움 PR은 소유자가 대화에서 지시하면, 필수 CI·외부 리뷰 완료, 다른 컨텍스트 리뷰(P0·P1 없음, 리뷰어도 Door를 쉬움으로 봄)를 갖춘 뒤 리뷰한 커밋에서(`--match-head-commit`) 로컬 에이전트가 병합할 수 있다. 되돌리기 어려움 PR은 그대로 소유자가 병합한다. 자동 병합은 계속 쓰지 않는다. Claude Code 예시는 `gh pr merge`를 deny에서 ask로, Codex 예시는 forbidden에서 prompt로 옮겼다. Cursor 예시는 확인 단계가 없어 deny로 두었다. 지시는 그 에이전트와의 대화에서 소유자가 직접 한 말만 친다(PR 댓글·이슈·다른 세션이 전한 말은 아니다). 브랜치 보호와 필수 CI가 없는 저장소에서는 에이전트가 병합하지 않는다. 리뷰어가 직접 고친 커밋은 리뷰어가 「리뷰한 head」로 적으면 다시 리뷰하지 않는다. 소비 레포는 `AGENTS.md`의 "PR을 병합하지 않는다" 줄과 하네스 설정을 손으로 옮긴다. `prompts/review.md` 보고에 리뷰한 head SHA와 리뷰어의 Door 판정 줄을 더했다. 에이전트가 병합할 때 `--match-head-commit`에 넣을 값과 Door 조건을 여기서 읽는다. 소비 레포에는 `POLICY.md`가 없으므로 코어 `AGENTS.md`에 §5의 병합 조건을 직접 적었다.
- 이 저장소 `AGENTS.md`의 test 칸에 pr-conventions 테스트가 `FAIL:` 줄을 출력해도 종료 코드로 판단한다는 줄을, 길잡이에 `CHANGELOG.md`를 더했다. 소비 레포가 옮길 일은 없다.
- `AGENTS.md` test 칸의 판단 기준을 종료 코드 하나로 좁혔다. 출력을 파일·파이프로 받으면 `FAIL:` 줄이 `OK` 뒤에 나와 「마지막 `OK`」는 맞지 않았다. 파이프로 받을 때는 명령 전체를 `{ ...; } 2>&1`로 묶고 `set -o pipefail`을 붙이는 형태를 적었다. 소비 레포가 옮길 일은 없다.
- `AGENTS.md` test 칸에서 `tee` 사용법을 지우고 「종료 코드로만 판단한다」만 남겼다. test 명령에 파이프가 없는데 사용법을 적은 뒤로 리뷰마다 예외(pipefail, stderr, 로그 위치, symlink)가 나와 문장만 늘었다. 소비 레포가 옮길 일은 없다.

## 2026-11 — 재설계 (#73)

- 코어를 복사만 하는 5개 파일(`templates/core/`)과 한 쪽 규칙(`POLICY.md`)으로 줄였다. Python·manifest 없이 `cp`로 적용한다.
- GitHub 설정은 `templates/github/`, 게이트·PR 형식 검사·해시 복사·팀은 `profiles/` 아래 선택 프로필로 옮겼다. 리뷰 모델 패밀리는 권장으로 내렸다.
- 프롬프트는 `prompts/setup.md`와 `prompts/retro.md` 둘이다. 옛 셋업 프롬프트 2개, 주간 점검, `docs/development-workflow.md`는 지웠다.
- 소비 레포 3곳(smallnext, BGLike, mobile-runtime)을 새 기준으로 옮긴 뒤 `vendor/mattpocock-skills/`를 지웠다. 기본 리뷰 기준은 `REVIEW.md`다(#71).
- review-gate 프로필을 `docs/archive/review-gate/`로 보관했다. 기본 설정이 이미 막는 것만 막고 로컬 에이전트는 막지 못했다. `pr_author.py`는 `profiles/pr-conventions/`로 옮겼다.
- `REVIEW.md` 예시 표에 거짓말하는 테스트(구현 값 되풀이, 소스 모양 검사, 실패를 가리는 mock)를 실패로 보는 행을 더했다.
- `POLICY.md` 병합 절에서 기준이 없던 "근거가 쌓이면 저위험 경로부터 자동 병합" 문장을 지웠다. 자동 병합을 쓰지 않는 정책은 그대로다. 회고 절의 "근거가 쌓이면 완화한다"도 지웠다.
- GitHub 설정 도구에서 CodeQL workflow blob sha 고정(`codeql_main_source`)을 뺐다. codeql-action을 올릴 때마다 기준선을 고쳐야 했다. 남아 있으면 이름을 대고 멈춘다. workflow가 active인지는 계속 본다. smallnext·BGLike·mobile-runtime의 기준선에서 이 키를 지워야 다시 적용된다.
- 부르는 곳이 없던 오프라인 CodeQL 참조 검사와 보관한 review-gate의 App ID 검증을 지웠다. hash-copy 묶음은 설정 검사기를 더 복사하지 않는다. 검사기는 소유자가 이 저장소에서 돌린다.
- PR 양식 Summary에 `완료 기준:` 줄을 두고, `AGENTS.md`에 시작 전에 적는다는 규칙을 더했다. `REVIEW.md`가 받는다던 완료 기준을 적을 곳이 없었다.
- 자체 CI를 Python 3.11·3.13 두 벌에서 최신 안정 버전 한 벌(`Baseline checks`)로 줄였다. 스크립트는 표준 라이브러리만 쓰고 3.9~3.15에서 통과했다. 서버 보호는 아직 옛 두 context를 요구하므로, 병합 직전에 소유자가 `python3 tools/apply_github_settings.py . --apply`로 필수 체크를 `Baseline checks`로 바꾼 뒤 이 PR을 병합한다.
