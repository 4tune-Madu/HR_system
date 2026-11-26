from django.urls import path
from .views import OnboardingTaskDetailView, OnboardingTaskListCreateView

urlpatterns = [
    path("organizations/<uuid:organization_id>/onboarding/tasks/", OnboardingTaskListCreateView.as_view()),
    path("organizations/<uuid:organization_id>/onboarding/tasks/<uuid:task_id>/", OnboardingTaskDetailView.as_view()),
]
