# from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import certifi

# MONGO_URI = "mongodb://localhost:27017"
# DB_NAME = "paying_app"

# client = AsyncIOMotorClient(MONGO_URI)
# db = client["paying_app"]

# client = MongoClient("mongodb://localhost:27017")
# db = client["paying_app"]
MONGO_URI = "mongodb+srv://nells4all_db_user:pO88cNjQRzAGAP8i@paying-app.7to4kcg.mongodb.net/paying-app?retryWrites=true&w=majority&appName=paying-app"

client = MongoClient(MONGO_URI,  tlsCAFile=certifi.where(), server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client["paying-app"]

wallets_collection = db["wallets"]
transactions_collection = db["transactions"]
users_collection = db["users"]

password = "pO88cNjQRzAGAP8i"
user= "nells4all_db_user"
# mongodb+srv://nells4all_db_user:pO88cNjQRzAGAP8i@paying-app.7to4kcg.mongodb.net/?appName=paying-app




