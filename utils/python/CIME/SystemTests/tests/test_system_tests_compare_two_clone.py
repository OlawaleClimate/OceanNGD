#!/usr/bin/env python

"""
This module contains unit tests of the core logic in SystemTestsCompareTwoClone.
"""

import unittest
from CIME.SystemTests.system_tests_compare_two_clone import SystemTestsCompareTwoClone
import CIME.test_status as test_status

import os
import shutil
import tempfile
from copy import deepcopy

# ========================================================================
# Fake version of Case object that provides the functionality needed for these
# tests
#
# TODO(wjs, 2016-08-10) Should this be moved into case.py? (Is it useful enough
# to warrant that?)
# ========================================================================

class CaseFake(object):
    def __init__(self, case_root, create_case_root=True):
        """
        Initialize a new case object for the given case_root directory.

        Args:
            case_root (str): path to CASEROOT
            create_case_root (bool): If True, creates the directory given by case_root
        """
        self.vars = dict()
        if create_case_root:
            os.makedirs(case_root)
        self.set_value('CASEROOT', case_root)
        casename = os.path.basename(case_root)
        self.set_value('CASE', casename)
        self.set_value('CASEBASEID', casename)

    def get_value(self, item):
        """
        Get the value of the given item

        Returns None if item isn't set for this case

        Args:
            item (str): variable of interest
        """
        return self.vars.get(item)

    def set_value(self, item, value):
        """
        Set the value of the given item to the given value

        Args:
            item (str): variable of interest
            value (any type): new value for item
        """
        self.vars[item] = value

    def copy(self, newcasename, newcaseroot):
        """
        Create and return a copy of self, but with CASE and CASEBASEID set to newcasename
        and CASEROOT set to newcaseroot

        Args:
            newcasename (str): new value for CASE
            newcaseroot (str): new value for CASEROOT
        """
        newcase = deepcopy(self)
        newcase.set_value('CASE', newcasename)
        newcase.set_value('CASEBASEID', newcasename)
        newcase.set_value('CASEROOT', newcaseroot)

        return newcase

    def create_clone(self, newcase, keepexe=False):
        """
        Create a clone of the current case. Also creates the CASEROOT directory
        for the clone case (given by newcase).

        Args:
            newcase (str): full path to the new case. This directory should not
                already exist; it will be created
            keepexe (bool, optional): Ignored

        Returns the clone case object
        """
        newcaseroot = os.path.abspath(newcase)
        newcasename = os.path.basename(newcase)
        os.makedirs(newcaseroot)
        clone = self.copy(newcasename = newcasename, newcaseroot = newcaseroot)

        return clone

    def flush(self):
        pass

# ========================================================================
# Tests of CaseFake
# ========================================================================

