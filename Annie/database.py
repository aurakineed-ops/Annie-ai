from pymongo import MongoClient
import certifi
from Annie.config import MONGO_URI

# Initialize MongoDB Connection (Atlas / SSL)
ANNIE = MongoClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where()
)

# Select Database
db = ANNIE["ANNIEbot_db"]

# --- DEFINING COLLECTIONS ---
users_collection = db["users"]        # Stores balance, inventory, waifus, stats
groups_collection = db["groups"]      # Tracks group settings (welcome, claim status)
sudoers_collection = db["sudoers"]    # Stores admin IDs
chatbot_collection = db["chatbot"]    # Stores AI chat history per group/user
riddles_collection = db["riddles"]    # Stores active riddles and answers
