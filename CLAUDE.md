# CLAUDE.md

프로젝트 규칙은 모두 AGENTS.md에 있습니다. 다른 에이전트와 같은 규칙을 쓰기 위해 그대로 가져옵니다.
규칙을 고칠 때는 AGENTS.md를 고칩니다.

@AGENTS.md

## Claude Code 전용

- Notion 작업일지는 연결된 Notion 커넥터로 씁니다. 데이터 소스 `collection://38d7ac18-71de-41df-816f-0defa99512b3`에 `notion-create-pages`로 페이지를 만들고, 같은 날 이어서 작업했다면 그날 페이지를 찾아서 내용을 덧붙입니다.
- 작업일지는 커밋·푸시가 끝난 뒤에 써서 커밋 해시를 넣습니다.
- 사용자가 직접 해야 하는 일(키 발급, Atlas·GitHub 로그인, 서버 env 값)은 대신 하지 않고 단계별로 안내합니다.
- 하네스(권한)는 `.claude/settings.json`에 있고 **저장소에 커밋됩니다.** 고치면 같이 쓰는 사람 모두에게 갑니다. 개인 설정은 `.claude/settings.local.json`(커밋 안 됨)에 둡니다.
- `.claude/settings.json`이 막는 것: `.env` 읽기, `git push --force`, `main`으로 바로 푸시. 커밋·PR에 Claude 표시가 붙지 않게 attribution을 껐습니다.
