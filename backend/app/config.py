from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # LLM
    llm_model_name: str = "qwen3:4b"
    llm_base_url: str = "http://172.22.80.1:11434/v1"
    llm_api_key: str = "ollama"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    # MySQL
    mysql_host: str = "localhost"
    mysql_port: int = 3307
    mysql_user: str = "kgqa"
    mysql_password: str = ""
    mysql_database: str = "general_kg_qa"

    # Embedding
    embedding_model: str = "bge-m3"
    embedding_base_url: str = "http://172.22.80.1:11434"

    # Milvus
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection: str = "kgqa_documents"

    # JWT
    jwt_secret_key: str = "change-me-to-a-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
