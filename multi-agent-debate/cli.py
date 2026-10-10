"""
cli.py – Terminal interface for the Multi-Agent Debate System
Usage: python cli.py "Should AI have legal personhood?" --rounds 2
"""

import argparse
import os
from agents import run_debate
from dotenv import load_dotenv

load_dotenv()


def print_section(title: str, content: str, color_code: str = "37"):
    """Print colored terminal section."""
    print(f"\n\033[{color_code}m{'='*60}\033[0m")
    print(f"\033[{color_code}m{title}\033[0m")
    print(f"\033[{color_code}m{'='*60}\033[0m")
    print(content)


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Agent Debate System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py "Should AI have legal personhood?"
  python cli.py "Is nuclear energy clean?" --rounds 3
        """
    )
    parser.add_argument("question", help="The debate question/topic")
    parser.add_argument(
        "--rounds", type=int,
        default=int(os.getenv("DEBATE_ROUNDS", "2")),
        help="Number of debate rounds (default: 2)"
    )
    args = parser.parse_args()

    print(f"\n\033[1m⚔️  MULTI-AGENT DEBATE ARENA\033[0m")
    print(f"Topic  : {args.question}")
    print(f"Rounds : {args.rounds}")
    print(f"Model  : {os.getenv('DEBATE_MODEL', 'llama3.2')}")
    print("Running debate...\n")

    result = run_debate(args.question, rounds=args.rounds)

    for i, (f_arg, a_arg) in enumerate(
        zip(result["for_args"], result["against_args"]), 1
    ):
        print_section(f"ROUND {i} — FOR  🟢", f_arg, color_code="32")
        print_section(f"ROUND {i} — AGAINST  🔴", a_arg, color_code="31")

    print_section("👨‍⚖️  JUDGE VERDICT", result["verdict"], color_code="34")


if __name__ == "__main__":
    main()
