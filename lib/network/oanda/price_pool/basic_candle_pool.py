import typing
from datetime import datetime

import pandas as pd

from lib.utils.logger import Logger
from .candle_pool import CandlePool
from ..data.models import CandleStick


class BasicCandlePool(CandlePool):

	def __init__(
			self,
			*args,
			granularities: typing.List[str],
			counts: typing.List[str],
			**kwargs
	):
		super().__init__(*args, **kwargs)
		self._granularities = granularities
		self._counts = counts

		self.__candle_map = {}
		self.last_update = None
		Logger.info(
			f"Initialized {self.__class__.__name__} with granularities={granularities}, counts={counts}, ")

	def __get_key(self, instrument: typing.Tuple[str, str], granularity: str, to: datetime, count: int) -> str:
		target_time = pd.to_datetime(to).floor(f"{self._trader.get_granularity_seconds(granularity)}s")
		return f"{'_'.join(instrument)}_{granularity}_{target_time.isoformat()}_{count}"

	def __fetch_candlesticks(self, instrument: typing.Tuple[str, str], granularity: str, to: datetime, count: int) -> typing.Tuple[str, typing.List[CandleStick]]:
		candlesticks = self._trader.fetch_candlestick(
			instrument=instrument,
			to=to,
			granularity=granularity,
			count=count
		)
		key = self.__get_key(instrument, granularity, to, count)
		return key, candlesticks

	def __fetch_all(self):

		candle_map = {}
		for instrument in self._instruments:
			for granularity in self._granularities:
				for count in self._counts:
					key, candles = self.__fetch_candlesticks(instrument, granularity, datetime.now(), count)
					candle_map[key] = candles
					self.__candle_map[key] = candles
		self.__candle_map = candle_map
		self.last_update = datetime.now()

	def get_candlesticks(self, instrument: typing.Tuple[str, str], granularity: str, to: datetime, count: int) -> \
	typing.List[CandleStick]:

		key = self.__get_key(instrument, granularity, to, count)
		return self.__candle_map.get(key)

	def _run(self):
		self.__fetch_all()
