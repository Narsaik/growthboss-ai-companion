from typing import List, Dict
from openai import OpenAI

from src.config import get_openai_api_key, OPENAI_CHAT_MODEL
from src.rag.vectorstore import query


class GaryVeeAgent:
	"""Agent representing Gary Vaynerchuk's perspective on marketing."""
	
	def __init__(self, collection_name: str):
		self.collection_name = collection_name
		self.client = OpenAI(api_key=get_openai_api_key())
		self.persona = (
			"You are Gary Vaynerchuk (Gary Vee), a serial entrepreneur and marketing expert. "
			"Your core beliefs: 1) Content is king - document, don't create. 2) Jab, Jab, Jab, Right Hook - "
			"give value first. 3) Attention is the new asset. 4) Long-term thinking, patience, and kindness. "
			"5) Native content for each platform. 6) PBCPG (Podcast, Blog, Clubhouse, Podcast, Group chats) framework. "
			"7) Live-streaming is the future. You emphasize authenticity, patience, and platform-native strategies."
		)
	
	def research(self, question: str, k: int = 8) -> Dict:
		"""Research using Gary Vee's knowledge base."""
		# Filter for Gary Vee content
		ctx = query(self.collection_name, question, k=k * 2)  # Over-fetch
		# Filter to Gary Vee sources
		gary_ctx = [c for c in ctx if 'garyvaynerchuk' in (c.get('metadata', {}).get('domain', '') or '').lower() or 
					'vayner' in (c.get('metadata', {}).get('source', '') or '').lower()][:k]
		
		if not gary_ctx:
			gary_ctx = ctx[:k]  # Fallback if no specific match
		
		def fmt(c):
			meta = c['metadata'] or {}
			title = meta.get('title') or meta.get('source') or 'unknown'
			return f"[Source: {title}]\n{c['text']}"
		
		context_blob = "\n\n".join([fmt(c) for c in gary_ctx])
		prompt = (
			f"{self.persona}\n\n"
			"Answer the user's question from Gary Vaynerchuk's perspective, drawing on the context below. "
			"Be authentic to Gary's voice: direct, practical, patient, and focused on long-term value. "
			"Cite specific insights from the context.\n\n"
			f"Context:\n{context_blob}\n\n"
			f"Question: {question}\n\n"
			"Answer as Gary Vaynerchuk:"
		)
		
		resp = self.client.chat.completions.create(
			model=OPENAI_CHAT_MODEL,
			messages=[{"role": "user", "content": prompt}],
			temperature=0.7,
		)
		answer = resp.choices[0].message.content.strip()
		return {"answer": answer, "evidence": gary_ctx, "mentor": "Gary Vee"}

