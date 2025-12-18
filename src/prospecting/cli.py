"""
CLI for Business Intelligence and Prospecting Tool
"""

import argparse
import json
from pathlib import Path
from rich import print
from rich.table import Table

from src.prospecting.business_intelligence import BusinessIntelligence


def cmd_sales_summary(args):
    """Display sales summary."""
    bi = BusinessIntelligence(
        apollo_api_key=args.apollo_key,
        hubspot_api_key=args.hubspot_key
    )
    
    print("[bold green]Fetching sales summary...[/bold green]")
    summary = bi.get_sales_summary()
    
    table = Table(title="Sales Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Deals", str(summary.get("total_deals", 0)))
    table.add_row("Closed Deals", str(summary.get("closed_deals", 0)))
    table.add_row("Open Deals", str(summary.get("open_deals", 0)))
    table.add_row("Total Revenue", f"${summary.get('total_revenue', 0):,.2f}")
    table.add_row("Open Pipeline Value", f"${summary.get('open_pipeline_value', 0):,.2f}")
    table.add_row("Average Deal Size", f"${summary.get('average_deal_size', 0):,.2f}")
    
    print(table)
    
    print("\n[bold]Top Clients:[/bold]")
    for i, client in enumerate(summary.get("top_clients", [])[:10], 1):
        print(f"{i}. {client.get('name', 'Unknown')}: ${client.get('amount', 0):,.2f}")


def cmd_clients(args):
    """List all client companies."""
    bi = BusinessIntelligence(
        apollo_api_key=args.apollo_key,
        hubspot_api_key=args.hubspot_key
    )
    
    print("[bold green]Fetching client companies...[/bold green]")
    clients = bi.get_client_companies()
    
    print(f"\n[bold]Found {len(clients)} client companies[/bold]\n")
    
    table = Table(title="Client Companies")
    table.add_column("Company", style="cyan")
    table.add_column("Industry", style="yellow")
    table.add_column("Deal Count", style="green")
    table.add_column("Total Value", style="magenta")
    
    for client in clients[:args.limit]:
        table.add_row(
            client.get("name", "Unknown"),
            client.get("industry", "N/A"),
            str(client.get("deal_count", 0)),
            f"${client.get('total_deal_value', 0):,.2f}"
        )
    
    print(table)


def cmd_pipeline(args):
    """Display pipeline information."""
    bi = BusinessIntelligence(
        apollo_api_key=args.apollo_key,
        hubspot_api_key=args.hubspot_key
    )
    
    print("[bold green]Fetching pipeline...[/bold green]")
    pipeline = bi.get_pipeline()
    
    for pipeline_id, pipeline_data in pipeline.items():
        print(f"\n[bold]Pipeline: {pipeline_data.get('label', 'Unknown')}[/bold]")
        
        table = Table(title="Pipeline Stages")
        table.add_column("Stage", style="cyan")
        table.add_column("Display Order", style="yellow")
        
        for stage in pipeline_data.get("stages", []):
            table.add_row(
                stage.get("label", "Unknown"),
                str(stage.get("display_order", 0))
            )
        
        print(table)


def cmd_find_similar(args):
    """Find companies similar to existing clients."""
    bi = BusinessIntelligence(
        apollo_api_key=args.apollo_key,
        hubspot_api_key=args.hubspot_key
    )
    
    # Get client companies
    clients = bi.get_client_companies()
    
    if not clients:
        print("[red]No client companies found. Cannot find similar companies.[/red]")
        return
    
    # Use first client or find by name
    target_client = clients[0]
    if args.client_name:
        for client in clients:
            if args.client_name.lower() in client.get("name", "").lower():
                target_client = client
                break
    
    print(f"[bold green]Finding companies similar to: {target_client.get('name', 'Unknown')}[/bold green]")
    
    similar = bi.find_similar_companies(target_client, limit=args.limit)
    
    print(f"\n[bold]Found {len(similar)} similar companies[/bold]\n")
    
    table = Table(title="Similar Companies")
    table.add_column("Company", style="cyan")
    table.add_column("Industry", style="yellow")
    table.add_column("Employees", style="green")
    table.add_column("Location", style="magenta")
    
    for company in similar[:args.limit]:
        table.add_row(
            company.get("name", "Unknown"),
            company.get("industry", "N/A"),
            str(company.get("employee_count", "N/A")),
            f"{company.get('city', '')}, {company.get('state', '')}"
        )
    
    print(table)


