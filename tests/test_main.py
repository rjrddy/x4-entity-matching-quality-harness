from main import evaluate, labeled_pairs, score


def test_exact_matches_and_score_bounds():
    row = {"name": "Synthetic Person", "city": "Northfield", "domain": "test.example.invalid"}
    assert score(row, row) == 1
    assert all(0 <= score(p["left"], p["right"]) <= 1 for p in labeled_pairs())


def test_threshold_changes_precision_recall_tradeoff():
    pairs = labeled_pairs()
    low = evaluate(pairs, 0.5)
    high = evaluate(pairs, 0.99)
    assert low["recall"] >= high["recall"]
    assert low["fp"] >= high["fp"]
    assert pairs == labeled_pairs()
