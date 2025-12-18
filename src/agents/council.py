from typing import List, Dict
from openai import OpenAI

from src.config import get_openai_api_key, OPENAI_CHAT_MODEL
from src.agents.mentors.gary_vee import GaryVeeAgent
from src.agents.mentors.alex_hormozi import AlexHormoziAgent
from src.agents.mentors.iman_gadzhi import ImanGadzhiAgent


class MarketingCouncil:
	"""Orchestrates a council of marketing mentors to debate and synthesize answers."""
	
	def __init__(self, collection_name: str):
		self.collection_name = collection_name
		self.gary_vee = GaryVeeAgent(collection_name)
		self.alex_hormozi = AlexHormoziAgent(collection_name)
		self.iman_gadzhi = ImanGadzhiAgent(collection_name)
		self.client = OpenAI(api_key=get_openai_api_key())
	
	def deliberate(self, question: str, growthboss_context: str = "") -> Dict:
		"""
		Have each mentor research and answer, then synthesize their perspectives.
		"""
		# Each mentor researches independently
		gary_response = self.gary_vee.research(question, k=6)
		hormozi_response = self.alex_hormozi.research(question, k=6)
		iman_response = self.iman_gadzhi.research(question, k=6)
		
		# Create debate and synthesis prompt
		deliberation_prompt = (
			"You are coordinating a Marketing Council for GrowthBoss, a marketing agency. "
			"Three expert mentors have independently researched and answered the same question. "
			"Their responses are below.\n\n"
			"Your task:\n"
			"1. Identify where they agree (consensus points)\n"
			"2. Identify where they differ or complement each other (unique perspectives)\n"
			"3. Synthesize the BEST answer that combines their wisdom\n"
			"4. Provide actionable recommendations specific to GrowthBoss\n\n"
			f"GrowthBoss Context: {growthboss_context or 'Marketing agency focused on client acquisition, offer design, content-led inbound, outbound SDR support, profitable delivery SLAs.'}\n\n"
			f"Question: {question}\n\n"
			"=== GARY VAYNERCHUK (Gary Vee) ===\n"
			f"{gary_response['answer']}\n\n"
			"=== ALEX HORMOZI ===\n"
			f"{hormozi_response['answer']}\n\n"
			"=== IMAN GADZHI ===\n"
			f"{iman_response['answer']}\n\n"
			"=== SYNTHESIS INSTRUCTIONS ===\n"
			"Provide a structured synthesis:\n"
			"1. **Executive Summary**: 2-3 sentence answer combining all perspectives\n"
			"2. **Consensus Points**: Where all three mentors agree\n"
			"3. **Unique Perspectives**: What each mentor adds that others don't\n"
			"4. **GrowthBoss Recommendation**: Specific, actionable steps for GrowthBoss\n"
			"5. **Implementation Priority**: Ranked list of next steps\n\n"
			"Format the synthesis clearly and make it immediately actionable."
		)
		
		resp = self.client.chat.completions.create(
			model=OPENAI_CHAT_MODEL,
			messages=[{"role": "user", "content": deliberation_prompt}],
			temperature=0.5,
		)
		synthesis = resp.choices[0].message.content.strip()
		
		return {
			"synthesis": synthesis,
			"mentor_responses": {
				"gary_vee": gary_response,
				"alex_hormozi": hormozi_response,
				"iman_gadzhi": iman_response,
			},
			"question": question,
		}
	
	def ask(self, question: str, growthboss_context: str = "", show_deliberation: bool = False) -> str:
		"""
		Main entry point - returns the council's synthesized answer.
		"""
		result = self.deliberate(question, growthboss_context)
		
		if show_deliberation:
			# Show individual mentor responses
			print("\n" + "="*80)
			print("MENTOR DELIBERATIONS")
			print("="*80)
			for mentor_name, response in result["mentor_responses"].items():
				print(f"\n[{response['mentor']}]")
				print("-" * 80)
				print(response["answer"])
			print("\n" + "="*80)
			print("COUNCIL SYNTHESIS")
			print("="*80 + "\n")
		
		return result["synthesis"]

