from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]

# Preset API bases for OpenAI-compatible providers (no trailing slash).
_DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"
_QWEN_COMPAT_API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM — OpenAI 官方，或 DeepSeek / 通义千问（DashScope 兼容模式）等 OpenAI-compatible 端点
    # LLM_PROVIDER: openai | deepseek | qwen | custom
    #   custom: 必须设置 OPENAI_API_BASE
    llm_provider: Literal["openai", "deepseek", "qwen", "custom"] = "openai"
    openai_api_key: str = ""
    openai_api_base: str = ""
    openai_model: str = "gpt-4o"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Milvus
    milvus_host: str = "localhost"
    milvus_port: int = 19530

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # LangSmith
    langsmith_api_key: str = ""
    langsmith_project: str = "fashion-agent"
    langchain_tracing_v2: bool = False

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # Data
    seed_data_dir: str = str(ROOT_DIR / "data" / "seed")

    @field_validator("llm_provider", mode="before")
    @classmethod
    def _normalize_llm_provider(cls, v: object) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return str(v) if v is not None else "openai"

    @property
    def resolved_openai_api_base(self) -> str | None:
        """Base URL for OpenAI-compatible HTTP APIs, or ``None`` for default OpenAI host."""
        explicit = (self.openai_api_base or "").strip().rstrip("/")
        if explicit:
            return explicit
        p = (self.llm_provider or "openai").lower()
        if p == "deepseek":
            return _DEEPSEEK_API_BASE
        if p == "qwen":
            return _QWEN_COMPAT_API_BASE
        return None

    @property
    def has_llm(self) -> bool:
        return bool(self.openai_api_key and self.openai_api_key != "sk-xxx")

    @property
    def has_openai(self) -> bool:
        """Backward-compatible alias: any configured OpenAI-compatible key counts."""
        return self.has_llm

    @property
    def has_langsmith(self) -> bool:
        return bool(self.langsmith_api_key and self.langsmith_api_key != "ls-xxx")


@lru_cache
def get_settings() -> Settings:
    return Settings()
