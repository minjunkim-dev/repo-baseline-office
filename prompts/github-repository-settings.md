# 범용 GitHub 저장소 설정 프롬프트

이 프로젝트의 GitHub 서버 설정을 점검하고 승인된 범위에서 적용해줘.
1인 개발 기준이다. 실제 저장소의 언어·CI·기본 브랜치·배포 방식에 맞춰 적용해. 이 문서의 main은 실제 기준 브랜치를 뜻한다.
별도 컨텍스트의 자체 리뷰를 기본으로 한다. 공개 배포·production 변경·유료 서비스 활성화는 금지한다.
구체적인 공통값은 `minjunkim-dev/repo-baseline`의 `POLICY.md`와 `templates/`를 따른다. 이 문서는 절차와 판단 기준만 정한다. 값을 새로 고르지 말고, 다르게 둬야 하면 허용 예외로 기록해.

## 1. 두 프롬프트의 순서와 책임

같은 채팅에서 이 GitHub 설정 프롬프트를 먼저 요청한다. 이어 PR·CI/CD 셋업 프롬프트를 요청한다. 두 파일을 처음부터 함께 첨부해 순서대로 적용하라고 요청해도 된다.
GitHub 최종 확인은 두 번째 작업의 마무리다. 세 번째 프롬프트를 요구하지 마.

| 담당 프롬프트 | 책임 |
| --- | --- |
| GitHub 설정 | 서버 설정 기준·필요한 App 접근·설정 재조회 |
| PR·CI/CD 셋업 | 저장소 문서·코드·workflow·설정 파일·검사기·독립 리뷰·실행 검증 |

1. 초기 점검에서 현재 상태를 기록해. 실행 근거가 있는 기본 설정을 적용해.
2. 저장소 파일 변경이나 새 CI 실행 근거가 필요한 항목은 인계 목록에 기록해. 문서 정리·workflow 생성·검사기 구현·CI 실패 시험을 이 단계에서 중복 실행하지 마.
3. 두 번째 프롬프트에서 파일 변경과 실제 PR 검증을 마친 뒤 이 문서의 서버 설정 기준으로 보류 항목을 완료해. 필요한 설정과 보호를 재조회한 뒤 위험별 병합과 main 검증을 마쳐.

이 프롬프트만 요청받았으면 초기 점검과 적용 가능한 설정을 완료해. 인계 목록을 보고하고 다음 요청을 계속 대기하지 마. 전체 셋업이 완료됐다고 보고하지 마.

## 2. 초기 점검과 인계 기록

1. Git remote에서 owner/name을 확인해. repository ID·공개 여부·기본 브랜치·권한·지원 기능을 기록해.
2. 열린 PR·worktree·미커밋 변경을 확인해. 다른 작업자의 변경을 보존해.
3. branch push·PR 생성·main 병합이 기존 공개 자동 배포를 유발하는지 확인해. 배포가 발생하는 동작은 보류해. 기존 배포 연결이나 보호를 임의로 해제하지 마.
4. 현재 workflow·App의 대상 저장소 접근·PR 봇 응답·check run·branch protection·ruleset을 확인해. 과거 댓글이나 App 설치만으로 현재 자동 실행을 판단하지 마.
5. ChatGPT/Codex Cloud 계정·서비스 저장소 목록은 탐색하지 마. 저장소와 무관한 계정 연결과 OAuth를 변경하지 마. 지원 여부가 불확실하면 최신 공식 문서를 확인해.

다음 정보를 같은 채팅에 인계 기록으로 남겨. 필요한 경우 로컬 기록 파일을 사용해. 비밀값은 기록하지 마.

- 대상 repository ID·owner/name·기본 브랜치·조회 시각
- 변경 전 설정과 적용·유지·보류 항목
- 실제 CI 이름·publisher/App ID·유효한 head/base·run/attempt와 결과
- 파일 변경이 필요한 항목의 목적·완료 조건·예상 영향
- 권한 확대 등 사람이 승인할 변경과 공개 배포 차단 사유

## 3. General과 기본 브랜치 보호

