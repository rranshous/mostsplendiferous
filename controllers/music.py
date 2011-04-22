import cherrypy
from lib.base import *


class Music(BaseController):
    """
    handles music suggestions
    """

    @cherrypy.expose
    def index(self):
        return render('/music.html')

    @cherrypy.expose
    def add_suggestion(self,suggestion=None):
        # we are going to append the suggestion
        # to the suggestion file
        with file('templates/music_list.txt','a') as fh:
            fh.write('<li>%s</li>\n\n' % suggestion)
        return redirect('/music')
