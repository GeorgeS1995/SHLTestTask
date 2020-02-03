from abc import ABC
from django.core.exceptions import ObjectDoesNotExist
from .models import Vacancy, AbilityTest, AbilityTest_Response
from rest_framework import serializers
from django.contrib.auth.models import User
import hashlib


class VacancySerializer(serializers.ModelSerializer):
    state = serializers.CharField(source='state.status', read_only=True)
    id = serializers.IntegerField(source='external_id', read_only=True)
    title = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    owner = serializers.IntegerField(read_only=True)

    class Meta:
        model = Vacancy
        fields = ['id', 'title', 'description', 'state', 'owner', 'inner_owner']


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class AbilityTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbilityTest
        fields = ['slug', 'title', 'description', 'is_active', 'vacancy']

    def validate_vacancy(self, value):
        if len(value) == 0:
            return value
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        try:
            vacancy = Vacancy.objects.get(inner_owner=user)
        except ObjectDoesNotExist:
            raise serializers.ValidationError("Attempt to assign a vacancy that does not belong to an authorized user")
        if vacancy.id == value[0].id:
            return value
        raise serializers.ValidationError("Attempt to assign a vacancy that does not belong to an authorized user")


class HashLinkField(serializers.Field, ABC):
    def to_representation(self, obj):
        hashing_string = "{}{}{}".format(obj.abilitytest.slug, obj.response.vacancy_id, obj.response.candidate_id)
        return "https://example.com/" + hashlib.md5(hashing_string.encode('utf-8')).hexdigest()


class TestNameField(serializers.ModelSerializer):
    title = serializers.CharField(source="abilitytest.title", read_only=True)
    hash_link = HashLinkField(source="*", read_only=True)

    class Meta:
        model = AbilityTest_Response
        fields = ["title", "hash_link"]


class ResponseSerializer(serializers.ModelSerializer):
    test = TestNameField(source="abilitytest_response_set", many=True, read_only=True)
    candidate = serializers.CharField(source="candidate_id", read_only=True)

    class Meta:
        model = AbilityTest_Response
        fields = ["candidate", "test"]
