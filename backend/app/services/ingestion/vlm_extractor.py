"""VLM-based extraction using Ollama for classification, summary, entities."""

import json
import logging
from typing import Optional

from app.services.llm.provider import llm_provider
from app.services.llm.prompts import (
    CLASSIFY_DOCUMENT, EXTRACT_PROJECT_NAME, STRUCTURED_SUMMARY,
    EXTRACT_ENTITIES, EXTRACT_DRAWING_TAGS
)

logger = logging.getLogger(__name__)


class VLMExtractor:
    """Use Ollama vision/text model for intelligent extraction."""

    async def classify_document(self, text: str) -> str:
        """Classify document type."""
        prompt = CLASSIFY_DOCUMENT.format(text=text[:2000])
        try:
            result = await llm_provider.generate(prompt)
            doc_type = result.strip().lower()
            valid_types = ["manual", "pid", "spec", "logbook", "drawing", "report", "other"]
            return doc_type if doc_type in valid_types else "other"
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return "other"

    async def extract_project_name(self, text: str) -> str:
        """Extract project/plant name."""
        prompt = EXTRACT_PROJECT_NAME.format(text=text[:3000])
        try:
            result = await llm_provider.generate(prompt)
            return result.strip() or "Unknown"
        except Exception as e:
            logger.error(f"Project name extraction failed: {e}")
            return "Unknown"

    async def extract_structured_summary(self, text: str) -> dict:
        """Extract structured summary as JSON."""
        prompt = STRUCTURED_SUMMARY.format(text=text[:4000])
        try:
            result = await llm_provider.generate(prompt)
            # Try to parse JSON from response
            return self._parse_json(result)
        except Exception as e:
            logger.error(f"Summary extraction failed: {e}")
            return {}

    async def extract_entities(self, text: str) -> list[dict]:
        """Extract engineering entities from text."""
        prompt = EXTRACT_ENTITIES.format(text=text[:3000])
        try:
            result = await llm_provider.generate(prompt)
            entities = self._parse_json_array(result)
            return entities
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []

    async def extract_drawing_tags(self, image_base64: str) -> list[dict]:
        """Extract tags from a drawing/P&ID image using vision model."""
        try:
            result = await llm_provider.generate(
                prompt=EXTRACT_DRAWING_TAGS,
                images=[image_base64]
            )
            return self._parse_json_array(result)
        except Exception as e:
            logger.error(f"Drawing tag extraction failed: {e}")
            return []

    def _parse_json(self, text: str) -> dict:
        """Parse JSON from LLM output, handling markdown code blocks."""
        text = text.strip()
        # Remove markdown code block if present
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON object in the text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            logger.warning(f"Failed to parse JSON: {text[:200]}")
            return {}

    def _parse_json_array(self, text: str) -> list[dict]:
        """Parse JSON array from LLM output."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        try:
            result = json.loads(text)
            return result if isinstance(result, list) else []
        except json.JSONDecodeError:
            start = text.find("[")
            end = text.rfind("]") + 1
            if start >= 0 and end > start:
                try:
                    result = json.loads(text[start:end])
                    return result if isinstance(result, list) else []
                except json.JSONDecodeError:
                    pass
            logger.warning(f"Failed to parse JSON array: {text[:200]}")
            return []


vlm_extractor = VLMExtractor()
