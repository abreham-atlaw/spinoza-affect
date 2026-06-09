import typing
from datetime import datetime

from lib.utils.logger import Logger
from .candle_pool import CandlePool
from ..data.models import CandleStick


class MultiCandlePool(CandlePool):

	def __init__(self, pools: typing.List[CandlePool]):
		super().__init__(
			trader=None,
			instruments=[]
		)
		self.__pools = pools
		Logger.info(f"Initialized {self.__class__.__name__} with pools = [{', '.join([p.__class__.__name__ for p in pools])}")

	def get_candlesticks(self, instrument: typing.Tuple[str, str], granularity: str, to: datetime, count: int) -> \
	typing.List[CandleStick]:
		for pool in self.__pools:
			candles = pool.get_candlesticks(instrument, granularity, to, count)
			if candles is not None:
				return candles
		return None

	def start(self):
		Logger.info(f"[{self.__class__.__name__}] Starting Pools...")
		for pool in self.__pools:
			pool.start()

	def _run(self):
		pass
	