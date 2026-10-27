# HANDBOOK

같은 지적이 두 번 나오면 `MEMORY.md`에서 이 파일의 정식 규칙으로 올린다.

## 복사 경계

사무실 세션은 `scripts/`와 `templates/`를 수정하지 않는다. 기준 변경은 `minjunkim-dev/repo-baseline`에서 하고, 제품에는 그 원본을 다시 적용한다.

## 배포 위임

#### 승인 생략

reviewer 검수가 통과하면 leader는 사람 승인을 기다리지 않고 `tools/deploy.py --target prod`로 production 배포를 진행해도 된다. 배포 대상 이름은 `prod`로 통일한다.
