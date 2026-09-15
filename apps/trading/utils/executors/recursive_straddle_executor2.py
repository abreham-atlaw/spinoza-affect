from lib.network.oanda.data.models import Order, Trade
from lib.utils.logger import Logger
from .recursive_dual_order_abstract_executor import RecursiveDualOrderAbstractExecutor
from ...models import ExecutionOrder


class RecursiveStraddleExecutor2(RecursiveDualOrderAbstractExecutor):

	def _on_trade_closed(self, order: Order, execution_order: ExecutionOrder, trade: Trade):
		if trade.takeProfitOrder is not None and trade.takeProfitOrder.state in (Order.State.filled,
																				 Order.State.triggered):
			Logger.success(f"Trade closed through take profit({trade.takeProfitOrder}). Closing {self._order}.")
			self._order.deactivate()
			return
		super()._on_trade_closed(order, execution_order, trade)
