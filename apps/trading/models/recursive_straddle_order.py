import uuid
from uuid import UUID

from django.db import models

from apps.core.models import Account
from lib.utils.django_utils import DjangoUtils
from .execution_order import ExecutionOrder
from .recursive_dual_order import RecursiveDualOrder


class RecursiveStraddleOrder(RecursiveDualOrder):
	pass
