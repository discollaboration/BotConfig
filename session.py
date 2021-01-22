from redis import Redis
from os import environ as env
from flask import session
from json import loads, dumps
from random import choices
from string import ascii_letters


class SessionManager:
    def __init__(self):
        self.redis = Redis(env["REDIS_HOST"])

    def get(self):
        if "SUPER_SESSION_ID" in session.keys():
            res = self.redis.get("session:%s" % session["SUPER_SESSION_ID"])
            if res is None:
                self.create_new_session()
                return self.get()
            return loads(res)
        else:
            self.create_new_session()
            return self.get()

    def set(self, val):
        if "SUPER_SESSION_ID" in session.keys():
            self.redis.set("session:%s" % session["SUPER_SESSION_ID"], dumps(val), ex=60 * 60)  # Expire after 1 hour
        else:
            self.create_new_session()
            self.set(val)

    def create_new_session(self):
        token = "".join(choices(ascii_letters, k=20))
        self.redis.set("session:%s" % token, "{}", ex=60 * 60)  # Expire after 1 hour
        session["SUPER_SESSION_ID"] = token

    def __setitem__(self, key, value):
        data = self.get()
        data[key] = value
        self.set(data)

    def __getitem__(self, item):
        data = self.get()
        return data[item]

    def keys(self):
        return self.get().keys()