class TestCaseFake(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_create_clone(self):
        # Setup
        old_caseroot = os.path.join(self.tempdir, 'oldcase')
        oldcase = CaseFake(old_caseroot)
        oldcase.set_value('foo', 'bar')

        # Exercise
        new_caseroot = os.path.join(self.tempdir, 'newcase')
        clone = oldcase.create_clone(new_caseroot)

        # Verify
        self.assertEqual('bar', clone.get_value('foo'))
        self.assertEqual('newcase', clone.get_value('CASE'))
        self.assertEqual('newcase', clone.get_value('CASEBASEID'))
        self.assertEqual(new_caseroot, clone.get_value('CASEROOT'))

# ========================================================================
# Fake version of SystemTestsCompareTwo that overrides some functionality for
# the sake of unit testing
# ========================================================================

class SystemTestsCompareTwoFake(SystemTestsCompareTwoClone):
    def __init__(self,
                 case1,
                 run_two_suffix = 'test',
                 case2setup_raises_exception=False):
        """
        Initialize a SystemTestsCompareTwoFake object

        Args:
            case1 (CaseFake): existing case
            run_two_suffix (str, optional): Suffix used for the second run. Defaults to 'test'.
            case2setup_raises_exception (bool, optional): If True, then the call
                to _case_two_setup will raise an exception. Defaults to False.
        """

        self._case2setup_raises_exception = case2setup_raises_exception

        SystemTestsCompareTwoClone.__init__(
            self,
            case1,
            separate_builds = False,
            run_two_suffix = run_two_suffix)

        # Need to tell test status that case has been built, since this is
        # checked in the run call
        with self._test_status:
            self._test_status.set_status(
                test_status.MODEL_BUILD_PHASE,
                test_status.TEST_PASS_STATUS)

    # ------------------------------------------------------------------------
    # Stubs of methods called by SystemTestsCommon.__init__ that interact with
    # the system or case object in ways we want to avoid here
    # ------------------------------------------------------------------------

    def _init_environment(self, caseroot):
        pass

    def _init_locked_files(self, caseroot, expected):
        pass

    def _init_case_setup(self):
        pass

    # ------------------------------------------------------------------------
    # Fake implementations of methods that are typically provided by
    # SystemTestsCommon
    # ------------------------------------------------------------------------

    def run_indv(self, suffix="base"):
        # FIXME(wjs, 2016-08-10) Introduce ability to raise exception
        pass

    def _component_compare_test(self, suffix1, suffix2):
        # Trying to use the real version of _component_compare_test would pull
        # too much baggage into these tests. Since the return value from this
        # method isn't important, it's sufficient for the tests of this class to
        # just ensure that _component_compare_test was actually called
        # correctly.
        #
        # An alternative would be to extract the main work of
        # _component_compare_test into a different method that returns a True
        # (success) / False (failure) result, with _component_compare_test then
        # updating test_status appropriately. Then we could override that new
        # method in this Fake class, using the true implementation of
        # _component_compare_test. Then the test verification would include
        # verification that TestStatus is set correctly for the COMPARE
        # phase. But that seems more about testing _component_compare_test than
        # testing SystemTestsCompareTwoClone itself, so I don't see much added
        # value of that.

        # FIXME(wjs, 2016-08-10) Record that this wass called
        pass

    def _check_for_memleak(self):
        pass

    # ------------------------------------------------------------------------
    # Fake implementations of methods that are typically provided by
    # SystemTestsCompareTwoClone
    #
    # Since we're overriding these, their functionality is untested!
    # ------------------------------------------------------------------------

    def _case_from_existing_caseroot(self, caseroot):
        """
        Returns a CaseFake object instead of a Case object
        """
        return CaseFake(caseroot, create_case_root=False)

    @staticmethod
    def _link_to_case2_output(casename1, casename2,
                              rundir1, rundir2,
                              run2suffix):
        # FIXME(wjs, 2016-08-10) record that this was called, and its arguments
        pass

    # ------------------------------------------------------------------------
    # Fake implementations of methods that are typically provided by the
    # individual test
    #
    # The values set here are asserted against in some unit tests
    # ------------------------------------------------------------------------

    def _common_setup(self):
        self._case.set_value('var_set_in_common_setup', 'common_val')

    def _case_one_setup(self):
        self._case.set_value('var_set_in_setup', 'case1val')

    def _case_two_setup(self):
        self._case.set_value('var_set_in_setup', 'case2val')
        if self._case2setup_raises_exception:
            raise RuntimeError

# ========================================================================
# Test class itself
# ========================================================================

class TestSystemTestsCompareTwoClone(unittest.TestCase):

    def setUp(self):
        # create a sandbox in which case directories can be created
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_setup(self):
        # Ensure that test setup properly sets up case 1 and case 2

        # Setup
        case1root = os.path.join(self.tempdir, 'case1')
        case1 = CaseFake(case1root)
        case1.set_value('var_preset', 'preset_value')

        # Exercise
        mytest = SystemTestsCompareTwoFake(case1)

        # Verify
        # Make sure that pre-existing values in case1 are copied to case2 (via
        # clone)
        self.assertEqual('preset_value',
                         mytest._case2.get_value('var_preset'))

        # Make sure that _common_setup is called for both
        self.assertEqual('common_val',
                         mytest._case1.get_value('var_set_in_common_setup'))
        self.assertEqual('common_val',
                         mytest._case2.get_value('var_set_in_common_setup'))

        # Make sure that _case_one_setup and _case_two_setup are called
        # appropriately
        self.assertEqual('case1val',
                         mytest._case1.get_value('var_set_in_setup'))
        self.assertEqual('case2val',
                         mytest._case2.get_value('var_set_in_setup'))

    def test_setup_case2_exists(self):
        # If case2 already exists, then setup code should not be called

        # Setup
        case1root = os.path.join(self.tempdir, 'case1')
        case1 = CaseFake(case1root)
        os.makedirs(os.path.join(case1root, 'case1.test'))

        # Exercise
        mytest = SystemTestsCompareTwoFake(case1,
                                           run_two_suffix = 'test')

        # Verify:

        # Make sure that case2 object is set (i.e., that it doesn't remain None)
        self.assertEqual('case1.test', mytest._case2.get_value('CASE'))

        # Variables set in various setup methods should not be set
        # (In the real world - i.e., outside of this unit testing fakery - these
        # values would be set when the Case objects are created.)
        self.assertIsNone(mytest._case1.get_value('var_set_in_common_setup'))
        self.assertIsNone(mytest._case2.get_value('var_set_in_common_setup'))
        self.assertIsNone(mytest._case1.get_value('var_set_in_setup'))
        self.assertIsNone(mytest._case2.get_value('var_set_in_setup'))

    def test_setup_error(self):
        # If there is an error in setup, an exception should be raised and the
        # case2 directory should be removed

        # Setup
        case1root = os.path.join(self.tempdir, 'case1')
        case1 = CaseFake(case1root)

        # Exercise
        with self.assertRaises(Exception):
            mytest = SystemTestsCompareTwoFake(case1,
                                               run_two_suffix = 'test',
                                               case2setup_raises_exception = True)

        # Verify
        self.assertFalse(os.path.exists(os.path.join(case1root, 'case1.test')))

    def test_run_phase_succeeds(self):
        # Make sure the run phase behaves properly when all runs succeed

        # Setup
        case1root = os.path.join(self.tempdir, 'case1')
        case1 = CaseFake(case1root)
        mytest = SystemTestsCompareTwoFake(case1)

        # Exercise
        mytest.run()

        # Verify
        # Verify that run phase didn't raise any exceptions
        self.assertEqual(test_status.TEST_PASS_STATUS,
                         mytest._test_status.get_status(test_status.RUN_PHASE))

        # FIXME(wjs, 2016-08-10) Verify test status

        # FIXME(wjs, 2016-08-10) Verify that link_to_case2_output was called correctly

        # FIXME(wjs, 2016-08-10) Verify that compare was called correctly (test
        # should fail if I change / remove the call to component_compare_test)

    # FIXME(wjs, 2016-08-10) run 1 fails should raise exception (test should
    # fail if I remove call to first run)

    # FIXME(wjs, 2016-08-10) run 2 fails should raise exception (test should
    # fail if I remove activate_case2)
