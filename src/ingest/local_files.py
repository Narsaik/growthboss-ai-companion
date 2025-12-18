"""Ingest local markdown files and documents into the RAG system."""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict
from urllib.parse import urlparse

from src.config import RAW_DIR


def _slugify(text: str) -> str:
	"""Convert text to filename-safe slug."""
	import re
	text = re.sub(r"[^a-zA-Z0-9_-]+", "-", text.strip().lower())
	return re.sub(r"-+", "-", text).strip("-")


def save_local_document(file_path: str, content: str, title: str = None) -> str:
	"""Save a local file as a raw document for ingestion."""
	file_path_obj = Path(file_path)
	sha = hashlib.sha256(file_path.encode("utf-8")).hexdigest()[:12]
	filename = f"local-{_slugify(file_path_obj.stem)}-{sha}.json"
	path = os.path.join(RAW_DIR, filename)
	
	with open(path, "w", encoding="utf-8") as f:
		json.dump({
			"url": f"file://{file_path}",
			"domain": "local",
			"title": title or file_path_obj.stem.replace("_", " ").title(),
			"kind": "local",
			"content": content
		}, f, ensure_ascii=False)
	
	return path


def ingest_local_files(file_paths: List[str]) -> List[str]:
	"""Ingest local markdown/text files into the RAG system."""
	saved: List[str] = []
	
	for file_path in file_paths:
		path_obj = Path(file_path)
		if not path_obj.exists():
			print(f"⚠ File not found: {file_path}")
			continue
		
		try:
			with open(path_obj, "r", encoding="utf-8") as f:
				content = f.read()
			
			if len(content.strip()) < 100:
				print(f"⚠ File too short, skipping: {file_path}")
				continue
			
			# Extract title from first heading if markdown
			title = None
			if path_obj.suffix == ".md":
				lines = content.split("\n")
				for line in lines[:10]:
					if line.startswith("# "):
						title = line[2:].strip()
						break
			
			if not title:
				title = path_obj.stem.replace("_", " ").title()
			
			saved_path = save_local_document(file_path, content, title)
			saved.append(saved_path)
			print(f"✓ Ingested: {path_obj.name}")
		
		except Exception as e:
			print(f"✗ Error reading {file_path}: {e}")
	
	return saved


def ingest_growthboss_docs() -> List[str]:
	"""Ingest all GrowthBoss-related documents."""
	project_root = Path(__file__).parent.parent.parent
	
	# GrowthBoss documents to ingest
	growthboss_files = [
		project_root / "docs" / "growthboss_business_knowledge.md",
		project_root / "docs" / "growthboss_30day_content_plan.md",
		project_root / "docs" / "growthboss_high_converting_ads.md",
	]
	
	# Filter to existing files
	existing_files = [str(f) for f in growthboss_files if f.exists()]
	
	if not existing_files:
		print("No GrowthBoss documents found to ingest")
		return []
	
	return ingest_local_files(existing_files)


if __name__ == "__main__":
	import sys
	if len(sys.argv) > 1:
		files = sys.argv[1:]
		saved = ingest_local_files(files)
		print(f"\n✓ Ingested {len(saved)} files")
	else:
		saved = ingest_growthboss_docs()
		print(f"\n✓ Ingested {len(saved)} GrowthBoss documents")

