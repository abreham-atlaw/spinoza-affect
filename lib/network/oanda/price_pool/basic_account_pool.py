import time
from datetime import datetime

from lib.utils.logger import Logger
from .account_pool import AccountPool


class BasicAccountPool(AccountPool):

	def __init__(self, *args, interval: float = 2, **kwargs):
		super().__init__(*args, **kwargs)
		self.__account_summary = None
		self.last_update = None
		self.__interval = interval
		Logger.info(f"Initialized {self.__class__.__name__} with interval={interval}")

	def __fetch_account_summary(self):
		self.__account_summary = self._trader.get_account_summary()
		self.last_update = datetime.now()

	def get_account_summary(self):
		return self.__account_summary

	def run(self):
		while True:
			self.__fetch_account_summary()
			time.sleep(self.__interval)