#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2013 Edgewall Software
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.

import os
import re

from datetime import datetime, timedelta

from trac.admin.tests.functional import AuthorizationTestCaseSetup
from trac.test import locale_en
from trac.tests.functional import *
from trac.util.datefmt import utc, localtz, format_date, format_datetime, \
                              pretty_timedelta
from trac.util.text import to_utf8

class MaySetOwnerOperationDefault(FunctionalTwillTestCaseSetup):
    def runTest(self):
        """Test for may_set_owner operation introduced in http://trac.edgewall.org/ticket/10018

        When using the workflow operation `may_set_owner`, the assign-to field
        will default to the ticket's current owner.
        """
        env = self._testenv.get_trac_environment()
        env.config.set('ticket-workflow', 'reassign.operations',
                       'may_set_owner')
        restrict_owner = env.config.get("ticket", "restrict_owner")
        env.config.set("ticket", "restrict_owner", "false")
        env.config.save()

        try:
            self._testenv.restart()

            ticket_id = self._tester.create_ticket("MaySetOwnerOperationDefault", 
                                                   info={'owner': "lammy"})
            self._tester.go_to_ticket(ticket_id)
            tc.find("The owner will be changed from lammy")
            tc.find('<input type="text" name="action_reassign_reassign_owner" value="lammy" id="action_reassign_reassign_owner" />')
        finally:
            # Undo the config change to avoid causing problems for later
            # tests.
            env.config.set('ticket-workflow', 'resolve.operations',
                           'set_resolution')
            env.config.set("ticket", "restrict_owner", restrict_owner)
            env.config.save()
            self._testenv.restart()


class MaySetOwnerOperationDefaultNoOwner(FunctionalTwillTestCaseSetup):
    def runTest(self):
        """Test for may_set_owner operation introduced in http://trac.edgewall.org/ticket/10018

        When using the workflow operation `may_set_owner` with restrict_owner=false,
        the assign-to field will default to a blank field if the ticket currently has no owner.
        """
        env = self._testenv.get_trac_environment()
        env.config.set('ticket-workflow', 'reassign.operations',
                       'may_set_owner')
        restrict_owner = env.config.get("ticket", "restrict_owner")
        env.config.set("ticket", "restrict_owner", "false")
        env.config.save()

        try:
            self._testenv.restart()

            ticket_id = self._tester.create_ticket("MaySetOwnerOperationDefault", 
                                                   info={'owner': ""}
                                                   )
            self._tester.go_to_ticket(ticket_id)
            tc.find("The ticket will remain with no owner.")
            tc.find("The owner will be changed from \(none\)")
            tc.find('<input type="text" name="action_reassign_reassign_owner" id="action_reassign_reassign_owner" />')
        finally:
            # Undo the config change to avoid causing problems for later
            # tests.
            env.config.set('ticket-workflow', 'resolve.operations',
                           'set_resolution')
            env.config.set("ticket", "restrict_owner", restrict_owner)
            env.config.save()
            self._testenv.restart()


class MaySetOwnerOperationDefaultRestrictOwnerNoOwner(FunctionalTwillTestCaseSetup):
    def runTest(self):
        """Test for may_set_owner operation introduced in http://trac.edgewall.org/ticket/10018

        When using the workflow operation `may_set_owner` with restrict_owner=true,
        the assign-to field will default to an empty option labelled (none) if the ticket 
        currently has no owner.
        """
        env = self._testenv.get_trac_environment()
        env.config.set('ticket-workflow', 'reassign.operations',
                       'may_set_owner')
        env.config.save()

        try:
            self._testenv.restart()

            ticket_id = self._tester.create_ticket("MaySetOwnerOperationDefault", 
                                                   info={'owner': ""}
                                                   )
            restrict_owner = env.config.get("ticket", "restrict_owner")
            env.config.set("ticket", "restrict_owner", "true")
            env.config.save()

            self._tester.go_to_ticket(ticket_id)
            tc.find("The ticket will remain with no owner.")
            tc.find("The owner will be changed from \(none\)")
            tc.find('<option selected="selected" value="">\(none\)</option>')
        finally:
            # Undo the config change to avoid causing problems for later
            # tests.
            env.config.set('ticket-workflow', 'resolve.operations',
                           'set_resolution')
            env.config.set("ticket", "restrict_owner", restrict_owner)
            env.config.save()
            self._testenv.restart()


class MaySetOwnerOperationDefaultRestrictOwnerAnonymous(FunctionalTwillTestCaseSetup):
    def runTest(self):
        """When using the workflow operation `may_set_owner` with restrict_owner=true,
        the assign-to dropdown menu will contain a selected option "anonymous" if the
        ticket is owned by "anonymous"."""
        env = self._testenv.get_trac_environment()
        env.config.set('ticket-workflow', 'reassign.operations',
                       'may_set_owner')
        restrict_owner = env.config.get("ticket", "restrict_owner")
        env.config.set("ticket", "restrict_owner", "false")
        env.config.save()

        try:
            self._testenv.restart()

            ticket_id = self._tester.create_ticket("MaySetOwnerOperationDefaultRestrictOwnerAnonymous",
                                                   info={'owner': "anonymous"})
            env.config.set("ticket", "restrict_owner", "true")
            env.config.save()
            self._tester.logout()

            from trac.perm import PermissionSystem
            PermissionSystem(env).grant_permission('anonymous', 'TICKET_ADMIN')
            
            self._testenv.restart()

            self._tester.go_to_ticket(ticket_id)
            tc.find("The owner will be changed from anonymous")
            tc.find('<option selected="selected" value="anonymous">anonymous</option>')

        finally:
            # Undo the config change to avoid causing problems for later
            # tests.
            env.config.set('ticket-workflow', 'resolve.operations',
                           'set_resolution')
            env.config.set("ticket", "restrict_owner", restrict_owner)
            env.config.save()

            from trac.perm import PermissionSystem
            PermissionSystem(env).revoke_permission('anonymous', 'TICKET_ADMIN')

            self._tester.login("admin")
            self._testenv.restart()


