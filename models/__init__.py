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
    metadata.bind = "sqlite:////home/robby/coding/mostsplendiferous/dbs/dev.db"
    metadata.bind.echo = False
    setup_all()

## end helper functions ##

# for now
BaseEntity = Entity

class Guest(BaseEntity):
    name = Field(Unicode)
    rsvpd = Field(Boolean,default=False)
    attending = Field(Boolean,default=None)
    comment = Field(UnicodeText,default='')
    party_size = Field(Integer,default=1)

    guests_allowed = Field(Integer,default=0)
    guests_requested = Field(Integer,default=0)
    guests_coming = Field(Integer,default=0)
