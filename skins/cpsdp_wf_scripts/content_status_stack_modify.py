##parameters=workflow_action, REQUEST=None, **kw
# $Id$
"""
    call distantWorkflowTransition
"""
publisher = context.portal_distant_publisher
publisher.distantWorkflowTransition(context, workflow_action, REQUEST, **kw)
