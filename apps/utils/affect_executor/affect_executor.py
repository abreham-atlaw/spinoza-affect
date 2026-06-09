from abc import ABC

from apps.core.models import Account
from lib.network.oanda import Trader


class AffectExecutor(ABC):

	def __init__(self, account: Account, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._account = account
		self._trader = self.__init_trader(account)

	@staticmethod
	def __init_trader(account: Account) -> Trader:
		return Trader(
			trading_url=account.url,
			streaming_url=account.streaming_url,
			token=account.token,
			account_no=account.account_id,
		)
