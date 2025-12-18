"""
Enhanced CLI with analytics dashboard and memory support.
"""

import argparse
import sys
from rich import print
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.agents.researcher import ResearcherAgent
from src.agents.council import MarketingCouncil
from src.analytics.query_tracker import get_tracker
from src.memory.conversation_memory import get_memory

console = Console()

DEFAULT_COLLECTION = "growthboss-rag"


def cmd_analytics(args: argparse.Namespace):
	"""Show analytics dashboard."""
	tracker = get_tracker()
	metrics = tracker.get_metrics()
	insights = tracker.get_insights()
	
	console.print("\n[bold cyan]📊 Analytics Dashboard[/bold cyan]\n")
	
	# Metrics table
	table = Table(title="Performance Metrics", show_header=True, header_style="bold magenta")
	table.add_column("Metric", style="cyan")
	table.add_column("Value", style="green")
	
	table.add_row("Total Queries", str(metrics['total_queries']))
	table.add_row("Average Response Time", f"{metrics['avg_response_time']}s")
	table.add_row("Unique Queries", str(metrics['unique_queries']))
	table.add_row("Active Sessions", str(metrics['active_sessions']))
	
	console.print(table)
	
	# Top queries
	if insights['top_queries']:
		console.print("\n[bold cyan]🔍 Top Queries[/bold cyan]\n")
		query_table = Table(show_header=True, header_style="bold magenta")
		query_table.add_column("Query", style="cyan")
		query_table.add_column("Count", style="green")
		
		for item in insights['top_queries']:
			query_table.add_row(item['query'][:60], str(item['count']))
		
		console.print(query_table)
	
	# Recommendations
	if insights['recommendations']:
		console.print("\n[bold cyan]💡 Recommendations[/bold cyan]\n")
		for rec in insights['recommendations']:
			console.print(f"  • {rec}")


def cmd_ask_enhanced(args: argparse.Namespace):
	"""Enhanced ask command with memory and analytics."""
	memory = get_memory(args.session_id)
	
	if args.council:
		council = MarketingCouncil(args.collection or DEFAULT_COLLECTION)
		context = args.context or "GrowthBoss: Marketing agency"
		
		print("\n[bold magenta]🧠 Consulting Marketing Council...[/bold magenta]")
		answer = council.ask(
			args.q,
			context,
			show_deliberation=args.show_deliberation
		)
		
		# Save to memory
		memory.add_exchange(args.q, answer)
		
		print("\n[bold magenta]🎯 Marketing Council Answer[/bold magenta]\n")
		print(answer)
	else:
		researcher = ResearcherAgent(
			args.collection or DEFAULT_COLLECTION,
			use_enhanced=args.enhanced,
			session_id=args.session_id
		)
		
		res = researcher.research(args.q, k=args.k)
		
		print("\n[bold cyan]Answer[/bold cyan]\n")
		print(res["answer"])
		
		if args.show_evidence:
			print("\n[bold yellow]📚 Sources[/bold yellow]\n")
			for i, ev in enumerate(res["evidence"][:5], 1):
				meta = ev.get('metadata', {})
				title = meta.get('title', 'Unknown')
				print(f"{i}. {title}")
	
	if args.session_id:
		print(f"\n[dim]Session: {memory.session_id}[/dim]")


def main():
	parser = argparse.ArgumentParser(description="Enhanced GrowthBoss RAG CLI")
	subparsers = parser.add_subparsers(dest="command", help="Commands")
	
	# Ask command
	ask_parser = subparsers.add_parser("ask", help="Ask a question")
	ask_parser.add_argument("-q", "--q", required=True, help="Question")
	ask_parser.add_argument("-k", type=int, default=12, help="Number of results")
	ask_parser.add_argument("--collection", default=DEFAULT_COLLECTION)
	ask_parser.add_argument("--council", action="store_true", help="Use Marketing Council")
	ask_parser.add_argument("--context", help="Additional context")
	ask_parser.add_argument("--show-deliberation", action="store_true")
	ask_parser.add_argument("--show-evidence", action="store_true")
	ask_parser.add_argument("--enhanced", action="store_true", default=True, help="Use enhanced retrieval")
	ask_parser.add_argument("--session-id", help="Session ID for conversation memory")
	
	# Analytics command
	analytics_parser = subparsers.add_parser("analytics", help="Show analytics dashboard")
	
	args = parser.parse_args()
	
	if args.command == "ask":
		cmd_ask_enhanced(args)
	elif args.command == "analytics":
		cmd_analytics(args)
	else:
		parser.print_help()


if __name__ == "__main__":
	main()

