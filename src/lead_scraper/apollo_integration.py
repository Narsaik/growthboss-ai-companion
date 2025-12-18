"""
Apollo Integration - Lead Discovery and Enrichment
Comprehensive integration for searching and fetching leads from Apollo.io.
"""

import os
import requests
import time
from typing import List, Dict, Optional, Any
from datetime import datetime


class ApolloIntegration:
    """Comprehensive Apollo.io API integration for lead discovery."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Apollo integration.
        
        Args:
            api_key: Apollo API key (defaults to APOLLO_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("APOLLO_API_KEY")
        self.base_url = "https://api.apollo.io/v1"
        
        if not self.api_key:
            raise ValueError(
                "Apollo API key required. Set APOLLO_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.headers = {
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "X-Api-Key": self.api_key
        }
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None, 
        params: Optional[Dict] = None
    ) -> Dict:
        """Make API request to Apollo."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Apollo uses API key in header (X-Api-Key) - already set in headers
        # Keep params for other query parameters
        if params is None:
            params = {}
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data, params=params, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"Apollo API error: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_msg += f" - Response: {e.response.text}"
                except:
                    pass
            raise Exception(error_msg)
    
    def search_people(
        self,
        person_titles: Optional[List[str]] = None,
        person_locations: Optional[List[str]] = None,
        person_seniorities: Optional[List[str]] = None,
        person_departments: Optional[List[str]] = None,
        q_keywords: Optional[str] = None,
        q_organization_name: Optional[str] = None,
        q_organization_domains: Optional[List[str]] = None,
        q_organization_num_employees_ranges: Optional[List[str]] = None,
        q_organization_keyword_tags: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 25
    ) -> Dict[str, Any]:
        """
        Search for people/leads in Apollo.
        
        Args:
            person_titles: List of job titles to search for
            person_locations: List of locations (e.g., ["San Francisco, CA, United States"])
            person_seniorities: List of seniority levels (e.g., ["VP", "Director", "Manager"])
            person_departments: List of departments (e.g., ["Sales", "Marketing"])
            q_keywords: Keywords to search for
            q_organization_name: Company name to search for
            q_organization_domains: List of company domains
            q_organization_num_employees_ranges: Employee count ranges (e.g., ["1,10", "11,50"])
            q_organization_keyword_tags: Industry tags/keywords
            page: Page number (default: 1)
            per_page: Results per page (max 100, default: 25)
        
        Returns:
            Dictionary with people/leads and pagination info
        """
        data = {
            "page": page,
            "per_page": min(per_page, 100),
        }
        
        if person_titles:
            data["person_titles"] = person_titles
        if person_locations:
            data["person_locations"] = person_locations
        if person_seniorities:
            data["person_seniorities"] = person_seniorities
        if person_departments:
            data["person_departments"] = person_departments
        if q_keywords:
            data["q_keywords"] = q_keywords
        if q_organization_name:
            data["q_organization_name"] = q_organization_name
        if q_organization_domains:
            data["q_organization_domains"] = q_organization_domains
        if q_organization_num_employees_ranges:
            data["q_organization_num_employees_ranges"] = q_organization_num_employees_ranges
        if q_organization_keyword_tags:
            data["q_organization_keyword_tags"] = q_organization_keyword_tags
        
        try:
            response = self._make_request("POST", "/mixed_people/search", data=data)
            
            people = []
            for person in response.get("people", []):
                person_data = self._normalize_person(person)
                people.append(person_data)
            
            pagination = response.get("pagination", {})
            return {
                "people": people,
                "page": pagination.get("page", page),
                "per_page": pagination.get("per_page", per_page),
                "total_entries": pagination.get("total_entries", 0),
                "total_pages": pagination.get("total_pages", 1),
                "has_more": pagination.get("page", page) < pagination.get("total_pages", 1)
            }
        except Exception as e:
            print(f"Error searching people: {e}")
            return {
                "people": [],
                "page": page,
                "per_page": per_page,
                "total_entries": 0,
                "total_pages": 0,
                "has_more": False
            }
    
    def _normalize_person(self, person: Dict) -> Dict:
        """Normalize Apollo person data to standard format."""
        organization = person.get("organization", {})
        
        return {
            "id": person.get("id"),
            "source": "apollo",
            "email": person.get("email", ""),
            "first_name": person.get("first_name", ""),
            "last_name": person.get("last_name", ""),
            "full_name": person.get("name", ""),
            "phone": person.get("phone_numbers", [{}])[0].get("raw_number", "") if person.get("phone_numbers") else "",
            "company": organization.get("name", ""),
            "company_id": organization.get("id"),
            "job_title": person.get("title", ""),
            "website": organization.get("website_url", ""),
            "linkedin_url": person.get("linkedin_url", ""),
            "twitter_url": person.get("twitter_url", ""),
            "city": person.get("city", ""),
            "state": person.get("state", ""),
            "country": person.get("country", ""),
            "department": person.get("department", ""),
            "seniority": person.get("seniority", ""),
            "created_at": person.get("created_at", ""),
            "updated_at": person.get("updated_at", ""),
            "raw_data": person
        }
    
    def search_organizations(
        self,
        name: Optional[str] = None,
        website_url: Optional[str] = None,
        industry: Optional[str] = None,
        employee_count_ranges: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        locations: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 25
    ) -> Dict[str, Any]:
        """
        Search for organizations/companies in Apollo.
        
        Args:
            name: Company name to search for
            website_url: Company website URL
            industry: Industry to filter by
            employee_count_ranges: Employee count ranges (e.g., ["1,10", "11,50"])
            keywords: Keywords to search for
            locations: List of locations
            page: Page number (default: 1)
            per_page: Results per page (max 100, default: 25)
        
        Returns:
            Dictionary with organizations and pagination info
        """
        data = {
            "page": page,
            "per_page": min(per_page, 100),
        }
        
        if name:
            data["name"] = name
        if website_url:
            data["website_url"] = website_url
        if industry:
            data["industry"] = industry
        if employee_count_ranges:
            data["organization_num_employees_ranges"] = employee_count_ranges
        if keywords:
            data["keywords"] = keywords
        if locations:
            data["organization_locations"] = locations
        
        try:
            response = self._make_request("POST", "/organizations/search", data=data)
            
            organizations = []
            for org in response.get("organizations", []):
                org_data = self._normalize_organization(org)
                organizations.append(org_data)
            
            pagination = response.get("pagination", {})
            return {
                "organizations": organizations,
                "page": pagination.get("page", page),
                "per_page": pagination.get("per_page", per_page),
                "total_entries": pagination.get("total_entries", 0),
                "total_pages": pagination.get("total_pages", 1),
                "has_more": pagination.get("page", page) < pagination.get("total_pages", 1)
            }
        except Exception as e:
            print(f"Error searching organizations: {e}")
            return {
                "organizations": [],
                "page": page,
                "per_page": per_page,
                "total_entries": 0,
                "total_pages": 0,
                "has_more": False
            }
    
    def _normalize_organization(self, organization: Dict) -> Dict:
        """Normalize Apollo organization data to standard format."""
        return {
            "id": organization.get("id"),
            "source": "apollo",
            "name": organization.get("name", ""),
            "domain": organization.get("website_url", ""),
            "website": organization.get("website_url", ""),
            "industry": organization.get("industry", ""),
            "employee_count": organization.get("estimated_num_employees", ""),
            "city": organization.get("city", ""),
            "state": organization.get("state", ""),
            "country": organization.get("country", ""),
            "linkedin_url": organization.get("linkedin_url", ""),
            "twitter_url": organization.get("twitter_url", ""),
            "created_at": organization.get("created_at", ""),
            "raw_data": organization
        }
    
    def get_all_people(
        self,
        person_titles: Optional[List[str]] = None,
        person_locations: Optional[List[str]] = None,
        person_seniorities: Optional[List[str]] = None,
        person_departments: Optional[List[str]] = None,
        q_keywords: Optional[str] = None,
        q_organization_name: Optional[str] = None,
        limit: Optional[int] = None,
        per_page: int = 25
    ) -> List[Dict]:
        """
        Get all people with automatic pagination.
        
        Args:
            person_titles: List of job titles to search for
            person_locations: List of locations
            person_seniorities: List of seniority levels
            person_departments: List of departments
            q_keywords: Keywords to search for
            q_organization_name: Company name to search for
            limit: Maximum number of results to retrieve
            per_page: Results per page (max 100)
        
        Returns:
            List of all matching people
        """
        all_people = []
        page = 1
        
        while True:
            if limit and len(all_people) >= limit:
                break
            
            result = self.search_people(
                person_titles=person_titles,
                person_locations=person_locations,
                person_seniorities=person_seniorities,
                person_departments=person_departments,
                q_keywords=q_keywords,
                q_organization_name=q_organization_name,
                page=page,
                per_page=min(per_page, 100)
            )
            
            people = result.get("people", [])
            all_people.extend(people)
            
            if not result.get("has_more") or (limit and len(all_people) >= limit):
                break
            
            page += 1
            # Rate limiting - Apollo recommends spacing out requests
            time.sleep(0.5)
        
        return all_people[:limit] if limit else all_people
    
    def enrich_person(self, email: Optional[str] = None, person_id: Optional[str] = None) -> Optional[Dict]:
        """
        Enrich person data by email or ID.
        
        Args:
            email: Email address to enrich
            person_id: Person ID to enrich
        
        Returns:
            Enriched person data or None
        """
        if not email and not person_id:
            raise ValueError("Either email or person_id must be provided")
        
        params = {}
        if email:
            params["email"] = email
        if person_id:
            params["person_id"] = person_id
        
        try:
            response = self._make_request("GET", "/people/match", params=params)
            person = response.get("person")
            if person:
                return self._normalize_person(person)
            return None
        except Exception as e:
            print(f"Error enriching person: {e}")
            return None

