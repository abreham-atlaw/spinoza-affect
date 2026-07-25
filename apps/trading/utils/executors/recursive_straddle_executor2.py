import time
from dataclasses import dataclass

from apps.trading.models import RecursiveStraddleOrder, ExecutionOrder
from lib.network.oanda.data.models import Order, Trade
from lib.utils.logger import Logger
from utils.affect_executor import ThreadAffectExecutor


@dataclass
class _State:
	long_order: Order
	short_order: Order


class RecursiveStraddleExecutor2(ThreadAffectExecutor):

	def __init__(
			self,
			order: RecursiveStraddleOrder,
			sleep_time: float = 0.5,
			initial_units_correction: bool = False
	):
		super().__init__(order.account)
		self.__order = order
		self.__sleep_time = sleep_time
		self.__state = _State(None, None)
		self.__initial_units_correction = initial_units_correction

		Logger.info(
			f"Initialized {self.__class__.__name__} with initial_units_correction={initial_units_correction}, "
			f"sleep_time={sleep_time}, order: {str(order)}"
		)

	@property
	def __is_active(self) -> bool:
		self.__order.refresh_from_db(fields=["is_active"])
		return self.__order.is_active

	def __refresh_state(self):
		self.__state.long_order = self._trader.get_order_by_id(self.__state.long_order.id)
		self.__state.short_order = self._trader.get_order_by_id(self.__state.short_order.id)

	def __get_units(self, execution_order: ExecutionOrder) -> float:
		units = execution_order.units
		if self.__order.recursions > 0:
			units *= (self.__order.units_multiplier ** self.__order.recursions)
			if self.__order.max_units is not None:
				units = min(units, self.__order.max_units)
			Logger.info(
				f"[RecursiveStraddleExecutor] Incremented units to {units}(max: {self.__order.max_units}) due to {self.__order.recursions} recursions"
			)
		return units

	def __place_order(self, execution_order: ExecutionOrder) -> Order:
		self.__order.increment_orders_placed()
		units = self.__get_units(execution_order)
		response = self._trader.trade(
			instrument=execution_order.instrument,
			action=execution_order.action,
			units=units,
			stop_price=execution_order.price if execution_order.type == ExecutionOrder.Type.STOP else None,
			limit_price=execution_order.price if execution_order.type == ExecutionOrder.Type.LIMIT else None,
			stop_loss=execution_order.stop_loss,
			take_profit=execution_order.take_profit
		)
		order = self._trader.get_order_by_id(response.orderCreateTransaction.id)
		return order

	def __place_and_set_order(self, execution_order: ExecutionOrder):
		assert execution_order.action in [ExecutionOrder.Action.BUY, ExecutionOrder.Action.SELL]

		order = self.__place_order(execution_order)

		if execution_order.action == ExecutionOrder.Action.BUY:
			self.__state.long_order = order
		else:
			self.__state.short_order = order

	def __get_order_trade(self, order: Order) -> Trade:
		if order.tradeOpenedID is None:
			raise ValueError(f"Received order({str(order)}) with no tradeOpenedId.")
		return self._trader.get_trade_by_id(order.tradeOpenedID)

	def __correct_initial_units(self, triggered_order: Order, triggered_execution_order: ExecutionOrder):
		Logger.info(f"Correcting initial units")
		order, execution_order = (self.__state.short_order, self.__order.short_order) if triggered_execution_order == self.__order.long_order else \
			(self.__state.long_order, self.__order.long_order)
		self._trader.cancel_order(order.id)
		self.__place_and_set_order(execution_order)

	def __monitor_order(self, order: Order, execution_order: ExecutionOrder):

		if order.state == Order.State.pending:
			return

		if order.state == Order.State.cancelled or order.tradeOpenedID is None:
			Logger.warning(f"Order({order}) cancelled or closed without trade being placed. Force placing order.")
			self.__place_and_set_order(execution_order)
			return

		assert order.tradeOpenedID is not None
		trade = self.__get_order_trade(order)

		if trade.state == Trade.State.open:
			if (
					self.__initial_units_correction and
					(not self.__order.initial_units_corrected) and
					self.__order.orders_placed == 2
			):
				self.__correct_initial_units(order, execution_order)
			return

		if trade.takeProfitOrder is not None and trade.takeProfitOrder.state in (Order.State.filled, Order.State.triggered):
			Logger.success(f"Trade closed through take profit({trade.takeProfitOrder}). Closing {self.__order}.")
			self.__order.deactivate()
			return

		Logger.info(f"Order({order}) and it's trade({trade}) closed without a take profit. Place order {execution_order}.")
		self.__place_and_set_order(execution_order)
		return

	def __monitor_orders(self):
		self.__refresh_state()

		self.__monitor_order(
			self.__state.long_order,
			self.__order.long_order
		)

		self.__monitor_order(
			self.__state.short_order,
			self.__order.short_order
		)

	def __tear_down(self):
		Logger.warning(f"Tearing down...")
		self._trader.close_all_trades()
		self._trader.cancel_all_orders()

	def __place_initial_orders(self):
		Logger.info(f"Placing initial orders...")
		self.__tear_down()
		for order in [self.__order.long_order, self.__order.short_order]:
			self.__place_and_set_order(order)
		Logger.success(f"Placed Initial Orders!")

	def __close(self):
		self.__tear_down()

	def __loop(self):
		while self.__is_active:
			self.__monitor_orders()
			time.sleep(self.__sleep_time)

	def run(self):
		Logger.info(f"[{self.__class__.__name__}] Starting the execution of {self.__order}")
		self.__place_initial_orders()
		self.__loop()
		self.__close()
