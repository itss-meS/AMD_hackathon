"""
Train an ML classifier to replace rule-based routing.
Run this AFTER collecting labeled data from real task runs.

Usage:
    python -m router.train_router

Input:  logs/labeled_data.csv
Output: router/classifier.pkl
"""

import os
import pickle
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from router.features import extract_features


def train(data_path: str = "logs/labeled_data.csv"):
    if not os.path.exists(data_path):
        print(f"❌ No labeled data found at {data_path}")
        print("   Run some tasks first, then manually label which model gave the best result.")
        print("   CSV format: task,best_model")
        print("   best_model values: local | remote_medium | remote_large")
        return

    df = pd.read_csv(data_path)
    print(f"📊 Loaded {len(df)} labeled samples")

    # Extract features from each task
    feature_rows = [extract_features(t) for t in df["task"]]
    X = pd.DataFrame(feature_rows)
    y = df["best_model"]

    # Check class distribution
    print("\nClass distribution:")
    print(y.value_counts())

    if len(df) < 30:
        print("\n⚠️  Warning: Less than 30 samples. Classifier may not generalize well.")
        print("   Continue collecting data. Rule-based router is fine for now.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if len(df) >= 30 else None
    )

    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=6,
        random_state=42,
        class_weight="balanced",
    )
    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    acc = (y_pred == y_test).mean()
    print(f"\n✅ Router classifier accuracy: {acc:.1%}")
    print("\nDetailed report:")
    print(classification_report(y_test, y_pred))

    # Feature importance
    importances = sorted(
        zip(X.columns, clf.feature_importances_),
        key=lambda x: x[1], reverse=True
    )
    print("\nTop routing signals:")
    for feat, imp in importances[:5]:
        print(f"  {feat}: {imp:.3f}")

    # Save
    out_path = os.path.join(os.path.dirname(__file__), "classifier.pkl")
    with open(out_path, "wb") as f:
        pickle.dump(clf, f)
    print(f"\n💾 Saved classifier to {out_path}")
    print("   Restart the agent to use ML routing automatically.")


if __name__ == "__main__":
    train()
