import asyncio
from typing import Dict
from logger import setup_logger
from config import ORDER_QUANTITY

logger = setup_logger()

class OrderManager:
    def __init__(self, binance_handler):
        """Initialize the OrderManager with a BinanceHandler instance."""
        self.binance_handler = binance_handler
        self.active_trades = {}  # Store active trades and their associated orders

    async def process_signal(self, signal_data: Dict):
        """
        Process a trading signal and execute the necessary orders.
        
        Args:
            signal_data (dict): Dictionary containing signal information:
                - symbol: Trading pair symbol (e.g., 'BTCUSDT')
                - entry_price: Price to enter the trade
                - stop_loss: Stop loss price
                - take_profit: Take profit price
        """
        try:
            symbol = signal_data['symbol']
            entry_price = signal_data['entry_price']
            stop_loss = signal_data['stop_loss']
            take_profit = signal_data['take_profit']

            logger.info(f"Processing signal for {symbol} - Entry: {entry_price}, SL: {stop_loss}, TP: {take_profit}")

            # Create entry order
            entry_order = await self.binance_handler.create_stop_market_order(
                symbol=symbol,
                entry_price=entry_price,
                quantity=ORDER_QUANTITY
            )

            if not entry_order:
                logger.error("Failed to create entry order")
                return

            entry_order_id = entry_order['orderId']
            
            # Store trade information
            self.active_trades[entry_order_id] = {
                'symbol': symbol,
                'entry_order_id': entry_order_id,
                'stop_loss_order_id': None,
                'take_profit_order_id': None,
                'quantity': ORDER_QUANTITY
            }

            # Monitor entry order
            filled = await self.binance_handler.monitor_order(symbol, entry_order_id)
            
            if not filled:
                logger.warning(f"Entry order {entry_order_id} was not filled")
                del self.active_trades[entry_order_id]
                return

            # Create stop loss and take profit orders
            stop_loss_order = await self.binance_handler.create_stoploss_order(
                symbol=symbol,
                stop_loss_price=stop_loss,
                quantity=ORDER_QUANTITY
            )

            take_profit_order = await self.binance_handler.create_takeprofit_order(
                symbol=symbol,
                take_profit_price=take_profit,
                quantity=ORDER_QUANTITY
            )

            if not stop_loss_order or not take_profit_order:
                logger.error("Failed to create stop loss or take profit orders")
                return

            # Update trade information with stop loss and take profit order IDs
            self.active_trades[entry_order_id].update({
                'stop_loss_order_id': stop_loss_order['orderId'],
                'take_profit_order_id': take_profit_order['orderId']
            })

            # Monitor stop loss and take profit orders
            await self.monitor_exit_orders(
                symbol,
                stop_loss_order['orderId'],
                take_profit_order['orderId']
            )

        except Exception as e:
            logger.error(f"Error processing signal: {str(e)}")

    async def monitor_exit_orders(self, symbol: str, sl_order_id: int, tp_order_id: int):
        """Monitor stop loss and take profit orders. Cancel the other order when one is filled."""
        try:
            # Create tasks to monitor both orders
            sl_task = asyncio.create_task(
                self.binance_handler.monitor_order(symbol, sl_order_id)
            )
            tp_task = asyncio.create_task(
                self.binance_handler.monitor_order(symbol, tp_order_id)
            )

            # Wait for either order to be filled
            done, pending = await asyncio.wait(
                [sl_task, tp_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel the pending order
            for task in pending:
                task.cancel()
                order_id = sl_order_id if task == sl_task else tp_order_id
                await self.binance_handler.cancel_order(symbol, order_id)

            # Clean up trade data
            for trade_id, trade_data in self.active_trades.items():
                if sl_order_id in [trade_data['stop_loss_order_id'], trade_data['take_profit_order_id']]:
                    del self.active_trades[trade_id]
                    break

        except Exception as e:
            logger.error(f"Error monitoring exit orders: {str(e)}")

    def get_active_trades(self) -> Dict:
        """Return the current active trades."""
        return self.active_trades