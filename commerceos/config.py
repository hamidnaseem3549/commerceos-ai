"""Central configuration — single source of truth for all settings."""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "qwen/qwen3-32b")
    fraud_llm_model: str = os.getenv("FRAUD_LLM_MODEL", "llama-3.3-70b-versatile")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///data/commerceos.db")
    store_name: str = "Urban Thread Co."
    tax_rate: float = 0.08
    low_stock_threshold_ratio: float = 1.0
    max_chat_history: int = 10

    @property
    def chroma_store_dir(self) -> str:
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "chroma_store"
        )

    @property
    def policy_file(self) -> str:
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "refund_policy.txt"
        )


settings = Settings()
