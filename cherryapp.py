#!/usr/bin/python
import cherrypy
import logging as log
import models as m
import controllers as c

if __name__ == "__main__":
    # setup the db connection
    m.setup()

    # create our app from root
    app = cherrypy.Application(c.Root())

    # setup a tool to rset our db session
    cherrypy.tools.reset_db = cherrypy.Tool('on_end_resource',
                                            m.reset_session)

    # get this thing hosted
    cherrypy.quickstart(app, config='cherryconfig.ini')

