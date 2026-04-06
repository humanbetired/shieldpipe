import sys
import os
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from database import init_db
from engine.pipeline import run


def main():
    parser = argparse.ArgumentParser(description="ShieldPipe — DevSecOps Security Scanner")
    parser.add_argument("--target",  required=True, help="Path to project folder to scan")
    parser.add_argument("--name",    default=None,  help="Project name (optional)")
    parser.add_argument("--image",   default=None,  help="Docker image to scan (optional)")
    args = parser.parse_args()

    target = os.path.abspath(args.target)
    if not os.path.exists(target):
        print(f"[Error] Target path not found: {target}")
        sys.exit(1)

    init_db()
    run(target_path=target, project_name=args.name, image=args.image)


if __name__ == "__main__":
    main()