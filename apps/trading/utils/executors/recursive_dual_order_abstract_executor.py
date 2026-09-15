from abc import ABC, abstractmethod

from dataclasses import dataclass
import time

from apps.trading.models import ExecutionOrder, RecursiveDualOrder
from lib.network.oanda.data.models import Order, Trade
from lib.utils.logger import Logger
from utils.affect_executor import ThreadAffectExecutor


@dataclass
class _State:
	long_order: Order
	short_order: Order


class RecursiveDualOrderAbstractExecutor(ThreadAffectExecutor, ABC):

	def __init__(
			self,
			order: RecursiveDualOrder,
			*args,
			sleep_time: float = 0.5,
			initial_units_correction: bool = False,
			**kwargs,
	):
		super().__init__(*args, account=order.account, **kwargs)
		self._order = order
		self.__sleep_time = sleep_time
		self.__initial_units_correction = initial_units_correction
		self.__state = _State(None, None)
		Logger.info(
			f"Initialized {self.__class__.__name__} with order: {str(order)}, sleep_time={sleep_time} , "
			f"initial_units_correction={initial_units_correction}"
		)

	def _on_order_pending(self, order: Order, execution_order: ExecutionOrder):
		pass

	def _on_order_cancelled(self, order: Order, execution_order: ExecutionOrder):
		Logger.warning(f"Order({order}) cancelled or closed without trade being placed. Force placing order.")
		self._place_and_set_order(execution_order)

	def _on_trade_open(self, order: Order, execution_order: ExecutionOrder, trade: Trade):
		if (
				self.__initial_units_correction and
				(not self._order.initial_units_corrected) and
				self._order.orders_placed == 2
		):
			self.__correct_initial_units(order, execution_order)

	def _on_trade_closed(self, order: Order, execution_order: ExecutionOrder, trade: Trade):
		if self.__has_reached_max_orders():
			Logger.warning(f"Unable to place {execution_order} due to maximum number of orders({self._order.max_orders}) reached.")
			return

		Logger.info(f"Order({order}) and it's trade({trade}) closed(on_trade_closed, default). Placing order {execution_order}.")
		self._place_and_set_order(execution_order)

	@property
	def __is_active(self) -> bool:
		self._order.refresh_from_db(fields=["is_active"])
		return self._order.is_active

	def __refresh_state(self):
		self.__state.long_order = self._trader.get_order_by_id(self.__state.long_order.id)
		self.__state.short_order = self._trader.get_order_by_id(self.__state.short_order.id)

	def __get_units(self, execution_order: ExecutionOrder) -> float:
		units = execution_order.units
		if self._order.recursions > 0:
			units *= (self._order.units_multiplier ** self._order.recursions)
			if self._order.max_units is not None:
				units = min(units, self._order.max_units)
			Logger.info(
				f"[{self.__class__.__name__}] Modified units to {units}(max: {self._order.max_units}) due to {self._order.recursions} recursions"
			)
		return units

	def __has_reached_max_orders(self) -> bool:
		if self._order.max_orders is None:
			return False
		orders = self._order.orders_placed
		if self._order.initial_units_corrected:
			orders =  orders - 1
		return orders >= self._order.max_orders

	def __place_order(self, execution_order: ExecutionOrder) -> Order:
		self._order.increment_orders_placed()
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

	def _place_and_set_order(self, execution_order: ExecutionOrder):
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
		order, execution_order = (self.__state.short_order, self._order.short_order) if triggered_execution_order == self._order.long_order else \
			(self.__state.long_order, self._order.long_order)
		self._trader.cancel_order(order.id)
		self._place_and_set_order(execution_order)
		self._order.initial_units_corrected = True

	def _monitor_order(self, order: Order, execution_order: ExecutionOrder):

		if order.state == Order.State.pending:
			self._on_order_pending(order, execution_order)
			return

		if order.state == Order.State.cancelled or order.tradeOpenedID is None:
			self._on_order_cancelled(order, execution_order)
			return

		assert order.tradeOpenedID is not None
		trade = self.__get_order_trade(order)

		if trade.state == Trade.State.open:
			self._on_trade_open(order, execution_order, trade)
			return

		self._on_trade_closed(order, execution_order, trade)
		return


	def __monitor_orders(self):
		self.__refresh_state()

		self._monitor_order(
			self.__state.long_order,
			self._order.long_order
		)

		self._monitor_order(
			self.__state.short_order,
			self._order.short_order
		)

	def __tear_down(self):
		Logger.warning(f"Tearing down...")
		self._trader.close_all_trades()
		self._trader.cancel_all_orders()

	def __place_initial_orders(self):
		Logger.info(f"Placing initial orders...")
		self.__tear_down()
		for order in [self._order.long_order, self._order.short_order]:
			self._place_and_set_order(order)
		Logger.success(f"Placed Initial Orders!")

	def __close(self):
		self.__tear_down()

	def __loop(self):
		while self.__is_active:
			self.__monitor_orders()
			time.sleep(self.__sleep_time)

	def run(self):
		Logger.info(f"[{self.__class__.__name__}] Starting the execution of {self._order}")
		self.__place_initial_orders()
		self.__loop()
		self.__close()
