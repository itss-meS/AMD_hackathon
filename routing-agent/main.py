"""
main.py — Entry point for the Hybrid Token-Efficient Routing Agent.

Usage:
    python main.py                    # Run with sample tasks
    python main.py --tasks my_tasks.json  # Run with custom tasks file
    python main.py --task "What is 2+2?"  # Run a single task
    python main.py --threshold 0.80   # Set accuracy threshold
"""

import argparse
import json
import os
import sys
from agent import HybridAgent

# ── Sample tasks (replace with hackathon tasks when revealed) ─────────────────
SAMPLE_TASKS = [
    "What is the capital of France?",
    "Explain the difference between TCP and UDP protocols.",
    "Write a Python function to check if a number is prime.",
    "What is 17 multiplied by 43?",
    "Summarize what machine learning is in one sentence.",
    "List 5 renewable energy sources.",
    "Why does the sky appear blue?",
    "Convert 100 Fahrenheit to Celsius.",
    "What are the pros and cons of microservices architecture?",
    "Write a SQL query to find duplicate emails in a users table.",
]


def main():
    parser = argparse.ArgumentParser(description="Hybrid Token-Efficient Routing Agent")
    parser.add_argument("--tasks", type=str, help="Path to JSON file with tasks list")
    parser.add_argument("--task", type=str, help="Run a single task")
    parser.add_argument("--threshold", type=float, default=0.85, help="Accuracy threshold (0–1)")
    parser.add_argument("--output", type=str, default="logs/results.json", help="Output file path")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose output")
    args = parser.parse_args()

    # ── Load tasks ─────────────────────────────────────────────────────────────
    if args.task:
        tasks = [args.task]
    elif args.tasks:
        if not os.path.exists(args.tasks):
            print(f"❌ Tasks file not found: {args.tasks}")
            sys.exit(1)
        with open(args.tasks) as f:
            tasks = json.load(f)
        print(f"📋 Loaded {len(tasks)} tasks from {args.tasks}")
    else:
        print("📋 Using sample tasks (pass --tasks <file> for hackathon tasks)")
        tasks = SAMPLE_TASKS

    # ── Run agent ──────────────────────────────────────────────────────────────
    agent = HybridAgent(
        accuracy_threshold=args.threshold,
        verbose=not args.quiet,
    )
    results = agent.run_all(tasks)

    # ── Save results ───────────────────────────────────────────────────────────
    agent.save_results(args.output)

    # ── Return exit code based on success rate ─────────────────────────────────
    success_rate = sum(1 for r in results if r["success"]) / len(results)
    if success_rate < 0.5:
        print(f"⚠️  Only {success_rate:.0%} of tasks succeeded. Check your API keys and model setup.")
        sys.exit(1)


if __name__ == "__main__":
    main()
