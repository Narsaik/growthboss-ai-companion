"""
Query analytics and tracking system.
10x improvement: Data-driven insights for continuous improvement.
"""

import json
import os
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
from collections import defaultdict

ANALYTICS_DIR = Path("data/analytics")
ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)


class QueryTracker:
	"""Tracks queries and performance metrics."""
	
	def __init__(self):
		self.queries_file = ANALYTICS_DIR / "queries.json"
		self.metrics_file = ANALYTICS_DIR / "metrics.json"
		self.queries: List[Dict] = []
		self.metrics: Dict = defaultdict(int)
		self._load()
	
	def _load(self):
		"""Load analytics data."""
		if self.queries_file.exists():
			try:
				with open(self.queries_file, 'r', encoding='utf-8') as f:
					self.queries = json.load(f)
			except Exception:
				self.queries = []
		
		if self.metrics_file.exists():
			try:
				with open(self.metrics_file, 'r', encoding='utf-8') as f:
					self.metrics = json.load(f)
			except Exception:
				self.metrics = defaultdict(int)
	
	def _save(self):
		"""Save analytics data."""
		try:
			with open(self.queries_file, 'w', encoding='utf-8') as f:
				json.dump(self.queries[-1000:], f, ensure_ascii=False, indent=2)  # Keep last 1000
			
			with open(self.metrics_file, 'w', encoding='utf-8') as f:
				json.dump(dict(self.metrics), f, ensure_ascii=False, indent=2)
		except Exception:
			pass
	
	def track_query(
		self,
		query: str,
		response_time: float,
		result_count: int,
		session_id: Optional[str] = None,
		metadata: Optional[Dict] = None,
	):
		"""Track a query and its performance."""
		entry = {
			'timestamp': datetime.now().isoformat(),
			'query': query,
			'response_time': response_time,
			'result_count': result_count,
			'session_id': session_id,
			'metadata': metadata or {},
		}
		self.queries.append(entry)
		
		# Update metrics
		self.metrics['total_queries'] += 1
		self.metrics['avg_response_time'] = (
			(self.metrics.get('avg_response_time', 0) * (self.metrics['total_queries'] - 1) + response_time)
			/ self.metrics['total_queries']
		)
		
		self._save()
	
	def get_top_queries(self, limit: int = 10) -> List[Dict]:
		"""Get most common queries."""
		query_counts = defaultdict(int)
		for entry in self.queries:
			query_counts[entry['query']] += 1
		
		top = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
		return [{'query': q, 'count': c} for q, c in top]
	
	def get_metrics(self) -> Dict:
		"""Get performance metrics."""
		return {
			'total_queries': self.metrics.get('total_queries', 0),
			'avg_response_time': round(self.metrics.get('avg_response_time', 0), 2),
			'unique_queries': len(set(e['query'] for e in self.queries)),
			'active_sessions': len(set(e['session_id'] for e in self.queries if e.get('session_id'))),
		}
	
	def get_insights(self) -> Dict:
		"""Get insights from query patterns."""
		# Find knowledge gaps (queries with low result counts)
		low_result_queries = [
			e for e in self.queries
			if e.get('result_count', 0) < 3
		]
		
		# Find slow queries
		slow_queries = [
			e for e in self.queries
			if e.get('response_time', 0) > 5.0
		]
		
		return {
			'knowledge_gaps': len(low_result_queries),
			'slow_queries': len(slow_queries),
			'top_queries': self.get_top_queries(5),
			'recommendations': self._generate_recommendations(),
		}
	
	def _generate_recommendations(self) -> List[str]:
		"""Generate recommendations based on analytics."""
		recommendations = []
		
		if self.metrics.get('avg_response_time', 0) > 3.0:
			recommendations.append("Consider optimizing retrieval for faster responses")
		
		if len(self.queries) > 100:
			top_queries = self.get_top_queries(3)
			if top_queries:
				recommendations.append(
					f"Most common query type: '{top_queries[0]['query'][:50]}...' - consider adding FAQ"
				)
		
		return recommendations


# Global tracker instance
_tracker = None

def get_tracker() -> QueryTracker:
	"""Get global query tracker instance."""
	global _tracker
	if _tracker is None:
		_tracker = QueryTracker()
	return _tracker

