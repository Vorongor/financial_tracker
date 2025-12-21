from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q, QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404

from accounts.models import UserConnection

user = get_user_model()


class UserConnectionsService:
    @classmethod
    def get_user_connections(
            cls,
            user_id: int,
            status: str = None
    ) -> QuerySet[UserConnection]:
        query = Q(from_user_id=user_id) | Q(to_user_id=user_id)

        if status == "pending":
            query &= Q(status=UserConnection.Status.PENDING)

        if status == "accepted":
            query &= Q(status=UserConnection.Status.ACCEPTED)

        return UserConnection.objects.filter(
            query
        ).select_related(
            "from_user",
            "to_user"
        ).distinct()

    @classmethod
    def get_user_from_uk(cls, uk: str) -> user:
        try:
            return get_object_or_404(user, connect_key=uk)
        except ValidationError:
            raise Http404("Invalid UUID format")
