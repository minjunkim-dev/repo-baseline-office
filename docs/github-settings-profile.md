# GitHub 설정 기준선과 기능 지원

프로젝트의 `.github/repository-settings.json`은 기대값과 감사 범위를 기록한다. 공통 검사기는 GET만 사용한다. 서버 적용은 원본의 `tools/apply_github_settings.py`가 같은 기준선으로 한다. 시작점은 원본의 `templates/repository-settings.json`이다.

## 적용 도구

새 프로젝트의 채울 값은 README "새 프로젝트에 적용" 7단계를 따른다.

1. 기본 실행은 읽기만 한다. 기준선과 다른 항목마다 `DIFF: 경로: 현재 값 -> 기준값`과 쓰기 요청 `PLAN`을 출력한다. 바꿀 것이 있으면 종료 코드 1이다.
2. 사람이 계획을 승인하면 `--apply`로 실행한다. 다시 조회해 그때 다른 항목만 쓰고, 같은 검사기로 감사한다. 계획을 본 뒤 다른 사람이 설정을 바꿨다면 적용 출력이 계획과 다를 수 있으니 출력도 확인한다.
3. 쓰기는 항목 단위다. 병합 설정 하나가 다르면 저장소 항목의 다른 기준값도 함께 다시 보낸다.
4. 공개 여부·ruleset·CodeQL workflow 파일, 감사 도구가 요구하지 않는 필드는 쓰지 않고 `MANUAL`로 보고한다. 기준선이 관리하지 않는 브랜치 보호(서명 커밋·push 제한·브랜치 생성 차단·fork 동기화·리뷰 우회와 승인 무효화 권한 목록)가 설정돼 있으면 보호를 다시 쓰지 않고 `MANUAL`로 보고한다. 보호를 쓰면 이 값들이 초기화되기 때문이다. CodeQL advanced 기준선이면 workflow가 활성화되고 기본 브랜치의 파일이 기준선의 pin과 같아질 때까지 default setup을 끄지 않는다. `MANUAL`이 하나라도 남으면 사람이 처리할 일이 남은 것이므로, 다른 항목의 감사 결과와 관계없이 종료 코드는 1이다.
5. 예외로 선언한 항목은 쓰지 않는다. 예외가 있으면 결과는 `PASS`가 아니라 `LIMITED`다.
6. 계획 단계에서 도구가 쓰는 설정 항목의 조회가 404면 "아직 설정 안 됨"으로 보고 쓰기 대상에 넣는다. 저장소 자체의 조회가 404면 멈추고, `MANUAL` 항목은 404여도 `MANUAL`로 보고한다. 403 같은 다른 오류는 아무것도 쓰지 않고 실패로 끝난다. 기준선 오류(schema·저장소 이름·브랜치·남은 `REPLACE` 값)는 조회 전에 멈춘다. `--apply`가 쓴 뒤의 감사에서 조회가 실패하면 쓰기는 이미 끝났으므로, 출력된 쓰기 목록을 보고 계획을 다시 실행한다.
7. 쓰기가 중간에 실패하면 이미 쓴 요청과 결과를 알 수 없는 요청(시간 초과 등)을 출력하고 멈춘다. 계획을 다시 실행해 현재 상태를 본다.
8. CodeQL default setup은 비동기로 켜지므로 최대 2분 기다린 뒤 감사한다.
9. 기준선 밖의 설정(Grouped security updates, private vulnerability reporting, Wiki 등)은 다루지 않는다.

## 기존 기준선과 예외

기존 `schema_version: 1`과 `expected` 형식은 유지한다. 지원되는 항목은 모든 필수 필드와 자료형을 명시한다. default CodeQL은 `codeql.state: configured`, advanced CodeQL은 `not-configured`와 workflow·blob pin을 함께 기록한다.

요금제·공개 여부·언어·기능 사용 여부로 적용할 수 없는 항목에만 선택적 `exceptions`를 쓴다. 다음은 전체 파일이 아닌 예외 부분의 예시다.

```json
{
  "exceptions": {
    "protection": {
      "status": "unsupported",
      "reason": "현재 비공개 저장소의 요금제가 브랜치 보호를 제공하지 않음",
      "evidence": "공식 protected branches 문서와 저장소 공개 여부·요금제 확인 기록"
    },
    "codeql": {
      "status": "not_applicable",
      "reason": "프로젝트에 CodeQL 지원 언어가 없음",
      "evidence": "공식 지원 언어 목록과 현재 소스 언어 조사 기록"
    }
  }
}
```