| 설정 | 목표 |
| --- | --- |
| Squash merging | On |
| Merge commits / Rebase merging | Off / Off |
| Squash 기본 메시지 | PR 제목과 본문 |
| 병합 후 브랜치 자동 삭제 / 업데이트 제안 | On / On |
| Allow auto-merge | On |
| PR 필수 / 관리자에게도 보호 적용 | On / On |
| 실제 필수 CI / 최신 기준 브랜치 검사 | On / On |
| 선형 이력 / 리뷰 대화 해결 | On / On |
| Force push / 보호 브랜치 삭제 | Off / Off |
| GitHub 필수 승인 인원 | 0명 |

1인 개발에서 본인 PR에 다른 사람의 승인 1명을 강제하지 마. 승인 0명이어도 한쪽 문과 넓은 영향의 변경은 사람이 최종 커밋을 승인한다.
기존 협업·release 운영과 충돌하면 근거를 확인해. 다른 목적의 보호를 삭제하거나 보호 공백을 만들지 마.
branch protection·ruleset·상속 규칙의 중복과 충돌을 확인해. 관리자 우회와 일시적인 보호 해제로 병합하지 마.
Allow auto-merge는 사용 가능한 상태로만 둬. 모든 PR에 자동 병합을 예약하거나 자동 병합 workflow를 만들지 마.
Release를 사용하는 저장소는 미래 공개 Release의 immutability 지원과 영향을 확인해. 설정 변경과 실제 Release 생성·공개를 구분해.

## 4. 실제 CI와 필수 체크 연결

1. 다른 프로젝트의 검사 이름을 복사하지 마. 실제 PR의 최종 head에서 실행과 성공을 확인한 검사만 필수 체크로 연결해. 가능하면 실제 publisher/App ID로 제한해.
2. aggregate가 선택된 실제 하위 job의 결과를 반영하는지 확인해. 실패·취소·누락은 성공으로 취급하지 마. 불필요한 job의 skip은 명시된 기존 정책을 확인해.
3. head·base·run ID·최신 attempt를 대조해. 이름이 같다는 이유로 과거 결과나 다른 출처의 결과를 사용하지 마.
4. 새 CI가 없거나 실행되지 않았으면 필수 이름을 추측해 등록하지 마. 파일 구현과 실행 검증을 PR·CI/CD 작업에 인계해.
5. 기존 필수 체크를 교체하면 전환 계획을 먼저 확인해. 새 검사가 검증될 때까지 유효한 기존 검사를 유지해. 보호 우회나 검사 실패 은폐로 이름 변경을 처리하지 마.

빌드·테스트·린트·보안·dependency 검사와 trusted aggregation은 보존해. 검사 구현과 CI 실패 복구는 PR·CI/CD 프롬프트의 책임이다.

## 5. Actions 권한과 의존성

| 설정 | 목표 |
| --- | --- |
| 기본 GITHUB_TOKEN | 읽기 전용 |
| Actions의 PR 생성·승인 허용 | Off |
| 외부 fork 승인 | 지원 범위에서 모든 외부 기여자 |
| 허용 Actions | 실제 필요한 공식·외부 Actions만 |
| 전체 commit SHA 고정 요구 | 지원하면 On |

기존 workflow와 reusable workflow의 직접·간접 의존성을 확인해. 필요한 Action을 허용 목록에서 제거하지 마.
사용하지 않는 AI 리뷰 Action 예외는 정리해. 파일의 SHA 고정·job별 최소 권한·credential persistence 보완은 PR·CI/CD 작업에 인계해.
외부 PR 코드를 높은 권한·Secret 환경에서 실행하지 마. pull_request_target의 checkout과 실행 경계를 확인해.
새 쓰기 권한·Secret 접근·App 접근 확대·신뢰 경계 변경은 사람 승인이 필요하다. 파일 변경은 최종 head와 검증 근거를 제시해. 서버 변경은 변경 전후 값·대상·영향을 구체적으로 제시해. 파일 승인은 승인받은 최종 head와 영향 범위가 같을 때 재사용해. 이미 승인받은 동일한 서버 변경은 다시 승인받지 마.

## 6. 보안 기능·Dependabot·CodeQL

