# 에이전트 권한 예시

하네스 거부 규칙은 보안 경계가 아니다. `gh api`, `gh auth token`과 `curl`, 셸 스크립트, `git -C . push` 같은 다른 표기로 우회된다. 브랜치 보호와 필수 CI도 소유자 `gh` 로그인으로 도는 에이전트의 병합까지는 막지 못한다(POLICY §5). 이 설정은 실수를 줄이는 장치다. 기계적으로 막아야 하면 에이전트를 별도 OS 사용자와 GitHub 계정으로 돌린다.

`gh api`는 인자 패턴으로 읽기와 쓰기를 확실히 가를 수 없어서 전부 확인(`ask`)을 받는다. 보호·ruleset 경로는 거부한다. 이슈·PR 댓글은 `gh issue comment`, `gh pr comment`처럼 하위 명령으로 쓴다.

`main` push 거부는 명시적 표기만 잡는다. `main`에 있는 채로 `git push origin`을 하면 통과한다. 그 경우는 서버의 브랜치 보호(PR 필수, `enforce_admins`)가 거절한다. GitHub 프로필을 켜지 않은 저장소에서는 이 구멍이 남는다.

막을 것은 세 가지다: `.env` 읽기, `main`으로의 push, 브랜치 보호·저장소 설정을 쓰는 `gh api`. `gh pr merge`는 막지 않고 매번 확인을 받는다. 되돌리기 쉬움 PR은 소유자가 지시하면 에이전트가 병합할 수 있기 때문이다(POLICY §5). 확인 창에서 PR 번호와 `--match-head-commit`이 붙었는지 본다.

확인일: 2026-11-08. 하네스가 바뀌면 링크한 공식 문서를 다시 본다.

## 어디에 두는가

워크플로우에 쓰는 것을 둘 곳은 아래 기준으로 고른다.

1. 모든 세션(사람, 로컬 에이전트, 클라우드 에이전트)이 같게 써야 하면 저장소에 커밋한다. 하네스 폴더와 `.mcp.json`은 신뢰 경계라서 그 PR은 되돌리기 어려움이고 소유자가 병합한다(POLICY §4).
2. 사람마다 다르거나 사람이 부를 때만 쓰는 것은 각자의 기기에 둔다. 저장소는 그것 없이 돈다.
3. 비밀값은 저장소에 두지 않는다. 클라우드에는 하네스의 비밀값 설정으로 주고, 병합 권한이 없는 것만 준다(POLICY §5·§7).
4. 기계로 막아야 하는 것은 CI와 브랜치 보호에 둔다. 훅과 권한 설정은 실수를 줄이는 장치다. 훅이 막는 것은 CI가 다시 검사한다.
5. 공식 문서에 없는 하네스 동작에는 기대지 않는다. 그 동작은 없다고 보고 위 1~4번으로 대신한다. 아래에서 "문서에 없다"고 적은 칸이 그렇다. 시험이나 문서로 확인되면 링크와 확인일을 적고 그 칸을 넓힌다.

