# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Authors:
# Anahide Tchertchian <at@nuxeo.com>
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
"""Definition of the validation workflow for distant publication.
"""

from Products.CMFCore.permissions import View, ModifyPortalContent

# transition behaviours
from Products.CPSWorkflow.transitions import \
     TRANSITION_INITIAL_PUBLISHING, \
     TRANSITION_BEHAVIOR_FREEZE, \
     TRANSITION_BEHAVIOR_DELETE, \
     TRANSITION_BEHAVIOR_MERGE, \
     TRANSITION_BEHAVIOR_PUSH_DELEGATEES, \
     TRANSITION_BEHAVIOR_POP_DELEGATEES, \
     TRANSITION_BEHAVIOR_PUBLISHING,\
     TRANSITION_ALLOWSUB_CREATE,\
     TRANSITION_ALLOWSUB_PUBLISHING

from Products.DCWorkflow.Transitions import TRIGGER_USER_ACTION

# state behaviours
from Products.CPSWorkflow.states import \
     STATE_BEHAVIOR_PUSH_DELEGATEES, \
     STATE_BEHAVIOR_POP_DELEGATEES


view_roles = ('Manager',
              'WorkspaceManager',
              'WorkspaceMember',
              'WorkspaceReader')

pub_roles = ('Manager', 'WorkspaceManager')

distant_reviewer_roles = ('DistantReviewer',)

distant_pub_roles = ('Manager', 'WorkspaceManager')

edit_roles = ('Manager',
              'WorkspaceManager',
              'WorkspaceMember')

def setValidationWorkflowDefinition(context):
    """Get the validation workflow definition.

    This method will be called by the product installer

    context helps to get current wf state
    """
    setValidationWorkflowContainer(context)

    wc_wf = context.portal_workflow.workspace_content_wf
    setValidationWorkflowVariables(wc_wf)
    setValidationWorkflowStates(wc_wf)
    setValidationWorkflowTransitions(wc_wf)


def setValidationWorkflowContainer(context):
    """ sets the container behavior """
    wf_wf = context.portal_workflow.workspace_folder_wf
    transitions = wf_wf.transitions

    kw  = {'title': 'Allow sub publishing',
           'transition_behavior': (TRANSITION_ALLOWSUB_CREATE,
                                   TRANSITION_ALLOWSUB_PUBLISHING),
           'new_state_id': '',
           'props': {'guard_roles': '; '.join(edit_roles)}}

    if 'sub_publishing' in transitions.objectIds():
        transitions.deleteTransitions(('sub_publishing',))
    transitions.addTransition('sub_publishing')
    ob = transitions['sub_publishing']
    ob.setProperties(**kw)

    work_state = wf_wf.states['work']


    for new_behavior in (TRANSITION_ALLOWSUB_PUBLISHING,):
        state_behaviors = work_state.state_behaviors
        if new_behavior not in state_behaviors:
            work_state.state_behaviors = state_behaviors + (new_behavior,)

    for new_transition in ('sub_publishing',):
        transitions = work_state.transitions
        if new_transition not in transitions:
            work_state.transitions = transitions + (new_transition,)

def setValidationWorkflowVariables(context):
    """ sets the validation workflow variables """
    variables = context.variables

    dvariables = {}

    dvariables['distant_container'] = {
        'description': 'Destination container(s) for the last paste/publish',
        'default_expr': "python:state_change.kwargs.get('distant_container', '')",
        'for_status': 1,
        'update_always': 1
        }

    dvariables['distant_container_with_submission'] = {
        'description': 'Destination container(s) for the last submission',
        'default_expr':
          "python:state_change.kwargs.get('distant_container_with_submission', '')",
        'for_status': 1,
        'update_always': 1
        }

    dvariables['distant_portal'] = {
        'description': 'Destination server settled for distant publishing',
        'default_expr': "python:state_change.kwargs.get('distant_portal', '')",
        'for_status': 1,
        'update_always': 1
        }

    dvariables['distant_partial_validation'] = {
        'description': 'Tells who validated the document',
        'default_expr':
            "python:state_change.kwargs.get('distant_partial_validation', '')",
        'for_status': 1,
        'update_always': 1
        }

    dvariables['distant_published_rpaths'] = {
        'description': 'Give the full rpaths on distant server',
        'default_expr':
            "python:state_change.kwargs.get('distant_published_rpaths', [])",
        'for_status': 1,
        'update_always': 1
        }


    for dvariable in dvariables:
        if dvariable in variables.objectIds():
            variables.deleteVariables((dvariable,))
        variables.addVariable(id=dvariable)
        ob = variables[dvariable]
        ob.setProperties(**dvariables[dvariable])

