import os
from openai import OpenAI

class OpenAIClient:
    def __init__(self, model: str):
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = model

    def complete(self, system: str, user: str) -> str:
        resp = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return (resp.output_text or "").strip()