import datetime
import typing
from typing import Tuple

from .trader import Trader
from .data.models import SpreadPrice, CandleStick, AccountSummary
from .price_pool import PricePool, CandlePool, AccountPool
from ...utils.logger import Logger


class Trader2(Trader):

	def __init__(
			self,
			*args,
			price_pool: PricePool,
			candle_pool: CandlePool,
			account_pool: AccountPool,
			**kwargs
	):
		self.__account_pool = account_pool
		self.__pool = price_pool
		self.__candle_pool = candle_pool
		self.__account_pool.start()
		self.__pool.start()
		self.__candle_pool.start()
		super().__init__(*args, **kwargs)
		Logger.info(
			f"Initialized {self.__class__.__name__} price_pool={price_pool.__class__.__name__}, "
			f"candle_pool={candle_pool.__class__.__name__}, account_pool={account_pool.__class__.__name__}"
		)

	def get_price(self, instrument: Tuple[str, str]) -> float:
		price = self.__pool.get_price(instrument)
		if price is not None:
			return price
		Logger.warning(f"Price not found in pool. Fetching from server...")
		return super().get_price(instrument)

	def get_spread_price(self, instrument: Tuple[str, str]) -> SpreadPrice:
		price = self.__pool.get_spread_price(instrument)
		if price is not None:
			return price
		Logger.warning(f"Spread Price not found in pool. Fetching from server...")
		return super().get_spread_price(instrument)

	def fetch_candlestick(
			self,
			instrument: Tuple[str, str],
			from_: datetime.datetime = None,
			to: datetime.datetime = None,
			granularity: str = None,
			count: int = None,
	) -> typing.List[CandleStick]:
		candles = self.__candle_pool.get_candlesticks(instrument, granularity, to, count)
		if from_ is None and candles is not None:
			return candles
		Logger.warning(f"Candles for {instrument}[to={to.isoformat()}][{granularity}][count={count}] not found in candle pool. Fetching from server...")
		return super().fetch_candlestick(instrument, from_, to, granularity, count)

	def _fetch_account_summary(self) -> AccountSummary:
		account = self.__account_pool.get_account_summary()
		if account is not None:
			return account
		Logger.warning(f"Account not found in pool. Fetching from server...")
		return super()._fetch_account_summary()
