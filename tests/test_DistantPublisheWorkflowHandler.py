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

import unittest
from Testing import ZopeTestCase
import DistantPublisherTestCase
from OFS.SimpleItem import SimpleItem
from Products.CPSDefault.tests.CPSTestCase import MANAGER_ID

from Products.CPSDistantPublisher.DistantPublisher import \
    DistantPublisherWorkflowHandler

class Redirector(object):
    def __init__(self):
        self.url = None

    def redirect(self, url):
        self.url = url

class FakeRequest(object):
    RESPONSE = Redirector()
    form = {}
    def getRedirect(self):
        return self.RESPONSE.url

class FakePublishable(SimpleItem):
    pass

class FakeWorkflowTool(SimpleItem):
    pass

class DistantPublisherTestCase(DistantPublisherTestCase.DistantPublisherTestCase):

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
        #self.portal._setObject('portal_workflow', FakeWorkflowTool())

    def beforeTearDown(self):
        self.logout()

    def _addPortalObject(self, id):
        object = FakePublishable(id)
        self.portal._setObject(id, object)
        return getattr(self.portal, id)

    def test_copy_distant_submit_checks(self):
        # let's check that the distant submission is not done
        # if some parameters are missing
        self.assert_('portal_workflow' in self.portal.objectIds())

        object = self._addPortalObject('object')

        REQUEST = FakeRequest()
        params = {}
        wf_publisher = DistantPublisherWorkflowHandler()

        # no params at all
        wf_publisher(object, 'copy_distant_submit', REQUEST, **params)
        self.assert_(REQUEST.getRedirect().find(('portal_status_message='
                                                 'psm_miss_distant_section')))
        # let's add a section
        params['distant_submit'] = 'yes!'
        wf_publisher(object, 'copy_distant_submit', REQUEST, **params)
        self.assert_(REQUEST.getRedirect().find(('portal_status_message='
                                                 'psm_miss_push_ids')))

        # let's add two guys
        params['push_ids'] = ['me','him']

        from Products.CMFCore.WorkflowCore import WorkflowException
        self.assertRaises(WorkflowException, wf_publisher, object,
                         'copy_distant_submit', REQUEST, **params)

        # let's remove sections
        del params['distant_submit']
        wf_publisher(object, 'copy_distant_submit', REQUEST, **params)
        self.assert_(REQUEST.getRedirect().find(('portal_status_message='
                                                 'psm_miss_push_ids')))

    def test_distant_reject_redirection(self):
        # making sure we redirect to the parent
        object = self._addPortalObject('object2')
        wf_publisher = DistantPublisherWorkflowHandler()
        ob = wf_publisher._redirectObject(object, 'distant_reject')
        self.assertEquals(ob, self.portal)

    def test_comment(self):
        class FakeWF:
          def doActionFor(self, object, action, **kw):
            self.kw = kw

        old = self.portal.portal_workflow
        self.portal.portal_workflow = FakeWF()
        try:
            object = self._addPortalObject('object2')
            wf_publisher = DistantPublisherWorkflowHandler()
            wf_publisher._doActionFor(object, 'toto', **{'comment': 'toto'})
            self.assertEquals(self.portal.portal_workflow.kw['comments'], 'toto')
        finally:
            self.portal.portal_workflow = old

    def test_canPublish(self):
        my_ob = self._addPortalObject('my_ob')
        wf_publisher = DistantPublisherWorkflowHandler()
        result = wf_publisher.canPublish(my_ob, ('Manager',))
        self.assertEquals(result, False)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DistantPublisherTestCase))
    #suite.addTest(doctest.DocTestSuite('Products.CPSDistantPublisher.DistantPublisher'))
    return suite

