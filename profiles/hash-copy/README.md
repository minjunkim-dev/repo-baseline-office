# hash-copy 프로필

선택 프로필이다. 이 저장소의 파일을 소비 레포에 복사하고 sha256을 기록해서, 복사본을 손으로 고치면 CI가 잡게 한다. 코어 적용은 `cp` 몇 번이고 이 프로필이 필요 없다(`docs/archive/redesign-2026-11.md` D6).

## 언제 켜는가

- 공통 검사기(pr-conventions 등)를 여러 레포에 똑같이 두고, 레포마다 몰래 고쳐지는 것을 막고 싶을 때.
- 이 저장소를 고칠 때마다 소비 레포를 한 명령으로 맞추고 싶을 때.

복사하는 파일이 코어 몇 개뿐이면 켜지 않는다. 손으로 `cp`하는 편이 짧다.

## 켜는 법

1. 소비 레포에 `.github/repo-baseline.json`을 둔다. `repo-baseline.core.json`(PR 양식만) 또는 `repo-baseline.json`(검사기 묶음)을 복사해 시작한다. 키는 소비 레포의 경로, `source`는 이 저장소의 경로다. 키가 프로젝트 밖이나 `.git/` 안을 가리키면 멈춘다.
2. 이 저장소의 깨끗한 checkout에서 실행한다. 커밋하지 않은 변경이 있으면 멈춘다.

```bash
python3 profiles/hash-copy/apply_baseline.py <소비 레포 경로>
```

   파일을 복사하고 `source_commit`과 각 파일의 `sha256`을 manifest에 쓴다. `--check`는 쓰지 않고 다른 파일만 보고한다.
3. 소비 레포 CI에서 `python3 scripts/check_repo_baseline.py`를 돌린다(manifest에 `scripts/check_repo_baseline.py`가 들어 있어야 한다). 해시가 다르면 실패한다. `.mcp.json`에 비밀값처럼 보이는 문자 그대로의 값이 있어도 실패한다.
4. `ecosystems`가 있는 항목은 복사 대신 생성한다. `templates/github/dependabot.yml` 뒤에 생태계마다 `profiles/hash-copy/dependabot-ecosystem.yml` 블록(옛 소비 레포 형식, `$ecosystem`·`$directory` 치환)을 붙인다.

`source` 경로는 2026-11 재배치(#66) 뒤의 위치다. 옛 경로(`scripts/…`, `templates/dependabot.yml`)를 적은 소비 레포 manifest는 다시 적용하기 전에 고쳐야 한다(W9).
