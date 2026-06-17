from pymongo import MongoClient
import certifi

uri = "mongodb+srv://nells4all_db_user:pO88cNjQRzAGAP8i@paying-app.7to4kcg.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(
    uri,
    tls=True,
    tlsCAFile=certifi.where(),
)

try:
    print(client.admin.command("ping"))
    print("CONNECTED SUCCESSFULLY")
except Exception as e:
    print("FAILED")
    print(e)