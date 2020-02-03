from .filters import VacancyFilter
from rest_framework import viewsets, permissions
from django.contrib.auth.models import User
from .models import Vacancy, AbilityTest, Responce
from .serializers import VacancySerializer, UserSerializer, AbilityTestSerializer, ResponseSerializer
from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope
from .permissions import SaveOnlyMethods, VacancyChangePermission


# Create your views here.


class VacancyView(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, TokenHasReadWriteScope, VacancyChangePermission]
    serializer_class = VacancySerializer
    filterset_class = VacancyFilter

    def get_queryset(self):
        if self.request.query_params.get('state') is None and self.request.method == 'GET':
            return Vacancy.objects.all().exclude(state__status='ARCHIVE').order_by('id')
        return Vacancy.objects.all().order_by('id')


class UserView(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, TokenHasReadWriteScope, SaveOnlyMethods]
    serializer_class = UserSerializer
    queryset = User.objects.exclude(groups__name='Technical users').order_by('id')

    def get_object(self):
        pk = self.kwargs.get('pk')

        if pk == "current":
            return self.request.user

        return super(UserView, self).get_object()


class AbilityTesView(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, TokenHasReadWriteScope]
    queryset = AbilityTest.objects.all().exclude(is_active=False).order_by('id')
    serializer_class = AbilityTestSerializer


class ResponseView(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, TokenHasReadWriteScope]
    serializer_class = ResponseSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Responce.objects.filter(vacancy__inner_owner=user).order_by("id")
        return queryset
