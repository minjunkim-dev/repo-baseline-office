# repo-baseline 재점검과 재설계안 (2026-11-08)

기준: `main` 55acc14. 참고 자료: Readray 노트 10개의 강연 본문 전체. Readray가 덧붙인 외부 리서치는 펼쳐져 있던 것 중 Anthropic 글 수치 확인 1건만 사용했고, 접혀 있던 블록은 열지 않았다.
**보관 문서다. 재설계는 2026-11-08에 끝났고(W1~W10), 현행 규칙은 [POLICY.md](../../POLICY.md)다.** 아래는 당시 정본 그대로다. 진행 상태는 [추적 이슈 #73](https://github.com/minjunkim-dev/repo-baseline/issues/73)에 있다. 작업 이슈는 #64(W2)~#72(W10). 이어받는 사람은 §9부터 읽는다.
재설계 중에는 기존 `POLICY.md`·`prompts/`·`docs/development-workflow.md`의 절차를 따르지 않는다(소유자 결정, 2026-11-08). 서버 보호는 §7의 W7 전까지 그대로라서, 병합만은 현행 보호를 통과하거나 소유자가 풀어야 한다.

## 0. 결론 한 줄

자료들이 말하는 핵심은 "결정적 검사 → 별도 컨텍스트 에이전트 리뷰(직접 고침) → 위험한 변경만 사람이 깊게"와 "반복 실수는 환경(린트·검사·규칙 파일)으로 옮긴다"이다.
지금 레포는 그 위에 **1인 개발자에게는 과한 승인 기계(전용 GitHub App 게이트, 근거 표 파서, 모델 패밀리 판정, 카나리)**를 쌓았고, 정작 **모든 하네스가 읽는 진입 파일(AGENTS.md)과 리뷰 기준 파일(REVIEW.md)**은 없다.
재설계 방향: 코어는 "복사만 하는 작은 파일 4개 + 한 쪽짜리 규칙", 나머지는 선택 프로필로 내린다.

## 1. 자료가 실제로 말하는 것 (레포 설계 기준으로 압축)

| 원칙 | 출처 | 1인·소규모에 맞는 형태 |
| --- | --- | --- |
| 브레이크 3겹: 자동 검사 → 자동 리뷰 → 사람 | Matt, Anthropic 7겹, Grok 역피라미드 | CI 필수 + 리뷰 에이전트 1회 + 사람은 위험 변경만 |
| 사람 리뷰는 되돌릴 수 있는지(door)와 영향 범위로 강도를 정한다 | Matt, Anthropic(낮음 0명·중간 1명·높음 2명), Grok(녹·황·적) | PR 본문 맨 아래 Merge Danger 3줄 |
| 코딩 기준은 구현 에이전트가 아니라 리뷰 에이전트에게. 규칙은 AGENTS.md가 아닌 별도 파일에 | Matt(coding standards), Anthropic(REVIEW.md) | `REVIEW.md` 하나 |
| 리뷰 에이전트는 댓글보다 수정 커밋. 애매한 것만 댓글 | Matt, Anthropic | 리뷰 절차 한 줄 |
| 리뷰 루프 상한: 3라운드 넘으면 접근을 다시 생각, 첫 라운드 뒤엔 바뀐 부분만, 버그 유형으로 보고, 같은 지적 반복 금지 | Anthropic, 검증 루프 영상 | 리뷰 절차 4줄 |
| 같은 리뷰 댓글을 두 번 쓰지 않는다 → 린트·검사·규칙으로 | Matt retro, Lauren, Grok | 회고는 필요할 때. 결과는 린트 > 검사 > REVIEW.md 한 줄 > AGENTS.md 길잡이 순 |
| 완료 주장은 증거(명령 출력·스크린샷)로 | Anthropic, Lauren, 검증 루프 | PR 템플릿 Evidence 칸 |
| 반복되는 결정적 작업은 스크립트로, 에이전트는 판단만 | Lauren | 프로젝트 `check` 스크립트 하나 |
| 에이전트 통제는 에이전트 자신이 아니라 실행 환경에. PR은 열되 병합은 막는다 | Grok 영상(Docker 참고 구조), Addy | 에이전트 자격증명에 병합 권한을 주지 않는 것이 핵심 |
| 승인은 특정 커밋에만 유효. 봇 승인은 사람 승인이 아니다. CI 워크플로 경로는 항상 사람 | Anthropic | 1인은 "소유자의 병합 클릭"이 그 승인 |
| 공급망 검사, 에이전트 작성 표시, 사람이 최종 책임 | Addy | Dependabot·push protection·Author 줄 |
| 일회용 vs 오래 쓰는 코드는 실패 대가·의존 수·교체 비용·유지 비용으로. 엄밀함을 빼지 말고 그 비용을 낮춘다(표준화, 자동 실행 도구, 쉬운 테스트, 처음부터 엄격한 린트) | Max(Capital One) | 프로필 선택 기준. 코어는 비용이 거의 0이어야 한다 |
| 에이전트 50개 말고 루프 하나부터. 매시간 루틴은 토큰을 태운다 | Grok 영상, Lauren | 정기 자동 실행은 기본값에서 뺀다 |
| 처음엔 엄격하게, 근거가 쌓이면 완화. 되돌림 비율을 가드레일로 | Anthropic | 주간 점검은 선택, 지표는 되돌림 수 하나 |

자료가 **하지 않는 것**: 리뷰 모델 패밀리를 강제하지 않는다(Anthropic은 같은 Claude를 새 컨텍스트로 쓴다). 모든 PR에 축별 근거 표를 요구하고 CI가 그것을 파싱해 병합을 막지 않는다.
반대로 Anthropic의 "승인은 그 커밋에만 유효, 봇 승인은 사람 승인이 아님, CI 경로는 항상 사람"은 자료가 실제로 하는 것이다. 지금의 `review/gate`는 GitHub 개인 계정의 제약 아래에서 그 규칙을 구현하려던 장치다. 원칙은 맞고, 문제는 적용 범위(모든 PR)와 비용이다.

## 2. 진단

### 2.1 과한 것 (병목이 되는 것)

1. **승인 기계 전체**: `review/gate` 전용 App + Keychain PEM + `post_review_gate.py`(45KB) + `check_review_status.py`(36KB) + 테스트 약 120KB + 카나리 기록.
   - 막으려던 위협은 "에이전트가 리뷰 없이 스스로 병합"과 "workflow 토큰의 체크 위조"다. 위협 자체는 맞다.
   - 개인 계정 저장소에서는 GitHub가 "누가 병합하는가"를 제한하지 못한다. 필수 status가 없으면, 소유자 `gh` 로그인으로 도는 로컬 에이전트는 초록 PR을 언제든 병합할 수 있다. 하네스 거부 규칙은 보안 경계가 아니다. `gh api`, `gh auth token`과 `curl`, 셸 스크립트로 우회된다.
   - 게이트가 실제로 더하는 장벽은 "Keychain 안의 PEM 없이는 필수 status를 못 올린다"이다. 다만 `docs/review-gate-app.md:34`가 적듯 같은 macOS 사용자의 에이전트는 개발자 세션과 격리되지 않는다. Keychain 접근 시 확인창이 뜨는지는 항목의 ACL에 달려 있고, 여기서는 확인하지 않았다.
   - 그러니 문제는 게이트의 존재가 아니라 **비용 배분**이다. 모든 PR(문서 한 줄, Dependabot 포함)에 축별 근거 표, 패밀리 판정, 소유자 SHA 댓글을 요구한다.
   - 대안 두 가지(소유자 결정, §5):
     - (A) 게이트 유지·조건 축소: 앱은 그대로 둔다. 되돌리기 쉬운 PR은 CI 성공과 "Review 칸에 리뷰어 기록이 있음"만 보고 status를 올린다. 근거 표 파싱·패밀리 판정은 뺀다. 기계적 방어는 남고, PR당 비용은 크게 준다.
     - (B) 게이트 제거: 브랜치 보호(PR 필수, 필수 CI, force push 금지) + 클라우드 에이전트에는 병합 권한 없는 토큰 + 로컬 하네스 거부 규칙 + "병합은 소유자가 누른다". 남는 위험: 로컬 에이전트의 무단 병합을 기술적으로 막지 못한다. 습관과 하네스 설정에 기댄다. 되돌리기는 revert 한 번이다.
   - 처음 권장은 "이 레포·소비 레포는 (A)"였다. 소유자가 기존 규칙을 따르지 않기로 해서 §6 D2에서 (B)를 기본값으로 채택했다. 이 레포도 (B)이고, (A)는 선택 프로필이다.
2. **PR마다 드는 의식 비용**: 4축 × 8칸 근거 표, 40자 head SHA, `Author` 형식, 같은 패밀리 예외 블록, 소유자 SHA 댓글. 이슈 #58에서 한 줄 문서·테스트 수정 PR 3개가 `review status MISSING`으로 멈췄고, CodeRabbit도 진행 중이었다. 자료의 목표(사람 리뷰를 빠르게)와 반대 방향이다.
3. **모델·제품 이름이 정책과 코드에 박혀 있다**: Composer·Opus·Sonnet·Grok의 별칭 표(`scripts/check_review_status.py:294-343`), 구독(Claude Pro, X $30), Linear 정본, Grok Bot, Mac Studio 이전. 새 모델이 나올 때마다 검사기를 고쳐야 한다. 개인 운영 메모가 "범용 기준"에 섞여 있다.
4. **문서량**: README 1.6만, POLICY 3.5만, development-workflow 3만, pr-ci-setup 1.9만, github-settings 1.1만, review-gate-app 1.9만, CHANGELOG 5.8만 자(한국어). README의 요청문대로 하면 한 세션에 약 9.5만 자가 들어간다. 대략 6만~9만 토큰으로 추정된다(한국어 토큰화 비율에 따라 다름). 같은 사실의 반복도 많다. 예를 들어 카나리 단락은 README에 두 번 있고, "Review status는 필수가 아니다"는 세 문서에 있다.
5. **해시 복사하는 Python 검사기**: 비Python 프로젝트의 CI에 Python 검사기가 들어간다. 코어 manifest로 일부 풀었지만, GitHub 프로필을 켜면 다시 Python이 필요하다.

### 2.2 빠졌거나 약한 것 (큰 리스크)

1. **AGENTS.md는 개념만 있고 템플릿이 없다**: `prompts/pr-ci-setup.md` §3과 `docs/development-workflow.md`의 층 표가 "`AGENTS.md` + `@AGENTS.md`만 있는 `CLAUDE.md`"를 정해 두었다. 하지만 복사할 파일이 없어서, 에이전트가 프로젝트마다 1.9만 자 프롬프트를 읽고 매번 새로 만든다. 결과가 매번 다르고 토큰도 든다. 50줄짜리 템플릿 하나로 대체할 수 있다.
2. **코딩 기준·리뷰 문서도 같은 상태**: `prompts/pr-ci-setup.md` §6에 내용(영역별 실패 정의, `file:line` 근거, "배운 규칙" 섹션)은 잘 들어 있다. 파일 템플릿만 없다. 자료 셋(Matt, Anthropic, 검증 루프)이 공통으로 권하는 `REVIEW.md` 형태로 고정하면 된다.
3. **에이전트 권한 경계가 Claude에만 있다**: `templates/claude-settings.json`은 `.env` 읽기만 막는다. 병합·push·보호 설정 변경 금지는 없고, Codex·Cursor용 설정도 없다.
4. **`.gitignore` 기본값 없음**: `.env*`, 키 파일. 원격 push protection은 있지만 로컬 1차 방어가 없다.
5. **Codex 모델을 리뷰어로 기록할 수 없다**: `model_family()`는 `gpt-5-codex`처럼 이름에 `codex`나 `chatgpt`가 들어간 모델명을 무효로 본다(`scripts/check_review_status.py:322`, 의도는 `docs/development-workflow.md:94`). PR 템플릿의 작성 도구 목록에도 Codex가 없다. Codex를 쓰는 것 자체를 막지는 않지만, Codex가 한 리뷰는 근거 표에서 통과하지 못한다. "어떤 하네스든"과 충돌한다.
6. **리뷰 루프 종료 규칙이 반쪽**: 라운드 상한 3은 있다. "첫 라운드 뒤 변경분만"은 실제로 하고 있지만(이슈 #58), `prompts/pr-ci-setup.md:57`에 미결 결정안으로 남아 있다. "버그 유형으로 보고"와 "보고한 지적 반복 금지"는 찾지 못했다.
7. **빠른 되돌리기**: 트렁크 문서에 피처 플래그가 있지만, PR 템플릿의 `복구:` 칸 말고는 "되돌리기 쉬움을 실제로 보장하는 습관"(작은 PR, revert 한 번)이 코어 규칙에 없다.

### 2.3 스택 독립성 판정

| 항목 | 범용? | 판정 |
| --- | --- | --- |
| main 하나·squash·짧은 브랜치·피처 플래그 | 예 | 코어 |
| 명령 4칸(setup/check/test/build), 없으면 N/A | 예 | 코어 |
| PR 템플릿(요약·증거·Merge Danger·작성자) | 예 | 코어(슬림화) |
| Door 판정·신뢰 경계 경로 목록 | 예 | 코어(한 쪽으로) |
| AGENTS.md·REVIEW.md·.gitignore | 예 | 코어(신설) |
| Dependabot·CodeQL·push protection·브랜치 보호 | GitHub 한정 | GitHub 프로필 |
| Python 검사기 해시 복사, 근거 표 파서, review/gate | 아니요(Python·GitHub·이 소유자 전용) | 선택 프로필 |
| 모델 로스터·구독·Linear·Grok·Mac Studio | 아니요(개인 운영) | 레포 밖이나 `docs/owner/`로 |
| 포매터·린터·테스트 도구 | 스택마다 | 각 프로젝트가 고른다(지금처럼) |

### 2.4 하네스 독립성 판정

- 진입 파일: 설계(AGENTS.md 정본, `CLAUDE.md`는 `@AGENTS.md`)는 맞다. 템플릿으로 고정하기만 하면 된다. 하네스별 로딩 여부는 `docs/development-workflow.md`의 「도구 설치와 확인」 표를 정본으로 두고, 미확인 칸은 그대로 미확인이다.
- 스킬: `.claude/skills`와 `.agents/skills`에 이중 복사. 둘 다 유지하되 Matt 플러그인 설치는 "선택"으로 둔다. 리뷰 절차 자체는 REVIEW.md와 PR 템플릿만 있으면 어떤 하네스든 돌 수 있게 한다.
- 검사기: 모델 이름을 해석하지 않게 한다. 이름은 기록용 문자열일 뿐이다.

### 2.5 토큰 관점

- 지금: 셋업 한 번에 6만~9만 토큰, 그 뒤 PR마다 근거 표 작성과 4축 리뷰, 패밀리가 다른 두 번째 도구 호출.
- 목표: 에이전트가 매 세션 읽는 것은 AGENTS.md(약 3천 자 이하)뿐. 리뷰 때만 REVIEW.md(약 6천 자 이하). 셋업 프롬프트는 파일 1개, 1만 자 이하. README·CHANGELOG·정책 원문은 사람용이고 에이전트가 읽을 필요가 없다.
- 리뷰는 되돌리기 쉬운 PR이면 1회(새 컨텍스트, 모델 무관). 되돌리기 어려운 변경이나 신뢰 경계 변경일 때만 Security를 더한다. 정기 자동 루틴은 기본값에서 뺀다.

### 2.6 그 밖에 놓친 것

- **이 레포 자신이 자기 절차에 갇혀 있다**: 재설계 PR도 현재의 게이트·근거 표·패밀리 규칙을 통과해야 한다. 첫 PR 하나는 현행 절차로 통과시키고, 그 PR이 절차를 줄이는 순서로 가야 한다.
- **소비 레포 3곳(smallnext, BGLike, mobile-runtime)**: 전체 manifest와 해시 검사를 쓴다. 갑자기 지우면 CI가 깨진다. 아래 4단계로 각자 옮긴다.
- **팀 프로필**: CODEOWNERS와 사람 1명 승인은 GitHub 기본 기능으로 충분하다. 앱이 필요 없다.
- **문서의 "확인하지 않음" 남발**: 미확인 표기는 Evidence 칸 한 곳에만 둔다. 정책 문장마다 붙이지 않는다.

## 3. 재설계안

### 3.1 코어 (모든 레포, 복사만, Python 불필요)

```
AGENTS.md                       # 60줄 이하. 목적, 명령 4칸, 디렉터리 길잡이, 완료=명령 출력, 금지(비밀값 커밋·main 직접 push·병합)
CLAUDE.md                       # "@AGENTS.md" 한 줄
REVIEW.md                       # 리뷰 에이전트 전용. 실패 정의·심각도·무시할 것·보고 형식·학습 규칙 섹션
.github/pull_request_template.md  # 아래 슬림 양식
.gitignore 추가분               # .env*, *.pem, *.key 등
```

슬림 PR 양식(20줄 이내):

```
Author: <도구> / <모델>   (에이전트가 썼으면 그대로 적는다)
## Summary      왜, 전후
## Evidence     실행한 명령과 결과, 확인하지 않은 범위
## Merge Danger Door: 되돌리기 쉬움|어려움 · 영향 범위 · 되돌리는 법 · 신뢰 경계: 없음|<경로>
## Review       리뷰어(새 컨텍스트, 모델 이름) · 고친 것 · 남은 지적
```

규칙 한 쪽(`POLICY.md` 대체, 1만 자 이하):

1. 트렁크: main 하나, squash, 작은 PR, 미완성은 꺼진 플래그 뒤에.
2. 완료는 `check`·`test` 출력이다.
3. 리뷰: 구현과 다른 컨텍스트의 리뷰 에이전트가 REVIEW.md로 본다. 확실한 결함은 직접 커밋하고, 애매한 것만 남긴다. 최대 3라운드. 2라운드부터는 변경분만 본다. 버그 유형으로 보고하고, 이미 보고한 지적은 반복하지 않는다. 3라운드 뒤에도 남으면 접근을 다시 생각한다. 다른 모델 패밀리는 권장이지 필수가 아니다.
4. Door: diff로 정한다. 애매하면 되돌리기 어려움이다. 되돌리기 어려움이나 신뢰 경계 경로(workflows, 설정, 의존성 manifest, 인증·결제·마이그레이션 등 프로젝트가 정한 경로)면 Security 리뷰를 더하고, 소유자가 diff를 읽고 그 head에서 직접 병합한다.
5. 병합: 사람만 한다. 클라우드 에이전트 토큰에는 병합 권한이 없다. 로컬 에이전트는 하네스 거부 규칙으로 막지만, 이것은 습관이지 보안 경계가 아니다. 기계적으로 막아야 하는 프로젝트는 게이트 프로필(§3.3)을 켠다. 자동 병합은 쓰지 않는다(근거가 쌓이면 문서·저위험 경로부터 소유자가 켠다).
6. 회고: 같은 지적이 두 번 나오면 린트·검사 > REVIEW.md 한 줄 > AGENTS.md 길잡이 순으로 고친다. 사용자가 고른 것만 넣는다.
7. 비밀값은 커밋하지 않는다. 장기 키는 소유자 기기에만 둔다.

### 3.2 GitHub 프로필 (GitHub에 올릴 때, 권장)

- `templates/repository-settings.json`과 `tools/apply_github_settings.py`는 유지한다. 소유자 기기에서만 돌린다. 값: PR 필수, 필수 CI, force push·삭제 금지, secret scanning·push protection, Dependabot(actions + 생태계), CodeQL default setup(가능한 경우).
- CI 템플릿: 프로젝트 `check` 명령을 부르는 workflow 골격 하나. 언어는 프로젝트가 채운다.
- 에이전트 권한 템플릿: Claude `permissions.deny`에 `.env` 읽기, `gh pr merge`, `git push` to main, `gh api` 보호 설정 쓰기를 넣는다. Codex·Cursor는 같은 의미의 설정을 문서 한 줄로 안내한다.

### 3.3 선택 프로필 (그럴 이유가 있을 때만)

- 고위험·지속형(결제·개인정보·사용자 다수): CODEOWNERS, 1~2명 승인, merge queue, 단계 배포, 정기 security-audit.
- 승인 위조까지 막아야 할 때: 현행 `review/gate` App·근거 표 검사기를 그대로 옮겨 둔다(삭제하지 않고 `profiles/review-gate/`로). 단 패밀리 별칭 판정과 Codex 거부는 뺀다.
- 해시로 지키는 공통 검사기: 원하면 `apply_baseline.py`를 유지한다.
- 외부 리뷰(CodeRabbit), Grok Bot 등 조율자, pstack, 주간 점검: 전부 선택이다.

### 3.4 레포 구조 목표

```
README.md          # 1쪽: 무엇, 코어 적용 3단계, 프로필 표
POLICY.md          # 1쪽 규칙(위 3.1)
templates/core/    # AGENTS.md, CLAUDE.md, REVIEW.md, pull_request_template.md, gitignore
templates/github/  # repository-settings.json, dependabot, ci 골격, claude-settings.json
profiles/          # review-gate/, team/, high-risk/ (현행 코드 이동)
tools/             # apply_github_settings.py, apply_baseline.py
prompts/setup.md   # 셋업 프롬프트 하나(1만 자 이하)
CHANGELOG.md       # 항목당 1~3줄. 과거 서술은 docs/archive/로
```

## 4. 옮기는 순서 (초안. 기존 규칙을 따르지 않기로 해서 §7 작업 단위로 대체)

| 단계 | 내용 | 깨지는 것 | Door |
| --- | --- | --- | --- |
| 1 | `templates/core/` 신설(AGENTS.md, CLAUDE.md, REVIEW.md, 슬림 PR 양식, gitignore), `docs/start.md`를 1쪽으로 | 없음(추가만) | 되돌리기 쉬움 |
| 2 | POLICY·README·development-workflow를 1쪽 규칙으로 합치고 중복 삭제. 개인 운영 메모(모델 로스터·구독·Linear·Grok·Mac Studio)는 `docs/owner/`나 레포 밖으로 | 문서 링크 | 되돌리기 쉬움 |
| 3 | 검사기에서 패밀리 별칭·Codex 거부 제거. 근거 표 필수 칸 축소(슬림 양식과 호환) | 이 레포와 소비 레포의 Review status job(필수는 아님) | 되돌리기 어려움(신뢰 경계 경로) |
| 4 | §5-1 결정대로: (A)면 `post_review_gate.py`의 성공 조건을 축소, (B)면 필수 체크에서 빼고 `profiles/review-gate/`로 이동 | 브랜치 보호 | 되돌리기 어려움, 소유자 적용 |
| 5 | 소비 레포 3곳: 각 레포 PR로 코어 파일 추가 → 원하면 manifest 축소와 게이트 제외. 그때까지 현행 유지 | 각 레포 CI | 레포마다 소유자 |
| 6 | CHANGELOG 정리, `prompts/` 3개를 1개로 | 없음 | 되돌리기 쉬움 |

1단계 PR은 현행 절차(근거 표·게이트)로 통과시킨다. 3·4단계부터 절차가 가벼워진다.

## 5. 소유자가 정할 것 (→ §6에서 채택)

1. 게이트: (A) 유지하되 조건 축소(되돌리기 쉬움은 CI와 리뷰어 기록만), (B) 제거하고 "소유자가 병합"을 습관으로 둔다. (B)의 남는 위험은 로컬 에이전트의 무단 병합을 기술적으로 못 막는다는 점이다. 권장은 이 레포·소비 레포는 (A), 새 프로젝트 기본값은 (B).
2. "다른 모델 패밀리 리뷰"를 필수에서 권장으로 내릴지.
3. 개인 운영 메모를 레포 안 `docs/owner/`에 둘지, 레포 밖(개인 노트)으로 뺄지.

## 6. 채택한 결정 (2026-11-08)

소유자가 바꾸라고 하기 전까지 아래가 기본값이다. 바꾸면 이 표와 추적 이슈를 같이 고친다.

| # | 결정 | 내용 |
| --- | --- | --- |
| D1 | 기존 규칙 비구속 | 재설계 작업은 옛 `POLICY.md`·근거 표·패밀리 규칙·소유자 SHA 댓글을 따르지 않는다 |
| D2 | 게이트는 선택 프로필 | 새 기본값은 §2.1의 (B): 브랜치 보호 + 필수 CI + 사람 병합. `review/gate`는 `profiles/review-gate/`로 옮기고 패밀리 판정·Codex 거부를 뺀다. 이 레포 자신도 기본값(B)을 쓴다 |
| D3 | 패밀리 다양성은 권장 | 리뷰는 구현과 다른 컨텍스트면 된다. 다른 모델 패밀리는 권장이다 |
| D4 | 개인 운영 메모는 레포 밖 | 모델 로스터·구독·Linear·Grok Bot·Mac Studio 이전은 레포에서 지운다. 옮길 항목 목록은 W5 PR 설명에 남기고 소유자가 직접 옮긴다 |
| D5 | 하나의 브랜치·하나의 PR | W2~W6은 브랜치 하나에서 끝내고 PR 하나로 병합한다. W7(서버)과 W9(소비 레포)는 따로 |
| D6 | 코어에는 Python·manifest가 없다 | 코어 적용은 `cp` 몇 번이다. 해시 복사(`apply_baseline.py`)는 선택 프로필 |

## 7. 파일별 처리표

현재 `main`의 모든 추적 파일이 어디로 가는지 정한다. "이동"은 `git mv`로 이력을 보존한다.
소비 레포 CI는 이 레포에 접근하지 않으므로 이동해도 그 CI는 깨지지 않는다. 다만 소비 레포에서 `apply_baseline.py`를 다시 돌리면 옛 경로를 못 찾는다. 그 이전은 W9에서 한다.

| 현재 경로 | 처리 | 새 위치·메모 |
| --- | --- | --- |
| `README.md` | 재작성 | 1쪽: 무엇, 코어 적용 3단계, 프로필 표, 정본 링크 |
| `POLICY.md` | 재작성 | 1쪽 규칙(§3.1의 1~7), 1만 자 이하 |
| `SECURITY.md` | 유지 | |
| `CHANGELOG.md` | 이동 후 새로 | `docs/archive/CHANGELOG-2026.md`로 옮기고, 새 `CHANGELOG.md`는 항목당 1~3줄 |
| `docs/start.md` | 재작성 | 코어 적용 절차 1쪽(`cp` 명령, AGENTS.md 채우기, 명령 4칸) |
| `docs/development-workflow.md` | 삭제 | 범용 부분(트렁크·피처 플래그)은 `POLICY.md`로. 개인 부분은 D4 |
| `docs/github-settings-profile.md` | 흡수 | `templates/github/README.md`(짧게) |
| `docs/review-gate-app.md` | 이동 | `profiles/review-gate/README.md` |
| `docs/redesign-2026-11.md` | 유지 | 완료 후 `docs/archive/`로 |
| `prompts/github-repository-settings.md`, `prompts/pr-ci-setup.md` | 대체 | `prompts/setup.md` 하나(1만 자 이하): 코어 적용 → GitHub 프로필 → 검증 |
| `prompts/weekly-check.md` | 대체 | `prompts/retro.md`(필요할 때 실행, 정기 실행 아님) |
| `.github/pull_request_template.md` | 교체 | `templates/core/pull_request_template.md`와 같은 내용 |
| `.github/repository-settings.json` | 수정 | 필수 체크에서 `review/gate` 제거(D2). 서버 적용은 W7 |
| `.github/workflows/check.yml` | 수정 | 남는 테스트만 실행. matrix는 최소로 |
| `.github/workflows/review-status.yml` | 삭제 | 템플릿은 `profiles/review-gate/`에 있음 |
| `.github/workflows/pr-policy.yml`, `.github/workflow-policy.json` | 삭제 | 템플릿은 `profiles/pr-conventions/` |
| `.github/dependabot.yml` | 유지 | |
| `templates/repository-settings.json` | 이동·수정 | `templates/github/`. 기본 필수 체크에 `review/gate` 없음 |
| `templates/dependabot.yml`, `templates/dependabot-ecosystem.yml` | 이동 | `templates/github/`. 생태계는 손으로 적는 예시로 단순화 |
| `templates/claude-settings.json` | 이동·수정 | `templates/github/agents/claude-settings.json`. deny에 `.env` 읽기 + `gh pr merge` + main push + 보호 설정 쓰기. Matt 플러그인은 주석 수준의 선택 |
| (신규) | 추가 | `templates/github/agents/README.md`: Codex·Cursor의 같은 의미 설정 안내(공식 문서로 확인한 것만, 미확인은 미확인) |
| (신규) | 추가 | `templates/github/ci.yml`: `check`·`test` 명령을 부르는 골격 |
| `templates/CODEOWNERS` | 이동 | `profiles/team/CODEOWNERS` |
| `templates/review-status.yml`, `templates/review-status-policy.json` | 이동 | `profiles/review-gate/` |
| `templates/pr-policy.yml` | 이동 | `profiles/pr-conventions/` |
| `templates/repo-baseline.json`, `templates/repo-baseline.core.json` | 이동 | `profiles/hash-copy/` |
| `templates/core/*` | 유지 | 이미 추가됨(AGENTS, CLAUDE, REVIEW, PR 양식, gitignore) |
| `scripts/check_github_settings.py` + 테스트 | 이동 | `tools/`. `tools/apply_github_settings.py:29`의 `sys.path`를 함께 고친다 |
| `scripts/check_review_status.py`, `scripts/pr_author.py` + 테스트 | 이동·수정 | `profiles/review-gate/`. 패밀리 별칭(`:294-343`)·Codex 거부(`:322`) 삭제, 근거 표 필수 칸을 슬림 양식 Review 칸으로 축소 |
| `scripts/workflow_policy.py` + 테스트 | 이동 | `profiles/pr-conventions/` |
| `scripts/check_repo_baseline.py` + 테스트 | 이동 | `profiles/hash-copy/` |
| `tools/apply_baseline.py` + 테스트 | 이동 | `profiles/hash-copy/` |
| `tools/apply_github_settings.py` + 테스트 | 유지 | |
| `tools/post_review_gate.py`, `tools/review_status_policy.py` + 테스트 | 이동 | `profiles/review-gate/`. `post_review_gate.py:62`의 `sys.path` 수정 |
| `tools/test_distribution.py` | 재작성 | 새 구조 검사: 코어에 `.py` 없음, README·POLICY의 상대 링크가 모두 존재, `templates/core` 파일 목록, POLICY 1만 자 이하 |
| `vendor/mattpocock-skills/matt-code-review/` | W9 뒤 삭제 | 소비 레포 manifest가 이 경로를 원본으로 쓴다. 이전 전까지 둔다. 새 기본 리뷰는 `REVIEW.md` |

## 8. 작업 단위와 완료 기준

각 단위는 추적 이슈의 하위 이슈 하나다. 순서대로 한다. "누가"가 소유자인 것은 에이전트가 하지 않는다.

| ID | 작업 | 누가 | 완료 기준 |
| --- | --- | --- | --- |
| W1 | 설계 확정과 이슈 정리 | 에이전트 | 이 문서 §6~§9, 추적 이슈·하위 이슈, 옛 이슈 정리, README 안내. **완료(이 PR)** |
| W2 | 코어 템플릿 | 에이전트 | `templates/core/` 5개 파일. AGENTS.md 60줄 이하, REVIEW.md에 라운드 규칙·배운 규칙 섹션, 모델 선택 규칙 없음. **초안 완료(이 PR)**, 다른 컨텍스트 리뷰 남음 |
| W3 | GitHub 프로필 템플릿 | 에이전트 | §7의 `templates/github/` 행 전부. `repository-settings.json`에 `review/gate` 없음. 에이전트 권한 예시 3종(Claude 파일, Codex·Cursor 안내) |
| W4 | 선택 프로필로 이동 | 에이전트 | §7의 `profiles/` 행 전부 `git mv`. 패밀리 판정·Codex 거부 삭제. 각 프로필 폴더에 "언제 켜는가·켜는 법" README 1쪽 |
| W5 | 문서 재작성·삭제 | 에이전트 | README·POLICY·start·prompts(setup, retro)·CHANGELOG 처리. 삭제 대상 삭제. 개인 운영 메모 제거와 옮길 목록(PR 설명) |
| W6 | 테스트·CI 재구성 | 에이전트 | 남는 도구와 각 프로필 테스트가 새 경로에서 통과. `test_distribution.py` 재작성. `check.yml`이 그 테스트를 실행. 로컬 `python3 -m unittest discover -s <dir>` 출력이 PR Evidence에 있음 |
| W7 | 서버 보호 변경과 병합 | 소유자 | Mac에서 새 `.github/repository-settings.json`으로 `python3 tools/apply_github_settings.py . --apply` 실행 후 `PASS`. 그다음 W2~W6 PR squash 병합 |
| W8 | 빈 프로젝트 적용 시험 | 에이전트, 확인은 소유자 | 빈 디렉터리에 `docs/start.md`대로 적용. 걸린 시간, 막힌 곳, 고친 문서를 이슈에 기록 |
| W9 | 소비 레포 이전 | 레포마다 PR, 병합은 소유자 | smallnext → BGLike → mobile-runtime. 코어 파일 추가, 게이트·해시 복사를 남길지 레포별 결정, 남기지 않으면 manifest·workflow·필수 체크 제거. 셋 끝나면 `vendor/` 삭제 |
| W10 | 마무리 | 에이전트 | 이 문서를 `docs/archive/`로, 추적 이슈 닫기 |

## 9. 이어받는 법 (다른 세션·다른 계정)

1. 저장소를 받고 재설계 브랜치(추적 이슈에 적힌 이름)를 checkout한다. 병합됐으면 `main`.
2. 이 문서 §6(결정)·§7(파일별 처리)·§8(작업 단위)만 읽으면 된다. §1~§3은 근거다. 옛 `POLICY.md`와 `prompts/`는 따르지 않는다(D1).
3. 추적 이슈에서 체크되지 않은 첫 하위 이슈를 고른다. 그 이슈의 완료 기준이 끝나면 이슈에 결과(명령 출력·커밋)를 댓글로 남기고 닫는다.
4. 결정을 바꿔야 하면 코드보다 먼저 §6과 추적 이슈를 고친다.
5. 서버 설정 쓰기, 병합, 브랜치 보호 변경, 다른 저장소 쓰기는 소유자만 한다(W7, W9).
