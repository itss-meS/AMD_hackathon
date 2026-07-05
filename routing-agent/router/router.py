"""
HybridRouter — decides whether a task goes to:
  1. local      (LM Studio, free, fast for simple tasks)
  2. remote_medium  (Fireworks 8B AMD model, cheap)
  3. remote_large   (Fireworks 70B AMD model, best quality)

Rule-based by default. Automatically upgrades to ML-based
if a trained classifier exists at router/classifier.pkl
"""

import os
import pickle
import pandas as pd
from router.features import extract_features, classify_task_type


# Estimated local model accuracy per task type (tune these from your testing)
LOCAL_ACCURACY_ESTIMATES = {
    "simple_qa":     0.93,
    "extraction":    0.88,
    "factual":       0.85,
    "summarization": 0.80,
    "creative":      0.75,
    "reasoning":     0.68,
    "math":          0.62,
    "code":          0.58,
}

MEDIUM_ACCURACY_ESTIMATES = {
    "simple_qa":     0.97,
    "extraction":    0.94,
    "factual":       0.93,
    "summarization": 0.91,
    "creative":      0.88,
    "reasoning":     0.87,
    "math":          0.84,
    "code":          0.82,
}


class HybridRouter:
    def __init__(self, accuracy_threshold: float = 0.85):
        """
        accuracy_threshold: minimum acceptable accuracy (0.0–1.0).
        Tasks where local model can't meet this go to remote.
        """
        self.threshold = accuracy_threshold
        self._clf = self._load_classifier()

    def _load_classifier(self):
        clf_path = os.path.join(os.path.dirname(__file__), "classifier.pkl")
        if os.path.exists(clf_path):
            with open(clf_path, "rb") as f:
                print("✅ Loaded trained ML router classifier")
                return pickle.load(f)
        return None

    def route(self, task: str) -> str:
        """
        Returns one of: 'local', 'remote_medium', 'remote_large'
        """
        features = extract_features(task)

        # ── ML-based routing (if classifier trained) ──────
        if self._clf is not None:
            feature_df = pd.DataFrame([features])
            prediction = self._clf.predict(feature_df)[0]
            return prediction  # returns 'local', 'remote_medium', or 'remote_large'

        # ── Rule-based routing (default) ──────────────────
        return self._rule_based_route(features)

    def _rule_based_route(self, features: dict) -> str:
        task_type = classify_task_type(features)
        difficulty = features["difficulty"]

        local_acc = LOCAL_ACCURACY_ESTIMATES.get(task_type, 0.70)
        medium_acc = MEDIUM_ACCURACY_ESTIMATES.get(task_type, 0.88)

        # Very hard tasks → large model
        if difficulty >= 7:
            return "remote_large"

        # Local can handle it
        if local_acc >= self.threshold:
            return "local"

        # Medium remote can handle it
        if medium_acc >= self.threshold:
            return "remote_medium"

        # Fall back to large for anything else
        return "remote_large"

    def explain(self, task: str) -> dict:
        """Return a full explanation of the routing decision."""
        features = extract_features(task)
        task_type = classify_task_type(features)
        decision = self.route(task)
        local_acc = LOCAL_ACCURACY_ESTIMATES.get(task_type, 0.70)
        medium_acc = MEDIUM_ACCURACY_ESTIMATES.get(task_type, 0.88)

        return {
            "decision": decision,
            "task_type": task_type,
            "difficulty_score": features["difficulty"],
            "local_est_accuracy": local_acc,
            "medium_est_accuracy": medium_acc,
            "threshold": self.threshold,
            "features": features,
            "using_ml_router": self._clf is not None,
        }
