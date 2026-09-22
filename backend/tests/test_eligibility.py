import unittest

from app.models.schemas import EligibilityRequest
from app.services import eligibility


def status_map(**kwargs):
    profile = EligibilityRequest(**{"age": None, "gender": None, "category": None, "situations": [], "language": "en", **kwargs})
    return {m.scheme.id: m for m in eligibility.screen(profile)}


class TestEligibility(unittest.TestCase):
    def test_pension_needs_age_60_and_residency(self):
        m = status_map(age=62, situations=["punjab_resident_3y"])["old-age-pension"]
        self.assertEqual(m.status, "likely")
        self.assertIn("income_limit", [r.code for r in m.verify])   # income is always left to the department

    def test_pension_too_young_is_unlikely(self):
        m = status_map(age=45, situations=["punjab_resident_3y"])["old-age-pension"]
        self.assertEqual(m.status, "unlikely")
        self.assertEqual([r.code for r in m.unmet], ["min_age"])

    def test_missing_age_is_maybe_not_no(self):
        m = status_map(age=None, situations=["punjab_resident_3y"])["old-age-pension"]
        self.assertEqual(m.status, "maybe")

    def test_rozgar_age_band(self):
        self.assertEqual(status_map(age=25, situations=["job_seeker"])["ghar-ghar-rozgar"].status, "likely")
        self.assertEqual(status_map(age=40, situations=["job_seeker"])["ghar-ghar-rozgar"].status, "unlikely")
        self.assertEqual(status_map(age=16, situations=["job_seeker"])["ghar-ghar-rozgar"].status, "unlikely")

    def test_scholarship_requires_sc_and_student(self):
        self.assertEqual(status_map(category="sc", situations=["student_post_matric"])["ashirwad-scholarship"].status, "likely")
        self.assertEqual(status_map(category="general", situations=["student_post_matric"])["ashirwad-scholarship"].status, "unlikely")
        self.assertEqual(status_map(category=None, situations=["student_post_matric"])["ashirwad-scholarship"].status, "maybe")
        self.assertEqual(status_map(category="sc", situations=[])["ashirwad-scholarship"].status, "unlikely")

    def test_hard_group_aashirwad(self):
        ok = status_map(situations=["daughter_marriage_planned", "widow_or_destitute_woman"])["aashirwad-scheme"]
        self.assertEqual(ok.status, "likely")
        no = status_map(situations=["daughter_marriage_planned"])["aashirwad-scheme"]
        self.assertEqual(no.status, "unlikely")
        self.assertEqual(no.unmet[0].code, "any_of")

    def test_soft_group_shagun_other_notified_categories(self):
        # Not SC and not BPL: the text says "other notified categories", so worth checking, not a hard no.
        m = status_map(category="general", situations=["daughter_marriage_planned"])["shagun-scheme"]
        self.assertEqual(m.status, "maybe")
        self.assertEqual(status_map(category="sc", situations=["daughter_marriage_planned"])["shagun-scheme"].status, "likely")
        self.assertEqual(status_map(category="general", situations=[])["shagun-scheme"].status, "unlikely")

    def test_ration_card_never_a_hard_no(self):
        self.assertNotEqual(status_map()["smart-ration-card"].status, "unlikely")
        self.assertEqual(status_map(situations=["bpl_or_nfsa_household"])["smart-ration-card"].status, "likely")

    def test_results_sorted_likely_first(self):
        profile = EligibilityRequest(age=62, gender=None, category=None, situations=["punjab_resident_3y"], language="en")
        order = [m.status for m in eligibility.screen(profile)]
        self.assertEqual(order, sorted(order, key=["likely", "maybe", "unlikely"].index))

    def test_localised_names(self):
        m = status_map(age=62, language="pa", situations=["punjab_resident_3y"])["old-age-pension"]
        self.assertNotEqual(m.scheme.name, "Old Age Pension Scheme")

    def test_every_scheme_is_returned(self):
        self.assertEqual(len(status_map()), 6)


if __name__ == "__main__":
    unittest.main()
