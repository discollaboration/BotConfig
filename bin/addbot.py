from base import database

table = database["bot_data"]

bot_id = int(input("Bot id> "))
icon_url = input("Bot icon url> ")
bot_name = input("Bot name> ")

table.insert_one({"_id": bot_id, "icon": icon_url, "name": bot_name})
print("Ok.")
