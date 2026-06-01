# from dotenv import load_dotenv
# import os

# load_dotenv()

# DATABASE_URL = os.getenv("DATABASE_URL")
# SECRET_KEY = os.getenv("SECRET_KEY")
from dotenv import load_dotenv
import os

load_dotenv(override=True)
SECRET_KEY = os.getenv("SECRET_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "openai/text-embedding-3-small")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))

SQL_AGENT_DATABASE_URL = os.getenv(
    "SQL_AGENT_DATABASE_URL"
)

RAG_DATABASE_URL = os.getenv(
    "RAG_DATABASE_URL"
)