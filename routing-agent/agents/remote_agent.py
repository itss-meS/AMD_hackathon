"""
Remote Agent — calls Fireworks AI API (AMD-hardware models only).
Get your API key from: https://fireworks.ai/api-keys
"""

import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
# AMD models available on Fireworks AI
# Update these if Fireworks changes their model IDs
# ──────────────────────────────────────────────
AMD_MODELS = {
    "large": "accounts/fireworks/models/llama-v3p1-70b-instruct",
    "medium": "accounts/fireworks/models/llama-v3p1-8b-instruct",
}

# Approximate cost per 1K tokens (check fireworks.ai/pricing for latest)
COST_PER_1K = {
    "large": 0.0009,   # ~$0.90 per million tokens
    "medium": 0.0002,  # ~$0.20 per million tokens
}


class RemoteAgent:
    def __init__(self, model_size: str = "medium"):
        assert model_size in AMD_MODELS, f"model_size must be one of {list(AMD_MODELS.keys())}"
        self.api_key = os.getenv("FIREWORKS_API_KEY", "")
        self.model_id = AMD_MODELS[model_size]
        self.model_size = model_size
        self.url = "https://api.fireworks.ai/inference/v1/chat/completions"

    def run(self, prompt: str, max_tokens: int = 512) -> dict:
        """Call Fireworks AI and return result with cost info."""
        if not self.api_key:
            return {
                "output": "",
                "tokens": 0,
                "cost": 0.0,
                "model": f"fireworks/{self.model_size}",
                "latency_s": 0,
                "success": False,
                "error": "FIREWORKS_API_KEY not set in .env file",
            }

        start = time.time()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.1,
        }

        try:
            resp = requests.post(self.url, json=payload, headers=headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()

            output = data["choices"][0]["message"]["content"].strip()
            usage = data.get("usage", {})
            tokens = usage.get("total_tokens", len(prompt.split()) + len(output.split()))
            cost = (tokens / 1000) * COST_PER_1K[self.model_size]
            latency = round(time.time() - start, 2)

            return {
                "output": output,
                "tokens": tokens,
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "cost": round(cost, 6),
                "model": f"fireworks/{self.model_size}",
                "latency_s": latency,
                "success": True,
            }

        except Exception as e:
            return {
                "output": "",
                "tokens": 0,
                "cost": 0.0,
                "model": f"fireworks/{self.model_size}",
                "latency_s": time.time() - start,
                "success": False,
                "error": str(e),
            }
