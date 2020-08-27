"""
# FIXME: running the tests causes weird uncatchable "AttributeError: 'WindowsPath' object has no attribute 'rstrip'"
#  ('WindowsPath' is replaced by 'UnixPath' on Unix-based systems.) The error does not appear if running tests in debug mode.
from io import StringIO

from django.test import TestCase
from django.core.management import call_command
from . import generate_fixtures


class GenerateFixturesTests(TestCase):
    def setUp(self):
        self.fixtures_file_name = "test_mock_data"
        fixtures_test_dir_name = "test"
        self.fixtures_test_dir = generate_fixtures.FIXTURES_DIR / fixtures_test_dir_name
        self.fixtures_file_path = self.fixtures_test_dir / f"{self.fixtures_file_name}.json"
        self.fixtures_file_path_for_loaddata = f"{fixtures_test_dir_name}/{self.fixtures_file_name}"

    def tearDown(self):
        # Delete generated fixtures file and directory
        self.fixtures_file_path.unlink()
        self.fixtures_test_dir.rmdir()

    def test_generated_fixtures_load_without_errors(self):
        generate_fixtures.create_fixture_file(self.fixtures_file_path)
        out = StringIO()
        call_command(f"loaddata", self.fixtures_file_path_for_loaddata, stdout=out)
        self.assertTrue(out.getvalue().strip().startswith("Installed"))
"""
