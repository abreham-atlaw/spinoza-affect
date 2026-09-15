from django.db.models import Model


class DjangoUtils:

	@staticmethod
	def articulate_object(obj: Model) -> str:
		field_values = [
			f"{field.name}={getattr(obj, field.name)}"
			for field in obj._meta.fields
		]
		return f"{obj.__class__.__name__}({', '.join(field_values)})"
