import unittest

from app.core.sanitize import clean_history, redact_sensitive


class TestSanitize(unittest.TestCase):
    def test_aadhaar_removed(self):
        for text in ["my aadhaar is 1234 5678 9012 ok", "1234-5678-9012", "123456789012"]:
            clean, changed = redact_sensitive(text)
            self.assertTrue(changed, text)
            self.assertNotRegex(clean, r"\d{4}")

    def test_mobile_and_otp_removed(self):
        for text in ["call me on 9876543210", "+91 98765 43210", "+919876543210", "OTP is 482913", "otp: 4821"]:
            clean, changed = redact_sensitive(text)
            self.assertTrue(changed, text)

    def test_card_number_removed(self):
        clean, changed = redact_sensitive("card 4111 1111 1111 1111 thanks")
        self.assertTrue(changed)
        self.assertNotIn("4111", clean)

    def test_normal_questions_untouched(self):
        for text in [
            "My father is 62 and gets ₹1,500 a month",
            "Marriage grant of 51000 rupees for 2 daughters",
            "I am 25 years old, class 12 passed in 2023",
            "ਮੇਰੇ ਬਾਪੂ ਜੀ ਦੀ ਉਮਰ 62 ਸਾਲ ਹੈ",
        ]:
            clean, changed = redact_sensitive(text)
            self.assertFalse(changed, text)
            self.assertEqual(clean, text)

    def test_history_is_trimmed_and_redacted(self):
        history = [{"role": "user", "content": f"message {i}"} for i in range(30)]
        history[-1]["content"] = "my number 9876543210"
        cleaned = clean_history(history, 10)
        self.assertEqual(len(cleaned), 10)
        self.assertNotIn("9876543210", cleaned[-1]["content"])
        self.assertEqual(clean_history(history, 0), [])


if __name__ == "__main__":
    unittest.main()
