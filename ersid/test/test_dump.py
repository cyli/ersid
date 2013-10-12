"""
Unit tests for dump.py
"""
import os

from twisted.trial import unittest
from twisted.internet import defer, task

from ersid import dump


class TestBackup(unittest.TestCase):
    """
    Tests the backup function.  Make sure to check out _trial_temp/test.log
    to see the log messages printed out.
    """

    def setUp(self):
        """
        Example of stubbing - create an object that returns a deferred that
        fires right away, so that this test does not need to do any
        asynchronous waiting.
        """
        class Storage(object):
            def getAll(self):
                return defer.succeed({'key': 'value'})

        class Service(object):
            storage = Storage()

        self.service = Service()

    def test_backup_writes_file(self):
        """
        Backup writes successfully to a file
        """
        filename = self.mktemp()
        d = dump.backup(self.service, filename)
        r = self.successResultOf(d)
        self.assertEqual(r, None)
        with open(filename) as f:
            self.assertEqual('{"key": "value"}', f.read())

    def test_backup_still_succeeds_if_write_fails(self):
        """
        Backup does not raise an exception if the write fails.
        """
        # you can't write to a directory
        filename = self.mktemp()
        os.mkdir(filename)
        d = dump.backup(self.service, filename)
        r = self.successResultOf(d)
        self.assertEqual(r, None)
        self.assertTrue(os.path.isdir(filename))


class TestStartLoop(unittest.TestCase):
    """
    Tests the startLoop function.  Demonstrats replacing the clock so that
    testing timing things doesn't actually take real time.
    """
    def setUp(self):
        """
        Set up a twisted.internet.task.Clock to take the place of the reactor,
        which is used for timing.  Also stub out the backup function to not
        actually write to a file, and make LoopingCall use the fake clock.

        Demonstrates use of trial's 'patch' method.
        """
        self.clock = task.Clock()
        self.backup_calls = []

        def backup(*args):
            self.backup_calls.append(args)

        self.patch(dump, 'backup', backup)

        def looping_call(f, *args, **kwargs):
            lc = task.LoopingCall(f, *args, **kwargs)
            lc.clock = self.clock
            return lc

        self.patch(dump, 'LoopingCall', looping_call)

    def test_startLoop_calls_backup_right_away_and_at_every_interval(self):
        """
        Backup is called as soon as startLoop is called
        """
        dump.startLoop(5, "service", "filename")
        self.assertEqual(self.backup_calls, [("service", "filename")])
        self.clock.advance(5)
        self.assertEqual(self.backup_calls, [("service", "filename")] * 2)
        self.clock.advance(5)
        self.assertEqual(self.backup_calls, [("service", "filename")] * 3)
