"""
Business Intelligence Tool - Apollo + HubSpot Integration
Extracts client data, sales data, pipeline data, and uses it for prospecting and business insights.
"""

import os
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path

from src.lead_scraper.apollo_integration import ApolloIntegration
from src.lead_scraper.hubspot_integration import HubSpotIntegration


class BusinessIntelligence:
    """
    Comprehensive business intelligence tool that combines Apollo and HubSpot
    to understand clients, sales, pipeline, and enable smart prospecting.
    """
    
    def __init__(
        self,
        apollo_api_key: Optional[str] = None,
        hubspot_api_key: Optional[str] = None
    ):
        """
        Initialize Business Intelligence tool.
        
        Args:
            apollo_api_key: Apollo API key
            hubspot_api_key: HubSpot API key
        """
        self.apollo = ApolloIntegration(api_key=apollo_api_key) if apollo_api_key else None
        self.hubspot = HubSpotIntegration(api_key=hubspot_api_key) if hubspot_api_key else None
        
        # Data storage
        self.data_dir = Path("data/business_intelligence")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    # ==================== HUBSPOT DATA EXTRACTION ====================
    
    def get_all_deals(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get all deals from HubSpot (what we've sold).
        
        Args:
            limit: Maximum number of deals to retrieve
            
        Returns:
            List of deal dictionaries
        """
        if not self.hubspot:
            return []
        
        deals = []
        after = None
        batch_size = 100
        
        properties = [
            "dealname", "amount", "dealstage", "closedate", "pipeline",
            "dealtype", "hubspot_owner_id", "createdate", "closed_won_date",
            "hs_analytics_source", "hs_analytics_source_data_1", "hs_analytics_source_data_2"
        ]
        
        while True:
            if limit and len(deals) >= limit:
                break
            
            params = {
                "limit": min(batch_size, limit - len(deals)) if limit else batch_size,
                "properties": ",".join(properties)
            }
            
            if after:
                params["after"] = after
            
            try:
                response = self.hubspot._make_request("GET", "/crm/v3/objects/deals", params=params)
                
                for deal in response.get("results", []):
                    deal_data = self._normalize_deal(deal)
                    deals.append(deal_data)
                
                paging = response.get("paging", {})
                if "next" not in paging or not paging.get("next"):
                    break
                
                after = paging.get("next", {}).get("after")
                if not after:
                    break
                    
            except Exception as e:
                print(f"Error fetching deals: {e}")
                break
        
        return deals[:limit] if limit else deals
    
    def get_pipeline(self) -> Dict[str, Any]:
        """
        Get pipeline information from HubSpot.
        
        Returns:
            Dictionary with pipeline stages and deal counts
        """
        if not self.hubspot:
            return {}
        
        try:
            # Get all pipelines
            pipelines_response = self.hubspot._make_request("GET", "/crm/v3/pipelines/deals")
            pipelines = pipelines_response.get("results", [])
            
            # Get deals in each stage
            pipeline_data = {}
            for pipeline in pipelines:
                pipeline_id = pipeline.get("id")
                stages = pipeline.get("stages", [])
                
                pipeline_data[pipeline_id] = {
                    "id": pipeline_id,
                    "label": pipeline.get("label", ""),
                    "stages": []
                }
                
                for stage in stages:
                    stage_id = stage.get("id")
                    stage_label = stage.get("label", "")
                    
                    # Count deals in this stage - using search API
                    try:
                        deals_response = self.hubspot._make_request(
                            "POST",
                            "/crm/v3/objects/deals/search",
                            data={
                                "filterGroups": [{
                                    "filters": [{
                                        "propertyName": "dealstage",
                                        "operator": "EQ",
                                        "value": stage_id
                                    }]
                                }],
                                "limit": 1,
                                "properties": ["dealname", "amount"]
                            }
                        )
                        deal_count = len(deals_response.get("results", []))
                    except:
                        deal_count = 0
                    
                    stage_data = {
                        "id": stage_id,
                        "label": stage_label,
                        "display_order": stage.get("displayOrder", 0),
                        "deal_count": deal_count
                    }
                    
                    pipeline_data[pipeline_id]["stages"].append(stage_data)
            
            return pipeline_data
            
        except Exception as e:
            print(f"Error fetching pipeline: {e}")
            return {}
    
    def get_client_companies(self) -> List[Dict]:
        """
        Get all companies that are clients (have deals or are marked as clients).
        
        Returns:
            List of client company dictionaries
        """
        if not self.hubspot:
            return []
        
        # Get all companies
        companies = []
        after = None
        
        while True:
            params = {
                "limit": 100,
                "properties": "name,domain,website,industry,city,state,country,numberofemployees,createdate,lifecyclestage"
            }
            
            if after:
                params["after"] = after
            
            try:
                response = self.hubspot._make_request("GET", "/crm/v3/objects/companies", params=params)
                
                for company in response.get("results", []):
                    company_data = self.hubspot._normalize_company(company)
                    
                    # Check if company has deals (is a client)
                    company_id = company.get("id")
                    deals = self._get_company_deals(company_id)
                    
                    if deals or company.get("properties", {}).get("lifecyclestage") in ["customer", "client"]:
                        company_data["deal_count"] = len(deals)
                        company_data["total_deal_value"] = sum(d.get("amount", 0) for d in deals)
                        company_data["deals"] = deals
                        companies.append(company_data)
                
                paging = response.get("paging", {})
                if "next" not in paging or not paging.get("next"):
                    break
                
                after = paging.get("next", {}).get("after")
                if not after:
                    break
                    
            except Exception as e:
                print(f"Error fetching client companies: {e}")
                break
        
        return companies
    
    def _get_company_deals(self, company_id: str) -> List[Dict]:
        """Get deals associated with a company."""
        if not self.hubspot:
            return []
        
        try:
            # Use search API to find deals associated with company
            response = self.hubspot._make_request(
                "POST",
                "/crm/v3/objects/deals/search",
                data={
                    "filterGroups": [{
                        "filters": [{
                            "propertyName": "associatedcompanyid",
                            "operator": "EQ",
                            "value": company_id
                        }]
                    }],
                    "limit": 10,
                    "properties": ["dealname", "amount", "dealstage", "closedate", "closed_won_date"]
                }
            )
            
            deals = []
            for deal in response.get("results", []):
                deals.append(self._normalize_deal(deal))
            
            return deals
            
        except Exception as e:
            return []
    
    def _normalize_deal(self, deal: Dict) -> Dict:
        """Normalize HubSpot deal data."""
        properties = deal.get("properties", {})
        
        amount = properties.get("amount", "")
        try:
            amount = float(amount) if amount else 0
        except:
            amount = 0
        
        return {
            "id": deal.get("id"),
            "source": "hubspot",
            "name": properties.get("dealname", ""),
            "amount": amount,
            "stage": properties.get("dealstage", ""),
            "pipeline": properties.get("pipeline", ""),
            "close_date": properties.get("closedate", ""),
            "closed_won_date": properties.get("closed_won_date", ""),
            "deal_type": properties.get("dealtype", ""),
            "owner_id": properties.get("hubspot_owner_id", ""),
            "created_at": properties.get("createdate", ""),
            "source_analytics": {
                "source": properties.get("hs_analytics_source", ""),
                "source_data_1": properties.get("hs_analytics_source_data_1", ""),
                "source_data_2": properties.get("hs_analytics_source_data_2", "")
            },
            "raw_data": deal
        }
    
    # ==================== SALES ANALYTICS ====================
    
    def get_sales_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive sales summary.
        
        Returns:
            Dictionary with sales statistics
        """
        deals = self.get_all_deals()
        
        total_deals = len(deals)
        closed_deals = [d for d in deals if d.get("closed_won_date")]
        open_deals = [d for d in deals if not d.get("closed_won_date")]
        
        total_revenue = sum(d.get("amount", 0) for d in closed_deals)
        open_pipeline_value = sum(d.get("amount", 0) for d in open_deals)
        
        # Deal stages breakdown
        stage_breakdown = {}
        for deal in deals:
            stage = deal.get("stage", "Unknown")
            if stage not in stage_breakdown:
                stage_breakdown[stage] = {"count": 0, "value": 0}
            stage_breakdown[stage]["count"] += 1
            stage_breakdown[stage]["value"] += deal.get("amount", 0)
        
        # Revenue by month
        monthly_revenue = {}
        for deal in closed_deals:
            close_date = deal.get("closed_won_date", deal.get("close_date", ""))
            if close_date:
                try:
                    # Parse date (format: timestamp in milliseconds)
                    timestamp = int(close_date)
                    date = datetime.fromtimestamp(timestamp / 1000)
                    month_key = date.strftime("%Y-%m")
                    
                    if month_key not in monthly_revenue:
                        monthly_revenue[month_key] = 0
                    monthly_revenue[month_key] += deal.get("amount", 0)
                except:
                    pass
        
        return {
            "total_deals": total_deals,
            "closed_deals": len(closed_deals),
            "open_deals": len(open_deals),
            "total_revenue": total_revenue,
            "open_pipeline_value": open_pipeline_value,
            "average_deal_size": total_revenue / len(closed_deals) if closed_deals else 0,
            "stage_breakdown": stage_breakdown,
            "monthly_revenue": monthly_revenue,
            "top_clients": sorted(
                [{"name": d.get("name", ""), "amount": d.get("amount", 0)} for d in closed_deals],
                key=lambda x: x["amount"],
                reverse=True
            )[:10]
        }
    
    # ==================== PROSPECTING ====================
    
    def find_similar_companies(self, client_company: Dict, limit: int = 50) -> List[Dict]:
        """
        Find companies similar to existing clients using Apollo.
        
        Args:
            client_company: Client company dictionary
            limit: Maximum number of similar companies to find
            
        Returns:
            List of similar companies from Apollo
        """
        if not self.apollo:
            return []
        
        # Use client company attributes to find similar companies
        industry = client_company.get("industry", "")
        employee_count = client_company.get("employee_count", "")
        location = f"{client_company.get('city', '')}, {client_company.get('state', '')}"
        
        # Determine employee range
        employee_ranges = []
        if employee_count:
            try:
                emp_count = int(str(employee_count).replace(",", ""))
                if emp_count < 10:
                    employee_ranges = ["1,10"]
                elif emp_count < 50:
                    employee_ranges = ["11,50"]
                elif emp_count < 200:
                    employee_ranges = ["51,200"]
                elif emp_count < 1000:
                    employee_ranges = ["201,1000"]
                else:
                    employee_ranges = ["1001,5000"]
            except:
                pass
        
        results = self.apollo.search_organizations(
            industry=industry if industry else None,
            employee_count_ranges=employee_ranges if employee_ranges else None,
            locations=[location] if location and location != ", " else None,
            per_page=min(limit, 100)
        )
        
        return results.get("organizations", [])[:limit]
    
    def find_decision_makers(self, company_name: Optional[str] = None, company_domain: Optional[str] = None, limit: int = 25) -> List[Dict]:
        """
        Find decision makers at companies using Apollo.
        
        Args:
            company_name: Company name to search for
            company_domain: Company domain to search for
            limit: Maximum number of decision makers to find
            
        Returns:
            List of decision maker contacts
        """
        if not self.apollo:
            return []
        
        # Search for decision makers (VP, Director, C-level, Owner)
        results = self.apollo.search_people(
            q_organization_name=company_name,
            q_organization_domains=[company_domain] if company_domain else None,
            person_seniorities=["VP", "Director", "C-Level", "Owner", "Founder"],
            per_page=min(limit, 100)
        )
        
        return results.get("people", [])[:limit]
    
    def enrich_prospect(self, email: str) -> Optional[Dict]:
        """
        Enrich a prospect using Apollo.
        
        Args:
            email: Email address to enrich
            
        Returns:
            Enriched prospect data
        """
        if not self.apollo:
            return None
        
        return self.apollo.enrich_person(email=email)
    
    # ==================== DATA STORAGE ====================
    
    def save_business_data(self) -> Dict[str, str]:
        """
        Save all business data to files for RAG ingestion.
        
        Returns:
            Dictionary with file paths
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        saved_files = {}
        
        # Save deals
        deals = self.get_all_deals()
        deals_file = self.data_dir / f"deals_{timestamp}.json"
        with open(deals_file, "w", encoding="utf-8") as f:
            json.dump(deals, f, indent=2, ensure_ascii=False, default=str)
        saved_files["deals"] = str(deals_file)
        
        # Save client companies
        clients = self.get_client_companies()
        clients_file = self.data_dir / f"clients_{timestamp}.json"
        with open(clients_file, "w", encoding="utf-8") as f:
            json.dump(clients, f, indent=2, ensure_ascii=False, default=str)
        saved_files["clients"] = str(clients_file)
        
        # Save pipeline
        pipeline = self.get_pipeline()
        pipeline_file = self.data_dir / f"pipeline_{timestamp}.json"
        with open(pipeline_file, "w", encoding="utf-8") as f:
            json.dump(pipeline, f, indent=2, ensure_ascii=False, default=str)
        saved_files["pipeline"] = str(pipeline_file)
        
        # Save sales summary
        sales_summary = self.get_sales_summary()
        sales_file = self.data_dir / f"sales_summary_{timestamp}.json"
        with open(sales_file, "w", encoding="utf-8") as f:
            json.dump(sales_summary, f, indent=2, ensure_ascii=False, default=str)
        saved_files["sales_summary"] = str(sales_file)
        
        # Create markdown summary for RAG
        markdown_file = self.data_dir / f"business_intelligence_{timestamp}.md"
        with open(markdown_file, "w", encoding="utf-8") as f:
            f.write("# GrowthBoss Business Intelligence Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Sales Summary\n\n")
            f.write(f"- Total Deals: {sales_summary.get('total_deals', 0)}\n")
            f.write(f"- Closed Deals: {sales_summary.get('closed_deals', 0)}\n")
            f.write(f"- Open Deals: {sales_summary.get('open_deals', 0)}\n")
            f.write(f"- Total Revenue: ${sales_summary.get('total_revenue', 0):,.2f}\n")
            f.write(f"- Open Pipeline Value: ${sales_summary.get('open_pipeline_value', 0):,.2f}\n")
            f.write(f"- Average Deal Size: ${sales_summary.get('average_deal_size', 0):,.2f}\n\n")
            
            f.write("## Top Clients\n\n")
            for client in sales_summary.get("top_clients", [])[:10]:
                f.write(f"- {client.get('name', 'Unknown')}: ${client.get('amount', 0):,.2f}\n")
            
            f.write("\n## Client Companies\n\n")
            f.write(f"Total Client Companies: {len(clients)}\n\n")
            for client in clients[:20]:
                f.write(f"### {client.get('name', 'Unknown')}\n")
                f.write(f"- Industry: {client.get('industry', 'N/A')}\n")
                f.write(f"- Employees: {client.get('employee_count', 'N/A')}\n")
                f.write(f"- Deal Count: {client.get('deal_count', 0)}\n")
                f.write(f"- Total Value: ${client.get('total_deal_value', 0):,.2f}\n\n")
            
            f.write("## Pipeline Stages\n\n")
            for stage_id, stage_data in sales_summary.get("stage_breakdown", {}).items():
                f.write(f"- {stage_id}: {stage_data.get('count', 0)} deals, ${stage_data.get('value', 0):,.2f}\n")
        
        saved_files["markdown"] = str(markdown_file)
        
        return saved_files

