from openai import OpenAI

from src.config import get_openai_api_key, OPENAI_CHAT_MODEL


class CriticAgent:
	def __init__(self):
		self.client = OpenAI(api_key=get_openai_api_key())

	def critique(self, plan_text: str) -> str:
		prompt = (
			"You are a rigorous marketing operator. Critique the plan. "
			"Identify assumptions, missing steps, measurability, capacity constraints, and potential improvements. "
			"Return an improved version preserving structure with explicit timelines and numeric KPIs where possible.\n\n"
			f"Plan to critique:\n{plan_text}\n\nImproved Plan:"
		)
		resp = self.client.chat.completions.create(
			model=OPENAI_CHAT_MODEL,
			messages=[{"role": "user", "content": prompt}],
			temperature=0.2,
		)
		return resp.choices[0].message.content.strip()


