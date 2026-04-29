from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    project_root: Path
    backend_root: Path
    data_root: Path
    default_data_dir: Path
    users_data_dir: Path
    user_contracts_dir: Path
    qdrant_url: str
    qdrant_api_key: str | None
    qdrant_collection: str
    embedding_model: str
    ollama_url: str
    ollama_model: str


def _load_env_file() -> None:
    backend_env = Path(__file__).resolve().parents[1] / ".env"
    if backend_env.exists():
        load_dotenv(dotenv_path=backend_env, override=False)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    _load_env_file()

    project_root = Path(__file__).resolve().parents[2]
    backend_root = project_root / "backend"
    data_root = project_root / "data"
    default_data_dir = data_root / "default"
    users_data_dir = data_root / "users"
    user_contracts_dir = users_data_dir / "contracts"
    user_contracts_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        project_root=project_root,
        backend_root=backend_root,
        data_root=data_root,
        default_data_dir=default_data_dir,
        users_data_dir=users_data_dir,
        user_contracts_dir=user_contracts_dir,
        qdrant_url=os.getenv(
            "QDRANT_URL",
            "https://5d12e4e3-03ea-4848-b40c-a1ed6490a4c5.eu-central-1-0.aws.cloud.qdrant.io",
        ),
        qdrant_api_key=os.getenv("QDRANT_API_KEY"),
        qdrant_collection=os.getenv("QDRANT_COLLECTION", "contractlens_legal"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "law-ai/InLegalBERT"),
        ollama_url=os.getenv("OLLAMA_URL", "http://127.0.0.1:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2:latest"),
    )
