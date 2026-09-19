from dataclasses import dataclass
import os


@dataclass(frozen=True)
class LLMConfig:
    provider: str = os.getenv("GENCAD_LLM_PROVIDER", "openai")
    model: str = os.getenv("GENCAD_LLM_MODEL", "gpt-5.6-sol")
    timeout_seconds: float = float(os.getenv("GENCAD_LLM_TIMEOUT", "30"))
    max_retries: int = int(os.getenv("GENCAD_LLM_MAX_RETRIES", "1"))
