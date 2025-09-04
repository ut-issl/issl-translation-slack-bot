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
                
                # Note: item_user contains original message author if needed
                
                # Add processing reaction (ignore if already exists)
                try:
                    await client.reactions_add(
                        channel=channel,
                        timestamp=ts,
                        name=self.processing_emoji
                    )
                except Exception as e:
                    if "already_reacted" not in str(e):
                        logger.warning(f"Could not add processing reaction: {e}")
                    # Continue processing regardless
                
                # Try to get message - check both main messages and thread replies
                message = None
                
                # First try: main messages
                try:
                    result = await client.conversations_history(
                        channel=channel,
                        limit=50
                    )
                    messages = [msg for msg in result.get("messages", []) if msg.get("ts") == ts]
                    if messages:
                        message = messages[0]
                except Exception as e:
                    logger.warning(f"Main message search failed: {e}")
                
                # Second try: check if it's in a thread using conversations.replies directly
                if not message:
                    try:
                        # Try conversations.replies - if ts is in any thread, this will return the full thread
                        replies_result = await client.conversations_replies(
                            channel=channel,
                            ts=ts
                        )
                        
                        # Find our specific message in the thread
                        for reply in replies_result.get("messages", []):
                            if reply.get("ts") == ts:
                                message = reply
                                break
                            
                    except Exception as e:
                        logger.warning(f"conversations.replies failed: {e}")
                
                if not message:
                    logger.warning(f"Message not found for ts={ts}, skipping")
                    return
                    
                text = message.get("text", "")
                
                # Collect text from attachments as well
                attachments = message.get("attachments", [])
                attachment_texts = []
                if attachments:
                    for attachment in attachments:
                        # Get title and text from attachment
                        title = attachment.get("title", "")
                        att_text = attachment.get("text", "")
                        fallback = attachment.get("fallback", "")
                        
                        if title:
                            attachment_texts.append(title)
                        if att_text:
                            attachment_texts.append(att_text)
                        elif fallback:
                            attachment_texts.append(fallback)
                
                # Combine main text and attachment texts
                all_texts = []
                if text.strip():
                    all_texts.append(text)
                if attachment_texts:
                    all_texts.extend(attachment_texts)
                
                if not all_texts:
                    # Debug: check what type of message this is
                    msg_type = message.get("type", "unknown")
                    subtype = message.get("subtype", "none")
                    logger.warning(f"No translatable text found - type: {msg_type}, subtype: {subtype}")
                    return
                
                # Join all text content
                text = "\n".join(all_texts)
                
                # Translate the text
                translation = await self.translator.translate(text)
                
                # Check if translation is empty or just whitespace
                if not translation or not translation.strip():
                    translation = "翻訳できませんでした / Translation failed"
                
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
                try:
                    await client.reactions_remove(
                        channel=channel,
                        timestamp=ts,
                        name=self.processing_emoji
                    )
                except Exception as e:
                    logger.warning(f"Could not remove processing reaction: {e}")
                
            except Exception as e:
                logger.error(f"Error handling reaction: {e}")
                # Always try to remove processing reaction on error
                try:
                    await client.reactions_remove(
                        channel=channel,
                        timestamp=ts,
                        name=self.processing_emoji
                    )
                except Exception as cleanup_error:
                    logger.error(f"Failed to remove processing reaction: {cleanup_error}")

    async def start(self):
        """Start the bot"""
        handler = AsyncSocketModeHandler(self.app, os.getenv("SLACK_APP_TOKEN"))
        logger.info("Starting ISSL Translation Bot...")
        await handler.start_async()