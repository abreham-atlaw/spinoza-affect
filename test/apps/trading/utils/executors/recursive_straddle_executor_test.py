import time

import matplotlib.pyplot as plt

from django import test

from apps.core.models import Account
from apps.trading.models import RecursiveStraddleOrder, ExecutionOrder
from affect import config
from apps.trading.utils.executors import RecursiveStraddleExecutor
from lib.network.oanda import Trader
from lib.utils.logger import Logger


class RecursiveStraddleExecutorTest(test.TransactionTestCase):

	def setUp(self):
		self.trader = Trader(
			token=config.DEFAULT_OANDA_TOKEN,
			account_no=config.DEFAULT_OANDA_TRADING_ACCOUNT_ID,
			trading_url=config.DEFAULT_OANDA_TRADING_URL,
			# timezone=pytz.timezone("Africa/Addis_Ababa")
		)
		self.trader.close_all_trades()
		self.trader.cancel_all_orders()
		self.account = Account.objects.create(
			account_id=config.DEFAULT_OANDA_TRADING_ACCOUNT_ID,
			token=config.DEFAULT_OANDA_TOKEN,
			url=config.DEFAULT_OANDA_TRADING_URL,
		)

	def tearDown(self):
		self.trader.close_all_trades()
		self.trader.cancel_all_orders()

	def test_live_order(self):

		instrument = ("XAU", "USD")
		price = self.trader.get_price(instrument)
		units = 0.3

		upper_bound = 1.0002  * price
		lower_bound = 0.9998 * price

		Logger.info(f"UPPER_BOUND = {upper_bound}")
		Logger.info(f"LOWER_BOUND = {lower_bound}")

		order = RecursiveStraddleOrder.objects.create(
			account=self.account,
			long_order=ExecutionOrder.objects.create(
				type=ExecutionOrder.Type.STOP,
				action=ExecutionOrder.Action.BUY,
				units=units,
				price=upper_bound,
				stop_loss=lower_bound,
				base_currency=instrument[0],
				quote_currency=instrument[1]
			),
			short_order=ExecutionOrder.objects.create(
				type=ExecutionOrder.Type.STOP,
				action=ExecutionOrder.Action.SELL,
				units=units,
				price=lower_bound,
				stop_loss=upper_bound,
				base_currency=instrument[0],
				quote_currency=instrument[1]
			),
		)

		executor = RecursiveStraddleExecutor(order)
		executor.start()

		y_lim = (price*0.99, price*1.01)
		prices = []
		times = []

		while True:
			active_orders = self.trader.get_pending_orders()
			active_trades = self.trader.get_open_trades()

			current_price = self.trader.get_price(instrument)
			current_time = self.trader.get_current_time(instrument)

			prices.append(current_price)
			times.append(current_time)

			plt.cla()
			plt.grid()
			plt.ylim(*y_lim)
			plt.plot(times, prices)
			plt.scatter([current_time], [current_price], color="red")
			for b in [upper_bound, lower_bound]:
				plt.axhline(y=b, color="green")
			plt.pause(1)

			Logger.info(f"Open Trades({len(active_trades)}): {active_trades}")
			Logger.info(f"Active Orders({len(active_orders)}): {active_orders}")
			Logger.info(f"Current Time: {current_time.isoformat()}, Current Price: {current_price}")

			has_equilibrium = (len(active_orders) == 2 and len(active_trades) == 0) or \
				(len(active_orders) == 1 and len(active_trades) == 1)

			if has_equilibrium:
				Logger.success(f"Equilibrium in check!")
				continue

			Logger.warning(f"Equilibrium failed: Pausing 10 seconds")
			time.sleep(15)
			active_orders = self.trader.get_pending_orders()
			active_trades = self.trader.get_open_trades()
			has_equilibrium = (len(active_orders) == 2 and len(active_trades) == 0) or \
							  (len(active_orders) == 1 and len(active_trades) == 1)
			self.assertTrue(has_equilibrium)

	def test_close(self):
		instrument = ("XAU", "USD")
		price = self.trader.get_price(instrument)
		units = 0.3

		upper_bound = 1.0001  * price
		lower_bound = 0.9999  * price

		Logger.info(f"UPPER_BOUND = {upper_bound}")
		Logger.info(f"LOWER_BOUND = {lower_bound}")

		order = RecursiveStraddleOrder.objects.create(
			account=self.account,
			long_order=ExecutionOrder.objects.create(
				type=ExecutionOrder.Type.STOP,
				action=ExecutionOrder.Action.BUY,
				units=units,
				price=upper_bound,
				stop_loss=lower_bound,
				base_currency=instrument[0],
				quote_currency=instrument[1]
			),
			short_order=ExecutionOrder.objects.create(
				type=ExecutionOrder.Type.STOP,
				action=ExecutionOrder.Action.SELL,
				units=units,
				price=lower_bound,
				stop_loss=upper_bound,
				base_currency=instrument[0],
				quote_currency=instrument[1]
			),
		)

		executor = RecursiveStraddleExecutor(order)
		executor.start()

		time.sleep(15)

		active_orders = self.trader.get_pending_orders()
		active_trades = self.trader.get_open_trades()
		has_equilibrium = (len(active_orders) == 2 and len(active_trades) == 0) or \
						  (len(active_orders) == 1 and len(active_trades) == 1)

		self.assertTrue(has_equilibrium)

		order.is_active = False
		order.save()
		time.sleep(5)
		active_orders = self.trader.get_pending_orders()
		active_trades = self.trader.get_open_trades()
		self.assertEqual(len(active_orders), 0)
		self.assertEqual(len(active_trades), 0)
		self.assertFalse(executor.is_alive())
