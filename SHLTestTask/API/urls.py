from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import VacancyView, UserView, AbilityTesView, ResponseView

router_v1 = DefaultRouter()
router_v1.register('vacancy', VacancyView, basename='vacancy')
router_v1.register('user', UserView)
router_v1.register('abilitytest', AbilityTesView)
router_v1.register('response', ResponseView, basename='response')

urlpatterns = [
    path('v1/', include(router_v1.urls)),
    path('auth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
]
