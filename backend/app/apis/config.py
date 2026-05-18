from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Fetch variables

DATABASE_URL = os.getenv("DATABASE_URL","")


class Setting:
    def __init__(self):
        self.PROJECT_NAME = "AI-Assisted-Smart-Job-Outreach-System"
        self.PROJECT_VERSION = "1.0.0"
        self.PROJECT_DESCRIPTION = "AI-Assisted-Smart-Job-Outreach-System"
        self.SECRET_KEY: str = "c7680bd1c30fd6663180ad944cc8155495127783a4c89caaccf9b9231ce4fd00"
        self.ALGORITHM: str = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = 30      
        self.REFRESH_TOKEN_EXPIRE_DAYS: int = 7         
        self.ROTATE_REFRESH_TOKENS: bool = False        
        self.ENABLE_TOKEN_BLOCKLIST: bool = False
        self.DATABASE_URL: str = DATABASE_URL 
        self.DEBUG: bool = True

    def get_settings(self):
        return self

settings = Setting() 