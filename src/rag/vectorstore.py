import os
import json
from typing import List, Dict, Tuple

import chromadb
from chromadb.config import Settings
from openai import OpenAI

from src.config import CHROMA_DIR, PROCESSED_DIR, get_openai_api_key, OPENAI_EMBED_MODEL


def _iter_processed() -> List[str]:
	return [os.path.join(PROCESSED_DIR, f) for f in os.listdir(PROCESSED_DIR) if f.endswith(".json")]


def _load_json(path: str) -> Dict:
	with open(path, "r", encoding="utf-8") as f:
		return json.load(f)


def _get_or_create_collection(client: chromadb.Client, name: str):
	return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})


def build_vectorstore(collection_name: str = "growthboss-rag") -> Tuple[chromadb.Client, str]:
	client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
	try:
		collection = client.get_collection(name=collection_name)
		# Delete all existing documents
		all_ids = collection.get()["ids"]
		if all_ids:
			collection.delete(ids=all_ids)
	except:
		# Collection doesn't exist, create it
		collection = _get_or_create_collection(client, collection_name)

	client_oai = OpenAI(api_key=get_openai_api_key())
	texts: List[str] = []
	metadatas: List[Dict] = []
	ids: List[str] = []

	for path in _iter_processed():
		payload = _load_json(path)
		text = payload.get("text", "").strip()
		meta = payload.get("metadata", {})
		if not text:
			continue
		texts.append(text)
		metadatas.append(meta)
		ids.append(os.path.basename(path))

	# Embed in batches to avoid token/size limits
	batch_size = 64
	for i in range(0, len(texts), batch_size):
		batch = texts[i : i + batch_size]
		resp = client_oai.embeddings.create(model=OPENAI_EMBED_MODEL, input=batch)
		embeds = [e.embedding for e in resp.data]
		collection.add(ids=ids[i : i + batch_size], embeddings=embeds, metadatas=metadatas[i : i + batch_size], documents=batch)

	return client, collection.name


def query(collection_name: str, query_text: str, k: int = 8, per_domain: int = 3) -> List[Dict]:
	client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
	collection = _get_or_create_collection(client, collection_name)
	# Embed query text using OpenAI
	client_oai = OpenAI(api_key=get_openai_api_key())
	query_embed = client_oai.embeddings.create(model=OPENAI_EMBED_MODEL, input=[query_text])
	query_embedding = query_embed.data[0].embedding
	# Over-fetch to enable diversity filtering
	overfetch = max(k * 3, k + 10)
	results = collection.query(query_embeddings=[query_embedding], n_results=overfetch)
	docs = results.get("documents", [[]])[0]
	metas = results.get("metadatas", [[]])[0]
	scores = results.get("distances", [[]])[0]
	ranked = [
		{"text": d, "metadata": m, "score": s}
		for d, m, s in zip(docs, metas, scores)
	]
	# Domain diversity limiting
	kept: List[Dict] = []
	per_domain_counts: Dict[str, int] = {}
	for item in ranked:
		domain = (item["metadata"] or {}).get("domain") or "unknown"
		count = per_domain_counts.get(domain, 0)
		if count >= per_domain:
			continue
		kept.append(item)
		per_domain_counts[domain] = count + 1
		if len(kept) >= k:
			break
	if not kept:
		return ranked[:k]
	return kept


