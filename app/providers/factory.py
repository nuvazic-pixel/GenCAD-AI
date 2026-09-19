from app.config import LLMConfig
from app.parsers.base import EngineeringParser
from app.providers.openai_parser import OpenAIEngineeringParser


def build_parser(config: LLMConfig | None = None) -> EngineeringParser:
    config = config or LLMConfig()

    if config.provider == "openai":
        return OpenAIEngineeringParser(config=config)

    raise ValueError(
        f"Unsupported provider: {config.provider}. "
        "The interface is provider-neutral; add another adapter without changing the pipeline."
    )
