# Hybrid Token-Efficient Routing Agent

Routes each task to the cheapest model that can handle it accurately.
- **Local** → LM Studio (free, fast for simple tasks)
- **Remote Medium** → Fireworks AI 8B AMD model (cheap)
- **Remote Large** → Fireworks AI 70B AMD model (best quality)

---

## Setup (5 minutes)

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up LM Studio
1. Download LM Studio from https://lmstudio.ai
2. Search for and download **Phi-3-mini-4k-instruct** (best CPU model)
   - Or any other model you prefer
3. Go to **Local Server** tab (left sidebar icon)
4. Click **"Start Server"**
5. Server runs at `http://localhost:1234`

### 3. Set up Fireworks AI
1. Sign up at https://fireworks.ai
2. Get your API key from https://fireworks.ai/api-keys
3. Edit `.env` and add your key:
   ```
   FIREWORKS_API_KEY=your_actual_key_here
   ```

### 4. Run the agent
```bash
# Test with sample tasks
python main.py

# Run a single task
python main.py --task "What is the capital of France?"

# Load hackathon tasks (once revealed)
python main.py --tasks tasks/hackathon_tasks.json

# Lower threshold = more local inference = cheaper
python main.py --threshold 0.80
```

---

## How the Router Works

```
Task Input
    │
    ▼
Extract Features (word count, has_code, has_math, difficulty score...)
    │
    ▼
Classify Task Type (simple_qa / math / code / reasoning / creative)
    │
    ▼
Lookup estimated local accuracy for that type
    │
    ├─ local_accuracy >= threshold? → Send to LM Studio (FREE)
    │
    ├─ medium_accuracy >= threshold? → Send to Fireworks Medium (cheap)
    │
    └─ else → Send to Fireworks Large (best quality)
```

### Accuracy thresholds by task type

| Task Type   | Local Est. | Medium Est. | Default Route  |
|-------------|-----------|------------|----------------|
| simple_qa   | 93%       | 97%        | local          |
| extraction  | 88%       | 94%        | local          |
| summarize   | 80%       | 91%        | local          |
| creative    | 75%       | 88%        | local          |
| reasoning   | 68%       | 87%        | remote_medium  |
| math        | 62%       | 84%        | remote_medium  |
| code        | 58%       | 82%        | remote_medium  |

---

## Project Structure

```
routing-agent/
├── main.py               ← Run this
├── agent.py              ← Main orchestrator
├── .env                  ← Your API keys (edit this)
├── requirements.txt
│
├── agents/
│   ├── local_agent.py    ← Talks to LM Studio
│   └── remote_agent.py   ← Talks to Fireworks AI
│
├── router/
│   ├── features.py       ← Extracts task features
│   ├── router.py         ← Routing decision logic
│   ├── token_optimizer.py← Compresses prompts
│   └── train_router.py   ← Train ML router (optional)
│
├── evaluation/
│   └── eval.py           ← Score accuracy vs cost
│
├── tasks/
│   └── tasks.json        ← Put hackathon tasks here
│
└── logs/
    ├── results.json      ← Auto-saved after each run
    └── labeled_data.csv  ← For training ML router
```

---

## Hackathon Day Workflow

1. **Tasks revealed** → Save them to `tasks/hackathon_tasks.json`:
   ```json
   ["Task 1 here", "Task 2 here", "Task 3 here"]
   ```

2. **Run the agent**:
   ```bash
   python main.py --tasks tasks/hackathon_tasks.json
   ```

3. **Check results** in `logs/results.json`

4. **Evaluate** (when ground truth is shared):
   ```bash
   python -m evaluation.eval --results logs/results.json --truth tasks/ground_truth.json
   ```

5. **Tune threshold** if accuracy is too low:
   ```bash
   python main.py --tasks tasks/hackathon_tasks.json --threshold 0.90
   ```

---

## Training the ML Router (Optional Upgrade)

After running enough tasks:

1. Create `logs/labeled_data.csv`:
   ```csv
   task,best_model
   "What is 2+2?",local
   "Write a binary search in Python",remote_medium
   "Explain quantum entanglement in detail",remote_large
   ```

2. Train the classifier:
   ```bash
   python -m router.train_router
   ```

3. Restart `main.py` — it auto-loads the trained classifier.

---

## Token Optimization Tips

The agent automatically:
- Strips filler phrases ("Please could you...", "Can you please...")
- Adds output length constraints ("Answer in 1-2 sentences")
- Sets `max_tokens` to the minimum needed per task type

**Additional tips:**
- Use `--threshold 0.80` to push more tasks to local (free)
- The local model handles ~60-70% of typical hackathon tasks
- Every token saved counts toward your score

---

## Fireworks AI AMD Models

Check https://fireworks.ai/models for current AMD model IDs.
Update `AMD_MODELS` in `agents/remote_agent.py` if needed.
