import unittest

from matching import build_text, clean, rank_matches, score_all


def item(name, desc, loc="library", cat="Accessories"):
    return {"name": name, "category": cat, "description": desc, "location": loc}


class MatchingTests(unittest.TestCase):
    def test_clean_lowercases_and_removes_punctuation(self):
        self.assertEqual(clean("Black WALLET, near Library!"), "black wallet near library")

    def test_build_text_joins_all_fields(self):
        text = build_text(item("Wallet", "Black leather", "Canteen"))
        for word in ("wallet", "black", "leather", "canteen", "accessories"):
            self.assertIn(word, text)

    def test_identical_reports_score_one(self):
        a = item("Calculator", "Casio fx-991 black")
        scores = score_all(a, [a, item("Umbrella", "red umbrella")])
        self.assertAlmostEqual(scores[0], 1.0, places=6)

    def test_unrelated_reports_score_zero(self):
        scores = score_all(item("Calculator", "Casio black"),
                           [item("Umbrella", "red checked", "bus stop", "Misc")])
        self.assertEqual(scores[0], 0.0)

    def test_scores_are_between_zero_and_one(self):
        pool = [item("Wallet", "brown leather"), item("Wallet", "black zip"), item("Keys", "red keychain")]
        for s in score_all(item("Wallet", "brown leather with zip"), pool):
            self.assertGreaterEqual(s, 0.0)
            self.assertLessEqual(s, 1.0 + 1e-9)

    def test_best_match_is_ranked_first(self):
        pool = [item("Umbrella", "red umbrella"), item("Water bottle", "blue steel bottle Milton"),
                item("Keys", "bunch with red keychain")]
        result = rank_matches(item("Water bottle", "blue Milton bottle"), pool, threshold=0.1)
        self.assertEqual(result[0][0]["name"], "Water bottle")

    def test_threshold_filters_weak_matches(self):
        pool = [item("Umbrella", "red umbrella", "bus stop", "Misc")]
        self.assertEqual(rank_matches(item("Calculator", "Casio black"), pool, threshold=0.25), [])

    def test_top_n_limits_results(self):
        pool = [item("Wallet", "black wallet %d" % i) for i in range(10)]
        self.assertEqual(len(rank_matches(item("Wallet", "black wallet"), pool, threshold=0.0, top_n=3)), 3)

    def test_empty_candidate_list(self):
        self.assertEqual(rank_matches(item("Wallet", "black"), []), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
