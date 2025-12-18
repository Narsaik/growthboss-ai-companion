"""
Conversation memory and session management.
10x improvement: Context-aware responses with conversation history.
"""

import json
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path

MEMORY_DIR = Path("data/memory")
MEMORY_DIR.mkdir(parents=True, exist_ok=True)


class ConversationMemory:
	"""Manages conversation history and context."""
	
	def __init__(self, session_id: Optional[str] = None):
		self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
		self.memory_file = MEMORY_DIR / f"{self.session_id}.json"
		self.conversations: List[Dict] = []
		self.user_profile: Dict = {}
		self._load()
	
	def _load(self):
		"""Load conversation history from disk."""
		if self.memory_file.exists():
			try:
				with open(self.memory_file, 'r', encoding='utf-8') as f:
					data = json.load(f)
					self.conversations = data.get('conversations', [])
					self.user_profile = data.get('user_profile', {})
			except Exception:
				self.conversations = []
				self.user_profile = {}
	
	def _save(self):
		"""Save conversation history to disk."""
		try:
			with open(self.memory_file, 'w', encoding='utf-8') as f:
				json.dump({
					'session_id': self.session_id,
					'conversations': self.conversations,
					'user_profile': self.user_profile,
					'last_updated': datetime.now().isoformat(),
				}, f, ensure_ascii=False, indent=2)
		except Exception:
			pass
	
	def add_exchange(self, query: str, answer: str, metadata: Optional[Dict] = None):
		"""Add a query-answer exchange to memory."""
		exchange = {
			'timestamp': datetime.now().isoformat(),
			'query': query,
			'answer': answer,
			'metadata': metadata or {},
		}
		self.conversations.append(exchange)
		self._save()
	
	def get_context(self, max_exchanges: int = 5) -> str:
		"""Get recent conversation context."""
		recent = self.conversations[-max_exchanges:]
		if not recent:
			return ""
		
		context = "Previous conversation:\n"
		for i, exchange in enumerate(recent, 1):
			context += f"\n{i}. Q: {exchange['query']}\n   A: {exchange['answer'][:200]}...\n"
		
		return context
	
	def get_user_preferences(self) -> Dict:
		"""Get user preferences from conversation history."""
		preferences = {
			'common_topics': [],
			'preferred_mentor': None,
			'query_patterns': [],
		}
		
		if not self.conversations:
			return preferences
		
		# Extract common topics from queries
		topics = {}
		for exchange in self.conversations:
			query_lower = exchange['query'].lower()
			# Simple keyword extraction
			for keyword in ['growth', 'marketing', 'ads', 'content', 'seo', 'retention', 'conversion']:
				if keyword in query_lower:
					topics[keyword] = topics.get(keyword, 0) + 1
		
		preferences['common_topics'] = sorted(
			topics.items(),
			key=lambda x: x[1],
			reverse=True
		)[:5]
		
		return preferences
	
	def update_profile(self, key: str, value: str):
		"""Update user profile information."""
		self.user_profile[key] = value
		self._save()
	
	def clear(self):
		"""Clear conversation history."""
		self.conversations = []
		self.user_profile = {}
		self._save()
	
	def get_session_summary(self) -> Dict:
		"""Get summary of current session."""
		return {
			'session_id': self.session_id,
			'exchange_count': len(self.conversations),
			'last_activity': self.conversations[-1]['timestamp'] if self.conversations else None,
			'preferences': self.get_user_preferences(),
		}


def get_memory(session_id: Optional[str] = None) -> ConversationMemory:
	"""Get or create conversation memory for a session."""
	return ConversationMemory(session_id=session_id)

