import threading
import time
import unittest

from lib.network.oanda import Trader
from affect import config
from lib.utils.logger import Logger


class TraderTest(unittest.TestCase):

	def setUp(self):
		self.trader = Trader(
			token=config.DEFAULT_OANDA_TOKEN,
			account_no=config.DEFAULT_OANDA_TRADING_ACCOUNT_ID,
			trading_url=config.DEFAULT_OANDA_TRADING_URL
		)
		self.trader.close_all_trades()
		self.trader.cancel_all_orders()

	def tearDown(self):
		Logger.warning("Tearing down test...")
		time.sleep(30)
		self.trader.close_all_trades()
		self.trader.cancel_all_orders()

	def test_place_stop_order(self):
		active_orders = self.trader.get_pending_orders()
		self.assertEqual(len(active_orders), 0)

		instrument = ("XAU", "USD")
		price = self.trader.get_price(instrument)
		order = self.trader.trade(
			instrument,
			Trader.TraderAction.BUY,
			units=0.3,
			stop_price=price*1.002
		)

		active_orders = self.trader.get_pending_orders()
		self.assertEqual(len(active_orders), 1)

	def test_close_trades_tolerance(self):

		def async_close_trades():
			time.sleep(2)
			Logger.info(f"Async Closing all Trades")
			for trade in trades:
				self.trader.close_trade(trade.id)
			Logger.success(f"Closed all trades")

		[
			self.trader.trade(
				instrument=("XAU", "USD"),
				action=Trader.TraderAction.BUY,
				units=0.1,
			)
			for i in range(3)
		]

		trades = self.trader.get_open_trades()
		threading.Thread(target=async_close_trades).start()

		self.trader.close_all_trades()

