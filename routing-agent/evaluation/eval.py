"""
Evaluator — scores your agent's output against ground truth.
Use this after the hackathon reveals the answer key.

Usage:
    python -m evaluation.eval --results logs/results.json --truth tasks/ground_truth.json
"""

import argparse
import json
import re
import os


def normalize(text: str) -> str:
    """Normalize text for comparison (lowercase, strip punctuation)."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def exact_match(pred: str, truth: str) -> bool:
    return normalize(pred) == normalize(truth)


def contains_match(pred: str, truth: str) -> bool:
    """Check if the truth answer appears somewhere in the prediction."""
    return normalize(truth) in normalize(pred)


def score_results(results: list, ground_truth: list) -> dict:
    """
    Score predictions against ground truth answers.
    Returns accuracy, token stats, and cost stats.
    """
    assert len(results) == len(ground_truth), \
        f"Mismatch: {len(results)} results vs {len(ground_truth)} truth answers"

    exact_correct = 0
    contains_correct = 0
    total_tokens = 0
    total_cost = 0.0
    per_task = []

    for result, truth in zip(results, ground_truth):
        pred = result.get("output", "")
        em = exact_match(pred, truth)
        cm = contains_match(pred, truth)

        exact_correct += int(em)
        contains_correct += int(cm)
        total_tokens += result.get("tokens", 0)
        total_cost += result.get("cost_usd", 0.0)

        per_task.append({
            "task_id": result.get("task_id"),
            "task": result.get("task", "")[:60],
            "model": result.get("model"),
            "exact_match": em,
            "contains_match": cm,
            "tokens": result.get("tokens"),
            "cost_usd": result.get("cost_usd"),
        })

    n = len(results)
    exact_acc = exact_correct / n
    contains_acc = contains_correct / n

    # Hackathon score formula: maximize accuracy / (total_tokens / 1000)
    # Higher accuracy AND lower tokens = better score
    score = contains_acc / (total_tokens / 1000) if total_tokens > 0 else 0

    summary = {
        "total_tasks": n,
        "exact_match_accuracy": round(exact_acc, 4),
        "contains_match_accuracy": round(contains_acc, 4),
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 6),
        "avg_tokens_per_task": round(total_tokens / n),
        "hackathon_score": round(score, 4),
        "per_task": per_task,
    }
    return summary


def print_report(summary: dict):
    print(f"\n{'='*60}")
    print(f"🏆 EVALUATION REPORT")
    print(f"{'='*60}")
    print(f"  Tasks          : {summary['total_tasks']}")
    print(f"  Exact match    : {summary['exact_match_accuracy']:.1%}")
    print(f"  Contains match : {summary['contains_match_accuracy']:.1%}")
    print(f"  Total tokens   : {summary['total_tokens']:,}")
    print(f"  Total cost     : ${summary['total_cost_usd']:.4f}")
    print(f"  Avg tokens/task: {summary['avg_tokens_per_task']:,}")
    print(f"  Hackathon score: {summary['hackathon_score']:.4f}")
    print(f"{'='*60}")

    # Show failed tasks
    failed = [t for t in summary["per_task"] if not t["contains_match"]]
    if failed:
        print(f"\n❌ Failed tasks ({len(failed)}):")
        for t in failed:
            print(f"  #{t['task_id']}: {t['task']}...")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="logs/results.json")
    parser.add_argument("--truth", default="tasks/ground_truth.json")
    parser.add_argument("--output", default="logs/eval_report.json")
    args = parser.parse_args()

    if not os.path.exists(args.results):
        print(f"❌ Results file not found: {args.results}")
        return
    if not os.path.exists(args.truth):
        print(f"❌ Ground truth file not found: {args.truth}")
        print("   Create tasks/ground_truth.json as a list of expected answers")
        return

    with open(args.results) as f:
        data = json.load(f)
        results = data.get("results", data)  # handle both formats

    with open(args.truth) as f:
        ground_truth = json.load(f)

    summary = score_results(results, ground_truth)
    print_report(summary)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n💾 Report saved to {args.output}")


if __name__ == "__main__":
    main()
