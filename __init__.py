# (C) Copyright 2005 Nuxeo SA <http://nuxeo.com>
# Authors:
# Tarek Ziade <tz@nuxeo.com>
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
""" CPSDistantPublisher Init
"""
import Products.CMFCore
from Products.CMFCore.DirectoryView import registerDirectory

import DistantPublisher
import PartialPublisherStackElement
import PartialPublisherStack

registerDirectory('skins', globals())

def initialize(registrar):
    Products.CMFCore.utils.ToolInit(
        'CPS Distant Publisher Tool',
        tools=(DistantPublisher.DistantPublisher,),
        product_name='CPSDistantPublisher',
        icon='tool.png',
        ).initialize(registrar)
