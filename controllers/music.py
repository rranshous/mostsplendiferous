import cherrypy
from lib.base import *


class Music(BaseController):
    """
    handles music suggestions
    """
    MUSIC_LIST_PATH = '/home/robby/coding/mostsplendiferous/templates/music_list.txt'
    @cherrypy.expose
    def index(self):
        return render('/music.html')

    @cherrypy.expose
    def add_suggestion(self,suggestion=None):
        # we are going to append the suggestion
        # to the suggestion file
        with file(self.MUSIC_LIST_PATH,'a') as fh:
            fh.write('<li>%s</li>\n\n' % suggestion)
        return redirect('/music')
