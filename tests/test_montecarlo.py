import json

from src.montecarlo import simulate_keyword_coverage


def test_simulation_is_reproducible_with_same_seed():
    words = [("文档", 14), ("词云", 13), ("分词", 10), ("停用词", 11)]
    first = simulate_keyword_coverage(words, 757, 94, trials=1000, seed=42)
    second = simulate_keyword_coverage(words, 757, 94, trials=1000, seed=42)
    assert first == second


def test_simulation_returns_valid_probabilities():
    words = [("文档", 10), ("词云", 8), ("分词", 6)]
    result = simulate_keyword_coverage(words, 300, 80, trials=2000, threshold=0.5)
    assert 0 <= result.mean_coverage <= 1
    assert 0 <= result.p05 <= result.p95 <= 1
    assert 0 <= result.pass_probability <= 1
    assert result.keyword_count == 3


def test_empty_input_raises():
    import pytest

    with pytest.raises(ValueError):
        simulate_keyword_coverage([], 0, 10)


def test_result_serializes_to_json():
    words = [("文档", 10), ("词云", 8)]
    payload = simulate_keyword_coverage(words, 100, 40, trials=100).to_dict()
    assert set(payload) >= {"trials", "mean_coverage", "pass_probability"}
    json.dumps(payload, ensure_ascii=False)
