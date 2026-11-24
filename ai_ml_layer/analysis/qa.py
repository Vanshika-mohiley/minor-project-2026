"""Lightweight page-grounded retrieval for annual-report Q&A (no unsupported claims)."""
import re
from collections import Counter
STOP = {"what", "which", "when", "where", "does", "this", "that", "with", "from", "have", "about", "company", "report", "tell", "show", "give", "were", "was", "the", "and", "for"}
def _tokens(text): return [t for t in re.findall(r"[a-zA-Z0-9₹.,%-]+", str(text).lower()) if len(t) > 2 and t not in STOP]
def answer_question(pages, question, top_k=4):
    terms = _tokens(question)
    if not terms: return {"answer": "Please ask a more specific question about the report.", "sources": []}
    ranked = []
    for page in pages:
        text = str(page.get("text", ""))
        counts = Counter(_tokens(text))
        score = sum(min(counts[t], 3) for t in terms)
        if score:
            sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
            relevant = sorted(((sum(1 for t in terms if t in set(_tokens(s))), s.strip()) for s in sentences if s.strip()), reverse=True)
            excerpt = " ".join(s for score_s, s in relevant[:2] if score_s > 0)[:900]
            if excerpt: ranked.append((score, page.get("page"), excerpt))
    ranked.sort(reverse=True)
    selected = ranked[:max(1, min(top_k, 8))]
    if not selected:
        return {"answer": "I could not find relevant text for that question in this document. Try different keywords or check whether the PDF contains selectable text.", "sources": []}
    sources = [{"page": p, "excerpt": e} for _, p, e in selected]
    answer = "The most relevant passages in the uploaded report are:\n\n" + "\n\n".join(f"Page {s['page']}: {s['excerpt']}" for s in sources)
    return {"answer": answer, "sources": sources}
