"""
HubSpot Integration - Lead Management
Comprehensive integration for fetching leads and contacts from HubSpot.
"""

import os
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime


class HubSpotIntegration:
    """Comprehensive HubSpot API integration for lead and contact management."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize HubSpot integration.
        
        Args:
            api_key: HubSpot API key (defaults to HUBSPOT_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("HUBSPOT_API_KEY")
        self.base_url = "https://api.hubapi.com"
        
        if not self.api_key:
            raise ValueError(
                "HubSpot API key required. Set HUBSPOT_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        # HubSpot API v3 uses Bearer token OR hapikey query parameter
        # Try Bearer first, fall back to query param if needed
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None, 
        params: Optional[Dict] = None
    ) -> Dict:
        """Make API request to HubSpot."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # HubSpot v3 API: if Bearer fails, try hapikey query param
        # For v3, we'll use Bearer token (private app access token)
        # If that fails with 401, try hapikey query parameter (legacy)
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data, params=params, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data, params=params, timeout=30)
            elif method.upper() == "PATCH":
                response = requests.patch(url, headers=self.headers, json=data, params=params, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers, params=params, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # If 401, try with hapikey query parameter (legacy API key format)
            if response.status_code == 401:
                # Retry with hapikey in query params
                if params is None:
                    params = {}
                params["hapikey"] = self.api_key
                # Remove Bearer token for legacy auth
                headers_no_bearer = {"Content-Type": "application/json"}
                
                if method.upper() == "GET":
                    response = requests.get(url, headers=headers_no_bearer, params=params, timeout=30)
                elif method.upper() == "POST":
                    response = requests.post(url, headers=headers_no_bearer, json=data, params=params, timeout=30)
                elif method.upper() == "PUT":
                    response = requests.put(url, headers=headers_no_bearer, json=data, params=params, timeout=30)
                elif method.upper() == "PATCH":
                    response = requests.patch(url, headers=headers_no_bearer, json=data, params=params, timeout=30)
                elif method.upper() == "DELETE":
                    response = requests.delete(url, headers=headers_no_bearer, params=params, timeout=30)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"HubSpot API error: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_msg += f" - Response: {e.response.text}"
                except:
                    pass
            raise Exception(error_msg)
    
    def get_contacts(
        self,
        limit: int = 100,
        after: Optional[str] = None,
        properties: Optional[List[str]] = None,
        filters: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Get contacts from HubSpot.
        
        Args:
            limit: Number of contacts to retrieve (max 100)
            after: Pagination cursor
            properties: List of properties to retrieve
            filters: List of filter objects
        
        Returns:
            Dictionary with contacts and pagination info
        """
        default_properties = [
            "email", "firstname", "lastname", "phone", "company", 
            "jobtitle", "website", "hubspot_owner_id", "createdate", "lastmodifieddate"
        ]
        
        params = {
            "limit": min(limit, 100),
        }
        
        if after:
            params["after"] = after
        
        if properties:
            params["properties"] = ",".join(properties)
        else:
            params["properties"] = ",".join(default_properties)
        
        if filters:
            # HubSpot v3 search API for filters
            return self._search_contacts(limit=limit, after=after, properties=properties, filters=filters)
        
        try:
            response = self._make_request("GET", "/crm/v3/objects/contacts", params=params)
            
            contacts = []
            for contact in response.get("results", []):
                contact_data = self._normalize_contact(contact)
                contacts.append(contact_data)
            
            return {
                "contacts": contacts,
                "paging": response.get("paging", {}),
                "has_more": "next" in response.get("paging", {}).get("next", {}),
                "next_cursor": response.get("paging", {}).get("next", {}).get("after") if "next" in response.get("paging", {}) else None
            }
        except Exception as e:
            print(f"Error fetching contacts: {e}")
            return {"contacts": [], "paging": {}, "has_more": False, "next_cursor": None}
    
    def _search_contacts(
        self,
        limit: int = 100,
        after: Optional[str] = None,
        properties: Optional[List[str]] = None,
        filters: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Search contacts using HubSpot search API."""
        default_properties = [
            "email", "firstname", "lastname", "phone", "company", 
            "jobtitle", "website", "hubspot_owner_id", "createdate", "lastmodifieddate"
        ]
        
        search_data = {
            "limit": min(limit, 100),
            "properties": properties or default_properties,
        }
        
        if after:
            search_data["after"] = after
        
        if filters:
            search_data["filterGroups"] = [{"filters": filters}]
        
        try:
            response = self._make_request("POST", "/crm/v3/objects/contacts/search", data=search_data)
            
            contacts = []
            for contact in response.get("results", []):
                contact_data = self._normalize_contact(contact)
                contacts.append(contact_data)
            
            return {
                "contacts": contacts,
                "paging": response.get("paging", {}),
                "has_more": "next" in response.get("paging", {}).get("next", {}),
                "next_cursor": response.get("paging", {}).get("next", {}).get("after") if "next" in response.get("paging", {}) else None
            }
        except Exception as e:
            print(f"Error searching contacts: {e}")
            return {"contacts": [], "paging": {}, "has_more": False, "next_cursor": None}
    
    def _normalize_contact(self, contact: Dict) -> Dict:
        """Normalize HubSpot contact data to standard format."""
        properties = contact.get("properties", {})
        
        return {
            "id": contact.get("id"),
            "source": "hubspot",
            "email": properties.get("email", ""),
            "first_name": properties.get("firstname", ""),
            "last_name": properties.get("lastname", ""),
            "full_name": f"{properties.get('firstname', '')} {properties.get('lastname', '')}".strip(),
            "phone": properties.get("phone", ""),
            "company": properties.get("company", ""),
            "job_title": properties.get("jobtitle", ""),
            "website": properties.get("website", ""),
            "owner_id": properties.get("hubspot_owner_id", ""),
            "created_at": properties.get("createdate", ""),
            "updated_at": properties.get("lastmodifieddate", ""),
            "raw_data": contact
        }
    
    def get_companies(
        self,
        limit: int = 100,
        after: Optional[str] = None,
        properties: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get companies from HubSpot.
        
        Args:
            limit: Number of companies to retrieve (max 100)
            after: Pagination cursor
            properties: List of properties to retrieve
        
        Returns:
            Dictionary with companies and pagination info
        """
        default_properties = [
            "name", "domain", "phone", "website", "industry", 
            "city", "state", "country", "numberofemployees", "createdate"
        ]
        
        params = {
            "limit": min(limit, 100),
        }
        
        if after:
            params["after"] = after
        
        if properties:
            params["properties"] = ",".join(properties)
        else:
            params["properties"] = ",".join(default_properties)
        
        try:
            response = self._make_request("GET", "/crm/v3/objects/companies", params=params)
            
            companies = []
            for company in response.get("results", []):
                company_data = self._normalize_company(company)
                companies.append(company_data)
            
            return {
                "companies": companies,
                "paging": response.get("paging", {}),
                "has_more": "next" in response.get("paging", {}).get("next", {}),
                "next_cursor": response.get("paging", {}).get("next", {}).get("after") if "next" in response.get("paging", {}) else None
            }
        except Exception as e:
            print(f"Error fetching companies: {e}")
            return {"companies": [], "paging": {}, "has_more": False, "next_cursor": None}
    
    def _normalize_company(self, company: Dict) -> Dict:
        """Normalize HubSpot company data to standard format."""
        properties = company.get("properties", {})
        
        return {
            "id": company.get("id"),
            "source": "hubspot",
            "name": properties.get("name", ""),
            "domain": properties.get("domain", ""),
            "phone": properties.get("phone", ""),
            "website": properties.get("website", ""),
            "industry": properties.get("industry", ""),
            "city": properties.get("city", ""),
            "state": properties.get("state", ""),
            "country": properties.get("country", ""),
            "employee_count": properties.get("numberofemployees", ""),
            "created_at": properties.get("createdate", ""),
            "raw_data": company
        }
    
    def get_all_contacts(
        self,
        limit: Optional[int] = None,
        properties: Optional[List[str]] = None,
        filters: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        Get all contacts with automatic pagination.
        
        Args:
            limit: Maximum number of contacts to retrieve (None for all)
            properties: List of properties to retrieve
            filters: List of filter objects
        
        Returns:
            List of all contacts
        """
        all_contacts = []
        after = None
        batch_size = 100
        
        while True:
            if limit and len(all_contacts) >= limit:
                break
            
            current_limit = min(batch_size, limit - len(all_contacts)) if limit else batch_size
            result = self.get_contacts(
                limit=current_limit,
                after=after,
                properties=properties,
                filters=filters
            )
            
            all_contacts.extend(result.get("contacts", []))
            
            if not result.get("has_more") or not result.get("next_cursor"):
                break
            
            after = result.get("next_cursor")
        
        return all_contacts[:limit] if limit else all_contacts
    
    def search_leads(
        self,
        query: Optional[str] = None,
        job_title: Optional[str] = None,
        company: Optional[str] = None,
        industry: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search for leads based on criteria.
        
        Args:
            query: General search query
            job_title: Filter by job title
            company: Filter by company name
            industry: Filter by industry
            limit: Maximum number of results
        
        Returns:
            List of matching contacts
        """
        filters = []
        
        if job_title:
            filters.append({
                "propertyName": "jobtitle",
                "operator": "CONTAINS_TOKEN",
                "value": job_title
            })
        
        if company:
            filters.append({
                "propertyName": "company",
                "operator": "CONTAINS_TOKEN",
                "value": company
            })
        
        # For general query, search across multiple fields
        if query:
            # HubSpot doesn't support full-text search directly, so we'll use multiple filters
            # This is a simplified approach - you might want to use the search API differently
            pass
        
        return self.get_all_contacts(limit=limit, filters=filters if filters else None)

