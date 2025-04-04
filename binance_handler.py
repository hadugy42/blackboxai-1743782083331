from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException
import websockets
import json
import asyncio
from config import (
    BINANCE_API_KEY,
    BINANCE_API_SECRET,
    BINANCE_TESTNET,
    BINANCE_WS_ENDPOINT,
    MAX_RETRIES,
    RETRY_DELAY
)
from logger import setup_logger

logger = setup_logger()

class BinanceHandler:
    def __init__(self):
        self.client = Client(
            BINANCE_API_KEY,
            BINANCE_API_SECRET,
            testnet=BINANCE_TESTNET
        )
        self.ws = None
        self.active_orders = {}
        
    async def connect_websocket(self):
        """Establish websocket connection with Binance."""
        try:
            self.ws = await websockets.connect(BINANCE_WS_ENDPOINT)
            logger.info("Successfully connected to Binance websocket")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to websocket: {str(e)}")
            return False

    async def subscribe_user_data(self):
        """Subscribe to user data stream for order updates."""
        try:
            # Get listen key for user data stream
            listen_key = self.client.futures_stream_get_listen_key()
            
            # Subscribe to user data stream
            subscribe_message = {
                "method": "SUBSCRIBE",
                "params": [f"{listen_key}"],
                "id": 1
            }
            await self.ws.send(json.dumps(subscribe_message))
            logger.info("Successfully subscribed to user data stream")
        except Exception as e:
            logger.error(f"Failed to subscribe to user data stream: {str(e)}")

    async def create_stop_market_order(self, symbol: str, entry_price: float, quantity: float):
        """Create a stop market order for entry."""
        for _ in range(MAX_RETRIES):
            try:
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side=SIDE_BUY,
                    type=FUTURE_ORDER_TYPE_STOP_MARKET,
                    quantity=quantity,
                    stopPrice=entry_price
                )
                logger.info(f"Successfully created stop market order: {order}")
                return order
            except BinanceAPIException as e:
                logger.error(f"Binance API error creating stop market order: {str(e)}")
                await asyncio.sleep(RETRY_DELAY)
            except Exception as e:
                logger.error(f"Unexpected error creating stop market order: {str(e)}")
                await asyncio.sleep(RETRY_DELAY)
        return None

    async def create_stoploss_order(self, symbol: str, stop_loss_price: float, quantity: float):
        """Create a stop loss order."""
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=SIDE_SELL,
                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                quantity=quantity,
                stopPrice=stop_loss_price
            )
            logger.info(f"Successfully created stop loss order: {order}")
            return order
        except Exception as e:
            logger.error(f"Failed to create stop loss order: {str(e)}")
            return None

    async def create_takeprofit_order(self, symbol: str, take_profit_price: float, quantity: float):
        """Create a take profit order."""
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=SIDE_SELL,
                type=FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET,
                quantity=quantity,
                stopPrice=take_profit_price
            )
            logger.info(f"Successfully created take profit order: {order}")
            return order
        except Exception as e:
            logger.error(f"Failed to create take profit order: {str(e)}")
            return None

    async def cancel_order(self, symbol: str, order_id: int):
        """Cancel an existing order."""
        try:
            result = self.client.futures_cancel_order(
                symbol=symbol,
                orderId=order_id
            )
            logger.info(f"Successfully cancelled order {order_id}: {result}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {str(e)}")
            return False

    async def monitor_order(self, symbol: str, order_id: int):
        """Monitor an order's status via websocket."""
        while True:
            try:
                message = await self.ws.recv()
                data = json.loads(message)
                
                if data.get('e') == 'ORDER_TRADE_UPDATE':
                    order_data = data['o']
                    if str(order_data['i']) == str(order_id):
                        status = order_data['X']
                        if status == 'FILLED':
                            logger.info(f"Order {order_id} has been filled")
                            return True
                        elif status in ['CANCELED', 'REJECTED', 'EXPIRED']:
                            logger.warning(f"Order {order_id} status: {status}")
                            return False
            except Exception as e:
                logger.error(f"Error monitoring order {order_id}: {str(e)}")
                await asyncio.sleep(RETRY_DELAY)

    async def close(self):
        """Close websocket connection."""
        if self.ws:
            await self.ws.close()
            logger.info("Closed Binance websocket connection")