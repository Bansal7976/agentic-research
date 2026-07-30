"""LangSmith evaluation: measures report quality with an LLM-as-judge.

Run:  python evals/run_evals.py     (needs LANGSMITH_API_KEY + GOOGLE_API_KEY in .env,
                                     and the local stack running: see README quickstart)
Results appear at smith.langchain.com under experiments.
"""
import os

import httpx
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import Client
from pydantic import BaseModel, Field

load_dotenv()

DATASET = "research-topics-v1"
API_URL = os.getenv("EVAL_TARGET_URL", "http://localhost:8000")
API_KEY = os.getenv("SERVICE_API_KEY", "dev-secret-key")

EXAMPLES = [
    {"topic": "Impact of AI on the Indian job market"},
    {"topic": "How does UPI work and why did it succeed"},
    {"topic": "Pros and cons of electric vehicles in India"},
    {"topic": "What is quantum computing in simple terms"},
    {"topic": "History and future of ISRO's space missions"},
]


class Judgement(BaseModel):
    score: float = Field(ge=0, le=1, description="0 = terrible, 1 = excellent")
    reasoning: str


judge = ChatGoogleGenerativeAI(
    model="gemini-flash-lite-latest", temperature=0
).with_structured_output(
    Judgement
)


def make_judge(criterion: str, instruction: str):
    def evaluator(run, example):
        report = run.outputs.get("report", "") if run.outputs else ""
        topic = example.inputs["topic"]
        verdict = judge.invoke(
            f"You are grading a research report on: '{topic}'.\n"
            f"Criterion — {criterion}: {instruction}\n\nReport:\n{report[:8000]}"
        )
        return {"key": criterion, "score": verdict.score, "comment": verdict.reasoning}

    return evaluator


def target(inputs: dict) -> dict:
    r = httpx.post(
        f"{API_URL}/research",
        json={"topic": inputs["topic"]},
        headers={"X-API-Key": API_KEY},
        timeout=600,
    )
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    client = Client()
    if not client.has_dataset(dataset_name=DATASET):
        ds = client.create_dataset(DATASET)
        client.create_examples(inputs=EXAMPLES, dataset_id=ds.id)

    results = client.evaluate(
        target,
        data=DATASET,
        evaluators=[
            make_judge("relevance", "Does the report actually address the topic?"),
            make_judge("structure",
                       "Is it well-organized: summary, sections, conclusion, sources?"),
            make_judge("groundedness", "Are claims supported by the cited sources (URLs present)?"),
        ],
        experiment_prefix="research-eval",
        max_concurrency=1,
    )
    print("Done. View experiment:", results.experiment_name)
