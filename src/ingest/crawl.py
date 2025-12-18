import os
import re
import json
import hashlib
from urllib.parse import urlparse, parse_qs
from typing import List, Dict, Optional

import trafilatura
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import yaml
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

from src.config import RAW_DIR


def _slugify(text: str) -> str:
	text = re.sub(r"[^a-zA-Z0-9_-]+", "-", text.strip().lower())
	return re.sub(r"-+", "-", text).strip("-")


def load_sources(path: str) -> Dict:
	with open(path, "r", encoding="utf-8") as f:
		return yaml.safe_load(f)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def fetch_web_to_text(url: str) -> Optional[str]:
	downloaded = trafilatura.fetch_url(url)
	if not downloaded:
		return None
	text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
	return text


def extract_youtube_video_id(url: str) -> Optional[str]:
	parsed = urlparse(url)
	if parsed.netloc.endswith("youtube.com"):
		qs = parse_qs(parsed.query)
		return qs.get("v", [None])[0]
	if parsed.netloc.endswith("youtu.be"):
		return parsed.path.strip("/") or None
	return None


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8),
       retry=retry_if_exception_type(Exception))
def fetch_youtube_transcript(video_id: str) -> Optional[str]:
	try:
		transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
		# Try to get English transcript
		try:
			transcript = transcript_list.find_transcript(['en'])
			tracks = transcript.fetch()
		except:
			# Try auto-generated English
			try:
				transcript = transcript_list.find_generated_transcript(['en'])
				tracks = transcript.fetch()
			except:
				return None
		text = "\n".join([t.get("text", "").replace("\n", " ") for t in tracks])
		return text or None
	except (TranscriptsDisabled, NoTranscriptFound):
		return None
	except Exception:
		return None


def _extract_title(html: str) -> Optional[str]:
	try:
		soup = BeautifulSoup(html, "html.parser")
		title = soup.title.string if soup.title else None
		if title:
			return title.strip()
	except Exception:
		return None
	return None


def save_raw_document(source_url: str, content: str, kind: str, title: Optional[str] = None) -> str:
	sha = hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:12]
	filename = f"{kind}-{_slugify(source_url)[:60]}-{sha}.json"
	path = os.path.join(RAW_DIR, filename)
	with open(path, "w", encoding="utf-8") as f:
		parsed = urlparse(source_url)
		json.dump({
			"url": source_url,
			"domain": parsed.netloc,
			"title": title,
			"kind": kind,
			"content": content
		}, f, ensure_ascii=False)
	return path


def run_crawl(sources_yaml: str) -> List[str]:
	sources = load_sources(sources_yaml)
	saved: List[str] = []
	seen: set[str] = set()

	for url in sources.get("web", []) or []:
		if url in seen:
			continue
		seen.add(url)
		try:
			downloaded = trafilatura.fetch_url(url)
			text = trafilatura.extract(downloaded, include_comments=False, include_tables=False) if downloaded else None
			if text and len(text.strip()) > 200:
				title = _extract_title(downloaded or "") if downloaded else None
				path = save_raw_document(url, text, kind="web", title=title)
				saved.append(path)
		except Exception as e:
			print(f"Failed to fetch {url}: {e}")

	for yurl in sources.get("youtube", []) or []:
		vid = extract_youtube_video_id(yurl)
		if not vid:
			continue
		text = fetch_youtube_transcript(vid)
		if text and len(text.strip()) > 100:
			path = save_raw_document(yurl, text, kind="youtube", title=None)
			saved.append(path)

	return saved


