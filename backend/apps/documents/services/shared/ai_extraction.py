"""
AI-powered document extraction utilities.
Shared functions for GPT Vision API calls.
"""

import json
import logging
from typing import Dict, List, Optional

from ..processors.base import get_openai_client, encode_image, get_mime_type

logger = logging.getLogger(__name__)


def extract_with_vision_api(
    image_path: str,
    prompt: str,
    text_context: Optional[str] = None,
    model: str = "gpt-5",
    temperature: float = 0.1,
    max_output_tokens: int = 2000
) -> Dict:
    """
    Extract structured data from document image using GPT Vision API.

    Args:
        image_path: Path to image file
        prompt: Extraction prompt for AI
        text_context: Optional text context from OCR
        model: OpenAI model to use
        temperature: Temperature for API call
        max_output_tokens: Maximum tokens in response

    Returns:
        Extracted data as dictionary

    Raises:
        RuntimeError: If extraction fails
    """
    logger.info(f"Calling OpenAI Vision API for document extraction")

    # Encode image
    base64_image = encode_image(image_path)
    mime_type = get_mime_type(image_path)

    # Build prompt with optional context
    full_prompt = prompt
    if text_context:
        full_prompt = f"{prompt}\n\n**Text Context:**\n{text_context[:1000]}"

    try:
        # Call OpenAI Response API
        response = get_openai_client().responses.create(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": full_prompt},
                        {
                            "type": "input_image",
                            "image_url": f"data:{mime_type};base64,{base64_image}"
                        }
                    ]
                }
            ],
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_format={"type": "json_object"}
        )

        # Extract JSON from response
        raw_json = _extract_response_text(response)

        if not raw_json:
            raise RuntimeError("OpenAI Response API returned no text output")

        extracted_data = json.loads(raw_json)
        logger.info("Successfully extracted document data via Vision API")
        return extracted_data

    except json.JSONDecodeError as e:
        logger.exception(f"Failed to parse JSON response")
        raise RuntimeError(f"Invalid JSON in API response") from e

    except Exception as e:
        logger.exception(f"Openai API extraction failed")
        raise RuntimeError(f"Failed to extract document data") from e


def _extract_response_text(response) -> Optional[str]:
    """
    Extract text from OpenAI Response API response.
    Handles multiple response formats.
    """
    # Try output_text attribute
    if hasattr(response, "output_text") and response.output_text:
        return response.output_text

    # Try output array
    if hasattr(response, "output"):
        try:
            return response.output[0].content[0].text
        except (IndexError, AttributeError):
            pass

    # Try choices array (fallback for Chat Completions format)
    if hasattr(response, "choices"):
        try:
            return response.choices[0].message.content
        except (IndexError, AttributeError):
            pass

    return None
