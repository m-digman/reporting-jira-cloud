import unittest
from jira_config import jira_config


class jira_config_test(unittest.TestCase):


    def setUp(self):
        self.config = jira_config("test_conf.yaml")


    def test_uppercase_team_is_found(self):
        actual = self.config.find_team(["TEAM1", "project", "team2"])
        self.assertEqual(actual, "My team")


    def test_mixed_case_team_is_found(self):
        actual = self.config.find_team(["Team1", "product", "team2"])
        self.assertEqual(actual, "My team")


    def test_lowercase_team_is_found(self):
        actual = self.config.find_team(["bau", "team2", "team1"])
        self.assertEqual(actual, "Another team")


    def test_uppercase_category_is_found(self):
        actual = self.config.find_category(["team1", "PROJECT"])
        self.assertEqual(actual, "Project")


    def test_mixed_case_category_is_found(self):
        actual = self.config.find_category(["Improvement", "team2"])
        self.assertEqual(actual, "Product")


    def test_lowercase_category_is_found(self):
        actual = self.config.find_category(["bau", "team2"])
        self.assertEqual(actual, "BAU")


    def test_no_match_returns_unknown_category(self):
        actual = self.config.find_category(["QA"])
        self.assertEqual(actual, "Unknown")


    def test_find_filter_id(self):
        actual = self.config.find_filter_id("work_done")
        self.assertEqual(actual, 12345)


    def test_first_filter_found(self):
        actual = self.config.first_filter_id
        self.assertEqual(actual, 12345)


    def test_unknown_category_returned_if_not_configured(self):
        actual = self.config.category_colours.get("Unknown")
        self.assertIsNotNone(actual)


    def test_category_bau_is_darkviolet(self):
        actual = self.config.category_colours.get("BAU")
        self.assertEqual(actual, "darkviolet")


    def test_no_duplicate_teams_returned(self):
        actual = self.config.teams
        self.assertEqual(actual, ["My team", "Another team"])


    def test_base_url_returned(self):
        actual = self.config.base_url
        self.assertEqual(actual, "https://your-domain.atlassian.net/")


    def test_auth_values_returned(self):
        actual = self.config.auth_values
        self.assertEqual(actual, ("me@example.com", "my-api-token"))


if __name__ == '__main__':
    unittest.main()