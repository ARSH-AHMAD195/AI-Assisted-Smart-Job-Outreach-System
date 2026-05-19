import os
from dotenv import load_dotenv

load_dotenv()
print("DATABASE_URL in env:", os.getenv("DATABASE_URL"))
