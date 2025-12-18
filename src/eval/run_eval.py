import json
import argparse
from pathlib import Path

from src.agents.researcher import ResearcherAgent


def run_eval(collection: str, bench_path: str, k: int = 8) -> None:
    agent = ResearcherAgent(collection)
    bench = json.loads(Path(bench_path).read_text(encoding="utf-8"))
    results = []
    for item in bench:
        q = item["q"]
        res = agent.research(q, k=k)
        results.append({"q": q, "answer": res["answer"]})
    out_path = Path(bench_path).with_suffix(".out.json")
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--collection", default="growthboss-rag")
    p.add_argument("--bench", default="src/eval/bench.json")
    p.add_argument("--k", type=int, default=8)
    args = p.parse_args()
    run_eval(args.collection, args.bench, args.k)


if __name__ == "__main__":
    main()


