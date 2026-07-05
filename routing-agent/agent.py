"""
HybridAgent — the main orchestrator.
Combines router + local + remote agents into one pipeline.
"""

import json
import os
import time
from datetime import datetime

from agents.local_agent import LocalAgent
from agents.remote_agent import RemoteAgent
from router.router import HybridRouter
from router.token_optimizer import build_prompt, estimate_tokens, max_tokens_for_task


class HybridAgent:
    def __init__(self, accuracy_threshold: float = 0.85, verbose: bool = True):
        self.verbose = verbose
        self.router = HybridRouter(accuracy_threshold=accuracy_threshold)
        self.local = LocalAgent()
        self.remote_medium = RemoteAgent("medium")
        self.remote_large = RemoteAgent("large")

        self.results = []
        self.total_tokens = 0
        self.total_cost = 0.0

        # Check local availability at startup
        if not self.local.is_available():
            print("⚠️  LM Studio not detected at http://localhost:1234")
            print("   → Make sure LM Studio is open and a model is loaded")
            print("   → Click 'Start Server' in LM Studio's Local Server tab")
        else:
            model = self.local.get_loaded_model()
            print(f"LM Studio connected — model: {model}")

    def run_task(self, task: str, task_id: int = 0) -> dict:
        """Route and execute a single task."""
        # Step 1: Explain routing decision
        explanation = self.router.explain(task)
        decision = explanation["decision"]

        # Step 2: Build compressed prompt
        prompt = build_prompt(task, decision)
        max_tok = max_tokens_for_task(task)
        input_tokens_est = estimate_tokens(prompt)

        if self.verbose:
            print(f"\n{'─'*60}")
            print(f"Task #{task_id}: {task[:70]}{'...' if len(task) > 70 else ''}")
            print(f"  Type: {explanation['task_type']} | Difficulty: {explanation['difficulty_score']}/10")
            print(f"  Route: {decision.upper()} | Est. input tokens: {input_tokens_est}")

        # Step 3: Execute on chosen model
        if decision == "local":
            if not self.local.is_available():
                if self.verbose:
                    print("  ⚠️  Local unavailable, falling back to remote_medium")
                decision = "remote_medium"
                result = self.remote_medium.run(prompt, max_tokens=max_tok)
            else:
                result = self.local.run(prompt, max_tokens=max_tok)

        elif decision == "remote_medium":
            result = self.remote_medium.run(prompt, max_tokens=max_tok)
        else:
            result = self.remote_large.run(prompt, max_tokens=max_tok)

        # Step 4: Update totals
        self.total_tokens += result["tokens"]
        self.total_cost += result["cost"]

        if self.verbose:
            status = "done" if result["success"] else "X"
            print(f"  {status} {result['model']} | {result['tokens']} tokens | "
                  f"${result['cost']:.5f} | {result['latency_s']}s")
            if not result["success"]:
                print(f"  Error: {result.get('error', 'unknown')}")
            else:
                preview = result["output"][:120].replace("\n", " ")
                print(f"  Output: {preview}{'...' if len(result['output']) > 120 else ''}")

        # Step 5: Build full record
        record = {
            "task_id": task_id,
            "task": task,
            "route": decision,
            "task_type": explanation["task_type"],
            "difficulty": explanation["difficulty_score"],
            "output": result["output"],
            "tokens": result["tokens"],
            "cost_usd": result["cost"],
            "model": result["model"],
            "latency_s": result["latency_s"],
            "success": result["success"],
            "timestamp": datetime.now().isoformat(),
        }
        self.results.append(record)
        return record

    def run_all(self, tasks: list) -> list:
        """Run all tasks and print a summary."""
        print(f"\n Starting {len(tasks)} tasks\n{'='*60}")
        start = time.time()

        for i, task in enumerate(tasks, 1):
            self.run_task(task, task_id=i)

        elapsed = round(time.time() - start, 1)
        self._print_summary(elapsed)
        return self.results

    def _print_summary(self, elapsed: float):
        total = len(self.results)
        success = sum(1 for r in self.results if r["success"])
        local_count = sum(1 for r in self.results if "local" in r["model"])
        medium_count = sum(1 for r in self.results if "medium" in r["model"])
        large_count = sum(1 for r in self.results if "large" in r["model"])

        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"  Tasks completed : {success}/{total}")
        print(f"  Total tokens    : {self.total_tokens:,}")
        print(f"  Total cost      : ${self.total_cost:.4f}")
        print(f"  Elapsed time    : {elapsed}s")
        print(f"  Routing split   : local={local_count} | medium={medium_count} | large={large_count}")
        if total > 0:
            print(f"  Avg tokens/task : {self.total_tokens // total:,}")
            print(f"  Avg cost/task   : ${self.total_cost/total:.5f}")
        print(f"{'='*60}\n")

    def save_results(self, path: str = "logs/results.json"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump({
                "summary": {
                    "total_tasks": len(self.results),
                    "total_tokens": self.total_tokens,
                    "total_cost_usd": self.total_cost,
                },
                "results": self.results,
            }, f, indent=2)
        print(f"Results saved to {path}")
