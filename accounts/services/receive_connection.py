from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404

from accounts.models import UserConnection

user = get_user_model()


def get_user_connections(
        user_id: int,
        status: str = None
) -> QuerySet[UserConnection]:
    query = Q(from_user_id=user_id) | Q(to_user_id=user_id)

    if status == "pending":
        query &= Q(status=UserConnection.Status.PENDING)

    if status == "accepted":
        query &= Q(status=UserConnection.Status.ACCEPTED)

    return UserConnection.objects.filter(query).distinct()

def get_user_from_uk(uk: str) -> user:
    return get_object_or_404(user, connect_key=uk)

