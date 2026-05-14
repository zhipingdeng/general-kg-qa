"""RAG Evaluation Runner - Evaluate retrieval and generation quality."""

import asyncio
import time
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import get_settings
from app.database.neo4j_client import Neo4jClient
from app.database.milvus_client import MilvusClient
from app.rag.embeddings import EmbeddingService
from app.rag.bm25_retriever import BM25Retriever
from app.rag.hyde import HyDEGenerator
from app.rag.hybrid_retriever import HybridRetriever
from app.rag.query_rewriter import QueryRewriter
from app.qa.entity_linker import EntityLinker
from app.qa.subgraph_retriever import SubgraphRetriever
from app.qa.answer_generator import AnswerGenerator
from app.qa.pipeline import QAPipeline
from app.eval.metrics import (
    compute_retrieval_metrics,
    compute_generation_metrics,
    compute_aggregate_metrics,
    EvalResult,
)
from app.eval.dataset import load_kgclue_dataset, EvalSample

KGCLUE_PATH = "/mnt/e/hermes_code_workspace/dataset/通用百科数据集/KgCLUE/datasets/test_public.json"


async def build_pipeline() -> tuple[QAPipeline, Neo4jClient]:
    """Initialize the full QA pipeline for evaluation."""
    settings = get_settings()

    # Neo4j
    neo4j = Neo4jClient(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
    await neo4j.connect()

    # Milvus
    milvus = MilvusClient(host=settings.milvus_host, port=settings.milvus_port)

    # Embedding
    embedding = EmbeddingService(base_url=settings.embedding_base_url, model=settings.embedding_model)

    # HyDE
    hyde = HyDEGenerator(settings.llm_model_name, settings.llm_base_url, settings.llm_api_key)

    # BM25
    bm25 = BM25Retriever()
    try:
        docs = milvus.load_all_docs(settings.milvus_collection)
        bm25.build_index(docs)
    except Exception:
        pass

    # Query Rewriter
    query_rewriter = QueryRewriter(settings.llm_model_name, settings.llm_base_url, settings.llm_api_key)

    # Entity Linker
    entity_linker = EntityLinker()
    try:
        result = await neo4j.execute(
            "MATCH (n:Entity {source: 'ownthink'}) RETURN n.name AS name LIMIT 10000"
        )
        entity_names = [r["name"] for r in result if r.get("name")]
        entity_linker.load_from_neo4j(entity_names)
    except Exception:
        pass

    # Graph Retriever
    graph_retriever = SubgraphRetriever(neo4j)

    # Hybrid Retriever
    retriever = HybridRetriever(
        milvus=milvus,
        embedding=embedding,
        bm25=bm25,
        hyde=hyde,
        collection=settings.milvus_collection,
        query_rewriter=query_rewriter,
        graph_retriever=graph_retriever,
        entity_linker=entity_linker,
    )

    # Answer Generator
    generator = AnswerGenerator(settings.llm_model_name, settings.llm_base_url, settings.llm_api_key)

    # Pipeline
    pipeline = QAPipeline(retriever, generator)
    return pipeline, neo4j


async def evaluate_sample(
    pipeline: QAPipeline,
    sample: EvalSample,
    entity_names: set[str],
) -> EvalResult:
    """Evaluate a single question through the pipeline."""
    t0 = time.monotonic()

    # Run pipeline
    result = await pipeline.answer(sample.question)
    latency_ms = (time.monotonic() - t0) * 1000

    # Retrieval metrics: check if the correct entity was retrieved
    retrieved_entities = result.entities
    relevant_entities = [sample.entity]

    retrieval = compute_retrieval_metrics(
        retrieved_ids=retrieved_entities,
        relevant_ids=relevant_entities,
        k=5,
    )

    # Generation metrics: compare generated answer with reference
    generation = compute_generation_metrics(
        generated=result.answer,
        reference=sample.reference_answer,
    )

    return EvalResult(
        question=sample.question,
        reference_answer=sample.reference_answer,
        generated_answer=result.answer,
        retrieved_entities=retrieved_entities,
        retrieval=retrieval,
        generation=generation,
        latency_ms=latency_ms,
    )


async def main():
    """Run full evaluation."""
    print("=" * 60)
    print("RAG Evaluation - General KG-QA")
    print("=" * 60)

    # Build pipeline
    print("\n[1/4] Building pipeline...")
    pipeline, neo4j = await build_pipeline()

    # Load entity names
    print("[2/4] Loading entity names from Neo4j...")
    result = await neo4j.execute(
        "MATCH (n:Entity {source: 'ownthink'}) RETURN n.name AS name"
    )
    entity_names = {r["name"] for r in result if r.get("name")}
    print(f"  Loaded {len(entity_names)} entity names")

    # Load evaluation dataset
    print("[3/4] Loading KgCLUE evaluation dataset...")
    samples = load_kgclue_dataset(KGCLUE_PATH, entity_names, max_samples=50)
    print(f"  Loaded {len(samples)} evaluation samples")

    if not samples:
        print("  No matching samples found. Exiting.")
        await neo4j.close()
        return

    # Run evaluation
    print(f"[4/4] Evaluating {len(samples)} questions...")
    results = []
    for i, sample in enumerate(samples):
        try:
            eval_result = await evaluate_sample(pipeline, sample, entity_names)
            results.append(eval_result)

            # Progress
            status = "✓" if eval_result.generation.contains_answer else "✗"
            print(f"  [{i+1}/{len(samples)}] {status} "
                  f"F1={eval_result.generation.f1_score:.2f} "
                  f"Hit={eval_result.retrieval.hit_rate:.0f} "
                  f"{eval_result.latency_ms:.0f}ms "
                  f"Q: {sample.question[:30]}...")
        except Exception as e:
            print(f"  [{i+1}/{len(samples)}] ERROR: {e}")

    # Aggregate results
    if results:
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        agg = compute_aggregate_metrics(results)
        print(json.dumps(agg, indent=2, ensure_ascii=False))

        # Save detailed results
        output_path = os.path.join(os.path.dirname(__file__), "eval_results.json")
        detailed = []
        for r in results:
            detailed.append({
                "question": r.question,
                "reference": r.reference_answer,
                "generated": r.generated_answer,
                "entities": r.retrieved_entities,
                "retrieval": {
                    "recall": r.retrieval.recall_at_k,
                    "precision": r.retrieval.precision_at_k,
                    "mrr": r.retrieval.mrr,
                    "hit_rate": r.retrieval.hit_rate,
                },
                "generation": {
                    "exact_match": r.generation.exact_match,
                    "f1": r.generation.f1_score,
                    "contains": r.generation.contains_answer,
                },
                "latency_ms": r.latency_ms,
            })

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"aggregate": agg, "details": detailed}, f, indent=2, ensure_ascii=False)
        print(f"\nDetailed results saved to: {output_path}")

    await neo4j.close()


if __name__ == "__main__":
    asyncio.run(main())
