import os

# VECTOR DATABASE
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
# QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "my_documents")

# EMBEDDING MODEL
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

# LLM MODEL
# GEMINI
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
GOOGLE_API_KEY= os.getenv("GOOGLE_API_KEY", "AIzaSyAQXdw5stmzgpq9W7UAe32kAss_CLd_XUY")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-secret")
JWT_ALGORITHM = "HS256"

# DATABASE MYSQL
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_DATABASE", "mydatabase")
DB_USER = os.getenv("DB_USERNAME", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

# OPENROUTER
BASE_URL_OPEN_ROUTER = os.getenv("BASE_URL_OPEN_ROUTER", "https://openrouter.ai/api/v1")
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "ChatBudgeting")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "your-openrouter-api-key")