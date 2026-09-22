import unittest

from app.core import rate_limit


class TestRateLimit(unittest.TestCase):
    def setUp(self):
        rate_limit.reset()

    def test_allows_up_to_limit_then_blocks(self):
        results = [rate_limit.check("ip1", 3, now=100.0 + i) for i in range(5)]
        self.assertEqual([r[0] for r in results], [True, True, True, False, False])
        self.assertGreaterEqual(results[3][1], 1)

    def test_window_slides(self):
        for i in range(3):
            rate_limit.check("ip1", 3, now=100.0 + i)
        self.assertFalse(rate_limit.check("ip1", 3, now=110.0)[0])
        self.assertTrue(rate_limit.check("ip1", 3, now=170.0)[0])   # >60s later

    def test_keys_are_independent(self):
        for i in range(3):
            rate_limit.check("a", 3, now=100.0)
        self.assertFalse(rate_limit.check("a", 3, now=100.0)[0])
        self.assertTrue(rate_limit.check("b", 3, now=100.0)[0])


if __name__ == "__main__":
    unittest.main()
