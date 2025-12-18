import os
from dotenv import load_dotenv

load_dotenv()


def get_openai_api_key() -> str:
	key = os.getenv("OPENAI_API_KEY", "").strip()
	if not key:
		raise RuntimeError(
			"OPENAI_API_KEY is not set. Please:\n"
			"  1. Create a .env file in the project root, or\n"
			"  2. Export the environment variable: export OPENAI_API_KEY='your-key-here'\n"
			"  3. Get your API key from: https://platform.openai.com/api-keys"
		)
	return key


OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-large")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

DATA_DIR = os.path.join("data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
CHROMA_DIR = os.path.join(DATA_DIR, "chroma")

# Only create directories if not in serverless environment (Vercel has read-only filesystem)
if not os.getenv("VERCEL"):
	try:
		os.makedirs(RAW_DIR, exist_ok=True)
		os.makedirs(PROCESSED_DIR, exist_ok=True)
		os.makedirs(CHROMA_DIR, exist_ok=True)
	except OSError:
		pass  # Ignore if we can't create directories (serverless)


