"""
Multilingual scheme retrieval (English, Punjabi/Gurmukhi, Hindi/Devanagari and
romanised Hinglish/Punjabi such as "shaadi" or "naukri").

Why this exists: the first version only matched English words against English
text, so a Punjabi or Hindi question could never find a scheme. Here every
language of every field is indexed together with per-scheme `keywords`, and a
small BM25 scorer ranks the results.

No external services or model downloads are required. When you are ready for
semantic search, replace `find_relevant()` with Azure AI Search (hybrid /
vector) and keep the same signature.
"""
import math
import re
import unicodedata
from collections import Counter

from app.models.schemas import Scheme
from app.services import scheme_store

# Latin + digits, Devanagari (minus the danda marks) and Gurmukhi.
# NOTE: Python's \w does NOT include Indic vowel signs (matras), so a plain \w+
# would chop Punjabi/Hindi words into pieces. The explicit ranges avoid that.
_TOKEN_RE = re.compile(r"[A-Za-z0-9\u0900-\u0963\u0966-\u097F\u0A00-\u0A7F]+")

def normalize(text: str) -> str:
    """NFC-normalise (unifies Gurmukhi/Devanagari nukta forms), drop ZWJ/ZWNJ, lowercase."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u200d", "").replace("\u200c", "")
    return text.lower()


_SMALLTALK = {
    "hi", "hello", "hey", "thanks", "thank", "thankyou", "ok", "okay", "bye", "namaste",
    "sat", "sri", "akal", "dhanyavad", "shukriya",
    "ਸਤਿ", "ਸ੍ਰੀ", "ਅਕਾਲ", "ਨਮਸਤੇ", "ਧੰਨਵਾਦ", "ਸ਼ੁਕਰੀਆ",
    "नमस्ते", "धन्यवाद", "शुक्रिया", "हेलो",
}

_STOPWORDS = _SMALLTALK | {
    # English
    "a", "an", "the", "is", "are", "am", "was", "be", "been", "i", "me", "my", "we", "our", "you", "your",
    "he", "she", "him", "her", "his", "they", "them", "their", "it", "its", "for", "of", "to", "in", "on", "at",
    "and", "or", "with", "can", "could", "would", "should", "do", "does", "did", "how", "what", "which", "who",
    "when", "where", "why", "get", "got", "want", "need", "have", "has", "any", "some", "there", "this", "that",
    "from", "by", "about", "help", "please", "tell", "know", "there", "than", "then", "also", "very",
    "scheme", "schemes", "yojana", "government", "govt", "punjab", "apply", "applied", "applying",
    "application", "eligible", "eligibility", "benefit", "benefits", "much", "many", "will", "not", "no",
    # Romanised Hindi / Punjabi function words
    "mera", "meri", "mere", "hai", "hain", "ka", "ki", "ke", "ko", "se", "me", "mein", "main", "kya", "kaise",
    "chahiye", "kaun", "liye", "aur", "ya", "koi", "ho", "hoga", "sakta", "sakti", "kar", "karna", "batao",
    "bataiye", "da", "di", "de", "nu", "te", "tho", "layi", "hunda", "kiven",
    # Hindi
    "के", "का", "की", "में", "है", "हैं", "और", "से", "को", "पर", "मेरे", "मेरा", "मेरी", "मुझे", "कि", "लिए",
    "एक", "कोई", "क्या", "कैसे", "कर", "करना", "सकता", "सकती", "चाहिए", "हो", "था", "थी", "यह", "वह", "ये", "वो",
    "तो", "भी", "कौन", "योजना", "योजनाएँ", "सरकार", "पंजाब", "आवेदन", "पात्र", "लाभ", "कितना", "मिलेगा", "बताएं",
    # Punjabi
    "ਦੇ", "ਦਾ", "ਦੀ", "ਵਿੱਚ", "ਹੈ", "ਹਨ", "ਅਤੇ", "ਤੋਂ", "ਨੂੰ", "ਲਈ", "ਮੇਰੇ", "ਮੇਰਾ", "ਮੇਰੀ", "ਮੈਨੂੰ", "ਕੀ",
    "ਕਿਵੇਂ", "ਕੋਈ", "ਇੱਕ", "ਹੋ", "ਸਕਦਾ", "ਸਕਦੀ", "ਚਾਹੀਦਾ", "ਇਹ", "ਉਹ", "ਵੀ", "ਕੌਣ", "ਤੇ", "ਜੀ", "ਕਰ",
    "ਸਕੀਮ", "ਸਕੀਮਾਂ", "ਸਰਕਾਰ", "ਪੰਜਾਬ", "ਅਰਜ਼ੀ", "ਯੋਗ", "ਲਾਭ", "ਕਿੰਨਾ", "ਮਿਲੇਗਾ", "ਦੱਸੋ",
}

# Static lists must be normalised the same way as user text, otherwise a word typed
# with a precomposed nukta letter (e.g. U+0A5B) would never equal its NFC form.
_SMALLTALK = {normalize(w) for w in _SMALLTALK}
_STOPWORDS = {normalize(w) for w in _STOPWORDS}

# Where a match counts for more.
_FIELD_WEIGHTS = {
    "name": 3.0,
    "keywords": 3.0,
    "category": 2.0,
    "description": 1.0,
    "eligibility": 1.0,
    "benefits": 1.0,
    "how_to_apply": 0.5,
}

_K1 = 1.5
_B = 0.75
_PREFIX_WEIGHT = 0.5      # "pensions" ~ "pension", Hindi/Punjabi suffix variants
_MIN_ABSOLUTE_SCORE = 0.6
_MIN_RELATIVE_SCORE = 0.4  # keep results within 40% of the best match


def tokenize(text: str, drop_stopwords: bool = True) -> list[str]:
    tokens = _TOKEN_RE.findall(normalize(text))
    if drop_stopwords:
        return [t for t in tokens if len(t) >= 2 and t not in _STOPWORDS]
    return tokens


def is_smalltalk(text: str) -> bool:
    """True for pure greetings / thanks like 'hello' or 'ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ'."""
    tokens = tokenize(text, drop_stopwords=False)
    return bool(tokens) and all(t in _SMALLTALK for t in tokens)


class _Index:
    def __init__(self, schemes: list[Scheme]):
        self.schemes = schemes
        self.docs: list[Counter] = []
        for s in schemes:
            tf: Counter = Counter()

            def add(texts, weight):
                for text in texts:
                    for tok in tokenize(text):
                        tf[tok] += weight

            add(s.name.values(), _FIELD_WEIGHTS["name"])
            add(s.keywords, _FIELD_WEIGHTS["keywords"])
            add([s.category, s.department], _FIELD_WEIGHTS["category"])
            add(s.description.values(), _FIELD_WEIGHTS["description"])
            add(s.eligibility.values(), _FIELD_WEIGHTS["eligibility"])
            add(s.benefits.values(), _FIELD_WEIGHTS["benefits"])
            add(s.how_to_apply.values(), _FIELD_WEIGHTS["how_to_apply"])
            self.docs.append(tf)

        self.lengths = [sum(tf.values()) for tf in self.docs]
        self.avg_len = (sum(self.lengths) / len(self.lengths)) if self.lengths else 1.0

    def _effective_tf(self, tf: Counter, token: str) -> float:
        if token in tf:
            return float(tf[token])
        if len(token) >= 4:
            best = 0.0
            for term, value in tf.items():
                if len(term) >= 4 and (term.startswith(token) or token.startswith(term)):
                    best = max(best, _PREFIX_WEIGHT * value)
            return best
        return 0.0

    def score(self, query: str) -> list[float]:
        tokens = set(tokenize(query))
        n_docs = len(self.docs)
        scores = [0.0] * n_docs
        if not tokens or n_docs == 0:
            return scores

        for token in tokens:
            eff = [self._effective_tf(tf, token) for tf in self.docs]
            n_match = sum(1 for e in eff if e > 0)
            if n_match == 0:
                continue
            idf = math.log(1 + (n_docs - n_match + 0.5) / (n_match + 0.5))
            for i, e in enumerate(eff):
                if e > 0:
                    length_norm = _K1 * (1 - _B + _B * self.lengths[i] / self.avg_len)
                    scores[i] += idf * (e * (_K1 + 1)) / (e + length_norm)
        return scores


_index: _Index | None = None
_index_source: int | None = None


def _get_index() -> _Index:
    """Build the index lazily and rebuild if the scheme list object changes."""
    global _index, _index_source
    schemes = scheme_store.load_schemes()
    if _index is None or _index_source != id(schemes):
        _index = _Index(schemes)
        _index_source = id(schemes)
    return _index


def search(query: str, limit: int = 3) -> list[tuple[Scheme, float]]:
    """Ranked (scheme, score) pairs for a single piece of text."""
    index = _get_index()
    scores = index.score(query)
    ranked = sorted(zip(index.schemes, scores), key=lambda pair: pair[1], reverse=True)
    if not ranked or ranked[0][1] < _MIN_ABSOLUTE_SCORE:
        return []
    floor = max(_MIN_ABSOLUTE_SCORE, ranked[0][1] * _MIN_RELATIVE_SCORE)
    return [(s, sc) for s, sc in ranked if sc >= floor][:limit]


def find_relevant(query: str, prior_user_messages: list[str] | None = None, limit: int = 3) -> list[Scheme]:
    """
    Schemes relevant to `query`.

    Follow-up questions such as "how do I apply?" carry no topic words, so when
    the message alone matches nothing we retry with the user's previous
    messages added. Greetings never trigger that fallback.
    """
    if is_smalltalk(query):
        return []

    results = search(query, limit)
    if not results and prior_user_messages:
        combined = " ".join(prior_user_messages[-2:]) + " " + query
        results = search(combined, limit)
    return [s for s, _ in results]
