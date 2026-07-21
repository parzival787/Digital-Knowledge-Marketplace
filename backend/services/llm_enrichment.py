import asyncio
import json
import os

from openai import AsyncOpenAI

client = AsyncOpenAI(
    base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
    api_key="ollama",
)

SYSTEM_PROMPT  = """
You are a knowledge asset cataloguing specialist for a data marketplace.

Given document text, analyze it and return ONLY a valid JSON object with exactly these fields:

{
  "title": "descriptive title for this dataset or document, max 80 characters",
  "summary": "plain English description of what this data contains, max 200 characters",
  "tags": ["lowercase", "relevant", "topic"],
  "domain": "science|finance|healthcare|technology|social|agriculture|environment|other",
  "quality_score": 0.75,
  "recommended_price_usdc": 5
}

Rules:
- Return ONLY JSON.
- No explanation.
- No markdown.
- quality_score must be between 0.0 and 1.0.
"""

async def enrich_document(text: str) -> dict:
    for attempt in range(3):
        try:
            response = await client.chat.completions.create(
                model="llama3.2:3b",
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this document:\n\n{text[:4000]}",
                    },
                ],
                temperature=0.1,
                max_tokens=400,
            )

            raw = response.choices[0].message.content.strip()

            # Remove markdown code fences if present
            if "```" in raw:
                parts = raw.split("```")
                for part in parts:
                    cleaned = part.strip()

                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:].strip()

                    if cleaned.startswith("{"):
                        raw = cleaned
                        break

            metadata = json.loads(raw)

            required = [
                "title",
                "summary",
                "tags",
                "domain",
                "quality_score",
            ]

            for field in required:
                if field not in metadata:
                    raise ValueError(f"Missing field: {field}")

            metadata["quality_score"] = max(
                0.0,
                min(
                    1.0,
                    float(metadata["quality_score"]),
                ),
            )

            metadata["tags"] = [
                str(tag).lower().strip()
                for tag in metadata.get("tags", [])
            ][:10]

            metadata["recommended_price_usdc"] = int(
                metadata.get("recommended_price_usdc", 5)
            )

            valid_domains = [
                "science",
                "finance",
                "healthcare",
                "technology",
                "social",
                "agriculture",
                "environment",
                "other",
            ]

            if metadata["domain"] not in valid_domains:
                metadata["domain"] = "other"

            return metadata

        except json.JSONDecodeError:
            if attempt == 2:
                return {
                    "title": "Untitled Document",
                    "summary": text[:150].replace("\n", " "),
                    "tags": [],
                    "domain": "other",
                    "quality_score": 0.5,
                    "recommended_price_usdc": 5,
                }

            await asyncio.sleep(1)

        except Exception:
            if attempt == 2:
                raise

            await asyncio.sleep(2 ** attempt)