1. 실제 저장소와 최신 공식 지원 범위를 대조하고 근거에 문서 URL·확인 시점·프로젝트 조사 기록을 남긴다. `unsupported`는 기능 미지원, `not_applicable`은 기능이 이 프로젝트에 해당하지 않는 경우다. 권한 부족·원인 불명은 예외로 등록하지 않는다.
2. 예외 항목은 `expected`에서 제거한다. 같은 항목을 기대값과 예외에 동시에 넣거나, 부모·자식을 겹쳐 제외하면 스키마 오류다. 생략만 하고 예외를 쓰지 않아도 오류다.
3. 예외 경로는 API 단위의 기능 항목(`protection`, `rulesets`, `actions`, `allowed_actions`, `workflow_token`, `fork_policy`, `immutable_releases`, `dependabot_alerts`, `codeql`), `actions.sha_pinning_required`, 세 가지 `repository.security_and_analysis.<기능>.status`다. 저장소 ID·이름·기본 브랜치·공개 여부·병합 정책은 예외로 지울 수 없다.
4. `codeql` 전체 예외에는 `codeql_workflow`와 `codeql_main_source`도 넣지 않는다. 두 항목은 advanced setup에서만 함께 필요하다. 중첩 security 필드 예외는 그 필드만 제외한다. 다른 보안 필드의 누락·불일치는 계속 실패한다.
5. 예외 추가·변경은 설정 정책 변경으로 리뷰한다. 프로젝트의 `docs/REPOSITORY_SETUP.md`에도 사유를 연결한다. 지원·언어·요금제·공개 여부가 바뀌면 재검토하고, 지원되면 예외를 제거한 뒤 실제 설정을 확인한다.

예외는 사람이 확인한 감사 범위 선언이다. 검사기가 근거의 진위를 판정하거나 서버 미지원을 증명하지 않는다. 예외가 없는 요청의 403·404·누락 필드는 자동으로 미지원으로 바뀌지 않는다. 현재 설정과 다른 기대값을 단순히 예외로 옮겨 drift를 숨기지 않는다.

## 실행 결과와 CI

| 결과 | 종료 코드 | 뜻 |
| --- | --- | --- |
| `PASS` | 0 | 모든 필수 기대값을 조회했고 일치함 |
| `LIMITED` + `UNSUPPORTED` / `NOT_APPLICABLE` | 0 | 확인한 항목은 일치하나 명시된 예외는 검사 범위 밖임. 전체 보호 완료가 아님 |
| `DRIFT` | 1 | 지원되는 기대값과 실제 값이 다르거나 필드가 누락됨 |
| `UNVERIFIED` | 2 | 기준선 오류·권한 부족·API 오류 등으로 검증 불가 |

`LIMITED`는 승인된 감사 범위를 검사하는 CI에서 성공으로 처리할 수 있다. 필수 보호·전체 보안 검증이 완료됐다는 근거로 사용하지 않는다. 예외와 결과 원문을 인계 보고에 남기고 위험별 병합 기준을 적용한다.

소비 프로젝트의 PR CI에서는 최소한 다음 두 검증을 연결한다.

```sh
python3 scripts/check_repo_baseline.py
python3 -m unittest discover -s scripts -p 'test_*.py'
```

첫 명령은 복사 파일의 누락·변조·manifest 오류를 검사한다. 테스트는 합성 fixture로 API 비교 동작을 검사하고, 실제 프로젝트 기준선이 있으면 CodeQL workflow의 blob pin도 오프라인 검사한다. 서버 감사 `python3 scripts/check_github_settings.py`는 별도 권한이 필요한 읽기 작업이다. PR token 권한을 늘려 합성 테스트를 실제 서버 감사로 바꾸지 않는다.

공식 근거: [브랜치 보호의 요금제 지원](https://docs.github.com/en/rest/branches/branch-protection#get-branch-protection), [CodeQL 지원 언어](https://codeql.github.com/docs/codeql-overview/supported-languages-and-frameworks/). 실제 적용 때 최신 문서를 다시 확인한다.
