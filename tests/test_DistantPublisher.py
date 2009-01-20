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

# XXX: need to create a Fake RPC server in order to test
# APIS calls

import doctest
import os, sys
import os.path

import unittest
from Testing import ZopeTestCase
import DistantPublisherTestCase
from Products.CPSDefault.tests.CPSTestCase import MANAGER_ID

from Products.CPSDistantPublisher.DistantPublisher import \
    DistantPublisher

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

class DistantPublisherTestCase(DistantPublisherTestCase.DistantPublisherTestCase):

    def afterSetUp(self):
        self.login_id = MANAGER_ID
        self.login(self.login_id)
        self._installPublisher()
        self.tool = self.portal.portal_remote_controller
        self.ws = self.portal.workspaces
        self.publisher = self.portal.portal_distant_publisher
        self.wftool = self.portal.portal_workflow
        self._distantReviewingFixture()

    def beforeTearDown(self):
        self.logout()

    def _installPublisher(self):
        self.portal.REQUEST.SESSION = {}
        self.portal.REQUEST['AUTHENTICATED_USER'] = self.login_id

        from Products.ExternalMethod.ExternalMethod import ExternalMethod
        installer = ExternalMethod('installCPSDistantPublisher', '',
                                   'CPSDistantPublisher.install', 'install')
        self.portal._setObject('installCPSDistantPublisher', installer)
        self.assert_('installCPSDistantPublisher' in self.portal.objectIds())
        self.portal.installCPSDistantPublisher()

    def test_basic(self):
        publisher = DistantPublisher('id')
        self.assertNotEquals(publisher, None)

    def _distantReviewingFixture(self):
        """ prepare all needed to test distant publication """
        # create users
        members = self.portal.portal_directories.members
        members.createEntry({'id': 'publisher', 'roles': ['Member']})
        members.createEntry({'id': 'reviewer1', 'roles': ['Member']})
        members.createEntry({'id': 'reviewer2', 'roles': ['Member']})
        members.createEntry({'id': 'reviewer3', 'roles': ['Member', 'Manager']})

        # create a ws with the users as members
        self.portal_membership = self.portal.portal_membership
        self.portal.portal_membership.createMemberArea('publisher')
        self.publisher_area = self.portal.workspaces.members.publisher

    def _distantPublish(self, document_type, document_id, owner, REQUEST=None,
                        push_ids=['publisher', 'reviewer1', 'reviewer2']):

        self.publisher_area.invokeFactory(document_type, document_id)
        object = self.publisher_area.my_news
        self.assertEquals(self.wftool.getInfoFor(object, 'review_state', None),
                         'work')
        kw = {}
        kw['push_ids'] = push_ids
        kw['distant_submit'] = 'sections'
        kw['dest_container'] = 'workspaces/members/publisher'
        kw['initial_transition'] = 'distant_submit'

        self.login(owner)
        self.publisher.distantWorkflowTransition(object, 'copy_distant_submit',
                                                 REQUEST=REQUEST, **kw)

    def test_isMemberReviewer(self):
        REQUEST = FakeRequest()

        # let's prepare a document to distant-publish
        self._distantPublish('News Item', 'my_news', 'publisher', REQUEST)
        self.assertNotEquals(REQUEST.getRedirect().find('psm_status_changed'), -1)

        # let's check who need to review it
        object = self.portal.workspaces.members.publisher.my_news_1

        self.assert_(not self.publisher.isMemberReviewer(object, 'john'))
        self.assert_(self.publisher.isMemberReviewer(object))
        self.assert_(self.publisher.isMemberReviewer(object, 'publisher'))
        self.assert_(self.publisher.isMemberReviewer(object, 'reviewer1'))
        self.assert_(self.publisher.isMemberReviewer(object, 'reviewer2'))
        self.assert_(self.publisher.isMemberReviewer(object, 'reviewer3',
                                                     ('Manager',)))

        # let's accept it
        kw = {}
        self.publisher.distantWorkflowTransition(object, 'distant_accept',
                                                 REQUEST=REQUEST, **kw)

        self.assert_(self.publisher.isMemberReviewer(object, 'reviewer3',
                                                     ('Manager',)))

    def test_doublons(self):
        def searchEntries(*args, **kw):
            return [('toto', ['toto']),
                    ('toto', ['toto'])]

        def getLocalRoles(*args, **kw):
            return ('Owner',)

        mdir = self.portal.portal_directories.members
        mdir.searchEntries = searchEntries
        self.portal.getLocalRoles = getLocalRoles

        res = self.portal.stack_localrole_search(current_var_id='',
                                                 search_param='fullname')
        self.assertEquals(res, [(False, 'toto', ['toto'])])

    def test_persistence(self):
        def searchEntries(*args, **kw):
            return [('toto', ['toto']),
                    ('toto', ['toto'])]

        def getLocalRoles(*args, **kw):
            return ('Owner',)

        mdir = self.portal.portal_directories.members
        mdir.searchEntries = searchEntries
        self.portal.getLocalRoles = getLocalRoles

        res = self.portal.stack_localrole_search(current_var_id='',
                                                 search_param='fullname',
                                                 push_ids=['distant:titi'])
        self.assertEquals(res, [(False, 'toto', ['toto'])])


    def test_exceptsearch(self):
        def searchEntries(*args, **kw):
            return [('toto', ['toto']),
                    ('toto', ['toto'])]

        def getLocalRoles(*args, **kw):
            return ('Owner',)

        mdir = self.portal.portal_directories.members
        mdir.searchEntries = searchEntries
        self.portal.getLocalRoles = getLocalRoles
        meth = self.portal.stack_localrole_search
        from AccessControl import Unauthorized

        self.assertRaises(Unauthorized, meth, current_var_id='',
                          search_term='*', REQUEST=FakeRequest())

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DistantPublisherTestCase))
    #suite.addTest(doctest.DocTestSuite('Products.CPSDistantPublisher.DistantPublisher'))
    return suite

