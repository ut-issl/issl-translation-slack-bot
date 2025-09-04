"""Slack bot implementation for translation service"""

import asyncio
import logging
import os
from typing import Dict, Any

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from .translator import TranslationService

logger = logging.getLogger(__name__)


class TranslationBot:
    """Slack bot that handles translation reactions"""

    def __init__(self):
        self.app = AsyncApp(token=os.getenv("SLACK_BOT_TOKEN"))
        self.translator = TranslationService()
        
        # Configuration
        self.translation_emoji = os.getenv("TRANSLATION_EMOJI", "english-japanese-translation")
        self.processing_emoji = os.getenv("PROCESSING_EMOJI", "eyes")
        
        self.setup_handlers()

    def setup_handlers(self):
        """Setup event handlers for the bot"""
        
        @self.app.event("reaction_added")
        async def handle_reaction_added(event: Dict[str, Any], client):
            """Handle when a reaction is added to a message"""
            try:
                # Check if it's our translation emoji
                if event.get("reaction") != self.translation_emoji:
                    return

                # Get message details
                channel = event["item"]["channel"]
                ts = event["item"]["ts"]
                user = event.get("user", "unknown")
                
                # Add processing reaction
                await client.reactions_add(
                    channel=channel,
                    timestamp=ts,
                    name=self.processing_emoji
                )
                
                # Get the specific message by timestamp
                result = await client.conversations_history(
                    channel=channel,
                    oldest=ts,
                    latest=ts,
                    limit=1,
                    inclusive=True
                )
                
                if not result["messages"] or result["messages"][0].get("ts") != ts:
                    # Fallback: try to find the message in recent history
                    result = await client.conversations_history(
                        channel=channel,
                        limit=100
                    )
                    messages = [msg for msg in result.get("messages", []) if msg.get("ts") == ts]
                    if not messages:
                        return
                    message = messages[0]
                else:
                    message = result["messages"][0]
                text = message.get("text", "")
                
                if not text:
                    return
                
                # Translate the text
                translation = await self.translator.translate(text)
                
                # Format text for logging
                text_log = text.replace('\n', '\\n')
                translation_log = translation.replace('\n', '\\n')
                logger.info(f"[{user}@{channel}] '{text_log}' -> '{translation_log}'")
                
                # Post translation in thread
                thread_ts = message.get("thread_ts") or ts
                await client.chat_postMessage(
                    channel=channel,
                    thread_ts=thread_ts,
                    text=translation
                )
                
                # Remove processing reaction
                await client.reactions_remove(
                    channel=channel,
                    timestamp=ts,
                    name=self.processing_emoji
                )
                
            except Exception as e:
                logger.error(f"Error handling reaction: {e}")
                try:
                    await client.reactions_remove(
                        channel=channel,
                        timestamp=ts,
                        name=self.processing_emoji
                    )
                except:
                    pass

    async def start(self):
        """Start the bot"""
        handler = AsyncSocketModeHandler(self.app, os.getenv("SLACK_APP_TOKEN"))
        logger.info("Starting ISSL Translation Bot...")
        await handler.start_async()