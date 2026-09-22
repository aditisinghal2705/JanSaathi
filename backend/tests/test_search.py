import unittest

from app.services import search


def ids(query, prior=None):
    return [s.id for s in search.find_relevant(query, prior)]


class TestSearch(unittest.TestCase):
    def test_english_topics(self):
        self.assertEqual(ids("My father is 62 with no income. What pension schemes can he apply for?")[0], "old-age-pension")
        self.assertEqual(ids("What scholarships are available for SC students after class 10?")[0], "ashirwad-scholarship")
        self.assertEqual(ids("How do I get a subsidized ration card for my family?")[0], "smart-ration-card")
        self.assertEqual(ids("I finished college and I'm looking for a job or skill training")[0], "ghar-ghar-rozgar")

    def test_wedding_matches_both_marriage_schemes(self):
        found = ids("Are there any schemes to help with my daughter's wedding expenses?")
        self.assertIn("shagun-scheme", found)
        self.assertIn("aashirwad-scheme", found)

    def test_punjabi(self):
        self.assertEqual(ids("ਮੇਰੇ ਬਾਪੂ ਜੀ ਨੂੰ ਪੈਨਸ਼ਨ ਚਾਹੀਦੀ ਹੈ")[0], "old-age-pension")
        self.assertIn("shagun-scheme", ids("ਮੇਰੀ ਧੀ ਦੇ ਵਿਆਹ ਲਈ ਕੋਈ ਮਦਦ ਮਿਲ ਸਕਦੀ ਹੈ?"))
        self.assertEqual(ids("ਮੈਨੂੰ ਨੌਕਰੀ ਚਾਹੀਦੀ ਹੈ")[0], "ghar-ghar-rozgar")

    def test_hindi(self):
        self.assertEqual(ids("बुजुर्ग माता जी के लिए पेंशन")[0], "old-age-pension")
        self.assertIn("shagun-scheme", ids("मेरी बेटी की शादी के लिए मदद चाहिए"))
        self.assertEqual(ids("राशन कार्ड कैसे बनवाएं")[0], "smart-ration-card")

    def test_nukta_forms_are_equivalent(self):
        precomposed = "\u0A5B"            # Gurmukhi ZA as one code point
        decomposed = "\u0A1C\u0A3C"       # JA + nukta
        a = ids(f"ਵ{precomposed}ੀਫ਼ਾ")
        b = ids(f"ਵ{decomposed}ੀਫ਼ਾ")
        self.assertEqual(a, b)

    def test_romanised(self):
        self.assertEqual(ids("naukri chahiye")[0], "ghar-ghar-rozgar")
        self.assertEqual(ids("budhapa pension")[0], "old-age-pension")

    def test_unrelated_and_greetings_match_nothing(self):
        for q in ["what is the weather today", "tell me a joke", "hello", "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ", "धन्यवाद"]:
            self.assertEqual(ids(q), [], q)

    def test_followup_uses_previous_user_message(self):
        self.assertEqual(ids("How do I apply?", ["My father is 62 and needs a pension"]), ["old-age-pension"])

    def test_greeting_never_uses_history(self):
        self.assertEqual(ids("thanks", ["pension for my father"]), [])

    def test_empty_query(self):
        self.assertEqual(ids(""), [])
        self.assertEqual(ids("   "), [])

    def test_tokenizer_keeps_indic_words_whole(self):
        # \w would split at vowel signs; the custom tokenizer must not.
        self.assertEqual(search.tokenize("ਵਿਆਹ"), ["ਵਿਆਹ"])
        self.assertEqual(search.tokenize("विवाह"), ["विवाह"])

    def test_limit(self):
        self.assertLessEqual(len(search.find_relevant("marriage pension job scholarship ration", limit=2)), 2)


if __name__ == "__main__":
    unittest.main()