공개 여부·요금제·기능 지원을 확인해. 사용 가능한 Dependency graph·Dependabot alerts·security updates·Secret scanning·Push protection을 켜.
유료 기능을 구매하거나 실제 비밀값으로 시험하지 마. 미지원·조회 불가를 구분해 기록해.
Dependabot version updates는 GitHub Actions와 실제 생태계를 대상으로 `POLICY.md` §2를 따라. `.github/dependabot.yml`은 손으로 쓰지 말고 manifest의 `ecosystems`에 실제 생태계를 적은 뒤 `tools/apply_baseline.py`로 생성해. 일정·라벨·제목·상한(설정하지 않음, 기본 5)·`codeql-action` 그룹을 임의로 바꾸지 마. 설정 파일 보완은 PR·CI/CD 작업에 인계해.
SHA로 고정한 Action에는 Dependabot alert가 생기지 않는다. Action의 보안 수정은 정기 업데이트로만 들어온다. 열린 봇 PR이 상한을 채워 새 업데이트를 막고 있는지 확인해.

CodeQL은 실제 언어·runner OS·SDK·compiler·toolchain과 빌드 구조의 공식 호환성을 확인해.
default setup과 advanced setup을 중복 구성하지 마. 기본은 default setup이다. 빌드 명령이나 toolchain 지정이 필요할 때만 advanced setup을 선택해. 필요한 분석 방식과 build 명령의 요구조건을 인계해.
advanced setup에서 `github/codeql-action/*`을 SHA로 고정하면 모든 단계가 같은 commit을 써야 한다. 분리된 업데이트 PR은 분석을 실패시킨다.
집계 `CodeQL` check는 분석이 실패해도 `neutral`일 수 있다. GitHub는 필수 check의 `neutral`을 통과로 본다. 분석 실패로 병합을 막아야 하면 분석 job 결과를 필수 게이트에 연결하는 방안을 인계해.
제품 SDK를 임의로 낮추지 마. 미지원 언어·toolchain의 공백은 기록하거나 Issue로 추적해. 기존 빌드·테스트·보안 검사는 보존해.
실제 분석·결과 업로드·ref·commit SHA·언어·category를 확인해. 실행 성공과 경고 0건, PR 변경분과 main 전체 분석을 구분해.
새 CodeQL을 필수로 만들려면 PR과 main의 실제 결과를 확인해. 첫 main 결과가 아직 없으면 초기 필수 체크로 등록하지 말고 병합 후 검증에서 판단해. 기존 필수 품질 게이트는 유지해.
경고의 도달 가능한 경로를 검토하고 실제 결함 수정은 PR·CI/CD 작업에 맡겨. 오탐 근거를 기록해. 검사를 약화하거나 경고를 자동 dismissal하지 마.

## 7. 자체 리뷰와 기존 서비스 연결

별도 컨텍스트의 자체 리뷰를 기본으로 해. 실제 PR diff·코딩 규칙·확정 완료 조건으로 리뷰하고, 확실한 결함은 수정·커밋하는 절차를 PR·CI/CD 작업에 인계해.
기존 외부 리뷰 서비스·App·workflow가 있으면 대상 저장소에서 사용하는 기능과 필수 체크 의존성을 확인해. 불필요한 연결의 정리는 영향 범위를 제시하고 승인된 범위에서 수행해. 공유 App의 다른 저장소 접근과 로컬 Git·에이전트 사용을 보존해.
workflow·스크립트 변경은 PR·CI/CD 작업에 인계해. 결정적인 보안·dependency 검사와 로컬 독립 리뷰를 유지해.
공개 저장소는 CodeRabbit 무료 플랜 GitHub App을 `POLICY.md` §5의 외부 리뷰로 쓴다. 이 연결은 정리 대상이 아니다. 설치는 사람이 승인하고, 필수 체크·Autofix·유료 기능은 켜지 마. 그 밖의 새 리뷰 서비스를 연결하거나 유료 기능을 켜지 마.
Copilot을 리뷰 경로로 사용하지 않으면 MCP tools Off·PR 승인 Off·자동 리뷰 ruleset 없음으로 유지해.

## 8. 배포 승인·Environment 기준

실제 웹·모바일·CLI·게임·라이브러리의 기존 배포 단위를 확인해. 동일한 Release workflow를 모든 프로젝트에 강제하지 마.
산출물이 필요하면 수동 미공개 Draft 또는 동등한 미공개 artifact의 요구조건을 인계해. workflow·version/source 입력 검증·패키징·다운로드 시험은 PR·CI/CD 프롬프트가 맡는다.
Environment는 실제 승인·Secret·배포 경계가 필요할 때만 구성해. 해당 job에 environment가 연결돼야 보호가 적용된다. 1인 개발자가 자신의 실행을 승인할 수 없는 승인 조합을 만들지 마.
새 쓰기 권한과 신뢰 경계는 사람 승인 후 반영해. 이 GitHub 초기 설정 단계에서는 Draft 생성과 공개 배포를 실행하지 마. 미공개 Draft의 실제 생성은 두 번째 프롬프트의 명시적 실행 조건을 따른다.