| 무엇 | 둘 곳 | 클라우드 세션에서 |
| --- | --- | --- |
| 규칙(`AGENTS.md`, `REVIEW.md`, PR 템플릿) | 저장소 | 클론에 들어 있다 |
| check·test 명령 | 저장소의 명령, GitHub Actions 필수 체크 | 같은 명령을 돌린다 |
| 브랜치 보호, CodeQL, Dependabot, 저장소 설정 | GitHub 서버. 소유자가 `tools/apply_github_settings.py`로 적용한다 | 해당 없음 |
| 리뷰 봇 | 기본으로 쓰지 않는다. 리뷰는 POLICY §3대로 다른 컨텍스트의 리뷰어가 한다. 쓰려면 소유자가 GitHub App으로 연결한다. 설정 파일을 커밋하면 저장소 설정과 같이 신뢰 경계다. 봇이 공개 저장소의 자동 리뷰를 건너뛰면(예: CodeRabbit은 별이 적은 저장소에서 건너뛰고 PR 댓글의 체크박스로 손으로 시작하게 한다) 그 PR에는 외부 리뷰가 없는 것이다 | 해당 없음. 지적은 리뷰어가 판정한다(POLICY §3) |
| 리뷰 안전장치(`prompts/review.md`, `tools/review_preflight.py`) | repo-baseline 클론 | 클론이 없으면 그 세션에서 공개 저장소를 클론한다(`prompts/review.md`) |
| 하네스 권한 설정 | 저장소 하네스 폴더(이 문서 아래 절) | 하네스마다 다르다(아래) |
| 모든 세션이 쓰는 프로젝트 스킬 | 저장소 `.claude/skills/`, `.agents/skills/` | Claude Code·Codex는 읽는다. Cursor는 자동화에 쓸 스킬을 저장소 `.cursor/skills/`에 두라고 안내한다 |
| 개인 스킬·플러그인(Matt 스킬, pstack) | 각자의 기기 | 기본으로는 없다. 필요하면 하네스의 동기화 기능을 쓴다(아래) |
| 프로젝트 훅(포매터, 정책 검사) | 저장소 하네스 폴더 | Claude Code(저장소 하나인 세션)·Cursor(명령 훅)는 저장소 훅을 돌린다. 개인 훅은 돌지 않는다. Codex: 문서에 없다. 돌지 않는다고 본다 |
| 프로젝트 MCP | 저장소 `.mcp.json`. 비밀값은 `${VAR}` 참조로만 둔다(hash-copy 검사) | Claude Code는 저장소 하나인 세션에서 읽는다. Cursor는 팀·개인 MCP 설정만 쓴다고 본다(저장소 파일은 문서에 없다). Codex: 문서에 없다. 읽지 않는다고 본다. 저장소는 MCP 없이 돈다 |
| 개인 MCP, 개인 도구(전역 지침에만 적은 것) | 각자의 기기와 개인 설정 | 없다. 저장소는 그것 없이 돈다 |
| 비밀값, 장기 키, `gh` 로그인 | 소유자 기기 | 하네스의 비밀값 설정. 병합 권한 없는 토큰만 |

하네스별 근거(확인일 2026-11-10):

