#!/usr/bin/python
# Copyright (c) 2006 Nuxeo SARL <http://nuxeo.com>
# Author : Tarek Ziade <tz@nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
# $Id$
import doctest
import os, sys
import os.path
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest
from Testing import ZopeTestCase
import DistantPublisherTestCase
from Products.CPSDefault.tests.CPSTestCase import MANAGER_ID

from Products.CPSDistantPublisher.PartialPublisherStack import \
    PartialPublisherSimpleStack
from Products.CPSDistantPublisher.PartialPublisherStackElement import \
    PartialPublisherStackElement

class FakeWF:
    pass

class FakeMemberTool:
    def getMemberById(self, id):
        return None

class PPSTestCase(DistantPublisherTestCase.DistantPublisherTestCase):

    wftool = FakeWF()
    mtool = FakeMemberTool()

    def afterSetUp(self):
        self.login_id = MANAGER_ID
        self.login(self.login_id)
        self.portal.REQUEST.SESSION = {}
        self.portal.REQUEST['AUTHENTICATED_USER'] = self.login_id

        from Products.ExternalMethod.ExternalMethod import ExternalMethod
        installer = ExternalMethod('installCPSDistantPublisher', '',
                                   'CPSDistantPublisher.install', 'install')
        self.portal._setObject('installCPSDistantPublisher', installer)
        self.assert_('installCPSDistantPublisher' in self.portal.objectIds())
        self.portal.installCPSDistantPublisher()
        self.tool = self.portal.portal_remote_controller

    def beforeTearDown(self):
        self.logout()

    def test_basic(self):
        stack = PartialPublisherSimpleStack()
        self.assertNotEquals(stack, None)

    def test_containsMember(self):
        stack = PartialPublisherSimpleStack()
        self.assertEquals(stack.containsMember(self.wftool, self.mtool,
                                               member_id='toto'), False)

        stack_element = PartialPublisherStackElement('partial_publisher:toto')
        stack.push(stack_element)
        self.assertEquals(stack.containsMember(self.wftool, self.mtool,
                                               member_id='toto'), True)

    def test_hasValidated(self):
        stack = PartialPublisherSimpleStack()
        stack_element = PartialPublisherStackElement('partial_publisher:toto')
        stack.push(stack_element)
        self.assertEquals(stack.hasValidated(self.wftool, self.mtool,
                                             member_id='toto'), False)
        stack_element.acknowledgment = 1
        self.assertEquals(stack.hasValidated(self.wftool, self.mtool,
                                             member_id='toto'), True)

    def test_allValidated(self):
        stack = PartialPublisherSimpleStack()
        stack_element = PartialPublisherStackElement('partial_publisher:toto')
        stack.push(stack_element)
        stack_element2 = PartialPublisherStackElement('partial_publisher:toto2')
        stack.push(stack_element2)
        self.assertEquals(stack.allValidated(self.wftool, self.mtool), False)
        stack_element.acknowledgment = 1
        self.assertEquals(stack.allValidated(self.wftool, self.mtool), False)
        stack_element2.acknowledgment = 1
        self.assertEquals(stack.allValidated(self.wftool, self.mtool), True)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PPSTestCase))
    suite.addTest(doctest.DocTestSuite('Products.CPSDistantPublisher.PartialPublisherStack'))
    return suite

if __name__ == '__main__':
    framework(descriptions=1, verbosity=2)
