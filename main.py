import webapp2
import jinja2
import requests
import json
import base64
import os
import time
import logging

import config

from google.appengine.ext import deferred
from google.appengine.ext import ndb

import requests_toolbelt.adapters.appengine
requests_toolbelt.adapters.appengine.monkeypatch()

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class Home(webapp2.RequestHandler):
    def get(self):
        template = env.get_template('index.html')
        self.response.write(template.render())


app = webapp2.WSGIApplication([
    ('/', Home),
], debug=True)