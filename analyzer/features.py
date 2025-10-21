# service/analyzer/features.py
from typing import List, Dict
import textstat
import re

# YAKE keyword extractor is optional but recommended for better keywords.
# If you don't have it installed you can fallback to a simple frequency-based extractor.
try:
    import yake
    _YAKE_AVAILABLE = True
except Exception:
    _YAKE_AVAILABLE = False

def top_keywords_from_text(text: str, max_keywords: int = 10) -> List[str]:
    """
    Return a list of top keywords/phrases from text.
    Uses YAKE if available; otherwise a simple frequency-based extractor.
    """
    text = (text or "").strip()
    if not text:
        return []

    if _YAKE_AVAILABLE:
        kw_extractor = yake.KeywordExtractor(lan="en", n=3, dedupLim=0.9, top=max_keywords, features=None)
        keywords_with_scores = kw_extractor.extract_keywords(text)
        return [kw for kw, score in keywords_with_scores]

    # Simple fallback: tokenize, remove short words, count frequency of unigrams & bigrams
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    if not words:
        return []
    # unigram frequencies
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1

    # bigrams
    bigrams = []
    for i in range(len(words) - 1):
        bigrams.append((words[i], words[i+1]))
    bigram_freq = {}
    for a, b in bigrams:
        k = f"{a} {b}"
        bigram_freq[k] = bigram_freq.get(k, 0) + 1

    # pick top from bigrams first, then unigrams
    sorted_bigrams = sorted(bigram_freq.items(), key=lambda x: -x[1])
    sorted_unigrams = sorted(freq.items(), key=lambda x: -x[1])

    results = [k for k, _ in sorted_bigrams[: max_keywords//2]]
    # fill remaining with unigrams
    for k, _ in sorted_unigrams:
        if len(results) >= max_keywords:
            break
        if k not in results:
            results.append(k)
    return results[:max_keywords]


def readability_scores(text: str) -> Dict[str, float]:
    """
    Return common readability metrics and counts using textstat.
    """
    text = (text or "").strip()
    if not text:
        return {
            "flesch_reading_ease": 0.0,
            "flesch_kincaid_grade": 0.0,
            "smog_index": 0.0,
            "word_count": 0,
            "sentence_count": 0
        }

    try:
        fre = textstat.flesch_reading_ease(text)
        fk = textstat.flesch_kincaid_grade(text)
        smog = textstat.smog_index(text)
        wc = textstat.lexicon_count(text, removepunct=True)
        sc = textstat.sentence_count(text)
    except Exception:
        # If textstat not installed or fails, return conservative defaults
        return {
            "flesch_reading_ease": 0.0,
            "flesch_kincaid_grade": 0.0,
            "smog_index": 0.0,
            "word_count": len(re.findall(r"\w+", text)),
            "sentence_count": max(1, len(re.split(r"[.!?]+", text))) 
        }

    return {
        "flesch_reading_ease": fre,
        "flesch_kincaid_grade": fk,
        "smog_index": smog,
        "word_count": wc,
        "sentence_count": sc
    }
