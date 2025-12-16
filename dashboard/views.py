from django.views.generic import TemplateView

class HomeDashboard(TemplateView):
    template_name = "dashboard/dashboard.html"

class PersonalDashView(TemplateView):
    template_name = "personal-dash.html"