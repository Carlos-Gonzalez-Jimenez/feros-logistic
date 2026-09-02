from django.urls import include, path
from rest_framework.routers import DefaultRouter

from user import views

router = DefaultRouter()

router.register(r"employees", views.EmployeeViewSet, basename="employees")
router.register(r"clients", views.UserViewSet, basename="clients")
router.register(r"roles", views.RoleViewSet, basename="roles")
router.register(r"permissions", views.PermissionViewSet, basename="permissions")
router.register(r"event-logs", views.EventLogViewSet, basename="event-logs")
router.register(r"fees", views.FeeViewSet, basename="fees")
router.register(r"organizations", views.OrganizationViewSet, basename="organizations")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "register-client/", views.RegisterUserAPIView.as_view(), name="register-client"
    ),
    path(
        "confirm-register/",
        views.ConfirmRegisterView.as_view(),
        name="confirm-register",
    ),
    path(
        "register-employee/",
        views.RegisterEmployeeAPIView.as_view(),
        name="register-employee",
    ),
    path(
        "password-change/", views.ChangePasswordView.as_view(), name="password-change"
    ),
    path(
        "password-recovery/",
        views.RecoverPasswordView.as_view(),
        name="password-recovery",
    ),
    path("password-recover/change/", views.ChangeRecoverPasswordView.as_view()),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
]
