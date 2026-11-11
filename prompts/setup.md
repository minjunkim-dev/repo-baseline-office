# 셋업 프롬프트

이 파일 하나를 코딩 에이전트에게 첨부한다. 하네스는 무엇이든 된다.

---

이 저장소에 repo-baseline 코어를 적용해 줘. 아래 순서대로 하고, 끝나면 「완료 보고」 형식으로 보고해.

## 지킬 것

- 원본은 공개 저장소 `https://github.com/minjunkim-dev/repo-baseline`의 `main`이다. 저장소 밖 임시 폴더에 clone해서 읽는다.
- 읽을 것은 `templates/core/`, `POLICY.md`, (GitHub이면) `templates/github/`뿐이다. 옛 문서는 읽지 않는다.
- 있는 파일을 덮어쓰지 않는다. 이미 있으면 템플릿 내용을 합치고, 합친 내용을 보고한다.
- 비밀값 파일(`.env*`, 키)을 읽거나 만들거나 커밋하지 않는다.
- `main`에 직접 push하지 않는다. PR을 병합하지 않는다.
- 브랜치 보호·저장소 설정 같은 서버 쓰기는 하지 않는다. 그것은 소유자가 자기 기기에서 한다.
- 모르는 명령을 지어내지 않는다. 확인할 수 없으면 `N/A: <이유>` 또는 "확인하지 않음"으로 적는다.

## 1. 코어 적용

1. 작업 브랜치를 만든다.
2. `templates/core/`에서 복사한다.
   - `AGENTS.md`, `REVIEW.md` → 저장소 루트
   - `CLAUDE.md`는 만들지 않는다. 이미 있으면 내용을 `AGENTS.md`에 합치고 `CLAUDE.md`를 지운다. 지울 수 없는 이유가 있으면 `@AGENTS.md` 한 줄로 바꾼다. Claude Code는 둘 다 있으면 기본 설정에서 `CLAUDE.md`만 읽는다. `.claude/CLAUDE.md`도 같다.
   - `pull_request_template.md` → `.github/pull_request_template.md`
   - `gitignore` → 저장소의 `.gitignore` 뒤에 붙인다(없는 줄만)
3. `AGENTS.md`를 채운다.
   - 프로젝트 이름과 한두 문장 설명: README와 코드에서 읽는다.
   - 명령 4칸(setup/check/test/build): 프로젝트의 빌드 파일(`package.json`, `Makefile`, `go.mod`, `Cargo.toml`, `pyproject.toml`, Gradle·Xcode 설정 등)에서 찾는다. 각 명령을 실제로 돌린다. 없거나 돌릴 수 없으면 `N/A: <이유>`.
   - check 칸이 비면 포매터·린터를 새로 고르지 말고, 있는 도구만 적는다. 새 도구 도입은 제안으로 보고한다.
   - 길잡이 표: 주요 디렉터리와 역할.
   - 60줄 이하로 둔다.
4. `REVIEW.md`를 채운다.
   - 실패로 보는 것: 이 프로젝트의 영역(예: API, UI, 데이터, 문서)별 행.
   - P2 상한: 기본 5.
   - 건너뛸 것: 생성 파일·vendor 경로.
   - 신뢰 경계: 인증·결제·권한·migration 경로를 코드에서 찾아 적는다. 못 찾으면 "없음(확인한 범위: …)".

## 2. GitHub 프로필 (원격이 GitHub일 때만)

`git remote -v`가 GitHub를 가리키지 않으면 이 단계를 건너뛰고 보고에 적는다.

1. `templates/github/README.md`를 읽고 그대로 따른다. 거기 없는 값을 새로 고르지 않는다.
2. 파일로 두는 것만 한다: CI 골격(`.github/workflows/`), Dependabot 설정, 에이전트 권한 설정 예시, 저장소 설정 기준선 JSON, `SECURITY.md`.
3. CI 골격은 `AGENTS.md`의 check·test 명령을 부르게 채운다.
4. 서버에 설정을 적용하는 명령(`--apply` 등)은 실행하지 않는다. 소유자가 실행할 명령을 보고에 적는다.

`.github/workflows/**`, 저장소 설정 파일, 하네스 설정(`.claude/` 등)은 신뢰 경계다(`POLICY.md` §4). 이 단계를 했으면 이 PR은 되돌리기 어려움이다.

## 3. 검증

모두 실제로 돌리고 출력을 보고에 붙인다.

- `grep -nE '<[^>]+>' AGENTS.md REVIEW.md`: 템플릿 빈칸(`<프로젝트 이름>`, `<명령>`, `<영역>` 등)이 남지 않았다. `N/A: <이유>` 안내와 「배운 규칙」의 형식 예시는 남아도 된다.
- 명령 4칸: 각각 실행 결과(성공·실패) 또는 `N/A: <이유>`.
- `git check-ignore -q .env && git check-ignore -q .env.local && echo ignored`: `ignored`가 나온다. 예외 줄(`!.env`)이 있거나 이미 커밋된 파일이면 나오지 않는다.
- `git status`: 비밀값 파일이 스테이징되지 않았다.
- `CLAUDE.md`·`CLAUDE.local.md`가 없거나 `@AGENTS.md` 한 줄이고, `.claude/CLAUDE.md`가 없거나 `@../AGENTS.md` 한 줄이다. 상위 폴더에 `CLAUDE.md`가 있으면 보고에 적는다.
- GitHub 프로필을 했으면: workflow 파일의 YAML이 파싱된다(쓸 수 있는 도구로). 확인하지 못했으면 그렇게 적는다. `SECURITY.md`가 `.github/`, 루트, `docs/` 중 한 곳에만 있고, 그 파일에 `grep -n 'OWNER/REPO'`가 아무것도 출력하지 않는다.

## 4. PR 열기

커밋하고 PR을 연다. 본문은 `.github/pull_request_template.md` 양식이다.

- Author: 너의 도구 / 모델.
- Summary: 코어 적용(했으면 GitHub 프로필도). 완료 기준: 템플릿 빈칸이 없다, `.env`가 무시된다, 비밀값이 스테이징되지 않았다, `CLAUDE.md`가 없거나 `@AGENTS.md` 한 줄이다, (GitHub 프로필을 했으면) workflow YAML이 파싱된다. 전에 통과하던 프로젝트 명령은 그대로 통과한다.
- Evidence: 3단계 출력. 확인하지 않은 범위.
- Merge Danger: 코어만이면 되돌리기 쉬움, GitHub 프로필을 했으면 되돌리기 어려움과 걸린 경로.
- Review: 비워 둔다. 리뷰는 다른 컨텍스트가 원본 저장소의 `prompts/review.md`로 한다.

## 완료 보고

아래 형식으로 짧게 보고한다.

```
적용: 코어 [완료|부분] / GitHub 프로필 [완료|건너뜀(이유)]
PR: <링크>
명령 4칸: setup=<결과> check=<결과> test=<결과> build=<결과>
합친 기존 파일: <없음|목록>
Door: <되돌리기 쉬움|되돌리기 어려움(경로)>
소유자가 할 일: <서버 설정 적용 명령, 리뷰 요청, 병합>
제안(반영 안 함): <새 린터 등>
확인하지 않은 것: <목록>
```
