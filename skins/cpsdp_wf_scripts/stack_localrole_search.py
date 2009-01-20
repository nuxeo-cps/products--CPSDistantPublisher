##parameters=search_param=None, search_term=None, push_ids=[], REQUEST=None
#$Id$
"""
Perform search for members/groups that will be put in stacks

Changes wrt folder_localrole_search script in CPSDefault:
- perform security check on stack, and not on the 'Change permissions'
  permission
- filter out members according to their contextual localroles
- search on groups do not return groups themselved but group members

"""
if search_term is not None and search_term.strip() in ('*', ''):
    psm = 'cps_empty_search'
    url = context.absolute_url()
    REQUEST.RESPONSE.redirect(('%s/content_distant_submit_form?'
                               'portal_status_message=%s') % (url, psm))
    return []

mdir = context.portal_directories.members
id_field = mdir.id_field
return_fields = (id_field, 'givenName', 'sn', 'email')
results = []

if search_param in ('fullname', 'email'):
    # first get portal member ids without externall call (e.g. LDAP)
    if search_param == 'fullname':
        # cannot search both parameters at the same time because we want a
        # OR search, not AND.
        from_ids = mdir.searchEntries(**{
            id_field: search_term,
            'return_fields': return_fields,
        })
        results.extend(from_ids)

    from_fullname_or_email = mdir.searchEntries(**{
        search_param: search_term,
        'return_fields': return_fields,
    })
    results.extend(from_fullname_or_email)

elif search_param == 'groupname':
    gdir_id = getattr(context.acl_users, 'groups_dir', 'groups')
    gdir  = context.portal_directories[gdir_id]
    group_ids = gdir.searchEntries(group=search_term)
    if group_ids:
        # let's get people from the group and add them
        from_group = mdir.searchEntries(groups=group_ids,
                                        return_fields=return_fields)
        results.extend(from_group)


# add old results
push_ids = [push_id.split(':')[-1] for push_id in push_ids]
if push_ids:
    old_results = mdir.searchEntries(**{
        id_field: push_ids,
        'return_fields': return_fields
    })
    results.extend(old_results)

# filtering out redundant results
results = dict(results)
results = results.items()

# filters entries to local roles
# one cannot do the opposite beacause of localroles acquired from groups
# and especially virtual groups such as role:authenticated
qualified_roles = ('WorkspaceManager', 'WorkspaceMember', 'Manager', 'Owner')
filtered_results = []
for id, entry in results:
    local_roles = context.getLocalRoles(id, context, type='user')
    has_role = False
    for local_role in local_roles:
        if local_role in qualified_roles:
            has_role = True
            break
    if has_role:
        filtered_results.append((id in push_ids, id, entry))

filtered_results.sort()
return filtered_results

