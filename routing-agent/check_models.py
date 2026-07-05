"""
Probe a handful of known Fireworks AI model IDs directly against the
/chat/completions endpoint (the one your app actually uses) and report
which ones work with your API key.

We do this instead of GET /inference/v1/models because that listing
endpoint isn't reliable for account-scoped serverless availability —
testing the real call path is the ground truth.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("FIREWORKS_API_KEY")
print(f"API Key found: {'Yes' if api_key else 'NO - check your .env file!'}\n")

if not api_key:
    raise SystemExit("Set FIREWORKS_API_KEY in your .env file first.")

URL = "https://api.fireworks.ai/inference/v1/chat/completions"

# A mix of model IDs spanning small/medium/large that have been live on
# Fireworks serverless recently. Trim/extend this list as needed.
CANDIDATES = [
    "accounts/fireworks/models/llama-v3p1-8b-instruct",
    "accounts/fireworks/models/llama-v3p1-70b-instruct",
    "accounts/fireworks/models/llama-v3p3-70b-instruct",
    "accounts/fireworks/models/llama4-scout-instruct-basic",
    "accounts/fireworks/models/llama4-maverick-instruct-basic",
    "accounts/fireworks/models/qwen3-30b-a3b",
    "accounts/fireworks/models/qwen2p5-72b-instruct",
    "accounts/fireworks/models/deepseek-v3p1",
    "accounts/fireworks/models/kimi-k2-instruct-0905",
    "accounts/fireworks/models/mixtral-8x7b-instruct",
]

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

print(f"Testing {len(CANDIDATES)} model IDs against {URL}\n")
working = []

for model_id in CANDIDATES:
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": "Say OK"}],
        "max_tokens": 5,
    }
    try:
        resp = requests.post(URL, json=payload, headers=headers, timeout=30)
        if resp.ok:
            print(f"  OK   {model_id}")
            working.append(model_id)
        else:
            try:
                detail = resp.json().get("error", resp.text)
            except ValueError:
                detail = resp.text or "(empty body)"
            print(f"  FAIL {model_id}  -> {resp.status_code}: {detail}")
    except requests.RequestException as e:
        print(f"  ERR  {model_id}  -> {e}")

print("\n--- Summary ---")
if working:
    print("Working model IDs:")
    for m in working:
        print(f"  - {m}")
else:
    print("None of the candidates worked. This points to an account/key issue")
    print("(inactive key, no billing/credits set up, or org-level restriction)")
    print("rather than a model-name problem. Check https://app.fireworks.ai/account/billing")