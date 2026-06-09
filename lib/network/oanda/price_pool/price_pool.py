import typing
from abc import abstractmethod

from lib.utils.logger import Logger
from .thread_pool import ThreadPool
from ..data.models import SpreadPrice


class PricePool(ThreadPool):

	def __init__(
			self,
			*args,
			instruments: typing.List[typing.Tuple[str, str]],
			**kwargs,
	):
		super().__init__(*args, **kwargs)
		self._instruments = instruments
		Logger.info(
			f"Initialized {self.__class__.__name__} with instruments={instruments}"
		)

	@abstractmethod
	def get_price(self, instrument: typing.Tuple[float, float]) -> float:
		pass

	@abstractmethod
	def get_spread_price(self, instrument: typing.Tuple[float, float]) -> SpreadPrice:
		pass
