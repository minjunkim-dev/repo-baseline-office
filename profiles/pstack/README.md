# pstack 프로필

[pstack](https://github.com/cursor/plugins/tree/main/pstack) 스킬을 이 기준과 함께 쓸 때 켠다. pstack에는 검사·리뷰·구현·보고 단계와 겹치는 스킬이 있고, 그중 몇은 기본 동작이 [POLICY.md](../../POLICY.md)와 어긋난다. 이 프로필은 그 어긋남을 저장소 안에 적어서, 다른 기기·클라우드 세션·다른 사람도 같은 규칙을 보게 한다. 스크립트는 없다. pstack은 사람이 부를 때만 쓰기 때문이다.

## 설치

pstack은 각자의 기기에 설치한다. 저장소에는 커밋하지 않는다. 설치 방법은 [pstack README](https://github.com/cursor/plugins/tree/main/pstack)를 따른다(확인일 2026-11-10).

- Cursor: `/add-plugin pstack`
- Claude Code: `/plugin marketplace add cursor/plugins` 다음에 `/plugin install pstack@cursor-plugins`. 서드파티 마켓플레이스는 자동 업데이트가 꺼져 있어서 설치한 판에 머문다. 올릴 때는 `claude plugin update pstack@cursor-plugins`를 실행한다. 스킬은 `/pstack:poteto-mode`처럼 플러그인 이름을 붙여 부른다.
- Codex: 공식 설치 방법이 README에 없다. Codex에서는 이 프로필을 쓰지 않는다.

설치한 뒤 `/setup-pstack`(Claude Code는 `/pstack:setup-pstack`)으로 모델을 고른다. 이 명령은 개인 설정에 쓰고 저장소는 바꾸지 않는다. 판을 올리면 아래 「맞춘 판」을 다시 본다.

## 켜기

소비 레포 `AGENTS.md` 「작업 방식」 끝에 아래 절을 붙인다. 규칙을 그대로 옮기므로 repo-baseline 클론이 없는 세션도 읽는다.

```markdown
### pstack

pstack 스킬은 사람이 요청할 때만 쓴다. 이 저장소의 규칙이 pstack 기본 동작보다 먼저다.

- `poteto-mode`의 Shipping playbook과 병합·auto-merge 단계는 쓰지 않는다. 병합은 POLICY §5대로 한다.
- `correct`는 제안까지만 한다. 사람이 고른 것만 반영한다.
- 판단 규칙은 `AGENTS.md`가 아니라 `REVIEW.md` 「배운 규칙」에 둔다.
- `create-verification-skill`의 결과는 하네스가 읽는 저장소 스킬 경로(Claude `.claude/skills/`, Codex·Cursor `.agents/skills/`)에 두고, 실행 명령을 `AGENTS.md`의 check·test에 잇는다. 그 경로는 하네스 폴더라서 그 PR은 되돌리기 어려움이고 소유자가 병합한다(POLICY §4).
- `interrogate`·`blast-radius`는 리뷰에 관점을 더할 뿐이다. 리뷰는 그대로 새 세션에서 `prompts/review.md`로 받는다.
- 서로 다른 모델로 검토하지 않았으면 그 사실을 보고에 적는다.
```

Cursor도 `.agents/skills/`와 `.claude/skills/`를 읽고, 하위 폴더의 `.cursor/skills/`·`.agents/skills/`도 찾는다([Agent Skills](https://cursor.com/docs/skills), 확인일 2026-11-10). 그래서 하네스 폴더는 저장소 어디에 있어도 신뢰 경계다.

## 단계별로 겹치는 스킬

| 단계 | pstack 스킬 | 쓰는 법 |
| --- | --- | --- |
| 자동 검사 | `correct`, `create-verification-skill`, `principle-encode-lessons-in-structure` | `correct`는 반복 실수를 구조 > 타입 > 린트 > 테스트 > 문서 순서로 막는다. [prompts/retro.md](../../prompts/retro.md)와 하는 일이 같다. 제안만 받고 사람이 고른다(POLICY §6). `create-verification-skill`은 앱을 실제로 돌려 보는 검증 스킬을 만든다 |
| 리뷰 | `interrogate`, `blast-radius`, `no-comments` | 되돌리기 어려움 PR의 "보안 관점 한 번 더"에 `interrogate`를, Merge Danger의 영향 범위 확인에 `blast-radius`를 쓸 수 있다. 판정과 Review 칸은 [prompts/review.md](../../prompts/review.md)가 맡는다 |
| 구현 | `poteto-mode`, `architect`, `tdd`, `principle-test-behavior-not-implementation` | 시작 전 완료 기준을 정하는 규칙은 그대로다 |
| 보고 | `ketchup`, `show-me-your-work` | 오래 혼자 돈 작업의 결정 기록을 PR 본문에 옮길 때 쓴다. 칸은 PR 템플릿을 지킨다 |

## 다른 프로필과 함께 쓸 때

- [matt-skills](../matt-skills/README.md)도 `tdd` 스킬이 있다. 둘 다 설치했으면 플러그인 이름을 붙여 부른다(예: `pstack:tdd`). Claude Code는 플러그인 스킬을 `/플러그인 이름:스킬 이름`으로 구분한다([Skills](https://code.claude.com/docs/en/skills), 확인일 2026-11-10).
- `create-verification-skill`이 저장소 스킬 경로를 바꾼 PR에서는 matt-skills의 리뷰 위임이 꺼진다(`check_skills.py` 종료 코드 2). 의도한 동작이다.

## 맞춘 판

2026-11-10에 pstack 0.15.36의 스킬 목록으로 이 표를 맞췄다. pstack을 올리면 위 스킬 이름과 기본 동작이 그대로인지 다시 본다.
