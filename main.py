#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import os
import time
import datetime as dt
from google.appengine.ext import ndb
from google.appengine.api import users
import jinja2

JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
                                       extensions=["jinja2.ext.autoescape"],
                                       autoescape=True)


class User(ndb.Model):
    id_user = ndb.StringProperty(required=True)
    name = ndb.StringProperty(required=True)


class Juego(ndb.Model):
    titulo = ndb.StringProperty(required=True)
    desarrolladora = ndb.StringProperty(required=True)
    propietario = ndb.KeyProperty(required=True, kind=User)
    nota = ndb.IntegerProperty(default=None)
    plataforma = ndb.StringProperty(required=True)
    portada = ndb.BlobProperty(default=None)
    fecha = ndb.DateProperty()


class MainHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:

            db_user = User.query(User.id_user == user.user_id()).get()

            if not db_user:
                db_user = User(id_user=user.user_id(), name=user.nickname().partition("@")[0])
                db_user.put()
            self.redirect("/coleccion")
        else:
            labels = {
                "user_login": users.create_login_url("/")
            }
            template = JINJA_ENVIRONMENT.get_template("login.html")
            self.response.write(template.render(labels))


class ColeccionHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()

        if user:
            juegos = Juego.query().order(Juego.fecha)

            propietarios = []
            for juego in juegos:
                propietarios.append(User.query(User.key == juego.propietario).get())

            values = {
                'juegos': juegos,
                'username': user.nickname().partition("@")[0],
                'propietarios': propietarios,
                'user': user,
                "user_id": user.user_id(),
                'user_logout': users.create_logout_url("/"),
                'add': self.request.get("add"),
                'del': self.request.get("del"),
                'edi': self.request.get("edi"),
                'game': self.request.get("game")
            }

            template = JINJA_ENVIRONMENT.get_template("coleccion.html")
            self.response.write(template.render(values))
        else:
            self.redirect("/")


class AddHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            values = {
                "user": user.nickname(),
                "username": user.nickname().partition("@")[0],
                "user_logout": users.create_logout_url("/")
            }

            template = JINJA_ENVIRONMENT.get_template("add.html")
            self.response.write(template.render(values))
        else:
            self.redirect("/")

    def post(self):
        user = users.get_current_user()

        if user:
            titulo = self.request.get("titulo")
            plataforma = self.request.get("plataforma")
            desarrolladora = self.request.get("desarrolladora")
            fecha = dt.date.today()
            propietario = User.query(User.id_user == user.user_id()).get().key

            no = None
            if self.request.get("nota") != "":
                no = int(self.request.get("nota"))

            image_file = None
            if self.request.get("portada") != "":
                # Store the added image
                image_file = self.request.get("portada", None)

            juego = Juego(titulo=titulo, desarrolladora=desarrolladora, propietario=propietario, plataforma=plataforma, portada=image_file, nota=no, fecha=fecha)

            juego.put()
            time.sleep(1)

            self.redirect("/coleccion")
        else:
            self.redirect("/")


class DeleteHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        db_user = User.query(User.id_user == user.user_id()).get()

        if user and db_user:
            juego_id = int(self.request.get("id"))
            juego = Juego.query(Juego.key == ndb.Key(Juego, juego_id), Juego.propietario == db_user.key).get()

            juego.key.delete()
            time.sleep(1)
            self.redirect("coleccion")

        else:
            self.redirect("/")


class EditHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        db_user = User.query(User.id_user == user.user_id()).get()

        if user and db_user:
            juego_id = int(self.request.get("id"))
            juego = Juego.query(Juego.key == ndb.Key(Juego, juego_id), Juego.propietario == db_user.key).get()

            if juego:
                values = {
                    "user": user.nickname(),
                    "username": user.nickname().partition("@")[0],
                    "user_logout": users.create_logout_url("/"),
                    "juego": juego
                }

                template = JINJA_ENVIRONMENT.get_template("edit.html")
                self.response.write(template.render(values))
            else:
                self.redirect("coleccion")
        else:
            self.redirect("/")

    def post(self):
        user = users.get_current_user()
        db_user = User.query(User.id_user == user.user_id()).get()

        if user and db_user:
            juego_id = int(self.request.get("id"))
            juego = Juego.query(Juego.key == ndb.Key(Juego, juego_id), Juego.propietario == db_user.key).get()

            juego.titulo = self.request.get("titulo")
            juego.nota = int(self.request.get("nota"))
            juego.plataforma = self.request.get("plataforma")
            juego.desarrolladora = self.request.get("desarrolladora")

            if self.request.get("portada") != "":
                image_file = self.request.get("portada", None)
                juego.portada = image_file

            juego.put()
            time.sleep(1)

            self.redirect("coleccion")

        else:
            self.redirect("/")

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/coleccion', ColeccionHandler),
    ('/add', AddHandler),
    ('/del', DeleteHandler),
    ('/edit', EditHandler)
], debug=True)
