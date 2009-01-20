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
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from Products.CPSWorkflow.stackregistries import WorkflowStackElementRegistry
from Products.CPSWorkflow.basicstackelements import UserStackElement
from Products.CPSWorkflow.interfaces import IStackElement

class PartialPublisherStackElement(UserStackElement):
    """PartialPublicationStackElement

    help to store partial publication infos

    >>> ob = PartialPublisherStackElement('partial_publisher:id')
    >>> ob.getMemberId()
    'id'
    >>> ob.validate()
    >>> ob.acknowledgment
    1
    >>> ob.reject()
    >>> ob.acknowledgment
    0
    """
    __implement__ = (IStackElement,)

    id = ''
    meta_type = 'Partial Publisher Stack Element'
    prefix = 'partial_publisher'
    hidden_meta_type = 'Hidden Partial Publisher Stack Element'

    def __init__(self, id, **kw):
        self.id = id
        self.acknowledgment = kw.get('acknowledgment', 0)

    def __call__(self):
        return {'id': self.getId(),
                 'acknowledgment': self.hasValidated()}

    def __str_header(self):
        return self.meta_type.replace(' ', '')

    def __str__(self):
        return "<%s %s >" % (self.__str_header(), self())

    def hasValidated(self):
        return self.acknowledgment

    def getMemberId(self):
        return self.id[len(self.prefix)+1:]

    def validate(self):
        self.acknowledgment = 1

    def reject(self):
        self.acknowledgment = 0

InitializeClass(PartialPublisherStackElement)

class PartialHiddenPublisherStackElement(UserStackElement):
    __implement__ = (IStackElement,)

    prefix = 'hidden_partial_publisher'
    meta_type = 'Hidden Partial Publisher Stack Element'

    def __init__(self, id):
        self.id = id
        self.acknowledgment = 0

    def hasValidated(self):
        return 0

InitializeClass(PartialHiddenPublisherStackElement)


class PartialPublisherGroupStackElement(PartialPublisherStackElement):
    """Group Stack Element """
    meta_type = 'Partial Publisher Group Stack Element'
    prefix = 'partial_group'
    hidden_meta_type = 'Hidden Partial Publisher Group Stack Element'

    __implement__ = (IStackElement,)


InitializeClass(PartialPublisherGroupStackElement)


class PartialHiddenPublisherGroupStackElement(PartialPublisherStackElement):
    """MSG Hidden Group Stack Element
    """
    meta_type = 'Partial Publisher Hidden Group Stack Element'
    prefix = 'partial_hidden_group'

    __implement__ = (IStackElement,)

InitializeClass(PartialHiddenPublisherGroupStackElement)

WorkflowStackElementRegistry.register(PartialPublisherStackElement)
WorkflowStackElementRegistry.register(PartialHiddenPublisherStackElement)
WorkflowStackElementRegistry.register(PartialPublisherGroupStackElement)
WorkflowStackElementRegistry.register(PartialHiddenPublisherGroupStackElement)
