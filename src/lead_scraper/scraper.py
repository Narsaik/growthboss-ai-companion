"""
Unified Lead Scraper - Combines HubSpot and Apollo
Main interface for scraping leads from multiple sources.
"""

import os
import json
from typing import List, Dict, Optional, Any, Set
from datetime import datetime
from .hubspot_integration import HubSpotIntegration
from .apollo_integration import ApolloIntegration


class LeadScraper:
    """
    Unified lead scraper that combines HubSpot and Apollo integrations.
    Handles deduplication, merging, and unified lead management.
    """
    
    def __init__(
        self,
        hubspot_api_key: Optional[str] = None,
        apollo_api_key: Optional[str] = None
    ):
        """
        Initialize the lead scraper with HubSpot and Apollo integrations.
        
        Args:
            hubspot_api_key: HubSpot API key (defaults to HUBSPOT_API_KEY env var)
            apollo_api_key: Apollo API key (defaults to APOLLO_API_KEY env var)
        """
        self.hubspot = None
        self.apollo = None
        
        try:
            self.hubspot = HubSpotIntegration(api_key=hubspot_api_key)
        except ValueError as e:
            print(f"Warning: HubSpot integration not available: {e}")
        
        try:
            self.apollo = ApolloIntegration(api_key=apollo_api_key)
        except ValueError as e:
            print(f"Warning: Apollo integration not available: {e}")
        
        if not self.hubspot and not self.apollo:
            raise ValueError(
                "At least one API key must be provided. "
                "Set HUBSPOT_API_KEY or APOLLO_API_KEY environment variables."
            )
    
    def scrape_hubspot_leads(
        self,
        limit: Optional[int] = None,
        job_title: Optional[str] = None,
        company: Optional[str] = None,
        industry: Optional[str] = None
    ) -> List[Dict]:
        """
        Scrape leads from HubSpot.
        
        Args:
            limit: Maximum number of leads to retrieve
            job_title: Filter by job title
            company: Filter by company name
            industry: Filter by industry
        
        Returns:
            List of leads from HubSpot
        """
        if not self.hubspot:
            return []
        
        try:
            leads = self.hubspot.search_leads(
                job_title=job_title,
                company=company,
                industry=industry,
                limit=limit
            )
            return leads
        except Exception as e:
            print(f"Error scraping HubSpot leads: {e}")
            return []
    
    def scrape_apollo_leads(
        self,
        job_titles: Optional[List[str]] = None,
        locations: Optional[List[str]] = None,
        seniorities: Optional[List[str]] = None,
        departments: Optional[List[str]] = None,
        company_name: Optional[str] = None,
        keywords: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Scrape leads from Apollo.
        
        Args:
            job_titles: List of job titles to search for
            locations: List of locations (e.g., ["San Francisco, CA, United States"])
            seniorities: List of seniority levels (e.g., ["VP", "Director"])
            departments: List of departments (e.g., ["Sales", "Marketing"])
            company_name: Company name to search for
            keywords: Keywords to search for
            limit: Maximum number of leads to retrieve
        
        Returns:
            List of leads from Apollo
        """
        if not self.apollo:
            return []
        
        try:
            leads = self.apollo.get_all_people(
                person_titles=job_titles,
                person_locations=locations,
                person_seniorities=seniorities,
                person_departments=departments,
                q_organization_name=company_name,
                q_keywords=keywords,
                limit=limit
            )
            return leads
        except Exception as e:
            print(f"Error scraping Apollo leads: {e}")
            return []
    
    def scrape_all_leads(
        self,
        sources: Optional[List[str]] = None,
        hubspot_filters: Optional[Dict] = None,
        apollo_filters: Optional[Dict] = None,
        limit_per_source: Optional[int] = None
    ) -> List[Dict]:
        """
        Scrape leads from all available sources.
        
        Args:
            sources: List of sources to scrape from ("hubspot", "apollo"). Defaults to all available.
            hubspot_filters: Filters for HubSpot (job_title, company, industry, limit)
            apollo_filters: Filters for Apollo (job_titles, locations, seniorities, departments, company_name, keywords, limit)
            limit_per_source: Maximum leads per source
        
        Returns:
            List of all leads from all sources (deduplicated)
        """
        all_leads = []
        sources = sources or []
        
        if not sources or "hubspot" in sources:
            if self.hubspot:
                hubspot_leads = self.scrape_hubspot_leads(
                    limit=limit_per_source or hubspot_filters.get("limit") if hubspot_filters else None,
                    job_title=hubspot_filters.get("job_title") if hubspot_filters else None,
                    company=hubspot_filters.get("company") if hubspot_filters else None,
                    industry=hubspot_filters.get("industry") if hubspot_filters else None
                )
                all_leads.extend(hubspot_leads)
                print(f"Scraped {len(hubspot_leads)} leads from HubSpot")
        
        if not sources or "apollo" in sources:
            if self.apollo:
                apollo_leads = self.scrape_apollo_leads(
                    job_titles=apollo_filters.get("job_titles") if apollo_filters else None,
                    locations=apollo_filters.get("locations") if apollo_filters else None,
                    seniorities=apollo_filters.get("seniorities") if apollo_filters else None,
                    departments=apollo_filters.get("departments") if apollo_filters else None,
                    company_name=apollo_filters.get("company_name") if apollo_filters else None,
                    keywords=apollo_filters.get("keywords") if apollo_filters else None,
                    limit=limit_per_source or apollo_filters.get("limit") if apollo_filters else None
                )
                all_leads.extend(apollo_leads)
                print(f"Scraped {len(apollo_leads)} leads from Apollo")
        
        # Deduplicate leads
        deduplicated_leads = self.deduplicate_leads(all_leads)
        print(f"Total unique leads after deduplication: {len(deduplicated_leads)}")
        
        return deduplicated_leads
    
    def deduplicate_leads(self, leads: List[Dict]) -> List[Dict]:
        """
        Deduplicate leads based on email address.
        If multiple leads have the same email, merge their data.
        
        Args:
            leads: List of leads to deduplicate
        
        Returns:
            Deduplicated list of leads
        """
        seen_emails: Dict[str, Dict] = {}
        
        for lead in leads:
            email = lead.get("email", "").lower().strip()
            
            if not email:
                # If no email, keep the lead but add a unique identifier
                lead_id = f"{lead.get('source', 'unknown')}_{lead.get('id', 'no_id')}"
                if lead_id not in seen_emails:
                    seen_emails[lead_id] = lead
                continue
            
            if email in seen_emails:
                # Merge leads with same email
                existing = seen_emails[email]
                merged = self._merge_lead_data(existing, lead)
                seen_emails[email] = merged
            else:
                seen_emails[email] = lead
        
        return list(seen_emails.values())
    
    def _merge_lead_data(self, lead1: Dict, lead2: Dict) -> Dict:
        """
        Merge two lead records, preferring non-empty values.
        
        Args:
            lead1: First lead record
            lead2: Second lead record
        
        Returns:
            Merged lead record
        """
        merged = lead1.copy()
        
        # Combine sources
        sources = set(merged.get("source", "").split(","))
        sources.add(lead2.get("source", ""))
        merged["source"] = ",".join(sorted(sources))
        
        # Merge fields, preferring non-empty values
        fields_to_merge = [
            "first_name", "last_name", "full_name", "phone", "company",
            "job_title", "website", "city", "state", "country"
        ]
        
        for field in fields_to_merge:
            if not merged.get(field) and lead2.get(field):
                merged[field] = lead2.get(field)
        
        # Combine raw data
        if "raw_data" in merged and "raw_data" in lead2:
            merged["raw_data"] = {
                "hubspot": merged["raw_data"] if "hubspot" in merged.get("source", "") else lead2.get("raw_data"),
                "apollo": lead2.get("raw_data") if "apollo" in lead2.get("source", "") else merged.get("raw_data")
            }
        
        return merged
    
    def save_leads_to_file(
        self,
        leads: List[Dict],
        filepath: str,
        format: str = "json"
    ) -> bool:
        """
        Save leads to a file.
        
        Args:
            leads: List of leads to save
            filepath: Path to save file
            format: File format ("json" or "csv")
        
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
            
            if format.lower() == "json":
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(leads, f, indent=2, ensure_ascii=False)
            
            elif format.lower() == "csv":
                import csv
                
                if not leads:
                    return False
                
                fieldnames = set()
                for lead in leads:
                    fieldnames.update(lead.keys())
                
                fieldnames = sorted(list(fieldnames))
                
                with open(filepath, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for lead in leads:
                        # Flatten nested structures for CSV
                        row = {}
                        for key, value in lead.items():
                            if key == "raw_data":
                                continue  # Skip raw data in CSV
                            if isinstance(value, (dict, list)):
                                row[key] = json.dumps(value)
                            else:
                                row[key] = value
                        writer.writerow(row)
            
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            print(f"Saved {len(leads)} leads to {filepath}")
            return True
        
        except Exception as e:
            print(f"Error saving leads to file: {e}")
            return False
    
    def filter_leads(
        self,
        leads: List[Dict],
        has_email: bool = True,
        has_phone: bool = False,
        has_company: bool = False,
        job_title_keywords: Optional[List[str]] = None,
        company_keywords: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Filter leads based on criteria.
        
        Args:
            leads: List of leads to filter
            has_email: Require email address
            has_phone: Require phone number
            has_company: Require company name
            job_title_keywords: Filter by job title keywords
            company_keywords: Filter by company keywords
        
        Returns:
            Filtered list of leads
        """
        filtered = []
        
        for lead in leads:
            if has_email and not lead.get("email"):
                continue
            
            if has_phone and not lead.get("phone"):
                continue
            
            if has_company and not lead.get("company"):
                continue
            
            if job_title_keywords:
                job_title = lead.get("job_title", "").lower()
                if not any(keyword.lower() in job_title for keyword in job_title_keywords):
                    continue
            
            if company_keywords:
                company = lead.get("company", "").lower()
                if not any(keyword.lower() in company for keyword in company_keywords):
                    continue
            
            filtered.append(lead)
        
        return filtered
    
    def get_leads_summary(self, leads: List[Dict]) -> Dict[str, Any]:
        """
        Get a summary statistics of the leads.
        
        Args:
            leads: List of leads to analyze
        
        Returns:
            Dictionary with summary statistics
        """
        total = len(leads)
        
        sources = {}
        for lead in leads:
            source = lead.get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1
        
        with_email = sum(1 for lead in leads if lead.get("email"))
        with_phone = sum(1 for lead in leads if lead.get("phone"))
        with_company = sum(1 for lead in leads if lead.get("company"))
        
        job_titles = {}
        for lead in leads:
            title = lead.get("job_title", "Unknown")
            job_titles[title] = job_titles.get(title, 0) + 1
        
        top_job_titles = sorted(job_titles.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_leads": total,
            "sources": sources,
            "with_email": with_email,
            "with_phone": with_phone,
            "with_company": with_company,
            "email_coverage": round(with_email / total * 100, 2) if total > 0 else 0,
            "phone_coverage": round(with_phone / total * 100, 2) if total > 0 else 0,
            "company_coverage": round(with_company / total * 100, 2) if total > 0 else 0,
            "top_job_titles": top_job_titles
        }










