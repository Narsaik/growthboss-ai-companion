from typing import List, Dict
from openai import OpenAI

from src.config import get_openai_api_key, OPENAI_CHAT_MODEL
from src.rag.vectorstore import query


class ImanGadzhiAgent:
	"""Agent representing Iman Gadzhi's perspective on agency operations and SMMA."""
	
	def __init__(self, collection_name: str):
		self.collection_name = collection_name
		self.client = OpenAI(api_key=get_openai_api_key())
		self.persona = (
			"You are Iman Gadzhi, founder of Agency Navigator and SMMA expert. "
			"Your core beliefs: 1) Systematize agency operations - scripts, processes, SOPs. "
			"2) Focus on client retention and delivery excellence. 3) Build a lean, profitable agency first. "
			"4) Master cold outreach and email sequences. 5) Use case studies and social proof. "
			"6) Price based on ROI, not hours. 7) Build a team systematically as you scale. "
			"8) Focus on one niche before expanding. You're practical, process-oriented, and focus on "
			"profitable agency operations and proven systems."
		)
	
	def research(self, question: str, k: int = 8) -> Dict:
		"""Research using Iman Gadzhi's knowledge base."""
		ctx = query(self.collection_name, question, k=k * 2)
		# Filter to Iman Gadzhi content
		iman_ctx = [c for c in ctx if 'gadzhi' in (c.get('metadata', {}).get('domain', '') or '').lower() or
					'imangadzhi' in (c.get('metadata', {}).get('source', '') or '').lower()][:k]
		
		if not iman_ctx:
			iman_ctx = ctx[:k]
		
		def fmt(c):
			meta = c['metadata'] or {}
			title = meta.get('title') or meta.get('source') or 'unknown'
			return f"[Source: {title}]\n{c['text']}"
		
		context_blob = "\n\n".join([fmt(c) for c in iman_ctx])
		prompt = (
			f"{self.persona}\n\n"
			"Answer the user's question from Iman Gadzhi's perspective, using the context below. "
			"Be practical, system-focused, and emphasize agency operations, processes, and profitability. "
			"Cite specific tactics or systems.\n\n"
			f"Context:\n{context_blob}\n\n"
			f"Question: {question}\n\n"
			"Answer as Iman Gadzhi:"
		)
		
		resp = self.client.chat.completions.create(
			model=OPENAI_CHAT_MODEL,
			messages=[{"role": "user", "content": prompt}],
			temperature=0.6,
		)
		answer = resp.choices[0].message.content.strip()
		return {"answer": answer, "evidence": iman_ctx, "mentor": "Iman Gadzhi"}

