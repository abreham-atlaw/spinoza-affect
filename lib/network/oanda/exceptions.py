import typing


class InstrumentNotFoundException(Exception):

	def __init__(self, instrument: typing.Tuple[str, str]):
		super().__init__(f"Instrument {instrument} not found.")


class InvalidActionException(Exception):
	pass


class InsufficientMarginException(Exception):

	def __init__(self, available_margin: float, requested_margin: float):
		super().__init__(f"Available margin: {available_margin} is less than requested margin: {requested_margin}")
