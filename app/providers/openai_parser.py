from openai import OpenAI

from app.config import LLMConfig
from app.domain.intent import ParsedEngineeringIntent
from app.parsers.base import EngineeringParser
from app.providers.prompt import SYSTEM_PROMPT


class OpenAIEngineeringParser(EngineeringParser):
    """
    Cloud reference adapter for v0.2.2.

    The model may produce only ParsedEngineeringIntent.
    It never produces EngineeringSpec and therefore has no authority
    to create DERIVED engineering values.
    """

    def __init__(
        self,
        config: LLMConfig | None = None,
        client: OpenAI | None = None,
    ):
        self.config = config or LLMConfig()
        self.client = client or OpenAI(
            timeout=self.config.timeout_seconds,
            max_retries=self.config.max_retries,
        )

    def parse(self, prompt: str) -> ParsedEngineeringIntent:
        response = self.client.responses.parse(
            model=self.config.model,
            instructions=SYSTEM_PROMPT,
            input=prompt,
            store=False,
            text_format=ParsedEngineeringIntent,
        )

        parsed = response.output_parsed
        if parsed is None:
            raise RuntimeError(
                "LLM returned no parsed engineering intent. "
                "Inspect the full response for refusal or incomplete output."
            )

        return parsed
