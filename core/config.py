import os
import yaml
from dataclasses import dataclass

CONFIG_PATH = os.getenv("APP_CONFIG", "config.yaml")
cfg = yaml.safe_load(open(CONFIG_PATH, "r"))

@dataclass
class Settings:
    openai_model: str

    max_urls_per_task: int
    max_search_results: int
    max_search_excerpt_chars: int
    max_extract_chars: int

    max_evidence_items: int
    max_evidence_chars: int


def load_settings() -> Settings:
    return Settings(
        openai_model=os.getenv(
            "OPENAI_MODEL",
            cfg["models"]["openai"],
        ),

        max_urls_per_task=cfg["parallel"]["max_urls_per_task"],
        max_search_results=cfg["parallel"]["max_search_results"],
        max_search_excerpt_chars=cfg["parallel"]["max_search_excerpt_chars"],
        max_extract_chars=cfg["parallel"]["max_extract_chars"],

        max_evidence_items=cfg["evidence"]["max_items"],
        max_evidence_chars=cfg["evidence"]["max_chars"],
    )


class ParallelConfig:
    API_KEY = os.environ["PARALLEL_API_KEY"]
    BETA_VERSION = cfg["parallel"]["beta_version"]
    BETAS = [BETA_VERSION]


class OpenAIConfig:
    API_KEY = os.environ["OPENAI_API_KEY"]
    MODEL = os.getenv("OPENAI_MODEL", cfg["models"]["openai"])