- Claude Code: 클라우드 세션은 저장소를 새로 클론한다. 저장소의 `.claude/skills/`는 클론에 들어 있어 쓴다. `.claude/settings.json` 훅·권한 규칙과 `.mcp.json`은 저장소 하나인 세션에서만 쓴다. 저장소 설정에 적은 플러그인은 설치하지 않는다. 개인 `~/.claude/skills/`·개인 플러그인·개인 MCP는 없다. claude.ai에서 켠 스킬은 불러온다. 키는 환경의 network secrets로 준다([Cloud environments](https://code.claude.com/docs/en/cloud-environments#what-carries-over-from-your-setup)). Claude 프로젝트의 클라우드 스레드는 저장소 루트의 `CLAUDE.md`·`.claude/CLAUDE.md`와 경로 조건 없는 `.claude/rules/`만 읽는다. 이 목록에 `AGENTS.md`는 없다([Claude projects](https://code.claude.com/docs/en/claude-projects#what-threads-pick-up-from-your-repositories), 확인일 2026-11-10). 그래서 그 스레드에는 이 기준의 규칙(`AGENTS.md`)도 권한 설정도 들어가지 않는다. 그 스레드가 `CLAUDE.md`의 `@AGENTS.md` 불러오기를 따라가는지도 문서에 없다. 따라가지 않는다고 본다. 그래서 이 기준의 구현과 리뷰는 그 스레드에서 하지 않고 Claude Code 세션(로컬·클라우드)에서 한다.
- Cursor: Cloud Agent는 저장소 `.cursor/hooks.json`의 명령 훅을 돌리고, 개인 `~/.cursor/hooks.json`은 돌리지 않는다. MCP는 대시보드의 팀 설정과 cursor.com/agents의 개인 설정을 쓴다([Cloud Agents](https://cursor.com/docs/cloud-agent), [Capabilities](https://cursor.com/docs/cloud-agent/capabilities)). 저장소 `.cursor/mcp.json`은 문서에 없다. 개인 스킬은 `~/.cursor/skills/`만 Sync Skills로 동기화된다. `~/.agents/skills/`는 동기화되지 않는다. Cloud Agent가 저장소 스킬을 읽는다는 직접 문장은 없고, 자동화에 스킬을 주려면 저장소 `.cursor/skills/`에 두라고 안내한다([Agent Skills](https://cursor.com/docs/skills)).
- Codex: Codex Cloud는 환경에 저장소, 설치 스크립트, 시작 스킬, 환경 변수와 HTTP secrets를 둔다. HTTP secret을 저장하면 그 도메인 접근도 열린다([Codex Cloud](https://learn.chatgpt.com/docs/cloud)). 저장소에 둔 스킬은 클라우드 작업에서 쓰고, 개인 기기의 스킬은 동기화되지 않는다([Cloud environments](https://learn.chatgpt.com/codex/environments/cloud-environments)). 저장소 훅·MCP 설정·`AGENTS.md`를 읽는지는 두 문서에 없다(확인일 2026-11-10). 훅과 MCP는 없다고 본다. 규칙은 클론에 들어 있으니 작업을 맡길 때 `AGENTS.md`를 읽으라고 적는다.

## Claude Code

`claude-settings.json`을 프로젝트의 `.claude/settings.json`으로 복사한다. 이미 있으면 `permissions.deny`와 `permissions.ask`를 합친다. 예전 예시에서 가져온 `gh pr merge` deny 항목은 지운다. deny가 ask보다 먼저 걸려서 남아 있으면 병합이 계속 막힌다.

- 문법: [Permissions](https://code.claude.com/docs/en/permissions), [Settings](https://code.claude.com/docs/en/settings). `*`는 규칙의 어느 자리에나 올 수 있다. `.env` 예시 `Read(./.env)`, `Read(./.env.*)`는 Settings 문서의 예시와 같다. 하위 폴더의 `.env`는 `**/` 규칙으로 막는다.
- 지침 파일은 `AGENTS.md` 하나다. Claude Code는 작업 폴더와 그 위 폴더에 `CLAUDE.md`·`.claude/CLAUDE.md`·`CLAUDE.local.md`가 없을 때 `AGENTS.md`를 읽는다([Memory](https://code.claude.com/docs/en/memory), 확인일 2026-11-09). 개인용 `CLAUDE.local.md`를 하나 두기만 해도 `AGENTS.md`를 읽지 않으므로 만들지 않는다. 꼭 써야 하면 사용자 설정 `~/.claude/settings.json`에서 `pluginConfigs."cc-plugin-agents-md@builtin".options.instructionFiles`를 `"claude-md-and-agents-md"`로 둔다. 이 설정은 프로젝트의 `.claude/settings.json`에 두면 무시된다.
- `.env.example`도 막힌다. 필요하면 사람이 내용을 알려 준다.
- `gh api *protection*`은 보호 설정 읽기도 막는다. 감사는 소유자가 `tools/apply_github_settings.py`로 한다.
- Claude 프로젝트의 클라우드 스레드는 저장소의 `.claude/settings.json`을 읽지 않는다([Claude projects](https://code.claude.com/docs/en/claude-projects), 확인일 2026-11-08). 그 스레드에는 이 거부 규칙이 없다. 그 환경에는 비밀값을 두지 않고, 병합 권한 없는 토큰만 준다(POLICY §5·§7).

선택: Matt Pocock 스킬 플러그인을 쓰려면 같은 파일에 아래 두 키를 넣는다.

```json
"extraKnownMarketplaces": {
  "mattpocock": { "source": { "source": "github", "repo": "mattpocock/skills", "ref": "v1.3.2" } }
},
"enabledPlugins": { "mattpocock-skills@mattpocock": true }
```

이 두 키는 로컬 세션에서만 플러그인을 설치한다. 클라우드 세션은 저장소 설정에 적은 플러그인을 설치하지 않는다([Cloud environments](https://code.claude.com/docs/en/cloud-environments#what-carries-over-from-your-setup), 확인일 2026-11-08). 클라우드에서도 써야 하면 쓰는 스킬만 저장소에 커밋한다(Claude `.claude/skills/`, Codex·Cursor `.agents/skills/`). Claude 프로젝트의 클라우드 스레드는 저장소 스킬도 읽지 않는다. 그때는 [Claude projects](https://code.claude.com/docs/en/claude-projects#get-skills-plugins-connectors-and-tools-into-threads)를 따른다. 코어는 플러그인 없이 돈다.

플러그인·스킬은 같은 작업을 켤 때와 끌 때 한 번씩 돌려 보고, 결과가 나아진 것만 켠다.

리뷰의 두 축 판단·회고·PR 본문을 이 스킬에 맡기려면 [matt-skills 프로필](../../../profiles/matt-skills/README.md)을 켠다. Matt 스킬의 기본 동작 중 POLICY와 어긋나는 점, 그것을 메우는 절차, 설치 확인 스크립트가 그 프로필에 있다. 프로필을 켜지 않고 스킬만 써도 그 「어긋나는 점」은 지킨다.

pstack 스킬을 쓰면 [pstack 프로필](../../../profiles/pstack/README.md)의 절을 `AGENTS.md`에 붙인다.

코어 기준에 없는 것을 이 스킬로 채울 수 있다. 이 스킬은 사람이 부를 때만 돈다(`disable-model-invocation`, [v1.3.2](https://github.com/mattpocock/skills/tree/v1.3.2/skills), 확인일 2026-11-10).

- 깊은 모듈: `/improve-codebase-architecture`가 최근 자주 바뀐 영역에서 얕은 모듈을 찾아 HTML 보고서로 보여 주고, 고른 후보를 질문으로 다듬는다. 회고에서 테스트가 구현에 묶인다는 지적이 반복될 때 쓴다([prompts/retro.md](../../../prompts/retro.md) 7번). 용어는 `codebase-design`, 도메인 이름은 `GLOSSARY.md`를 따른다.

Claude Code에는 같은 이름의 내장 `/code-review`가 있다. Matt 플러그인으로 설치했으면 `/mattpocock-skills:code-review`처럼 플러그인 이름을 붙여 부른다.

## Codex

[Rules](https://developers.openai.com/codex/rules)로 명령을 막는다. 프로젝트의 `.codex/rules/default.rules`에 둔다. 프로젝트 `.codex/`를 신뢰한 경우에만 읽힌다. 기능은 실험 단계다.

```python
prefix_rule(pattern = ["gh", "pr", "merge"], decision = "prompt", justification = "지시받은 되돌리기 쉬움 PR인지 사람이 본다")
prefix_rule(pattern = ["git", "push"], decision = "prompt", justification = "main으로 push하지 않는다")
prefix_rule(pattern = ["gh", "repo", "edit"], decision = "forbidden", justification = "저장소 설정은 소유자가 바꾼다")
prefix_rule(pattern = ["gh", "api"], decision = "prompt", justification = "보호·설정 쓰기인지 사람이 본다")
```

- 규칙은 정확한 접두사로만 맞춘다. 대상 브랜치(`main`)나 `gh api`의 경로는 가려낼 수 없어서 `git push`와 `gh api`는 `prompt`로 둔다.
- 문서는 규칙이 "샌드박스 밖에서 실행할 명령"을 다룬다고 적는다([Rules](https://learn.chatgpt.com/docs/agent-configuration/rules), 확인일 2026-11-10). 샌드박스 안의 명령에는 걸리지 않는다고 본다. 위 명령은 네트워크를 쓴다. 샌드박스가 네트워크를 막으면 밖으로 나가야 하므로 그때 규칙이 걸린다.
- `.env` 같은 파일 읽기를 막는 설정은 문서에 없다. Codex에는 이 막기가 없다고 본다. 저장소에 비밀값을 두지 않는 규칙(POLICY §7)과 `.gitignore`로 대신한다.

## Cursor

CLI는 [Permissions](https://cursor.com/docs/cli/reference/permissions)대로 프로젝트의 `.cursor/cli.json`에 둔다. deny가 allow보다 우선한다.

```json
{
  "permissions": {
    "deny": ["Read(.env*)", "Shell(gh:pr merge*)", "Shell(git:push*)", "Shell(gh:api*)"]
  }
}
```

- `Read(.env*)`는 문서 예시 그대로다.
- 문서의 규칙 종류는 allow와 deny뿐이라 병합에 확인을 받는 설정이 없다. 승인하지 않은 셸 명령을 실행 전에 묻는다는 직접 문장도 문서에 없다. 묻지 않는다고 본다. 그러면 사람이 병합 명령을 실행 전에 볼 수 없다. 그래서 `gh pr merge`를 deny로 두고, Cursor로는 POLICY §5의 에이전트 병합을 쓰지 않는다.
- `Shell(명령:인자)`의 인자 글롭은 문서 예시가 `curl:*`뿐이다. `gh:pr merge*`처럼 공백이 든 인자가 맞는지는 문서에 없다. 맞지 않을 수 있다고 본다. 맞지 않으면 이 deny는 병합을 막지 못한다. 브랜치 보호와 필수 CI도 맨 위에 적은 대로 소유자 `gh` 로그인으로 도는 병합을 막지 못한다. 그래서 Cursor에 병합을 지시하지 않는다.
- IDE(에디터 안 에이전트)가 이 파일을 읽는지는 문서에 없다. 읽지 않는다고 본다. IDE에서는 확인 창을 사람이 본다.