def setValidationWorkflowStates(context):
    """Get the validation workflow states
    """
    states = context.states
    dstates = {}

    # lists of roles to be used in stacks and transitions guard roles
    # definitions
    validation_stack = {
        'stackdef_type': 'Simple Stack Definition',
        'stack_type'   : 'PartialPublisher Simple Stack',
        'var_id'    : 'distant_reviewers',
        'managed_role_exprs': {'DistantReviewer': 'python:True'},
        'empty_stack_manage_guard': {
            'guard_roles': '; '.join(edit_roles),
            },
        }

    dstates['distant_pending'] = {
        'title': 'Waiting for reviewer',
        'transitions': ('distant_accept',
                        'distant_reject',
                        'distant_partial_accept',
                        'manage_delegatees',
                        'view_delegatees',
                        ),
        'permissions': {
            View: edit_roles + distant_reviewer_roles,
            ModifyPortalContent: edit_roles + distant_reviewer_roles,
            },
        'state_behaviors': (STATE_BEHAVIOR_PUSH_DELEGATEES,
                            STATE_BEHAVIOR_POP_DELEGATEES
                            ),
        'stackdefs' : {
            'distant_reviewers': validation_stack,
            },
        'push_on_workflow_variable' : ('distant_reviewers',),
        'pop_on_workflow_variable' : ('distant_reviewers',),
        }

    dstates['distant_publish_ready'] = {
        'title': 'Document is ready to be published on distant portal',
        'transitions': ('distant_publishing', 'distant_reject'),
        'permissions': {
            View: edit_roles,
            ModifyPortalContent: pub_roles,
            },
        }

    for dstate_id, dstate_def in dstates.items():
        if dstate_id in states.objectIds():
            states.deleteStates((dstate_id,))
        states.addState(dstate_id)
        ob = states[dstate_id]
        for permission in dstate_def.get('permissions', {}).keys():
            ob.setPermission(permission, 0,
                             dstate_def['permissions'][permission])
        ob.setProperties(**dstate_def)

    # linking distant_publish and distant_submit transitions
    # to work state
    work_state = states['work']
    for new_transition in ('copy_distant_submit', 'distant_unpublish'):
        transitions = work_state.transitions
        if new_transition not in transitions:
            work_state.transitions = transitions + (new_transition,)

