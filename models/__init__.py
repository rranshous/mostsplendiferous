from elixir import *
import datetime
import cherrypy
from hashlib import sha1
import models as m
import os
import random
from json import dumps, loads

def reset_session():
    try:
        session.rollback()
        session.expunge_all()
        session.remove()
    except:
        pass
    return

def setup():
    metadata.bind = "sqlite:///./dbs/dev.db"
    metadata.bind.echo = False
    setup_all()

## end helper functions ##

# for now
BaseEntity = Entity

class Guest(BaseEntity):
    name = Field(Unicode)
    rsvpd = Field(Boolean,default=False)
    attending = Field(Boolean,default=False)
    comment = Field(UnicodeText,default='')
