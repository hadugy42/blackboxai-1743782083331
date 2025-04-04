# Binance Futures Trading Bot

A Python-based trading bot that automatically executes Binance Futures trades based on signals received from a Telegram channel. The bot creates stop market entry orders and manages associated stop-loss and take-profit orders.

## Features

- Connects to a specified Telegram channel to receive trading signals
- Creates STOP MARKET entry orders on Binance Futures
- Automatically sets stop-loss and take-profit orders when entry order is filled
- Uses websocket connections for real-time order status monitoring
- Implements proper order binding (stop-loss/take-profit orders are canceled when one is triggered)
- Comprehensive error handling and logging

## Prerequisites

- Python 3.7+
- Binance Futures account with API access
- Telegram bot token and channel access

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd binance-futures-bot
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your configuration:
```env
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Binance Configuration
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret
BINANCE_TESTNET=True  # Set to False for live trading

# Trading Configuration
ORDER_QUANTITY=0.001
MAX_RETRIES=3
RETRY_DELAY=5
```

## Usage

1. Start the bot:
```bash
python main.py
```

2. Send signals to your Telegram channel in the following format:
```
SIGNAL
Symbol: BTCUSDT
Entry: 50000
Stop Loss: 49000
Take Profit: 52000
```

## Signal Format

The bot expects signals in the following format:
- Must contain the word "SIGNAL"
- Symbol: Trading pair (e.g., BTCUSDT)
- Entry: Price to enter the trade
- Stop Loss: Price to exit if trade goes against you
- Take Profit: Price to exit with profit

## Project Structure

- `main.py`: Entry point of the application
- `config.py`: Configuration loading and management
- `logger.py`: Logging setup and configuration
- `binance_handler.py`: Binance API interactions and websocket management
- `telegram_handler.py`: Telegram bot setup and signal parsing
- `order_manager.py`: Trade execution and order management logic

## Error Handling

The bot includes comprehensive error handling:
- Automatic reconnection for websocket disconnections
- Retry mechanism for failed API calls
- Detailed logging of all operations and errors
- Graceful shutdown on system interrupts

## Logging

Logs are stored in the `logs` directory with the following format:
- Console: INFO level and above
- File: DEBUG level and above
- Filename format: `bot_YYYYMMDD.log`

## Important Notes

1. Always test with BINANCE_TESTNET=True first
2. Ensure sufficient funds in your Binance Futures account
3. Double-check API permissions (Futures trading enabled)
4. Verify Telegram bot permissions and channel access
5. Monitor the logs for any issues or errors

## Security Considerations

- Never share your API keys or .env file
- Use API keys with minimum required permissions
- Regularly monitor the bot's activities
- Keep your Python packages updated

## License

This project is licensed under the MIT License - see the LICENSE file for details.