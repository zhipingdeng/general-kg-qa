"""Tests for evaluation metrics."""
import pytest
from app.eval.metrics import (
    compute_retrieval_metrics,
    compute_generation_metrics,
    compute_aggregate_metrics,
    EvalResult,
    RetrievalMetrics,
    GenerationMetrics,
)


class TestRetrievalMetrics:
    def test_perfect_retrieval(self):
        metrics = compute_retrieval_metrics(
            retrieved_ids=["a", "b", "c"],
            relevant_ids=["a", "b", "c"],
            k=3,
        )
        assert metrics.recall_at_k == 1.0
        assert metrics.precision_at_k == 1.0
        assert metrics.mrr == 1.0
        assert metrics.hit_rate == 1.0
        assert metrics.ndcg == 1.0

    def test_no_relevant_retrieved(self):
        metrics = compute_retrieval_metrics(
            retrieved_ids=["x", "y", "z"],
            relevant_ids=["a", "b", "c"],
            k=3,
        )
        assert metrics.recall_at_k == 0.0
        assert metrics.precision_at_k == 0.0
        assert metrics.mrr == 0.0
        assert metrics.hit_rate == 0.0
        assert metrics.ndcg == 0.0

    def test_partial_retrieval(self):
        metrics = compute_retrieval_metrics(
            retrieved_ids=["a", "x", "b", "y", "c"],
            relevant_ids=["a", "b", "c"],
            k=5,
        )
        assert metrics.recall_at_k == 1.0  # all 3 relevant found
        assert metrics.precision_at_k == 0.6  # 3/5
        assert metrics.mrr == 1.0  # first relevant at rank 1
        assert metrics.hit_rate == 1.0

    def test_first_relevant_at_rank_2(self):
        metrics = compute_retrieval_metrics(
            retrieved_ids=["x", "a", "y"],
            relevant_ids=["a"],
            k=3,
        )
        assert metrics.mrr == 0.5  # 1/2
        assert metrics.recall_at_k == 1.0
        assert metrics.hit_rate == 1.0

    def test_empty_relevant(self):
        metrics = compute_retrieval_metrics(
            retrieved_ids=["a", "b"],
            relevant_ids=[],
            k=2,
        )
        assert metrics.recall_at_k == 0.0
        assert metrics.precision_at_k == 0.0

    def test_k_cutoff(self):
        """Only top-k retrieved docs should matter for recall/precision."""
        metrics = compute_retrieval_metrics(
            retrieved_ids=["x", "x", "x", "a"],
            relevant_ids=["a"],
            k=3,
        )
        assert metrics.recall_at_k == 0.0  # a is at rank 4, beyond k=3
        assert metrics.hit_rate == 0.0


class TestGenerationMetrics:
    def test_exact_match(self):
        metrics = compute_generation_metrics("苹果是水果", "苹果是水果")
        assert metrics.exact_match is True
        assert metrics.f1_score == 1.0
        assert metrics.contains_answer is True

    def test_partial_match(self):
        metrics = compute_generation_metrics("苹果是一种常见的水果", "苹果是水果")
        assert metrics.exact_match is False
        assert metrics.f1_score > 0.3
        assert metrics.contains_answer is True

    def test_no_match(self):
        metrics = compute_generation_metrics("太阳从西边升起", "苹果是水果")
        assert metrics.exact_match is False
        assert metrics.f1_score < 0.3
        assert metrics.contains_answer is False

    def test_contains_answer_with_extra_info(self):
        metrics = compute_generation_metrics(
            "大龙湫的门票价格是50元，位于浙江温州",
            "50元",
        )
        assert metrics.contains_answer is True
        assert metrics.f1_score > 0.0


class TestAggregateMetrics:
    def test_aggregate(self):
        results = [
            EvalResult(
                question="q1",
                reference_answer="a1",
                generated_answer="a1",
                retrieved_entities=["e1"],
                retrieval=RetrievalMetrics(1.0, 1.0, 1.0, 1.0, 1.0),
                generation=GenerationMetrics(True, 1.0, True, 0.9),
                latency_ms=100.0,
            ),
            EvalResult(
                question="q2",
                reference_answer="a2",
                generated_answer="wrong",
                retrieved_entities=[],
                retrieval=RetrievalMetrics(0.0, 0.0, 0.0, 0.0, 0.0),
                generation=GenerationMetrics(False, 0.0, False, 0.1),
                latency_ms=200.0,
            ),
        ]
        agg = compute_aggregate_metrics(results)
        assert agg["total_questions"] == 2
        assert agg["retrieval"]["recall@5"] == 0.5
        assert agg["generation"]["exact_match"] == 0.5
        assert agg["latency"]["avg_ms"] == 150.0
