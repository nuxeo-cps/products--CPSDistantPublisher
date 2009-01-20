#!/usr/bin/python
# (C) Copyright 2004 Nuxeo SARL <http://nuxeo.com>
# Author: Tarek Ziade <tz@nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# # by the Free Software Foundation.
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
CPSDistantPublisher Installer

HOWTO USE THAT ?

 - Log into the ZMI as manager
 - Go to your CPS root directory
 - Create an External Method with the following parameters:

     id    : CPSDistantPublisher INSTALLER (or whatever)
     title : CPSDistantPublisher INSTALLER (or whatever)
     Module Name   :  CPSDistantPublisher.install
     Function Name : install
 - save it
 - click now the test tab of this external method.
"""
__author__ = "Tarek Ziadé <tz@nuxeo.com>"

import sys, os
from zLOG import  LOG,INFO,DEBUG,TRACE

from Products.CPSInstaller.CPSInstaller import CPSInstaller
from Products.ExternalMethod.ExternalMethod import ExternalMethod
from OFS.ObjectManager import BadRequestException, BadRequest

from Products.CPSDistantPublisher.workflows import validation_workflow

skins = {'cpsdp_wf_templates': 'Products/CPSDistantPublisher/skins/cpsdp_wf_templates',
         'cpsdp_wf_scripts': 'Products/CPSDistantPublisher/skins/cpsdp_wf_scripts',
         'cpsdp_wf_media': 'Products/CPSDistantPublisher/skins/cpsdp_wf_media'
         }

class CPSDistantPublisherInstaller(CPSInstaller):
    """ CPSDistantPublisher installer class definition """
    product_name = 'CPSDistantPublisher'

    def log(self,message):
        CPSInstaller.log(self,message)
        LOG('CPSDistantPublisher Installer',INFO,message)

    def install(self):
        """Main call
        """
        self.log("Starting CPSDistantPublisher specific install")
        self.verifySkins(skins)
        self.resetSkinCache()
        self.installTool()
        self.setupNewRoles()
        self.setupValidationWorkflow()
        self.installMandatoryProducts()
        self.setupTranslations()
        self.reindexCatalog()
        self.finalize()
        self.log("End of specific CPSDistantPublisher install")

    def installTool(self):
        """ installs the singleton """
        self.verifyTool('portal_distant_publisher', 'CPSDistantPublisher',
                        'CPS Distant Publisher Tool')

    def installProduct(self, ModuleName, InstallModuleName='install',
                       MethodName='install'):
        """ creates an external method for a
            product install and launches it
        """
        objectName ="cpsdp_"+ModuleName+"_installer"
        objectName = objectName.lower()

        # Install the product
        self.log(ModuleName+" INSTALL [ START ]")
        installer = ExternalMethod(objectName,
                                   "",
                                   ModuleName+"."+InstallModuleName,
                                   MethodName)
        try:
            self.portal._setObject(objectName,installer)

        except BadRequestException:
            self.log("External Method for "+ModuleName+" already installed")

        method_link = getattr(self.portal,objectName)
        method_link()
        self.log(ModuleName+" INSTALL [ STOP ]")

    def installMandatoryProducts(self):
        """Installs the mandatory products for CPSDistantPublisher """
        self.log("Installing CPSRemoteController, required")
        self.installProduct('CPSRemoteController')
        self.log("CPSRemoteController installation: DONE")

    def setupNewRoles(self):
        already = self.portal.valid_roles()
        roles = ('DistantReviewer',)
        for role in roles:
            if role not in already:
                self.portal._addRole(role)
                self.log(" Add role %s" % role)
                self.portal._addRole(role)

    def setupValidationWorkflow(self):
        """ extends existing workflow """
        self.log("Installing distant publication workflow (extending workspace_content_wf)")
        reload(validation_workflow)
        validation_workflow.setValidationWorkflowDefinition(self.portal)
        self.log("Installing distant publication workflow: DONE")

def install(self):
    installer = CPSDistantPublisherInstaller(self)
    installer.install()
    return installer.logResult()
