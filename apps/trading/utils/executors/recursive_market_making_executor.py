from lib.network.oanda.data.models import Order, Trade
from lib.utils.logger import Logger
from .recursive_dual_order_abstract_executor import RecursiveDualOrderAbstractExecutor
from ...models import ExecutionOrder


class RecursiveMarketMakingExecutor(RecursiveDualOrderAbstractExecutor):

	def _on_trade_closed(self, order: Order, execution_order: ExecutionOrder, trade: Trade):
		if trade.stopLossOrder is not None and trade.stopLossOrder.state in (Order.State.filled,
																			 Order.State.triggered):
			Logger.warning(f"[{self.__class__.__name__}] Trade closed through stop loss({trade.stopLossOrder}). Closing {self._order}.")
			self._order.deactivate()
			return
		super()._on_trade_closed(order, execution_order, trade)