def setValidationWorkflowTransitions(context):
    """Get the validation workflow transitions
    """
    transitions = context.transitions

    dtransitions = {}

    dtransitions['distant_publish'] = {
        'title': 'Member publishes distant directly',
        'transition_behavior': (TRANSITION_INITIAL_PUBLISHING,
                                TRANSITION_BEHAVIOR_FREEZE,
                                TRANSITION_BEHAVIOR_MERGE),
        'new_state_id': 'distant_publish_ready',
        'props': {
           'guard_roles': '; '.join(pub_roles),
           },
        }

    dtransitions['copy_distant_submit'] = {
        'title': 'Copy document in a new local copy for distant submission',
        'new_state_id': '',
        'transition_behavior': (TRANSITION_BEHAVIOR_PUBLISHING,),
        'clone_allowed_transitions': ('distant_submit', 'distant_publish'),
        'trigger_type': TRIGGER_USER_ACTION,
        'actbox_name': 'action_distant_submit',
        'actbox_category': 'workflow',
        'actbox_url': '%(content_url)s/content_distant_submit_form',
        'props': {'guard_roles': ';'.join(edit_roles)}
        }

    dtransitions['distant_submit'] = {
        'title': 'Member requests distant publishing',
        'new_state_id': 'distant_pending',
        'transition_behavior': (TRANSITION_INITIAL_PUBLISHING,
                                TRANSITION_BEHAVIOR_FREEZE,),
        'props': {
            'guard_roles': '; '.join(edit_roles),
            }
        }

    dtransitions['distant_accept'] = {
        'title': 'Reviewer accepts distant publishing',
        'new_state_id': 'distant_publish_ready',
        'transition_behavior': (TRANSITION_BEHAVIOR_MERGE,),
        'actbox_name': 'action_distant_accept',
        'actbox_category': 'workflow',
        'actbox_url': '%(content_url)s/content_distant_accept_form',
        'props': {
            'guard_expr': ('python:here.portal_distant_publisher.canPublish'
                           '(here, %s)') % str(pub_roles)
            },
        }

    dtransitions['distant_partial_accept'] = {
        'title': 'Reviewer accepts distant publishing',
        'new_state_id': '',
        'transition_behavior': (TRANSITION_BEHAVIOR_MERGE,),
        'actbox_name': 'action_distant_partial_accept',
        'actbox_category': 'workflow',
        'actbox_url': '%(content_url)s/content_distant_partial_accept_form',
        'props': {
            'guard_expr': 'python:here.portal_distant_publisher.isMemberReviewer(here)',
            },
        }

    dtransitions['distant_publishing'] = {
        'title': 'Workspace Manager publishes',
        'new_state_id': '',
        'transition_behavior': (TRANSITION_BEHAVIOR_DELETE,),
        'actbox_name': 'action_distant_publish',
        'actbox_category': 'workflow',
        'actbox_url': '%(content_url)s/content_distant_publish_form',
        'props': {
            'guard_roles': '; '.join(distant_pub_roles)
            }
        }

    dtransitions['distant_reject'] = {
        'title': 'Reviewer rejects publishing',
        'new_state_id': '',
        'transition_behavior': (TRANSITION_BEHAVIOR_DELETE,),
        'actbox_name': 'action_distant_reject',
        'actbox_category': 'workflow',
        'actbox_url': '%(content_url)s/content_distant_reject_form',
        'props': {
            'guard_expr': ('python:here.portal_distant_publisher.'
                           'isMemberReviewer(here, roles=%s)') % str(pub_roles),
            },
        }
    dtransitions['distant_unpublish'] = {
        'title': 'Reviewer removes distant content from publication',
        'new_state_id': '',
        'transition_behavior': (),
        }

    dtransitions['manage_delegatees'] = {
        'title': "Manage delegatees for distant publication",
        'new_state_id': '',
        'transition_behavior': (TRANSITION_BEHAVIOR_PUSH_DELEGATEES,
                                TRANSITION_BEHAVIOR_POP_DELEGATEES,
                                ),
        'trigger_type': TRIGGER_USER_ACTION,
        'push_on_workflow_variable' : ('distant_reviewers',),
        'pop_on_workflow_variable' : ('distant_reviewers',)
        }

    dtransitions['view_delegatees'] = {
        'title': "View delegatees for distant publication",
        'new_state_id': '',
        'trigger_type': TRIGGER_USER_ACTION,
        'actbox_name': 'action_view_delegatees',
        'actbox_category': 'workflow',
        'actbox_url': '%(content_url)s/content_view_delegatees_form',
        'props': {
            # XXX might need to use this exp. here
            #'guard_expr': 'python:here.portal_distant_publisher.isMemberReviewer(here)'
            'guard_roles': '; '.join(edit_roles + distant_reviewer_roles)
            },
        }

    for dtransition in dtransitions:
        if dtransition in transitions.objectIds():
            transitions.deleteTransitions((dtransition,))
        transitions.addTransition(dtransition)
        ob = transitions[dtransition]
        ob.setProperties(**dtransitions[dtransition])

