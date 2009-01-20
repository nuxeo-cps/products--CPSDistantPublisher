##parameters=entry_id, proxy, type='user'
# $Id$
"""Return the roles of the given user local to the specified context.

Attention: this method doesn't know how to deal with blocked roles.
"""
members_directory = context.portal_directories.members
groups_field_id = getattr(context.acl_users, 'users_groups_field', 'groups')

roles_dict, local_roles_blocked = proxy.getCPSLocalRoles()
local_roles_struct = roles_dict.get('%s:%s' % (type, entry_id), [])

local_roles = []
for role_rpath_struct in local_roles_struct:
    local_roles += role_rpath_struct['roles']

if type is 'user':
    # Get the roles local associated with groups this user is member of
    entry = members_directory.getEntry(entry_id)
    groups = entry[groups_field_id]

    for group in groups:
        group_local_roles_struct = roles_dict.get('group:' + group, [])
        group_local_roles = []
        for role_rpath_struct in local_roles_struct:
            local_roles += role_rpath_struct['roles']
        local_roles += group_local_roles

return local_roles
