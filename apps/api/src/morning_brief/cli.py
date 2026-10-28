"""명령줄 진입점.

morning-brief run [--no-push] [--no-notion]   브리핑을 지금 한 번 만든다
morning-brief worker                          매일 아침 자동 생성 (서버에서 상주)
morning-brief vapid-keys                      알림용 VAPID 키를 새로 만든다 (처음 한 번)
"""

from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(prog="morning-brief")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="브리핑을 지금 한 번 만든다")
    run.add_argument("--no-push", action="store_true", help="알림을 보내지 않음")
    run.add_argument("--no-notion", action="store_true", help="Notion 에 올리지 않음")
    sub.add_parser("worker", help="매일 아침 자동 생성")
    sub.add_parser("vapid-keys", help="알림용 VAPID 키 생성")
    args = parser.parse_args()

    if args.command == "run":
        from .config import get_settings
        from .db import get_db
        from .markdown import briefing_markdown
        from .pipeline import run_once

        briefing = run_once(
            get_settings(), get_db(), send_push=not args.no_push, publish_notion=not args.no_notion
        )
        print(f"\n# {briefing['title']}\n\n{briefing_markdown(briefing)}")
        return 0 if briefing["status"] == "ok" else 1
    if args.command == "worker":
        from .worker import main as worker_main

        worker_main()
        return 0
    if args.command == "vapid-keys":
        from .push import generate_vapid_keys

        public, private = generate_vapid_keys()
        print("아래 두 줄을 .env 에 붙여 넣으세요. 비밀키는 절대 공유하거나 커밋하지 마세요.\n")
        print(f"VAPID_PUBLIC_KEY={public}")
        print(f"VAPID_PRIVATE_KEY={private}")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
