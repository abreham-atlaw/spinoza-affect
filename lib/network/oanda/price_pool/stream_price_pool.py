import typing
from datetime import datetime

from lib.utils.logger import Logger
from .price_pool import PricePool

class StreamPricePool(PricePool):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.__price_map = {}
		self.__spread_map = {}
		self.last_update = None

	def get_price(self, instrument: typing.Tuple[float, float]):
		return self.__price_map.get(instrument)

	def get_spread_price(self, instrument: typing.Tuple[float, float]):
		return self.__spread_map.get(instrument)

	def __stream_prices(self):
		Logger.info(f"[{self.__class__.__name__}] Starting streaming...")
		for price in self._trader.stream_price(self._instruments):
			if price is None:
				continue
			self.__price_map[price.get_instrument()] = price.get_price()
			self.__spread_map[price.get_instrument()] = price
			self.last_update = datetime.now()

	def _run(self):
		self.__stream_prices()
