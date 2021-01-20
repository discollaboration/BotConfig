from pymongo import MongoClient
from os import environ as env

client = MongoClient(env["MONGO_URI"])
database = client["BotConfig"]
