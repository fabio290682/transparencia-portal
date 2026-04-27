from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"unidades", views.UnidadeGestoraViewSet)
router.register(r"despesas", views.DespesaViewSet)
router.register(r"licitacoes", views.LicitacaoViewSet)
router.register(r"servidores", views.ServidorViewSet)
router.register(r"esic", views.EsicPedidoViewSet)

urlpatterns = [
    path("", views.home, name="home"),
    path("portal-moderno/", views.portal_moderno, name="portal_moderno"),
    path("portal-3d/", views.portal_3d, name="portal_3d"),
    path("painel/", views.painel_admin, name="painel_admin"),
    path("api/dashboard/", views.dashboard_stats, name="dashboard_stats"),
    path("health/", views.health, name="health"),
    path("api/health/", views.health, name="api_health"),
    path("api/public/portal-info/", views.public_portal_info, name="public_portal_info"),
    path("api/portal-info/", views.public_portal_info, name="portal_info_alias"),
    path("api/esic/submit/", views.submit_esic_request, name="submit_esic_request"),
    path("api/", include(router.urls)),
    path("api/register/", views.register_user, name="register_user"),
]

