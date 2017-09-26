from unittest import TestCase

import os

from gunbot_config_updater.check_webpage_updated import WebPageMonitor


MONITOR_FILE = '.webPageMonitorHashed'


def remove_file(path):
    if os.path.isfile(path):
        os.remove(path)


class TestWebPageMonitor(TestCase):

    URL_LAST_MODIFIED = 'https://stackoverflow.com/questions/20171392/python-pprint-dictionary-on-multiple-lines'
    URL_HASH = 'https://pastebin.com/raw/ci8ar4sw'

    def setUp(self):
        remove_file(WebPageMonitor.MONITOR_FILE)
        remove_file(MONITOR_FILE)

    def tearDown(self):
        remove_file(WebPageMonitor.MONITOR_FILE)
        remove_file(MONITOR_FILE)

    def test_check_last_modified(self):
        monitor = WebPageMonitor(self.URL_LAST_MODIFIED)
        monitor.check()
        self.assertTrue(monitor.url_changed)
        monitor.check()
        self.assertFalse(monitor.url_changed)

    def test_check_hash(self):
        monitor = WebPageMonitor(self.URL_HASH, monitor_file=MONITOR_FILE, force_use_hash=True)
        monitor.check()
        self.assertTrue(monitor.url_changed)
        monitor.check()
        self.assertFalse(monitor.url_changed)

    def test_check_no_last_modified(self):
        monitor = WebPageMonitor(self.URL_HASH, monitor_file=MONITOR_FILE)
        with self.assertRaises(KeyError) as context:
            monitor.check()
            self.assertTrue('Error: header' in context.exception)

    def test_auto_hash_switch(self):
        monitor = WebPageMonitor(self.URL_HASH, auto_switch_hash=True)
        monitor.check()
        self.assertTrue(monitor.url_changed)
        monitor.check()
        self.assertFalse(monitor.url_changed)
