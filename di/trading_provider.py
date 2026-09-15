import typing

from affect import config

if typing.TYPE_CHECKING:
	from lib.network.oanda.data.models import Order
	from apps.trading.utils.executors import RecursiveStraddleExecutor, RecursiveMarketMakingExecutor


class TradingProvider:


	@staticmethod
	def provide_recursive_straddle_executor(order: 'Order') -> 'RecursiveStraddleExecutor':
		from apps.trading.utils.executors import RecursiveStraddleExecutor, RecursiveStraddleExecutor2
		if config.USE_RECURSIVE_STRADDLE_EXECUTOR_2:
			return RecursiveStraddleExecutor2(
				order,
				initial_units_correction=config.ENABLE_INITIAL_UNITS_CORRECTION
			)
		return RecursiveStraddleExecutor(order)

	@staticmethod
	def provide_recursive_market_making_executor(order: 'Order') -> 'RecursiveMarketMakingExecutor':
		from apps.trading.utils.executors import RecursiveMarketMakingExecutor
		return RecursiveMarketMakingExecutor(order=order)
