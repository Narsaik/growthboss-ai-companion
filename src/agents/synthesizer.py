from openai import OpenAI

from src.config import get_openai_api_key, OPENAI_CHAT_MODEL


class SynthesizerAgent:
	def __init__(self):
		self.client = OpenAI(api_key=get_openai_api_key())

	def synthesize(self, question: str, research_answer: str, brand_context: str) -> str:
		prompt = (
			"You are a senior marketing strategist at GrowthBoss. Blend the research with our context to produce a clear, actionable plan. "
			"Return structured output with sections: Objective, Core Insight, Strategy, Tactics, Content Plan, Offers, KPIs, Risks, Next Steps.\n\n"
			f"GrowthBoss Context:\n{brand_context}\n\n"
			f"User Question:\n{question}\n\n"
			f"Research Summary:\n{research_answer}\n\n"
			"Now produce the plan:"
		)
		resp = self.client.chat.completions.create(
			model=OPENAI_CHAT_MODEL,
			messages=[{"role": "user", "content": prompt}],
			temperature=0.3,
		)
		return resp.choices[0].message.content.strip()


