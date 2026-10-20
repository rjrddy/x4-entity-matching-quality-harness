"""Threshold tradeoffs and explicit error analysis for synthetic record matching."""

import json
import random
import re
from difflib import SequenceMatcher
from pathlib import Path
import matplotlib.pyplot as plt


def normalize(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def score(left: dict, right: dict) -> float:
    name = SequenceMatcher(None, normalize(left["name"]), normalize(right["name"])).ratio()
    location = float(normalize(left["city"]) == normalize(right["city"]))
    domain = float(normalize(left["domain"]) == normalize(right["domain"]))
    return 0.55 * name + 0.2 * location + 0.25 * domain


def labeled_pairs(seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    pairs = []
    for i in range(300):
        company = i % 2 == 0
        name = f"Synthetic {'Company' if company else 'Person'} {i:03d}"
        left = {
            "name": name,
            "city": ["Northfield", "Westhaven", "Southport"][i % 3],
            "domain": f"entity{i}.example.invalid",
        }
        true_right = {**left, "name": name.upper().replace(" ", "-")}
        if i % 3 == 0:
            true_right["name"] = true_right["name"].replace("SYNTHETIC", "SYNTHETC")
        if i % 7 == 0:
            true_right["city"] = "Oldtown"
        if i % 11 == 0:
            true_right["domain"] = "changed.example.invalid"
        pairs.append(
            {
                "left": left,
                "right": true_right,
                "match": True,
                "kind": "company" if company else "person",
            }
        )
        other = rng.randrange(300)
        negative = {
            "name": f"Synthetic {'Company' if company else 'Person'} {other:03d}",
            "city": left["city"],
            "domain": f"entity{other}.example.invalid",
        }
        if other == i:
            negative["domain"] = "collision.example.invalid"
        pairs.append(
            {
                "left": left,
                "right": negative,
                "match": False,
                "kind": "company" if company else "person",
            }
        )
    return pairs


def evaluate(pairs: list[dict], threshold: float) -> dict:
    predicted = [score(r["left"], r["right"]) >= threshold for r in pairs]
    tp = sum(a and r["match"] for a, r in zip(predicted, pairs))
    fp = sum(a and not r["match"] for a, r in zip(predicted, pairs))
    fn = sum(not a and r["match"] for a, r in zip(predicted, pairs))
    return {
        "threshold": threshold,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn),
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def benchmark() -> dict:
    pairs = labeled_pairs()
    curve = [evaluate(pairs, t) for t in [0.5, 0.65, 0.75, 0.8, 0.85, 0.9, 0.95, 0.99]]
    chosen = evaluate(pairs, 0.9)
    errors = [
        {
            **r,
            "score": score(r["left"], r["right"]),
            "error": "false-positive" if not r["match"] else "false-negative",
        }
        for r in pairs
        if (score(r["left"], r["right"]) >= 0.9) != r["match"]
    ]
    Path("evidence/precision-recall.json").write_text(json.dumps(curve, indent=2))
    Path("evidence/errors.json").write_text(json.dumps(errors, indent=2))
    Path("evidence/error-analysis.md").write_text(
        "| Error | Left name | Right name | Score |\n|---|---|---|---|\n"
        + "".join(
            f"| {r['error']} | {r['left']['name']} | {r['right']['name']} | {r['score']} |\n"
            for r in errors[:30]
        )
    )
    plt.plot(
        [r["recall"] for r in curve],
        [r["precision"] if r["precision"] is not None else float("nan") for r in curve],
        marker="o",
    )
    plt.xlabel("recall")
    plt.ylabel("precision")
    plt.savefig("evidence/precision-recall.svg")
    plt.close()
    return {
        "labeled_synthetic_pairs": len(pairs),
        "threshold": 0.9,
        "precision": chosen["precision"],
        "recall": chosen["recall"],
        "error_count": len(errors),
    }


if __name__ == "__main__":
    print(json.dumps(benchmark(), indent=2))
