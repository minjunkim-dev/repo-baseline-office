# GitHub 프로필

코어(`templates/core/`)를 적용한 프로젝트를 GitHub에 올릴 때 쓴다. 기본 경계는 브랜치 보호 + 필수 CI + 소유자가 정하는 병합이다(POLICY §5).

| 파일 | 복사할 곳 | 메모 |
| --- | --- | --- |
| `ci.yml` | `.github/workflows/ci.yml` | `check`·`test` 단계를 `AGENTS.md`의 명령으로 바꾼다. 바꾸기 전에는 실패한다 |
| `dependabot.yml` | `.github/dependabot.yml` | 패키지 관리자마다 `dependabot-ecosystem.yml`의 블록을 붙인다 |
| `repository-settings.json` | `.github/repository-settings.json` | `REPLACE` 값을 채운다 |
| `SECURITY.md` | 저장소 루트 | GitHub은 `.github/`, 루트, `docs/` 순서로 이 파일을 찾는다. 셋 중 하나에 이미 있으면 그 파일에 합친다. `OWNER/REPO`를 채운다. 공개 저장소는 비공개 취약점 보고를 켠 뒤 이 파일을 병합한다. 비공개 저장소는 비공개 취약점 보고와 보안 권고가 없으므로 보고 안내·링크·권고 목록 줄을 소유자에게 비공개로 연락할 경로로 바꾼다 |
| `agents/` | 하네스별 | `agents/README.md` |

## 적용 순서

1. 위 파일을 복사하고 `ci.yml`의 두 단계를 채운다.
2. PR 하나를 열어 `ci` job이 실제로 성공하는 것을 본다.
3. `repository-settings.json`의 `repository`, `repository_id`(`gh api repos/OWNER/NAME --jq .id`), `visibility`, 필수 체크 `context`(2의 job 이름, 기본 `ci`), `patterns_allowed`를 채워 병합한다.
4. 소유자가 자기 기기에서 계획을 본다. 읽기만 한다.

   ```sh
   python3 <repo-baseline>/tools/apply_github_settings.py <project>
   ```

5. 계획을 승인하면 `--apply`를 붙여 다시 실행하고, 출력이 `PASS`인지 본다.

에이전트는 4·5를 실행하지 않는다. 도구는 소유자의 `gh` 로그인으로 `gh api`를 부른다.

## `apply_github_settings.py`

- 기본 실행은 다른 항목마다 `DIFF: 경로: 현재 값 -> 기준값`과 쓰기 요청 `PLAN`을 출력한다. 바꿀 것이 있으면 종료 코드 1이다.
- `--apply`는 다시 조회해 그때 다른 항목만 쓰고 같은 검사기로 감사한다. 쓰기는 항목 단위다.
- 남은 `REPLACE` 값, schema·저장소 이름·브랜치 오류는 조회 전에 멈춘다. 403 같은 오류는 아무것도 쓰지 않고 실패한다. 쓰기가 중간에 실패하면 쓴 요청을 출력하고 멈춘다. 계획을 다시 실행해 현재 상태를 본다.
- 공개 여부·ruleset·CodeQL workflow 파일, 기준선이 관리하지 않는 브랜치 보호(서명 커밋·push 제한 등)는 쓰지 않고 `MANUAL`로 보고한다. `MANUAL`이 남으면 종료 코드 1이다.
- CodeQL default setup은 비동기로 켜지므로 최대 2분 기다린 뒤 감사한다.

| 결과 | 종료 코드 | 뜻 |
| --- | --- | --- |
| `PASS` | 0 | 모든 기대값을 조회했고 일치함 |
| `LIMITED` | 0 | 확인한 항목은 일치하나 선언한 예외는 검사 밖. 보호 완료가 아님 |
| `DRIFT` | 1 | 기대값과 실제 값이 다르거나 필드가 없음 |
| `UNVERIFIED` | 2 | 기준선 오류·권한 부족·API 오류로 검증 못 함 |

## 예외

요금제·공개 여부·언어 때문에 적용할 수 없는 항목만 `exceptions`에 적고 `expected`에서 뺀다. 권한 부족이나 원인 불명은 예외가 아니다. 근거에는 공식 문서 URL과 확인 날짜를 적는다.

```json
"exceptions": {
  "codeql": {
    "status": "not_applicable",
    "reason": "CodeQL 지원 언어가 없음",
    "evidence": "https://codeql.github.com/docs/codeql-overview/supported-languages-and-frameworks/ (확인일)"
  }
}
```

- `status`는 `unsupported`(기능 미지원) 또는 `not_applicable`(이 프로젝트에 해당 없음)이다.
- 예외로 쓸 수 있는 항목은 `protection`, `rulesets`, `actions`, `allowed_actions`, `workflow_token`, `fork_policy`, `immutable_releases`, `private_vulnerability_reporting`, `dependabot_alerts`, `codeql`, `actions.sha_pinning_required`, `repository.security_and_analysis.<기능>.status`다. 저장소 ID·이름·기본 브랜치·공개 여부·병합 정책은 뺄 수 없다.
- 같은 항목을 기대값과 예외에 함께 두면 스키마 오류다.
- 비공개 취약점 보고는 공개 저장소에만 있다. 비공개 저장소는 `expected`에서 `private_vulnerability_reporting`을 빼고 예외에 `"private_vulnerability_reporting": {"status": "unsupported", "reason": "비공개 저장소", "evidence": "GET private-vulnerability-reporting이 404"}`를 둔다. 빼지 않으면 검사가 `UNVERIFIED`로 멈춘다.
