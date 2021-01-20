from base import database
from random import choices
from string import ascii_letters, digits

bot_data = database["bot_data"]
bot_tokens = database["bot_tokens"]

# Inputs
bot_id = int(input("Bot id> "))
icon_url = input("Bot icon url> ")
bot_name = input("Bot name> ")
secret_key = "".join(choices(ascii_letters + digits, k=40))

# Inserting data
bot_data.insert_one({"_id": bot_id, "icon": icon_url, "name": bot_name})
bot_tokens.insert_one({"_id": bot_id, "token": secret_key})

# Output
print("Secret key: %s" % secret_key)

print("Ok.")
