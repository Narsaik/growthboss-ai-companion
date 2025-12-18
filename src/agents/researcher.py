from typing import List, Optional
from openai import OpenAI
import time

from src.config import get_openai_api_key, OPENAI_CHAT_MODEL
from src.rag.vectorstore import query
from src.rag.enhanced_retrieval import enhanced_query
from src.memory.conversation_memory import get_memory, ConversationMemory
from src.analytics.query_tracker import get_tracker


class ResearcherAgent:
	def __init__(self, collection_name: str, use_enhanced: bool = True, session_id: Optional[str] = None):
		self.collection_name = collection_name
		self.client = OpenAI(api_key=get_openai_api_key())
		self.use_enhanced = use_enhanced
		self.memory = get_memory(session_id)
		self.tracker = get_tracker()

	def research(self, question: str, k: int = 12, include_context: bool = True) -> dict:
		start_time = time.time()
		
		# Get conversation context
		context = ""
		if include_context:
			context = self.memory.get_context()
		
		# Use enhanced retrieval if enabled
		if self.use_enhanced:
			ctx = enhanced_query(self.collection_name, question, k=k)
		else:
			ctx = query(self.collection_name, question, k=k)
		
		response_time = time.time() - start_time
		
		# Track query
		self.tracker.track_query(
			query=question,
			response_time=response_time,
			result_count=len(ctx),
			session_id=self.memory.session_id,
		)
		def fmt(c):
			meta = c['metadata'] or {}
			title = meta.get('title') or meta.get('source') or 'unknown'
			domain = meta.get('domain') or 'unknown'
			return f"[Source: {title} | {domain}]\n{c['text']}"
		context_blob = "\n\n".join([fmt(c) for c in ctx])
		# Build prompt with conversation context
		prompt_parts = [
			"You are a marketing researcher analyzing teachings from Gary Vaynerchuk, Alex Hormozi, and Iman Gadzhi. "
			"Summarize the most relevant insights to answer the user's question. "
			"Cite sources inline as (source). Be concise and actionable.",
		]
		
		if context:
			prompt_parts.append(f"\n{context}")
		
		prompt_parts.append(f"\nRetrieved Context:\n{context_blob}\n\nQuestion: {question}\n\nAnswer:")
		
		prompt = "\n".join(prompt_parts)
		resp = self.client.chat.completions.create(
			model=OPENAI_CHAT_MODEL,
			messages=[{"role": "user", "content": prompt}],
			temperature=0.2,
		)
		answer = resp.choices[0].message.content.strip()
		
		# Save to memory
		self.memory.add_exchange(question, answer, metadata={'result_count': len(ctx)})
		
		return {"answer": answer, "evidence": ctx, "session_id": self.memory.session_id}


