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
# $Id$
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import View

from Products.CPSWorkflow.interfaces import IWorkflowStack, ISimpleWorkflowStack
from Products.CPSWorkflow.stackregistries import WorkflowStackRegistry
from Products.CPSWorkflow.basicstacks import SimpleStack

class PartialPublisherSimpleStack(SimpleStack):
    """ Simple stack for distant publication

    >>> PartialPublisherSimpleStack() is not None
    True
    """
    meta_type = 'PartialPublisher Simple Stack'
    security = ClassSecurityInfo()
    __implements__ = (IWorkflowStack, ISimpleWorkflowStack)

    security.declareProtected(View, 'containsMember')
    def containsMember(self,  wftool, mtool, member_id=None):
        """ tells if a member is in the stack
        """
        if member_id is None:
            member = mtool.getAuthenticatedMember()
            member_id = member.getMemberId()
        else:
            member = mtool.getMemberById(member_id)

        return member_id in [stack_member.getMemberId()
                             for stack_member in self._getElementsContainer()]

    security.declareProtected(View, 'hasValidated')
    def hasValidated(self,  wftool, mtool, member_id=None):
        """ tells if a member has validated """
        if member_id is None:
            member = mtool.getAuthenticatedMember()
            member_id = member.getMemberId()
        else:
            member = mtool.getMemberById(member_id)

        for stack_member in self._getElementsContainer():
            if stack_member.getMemberId() == member_id:
                return stack_member.hasValidated()

        return False

    security.declareProtected(View, 'allValidated')
    def allValidated(self,  wftool, mtool):
        """ tells if all members have validated """
        for stack_member in self._getElementsContainer():
            if not stack_member.hasValidated():
                return False
        return True

InitializeClass(PartialPublisherSimpleStack)
WorkflowStackRegistry.register(PartialPublisherSimpleStack)