class SetOwnerOperationDefault(FunctionalTwillTestCaseSetup):
    def runTest(self):
        """When using the workflow operation `set_owner`, the assign-to field
        will default to the currently requesting username."""

        env = self._testenv.get_trac_environment()
        env.config.set('ticket-workflow', 'reassign.operations',
                       'set_owner')
        restrict_owner = env.config.get("ticket", "restrict_owner")
        env.config.set("ticket", "restrict_owner", "false")
        env.config.save()

        try:
            self._testenv.restart()

            ticket_id = self._tester.create_ticket("SetOwnerOperationDefault", 
                                                   info={'owner': "lammy"})
            self._tester.go_to_ticket(ticket_id)
            tc.find("The owner will be changed from lammy")
            # The logged-in user is "admin", and the set_owner operation will default
            # to changing the owner to the logged-in user
            tc.find('<input type="text" name="action_reassign_reassign_owner" value="admin" id="action_reassign_reassign_owner" />')
        finally:
            # Undo the config change to avoid causing problems for later
            # tests.
            env.config.set('ticket-workflow', 'resolve.operations',
                           'set_resolution')
            env.config.set("ticket", "restrict_owner", restrict_owner)
            env.config.save()
            self._testenv.restart()


class SetOwnerOperationDefaultRestrictOwnerNotKnownUser(FunctionalTwillTestCaseSetup):
    def runTest(self):
        """When using the workflow operation `set_owner` with restrict_owner=true,
        the assign-to dropdown menu will not contain the requesting user, if the
        requesting user is not a known user."""
        env = self._testenv.get_trac_environment()
        env.config.set('ticket-workflow', 'reassign.operations',
                       'set_owner')
        restrict_owner = env.config.get("ticket", "restrict_owner")
        env.config.set("ticket", "restrict_owner", "false")
        env.config.save()

        try:
            self._testenv.restart()

            ticket_id = self._tester.create_ticket("SetOwnerOperationDefaultRestrictOwnerAnonymous",
                                                   info={'owner': "lammy"})
            env.config.set("ticket", "restrict_owner", "true")
            env.config.save()
            self._tester.logout()

            from trac.perm import PermissionSystem
            PermissionSystem(env).grant_permission('anonymous', 'TICKET_ADMIN')
            
            self._testenv.restart()

            self._tester.go_to_ticket(ticket_id)
            tc.find("The owner will be changed from lammy")
            tc.notfind('<option selected="selected" value="anonymous">anonymous</option>')

        finally:
            # Undo the config change to avoid causing problems for later
            # tests.
            env.config.set('ticket-workflow', 'resolve.operations',
                           'set_resolution')
            env.config.set("ticket", "restrict_owner", restrict_owner)
            env.config.save()

            from trac.perm import PermissionSystem
            PermissionSystem(env).revoke_permission('anonymous', 'TICKET_ADMIN')

            self._tester.login("admin")
            self._testenv.restart()


class MaySetOwnerOperationDefaultRestrictOwner(FunctionalTwillTestCaseSetup):
    def runTest(self):
        """When using the workflow operation `may_set_owner` with restrict_owner=true,
        the assign-to field will default to the ticket's current owner, even if the
        current owner is not otherwise known to the Trac environment."""
        env = self._testenv.get_trac_environment()
        env.config.set('ticket-workflow', 'reassign.operations',
                       'may_set_owner')
        restrict_owner = env.config.get("ticket", "restrict_owner")
        env.config.set("ticket", "restrict_owner", "false")
        env.config.save()

        try:
            self._testenv.restart()

            ticket_id = self._tester.create_ticket("MaySetOwnerOperationDefaultRestrictOwner",
                                                   info={'owner': "lammy"})
            env.config.set("ticket", "restrict_owner", "true")
            env.config.save()
            self._tester.go_to_ticket(ticket_id)
            tc.find("The owner will be changed from lammy")
            tc.find('<option selected="selected" value="lammy">lammy</option>')

            known_usernames = [i[0] for i in env.get_known_users()]
            assert "lammy" not in known_usernames

        finally:
            # Undo the config change to avoid causing problems for later
            # tests.
            env.config.set('ticket-workflow', 'resolve.operations',
                           'set_resolution')
            env.config.set("ticket", "restrict_owner", restrict_owner)
            env.config.save()
            self._testenv.restart()


def functionalSuite(suite=None):
    if not suite:
        import trac.tests.functional
        suite = trac.tests.functional.functionalSuite()

    suite.addTest(SetOwnerOperationDefault())
    suite.addTest(SetOwnerOperationDefaultRestrictOwnerNotKnownUser())

    suite.addTest(MaySetOwnerOperationDefault())
    suite.addTest(MaySetOwnerOperationDefaultRestrictOwner())
    suite.addTest(MaySetOwnerOperationDefaultNoOwner())
    suite.addTest(MaySetOwnerOperationDefaultRestrictOwnerNoOwner())
    suite.addTest(MaySetOwnerOperationDefaultRestrictOwnerAnonymous())

    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='functionalSuite')
