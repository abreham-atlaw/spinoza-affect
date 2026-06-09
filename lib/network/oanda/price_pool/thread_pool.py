import time
from abc import ABC, abstractmethod
from threading import Thread

from lib.utils.logger import Logger
from ..trader import Trader


class ThreadPool(Thread, ABC):

	def __init__(self, trader: Trader, interval: float=1):
		super().__init__(daemon=True)
		self._trader = trader
		self._interval = interval
		Logger.info(
			f"Initialized {self.__class__.__name__} with trader={trader.__class__.__name__}, interval={interval}"
		)

	@abstractmethod
	def _run(self):
		pass

	def run(self):
		Logger.info(f"Starting {self.__class__.__name__} pooling...")
		while True:
			self._run()
			if self._interval > 0:
				time.sleep(self._interval)
