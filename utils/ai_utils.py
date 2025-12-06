"""
utils/ai_utils.py

AI helpers for ServeLoop MVP.

Features:
- auto_tag_media(file_bytes=None, media_url=None): returns list of tags/labels and confidence scores
- generate_impact_summary(texts, max_sentences=3): condensed natural-language summary of provided texts

Design notes:
- This module supports multiple backends via environment variables:
  - VISION_PROVIDER: 'google' or 'local'
  - NLP_PROVIDER: 'hf' (HuggingFace transformers) or 'local'
- For hackathon demos the "local" fallback provides simple heuristics so the app works without cloud creds.
- If you want to use Google Vision or HuggingFace transformers, set appropriate environment variables and install libs.

Environment variables (optional):
- VISION_PROVIDER
- GOOGLE_APPLICATION_CREDENTIALS (if using Google Vision)
- NLP_PROVIDER

"""
import os
from typing import List, Tuple, Dict

# Try optional imports
try:
    from google.cloud import vision
    _GOOGLE_VISION_AVAILABLE = True
except Exception:
    _GOOGLE_VISION_AVAILABLE = False

try:
    # lightweight sentence transformer or transformers generation can be used
    from transformers import pipeline
    _HF_AVAILABLE = True
except Exception:
    _HF_AVAILABLE = False


# -------------------------
# Auto-tagging (Vision)
# -------------------------

def _local_image_tagger_placeholder(file_bytes=None, media_url=None) -> List[Tuple[str, float]]:
    """Very simple heuristic tagger: inspect bytes or url and guess tags.

    This is a fallback for hackathon demos so the UI can still show tags without cloud APIs.
    """
    tags = []
    if media_url:
        low = media_url.lower()
        if "beach" in low or "marina" in low:
            tags.append(("beach", 0.98))
        if "health" in low or "clinic" in low:
            tags.append(("health", 0.92))
        if "cleanup" in low or "trash" in low or "plastic" in low:
            tags.append(("cleanup", 0.95))
        if "food" in low or "meal" in low:
            tags.append(("food", 0.9))
    else:
        # if bytes provided, do naive size-based heuristics
        if file_bytes and len(file_bytes) > 200_000:
            tags.append(("photo", 0.8))
        else:
            tags.append(("image", 0.6))
    if not tags:
        tags.append(("event", 0.5))
    return tags


def _google_vision_tagger(file_bytes=None, media_url=None) -> List[Tuple[str, float]]:
    if not _GOOGLE_VISION_AVAILABLE:
        raise RuntimeError("Google Vision client not available. Install google-cloud-vision and set credentials.")
    client = vision.ImageAnnotatorClient()
    if file_bytes:
        image = vision.Image(content=file_bytes)
    elif media_url:
        image = vision.Image(source=vision.ImageSource(image_uri=media_url))
    else:
        raise ValueError("Provide file_bytes or media_url")

    response = client.label_detection(image=image)
    tags = []
    for label in response.label_annotations:
        tags.append((label.description, float(label.score)))
    return tags


def auto_tag_media(file_bytes: bytes = None, media_url: str = None) -> List[Tuple[str, float]]:
    """Auto-tag an uploaded media file using available provider.

    Returns a list of (tag, confidence) sorted by confidence desc.
    """
    provider = os.getenv("VISION_PROVIDER", "local").lower()
    if provider == "google" and _GOOGLE_VISION_AVAILABLE:
        try:
            tags = _google_vision_tagger(file_bytes=file_bytes, media_url=media_url)
        except Exception as e:
            print("Google Vision failed:", e)
            tags = _local_image_tagger_placeholder(file_bytes=file_bytes, media_url=media_url)
    else:
        tags = _local_image_tagger_placeholder(file_bytes=file_bytes, media_url=media_url)

    # normalize/sort
    tags_sorted = sorted(tags, key=lambda x: x[1], reverse=True)
    return tags_sorted


# -------------------------
# NLP: impact summaries
# -------------------------

def _local_summary(texts: List[str], max_sentences: int = 3) -> str:
    """Very naive summary: join top unique sentences and truncate."""
    if not texts:
        return ""
    # flatten and pick the longest sentences
    all_text = "\n".join(texts)
    sents = [s.strip() for s in all_text.replace("\n", " ").split('.') if s.strip()]
    sents_sorted = sorted(sents, key=lambda s: -len(s))
    top = sents_sorted[:max_sentences]
    summary = '. '.join(top)
    if summary and not summary.endswith('.'):
        summary += '.'
    return summary


def _hf_summarize(texts: List[str], max_sentences: int = 3) -> str:
    if not _HF_AVAILABLE:
        raise RuntimeError("HuggingFace transformers not available. Install transformers.")
    # use a text2text-generation or summarization pipeline
    summarizer = pipeline("summarization")
    joined = "\n".join(texts)
    # HuggingFace summarizers may have max token limits — keep inputs small
    if len(joined) > 3000:
        joined = joined[:3000]
    result = summarizer(joined, max_length=max_sentences * 40, min_length=30, do_sample=False)
    return result[0]["summary_text"]


def generate_impact_summary(texts: List[str], max_sentences: int = 3) -> str:
    """Generate a short impact summary from a list of textual inputs (captions, descriptions).

    Picks provider based on env var NLP_PROVIDER.
    """
    provider = os.getenv("NLP_PROVIDER", "local").lower()
    if provider == "hf" and _HF_AVAILABLE:
        try:
            return _hf_summarize(texts, max_sentences=max_sentences)
        except Exception as e:
            print("HF summarizer failed:", e)
            return _local_summary(texts, max_sentences=max_sentences)
    else:
        return _local_summary(texts, max_sentences=max_sentences)


# -------------------------
# Convenience: tag + summary together
# -------------------------

def analyze_proof_media(file_bytes: bytes = None, media_url: str = None, caption: str = None) -> Dict:
    """Run tagging on media and produce a short summary combining caption + top tags.

    Returns dict: {"tags": [(tag,conf)], "summary": str}
    """
    tags = auto_tag_media(file_bytes=file_bytes, media_url=media_url)
    top_tags = [t for t, s in tags[:5]]
    texts = []
    if caption:
        texts.append(caption)
    if top_tags:
        texts.append('Detected: ' + ', '.join(top_tags))
    summary = generate_impact_summary(texts, max_sentences=2)
    return {"tags": tags, "summary": summary}


# -------------------------
# Quick self-test
# -------------------------
if __name__ == "__main__":
    print("AI utils self-test")
    print(auto_tag_media(media_url="https://example.com/beach_cleanup.jpg"))
    print(generate_impact_summary(["Collected 20kg of plastic waste.", "Helped 30 families with food packs."], max_sentences=2))
