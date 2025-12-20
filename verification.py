# verification.py

import requests
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SERP_API_KEY = "32f8787beb3b0dc1b8f908a7ceed37972a40ea72eaa379502f4a5a7ea2c67529"
SERP_URL = "https://serpapi.com/search"

TRUSTED_DOMAINS = [
    "reuters.com", "bbc.com", "apnews.com",
    "thehindu.com", "indianexpress.com", "ndtv.com",
    "who.int", "gov.in",
    "altnews.in", "boomlive.in",
    "snopes.com", "politifact.com"
]


def extract_claim(text: str) -> str:
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^\w\s]", "", text)

    sentences = re.split(r"[.!?]", text)
    sentences = [s.strip() for s in sentences if 6 <= len(s.split()) <= 18]

    return sentences[0] if sentences else text[:100]


def serp_search(query: str):
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERP_API_KEY,
        "num": 10
    }

    try:
        r = requests.get(SERP_URL, params=params, timeout=8)
        data = r.json()

        if "error" in data:
            print("SerpAPI error:", data["error"])
            return []

        # 🔥 Read BOTH organic + news results
        return data.get("organic_results", []) + data.get("news_results", [])

    except Exception as e:
        print("SerpAPI exception:", e)
        return []


def verify_claim(text: str, status: str):
    claim = extract_claim(text)
    results = serp_search(claim)

    SUPPORT_WORDS = ["confirmed", "official", "announced", "launches", "reports"]
    CONTRADICT_WORDS = [
        "fake", "false", "hoax", "misleading",
        "no evidence", "debunk", "fact check",
        "denies", "clarifies"
    ]

    sources = []
    support_count = 0
    contradict_count = 0

    for r in results:
        link = r.get("link")
        title = (r.get("title") or "").lower()
        snippet = (r.get("snippet") or "").lower()

        if not link or not title:
            continue

        domain = link.split("/")[2]
        trusted = any(d in domain for d in TRUSTED_DOMAINS)
        top_rank = r.get("position", 99) <= 5

        if not trusted and not top_rank:
            continue

        text_blob = title + " " + snippet

        is_contradict = any(w in text_blob for w in CONTRADICT_WORDS)
        is_support = any(w in text_blob for w in SUPPORT_WORDS)

        if is_contradict:
            contradict_count += 1
        elif is_support:
            support_count += 1

        sources.append({
            "title": r.get("title"),
            "url": link,
            "publisher": domain,
            "match_score": 1.0,
            "stance": "contradicts" if is_contradict else "supports" if is_support else "unclear"
        })

        if len(sources) >= 3:
            break

    # 🔥 FINAL VERDICT FROM SOURCES
    if contradict_count > support_count:
        verdict = "Fake"
        explanation = "Multiple trusted sources contradict or debunk this claim."
    elif support_count > 0:
        verdict = "Real"
        explanation = "Trusted sources support or confirm this claim."
    else:
        verdict = "Unverified"
        explanation = "Sources mention the topic but do not clearly confirm it."

    return {
        "verdict": verdict,
        "explanation": explanation,
        "sources": sources
    }