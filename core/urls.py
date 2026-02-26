from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'unidades', views.UnidadeGestoraViewSet)
router.register(r'despesas', views.DespesaViewSet)
router.register(r'licitacoes', views.LicitacaoViewSet)
router.register(r'servidores', views.ServidorViewSet)
router.register(r'esic', views.EsicPedidoViewSet)

urlpatterns = [
    path('', views.home, name='home'),
    path('api/esic/submit/', views.submit_esic_request, name='submit_esic_request'),
    path('api/', include(router.urls)),
    path('api/register/', views.register_user, name='register_user'),
]
