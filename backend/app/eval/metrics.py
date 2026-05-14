"""RAG Evaluation Metrics - Retrieval and Generation quality measurement."""

from dataclasses import dataclass


@dataclass
class RetrievalMetrics:
    """Metrics for document retrieval quality."""
    recall_at_k: float  # relevant docs retrieved / total relevant docs
    precision_at_k: float  # relevant docs retrieved / total retrieved
    mrr: float  # Mean Reciprocal Rank
    hit_rate: float  # at least one relevant doc retrieved
    ndcg: float  # Normalized Discounted Cumulative Gain


@dataclass
class GenerationMetrics:
    """Metrics for answer generation quality."""
    exact_match: bool  # answer exactly matches reference
    f1_score: float  # token-level F1 between answer and reference
    contains_answer: bool  # reference answer is contained in generated answer
    faithfulness: float  # 0-1, how well answer is grounded in context (LLM judge)


@dataclass
class EvalResult:
    """Single evaluation result."""
    question: str
    reference_answer: str
    generated_answer: str
    retrieved_entities: list[str]
    retrieval: RetrievalMetrics
    generation: GenerationMetrics
    latency_ms: float


def compute_retrieval_metrics(
    retrieved_ids: list[str],
    relevant_ids: list[str],
    k: int = 5,
) -> RetrievalMetrics:
    """Compute retrieval metrics given retrieved and relevant document IDs.

    Args:
        retrieved_ids: List of retrieved document/entity IDs (ordered by rank).
        relevant_ids: List of ground-truth relevant document/entity IDs.
        k: Cutoff for top-K metrics.

    Returns:
        RetrievalMetrics with recall@k, precision@k, MRR, hit_rate, NDCG@k.
    """
    retrieved_at_k = retrieved_ids[:k]
    relevant_set = set(relevant_ids)

    if not relevant_set:
        return RetrievalMetrics(0.0, 0.0, 0.0, 0.0, 0.0)

    # Recall@K
    hits = sum(1 for doc_id in retrieved_at_k if doc_id in relevant_set)
    recall = hits / len(relevant_set)

    # Precision@K
    precision = hits / len(retrieved_at_k) if retrieved_at_k else 0.0

    # MRR (Reciprocal Rank of first relevant doc)
    mrr = 0.0
    for i, doc_id in enumerate(retrieved_ids):
        if doc_id in relevant_set:
            mrr = 1.0 / (i + 1)
            break

    # Hit Rate
    hit_rate = 1.0 if hits > 0 else 0.0

    # NDCG@K
    ndcg = _compute_ndcg(retrieved_at_k, relevant_set, k)

    return RetrievalMetrics(
        recall_at_k=recall,
        precision_at_k=precision,
        mrr=mrr,
        hit_rate=hit_rate,
        ndcg=ndcg,
    )


def _compute_ndcg(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Compute NDCG@K."""
    import math

    # DCG
    dcg = 0.0
    for i, doc_id in enumerate(retrieved[:k]):
        rel = 1.0 if doc_id in relevant else 0.0
        dcg += rel / math.log2(i + 2)  # i+2 because log2(1) = 0

    # Ideal DCG
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_hits))

    return dcg / idcg if idcg > 0 else 0.0


def compute_generation_metrics(
    generated: str,
    reference: str,
) -> GenerationMetrics:
    """Compute generation metrics.

    Args:
        generated: Model-generated answer.
        reference: Ground-truth reference answer.

    Returns:
        GenerationMetrics with exact_match, f1, contains_answer, faithfulness.
    """
    gen_norm = generated.strip().lower()
    ref_norm = reference.strip().lower()

    # Exact Match
    exact_match = gen_norm == ref_norm

    # Contains Answer
    contains_answer = ref_norm in gen_norm or _token_overlap(ref_norm, gen_norm) > 0.8

    # F1 Score (token-level)
    f1 = _compute_f1(gen_norm, ref_norm)

    # Faithfulness placeholder (requires LLM judge, set to 0 by default)
    faithfulness = 0.0

    return GenerationMetrics(
        exact_match=exact_match,
        f1_score=f1,
        contains_answer=contains_answer,
        faithfulness=faithfulness,
    )


def _tokenize(text: str) -> list[str]:
    """Simple character-level tokenization for Chinese text."""
    tokens = []
    for char in text:
        if char.strip() and char not in "，。、：；！？""''（）【】《》":
            tokens.append(char)
    return tokens


def _compute_f1(prediction: str, reference: str) -> float:
    """Compute token-level F1 between prediction and reference."""
    pred_tokens = _tokenize(prediction)
    ref_tokens = _tokenize(reference)

    if not pred_tokens or not ref_tokens:
        return 0.0

    # Count common tokens (respecting duplicates)
    from collections import Counter
    pred_counter = Counter(pred_tokens)
    ref_counter = Counter(ref_tokens)
    common_count = sum((pred_counter & ref_counter).values())

    if common_count == 0:
        return 0.0

    precision = common_count / len(pred_tokens)
    recall = common_count / len(ref_tokens)
    return 2 * precision * recall / (precision + recall)


def _token_overlap(text1: str, text2: str) -> float:
    """Compute token overlap ratio."""
    tokens1 = set(_tokenize(text1))
    tokens2 = set(_tokenize(text2))
    if not tokens1 or not tokens2:
        return 0.0
    common = tokens1 & tokens2
    return len(common) / min(len(tokens1), len(tokens2))


def compute_aggregate_metrics(results: list[EvalResult]) -> dict:
    """Compute aggregate metrics across all evaluation results.

    Args:
        results: List of EvalResult from individual evaluations.

    Returns:
        Dict with aggregate metrics.
    """
    if not results:
        return {}

    n = len(results)

    # Retrieval aggregates
    avg_recall = sum(r.retrieval.recall_at_k for r in results) / n
    avg_precision = sum(r.retrieval.precision_at_k for r in results) / n
    avg_mrr = sum(r.retrieval.mrr for r in results) / n
    avg_hit_rate = sum(r.retrieval.hit_rate for r in results) / n
    avg_ndcg = sum(r.retrieval.ndcg for r in results) / n

    # Generation aggregates
    exact_match_rate = sum(1 for r in results if r.generation.exact_match) / n
    avg_f1 = sum(r.generation.f1_score for r in results) / n
    contains_rate = sum(1 for r in results if r.generation.contains_answer) / n
    avg_faithfulness = sum(r.generation.faithfulness for r in results) / n

    # Latency
    avg_latency = sum(r.latency_ms for r in results) / n
    p50_latency = sorted(r.latency_ms for r in results)[n // 2]
    p95_latency = sorted(r.latency_ms for r in results)[int(n * 0.95)]

    return {
        "total_questions": n,
        "retrieval": {
            "recall@5": round(avg_recall, 4),
            "precision@5": round(avg_precision, 4),
            "mrr": round(avg_mrr, 4),
            "hit_rate": round(avg_hit_rate, 4),
            "ndcg@5": round(avg_ndcg, 4),
        },
        "generation": {
            "exact_match": round(exact_match_rate, 4),
            "f1_score": round(avg_f1, 4),
            "contains_answer": round(contains_rate, 4),
            "faithfulness": round(avg_faithfulness, 4),
        },
        "latency": {
            "avg_ms": round(avg_latency, 1),
            "p50_ms": round(p50_latency, 1),
            "p95_ms": round(p95_latency, 1),
        },
    }
