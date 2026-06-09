from abc import ABC
from threading import Thread

from .affect_executor import AffectExecutor

class ThreadAffectExecutor(AffectExecutor, Thread, ABC):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, daemon=True, **kwargs)
