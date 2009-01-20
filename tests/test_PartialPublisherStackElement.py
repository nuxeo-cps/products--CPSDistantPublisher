#!/usr/bin/python
# (C) Copyright 2005-2009 Nuxeo SA <http://nuxeo.com>
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

from Products.CPSDistantPublisher.PartialPublisherStackElement import \
    PartialPublisherStackElement

class PPSTestCase(DistantPublisherTestCase.DistantPublisherTestCase):

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
        stack_element = PartialPublisherStackElement('id')
        self.assertEquals(stack_element()['id'], 'id')
        self.assertEquals(stack_element()['acknowledgment'], 0)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PPSTestCase))
    suite.addTest(doctest.DocTestSuite('Products.CPSDistantPublisher.PartialPublisherStackElement'))
    return suite

if __name__ == '__main__':
    framework(descriptions=1, verbosity=2)
