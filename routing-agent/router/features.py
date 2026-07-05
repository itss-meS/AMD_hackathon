"""
Feature extraction — converts raw task text into signals
that the router uses to pick the right model.
"""

import re


def extract_features(task: str) -> dict:
    words = task.split()
    word_count = len(words)
    char_count = len(task)

    # ── Content-type signals ──────────────────────────────
    has_math = bool(re.search(
        r'\d+\s*[\+\-\*\/\^]\s*\d+|equation|calculate|solve|integral|derivative|'
        r'probability|percent|average|mean|median|sum of|factorial|modulo',
        task, re.I
    ))
    has_code = bool(re.search(
        r'def |class |import |function|code|debug|python|sql|javascript|'
        r'algorithm|implement|bug|error|exception|syntax|compile|runtime',
        task, re.I
    ))
    has_reasoning = bool(re.search(
        r'why|explain|reason|compare|analyze|evaluate|critique|pros and cons|'
        r'discuss|argue|justify|infer|conclude|implication|consequence',
        task, re.I
    ))
    has_creative = bool(re.search(
        r'write a|story|poem|essay|creative|imagine|fiction|narrative|describe',
        task, re.I
    ))
    is_simple_qa = bool(re.search(
        r'^(what is|who is|when|where|which|how many|how much|name the|'
        r'list|define|spell|capital of|convert)',
        task.strip(), re.I
    ))
    has_multi_step = bool(re.search(
        r'step by step|first.*then|multiple|several|list all|enumerate|'
        r'comprehensive|detailed|thorough',
        task, re.I
    ))
    has_factual = bool(re.search(
        r'fact|true or false|correct|incorrect|accurate|historically|'
        r'scientifically|according to',
        task, re.I
    ))

    # ── Structural signals ────────────────────────────────
    question_marks = task.count("?")
    sentence_count = max(len(re.split(r'[.!?]+', task)), 1)
    avg_word_len = sum(len(w) for w in words) / max(word_count, 1)
    has_long_context = word_count > 150

    # ── Difficulty score (0–10, higher = harder) ─────────
    difficulty = 0
    difficulty += 2 if has_code else 0
    difficulty += 2 if has_math else 0
    difficulty += 2 if has_reasoning else 0
    difficulty += 1 if has_creative else 0
    difficulty += 1 if has_multi_step else 0
    difficulty += 1 if has_long_context else 0
    difficulty -= 2 if is_simple_qa else 0
    difficulty = max(0, min(10, difficulty))

    return {
        "word_count": word_count,
        "char_count": char_count,
        "has_math": int(has_math),
        "has_code": int(has_code),
        "has_reasoning": int(has_reasoning),
        "has_creative": int(has_creative),
        "is_simple_qa": int(is_simple_qa),
        "has_multi_step": int(has_multi_step),
        "has_factual": int(has_factual),
        "has_long_context": int(has_long_context),
        "question_marks": question_marks,
        "sentence_count": sentence_count,
        "avg_word_len": round(avg_word_len, 2),
        "difficulty": difficulty,
    }


def classify_task_type(features: dict) -> str:
    """Map features to a human-readable task category."""
    if features["has_code"]:
        return "code"
    elif features["has_math"]:
        return "math"
    elif features["has_reasoning"]:
        return "reasoning"
    elif features["has_creative"]:
        return "creative"
    elif features["is_simple_qa"]:
        return "simple_qa"
    elif features["has_long_context"]:
        return "summarization"
    else:
        return "extraction"
