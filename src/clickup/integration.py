"""
ClickUp Integration - Read and Write Documents
Comprehensive integration for managing ClickUp documents, tasks, and workflows.
"""

import os
import json
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime


class ClickUpIntegration:
	"""Comprehensive ClickUp API integration for reading and writing documents."""
	
	def __init__(self, api_token: Optional[str] = None, team_id: Optional[str] = None):
		"""
		Initialize ClickUp integration.
		
		Args:
			api_token: ClickUp API token (defaults to CLICKUP_API_TOKEN env var)
			team_id: ClickUp team ID (defaults to CLICKUP_TEAM_ID env var)
		"""
		self.api_token = api_token or os.getenv("CLICKUP_API_TOKEN")
		self.team_id = team_id or os.getenv("CLICKUP_TEAM_ID")
		self.base_url = "https://api.clickup.com/api/v2"
		
		if not self.api_token:
			raise ValueError("ClickUp API token required. Set CLICKUP_API_TOKEN environment variable or pass api_token parameter.")
		
		self.headers = {
			"Authorization": self.api_token,
			"Content-Type": "application/json"
		}
	
	def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
		"""Make API request to ClickUp."""
		url = f"{self.base_url}/{endpoint}"
		
		try:
			if method.upper() == "GET":
				response = requests.get(url, headers=self.headers, params=params, timeout=30)
			elif method.upper() == "POST":
				response = requests.post(url, headers=self.headers, json=data, params=params, timeout=30)
			elif method.upper() == "PUT":
				response = requests.put(url, headers=self.headers, json=data, params=params, timeout=30)
			elif method.upper() == "DELETE":
				response = requests.delete(url, headers=self.headers, params=params, timeout=30)
			else:
				raise ValueError(f"Unsupported HTTP method: {method}")
			
			response.raise_for_status()
			return response.json()
		except requests.exceptions.RequestException as e:
			error_msg = f"ClickUp API error: {e}"
			if hasattr(e.response, 'text'):
				error_msg += f" - Response: {e.response.text}"
			raise Exception(error_msg)
	
	# ==================== DOCUMENTS ====================
	# Note: ClickUp document API may vary. These methods attempt to work with available endpoints.
	
	def get_documents(self, folder_id: str) -> List[Dict]:
		"""
		Get all documents from a folder.
		Note: ClickUp document endpoints may vary. This attempts to fetch documents.
		
		Args:
			folder_id: ClickUp folder ID
		
		Returns:
			List of document dictionaries
		"""
		try:
			# Try folder documents endpoint
			response = self._make_request("GET", f"folder/{folder_id}/doc")
			return response.get("docs", [])
		except Exception as e:
			# Document API might not be available or might use different endpoint
			print(f"Note: Document API may not be available: {e}")
			return []
	
	def get_document(self, document_id: str) -> Optional[Dict]:
		"""
		Get a specific document by ID.
		
		Args:
			document_id: ClickUp document ID
		
		Returns:
			Document dictionary or None
		"""
		try:
			response = self._make_request("GET", f"doc/{document_id}")
			return response
		except Exception as e:
			print(f"Error fetching document {document_id}: {e}")
			return None
	
	def create_document(
		self,
		folder_id: str,
		name: str,
		content: str,
		content_type: str = "docx"
	) -> Optional[Dict]:
		"""
		Create a new document in ClickUp.
		
		Args:
			folder_id: ClickUp folder ID
			name: Document name
			content: Document content (markdown or text)
			content_type: Content type (docx, md, txt)
		
		Returns:
			Created document dictionary or None
		"""
		try:
			data = {
				"name": name,
				"content": content,
				"content_type": content_type
			}
			response = self._make_request("POST", f"folder/{folder_id}/doc", data=data)
			return response
		except Exception as e:
			print(f"Error creating document: {e}")
			return None
	
	def update_document(
		self,
		document_id: str,
		name: Optional[str] = None,
		content: Optional[str] = None
	) -> Optional[Dict]:
		"""
		Update an existing document.
		
		Args:
			document_id: ClickUp document ID
			name: New document name (optional)
			content: New document content (optional)
		
		Returns:
			Updated document dictionary or None
		"""
		try:
			data = {}
			if name:
				data["name"] = name
			if content:
				data["content"] = content
			
			if not data:
				return None
			
			response = self._make_request("PUT", f"doc/{document_id}", data=data)
			return response
		except Exception as e:
			print(f"Error updating document: {e}")
			return None
	
	def delete_document(self, document_id: str) -> bool:
		"""
		Delete a document.
		
		Args:
			document_id: ClickUp document ID
		
		Returns:
			True if successful, False otherwise
		"""
		try:
			self._make_request("DELETE", f"doc/{document_id}")
			return True
		except Exception as e:
			print(f"Error deleting document: {e}")
			return False
	
	# ==================== FOLDERS ====================
	
	def get_folders(self, space_id: str) -> List[Dict]:
		"""
		Get all folders in a space.
		
		Args:
			space_id: ClickUp space ID
		
		Returns:
			List of folder dictionaries
		"""
		try:
			response = self._make_request("GET", f"space/{space_id}/folder")
			return response.get("folders", [])
		except Exception as e:
			print(f"Error fetching folders: {e}")
			return []
	
	def create_folder(self, space_id: str, name: str) -> Optional[Dict]:
		"""
		Create a new folder.
		
		Args:
			space_id: ClickUp space ID
			name: Folder name
		
		Returns:
			Created folder dictionary or None
		"""
		try:
			data = {"name": name}
			response = self._make_request("POST", f"space/{space_id}/folder", data=data)
			return response
		except Exception as e:
			print(f"Error creating folder: {e}")
			return None
	
	# ==================== TEAMS ====================
	
	def get_teams(self) -> List[Dict]:
		"""
		Get all teams for the authenticated user.
		
		Returns:
			List of team dictionaries
		"""
		try:
			response = self._make_request("GET", "team")
			return response.get("teams", [])
		except Exception as e:
			print(f"Error fetching teams: {e}")
			return []
	
	# ==================== SPACES ====================
	
	def get_spaces(self, team_id: Optional[str] = None) -> List[Dict]:
		"""
		Get all spaces in a team.
		
		Args:
			team_id: ClickUp team ID (defaults to instance team_id, or first team if available)
		
		Returns:
			List of space dictionaries
		"""
		team = team_id or self.team_id
		
		# If no team ID, try to get first team
		if not team:
			teams = self.get_teams()
			if teams:
				team = teams[0].get("id")
				print(f"Using first team: {teams[0].get('name', 'Unknown')} (ID: {team})")
			else:
				raise ValueError("Team ID required. Set CLICKUP_TEAM_ID or pass team_id parameter.")
		
		try:
			response = self._make_request("GET", f"team/{team}/space")
			return response.get("spaces", [])
		except Exception as e:
			print(f"Error fetching spaces: {e}")
			return []
	
	# ==================== TASKS ====================
	
	def get_tasks(self, list_id: str, include_closed: bool = False) -> List[Dict]:
		"""
		Get tasks from a list.
		
		Args:
			list_id: ClickUp list ID
			include_closed: Include closed tasks
		
		Returns:
			List of task dictionaries
		"""
		try:
			params = {"archived": "false", "include_closed": str(include_closed).lower()}
			response = self._make_request("GET", f"list/{list_id}/task", params=params)
			return response.get("tasks", [])
		except Exception as e:
			print(f"Error fetching tasks: {e}")
			return []
	
	def create_task(
		self,
		list_id: str,
		name: str,
		description: Optional[str] = None,
		assignees: Optional[List[str]] = None,
		tags: Optional[List[str]] = None,
		status: Optional[str] = None,
		priority: Optional[int] = None,
		due_date: Optional[int] = None
	) -> Optional[Dict]:
		"""
		Create a new task.
		
		Args:
			list_id: ClickUp list ID
			name: Task name
			description: Task description
			assignees: List of assignee user IDs
			tags: List of tag names
			status: Task status
			priority: Priority (1=urgent, 2=high, 3=normal, 4=low)
			due_date: Due date (Unix timestamp in milliseconds)
		
		Returns:
			Created task dictionary or None
		"""
		try:
			data = {"name": name}
			if description:
				data["description"] = description
			if assignees:
				data["assignees"] = assignees
			if tags:
				data["tags"] = tags
			if status:
				data["status"] = status
			if priority:
				data["priority"] = priority
			if due_date:
				data["due_date"] = due_date
			
			response = self._make_request("POST", f"list/{list_id}/task", data=data)
			return response
		except Exception as e:
			print(f"Error creating task: {e}")
			return None
	
	def update_task(
		self,
		task_id: str,
		name: Optional[str] = None,
		description: Optional[str] = None,
		status: Optional[str] = None,
		priority: Optional[int] = None
	) -> Optional[Dict]:
		"""
		Update a task.
		
		Args:
			task_id: Task ID
			name: New task name
			description: New description
			status: New status
			priority: New priority
		
		Returns:
			Updated task dictionary or None
		"""
		try:
			data = {}
			if name:
				data["name"] = name
			if description:
				data["description"] = description
			if status:
				data["status"] = status
			if priority:
				data["priority"] = priority
			
			if not data:
				return None
			
			response = self._make_request("PUT", f"task/{task_id}", data=data)
			return response
		except Exception as e:
			print(f"Error updating task: {e}")
			return None
	
	# ==================== LISTS ====================
	
	def get_lists(self, folder_id: str) -> List[Dict]:
		"""
		Get all lists in a folder.
		
		Args:
			folder_id: ClickUp folder ID
		
		Returns:
			List of list dictionaries
		"""
		try:
			response = self._make_request("GET", f"folder/{folder_id}/list")
			return response.get("lists", [])
		except Exception as e:
			print(f"Error fetching lists: {e}")
			return []
	
	# ==================== UTILITY METHODS ====================
	
	def find_folder_by_name(self, space_id: str, folder_name: str) -> Optional[Dict]:
		"""Find a folder by name."""
		folders = self.get_folders(space_id)
		for folder in folders:
			if folder.get("name", "").lower() == folder_name.lower():
				return folder
		return None
	
	def find_space_by_name(self, team_id: Optional[str] = None, space_name: str = "") -> Optional[Dict]:
		"""Find a space by name."""
		spaces = self.get_spaces(team_id)
		for space in spaces:
			if space.get("name", "").lower() == space_name.lower():
				return space
		return None
	
	def find_document_by_name(self, folder_id: str, doc_name: str) -> Optional[Dict]:
		"""Find a document by name."""
		documents = self.get_documents(folder_id)
		for doc in documents:
			if doc.get("name", "").lower() == doc_name.lower():
				return doc
		return None
	
	def upload_document_from_file(
		self,
		folder_id: str,
		file_path: str,
		document_name: Optional[str] = None
	) -> Optional[Dict]:
		"""
		Upload a document from a local file.
		
		Args:
			folder_id: ClickUp folder ID
			file_path: Path to local file
			document_name: Optional document name (defaults to filename)
		
		Returns:
			Created document dictionary or None
		"""
		try:
			import os
			from pathlib import Path
			
			path = Path(file_path)
			if not path.exists():
				raise FileNotFoundError(f"File not found: {file_path}")
			
			name = document_name or path.stem
			
			# Read file content
			with open(path, 'r', encoding='utf-8') as f:
				content = f.read()
			
			# Determine content type
			ext = path.suffix.lower()
			content_type_map = {
				'.md': 'md',
				'.txt': 'txt',
				'.docx': 'docx',
				'.doc': 'docx'
			}
			content_type = content_type_map.get(ext, 'txt')
			
			return self.create_document(folder_id, name, content, content_type)
		except Exception as e:
			print(f"Error uploading document: {e}")
			return None
	
	def sync_document(
		self,
		folder_id: str,
		document_name: str,
		content: str,
		create_if_missing: bool = True
	) -> Optional[Dict]:
		"""
		Sync a document (create if missing, update if exists).
		
		Args:
			folder_id: ClickUp folder ID
			document_name: Document name
			content: Document content
			create_if_missing: Create document if it doesn't exist
		
		Returns:
			Document dictionary or None
		"""
		# Check if document exists
		existing = self.find_document_by_name(folder_id, document_name)
		
		if existing:
			# Update existing document
			return self.update_document(existing["id"], content=content)
		elif create_if_missing:
			# Create new document
			return self.create_document(folder_id, document_name, content)
		else:
			return None


# ==================== CONVENIENCE FUNCTIONS ====================

def get_clickup_client(api_token: Optional[str] = None, team_id: Optional[str] = None) -> ClickUpIntegration:
	"""Get a ClickUp integration client."""
	return ClickUpIntegration(api_token=api_token, team_id=team_id)


def upload_local_document_to_clickup(
	folder_id: str,
	file_path: str,
	api_token: Optional[str] = None
) -> Optional[Dict]:
	"""Upload a local document to ClickUp."""
	client = get_clickup_client(api_token=api_token)
	return client.upload_document_from_file(folder_id, file_path)


def sync_local_document_to_clickup(
	folder_id: str,
	document_name: str,
	file_path: str,
	api_token: Optional[str] = None
) -> Optional[Dict]:
	"""Sync a local document to ClickUp (create or update)."""
	client = get_clickup_client(api_token=api_token)
	
	# Read local file
	with open(file_path, 'r', encoding='utf-8') as f:
		content = f.read()
	
	return client.sync_document(folder_id, document_name, content, create_if_missing=True)

