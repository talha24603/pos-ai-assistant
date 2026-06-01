# from dotenv import load_dotenv
# import os

# load_dotenv()

# DATABASE_URL = os.getenv("DATABASE_URL")
# SECRET_KEY = os.getenv("SECRET_KEY")
from dotenv import load_dotenv
import os

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
SQL_AGENT_DATABASE_URL = os.getenv(
    "SQL_AGENT_DATABASE_URL"
)

RAG_DATABASE_URL = os.getenv(
    "RAG_DATABASE_URL"
)