import json
import boto3
from app.config import settings


class BedrockClient:
    def __init__(self):
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=settings.BEDROCK_REGION,
        )
        self.model_id = settings.BEDROCK_MODEL_ID

    async def invoke(self, prompt: str, system: str, max_tokens: int = 4096) -> str:
        """Invoke Claude via Amazon Bedrock."""
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        })

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=body,
            contentType="application/json",
            accept="application/json",
        )

        response_body = json.loads(response["body"].read())
        return response_body["content"][0]["text"]

    async def invoke_json(self, prompt: str, system: str, max_tokens: int = 4096) -> dict:
        """Invoke Claude and parse JSON response."""
        text = await self.invoke(prompt, system, max_tokens)
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return json.loads(text.strip())


# Singleton
bedrock_client = BedrockClient()
