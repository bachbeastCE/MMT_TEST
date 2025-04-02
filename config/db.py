from pymongo.mongo_client import MongoClient # type: ignore

uri = "mongodb+srv://admin1:cn242@cluster0.fum1o.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(uri)
db = client["user_database"]
def get_collection(collection_name):
    return db[collection_name]

users_collection = get_collection("users")
channels_collection = get_collection("channels")

try:
    client.admin.command("ping")
    print("Connected to MongoDB successfully!")
except Exception as e:
    print("MongoDB connection error:", e)