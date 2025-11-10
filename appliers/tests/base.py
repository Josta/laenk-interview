"""
Base test case with logging disabled.
"""
import logging
from django.test import TestCase


class NoLoggingTestCase(TestCase):
    """
    TestCase that disables logging to reduce test output noise.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Disable logging for tests
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Re-enable logging after tests
        logging.disable(logging.NOTSET)
