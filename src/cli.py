import argparse
import os

from rich import print

from src.ingest.crawl import run_crawl
from src.ingest.ingest import chunk_and_save
from src.rag.vectorstore import build_vectorstore, query
from src.agents.researcher import ResearcherAgent
from src.agents.synthesizer import SynthesizerAgent
from src.agents.critic import CriticAgent
from src.agents.council import MarketingCouncil


DEFAULT_COLLECTION = "growthboss-rag"


def cmd_ingest(args: argparse.Namespace) -> None:
	print("[bold green]Crawling sources...[/bold green]")
	sources_path = args.sources or os.path.join("src", "ingest", "sources.yaml")
	saved_raw = run_crawl(sources_path)
	print(f"Saved raw docs: {len(saved_raw)}")

	print("[bold green]Chunking...[/bold green]")
	saved_chunks = chunk_and_save()
	print(f"Saved chunks: {len(saved_chunks)}")

	print("[bold green]Building vector store...[/bold green]")
	collection = args.collection or DEFAULT_COLLECTION
	_, name = build_vectorstore(collection)
	print(f"Vector store ready: {name}")


def cmd_ask(args: argparse.Namespace) -> None:
	collection = args.collection or DEFAULT_COLLECTION
	
	if args.council:
		# Use Marketing Council
		council = MarketingCouncil(collection)
		context = args.context or "GrowthBoss: Marketing agency focused on client acquisition, offer design, content-led inbound, outbound SDR support, profitable delivery SLAs."
		answer = council.ask(args.q, context, show_deliberation=args.show_deliberation)
		print("\n[bold magenta]🎯 Marketing Council Answer[/bold magenta]\n")
		print(answer)
	else:
		# Use simple researcher
		researcher = ResearcherAgent(collection)
		res = researcher.research(args.q, k=args.k)
		print("\n[bold cyan]Answer[/bold cyan]\n")
		print(res["answer"])

		if args.show_context:
			print("\n[dim]Top Sources[/dim]")
			for r in res["evidence"][:args.k]:
				print(f"- {r['metadata'].get('source','unknown')} (score={r['score']:.3f})")


def cmd_council(args: argparse.Namespace) -> None:
	"""Ask the Marketing Council - mentors debate and synthesize answers."""
	collection = args.collection or DEFAULT_COLLECTION
	council = MarketingCouncil(collection)
	
	context = args.context or "GrowthBoss: Marketing agency focused on client acquisition, offer design, content-led inbound, outbound SDR support, profitable delivery SLAs."
	
	print("\n[bold yellow]🧠 Consulting Marketing Council...[/bold yellow]")
	print("[dim]Gary Vee, Alex Hormozi, and Iman Gadzhi are deliberating...[/dim]\n")
	
	answer = council.ask(args.q, context, show_deliberation=args.show_deliberation)
	
	print("\n" + "="*80)
	print("[bold magenta]📋 COUNCIL SYNTHESIS FOR GROWTHBOSS[/bold magenta]")
	print("="*80 + "\n")
	print(answer)
	print("\n" + "="*80)


def cmd_brief(args: argparse.Namespace) -> None:
	collection = args.collection or DEFAULT_COLLECTION
	researcher = ResearcherAgent(collection)
	res = researcher.research(args.topic, k=12)

	synth = SynthesizerAgent()
	planner = synth.synthesize(args.topic, res["answer"], args.context)

	critic = CriticAgent()
	improved = critic.critique(planner)

	print("\n[bold magenta]GrowthBoss Strategic Brief[/bold magenta]\n")
	print(improved)


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="GrowthBoss RAG Agents CLI")
	sub = parser.add_subparsers(dest="cmd", required=True)

	pi = sub.add_parser("ingest", help="Crawl, chunk, and build vector store")
	pi.add_argument("--sources", help="Path to sources.yaml")
	pi.add_argument("--collection", help="Vector store collection name")
	pi.set_defaults(func=cmd_ingest)

	pa = sub.add_parser("ask", help="Ask a question against RAG")
	pa.add_argument("--q", required=True, help="Question to ask")
	pa.add_argument("--k", type=int, default=8, help="Top-k results")
	pa.add_argument("--show-context", action="store_true")
	pa.add_argument("--council", action="store_true", help="Use Marketing Council (mentors debate)")
	pa.add_argument("--show-deliberation", action="store_true", help="Show individual mentor responses (with --council)")
	pa.add_argument("--context", help="GrowthBoss context for council")
	pa.add_argument("--collection", help="Vector store collection name")
	pa.set_defaults(func=cmd_ask)

	pc = sub.add_parser("council", help="Ask Marketing Council (mentors debate and synthesize)")
	pc.add_argument("--q", required=True, help="Question to ask the council")
	pc.add_argument("--context", help="GrowthBoss context")
	pc.add_argument("--show-deliberation", action="store_true", help="Show individual mentor responses")
	pc.add_argument("--collection", help="Vector store collection name")
	pc.set_defaults(func=cmd_council)

	pb = sub.add_parser("brief", help="Generate GrowthBoss strategic brief")
	pb.add_argument("--topic", required=True, help="Brief topic or goal")
	pb.add_argument("--context", default="Our focus: agency client acquisition, offer design, content-led inbound, outbound SDR support, profitable delivery SLAs.")
	pb.add_argument("--collection", help="Vector store collection name")
	pb.set_defaults(func=cmd_brief)

	return parser


def main() -> None:
	parser = build_parser()
	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