## 9. 설정 기준선과 읽기 전용 감사

변경 전후를 API 또는 실제 화면으로 기록해. 저장 후 재조회해. 완료 판정은 최신 재조회 결과를 사용해.
가능하면 기대 기준선과 GET 전용 감사 도구의 요구조건을 인계해. repository ID·owner/name·필수 필드·자료형·실제 체크·publisher를 확인하게 해.
기준선과 감사 도구 파일의 구현은 PR·CI/CD 작업이 맡는다. 감사 도구는 설정 쓰기를 수행하지 않는다. 설정 적용 작업과 읽기 전용 감사를 구분해.
서버 적용은 `repo-baseline`의 `tools/apply_github_settings.py`로 해. 기준선은 `templates/repository-settings.json`에서 시작해. 먼저 쓰기 없이 계획을 출력해 변경 전후를 제시하고, 승인 후 `--apply`로 적용해. 필수 체크는 §4로 검증한 것만 기준선에 적어.
조회 오류·누락을 PASS로 처리하지 마. drift·조회 불가·비해당을 구분해. 기능 미지원은 `repo-baseline`의 `docs/github-settings-profile.md`의 근거 있는 예외로 인계해. 403·404만으로 미지원이라고 판단하지 마. LIMITED는 전체 보호 완료가 아니다.
기준선 파일은 GitHub 네이티브 자동 적용 파일이 아니다. main의 실제 workflow·설정 파일과 서버 적용을 대조해. 필요하면 Git blob SHA를 확인해.
기준선이 workflow blob SHA를 고정하면 그 workflow를 바꾸는 PR(Dependabot 포함)은 기준선도 함께 갱신해야 한다. 병합 후 감사에서야 drift를 발견하지 않도록 PR CI의 오프라인 검사를 요구해. 감사 도구는 `repo-baseline`의 `scripts/check_github_settings.py`를 복사해 쓴다.
기본 Actions token의 권한을 늘려 감사 도구를 억지로 필수 CI에 넣지 마. 로그·산출물 보관과 cache 정책은 실제 필요와 기존 운영을 확인하고 유지해.

## 10. 초기 완료와 최종 적용

첫 요청은 적용·유지·보류·미확인과 인계 목록을 보고하고 마쳐. 파일 구현·독립 리뷰·복구 시험을 실행한 것으로 표시하지 마.

PR·CI/CD 작업에서 다음 근거를 받은 뒤 필요한 최종 서버 적용을 진행해.

1. 같은 저장소·유효한 기존 정책과 현재 권한인지 확인해. 새 PR의 최종 head·base와 실제 체크 이름·publisher·run/attempt를 확인해.
2. 검증된 검사만 필수로 등록해. 보류된 설정과 변경에 영향받는 기준선을 완료하고 재조회해. 기존에 유효한 설정·근거를 중복 변경하거나 재실행하지 마.
3. 보호가 적용된 상태에서 두 번째 프롬프트의 독립 리뷰·위험별 승인·정확한 최종 head 조건으로 병합해. 기존 보호를 우회하지 마.
4. main SHA·CI와 필요한 CodeQL의 결과를 확인해. 설정 기준선·main 파일·실제 실행을 대조해. 진행 중 결과는 진행 중으로 기록해.

최종 보고는 설정 적용·파일 준비·PR 검증·main 반영·미공개 Draft 실행·공개 배포를 구분해.
각 항목은 PASS·FAIL·보류·미확인·비해당을 근거와 함께 기록해. 필수 품질 게이트가 미검증이면 전체 완료로 표시하지 마. 선택 기능과 공식 미지원은 필요한 잔여 항목으로만 보고해.
서버 설정의 승인 0명은 사람 승인 경계를 없애지 않는다. 위험별 승인과 병합 실행의 상세 기준은 PR·CI/CD 프롬프트가 관리한다.
한국어로 간단명료하게 보고해. 재현 가능한 설정 조회 명령도 제공해.
