"""
Convenience script that trains all three models sequentially,
then runs compare_models.py to generate comparison charts.

Run from the ml-models/ directory:
    python train_all.py
"""

import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


TRAIN_SCRIPTS = [
    ("Random Forest", os.path.join(BASE_DIR, "models", "random_forest", "train.py")),
    ("XGBoost", os.path.join(BASE_DIR, "models", "xgboost_model", "train.py")),
    ("LSTM", os.path.join(BASE_DIR, "models", "lstm_model", "train.py")),
]


def main():
    for name, script in TRAIN_SCRIPTS:
        print(f"\n{'='*60}")
        print(f"  Training: {name}")
        print(f"{'='*60}")
        result = subprocess.run([sys.executable, script], check=False)
        if result.returncode != 0:
            print(f"[WARNING] {name} training exited with code {result.returncode}")

    print("\n[train_all] All models trained.")

    print(f"\n{'='*60}")
    print("  Comparing models & generating charts")
    print(f"{'='*60}")
    compare_script = os.path.join(BASE_DIR, "compare_models.py")
    result = subprocess.run([sys.executable, compare_script], check=False)
    if result.returncode != 0:
        print(f"[WARNING] compare_models.py exited with code {result.returncode}")
    else:
        print("[train_all] Comparison charts saved to reports/")


if __name__ == "__main__":
    main()
