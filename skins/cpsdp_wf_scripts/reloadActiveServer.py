##parameters=active_server, url
request = container.REQUEST
RESPONSE =  request.RESPONSE

context.portal_remote_controller_client.setActiveServer(active_server)

RESPONSE.redirect(url)
