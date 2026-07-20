import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Groq API key
    GROQ_API_KEY: str = os.getenv(
        "GROQ_API_KEY",
        ""
    )

    # Groq-hosted model
    MODEL_NAME: str = os.getenv(
        "MODEL_NAME",
        "llama-3.3-70b-versatile"
    )

    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL",
        "all-MiniLM-L6-v2"
    )

    CHROMA_PERSIST_DIR: str = os.getenv(
        "CHROMA_PERSIST_DIR",
        "./chroma_db"
    )

    CONFIDENCE_THRESHOLD: float = float(
        os.getenv("CONFIDENCE_THRESHOLD", "0.75")
    )

    LOG_LEVEL: str = os.getenv(
        "LOG_LEVEL",
        "INFO"
    )

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:1234@localhost:5432/digitalsofts"
    )


settings = Settings()

print("=" * 50)
print("API KEY:", settings.GROQ_API_KEY)
print("MODEL:", settings.MODEL_NAME)
print("=" * 50)