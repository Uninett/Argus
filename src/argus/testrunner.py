"""Integration to use Pytest as Django TEST_RUNNER.

Wholly copied from https://pytest-django.readthedocs.io/en/latest/faq.html - so
we'll assume this is licensed like pytest-django itself: BSD (3-clause)
license.

"""


class PytestTestRunner:
    """Runs pytest to discover and run tests."""

    def __init__(self, verbosity=1, failfast=False, keepdb=False, junitxml=None, **kwargs):
        self.verbosity = verbosity
        self.failfast = failfast
        self.keepdb = keepdb
        self.junitxml = junitxml

    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument("--keepdb", action="store_true", help="Preserves the test DB between runs.")
        parser.add_argument("--junitxml", metavar="PATH", help="Produce a JUnit XML test report.")

    def run_tests(self, test_labels):
        """Run pytest and return the exitcode.

        It translates some of Django's test command option to pytest's.
        """
        import pytest

        argv = []
        if self.verbosity == 0:
            argv.append("--quiet")
        if self.verbosity == 2:
            argv.append("--verbose")
        if self.verbosity == 3:
            argv.append("-vv")
        if self.failfast:
            argv.append("--exitfirst")
        if self.keepdb:
            argv.append("--reuse-db")
        if self.junitxml:
            argv.append("--junitxml={}".format(self.junitxml))

        argv.extend(test_labels)
        return pytest.main(argv)
