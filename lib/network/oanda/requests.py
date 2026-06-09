import typing
from typing import *

import json
from datetime import datetime

from lib.network.rest_interface import Request
from .data.models import AccountSummary, Trade, Order, CreateOrderResponse, CloseTradeResponse, Price, CandleStick, \
	SpreadPrice, ClosedTradeDetails, CancelOrderResponse


class AccountSummaryRequest(Request):

	def __init__(self):
		super().__init__("accounts/{{account_id}}/summary/", output_class=AccountSummary)

	def _filter_response(self, response: Dict) -> Dict:
		return response["account"]


class GetOpenTradesRequest(Request):

	def __init__(self):
		super().__init__("accounts/{{account_id}}/openTrades/", output_class=List[Trade])

	def _filter_response(self, response: Dict) -> Dict:
		return response["trades"]


class GetPendingOrdersRequest(Request):

	def __init__(self):
		super().__init__("accounts/{{account_id}}/pendingOrders/", output_class=List[Order])

	def _filter_response(self, response: Dict) -> Dict:
		orders = response["orders"]
		return list(filter(
			lambda order: order['type'] in ["LIMIT", "STOP"],
			orders
		))


class CreateOrderRequest(Request):

	def __init__(self, order: Order):
		super().__init__(
			"accounts/{{account_id}}/orders/",
			method=Request.Method.POST, 
			post_data=order, 
			output_class=CreateOrderResponse,
			headers={"Content-Type": "application/json"}
		)
	
	def get_post_data(self) -> Dict:
		data = super().get_post_data()
		data = {
			k: v
			for k, v in data.items()
			if v is not None
		}
		return json.dumps({
			"order": data
		})

	def _filter_response(self, response):
		return response


class GetInstrumentsRequest(Request):

	def __init__(self):
		super().__init__("accounts/{{account_id}}/instruments/", output_class=List[Tuple[str, str]])
	
	def _filter_response(self, response):
		from . import Trader
		return [Trader.split_instrument(instrument["name"]) for instrument in response["instruments"]]


class GetInstrumentPrecisionRequest(Request):

	def __init__(self, instrument: typing.Tuple[str, str]):
		super().__init__("accounts/{{account_id}}/instruments/", output_class=int)
		self.__instrument = instrument

	def _filter_response(self, response):
		from . import Trader
		instrument = Trader.format_instrument(self.__instrument)
		details = next(filter(
			lambda detail: detail["name"] == instrument,
			response["instruments"]
		))
		return details["displayPrecision"]

class GetTradeUnitsPrecisionMapRequest(Request):

	def __init__(self):
		super().__init__("accounts/{{account_id}}/instruments/", output_class=typing.Dict[typing.Tuple[str, str], int])

	def _filter_response(self, response):
		from . import Trader
		return {
			Trader.split_instrument(instrument_data["name"]): instrument_data["tradeUnitsPrecision"]
			for instrument_data in response["instruments"]
		}


class GetInstrumentsMarginRateRequest(Request):

	def __init__(self):
		super().__init__("accounts/{{account_id}}/instruments/", output_class=typing.Dict[typing.Tuple[str, str], float])

	def _filter_response(self, response):
		from . import Trader
		return {
			Trader.split_instrument(instrument_data["name"]): instrument_data["marginRate"]
			for instrument_data in response["instruments"]
		}


class CloseTradeRequest(Request):

	def __init__(self, id_):
		super().__init__(
			"accounts/{{account_id}}/trades/{trade_id}/close", 
			method=Request.Method.PUT,
			url_params={"trade_id": id_},
			output_class=CloseTradeResponse
		)
	
	def _filter_response(self, response):
		if "orderFillTransaction" in response:
			return response["orderFillTransaction"]
		return response["orderCancelTransaction"]


class CancelOrderRequest(Request):

	def __init__(self, id: str):
		super().__init__(
			"accounts/{{account_id}}/orders/{order_id}/cancel",
			method=Request.Method.PUT,
			url_params={"order_id": id},
			output_class=CancelOrderResponse
		)


class GetPriceRequest(Request):

	def __init__(self, instrument):
		super().__init__(
			"accounts/{{account_id}}/pricing/",
			get_params={"instruments": [instrument]},
			output_class=Price
		)
	
	def _filter_response(self, response):
		return response["prices"][0]


class GetCandleSticksRequest(Request):

	def __init__(self, instrument: Tuple[str, str], from_: datetime = None, to: datetime = None, granularity: str = None, count: int = None):
		from . import Trader
		get_params = {
			"granularity": granularity,
			"count": count,
			"Accept-Datetime-Format": "UNIX",
		}
		if to is not None:
			get_params["to"] = to.timestamp()
		if from_ is not None:
			get_params["from"] = from_.timestamp()
		super().__init__(
			"accounts/{{account_id}}/instruments/{instrument}/candles/",
			url_params={"instrument": Trader.format_instrument(instrument)},
			get_params=get_params,
			output_class=List[CandleStick]
		)

	def _filter_response(self, response):
		return response["candles"]


class GetSpreadPriceRequest(Request):

	def __init__(self, instrument: Tuple[str, str]):
		from . import Trader
		super().__init__(
			"accounts/{{account_id}}/pricing",
			get_params={
				"instruments": Trader.format_instrument(instrument)
			},
			output_class=SpreadPrice
		)

	def _filter_response(self, response):
		return response['prices'][0]


class GetClosedTradesRequest(Request):

	def __init__(self, count: int=50):
		super().__init__(
			"accounts/{{account_id}}/trades/",
			get_params={
				"count": count,
				"state": "CLOSED"
			},
			output_class=List[ClosedTradeDetails]
		)

	def _filter_response(self, response):
		return response["trades"]


class GetAllOrdersRequest(Request):

	def __init__(self, count: int = 50):
		super().__init__(
			"accounts/{{account_id}}/orders/",
			get_params={
				"count": count,
				"state": "ALL"
			},
			output_class=typing.List[Order]
		)

	def _filter_response(self, response):
		return list(filter(
			lambda order: order["type"] == "LIMIT",
			response["orders"]
		))


class StreamPriceRequest(Request):

	def __init__(self, instruments: typing.List[typing.Tuple[str, str]]):
		from .trader import Trader
		super().__init__(
			"accounts/{{account_id}}/pricing/stream/",
			get_params={"instruments": ','.join([Trader.format_instrument(ins) for ins in instruments])},
			stream=True,
			output_class=typing.Optional[SpreadPrice]
		)

	def _filter_response(self, response):
		if response["type"] != "PRICE":
			return None
		return response
