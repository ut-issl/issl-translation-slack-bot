"""Translation service using OpenAI GPT-4o-mini"""

import os
import re
from typing import Optional

from openai import AsyncOpenAI


class TranslationService:
    """Handles translation between English and Japanese using OpenAI"""

    def __init__(self, api_key: Optional[str] = None):
        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    async def detect_language(self, text: str) -> str:
        """Detect if text is primarily Japanese or English using GPT"""
        if not text.strip():
            return "en"
            
        try:
            response = await self.client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": "You are a language detector. Reply with only 'ja' for Japanese text or 'en' for English text. No explanations."},
                    {"role": "user", "content": text}
                ],
                max_completion_tokens=10
            )
            
            result = response.choices[0].message.content.strip().lower()
            return "ja" if result == "ja" else "en"
        except Exception:
            # Fallback to simple detection
            japanese_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text))
            total_chars = len(text.strip())
            japanese_ratio = japanese_chars / total_chars if total_chars > 0 else 0
            return "ja" if japanese_ratio > 0.3 else "en"

    async def translate(self, text: str) -> str:
        """Translate text between English and Japanese"""
        if not text.strip():
            return ""

        system_prompt = """You are a professional translator specializing in English-Japanese translation.

LANGUAGE DETECTION & TRANSLATION RULES:
1. If the input contains ANY Japanese characters (ひらがな、カタカナ、漢字), translate to English
2. If the input is entirely in Latin alphabet, translate to Japanese
3. For mixed language text, translate the primary language to the other
4. If text already contains both Japanese and English equally, respond with "翻訳不要 / Translation not needed"

TRANSLATION GUIDELINES:
- Translate naturally, preserving tone and context
- Keep technical terms, names, URLs, and code as-is
- For unclear technical terms, add ※ note at the end
- Maintain original formatting (line breaks, etc.)

EXAMPLES:
Input: "Hello" → Output: "こんにちは"
Input: "こんにちは" → Output: "Hello"  
Input: "Deploy the API" → Output: "APIをデプロイする"
Input: "APIをデプロイする" → Output: "Deploy the API"
Input: "こんにちは Hello" → Output: "翻訳不要 / Translation not needed"

Return ONLY the translated text or "翻訳不要 / Translation not needed"."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                max_completion_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Translation error: {str(e)}"