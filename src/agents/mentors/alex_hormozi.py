from typing import List, Dict
from openai import OpenAI

from src.config import get_openai_api_key, OPENAI_CHAT_MODEL
from src.rag.vectorstore import query


class AlexHormoziAgent:
	"""Agent representing Alex Hormozi's perspective on business and offers."""
	
	def __init__(self, collection_name: str):
		self.collection_name = collection_name
		self.client = OpenAI(api_key=get_openai_api_key())
		self.persona = (
			"You are Alex Hormozi, entrepreneur and author of '$100M Offers' and '$100M Leads'. "
			"Your core beliefs: 1) The offer is everything - make it so good they feel stupid saying no. "
			"2) Value equation: dream outcome x perceived likelihood / time delay x effort = offer value. "
			"3) Price based on value, not cost. 4) Front-load value delivery. 5) Systematize everything. "
			"6) Acquisition.com framework: offer → traffic → conversion. 7) Focus on existing customers first. "
			"You're analytical, direct, and focused on scalable systems and outrageous value creation."
		)
	
	def research(self, question: str, k: int = 8) -> Dict:
		"""Research using Alex Hormozi's knowledge base."""
		ctx = query(self.collection_name, question, k=k * 2)
		# Filter to Hormozi content
		hormozi_ctx = [c for c in ctx if 'hormozi' in (c.get('metadata', {}).get('domain', '') or '').lower() or
					   'acquisition.com' in (c.get('metadata', {}).get('source', '') or '').lower()][:k]
		
		if not hormozi_ctx:
			hormozi_ctx = ctx[:k]
		
		def fmt(c):
			meta = c['metadata'] or {}
			title = meta.get('title') or meta.get('source') or 'unknown'
			return f"[Source: {title}]\n{c['text']}"
		
		context_blob = "\n\n".join([fmt(c) for c in hormozi_ctx])
		prompt = (
			f"{self.persona}\n\n"
			"Answer the user's question from Alex Hormozi's perspective, using the context below. "
			"Be analytical, direct, and focused on value creation and scalable systems. "
			"Cite specific frameworks or insights.\n\n"
			f"Context:\n{context_blob}\n\n"
			f"Question: {question}\n\n"
			"Answer as Alex Hormozi:"
		)
		
		resp = self.client.chat.completions.create(
			model=OPENAI_CHAT_MODEL,
			messages=[{"role": "user", "content": prompt}],
			temperature=0.6,
		)
		answer = resp.choices[0].message.content.strip()
		return {"answer": answer, "evidence": hormozi_ctx, "mentor": "Alex Hormozi"}

