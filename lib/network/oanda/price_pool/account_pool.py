from abc import ABC, abstractmethod
from threading import Thread


from ..trader import Trader

class AccountPool(Thread, ABC):

	def __init__(self, trader: Trader):
		super().__init__(daemon=True)
		self._trader = trader

	@abstractmethod
	def get_account_summary(self):
		pass
