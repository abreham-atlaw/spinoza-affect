import typing

from django.db import models


class ExecutionOrder(models.Model):

	class Type:
		STOP: str = "STOP"
		LIMIT: str = "LIMIT"
		ALL = [STOP, LIMIT]

	class Action:
		SELL = 0
		BUY = 1
		ALL = [0, 1]

	type: str = models.CharField(max_length=16, choices=[(t, t) for t in Type.ALL])
	action: int = models.IntegerField(choices=[(a, a) for a in Action.ALL])
	margin: float = models.FloatField()
	price: float = models.FloatField()
	stop_loss: float = models.FloatField(null=True, default=None)
	take_profit: float = models.FloatField(null=True, default=None)
	base_currency: str = models.CharField(max_length=16)
	quote_currency: str = models.CharField(max_length=16)

	@property
	def instrument(self) -> typing.Tuple[str, str]:
		return self.base_currency, self.quote_currency

	def __str__(self):
		field_values = [
			f"{field.name}={getattr(self, field.name)}"
			for field in self._meta.fields
		]
		return f"{self.__class__.__name__}({', '.join(field_values)})"