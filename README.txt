CPSDistantPublisher
===================
$Id$

Goal
----

Add a remote publication transition to publish documents on a remote CPS
instance through XML-RPC. The document can be distantly unpublished as well.

Usage
-----

Use the portal_quickinstaller or an External Method to install
CPSDistantPublisher on your CPS instance. This will create a new tool
'portal_distant_publisher' where you can register the root of folders on the
remote CPS instance. The list of remote CPS instances is to be registered in the
portal_remote_controller_client tool::

  - Name: some_name
  - URL: http://user:password@server:port/cps

This installer also extends the workspace_content_wf workflow definition to add a
new transition for distant publishing to registered remote CPS instances
sections after a stack based local validation process.

Implementation
--------------

CPSDistantPublisher uses CPSRemoteController API to take control of the remote
server.
