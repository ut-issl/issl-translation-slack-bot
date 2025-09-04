"""Main entry point for the ISSL Translation Slack Bot"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from .bot import TranslationBot

def setup_logging():
    """Setup logging configuration"""
    import os
    
    # ローカル実行時は ./logs/ に、systemd実行時は /var/log に
    if os.path.exists('/var/log') and os.access('/var/log', os.W_OK):
        log_file = '/var/log/issl-translation-bot.log'
    else:
        os.makedirs('logs', exist_ok=True)
        log_file = 'logs/issl-translation-bot.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, mode='a')
        ]
    )

async def async_main():
    """Async main function"""
    # Load environment variables (override existing ones)
    load_dotenv(override=True)
    
    # Validate required environment variables
    required_vars = ["SLACK_BOT_TOKEN", "SLACK_APP_TOKEN", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Initializing ISSL Translation Bot...")
    
    # Create and start the bot
    bot = TranslationBot()
    await bot.start()

def main():
    """Main entry point"""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Error starting bot: {e}")

if __name__ == "__main__":
    main()