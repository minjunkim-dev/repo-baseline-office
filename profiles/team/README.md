# team 프로필

선택 프로필이다. 사람이 둘 이상이고, 위험한 경로를 바꿀 때 정해진 사람의 승인을 받게 한다.

## 언제 켜는가

- 쓰기 권한이 있는 사람이 둘 이상일 때.
- 결제·개인정보·사용자 다수처럼 되돌리기 어려운 변경이 잦을 때. 이때는 merge queue와 단계 배포도 같이 검토한다.

혼자면 켜지 않는다. CODEOWNERS 승인을 필수로 하면 혼자서는 병합하지 못한다.

## 켜는 법

1. `CODEOWNERS`를 `.github/CODEOWNERS`로 복사한다.
2. `@REPLACE-OWNERS`를 쓰기 권한이 있는 두 명 이상, 또는 조직 레포라면 GitHub 팀(`@org/team`)으로 바꾼다.
3. 프로젝트의 의존성 manifest·lockfile·신뢰 경계 경로(인증, 결제, 마이그레이션 등)를 아래에 더한다. 쓰지 않는 프로필의 경로(`scripts/workflow_policy.py` 등)는 지워도 된다.
4. `.github/repository-settings.json`의 브랜치 보호에서 `required_approving_review_count`(1~2)와 `require_code_owner_reviews`를 켜고, 소유자 기기에서 `python3 <repo-baseline>/tools/apply_github_settings.py <project> --apply`로 적용한다.
