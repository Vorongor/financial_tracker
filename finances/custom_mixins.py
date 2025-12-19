from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


class SuccessUrlFromNextMixin:
    def get_success_url(self):
        next_url = (self.request.POST.get("next")
                    or self.request.GET.get("next"))

        if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={self.request.get_host()},
        ):
            return next_url

        return reverse(
            "profile-page",
            kwargs={"pk": self.request.user.pk}
        )
