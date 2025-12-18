"""
Comprehensive Data Extraction - Pulls ALL data based on Marketing Council recommendations.
Extensive extraction of deals, opportunities, clients, and market intelligence.
"""

import os
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path

from src.lead_scraper.apollo_integration import ApolloIntegration
from src.lead_scraper.hubspot_integration import HubSpotIntegration


class ComprehensiveDataExtraction:
    """
    Comprehensive data extraction tool that pulls EVERYTHING based on Marketing Council recommendations.
    No detail is missed.
    """
    
    def __init__(
        self,
        apollo_api_key: Optional[str] = None,
        hubspot_api_key: Optional[str] = None
    ):
        """Initialize comprehensive data extraction."""
        self.apollo = ApolloIntegration(api_key=apollo_api_key) if apollo_api_key else None
        self.hubspot = HubSpotIntegration(api_key=hubspot_api_key) if hubspot_api_key else None
        
        self.data_dir = Path("data/comprehensive_extraction")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    # ==================== HUBSPOT: COMPREHENSIVE DEALS DATA ====================
    
    def extract_all_deals_comprehensive(self) -> Dict[str, Any]:
        """
        Extract ALL deal data comprehensively.
        Includes: values, close dates, win/loss, sources, types, stages, owners, etc.
        """
        if not self.hubspot:
            return {"error": "HubSpot not available"}
        
        print("📊 Extracting comprehensive deals data...")
        
        all_deals = []
        after = None
        batch_size = 100
        
        # Comprehensive properties list based on council recommendations
        properties = [
            # Core deal info
            "dealname", "amount", "dealstage", "pipeline", "closedate", "closed_won_date",
            "dealtype", "hubspot_owner_id", "createdate", "lastmodifieddate",
            
            # Source tracking (CRITICAL per council)
            "hs_analytics_source", "hs_analytics_source_data_1", "hs_analytics_source_data_2",
            "hs_analytics_source_data_3", "revenue", "amount_in_home_currency",
            
            # Deal details
            "description", "deal_currency_code", "closed_lost_reason", "closed_lost_reason_name",
            "closed_won_reason", "closed_won_reason_name",
            
            # Service packages (what we sell)
            "service_package", "service_type", "package_type",
            
            # Engagement metrics
            "num_associated_contacts", "num_associated_companies",
            "num_notes", "num_activities",
            
            # Custom properties (if any)
            "hs_all_owner_ids", "hs_created_by_user_id", "hs_last_modified_by_user_id",
            "hs_num_associated_deal_line_items", "hs_object_id", "hs_pipeline",
            "hs_pipeline_stage", "hs_predicted_amount", "hs_probability_to_close",
        ]
        
        while True:
            params = {
                "limit": batch_size,
                "properties": ",".join(properties)
            }
            
            if after:
                params["after"] = after
            
            try:
                response = self.hubspot._make_request("GET", "/crm/v3/objects/deals", params=params)
                
                for deal in response.get("results", []):
                    deal_data = self._normalize_deal_comprehensive(deal)
                    
                    # Get associated company and contacts
                    deal_id = deal.get("id")
                    deal_data["associated_company"] = self._get_deal_company(deal_id)
                    deal_data["associated_contacts"] = self._get_deal_contacts(deal_id)
                    deal_data["activities"] = self._get_deal_activities(deal_id)
                    
                    all_deals.append(deal_data)
                
                paging = response.get("paging", {})
                if "next" not in paging or not paging.get("next"):
                    break
                
                after = paging.get("next", {}).get("after")
                if not after:
                    break
                    
            except Exception as e:
                print(f"⚠️  Error fetching deals: {e}")
                break
        
        # Calculate comprehensive metrics
        metrics = self._calculate_deal_metrics(all_deals)
        
        return {
            "deals": all_deals,
            "total_count": len(all_deals),
            "metrics": metrics,
            "extracted_at": datetime.now().isoformat()
        }
    
    def _normalize_deal_comprehensive(self, deal: Dict) -> Dict:
        """Normalize deal with ALL data points."""
        properties = deal.get("properties", {})
        
        amount = properties.get("amount", "")
        try:
            amount = float(amount) if amount else 0
        except:
            amount = 0
        
        return {
            "id": deal.get("id"),
            "name": properties.get("dealname", ""),
            "amount": amount,
            "currency": properties.get("deal_currency_code", "USD"),
            "stage": properties.get("dealstage", ""),
            "stage_name": properties.get("hs_pipeline_stage", ""),
            "pipeline": properties.get("pipeline", ""),
            "pipeline_name": properties.get("hs_pipeline", ""),
            "close_date": properties.get("closedate", ""),
            "closed_won_date": properties.get("closed_won_date", ""),
            "closed_lost_reason": properties.get("closed_lost_reason", ""),
            "closed_lost_reason_name": properties.get("closed_lost_reason_name", ""),
            "closed_won_reason": properties.get("closed_won_reason", ""),
            "closed_won_reason_name": properties.get("closed_won_reason_name", ""),
            "deal_type": properties.get("dealtype", ""),
            "service_package": properties.get("service_package", ""),
            "service_type": properties.get("service_type", ""),
            "package_type": properties.get("package_type", ""),
            "description": properties.get("description", ""),
            "owner_id": properties.get("hubspot_owner_id", ""),
            "all_owner_ids": properties.get("hs_all_owner_ids", ""),
            "created_at": properties.get("createdate", ""),
            "created_by": properties.get("hs_created_by_user_id", ""),
            "updated_at": properties.get("lastmodifieddate", ""),
            "updated_by": properties.get("hs_last_modified_by_user_id", ""),
            "source": {
                "primary": properties.get("hs_analytics_source", ""),
                "data_1": properties.get("hs_analytics_source_data_1", ""),
                "data_2": properties.get("hs_analytics_source_data_2", ""),
                "data_3": properties.get("hs_analytics_source_data_3", "")
            },
            "engagement": {
                "num_contacts": int(properties.get("num_associated_contacts", "0") or 0),
                "num_companies": int(properties.get("num_associated_companies", "0") or 0),
                "num_notes": int(properties.get("num_notes", "0") or 0),
                "num_activities": int(properties.get("num_activities", "0") or 0)
            },
            "forecasting": {
                "predicted_amount": float(properties.get("hs_predicted_amount", "0") or 0),
                "probability_to_close": float(properties.get("hs_probability_to_close", "0") or 0)
            },
            "raw_data": deal
        }
    
    def _get_deal_company(self, deal_id: str) -> Optional[Dict]:
        """Get company associated with deal."""
        if not self.hubspot:
            return None
        
        try:
            response = self.hubspot._make_request(
                "GET",
                f"/crm/v4/objects/deals/{deal_id}/associations/companies"
            )
            
            associations = response.get("results", [])
            if not associations:
                return None
            
            company_id = associations[0].get("toObjectId")
            if not company_id:
                return None
            
            # Get company details
            company_response = self.hubspot._make_request(
                "GET",
                f"/crm/v3/objects/companies/{company_id}",
                params={
                    "properties": "name,domain,website,industry,city,state,country,numberofemployees,lifecyclestage,annualrevenue,phone"
                }
            )
            
            props = company_response.get("properties", {})
            return {
                "id": company_id,
                "name": props.get("name", ""),
                "domain": props.get("domain", ""),
                "website": props.get("website", ""),
                "industry": props.get("industry", ""),
                "city": props.get("city", ""),
                "state": props.get("state", ""),
                "country": props.get("country", ""),
                "employee_count": props.get("numberofemployees", ""),
                "lifecycle_stage": props.get("lifecyclestage", ""),
                "annual_revenue": props.get("annualrevenue", ""),
                "phone": props.get("phone", "")
            }
        except Exception as e:
            return None
    
    def _get_deal_contacts(self, deal_id: str) -> List[Dict]:
        """Get contacts associated with deal."""
        if not self.hubspot:
            return []
        
        try:
            response = self.hubspot._make_request(
                "GET",
                f"/crm/v4/objects/deals/{deal_id}/associations/contacts"
            )
            
            contact_ids = [assoc.get("toObjectId") for assoc in response.get("results", [])]
            contacts = []
            
            for contact_id in contact_ids[:10]:  # Limit to 10
                try:
                    contact_response = self.hubspot._make_request(
                        "GET",
                        f"/crm/v3/objects/contacts/{contact_id}",
                        params={
                            "properties": "email,firstname,lastname,jobtitle,phone,company,lifecyclestage"
                        }
                    )
                    
                    props = contact_response.get("properties", {})
                    contacts.append({
                        "id": contact_id,
                        "email": props.get("email", ""),
                        "first_name": props.get("firstname", ""),
                        "last_name": props.get("lastname", ""),
                        "full_name": f"{props.get('firstname', '')} {props.get('lastname', '')}".strip(),
                        "job_title": props.get("jobtitle", ""),
                        "phone": props.get("phone", ""),
                        "company": props.get("company", ""),
                        "lifecycle_stage": props.get("lifecyclestage", "")
                    })
                except:
                    continue
            
            return contacts
        except Exception as e:
            return []
    
    def _get_deal_activities(self, deal_id: str) -> Dict[str, int]:
        """Get activity counts for deal."""
        # Simplified - can be enhanced with actual activity API calls
        return {
            "notes": 0,
            "calls": 0,
            "emails": 0,
            "meetings": 0
        }
    
    def _calculate_deal_metrics(self, deals: List[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive deal metrics."""
        if not deals:
            return {}
        
        closed_deals = [d for d in deals if d.get("closed_won_date")]
        open_deals = [d for d in deals if not d.get("closed_won_date")]
        lost_deals = [d for d in deals if d.get("closed_lost_reason")]
        
        total_revenue = sum(d.get("amount", 0) for d in closed_deals)
        pipeline_value = sum(d.get("amount", 0) for d in open_deals)
        
        # Win/loss rate
        total_closed = len(closed_deals) + len(lost_deals)
        win_rate = (len(closed_deals) / total_closed * 100) if total_closed > 0 else 0
        
        # Deal sources analysis
        sources = {}
        for deal in deals:
            source = deal.get("source", {}).get("primary", "Unknown")
            if source not in sources:
                sources[source] = {"count": 0, "value": 0, "won": 0}
            sources[source]["count"] += 1
            sources[source]["value"] += deal.get("amount", 0)
            if deal.get("closed_won_date"):
                sources[source]["won"] += 1
        
        # Service package analysis
        service_packages = {}
        for deal in deals:
            package = deal.get("service_package") or deal.get("deal_type") or "Unknown"
            if package not in service_packages:
                service_packages[package] = {"count": 0, "value": 0, "won": 0}
            service_packages[package]["count"] += 1
            service_packages[package]["value"] += deal.get("amount", 0)
            if deal.get("closed_won_date"):
                service_packages[package]["won"] += 1
        
        # Stage analysis
        stage_breakdown = {}
        for deal in deals:
            stage = deal.get("stage_name") or deal.get("stage", "Unknown")
            if stage not in stage_breakdown:
                stage_breakdown[stage] = {"count": 0, "value": 0}
            stage_breakdown[stage]["count"] += 1
            stage_breakdown[stage]["value"] += deal.get("amount", 0)
        
        # Industry analysis (from associated companies)
        industries = {}
        for deal in deals:
            company = deal.get("associated_company")
            if company:
                industry = company.get("industry", "Unknown")
                if industry not in industries:
                    industries[industry] = {"count": 0, "value": 0}
                industries[industry]["count"] += 1
                industries[industry]["value"] += deal.get("amount", 0)
        
        return {
            "total_deals": len(deals),
            "closed_deals": len(closed_deals),
            "open_deals": len(open_deals),
            "lost_deals": len(lost_deals),
            "total_revenue": total_revenue,
            "pipeline_value": pipeline_value,
            "average_deal_size": total_revenue / len(closed_deals) if closed_deals else 0,
            "win_rate": win_rate,
            "loss_rate": 100 - win_rate,
            "sources": sources,
            "service_packages": service_packages,
            "stage_breakdown": stage_breakdown,
            "industries": industries
        }
    
    # ==================== HUBSPOT: COMPREHENSIVE CLIENT DATA ====================
    
    def extract_all_clients_comprehensive(self) -> Dict[str, Any]:
        """Extract ALL client company data comprehensively."""
        if not self.hubspot:
            return {"error": "HubSpot not available"}
        
        print("🏢 Extracting comprehensive client data...")
        
        all_companies = []
        after = None
        
        properties = [
            "name", "domain", "website", "industry", "city", "state", "country",
            "numberofemployees", "annualrevenue", "lifecyclestage", "phone",
            "createdate", "hs_lastmodifieddate", "hs_created_by_user_id",
            "description", "type", "address", "address2", "zip", "phone",
            "hs_num_associated_deals", "hs_num_associated_contacts"
        ]
        
        while True:
            params = {
                "limit": 100,
                "properties": ",".join(properties)
            }
            
            if after:
                params["after"] = after
            
            try:
                response = self.hubspot._make_request("GET", "/crm/v3/objects/companies", params=params)
                
                for company in response.get("results", []):
                    company_data = self._normalize_company_comprehensive(company)
                    
                    # Get all deals for this company
                    company_id = company.get("id")
                    company_data["deals"] = self._get_company_deals_comprehensive(company_id)
                    company_data["contacts"] = self._get_company_contacts(company_id)
                    
                    # Only include if has deals or is marked as client
                    if company_data["deals"] or company_data.get("lifecycle_stage") in ["customer", "client"]:
                        all_companies.append(company_data)
                
                paging = response.get("paging", {})
                if "next" not in paging or not paging.get("next"):
                    break
                
                after = paging.get("next", {}).get("after")
                if not after:
                    break
                    
            except Exception as e:
                print(f"⚠️  Error fetching companies: {e}")
                break
        
        # Calculate client metrics
        metrics = self._calculate_client_metrics(all_companies)
        
        return {
            "clients": all_companies,
            "total_count": len(all_companies),
            "metrics": metrics,
            "extracted_at": datetime.now().isoformat()
        }
    
    def _normalize_company_comprehensive(self, company: Dict) -> Dict:
        """Normalize company with ALL data points."""
        properties = company.get("properties", {})
        
        return {
            "id": company.get("id"),
            "name": properties.get("name", ""),
            "domain": properties.get("domain", ""),
            "website": properties.get("website", ""),
            "industry": properties.get("industry", ""),
            "city": properties.get("city", ""),
            "state": properties.get("state", ""),
            "country": properties.get("country", ""),
            "address": properties.get("address", ""),
            "zip": properties.get("zip", ""),
            "phone": properties.get("phone", ""),
            "employee_count": properties.get("numberofemployees", ""),
            "annual_revenue": properties.get("annualrevenue", ""),
            "lifecycle_stage": properties.get("lifecyclestage", ""),
            "company_type": properties.get("type", ""),
            "description": properties.get("description", ""),
            "created_at": properties.get("createdate", ""),
            "updated_at": properties.get("hs_lastmodifieddate", ""),
            "num_deals": int(properties.get("hs_num_associated_deals", "0") or 0),
            "num_contacts": int(properties.get("hs_num_associated_contacts", "0") or 0),
            "raw_data": company
        }
    
    def _get_company_deals_comprehensive(self, company_id: str) -> List[Dict]:
        """Get all deals for a company."""
        if not self.hubspot:
            return []
        
        try:
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
                    "limit": 100,
                    "properties": ["dealname", "amount", "dealstage", "closedate", "closed_won_date", "dealtype"]
                }
            )
            
            deals = []
            for deal in response.get("results", []):
                props = deal.get("properties", {})
                amount = props.get("amount", "")
                try:
                    amount = float(amount) if amount else 0
                except:
                    amount = 0
                
                deals.append({
                    "id": deal.get("id"),
                    "name": props.get("dealname", ""),
                    "amount": amount,
                    "stage": props.get("dealstage", ""),
                    "close_date": props.get("closedate", ""),
                    "closed_won_date": props.get("closed_won_date", ""),
                    "deal_type": props.get("dealtype", "")
                })
            
            return deals
        except Exception as e:
            return []
    
    def _get_company_contacts(self, company_id: str) -> List[Dict]:
        """Get contacts for a company."""
        if not self.hubspot:
            return []
        
        try:
            response = self.hubspot._make_request(
                "GET",
                f"/crm/v4/objects/companies/{company_id}/associations/contacts"
            )
            
            contact_ids = [assoc.get("toObjectId") for assoc in response.get("results", [])]
            contacts = []
            
            for contact_id in contact_ids[:20]:  # Limit to 20
                try:
                    contact_response = self.hubspot._make_request(
                        "GET",
                        f"/crm/v3/objects/contacts/{contact_id}",
                        params={
                            "properties": "email,firstname,lastname,jobtitle,phone,lifecyclestage"
                        }
                    )
                    
                    props = contact_response.get("properties", {})
                    contacts.append({
                        "id": contact_id,
                        "email": props.get("email", ""),
                        "first_name": props.get("firstname", ""),
                        "last_name": props.get("lastname", ""),
                        "full_name": f"{props.get('firstname', '')} {props.get('lastname', '')}".strip(),
                        "job_title": props.get("jobtitle", ""),
                        "phone": props.get("phone", ""),
                        "lifecycle_stage": props.get("lifecyclestage", "")
                    })
                except:
                    continue
            
            return contacts
        except Exception as e:
            return []
    
    def _calculate_client_metrics(self, clients: List[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive client metrics."""
        if not clients:
            return {}
        
        total_deal_value = sum(sum(d.get("amount", 0) for d in c.get("deals", [])) for c in clients)
        
        industries = {}
        for client in clients:
            industry = client.get("industry", "Unknown")
            if industry not in industries:
                industries[industry] = {"count": 0, "total_value": 0}
            industries[industry]["count"] += 1
            industries[industry]["total_value"] += sum(d.get("amount", 0) for d in client.get("deals", []))
        
        employee_ranges = {}
        for client in clients:
            emp_count = client.get("employee_count", "")
            if emp_count:
                try:
                    emp = int(str(emp_count).replace(",", ""))
                    if emp < 10:
                        range_key = "1-10"
                    elif emp < 50:
                        range_key = "11-50"
                    elif emp < 200:
                        range_key = "51-200"
                    elif emp < 1000:
                        range_key = "201-1000"
                    else:
                        range_key = "1000+"
                except:
                    range_key = "Unknown"
            else:
                range_key = "Unknown"
            
            if range_key not in employee_ranges:
                employee_ranges[range_key] = {"count": 0, "total_value": 0}
            employee_ranges[range_key]["count"] += 1
            employee_ranges[range_key]["total_value"] += sum(d.get("amount", 0) for d in client.get("deals", []))
        
        return {
            "total_clients": len(clients),
            "total_deal_value": total_deal_value,
            "average_deal_value_per_client": total_deal_value / len(clients) if clients else 0,
            "industries": industries,
            "employee_ranges": employee_ranges
        }
    
    # ==================== APOLLO: COMPREHENSIVE MARKET INTELLIGENCE ====================
    
    def extract_market_intelligence(self, top_clients: List[Dict], limit_per_client: int = 50) -> Dict[str, Any]:
        """
        Extract market intelligence using Apollo based on top clients.
        Finds similar companies, decision makers, industry trends.
        """
        if not self.apollo:
            return {"error": "Apollo not available"}
        
        print("🔍 Extracting market intelligence from Apollo...")
        
        all_similar_companies = []
        all_decision_makers = []
        
        for client in top_clients[:10]:  # Top 10 clients
            print(f"  Analyzing: {client.get('name', 'Unknown')}")
            
            # Find similar companies
            similar = self.apollo.search_organizations(
                name=client.get("name"),
                industry=client.get("industry"),
                employee_count_ranges=self._get_employee_ranges(client.get("employee_count", "")),
                per_page=limit_per_client
            )
            
            for org in similar.get("organizations", []):
                org_data = self.apollo._normalize_organization(org)
                org_data["source_client"] = client.get("name")
                all_similar_companies.append(org_data)
            
            # Find decision makers at similar companies
            if client.get("name"):
                decision_makers_result = self.apollo.search_people(
                    q_organization_name=client.get("name"),
                    person_seniorities=["VP", "Director", "C-Level", "Owner", "Founder", "Manager"],
                    per_page=25
                )
                
                for person in decision_makers_result.get("people", []):
                    person_data = self.apollo._normalize_person(person)
                    person_data["source_client"] = client.get("name")
                    all_decision_makers.append(person_data)
        
        return {
            "similar_companies": all_similar_companies,
            "decision_makers": all_decision_makers,
            "total_similar_companies": len(all_similar_companies),
            "total_decision_makers": len(all_decision_makers),
            "extracted_at": datetime.now().isoformat()
        }
    
    def _get_employee_ranges(self, employee_count: str) -> List[str]:
        """Convert employee count to Apollo range format."""
        if not employee_count:
            return []
        
        try:
            emp = int(str(employee_count).replace(",", ""))
            if emp < 10:
                return ["1,10"]
            elif emp < 50:
                return ["11,50"]
            elif emp < 200:
                return ["51,200"]
            elif emp < 1000:
                return ["201,1000"]
            else:
                return ["1001,5000"]
        except:
            return []
    
    # ==================== SAVE COMPREHENSIVE DATA ====================
    
    def save_all_data(self) -> Dict[str, str]:
        """Save ALL extracted data comprehensively."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        saved_files = {}
        
        # 1. Extract ALL deals
        print("\n[1/4] Extracting ALL deals comprehensively...")
        deals_data = self.extract_all_deals_comprehensive()
        deals_file = self.data_dir / f"comprehensive_deals_{timestamp}.json"
        with open(deals_file, "w", encoding="utf-8") as f:
            json.dump(deals_data, f, indent=2, ensure_ascii=False, default=str)
        saved_files["deals"] = str(deals_file)
        print(f"✅ Extracted {deals_data.get('total_count', 0)} deals")
        
        # 2. Extract ALL clients
        print("\n[2/4] Extracting ALL clients comprehensively...")
        clients_data = self.extract_all_clients_comprehensive()
        clients_file = self.data_dir / f"comprehensive_clients_{timestamp}.json"
        with open(clients_file, "w", encoding="utf-8") as f:
            json.dump(clients_data, f, indent=2, ensure_ascii=False, default=str)
        saved_files["clients"] = str(clients_file)
        print(f"✅ Extracted {clients_data.get('total_count', 0)} clients")
        
        # 3. Extract market intelligence
        print("\n[3/4] Extracting market intelligence from Apollo...")
        top_clients = sorted(
            clients_data.get("clients", []),
            key=lambda x: sum(d.get("amount", 0) for d in x.get("deals", [])),
            reverse=True
        )[:10]
        
        market_data = self.extract_market_intelligence(top_clients)
        market_file = self.data_dir / f"market_intelligence_{timestamp}.json"
        with open(market_file, "w", encoding="utf-8") as f:
            json.dump(market_data, f, indent=2, ensure_ascii=False, default=str)
        saved_files["market_intelligence"] = str(market_file)
        print(f"✅ Extracted {market_data.get('total_similar_companies', 0)} similar companies")
        print(f"✅ Extracted {market_data.get('total_decision_makers', 0)} decision makers")
        
        # 4. Create comprehensive markdown report for RAG
        print("\n[4/4] Creating comprehensive markdown report...")
        markdown_file = self.data_dir / f"comprehensive_business_intelligence_{timestamp}.md"
        self._create_comprehensive_markdown(
            deals_data, clients_data, market_data, markdown_file
        )
        saved_files["markdown"] = str(markdown_file)
        
        return saved_files
    
    def _create_comprehensive_markdown(
        self, deals_data: Dict, clients_data: Dict, market_data: Dict, output_file: Path
    ):
        """Create comprehensive markdown report for RAG."""
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# GrowthBoss Comprehensive Business Intelligence Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Deals summary
            f.write("## Sales & Deals Data\n\n")
            metrics = deals_data.get("metrics", {})
            f.write(f"- **Total Deals**: {metrics.get('total_deals', 0)}\n")
            f.write(f"- **Closed Deals**: {metrics.get('closed_deals', 0)}\n")
            f.write(f"- **Open Deals**: {metrics.get('open_deals', 0)}\n")
            f.write(f"- **Total Revenue**: ${metrics.get('total_revenue', 0):,.2f}\n")
            f.write(f"- **Pipeline Value**: ${metrics.get('pipeline_value', 0):,.2f}\n")
            f.write(f"- **Average Deal Size**: ${metrics.get('average_deal_size', 0):,.2f}\n")
            f.write(f"- **Win Rate**: {metrics.get('win_rate', 0):.2f}%\n\n")
            
            # Deal sources
            f.write("### Deal Sources (Where Leads Come From)\n\n")
            for source, data in metrics.get("sources", {}).items():
                f.write(f"- **{source}**: {data.get('count', 0)} deals, ${data.get('value', 0):,.2f} value, {data.get('won', 0)} won\n")
            
            # Service packages
            f.write("\n### Service Packages (What We Sell)\n\n")
            for package, data in metrics.get("service_packages", {}).items():
                f.write(f"- **{package}**: {data.get('count', 0)} deals, ${data.get('value', 0):,.2f} value, {data.get('won', 0)} won\n")
            
            # Industries
            f.write("\n### Industries We Serve\n\n")
            for industry, data in metrics.get("industries", {}).items():
                f.write(f"- **{industry}**: {data.get('count', 0)} deals, ${data.get('value', 0):,.2f} value\n")
            
            # Clients
            f.write("\n## Client Companies\n\n")
            client_metrics = clients_data.get("metrics", {})
            f.write(f"- **Total Clients**: {client_metrics.get('total_clients', 0)}\n")
            f.write(f"- **Total Deal Value**: ${client_metrics.get('total_deal_value', 0):,.2f}\n\n")
            
            f.write("### Top Clients by Value\n\n")
            top_clients = sorted(
                clients_data.get("clients", []),
                key=lambda x: sum(d.get("amount", 0) for d in x.get("deals", [])),
                reverse=True
            )[:20]
            
            for i, client in enumerate(top_clients, 1):
                total_value = sum(d.get("amount", 0) for d in client.get("deals", []))
                f.write(f"{i}. **{client.get('name', 'Unknown')}**\n")
                f.write(f"   - Industry: {client.get('industry', 'N/A')}\n")
                f.write(f"   - Employees: {client.get('employee_count', 'N/A')}\n")
                f.write(f"   - Location: {client.get('city', '')}, {client.get('state', '')}\n")
                f.write(f"   - Deal Count: {len(client.get('deals', []))}\n")
                f.write(f"   - Total Value: ${total_value:,.2f}\n\n")
            
            # Market intelligence
            f.write("## Market Intelligence (Apollo)\n\n")
            f.write(f"- **Similar Companies Found**: {market_data.get('total_similar_companies', 0)}\n")
            f.write(f"- **Decision Makers Found**: {market_data.get('total_decision_makers', 0)}\n\n")
            
            f.write("### Similar Companies to Top Clients\n\n")
            for company in market_data.get("similar_companies", [])[:30]:
                f.write(f"- **{company.get('name', 'Unknown')}** ({company.get('industry', 'N/A')})\n")
                f.write(f"  - Employees: {company.get('employee_count', 'N/A')}\n")
                f.write(f"  - Location: {company.get('city', '')}, {company.get('state', '')}\n")
                f.write(f"  - Similar to: {company.get('source_client', 'N/A')}\n\n")
        
        print(f"✅ Created comprehensive markdown report: {output_file}")

