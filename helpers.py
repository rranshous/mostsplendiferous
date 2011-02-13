from templates import render
import cherrypy
from cherrypy import HTTPRedirect, HTTPError
from decorator import decorator
from urlparse import urljoin
import models as m

ADMIN_TOKEN = '555'

def add_flash(msg_type,msg=None):
    if not msg:
        msg = msg_type
        msg_type = 'info'

    cherrypy.session.setdefault(msg_type,[]).append(msg)

def redirect(*args):
    url = '/'.join((str(x) for x in args))
    raise HTTPRedirect(url)

def get_guest_token(guest):
    token = str(hash(str(guest.id)))
    return token

def get_token():
    token = cherrypy.session.get('token')
    return token

def get_guest():
    guest = cherrypy.session.get('guest')
    print 'get_guest: %s' % guest
    return guest

def init_token(token,guest=None):
    print 'init_token: %s' % token
    cherrypy.session['token'] = token
    cherrypy.session['guest'] = guest

def is_guest(guest):
    if get_token() == ADMIN_TOKEN:
        return True
    if not get_guest():
        return False
    if guest.id == get_guest().id:
        return True
    if get_token() == guest:
        return True
    return False


#@decorator
def grab_token(f): #,*args,**kwargs):
    def gt(*args,**kwargs):
        # we are going to inspect the first
        # and last args as well as kwargs for tokens
        guest_tokens = []
        for guest in m.Guest.query.all():
            guest_tokens.append((guest,get_guest_token(guest)))
        guest_tokens.append((None,ADMIN_TOKEN))
        for guest,guest_token in guest_tokens:
            if args:
                if guest_token == args[0]:
                    args = args[1:]
                    init_token(guest_token,guest)
                if guest_token == args[-1]:
                    args = args[:-1]
                    init_token(guest_token,guest)
            if kwargs.get('token') == guest_token:
                init_token(guest_token,guest)
                del kwargs['token']
        return f(*args,**kwargs)
    return gt

