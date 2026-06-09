import typing
from abc import ABC, abstractmethod
from datetime import datetime

from lib.network.oanda.data.models import CandleStick
from .thread_pool import ThreadPool


class CandlePool(ThreadPool, ABC):

	def __init__(
			self,
			*args,
			instruments: typing.List[typing.Tuple[str, str]],
			**kwargs
	):
		super().__init__(*args, **kwargs)
		self._instruments = instruments

	@abstractmethod
	def get_candlesticks(
			self,
			instrument: typing.Tuple[str, str],
			granularity: str,
			to: datetime,
			count: int,
	) -> typing.List[CandleStick]:
		pass