def cmd_find_decision_makers(args):
    """Find decision makers at companies."""
    bi = BusinessIntelligence(
        apollo_api_key=args.apollo_key,
        hubspot_api_key=args.hubspot_key
    )
    
    print(f"[bold green]Finding decision makers at: {args.company}[/bold green]")
    
    decision_makers = bi.find_decision_makers(
        company_name=args.company,
        company_domain=args.domain,
        limit=args.limit
    )
    
    print(f"\n[bold]Found {len(decision_makers)} decision makers[/bold]\n")
    
    table = Table(title="Decision Makers")
    table.add_column("Name", style="cyan")
    table.add_column("Title", style="yellow")
    table.add_column("Company", style="green")
    table.add_column("Email", style="magenta")
    table.add_column("LinkedIn", style="blue")
    
    for person in decision_makers[:args.limit]:
        table.add_row(
            person.get("full_name", "Unknown"),
            person.get("job_title", "N/A"),
            person.get("company", "N/A"),
            person.get("email", "N/A"),
            person.get("linkedin_url", "N/A")[:50] if person.get("linkedin_url") else "N/A"
        )
    
    print(table)


def cmd_sync_data(args):
    """Sync business data and save for RAG ingestion."""
    bi = BusinessIntelligence(
        apollo_api_key=args.apollo_key,
        hubspot_api_key=args.hubspot_key
    )
    
    print("[bold green]Syncing business data...[/bold green]")
    
    saved_files = bi.save_business_data()
    
    print("\n[bold green]✅ Data saved successfully![/bold green]")
    print("\nSaved files:")
    for key, filepath in saved_files.items():
        print(f"  • {key}: {filepath}")
    
    print("\n[bold]Next steps:[/bold]")
    print("1. Review the markdown file in data/business_intelligence/")
    print("2. Ingest into RAG system using:")
    print("   python src/ingest/local_files.py data/business_intelligence/business_intelligence_*.md")
    print("   python -c \"from src.ingest.ingest import chunk_and_save; chunk_and_save()\"")
    print("   python -c \"from src.rag.vectorstore import build_vectorstore; build_vectorstore()\"")


def main():
    parser = argparse.ArgumentParser(description="Business Intelligence and Prospecting Tool")
    
    # Global arguments
    parser.add_argument("--apollo-key", help="Apollo API key", default=None)
    parser.add_argument("--hubspot-key", help="HubSpot API key", default=None)
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Sales summary command
    subparsers.add_parser("sales", help="Display sales summary")
    
    # Clients command
    clients_parser = subparsers.add_parser("clients", help="List client companies")
    clients_parser.add_argument("--limit", type=int, default=20, help="Maximum number of clients to display")
    
    # Pipeline command
    subparsers.add_parser("pipeline", help="Display pipeline information")
    
    # Find similar command
    similar_parser = subparsers.add_parser("similar", help="Find companies similar to clients")
    similar_parser.add_argument("--client-name", help="Name of client company to match")
    similar_parser.add_argument("--limit", type=int, default=50, help="Maximum number of similar companies")
    
    # Decision makers command
    dm_parser = subparsers.add_parser("decision-makers", help="Find decision makers at companies")
    dm_parser.add_argument("--company", required=True, help="Company name")
    dm_parser.add_argument("--domain", help="Company domain")
    dm_parser.add_argument("--limit", type=int, default=25, help="Maximum number of decision makers")
    
    # Sync data command
    subparsers.add_parser("sync", help="Sync business data and save for RAG")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Set default API keys from environment if not provided
    import os
    if not args.apollo_key:
        args.apollo_key = os.getenv("APOLLO_API_KEY")
    if not args.hubspot_key:
        args.hubspot_key = os.getenv("HUBSPOT_API_KEY")
    
    # Execute command
    if args.command == "sales":
        cmd_sales_summary(args)
    elif args.command == "clients":
        cmd_clients(args)
    elif args.command == "pipeline":
        cmd_pipeline(args)
    elif args.command == "similar":
        cmd_find_similar(args)
    elif args.command == "decision-makers":
        cmd_find_decision_makers(args)
    elif args.command == "sync":
        cmd_sync_data(args)


if __name__ == "__main__":
    main()

