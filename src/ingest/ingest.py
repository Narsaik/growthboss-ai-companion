import os
import json
from typing import List, Dict

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import RAW_DIR, PROCESSED_DIR


def _iter_raw() -> List[str]:
	return [os.path.join(RAW_DIR, f) for f in os.listdir(RAW_DIR) if f.endswith(".json")]


def _load_raw(path: str) -> Dict:
	with open(path, "r", encoding="utf-8") as f:
		return json.load(f)


def chunk_and_save() -> List[str]:
	text_splitter = RecursiveCharacterTextSplitter(
		chunk_size=1200,
		chunk_overlap=200,
		length_function=len,
		separators=["\n\n", "\n", ". ", " ", ""],
	)

	saved: List[str] = []
	for raw_path in _iter_raw():
		payload = _load_raw(raw_path)
		content = payload.get("content", "")
		if not content:
			continue
		chunks = text_splitter.split_text(content)
		for idx, chunk in enumerate(chunks):
			meta = {
				"source": payload.get("url"),
				"domain": payload.get("domain"),
				"title": payload.get("title"),
				"kind": payload.get("kind"),
				"chunk_index": idx,
			}
			fname = os.path.basename(raw_path).replace(".json", f"-c{idx:04d}.json")
			out_path = os.path.join(PROCESSED_DIR, fname)
			with open(out_path, "w", encoding="utf-8") as f:
				json.dump({"text": chunk, "metadata": meta}, f, ensure_ascii=False)
			saved.append(out_path)

	return saved


