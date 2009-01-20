##parameters=doc_rpath,distant_rpaths, REQUEST=None
# $Id$
"""
    call distantUnPublication
"""
publisher = context.portal_distant_publisher
proxy = context.restrictedTraverse(doc_rpath)

# extracting infos
for distant_rpath in distant_rpaths:
    distant_rpath = distant_rpath.split(':')
    distant_server = distant_rpath[0]
    distant_publishing_path = distant_rpath[1]

    # getting the state
    if REQUEST is not None:
        state = REQUEST.get('state_%s' % distant_rpath, 'published')
    else:
        state = 'pending'

    if state == 'published':
        result = publisher.distantUnpublication(distant_server, distant_publishing_path)
    else:
        result = publisher.distantRemoval(distant_server, distant_publishing_path)

    kw = {'distant_published_rpath': distant_publishing_path,
          'distant_server': distant_server}

    if result:
        publisher.distantWorkflowTransition(proxy, 'distant_unpublish', REQUEST, **kw)
    else:
        if REQUEST is not None:
            psm = 'cps_couldnot_unpublish'
            url = context.absolute_url()
            REQUEST.RESPONSE.redirect(('%s/content_distant_submit_form?'
                                      'portal_status_message=%s') % (url, psm))
