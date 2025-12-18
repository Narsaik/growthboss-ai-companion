"""
CLI Interface for Lead Scraper
Command-line interface for scraping leads from HubSpot and Apollo.
"""

import argparse
import json
import sys
from typing import Optional
from .scraper import LeadScraper


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Lead Scraper - Scrape leads from HubSpot and Apollo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape leads from both sources
  python -m src.lead_scraper.cli --output leads.json

  # Scrape only from HubSpot
  python -m src.lead_scraper.cli --source hubspot --output hubspot_leads.json

  # Scrape with filters
  python -m src.lead_scraper.cli --job-title "CEO" --company "Tech Corp" --output ceos.json

  # Scrape from Apollo with location filter
  python -m src.lead_scraper.cli --source apollo --location "San Francisco, CA" --output sf_leads.json

  # Export as CSV
  python -m src.lead_scraper.cli --output leads.csv --format csv

  # Filter results
  python -m src.lead_scraper.cli --require-email --require-company --output filtered_leads.json
        """
    )
    
    # Source selection
    parser.add_argument(
        "--source",
        choices=["hubspot", "apollo", "both"],
        default="both",
        help="Source to scrape from (default: both)"
    )
    
    # Output options
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output file path (JSON or CSV)"
    )
    
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Output format (default: json)"
    )
    
    # Limit
    parser.add_argument(
        "-l", "--limit",
        type=int,
        help="Maximum number of leads per source"
    )
    
    # HubSpot filters
    parser.add_argument(
        "--job-title",
        type=str,
        help="Filter by job title (HubSpot)"
    )
    
    parser.add_argument(
        "--company",
        type=str,
        help="Filter by company name"
    )
    
    parser.add_argument(
        "--industry",
        type=str,
        help="Filter by industry (HubSpot)"
    )
    
    # Apollo filters
    parser.add_argument(
        "--job-titles",
        type=str,
        nargs="+",
        help="Filter by job titles (Apollo) - can specify multiple"
    )
    
    parser.add_argument(
        "--locations",
        type=str,
        nargs="+",
        help="Filter by locations (Apollo) - can specify multiple"
    )
    
    parser.add_argument(
        "--seniorities",
        type=str,
        nargs="+",
        help="Filter by seniority levels (Apollo) - e.g., VP, Director"
    )
    
    parser.add_argument(
        "--departments",
        type=str,
        nargs="+",
        help="Filter by departments (Apollo) - e.g., Sales, Marketing"
    )
    
    parser.add_argument(
        "--keywords",
        type=str,
        help="Keywords to search for (Apollo)"
    )
    
    # Result filtering
    parser.add_argument(
        "--require-email",
        action="store_true",
        help="Require email address"
    )
    
    parser.add_argument(
        "--require-phone",
        action="store_true",
        help="Require phone number"
    )
    
    parser.add_argument(
        "--require-company",
        action="store_true",
        help="Require company name"
    )
    
    parser.add_argument(
        "--job-title-keywords",
        type=str,
        nargs="+",
        help="Filter by job title keywords in results"
    )
    
    parser.add_argument(
        "--company-keywords",
        type=str,
        nargs="+",
        help="Filter by company keywords in results"
    )
    
    # Display options
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Display summary statistics"
    )
    
    parser.add_argument(
        "--show",
        type=int,
        help="Show first N leads in console"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize scraper
        scraper = LeadScraper()
        
        # Determine sources
        sources = []
        if args.source == "both":
            sources = ["hubspot", "apollo"]
        else:
            sources = [args.source]
        
        # Prepare filters
        hubspot_filters = {}
        apollo_filters = {}
        
        if args.job_title:
            hubspot_filters["job_title"] = args.job_title
        if args.company:
            hubspot_filters["company"] = args.company
            apollo_filters["company_name"] = args.company
        if args.industry:
            hubspot_filters["industry"] = args.industry
        if args.limit:
            hubspot_filters["limit"] = args.limit
            apollo_filters["limit"] = args.limit
        
        if args.job_titles:
            apollo_filters["job_titles"] = args.job_titles
        if args.locations:
            apollo_filters["locations"] = args.locations
        if args.seniorities:
            apollo_filters["seniorities"] = args.seniorities
        if args.departments:
            apollo_filters["departments"] = args.departments
        if args.keywords:
            apollo_filters["keywords"] = args.keywords
        
        # Scrape leads
        print(f"Scraping leads from: {', '.join(sources)}")
        leads = scraper.scrape_all_leads(
            sources=sources,
            hubspot_filters=hubspot_filters if hubspot_filters else None,
            apollo_filters=apollo_filters if apollo_filters else None,
            limit_per_source=args.limit
        )
        
        # Apply result filters
        if args.require_email or args.require_phone or args.require_company or \
           args.job_title_keywords or args.company_keywords:
            leads = scraper.filter_leads(
                leads,
                has_email=args.require_email,
                has_phone=args.require_phone,
                has_company=args.require_company,
                job_title_keywords=args.job_title_keywords,
                company_keywords=args.company_keywords
            )
        
        # Display summary
        if args.summary:
            summary = scraper.get_leads_summary(leads)
            print("\n" + "=" * 70)
            print("Summary Statistics")
            print("=" * 70)
            print(f"Total Leads: {summary['total_leads']}")
            print(f"Sources: {summary['sources']}")
            print(f"\nContact Information:")
            print(f"  With Email: {summary['with_email']} ({summary['email_coverage']}%)")
            print(f"  With Phone: {summary['with_phone']} ({summary['phone_coverage']}%)")
            print(f"  With Company: {summary['with_company']} ({summary['company_coverage']}%)")
            print(f"\nTop Job Titles:")
            for title, count in summary['top_job_titles'][:10]:
                print(f"  {title}: {count}")
            print("=" * 70)
        
        # Show sample leads
        if args.show:
            print(f"\nShowing first {args.show} leads:")
            print("-" * 70)
            for i, lead in enumerate(leads[:args.show], 1):
                print(f"\nLead {i}:")
                print(f"  Name: {lead.get('full_name', 'N/A')}")
                print(f"  Email: {lead.get('email', 'N/A')}")
                print(f"  Company: {lead.get('company', 'N/A')}")
                print(f"  Job Title: {lead.get('job_title', 'N/A')}")
                print(f"  Phone: {lead.get('phone', 'N/A')}")
                print(f"  Source: {lead.get('source', 'N/A')}")
        
        # Save to file
        if args.output:
            scraper.save_leads_to_file(leads, args.output, format=args.format)
            print(f"\nSaved {len(leads)} leads to {args.output}")
        elif not args.summary and not args.show:
            # If no output specified and no display, save to default location
            default_path = "data/processed/leads.json"
            scraper.save_leads_to_file(leads, default_path, format=args.format)
            print(f"\nSaved {len(leads)} leads to {default_path}")
        
        print(f"\nTotal leads scraped: {len(leads)}")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()









