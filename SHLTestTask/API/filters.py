from django_filters import rest_framework as rf_filter
from .models import Vacancy


class VacancyFilter(rf_filter.FilterSet):
    state = rf_filter.CharFilter(field_name='state__status')

    class Meta:
        model = Vacancy
        fields = ['state', 'owner', 'inner_owner']