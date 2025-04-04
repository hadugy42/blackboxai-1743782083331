import asyncio
import signal
from binance_handler import BinanceHandler
from telegram_handler import TelegramHandler
from order_manager import OrderManager
from logger import setup_logger

logger = setup_logger()

class TradingBot:
    def __init__(self):
        """Initialize the trading bot components."""
        self.binance_handler = BinanceHandler()
        self.order_manager = OrderManager(self.binance_handler)
        self.telegram_handler = TelegramHandler(self.handle_signal)
        self.is_running = False

    def handle_signal(self, signal_data):
        """Handle incoming trading signals from Telegram."""
        if self.is_running:
            # Create task to process signal asynchronously
            asyncio.create_task(self.order_manager.process_signal(signal_data))
        else:
            logger.warning("Bot is not running. Signal ignored.")

    async def start(self):
        """Start the trading bot."""
        try:
            # Connect to Binance websocket
            if not await self.binance_handler.connect_websocket():
                logger.error("Failed to connect to Binance websocket")
                return False

            # Subscribe to user data stream
            await self.binance_handler.subscribe_user_data()

            # Start Telegram bot
            self.telegram_handler.start()
            
            self.is_running = True
            logger.info("Trading bot started successfully")
            return True

        except Exception as e:
            logger.error(f"Error starting trading bot: {str(e)}")
            return False

    async def stop(self):
        """Stop the trading bot."""
        try:
            self.is_running = False
            
            # Stop Telegram bot
            self.telegram_handler.stop()
            
            # Close Binance websocket connection
            await self.binance_handler.close()
            
            logger.info("Trading bot stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping trading bot: {str(e)}")

async def main():
    """Main function to run the trading bot."""
    # Initialize the bot
    bot = TradingBot()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler():
        logger.info("Shutdown signal received")
        asyncio.create_task(bot.stop())
    
    # Register signal handlers
    for sig in (signal.SIGTERM, signal.SIGINT):
        asyncio.get_event_loop().add_signal_handler(
            sig,
            signal_handler
        )
    
    try:
        # Start the bot
        if await bot.start():
            # Keep the bot running
            while bot.is_running:
                await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Error in main loop: {str(e)}")
    finally:
        # Ensure proper shutdown
        await bot.stop()

if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())