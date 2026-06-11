from rest_framework import serializers

from apps.core.models import Account


class AccountSerializer(serializers.ModelSerializer):

	class Meta:
		model = Account
		fields = ("account_id", "token", "url")
