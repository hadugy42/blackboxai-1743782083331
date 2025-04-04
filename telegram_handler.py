from telegram.ext import Updater, MessageHandler, Filters
import re
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from logger import setup_logger

logger = setup_logger()

class TelegramHandler:
    def __init__(self, signal_callback):
        """Initialize the Telegram handler with a callback for processing signals."""
        self.updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.signal_callback = signal_callback

    def parse_signal(self, message_text: str) -> dict:
        """
        Parse the signal message to extract trading information.
        Expected format example:
        SIGNAL
        Symbol: BTCUSDT
        Entry: 50000
        Stop Loss: 49000
        Take Profit: 52000
        """
        try:
            # Extract information using regex
            symbol_match = re.search(r'Symbol:\s*(\w+)', message_text)
            entry_match = re.search(r'Entry:\s*(\d+\.?\d*)', message_text)
            sl_match = re.search(r'Stop Loss:\s*(\d+\.?\d*)', message_text)
            tp_match = re.search(r'Take Profit:\s*(\d+\.?\d*)', message_text)

            if not all([symbol_match, entry_match, sl_match, tp_match]):
                logger.warning(f"Invalid signal format: {message_text}")
                return None

            signal_data = {
                'symbol': symbol_match.group(1),
                'entry_price': float(entry_match.group(1)),
                'stop_loss': float(sl_match.group(1)),
                'take_profit': float(tp_match.group(1))
            }

            logger.info(f"Successfully parsed signal: {signal_data}")
            return signal_data

        except Exception as e:
            logger.error(f"Error parsing signal: {str(e)}")
            return None

    def handle_message(self, update, context):
        """Handle incoming messages from Telegram."""
        try:
            # Check if message is from the configured chat
            if str(update.message.chat_id) != str(TELEGRAM_CHAT_ID):
                return

            message_text = update.message.text
            
            # Check if message contains "SIGNAL"
            if "SIGNAL" not in message_text.upper():
                return

            # Parse the signal
            signal_data = self.parse_signal(message_text)
            
            if signal_data:
                # Process the signal using the callback
                self.signal_callback(signal_data)
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")

    def start(self):
        """Start the Telegram bot."""
        try:
            # Add message handler
            self.dispatcher.add_handler(
                MessageHandler(Filters.text & ~Filters.command, self.handle_message)
            )
            
            # Start the bot
            self.updater.start_polling()
            logger.info("Telegram bot started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {str(e)}")
            raise

    def stop(self):
        """Stop the Telegram bot."""
        self.updater.stop()
        logger.info("Telegram bot stopped")