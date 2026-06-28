import typing
from typing import *

import math
import datetime
import pytz
import requests.exceptions

from lib.utils.logger import Logger
from .data.models import AccountSummary, Trade, Order, CloseTradeResponse, CreateOrderResponse, CandleStick, \
	SpreadPrice, \
	ClosedTradeDetails, TriggerPrice, CancelOrderResponse
from . import OandaNetworkClient
from .requests import AccountSummaryRequest, GetOpenTradesRequest, GetInstrumentsRequest, CreateOrderRequest, \
	CloseTradeRequest, GetPriceRequest, GetCandleSticksRequest, GetSpreadPriceRequest, GetClosedTradesRequest, \
	GetInstrumentPrecisionRequest, GetTradeUnitsPrecisionMapRequest, GetPendingOrdersRequest, CancelOrderRequest, \
	GetInstrumentsMarginRateRequest, GetAllOrdersRequest, StreamPriceRequest
from .exceptions import InstrumentNotFoundException, InvalidActionException, InsufficientMarginException
from lib.utils.cache.decorators import CacheDecorators


class Trader:

	INSTRUMENT_DELIMITER = "_"

	__GRAN_MAP = {
		"S5": 5,
		"S10": 10,
		"S15": 15,
		"S30": 30,

		"M1": 60,  # 1 min
		"M2": 2 * 60,  # 2 mins
		"M4": 4 * 60,  # 4 mins
		"M5": 5 * 60,  # 5 mins
		"M10": 10 * 60,  # 10 mins
		"M15": 15 * 60,  # 15 mins
		"M30": 30 * 60,  # 30 mins

		"H1": 60 * 60,  # 1 hour
		"H2": 2 * 60 * 60,  # 2 hours
		"H3": 3 * 60 * 60,  # 3 hours
		"H4": 4 * 60 * 60,  # 4 hours
		"H6": 6 * 60 * 60,  # 6 hours
		"H8": 8 * 60 * 60,  # 8 hours
		"H12": 12 * 60 * 60,  # 12 hours

		"D": 24 * 60 * 60,  # 1 day
		"W": 7 * 24 * 60 * 60,  # 1 week
		"M": 30 * 24 * 60 * 60,  # Approx. 1 month (30 days)
	}

	class TraderAction:
		SELL = 0
		BUY = 1

		@staticmethod
		def reverse(action):
			if action == Trader.TraderAction.BUY:
				return Trader.TraderAction.SELL
			if action == Trader.TraderAction.SELL:
				return Trader.TraderAction.BUY
			raise InvalidActionException()

	def __init__(
			self,
			token: str,
			account_no: str,
			timezone: pytz.tzinfo.BaseTzInfo = None,
			trading_url: str = "https://api-fxpractice.oanda.com/v3",
			streaming_url: str = "https://stream-fxpractice.oanda.com/v3",
			timeout: Optional[float] = None,
			min_gran="S5",
			candle_completion_threshold: float = 1.0,
			time_correction: bool = True,
			max_candlestick_count: int = 5000
	):
		self.__token: str = token
		self.__account_no: str = account_no
		self.__client = OandaNetworkClient(trading_url, self.__token, self.__account_no, timeout=timeout)
		self.__stream_client = OandaNetworkClient(streaming_url, self.__token, self.__account_no)
		self.__summary: AccountSummary = self.get_account_summary()
		self.__timezone = timezone
		if timezone is None:
			self.__timezone = pytz.timezone("UTC")
		self.__min_gran = min_gran
		self.__candle_completion_threshold = candle_completion_threshold
		self.__time_correction = time_correction
		self.__max_candlestick_count = max_candlestick_count
		Logger.info(
			f"Initialized {self.__class__.__name__} with account_no={account_no}, timezone={self.__timezone}, "
			f"trading_url={trading_url}, streaming_url={streaming_url}, timeout={timeout}, min_gran={min_gran}, "
			f"candle_completion_threshold={candle_completion_threshold}, time_correction={time_correction}"
		)

	def _fetch_account_summary(self) -> AccountSummary:
		return self.__client.execute(AccountSummaryRequest())

	def get_account_summary(self, update: bool = True) -> AccountSummary:
		summary = self._fetch_account_summary()
		if update:
			self.__summary = summary
		return summary

	def get_balance(self) -> float:
		return self.get_account_summary(True).balance

	def get_margin_available(self) -> float:
		return self.get_account_summary(True).marginAvailable

	def get_open_trades(self) -> List[Trade]:
		return self.__client.execute(GetOpenTradesRequest())

	def get_pending_orders(self) -> List[Order]:
		return self.__client.execute(GetPendingOrdersRequest())

	def get_margin_rate(self) -> float:
		return self.get_account_summary().marginRate

	def get_instruments(self) -> List[Tuple[str, str]]:
		return self.__client.execute(GetInstrumentsRequest())

	def __get_proper_instrument(self, instrument: Tuple[str, str]) -> Tuple[str, str]:
		available_instruments = self.get_instruments()
		rev_instrument = instrument[::-1]
		for cur_instrument in available_instruments:
			if cur_instrument == instrument:
				return instrument
			if cur_instrument == rev_instrument:
				return rev_instrument
		raise InstrumentNotFoundException(instrument)

	def __get_proper_instrument_action_pair(self, instrument, action) -> Tuple[Tuple[str, str], int]:
		proper_instrument = self.__get_proper_instrument(instrument)
		if proper_instrument == instrument:
			return proper_instrument, action
		return proper_instrument, Trader.TraderAction.reverse(action)

	@staticmethod
	def __get_units(action, units) -> int:
		if action == Trader.TraderAction.BUY:
			return units
		elif action == Trader.TraderAction.SELL:
			return -units
		raise InvalidActionException()

	def get_price(self, instrument: Tuple[str, str]) -> float:
		if instrument[0] == instrument[1]:
			return 1
		proper_instrument = self.__get_proper_instrument(instrument)
		price: float = self.__client.execute(
			GetPriceRequest(Trader.format_instrument(proper_instrument))
		).get_price()

		if proper_instrument == instrument:
			return price
		return 1 / price

	def __localize_datetime(self, dt: datetime.datetime) -> datetime.datetime:
		return self.__timezone.localize(dt)

	def __is_candle_complete(self, candle: CandleStick, granularity: int, current_time: datetime.datetime,
							 hard_complete: bool) -> bool:
		if candle.complete:
			return True
		if hard_complete or self.__candle_completion_threshold >= 1:
			return False
		completion = (current_time - candle.time).total_seconds() / granularity
		return completion >= self.__candle_completion_threshold

	def __recursive_fetch_candlestick(
			self,
			instrument: typing.Tuple[str, str],
			from_: datetime.datetime,
			to: datetime.datetime,
			granularity: str,
			count: int
	) -> typing.List[CandleStick]:
		if count <= self.__max_candlestick_count:
			return self.__client.execute(
				GetCandleSticksRequest(
					instrument,
					from_=from_,
					to=to,
					granularity=granularity,
					count=count
				)
			)
		last_candlesticks = self.__recursive_fetch_candlestick(instrument, from_, to, granularity,
															   self.__max_candlestick_count)

		new_to = last_candlesticks[0].time

		return self.__recursive_fetch_candlestick(instrument, from_, new_to, granularity,
												  count - len(last_candlesticks)) + last_candlesticks

	def fetch_candlestick(
			self,
			instrument: Tuple[str, str],
			from_: datetime.datetime = None,
			to: datetime.datetime = None,
			granularity: str = None,
			count: int = None,
	) -> typing.List[CandleStick]:
		if from_ is not None and from_.tzinfo is None:
			from_ = self.__localize_datetime(from_)
		if to is not None and to.tzinfo is None:
			to = self.__localize_datetime(to)

		return self.__recursive_fetch_candlestick(
			instrument, from_, to, granularity, count + 1 if count is not None else None
		)

	def get_candlestick(
			self,
			instrument: Tuple[str, str],
			from_: datetime.datetime = None,
			to: datetime.datetime = None,
			granularity: str = None,
			count: int = None,
			complete: bool = True,
			hard_complete: bool = False
	) -> List[CandleStick]:

		candlesticks = self.fetch_candlestick(
			instrument, from_, to, granularity, count
		)

		if complete:
			if hard_complete:
				filter_fn = lambda cd: cd.complete
			else:
				current_time = self.get_current_time(instrument, current_time=to)
				filter_fn = lambda cd: self.__is_candle_complete(cd, self.__GRAN_MAP[granularity], current_time,
																 hard_complete)
			candlesticks = list(filter(
				filter_fn,
				candlesticks
			))

		if count is not None:
			candlesticks = candlesticks[-count:]
		return candlesticks

	def get_spread_price(self, instrument: Tuple[str, str]) -> SpreadPrice:
		return self.__client.execute(
			GetSpreadPriceRequest(
				instrument
			)
		)

	def get_closed_trades(self, count=None) -> List[ClosedTradeDetails]:
		request = GetClosedTradesRequest()
		if count is not None:
			request = GetClosedTradesRequest(count=count)
		return self.__client.execute(
			request
		)

	def get_all_orders(self, count: int = 50):
		return self.__client.execute(
			GetAllOrdersRequest(count)
		)

	def __get_margin_rate(self, instrument: typing.Tuple[str, str]) -> float:
		return self.get_instruments_margin_rate()[instrument]

	def __get_margin_required(self, instrument: Tuple[str, str], units: int) -> float:
		in_quote = self.get_price(instrument) * self.__get_margin_rate(instrument) * units
		quote_price = self.get_price((instrument[1], self.__summary.currency))
		return in_quote * quote_price

	def __get_units_for_margin_used(self, instrument: Tuple[str, str], margin_used: float) -> float:
		in_quote = self.get_price((self.__summary.currency, instrument[1])) * margin_used
		precision = self.get_trade_units_precision_map()[instrument]
		price = self.get_price(instrument)
		rate = self.__get_margin_rate(instrument)
		units = in_quote / (rate * price)
		return math.floor(units * 10 ** precision) / 10 ** precision

	def __format_price(self, price: float, instrument: typing.Tuple[str, str]) -> str:
		return str(round(price, self.get_instrument_precision(instrument)))

	@Logger.logged_method
	def trade(
			self,
			instrument: Tuple,
			action: int,
			margin: float = None,
			units: float = None,
			time_in_force=None,
			stop_loss: float = None,
			take_profit: float = None,
			limit_price: float = None,
			stop_price: float = None
	) -> CreateOrderResponse:

		is_limit_order = limit_price is not None
		is_stop_order = stop_price is not None
		is_trigger_order = is_limit_order or is_stop_order

		if units is None and margin is None:
			raise ValueError(f"Both units and margin can not be None.")

		if time_in_force is None:
			time_in_force = "GTC" if is_trigger_order else "FOK"

		instrument, action = self.__get_proper_instrument_action_pair(instrument, action)

		if margin is None:
			margin = self.__get_margin_required(instrument, units)
		if units is None:
			units = self.__get_units_for_margin_used(instrument, margin)

		available_margin = self.get_margin_available()
		if (not is_trigger_order) and (available_margin < margin):
			raise InsufficientMarginException(available_margin, margin)
		units = self.__get_units(
			action,
			units
		)

		if take_profit is not None:
			take_profit = TriggerPrice(self.__format_price(take_profit, instrument))

		if stop_loss is not None:
			stop_loss = TriggerPrice(self.__format_price(stop_loss, instrument))

		trigger_price = self.__format_price(
			(limit_price if is_limit_order else stop_price),
			instrument
		) if is_trigger_order else None

		order = Order(
			str(units),
			Trader.format_instrument(instrument),
			time_in_force,
			stopLossOnFill=stop_loss,
			takeProfitOnFill=take_profit,
			type=Order.Types.limit if is_limit_order else Order.Types.stop if is_stop_order else Order.Types.market,
			price=trigger_price
		)
		return self.__client.execute(
			CreateOrderRequest(order)
		)

	@Logger.logged_method
	def close_trade(self, trade_id: int) -> CloseTradeResponse:
		response: CloseTradeResponse = self.__client.execute(
			CloseTradeRequest(trade_id)
		)
		return response

	def __close_trades(self, trades: typing.List[Trade]) -> List[CloseTradeResponse]:
		closed_traders = []

		for trade in trades:
			try:
				closed_traders.append(self.close_trade(trade.id))
			except requests.exceptions.HTTPError as ex:
				if ex.response is not None and ex.response.status_code != 404:
					raise ex
				Logger.warning(f"Trade(id={trade.id}) closed by another party.")

		return closed_traders

	@Logger.logged_method
	def close_trades(self, instrument: Tuple[str, str]) -> List[CloseTradeResponse]:
		open_trades = [
			trade
			for trade in self.get_open_trades()
			if trade.get_instrument() == instrument or instrument[::-1] == trade.get_instrument()
		]
		return self.__close_trades(open_trades)

	@Logger.logged_method
	def close_all_trades(self) -> List[CloseTradeResponse]:
		open_trades = self.get_open_trades()
		return self.__close_trades(open_trades)

	@Logger.logged_method
	def cancel_order(self, order_id: str) -> CancelOrderResponse:
		return self.__client.execute(
			CancelOrderRequest(order_id)
		)

	@Logger.logged_method
	def cancel_orders(self, instrument: Tuple[str, str]) -> List[CancelOrderResponse]:
		closed_orders = []

		for order in self.get_pending_orders():
			if order.get_instrument() == instrument or instrument[::-1] == order.get_instrument():
				try:
					closed_orders.append(self.cancel_order(order.id))
				except requests.exceptions.HTTPError as ex:
					if ex.response is not None and ex.response.status_code != 404:
						raise ex
					Logger.warning(f"Order(id={order.id}) cancelled by another party.")

		return closed_orders

	@Logger.logged_method
	def cancel_all_orders(self) -> List[CancelOrderResponse]:
		orders = self.get_pending_orders()
		return [
			self.cancel_order(order.id)
			for order in orders
		]

	@staticmethod
	def split_instrument(instrument: str) -> Tuple[str, str]:
		return tuple(instrument.split(Trader.INSTRUMENT_DELIMITER))

	@staticmethod
	def format_instrument(instrument: Tuple[str, str]) -> str:
		return f"{instrument[0]}{Trader.INSTRUMENT_DELIMITER}{instrument[1]}"

	@staticmethod
	def get_granularity_seconds(granularity: str) -> int:
		return Trader.__GRAN_MAP[granularity]

	def get_current_time(self, instrument: Tuple[str, str],
						 current_time: datetime.datetime = None) -> datetime.datetime:
		if current_time is None:
			current_time = datetime.datetime.now()
		cs = self.get_candlestick(
			instrument=instrument,
			count=1,
			granularity=self.__min_gran,
			to=current_time,
			complete=True,
			hard_complete=True
		)
		increment = self.__GRAN_MAP[self.__min_gran]
		if self.__time_correction:
			increment *= 1.5
		time = cs[0].time.astimezone(self.__timezone) + datetime.timedelta(seconds=increment)

		return time

	@CacheDecorators.cached_method()
	def get_instrument_precision(self, instrument: typing.Tuple[str, str]) -> float:
		return self.__client.execute(
			GetInstrumentPrecisionRequest(instrument)
		)

	@CacheDecorators.cached_method()
	def get_trade_units_precision_map(self) -> typing.Dict[typing.Tuple[str, str], int]:
		return self.__client.execute(
			GetTradeUnitsPrecisionMapRequest()
		)

	@CacheDecorators.cached_method()
	def get_instruments_margin_rate(self) -> typing.Dict[typing.Tuple[str, str], float]:
		return self.__client.execute(
			GetInstrumentsMarginRateRequest()
		)

	def stream_price(self, instruments: typing.List[typing.Tuple[str, str]]) -> typing.Iterator[
		typing.Optional[SpreadPrice]]:
		return self.__stream_client.execute(StreamPriceRequest(instruments=instruments))
