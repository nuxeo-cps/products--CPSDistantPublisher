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
#
"""
    DistantPublisher can be hooked to a portal to provide
    distant publishing APIs, based on CPSRemoteController
    client.
"""
from xmlrpclib import Fault
import socket
import copy

from OFS.Folder import Folder
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from Products.CMFCore.utils import UniqueObject
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import getToolByName

from DistantPublisherWorkflowHandler import DistantPublisherWorkflowHandler
from Products.CPSRemoteController.utils import marshallDocument

class DistantError(Exception): pass

class DistantPublisher(UniqueObject, Folder):
    """ High level APIs to controll
        a distant server via CPSRemoteController
    """
    id = 'portal_distant_publisher'
    meta_type = 'CPS Distant Publisher Tool'
    security = ClassSecurityInfo()

    _properties = Folder._properties + (
        {'id': 'distant_repository_rpath', 'type': 'string', 'mode': 'w',
         'label': 'Distant target rpath for document creation'},)

    distant_repository_rpath = 'workspaces'

    def _getRemote(self):
        """ returns the remote """
        return getToolByName(self, 'portal_remote_controller_client')

    def _getWFEngine(self):
        """ returns the remote """
        return getToolByName(self, 'portal_workflow')

    security.declareProtected(View, 'getDistantSectionsTree')
    def getDistantSectionsTree(self, server_name, default=[]):
        """ calls the section tree for the distant server_name """
        prmc = self._getRemote()
        try:
            res = prmc.callMethod(server_name, 'getSectionsTree')
            return res
        except (Fault, socket.gaierror, IOError, socket.timeout):
            return []
        except AttributeError, e:
            if str(e) == 'None: no such server':
                return []
            else:
                # returning a copy to avoid default's arbitrary value
                # to get be modified by the caller
                return copy.deepcopy(default)

    def _getDataFromProxy(self, proxy):
        """ returns a dict that can be used for transportation """
        doc = proxy.getContent()
        return proxy.getTypeInfo().getDataModel(ob=doc)

    def  _editDocument(self, distant_server, work_rpath, portal_type, doc_def):
        prmc = self._getRemote()
        try:
            return prmc.callMethod(distant_server, 'editOrCreateDocument',
                                   work_rpath, portal_type, doc_def,
                                   1, "")

        except Fault, e:
            # the creation failed
            msg = '%s: Could not update the document: %s' % (e.faultCode,
                                                            e.faultString)
            raise DistantError(msg)
        except socket.timeout, e:
            raise DistantError(str(e))

    def _createDocument(self, distant_server, portal_type, doc_def,
                        distant_creation_path):
        prmc = self._getRemote()
        try:
            return prmc.callMethod(distant_server, 'createDocument', portal_type,
                                   doc_def, distant_creation_path, 1, "")
        except Fault, e:
            msg = '%s: Could not create the document: %s' % (e.faultCode,
                                                             e.faultString)
            raise DistantError(msg)
        except socket.timeout, e:
            raise DistantError(str(e))

    def _publishDocument(self, distant_server, drpath, rpaths_to_publish,
                         wait_for_approval, comments):
        prmc = self._getRemote()
        try:
            return prmc.callMethod(distant_server, 'publishDocument', drpath,
                                   rpaths_to_publish, wait_for_approval,
                                   comments)
        except Fault, e:
            msg = '%s: Could not create the document: %s' % (e.faultCode,
                                                             e.faultString)
            raise DistantError(msg)
        except socket.timeout, e:
            raise DistantError(str(e))

    security.declareProtected(View, 'distantPublication')
    def distantPublication(self, proxy, distant_server, distant_creation_path,
                           distant_publishing_path, wait_for_approval=False,
                           comments=''):
        """ publishes document """
        # doc_def is a UserDict, we need
        # to send a pure dict to avoid mashalling errors
        doc_def = self._getDataFromProxy(proxy).data
        doc_def = marshallDocument(doc_def)

        portal_type = proxy.portal_type
        prmc = self._getRemote()

        # let's try to find if a document is already published
        # on the server
        distant_infos = self.getDistantPublishStatus(distant_server, proxy)
        distant_rpaths = [info['distant_rpath'] for info in distant_infos
                          if info['distant_server'] == distant_server and
                          info['review_state'] != 'unknown_distant_state']

        creation = True

        if distant_rpaths != []:
            for distant_rpath in distant_rpaths:
                if distant_rpath.startswith(distant_publishing_path):
                    creation = False
                    break

        # first create the document on the server
        if creation:
            distant_rpath = self._createDocument(distant_server, portal_type,
                                                 doc_def,
                                                 distant_creation_path)
        else:
            # getting the work document
            try:
                work_rpath = prmc.callMethod(distant_server, 'getOriginalDocument',
                                             distant_rpath)
            except Fault, e:
                # creating then
                work_rpath = []

            if work_rpath != []:
                work_rpath = work_rpath[0]
                distant_rpath = self._editDocument(distant_server, work_rpath,
                                                   portal_type, doc_def)
            else:
                # creating then
                distant_rpath = self._createDocument(distant_server, portal_type,
                                                     doc_def, distant_creation_path)

        # then publish it
        rpaths_to_publish = {distant_publishing_path: 'replace'}

        if not wait_for_approval:
            try:
                published_doc_id = self._publishDocument(distant_server,
                                                         distant_rpath,
                                                         rpaths_to_publish,
                                                         False, comments)
            except DistantError:
                # the rights might have changed
                # we'll try a submission
                wait_for_approval = True

        if wait_for_approval:
            published_doc_id = self._publishDocument(distant_server,
                                                     distant_rpath,
                                                     rpaths_to_publish, True,
                                                     comments)

        # always returns one element list, since we publish elements
        # one by one
        return published_doc_id[0]

    security.declareProtected(View, 'distantUnpublication')
    def distantUnpublication(self, distant_server, distant_published_rpath):
        """ this method tries to unpublish a document from a broad server """
        prmc = self._getRemote()
        try:
            prmc.callMethod(distant_server, 'unpublishDocument',
                            distant_published_rpath)
            return True
        except (Fault, socket.timeout):
            # failed...
            return False

    security.declareProtected(View, 'distantRemoval')
    def distantRemoval(self, distant_server, distant_published_rpath):
        """ this method tries to unpublish a document from a broad server """
        prmc = self._getRemote()
        try:
            prmc.callMethod(distant_server, 'deleteDocument',
                            distant_published_rpath)
            return True
        except (Fault, socket.timeout):
            # failed...
            return False

    security.declareProtected(View, 'distantWorkflowTransition')
    def distantWorkflowTransition(self, ob, workflow_action, REQUEST=None, **kw):
        """ delegates the transition handling to specialized subclass """
        dr_rpath = self.distant_repository_rpath
        transition_handler = DistantPublisherWorkflowHandler(dr_rpath)
        transition_handler(ob, workflow_action, REQUEST, **kw)

    security.declareProtected(View, 'isMemberReviewer')
    def isMemberReviewer(self, object, member_id=None, roles=()):
        dr_rpath = self.distant_repository_rpath
        transition_handler = DistantPublisherWorkflowHandler(dr_rpath)
        if transition_handler is None:
            return False
        return transition_handler.isMemberReviewer(object, member_id, roles)

    security.declareProtected(View, 'canPublish')
    def canPublish(self, object, roles=()):
        dr_rpath = self.distant_repository_rpath
        transition_handler = DistantPublisherWorkflowHandler(dr_rpath)
        if transition_handler is None:
            return False
        return transition_handler.canPublish(object, roles)

    security.declarePrivate('getDistantDocumentHistory')
    def getDistantDocumentHistory(self, distant_server, distant_rpath):
        """ this is for info purpose, if not retrievable,
        display an unknown state"""
        prmc = self._getRemote()
        try:
            return prmc.callMethod(distant_server, 'getDocumentHistory',
                                   distant_rpath)
        except (Fault, socket.timeout):
            return 'unknown_distant_state'

    security.declareProtected(View, 'getDistantPublishState')
    def getDistantPublishStatus(self, distant_server, ob):
        """ this method browses the document's history
        to get a list of published document"""
        def _computeKey(portal, container):
            return '%s:%s' % (portal, container)

        history = self._getWFEngine().getFullHistoryOf(ob)
        distant_published = {}

        # entries are sorted from the oldest to the newest
        for entry in history:
            action = entry.get('action', '')
            if action not in ('distant_publishing', 'distant_unpublish'):
                continue

            distant_portal = entry.get('distant_portal', '')
            distant_published_rpaths = entry.get('distant_published_rpaths', '')

            if distant_portal == '' or distant_published_rpaths == []:
                continue

            for distant_published_rpath in distant_published_rpaths:
                # key is the coordinate of distant publication
                key = _computeKey(distant_portal, distant_published_rpath)

                if action == 'distant_publishing':
                    # we keep the lastest publication
                    # in case of multiple publication
                    distant_published[key] = entry
                else:
                    # unpublished, let's remove it from the list
                    if key in distant_published:
                        del distant_published[key]

        # distant_published now contains the list of published
        # elements. Let's render a status table
        states = []
        for entry in distant_published:
            entry_rpath = entry.split(':')[-1]
            distant_history = self.getDistantDocumentHistory(distant_server,
                                                             entry_rpath)
            if distant_history == 'unknown_distant_state':
                continue    # we don't want to see those

            distant_history = [entry_h for entry_h in distant_history
                               if entry_h['review_state'] in ('published', 'pending')]

            if len(distant_history) == 0:
                continue

            distant_history = distant_history[0]
            state = {}
            state['location'] = entry
            state['rpath'] = entry      # voir si pas rpath
            state['title'] = ob.Title()
            state['time_str'] = distant_history['time_str']
            language_revs = distant_history['language_revs']
            state['rev'] = str(language_revs.values()[0])
            state['review_state'] = distant_history['review_state']
            state['lang'] = language_revs.keys()[0]
            state['language'] = state['lang']
            state['distant_server'] = distant_server
            state['distant_rpath'] = entry_rpath
            states.append(state)

        return states

InitializeClass(DistantPublisher)

