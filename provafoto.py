import cherrypy
import os, os.path


class provafoto:

	exposed = True

	def GET(self, *uri):

		if uri[0] == 'photo':
			return """ <html>
	        <head>
	            <title>Sample Web Form</title>
	        </head>
	    <body>

	     <img src="/static/image.jpg" alt="Flowers in Chania">

	    </body>
	    </html> """


if __name__ == '__main__':
	conf = {
		'/': {
		'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
		'tools.sessions.on': True,
		'tools.staticdir.root': os.path.abspath(os.getcwd())
	},
	'/static': {
		'tools.staticdir.on': True,
		'tools.staticdir.dir': '.'
	   }
  }

cherrypy.tree.mount (provafoto(), '/', conf)
cherrypy.config.update({'server.socket_host': '0.0.0.0'})
cherrypy.config.update({'server.socket_port': 8081})
cherrypy.engine.start()
cherrypy.engine.block()
