"""
Token Optimizer — compresses prompts before sending to any model.
Fewer tokens = lower cost = better hackathon score.
"""

import re


# Words that add zero meaning to a prompt
FILLER_PHRASES = [
    "Please ", "Could you ", "Can you ", "I would like you to ",
    "I need you to ", "Kindly ", "Would you be able to ",
    "I was wondering if you could ", "Do you think you could ",
    "I'd appreciate it if you ", "Feel free to ",
]

# Map verbose instructions to compact ones
VERBOSE_TO_COMPACT = {
    "in a detailed manner": "in detail",
    "provide me with": "give",
    "provide an explanation": "explain",
    "give me a list of": "list",
    "can you tell me": "tell me",
    "I am interested in knowing": "what is",
    "make sure to include": "include",
    "it is important that you": "",
    "please note that": "note:",
    "as mentioned above": "",
    "as previously stated": "",
}


def compress_prompt(task: str) -> str:
    """Remove filler words and redundant phrases from a prompt."""
    result = task.strip()

    # Strip filler openers
    for phrase in FILLER_PHRASES:
        result = result.replace(phrase, "")
        result = result.replace(phrase.lower(), "")

    # Replace verbose patterns
    for verbose, compact in VERBOSE_TO_COMPACT.items():
        result = re.sub(re.escape(verbose), compact, result, flags=re.I)

    # Collapse multiple spaces/newlines
    result = re.sub(r'\s+', ' ', result).strip()

    return result


def build_prompt(task: str, route: str) -> str:
    """
    Build the final prompt to send to the model.
    Keeps system instructions minimal to save tokens.
    """
    compressed = compress_prompt(task)

    # Use the shortest possible system instruction per route
    if route == "local":
        # Local models need slightly more guidance
        system = "Answer concisely and accurately."
    else:
        # Remote models are smart enough with minimal instruction
        system = "Be brief and accurate."

    # Add output length constraint to prevent rambling
    if len(compressed.split()) < 30:
        # Short task → enforce very short answer
        constraint = " Answer in 1-2 sentences."
    elif len(compressed.split()) < 80:
        constraint = " Be concise."
    else:
        constraint = ""

    final = f"{system}\n\n{compressed}{constraint}"
    return final


def estimate_tokens(text: str) -> int:
    """
    Fast token count approximation.
    Rule of thumb: 1 token ≈ 0.75 words (works for most English text)
    """
    word_count = len(text.split())
    return max(1, int(word_count / 0.75))


def max_tokens_for_task(task: str) -> int:
    """
    Estimate how many output tokens a task actually needs.
    Don't set max_tokens=2048 when 50 would do — wasted budget.
    """
    task_lower = task.lower()

    # Tasks that need long answers
    if any(k in task_lower for k in ["explain", "essay", "summarize", "describe in detail", "step by step"]):
        return 400

    # Tasks needing medium answers
    if any(k in task_lower for k in ["list", "compare", "pros and cons", "reasons", "examples"]):
        return 250

    # Tasks needing code output
    if any(k in task_lower for k in ["code", "function", "script", "implement", "write a program"]):
        return 350

    # Simple Q&A
    return 120
