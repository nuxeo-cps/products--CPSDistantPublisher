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
""" DistantPublisherWorkflowHandler is instanciated
    when a transition is triggered
"""
from urllib import urlencode
from Products.CMFCore.utils import getToolByName

class DistantPublisherWorkflowHandler:
    """ gathers all workflow operations in transitions
    for distant publishing """
    distant_transitions = ('copy_distant_submit', 'distant_partial_accept',
                           'distant_publishing', 'distant_accept',
                           'distant_unpublish', 'distant_reject')

    def __init__(self, distant_repository_rpath='workspaces'):
        self.distant_repository_rpath = distant_repository_rpath

    def __call__(self, ob, workflow_action, REQUEST=None, **kw):
        self.distantWorkflowTransition(ob, workflow_action, REQUEST, **kw)

    def _redirectObject(self, ob, workflow_action):
        if workflow_action in ('copy_distant_submit', 'distant_reject',
                               'distant_publishing'):
            return ob.aq_inner.aq_parent
        else:
            return ob

    def distantWorkflowTransition(self, ob, workflow_action, REQUEST=None, **kw):
        """ dispatch the call to the right method """
        if REQUEST is not None:
            kw.update(REQUEST.form)

        if 'workflow_action' in kw:
            workflow_action = kw['workflow_action']
            del kw['workflow_action']

        if workflow_action not in self.distant_transitions:
            # calling the regular CPS script
            ob.content_status_modify(workflow_action, REQUEST, **kw)
        else:
            result, psm = getattr(self, workflow_action)(ob, REQUEST, **kw)
            redirect_object = self._redirectObject(ob, workflow_action)
            self.finalizeTransition(ob, psm, result, redirect_object, REQUEST,
                                    **kw)

    def finalizeTransition(self, ob, psm, result, redirect_object, REQUEST=None,
                           **kw):
        """ called at the end of transition """
        if REQUEST is None:
            return None

        url = redirect_object.absolute_url()

        if result:
            kwargs = {'portal_status_message': 'psm_status_changed'}
            kwargs = urlencode(kwargs)
            redirect_url = '%s?%s' % (redirect_object.absolute_url(), kwargs)
        else:
            search_param = kw.get('search_param', '')
            search_term = kw.get('search_term', '')
            comments = kw.get('comments', '')
            kwargs = {
                'search_param': search_param,
                'search_term': search_term,
                'comments': comments,
                'portal_status_message': psm
                }
            kwargs = urlencode(kwargs)
            page_template = kw.get('workflow_action_form', '')
            redirect_url = '%s/%s?%s' % (redirect_object.absolute_url(),
                                         page_template, kwargs)

        REQUEST.RESPONSE.redirect(redirect_url)

    #
    # wf transitions APIs (method name == transition name)
    #
    def copy_distant_submit(self, ob, REQUEST=None, **kw):
        """ make a new copy """
        def _checkPushId(element):
            if not element.startswith('partial_publisher:'):
                element = 'partial_publisher:%s' % element
            return element

        # checking distant_submit and distant_publish elements
        distant_publish = kw.get('distant_publish', [])
        if isinstance(distant_publish, str):
            distant_publish = [distant_publish]

        distant_submit = kw.get('distant_submit', [])
        if isinstance(distant_submit, str):
            distant_submit = [distant_submit]

        if distant_submit == [] and distant_publish == []:
            return False, 'psm_miss_distant_section'

        # checking push_ids
        push_ids = kw.get('push_ids', [])
        if push_ids == []:
            return False, 'psm_miss_push_ids'

        push_ids = map(_checkPushId, push_ids)
        kw['push_ids'] = push_ids

        psm = ''
        kw['distant_container'] = distant_publish
        kw['distant_container_with_submission'] = distant_submit

        # distant publishing, adding members into the stack
        folder = ob.aq_inner.aq_parent
        folder_before = folder.objectIds()
        res = self._doActionFor(ob, 'copy_distant_submit', **kw)

        folder_after = folder.objectIds()
        for element in folder_after:
            if element in folder_before:
                continue
            else:
                ob = folder[element]
                break

        # calling a specific transition to push delegatees into the stack
        # in the new object
        kw['current_wf_var_id'] = 'distant_reviewers'
        self._doActionFor(ob, 'manage_delegatees', **kw)

        return True, psm

    def distant_accept(self, ob, REQUEST=None, **kw):
        """ distant accept """
        wftool = getToolByName(ob, 'portal_workflow')
        for element in ('distant_portal', 'distant_container',
                        'distant_container_with_submission'):
            kw[element] = wftool.getInfoFor(ob, element)

        self._doActionFor(ob, 'distant_accept', **kw)
        return True, ''

    def distant_partial_accept(self, ob, REQUEST=None, **kw):
        """ distant parial accept """
        wftool = getToolByName(ob, 'portal_workflow')

        # here we need to increment the stack variable associated with the user
        portal_membership = getToolByName(ob, 'portal_membership')
        member_id = portal_membership.getAuthenticatedMember().getId()

        # retrieving stack elements
        stack = wftool.getStackFor(ob, 'distant_reviewers')
        elements = stack.getStackContent('object', context=ob)

        # checking user state
        validaters = len(elements)
        validated = 0

        for element in elements:
            if element.getMemberId() == member_id:
                element.validate()
                validated += 1
            else:
                if element.hasValidated():
                    validated += 1


        for element in ('distant_portal', 'distant_container',
                        'distant_container_with_submission'):
            kw[element] = wftool.getInfoFor(ob, element)

        kw['current_wf_var_id'] = 'distant_reviewers'

        if validated == validaters:
            # everybody has validated
            self._doActionFor(ob, 'distant_accept', **kw)
        else:
            # there are still users that has not validated
            self._doActionFor(ob, 'distant_partial_accept', **kw)

        return True, ''

    def distant_publishing(self, ob, REQUEST=None, **kw):
        """ distant publishing """
        wftool = getToolByName(ob, 'portal_workflow')
        distant_server = wftool.getInfoFor(ob, 'distant_portal')

        comments = kw.get('comments', '')
        distant_creation_path = self.distant_repository_rpath

        # need to check the user's rights on the distant
        # site, to decide wheter to wait for its aproval
        pdp = ob.portal_distant_publisher
        distant_paths = wftool.getInfoFor(ob, 'distant_container')
        distant_paths_with_sub = wftool.getInfoFor(ob,
                                 'distant_container_with_submission')

        distant_published_rpaths = []

        for distant_publishing_path in distant_paths:
            distant_published_rpath = pdp.distantPublication(ob, distant_server,
                                                         distant_creation_path,
                                                         distant_publishing_path,
                                                         False, comments)
            distant_published_rpaths.append(distant_published_rpath)

        for distant_publishing_path in distant_paths_with_sub:
            distant_published_rpath = pdp.distantPublication(ob, distant_server,
                                                         distant_creation_path,
                                                         distant_publishing_path,
                                                         True, comments)
            distant_published_rpaths.append(distant_published_rpath)

        kw['distant_portal'] = distant_server
        kw['distant_container'] = distant_publishing_path
        kw['distant_published_rpaths'] = distant_published_rpaths

        self._doActionFor(ob, 'distant_publishing', **kw)

        return True, ''

    def distant_unpublish(self, ob, REQUEST=None, **kw):
        """ unpublish """
        kw['distant_portal'] = wftool.getInfoFor(ob, 'distant_portal')
        self._doActionFor(ob, 'distant_unpublish', **kw)
        return True, ''

    def distant_reject(self, ob, REQUEST=None, **kw):
        """ rejecting the distant publication """
        kw['distant_portal'] = wftool.getInfoFor(ob, 'distant_portal')
        self._doActionFor(ob, 'distant_reject', **kw)
        return True, ''

    def canPublish(self, object, roles=()):
        """ tells if the given object can be published """
        if not self.isMemberReviewer(object):
            return False

        mtool = getToolByName(object, 'portal_membership')
        member = mtool.getAuthenticatedMember()
        member_id = member.getMemberId()

        if roles != ():
            for role in roles:
                if member.has_role(role):
                    return True

        wftool = getToolByName(object, 'portal_workflow')
        stack = wftool.getStackFor(object, 'distant_reviewers')
        if stack is None:
            return False

        if not stack.containsMember(wftool, mtool, member_id):
            return False

        # here we allow the transition if the stack is fully
        # validated
        return stack.allValidated(wftool, mtool)

    def isMemberReviewer(self, object, member_id=None, roles=()):
        """ tells if given member belong to the stack """
        mtool = getToolByName(object, 'portal_membership')
        if member_id is None:
            member = mtool.getAuthenticatedMember()
            member_id = member.getMemberId()
        else:
            member = mtool.getMemberById(member_id)

        if roles != ():
            for role in roles:
                if member.has_role(role):
                    return True

        wftool = getToolByName(object, 'portal_workflow')
        stack = wftool.getStackFor(object, 'distant_reviewers')
        if stack is None:
            return False

        return stack.containsMember(wftool, mtool, member_id)

    def _doActionFor(self, object, action, **kw):
        wftool = getToolByName(object, 'portal_workflow')
        # unifiying comments
        if 'comment' in kw and kw['comment'] != '':
            kw['comments'] = kw['comment']
        elif 'comments' in kw and kw['comments'] != '':
            kw['comment'] = kw['comments']
        wftool.doActionFor(object, action, **kw)
