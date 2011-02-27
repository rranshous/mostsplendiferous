#!/usr/bin/python
import cherrypy
import logging as log
import models as m
import controllers as c
import sys

# setup the db connection
m.setup()

# setup a tool to rset our db session
cherrypy.tools.reset_db = cherrypy.Tool('on_end_resource',
                                        m.reset_session)

# if we get the production flag use the production config
config_file = 'cherryconfig.ini'
if 'production' in sys.argv:
    config_file = 'cherryconfig.production.ini'


if 'daemon' in sys.argv:
    cherrypy.tree.mount(c.Root(),config=config_file)

else:
    # get this thing hosted
    # create our app from root
    app = cherrypy.Application(c.Root())
    cherrypy.quickstart(app, config=config_file)
