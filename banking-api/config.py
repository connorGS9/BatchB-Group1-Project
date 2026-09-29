import os
from dotenv import load_dotenv

load_dotenv()
PORT = 8000
HOST = "0.0.0.0"
DEBUG = True

MONGO_URL = os.environ["MONGO_URL"]          # KeyError on startup if not set; better than a silent default
MONGO_DB = os.getenv("MONGO_DB", "banking")  # a db name isn't secret, so a default is fine
