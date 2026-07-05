"""
Local Agent — talks to LM Studio's built-in OpenAI-compatible server.
LM Studio exposes: http://localhost:1234/v1
Make sure LM Studio is running and a model is loaded before using this.
"""

import requests
import time


class LocalAgent:
    def __init__(self, base_url="http://localhost:1234/v1", model_name=None):
        self.base_url = base_url
        self.model_name = model_name  # None = whatever LM Studio has loaded
        self.cost_per_token = 0.0    # Local = FREE

    def is_available(self) -> bool:
        """Check if LM Studio server is running."""
        try:
            r = requests.get(f"{self.base_url}/models", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def get_loaded_model(self) -> str:
        """Get the name of the currently loaded model in LM Studio."""
        try:
            r = requests.get(f"{self.base_url}/models", timeout=3)
            models = r.json().get("data", [])
            if models:
                return models[0]["id"]
        except Exception:
            pass
        return "unknown"

    def run(self, prompt: str, max_tokens: int = 512) -> dict:
        """Run inference on local LM Studio model."""
        start = time.time()

        payload = {
            "model": self.model_name or self.get_loaded_model(),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.1,
            "stream": False,
        }

        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()

            output = data["choices"][0]["message"]["content"].strip()
            usage = data.get("usage", {})
            tokens_used = usage.get("total_tokens", len(prompt.split()) + len(output.split()))
            latency = round(time.time() - start, 2)

            return {
                "output": output,
                "tokens": tokens_used,
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "cost": 0.0,
                "model": f"local/{payload['model']}",
                "latency_s": latency,
                "success": True,
            }

        except Exception as e:
            return {
                "output": "",
                "tokens": 0,
                "cost": 0.0,
                "model": "local/error",
                "latency_s": time.time() - start,
                "success": False,
                "error": str(e),
            }
