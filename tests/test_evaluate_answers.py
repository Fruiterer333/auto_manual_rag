import argparse
import json

from app.core.config import Settings
from app.data.schemas.models import Citation, QueryResponse
from app.evaluation.answer_evaluator import AnswerEvalCase
from app.rag.chains.qa_chain import AnswerGenerationTrace
from app.rag.prompts.answer_prompt import PromptEvidenceSnapshot
from scripts import evaluate_answers


def test_answer_runner_writes_auditable_json_without_real_llm(tmp_path, monkeypatch) -> None:
    markdown_path = tmp_path / "answer_eval_v4.md"
    json_path = tmp_path / "answer_eval_v4.json"
    dataset_path = tmp_path / "answer_eval.jsonl"
    dataset_path.write_text("{}\n", encoding="utf-8")
    case = AnswerEvalCase(
        id="case-1",
        question="如何操作？",
        answer_type="procedure",
        source_case_id="retrieval-case-1",
    )
    snapshot = PromptEvidenceSnapshot(
        evidence_id="E1",
        order=1,
        chunk_id="chunk-1",
        page=158,
        chapter="启动和驾驶",
        section="电子驻车制动（EPB）",
        subsection="释放电子驻车制动（EPB）",
        heading_path="启动和驾驶 > 电子驻车制动（EPB） > 释放电子驻车制动（EPB）",
        content_type="procedure",
        text="踩下制动踏板并按下EPB开关。",
        truncated=False,
        original_text_chars=16,
        prompt_text_chars=16,
    )
    response = QueryResponse(
        question=case.question,
        answer="踩下制动踏板并按下EPB开关。",
        retrieval_mode="hybrid",
        citations=[
            Citation(
                source_file="manual.pdf",
                page=158,
                chunk_id="chunk-1",
                quote="按下EPB开关。",
            )
        ],
    )

    class FakeQAChain:
        def __init__(self, settings) -> None:
            self.settings = settings

        def answer_with_trace(self, question, top_k, retrieval_mode):
            assert question == case.question
            return AnswerGenerationTrace(
                response=response,
                raw_answer="根据 Evidence E1，踩下制动踏板并按下EPB开关。",
                final_answer=response.answer,
                prompt_evidence=(snapshot,),
            )

    monkeypatch.setattr(
        evaluate_answers,
        "parse_args",
        lambda: argparse.Namespace(
            dataset=str(dataset_path),
            output=str(markdown_path),
            json_output=str(json_path),
            retrieval_mode="hybrid",
            top_k=5,
            limit=1,
            split="dev",
        ),
    )
    monkeypatch.setattr(evaluate_answers, "get_settings", lambda: Settings())
    monkeypatch.setattr(evaluate_answers, "load_answer_eval_cases", lambda *args, **kwargs: [case])
    monkeypatch.setattr(evaluate_answers, "QAChain", FakeQAChain)
    monkeypatch.setattr(
        evaluate_answers,
        "collect_ollama_runtime_metadata",
        lambda settings: {
            "ollama_version": "0.test",
            "ollama_model_digest": "sha256:test",
        },
    )

    evaluate_answers.main()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    result = payload["results"][0]
    assert result["raw_answer"].startswith("根据 Evidence E1")
    assert result["final_answer"] == response.answer
    assert result["prompt_evidence"][0]["evidence_id"] == "E1"
    assert result["prompt_evidence"][0]["text"] == snapshot.text
    assert result["citations"][0]["quote"] != snapshot.text
    assert payload["semantics_version"] == "v4.3"
    assert payload["config"]["answer_eval_semantics_version"] == "v4.3"
    assert len(payload["config"]["answer_eval_dataset_sha256"]) == 64
    assert payload["config"]["generation_temperature"] == 0.0
    assert payload["config"]["generation_temperature_source"] == "settings_explicit"
    assert payload["config"]["generation_seed"] == 42
    assert payload["config"]["generation_seed_source"] == "settings_explicit"
    assert payload["config"]["generation_options"] == {"temperature": 0.0, "seed": 42}
    assert payload["config"]["generation_options_source"] == "settings_explicit"
    assert payload["config"]["generation_timeout_seconds"] == 120
    assert payload["config"]["ollama_version"] == "0.test"
    assert payload["config"]["ollama_model_digest"] == "sha256:test"


def test_formal_baseline_default_name_includes_mode_rerank_and_timestamp() -> None:
    path = evaluate_answers._default_output_path(
        retrieval_mode="hybrid",
        rerank_enabled=False,
    )

    assert path.parent.as_posix() == "reports/evaluation"
    assert path.name.startswith("v4_answer_baseline_hybrid_no_rerank_")
    assert path.suffix == ".md"
