import argparse
from db import add_input, init_db

def main():
    parser = argparse.ArgumentParser(description="Inject a test task into prayGPT DB.")
    parser.add_argument("--text", type=str, default="형님, 오늘 점심 메뉴로 돈까스와 제육볶음 중 무엇을 먹어야 우주 정복에 도움이 되겠습니까?", help="Text payload for the task")
    parser.add_argument("--image", type=str, default=None, help="Image path or URL")

    args = parser.parse_args()

    init_db()
    print(f"Injecting task: {args.text}")
    if args.image:
        print(f"With image: {args.image}")

    input_id = add_input(args.text, args.image)
    print(f"Task injected successfully! ID: {input_id}")

if __name__ == "__main__":
    main()
