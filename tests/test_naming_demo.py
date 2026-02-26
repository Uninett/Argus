"""Mock tests to demo the test naming convention checker."""


class TestNamingConventionDemo:
    # These follow the convention
    def test_when_user_is_admin_then_can_access_dashboard(self):
        pass

    def test_it_should_return_empty_list_for_no_incidents(self):
        pass

    def test_given_expired_token_when_refreshing_then_raises_error(self):
        pass

    # These do NOT follow the convention
    def test_admin_dashboard_access(self):
        pass

    def test_empty_list_no_incidents(self):
        pass

    def test_refresh_expired_token_raises_error(self):
        pass

    def test_can_create_user(self):
        pass
