import time
import typing

from apps.trading.models import RecursiveStraddleOrder, ExecutionOrder
from utils.affect_executor import ThreadAffectExecutor
from lib.network.oanda.data.models import Order, Trade
from lib.utils.logger import Logger


class RecursiveStraddleExecutor(ThreadAffectExecutor):

	def __init__(self, order: RecursiveStraddleOrder, sleep_time: float = 0.5):
		super().__init__(order.account)
		self.__order = order
		self.__sleep_time = sleep_time

	@property
	def __is_active(self) -> bool:
		self.__order.refresh_from_db(fields=["is_active"])
		return self.__order.is_active

	def __get_active_orders(self) -> typing.List[Order]:
		return self._trader.get_pending_orders()

	@staticmethod
	def __is_parallel_order(execution_order: ExecutionOrder, order: Order) -> bool:
		action = ExecutionOrder.Action.BUY if order.units > 0 else ExecutionOrder.Action.SELL
		return (execution_order.action == action) and (execution_order.type == order.type)

	@staticmethod
	def __is_parallel_to_trade(execution_order: ExecutionOrder, trade: Trade) -> bool:
		action = ExecutionOrder.Action.BUY if trade.initialUnits > 0 else ExecutionOrder.Action.SELL
		return execution_order.action == action

	def __place_order(self, execution_order: ExecutionOrder):
		return self._trader.trade(
			instrument=execution_order.instrument,
			action=execution_order.action,
			margin=execution_order.margin,
			stop_price=execution_order.price if execution_order.type == ExecutionOrder.Type.STOP else None,
			limit_price=execution_order.price if execution_order.type == ExecutionOrder.Type.LIMIT else None,
			stop_loss=execution_order.stop_loss,
			take_profit=execution_order.take_profit
		)

	def __check_and_place_order(self, order: ExecutionOrder, active_orders: typing.List[Order], active_trades: typing.List[Trade]):
		for active_order in active_orders:
			if self.__is_parallel_order(order, active_order):
				return
		for active_trade in active_trades:
			if self.__is_parallel_to_trade(order, active_trade):
				return
		Logger.info(f"[{self.__class__.__name__}] Found unplaced order: {order}")
		self.__place_order(order)

	def __check_and_place_orders(self):
		active_orders = self.__get_active_orders()
		active_trades = self._trader.get_open_trades()
		orders = [self.__order.long_order, self.__order.short_order]

		for order in orders:
			self.__check_and_place_order(order, active_orders, active_trades)

	def __place_initial_orders(self):
		Logger.info(f"Placing initial orders...")
		self.__check_and_place_orders()
		Logger.success(f"Placed Initial Orders!")

	def __check_equilibrium(self) -> bool:
		active_orders = self._trader.get_pending_orders()
		active_trades = self._trader.get_open_trades()

		return (
				(len(active_trades) == 0 and len(active_orders) == 2) or
				(len(active_trades) == 1 and len(active_orders) == 1)
		)

	def __close(self):
		self._trader.close_all_trades()
		self._trader.cancel_all_orders()

	def __loop(self):
		Logger.info(f"Starting loop...")
		while self.__is_active:
			if self.__check_equilibrium():
				time.sleep(self.__sleep_time)
				continue
			Logger.info(f"[{self.__class__.__name__}]Equilibrium Disturbed. Reacting")
			self.__check_and_place_orders()
		Logger.info(f"Received Close Signal. Exiting...")
		self.__close()

	def run(self):
		self.__place_initial_orders()
		self.__loop()
