from requests.exceptions import HTTPError, ConnectionError

from lib.utils.logger import Logger
from affect import config


def network_call(func):

	def wrapper(*args, **kwargs):
		tries = config.NETWORK_TRIES
		while tries is None or tries > 0:
			try:
				return func(*args, **kwargs)
			except (HTTPError, ConnectionError) as e:
				Logger.warning(f"Network Call {func.__name__} Failed.({e})")
				if tries is not None:
					tries -= 1
					Logger.warning(f"Tries Left {tries}")

		raise HTTPError

	return wrapper
