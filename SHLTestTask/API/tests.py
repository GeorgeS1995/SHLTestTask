from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from .models import Vacancy, VacancyStatus, AbilityTest, AbilityTest_Response, Responce
from django.contrib.auth.models import User, Group
from rest_framework import status
from .serializers import VacancySerializer, AbilityTestSerializer
from .tasks import vacancy_sync, response_sync
from oauth2_provider.models import AccessToken, Application
from django.utils import timezone
from guardian.shortcuts import assign_perm


# Create your tests here.

class ApiUserTestClient(APITestCase):
    """
    Helper base class for API test
    """
    client = APIClient()

    @classmethod
    def setUpTestData(cls):
        cls.group = Group.objects.create(
            name='Technical users'
        )
        cls.anon = User.objects.get(id=1)
        cls.group.user_set.add(cls.anon)
        cls.user = User.objects.create(
            username='test@test.com',
            email='test@test.com',
            password='12345',
            is_active=True,
        )
        cls.user.set_password('12345')
        cls.user.save()

        assign_perm('auth.view_user', cls.user)

        cls.application = Application.objects.create(
            name="Test Application",
            redirect_uris="http://localhost http://example.com http://example.org",
            user=cls.user,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        )

        cls.access_token = AccessToken.objects.create(
            user=cls.user,
            scope="read write",
            expires=timezone.now() + timezone.timedelta(seconds=300),
            token="secret-access-token-key",
            application=cls.application
        )
        cls.access_token.save()
        cls.application.save()

        cls.client.force_authenticate(user=cls.user, token=cls.access_token.token)

        for new_status in ['ARCHIVE', 'ACTIVE']:
            cls.vacancy_status_obj = VacancyStatus.objects.create(status=new_status)
            cls.vacancy_status_obj.save()
        cls.vacancy_obj = Vacancy.objects.create(external_id=1, title='Vacancy 1', state_id=1)
        cls.vacancy_obj.save()

        cls.vacancy_obj = Vacancy.objects.create(external_id=2, title='Vacancy 2', state_id=2, owner=5631,
                                                 description='Vacancy description long text', inner_owner_id=1)
        cls.vacancy_obj.save()

        cls.response_1 = Responce.objects.create(candidate_id=123, vacancy_id=1)
        cls.response_1.save()
        cls.response_2 = Responce.objects.create(candidate_id=555, vacancy_id=1)
        cls.response_2.save()

        cls.ability_obj_1 = AbilityTest.objects.create(slug='slug-test-1', title='test 1', description='desc')
        cls.ability_obj_1.save()
        cls.ability_obj_2 = AbilityTest.objects.create(slug='slug-test-2', title='test 2', description='desc')
        cls.ability_obj_2.save()

        cls.ability_test__response = AbilityTest_Response.objects.create(abilitytest_id=cls.ability_obj_1.id,
                                                                         response_id=cls.response_1.id)
        cls.ability_test__response.save()
        cls.ability_test__response = AbilityTest_Response.objects.create(abilitytest_id=cls.ability_obj_2.id,
                                                                         response_id=cls.response_1.id)
        cls.ability_test__response.save()
        cls.ability_test__response = AbilityTest_Response.objects.create(abilitytest_id=cls.ability_obj_2.id,
                                                                         response_id=cls.response_2.id)
        cls.ability_test__response.save()

        cls.test_candidate_test_links = [
            {
                "candidate": "123",
                "test": [
                    {
                        "title": "test 1",
                        "hash_link": "https://example.com/b5a8d0e1488e77d289f33ac0b48b0896"
                    },
                    {
                        "title": "test 2",
                        "hash_link": "https://example.com/d6208b4bf70fa491a9370694c746e31a"
                    }
                ]
            },
            {
                "candidate": "555",
                "test": [
                    {
                        "title": "test 2",
                        "hash_link": "https://example.com/fc36795132dfd358d07f662937338a8b"
                    }
                ]
            }
        ]

        cls.test_user_list = [
            {
                "id": 2,
                "username": "test@test.com",
                "first_name": "",
                "last_name": "",
                "email": "test@test.com"
            }
        ]

        cls.vacancy_list_exp = [
            {
                "id": 2,
                "title": "Vacancy 2",
                "description": "Vacancy description long text",
                "state": "ACTIVE",
                "owner": 5631,
                "inner_owner": 1
            }
        ]

        cls.vacancy_list_filtered_by_owner = [
            {
                "id": 2,
                "title": "Vacancy 2",
                "description": "Vacancy description long text",
                "state": "ACTIVE",
                "owner": 5631,
                "inner_owner": 1
            }
        ]

        cls.vacancy_list_filter_by_status = [
            {
                "id": 1,
                "title": "Vacancy 1",
                "description": None,
                "state": "ARCHIVE",
                "owner": None,
                "inner_owner": None
            }
        ]

        cls.vacancy_change_owner = {
            "id": 100,
            "title": "Vacancy 100",
            "description": "newdiscr",
            "state": "ACTIVE",
            "owner": 100,
            "inner_owner": 1
        }

        cls.add_abilitytest_data = {
            "slug": "slug-test-3",
            "title": "test 3",
            "description": "desc",
            "is_active": True,
            "vacancy": []
        }

    def setUp(self):
        self.login()

    def tearDown(self):
        self.logout()

    def login(self):
        self.client.credentials(Authorization='Bearer {}'.format(self.access_token.token))

    def logout(self):
        self.token = None


class VacancyViewTestCase(ApiUserTestClient):

    def test_vacancy_list(self):
        self.login()
        response = self.client.get(reverse('vacancy-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], self.vacancy_list_exp)

    def test_vacancy_list_filter_by_owner(self):
        self.login()
        response = self.client.get(reverse('vacancy-list'), {"owner": 5631})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], self.vacancy_list_filtered_by_owner)

    def test_vacancy_list_filter_by_status(self):
        self.login()
        response = self.client.get(reverse('vacancy-list'), {"state": 'ARCHIVE'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], self.vacancy_list_filter_by_status)

    def test_vacancy_change_owner(self):
        self.login()
        response = self.client.patch(reverse('vacancy-list') + '1/', self.vacancy_change_owner)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        db = Vacancy.objects.get(id=1)
        serialized_db = VacancySerializer(db)
        self.assertNotEqual(serialized_db.data, self.vacancy_change_owner)
        self.assertEqual(serialized_db.data, response.data)

    def test_vacancy_change_owner_per(self):
        self.login()
        response = self.client.patch(reverse('vacancy-list') + '1/', self.vacancy_change_owner)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.patch(reverse('vacancy-list') + '1/', self.vacancy_change_owner)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserViewTestCase(ApiUserTestClient):

    def test_get_user(self):
        self.login()
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], self.test_user_list)

    def test_current_user(self):
        self.login()
        response = self.client.get(reverse('user-list') + 'current/')
        self.assertEqual(response.data["id"], self.user.id)

    def test_user_unsafe_methods(self):
        self.login()
        response = self.client.post(reverse('user-list') + '1/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        response = self.client.put(reverse('user-list') + '1/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        response = self.client.patch(reverse('user-list') + '1/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        response = self.client.delete(reverse('user-list') + '1/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class AbilityTestViewTestCase(ApiUserTestClient):

    def test_add_abilitytest(self):
        self.login()
        response = self.client.post(reverse('abilitytest-list'), self.add_abilitytest_data)
        db = AbilityTest.objects.get(id=3)
        serialized_db = AbilityTestSerializer(db)
        self.assertEqual(serialized_db.data, response.data)

    def test_change_abilitytest(self):
        self.login()
        response = self.client.patch(reverse('vacancy-list') + '1/', {'inner_owner': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.patch(reverse('abilitytest-list') + '1/', {'vacancy': [1]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        db = AbilityTest.objects.get(id=1)
        serialized_db = AbilityTestSerializer(db)
        self.assertEqual(response.data, serialized_db.data)
        response = self.client.patch(reverse('abilitytest-list') + '1/', {'vacancy': [2]})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ResponseViewTestCase(ApiUserTestClient):

    def test_candidate_links(self):
        self.login()
        self.client.patch(reverse('vacancy-list') + '1/', {"inner_owner": 2})
        response = self.client.get(reverse('response-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], self.test_candidate_test_links)


class VacancySyncTestCase(APITestCase):

    def setUp(self) -> None:
        for new_status in ['ARCHIVE', 'ACTIVE']:
            self.vacancy_status_obj = VacancyStatus.objects.create(status=new_status)
            self.vacancy_status_obj.save()
        self.vacancy_obj = Vacancy.objects.create(external_id=1, title='Vacancy 1', state_id=1)
        self.vacancy_obj.save()

        self.vacancy_obj = Vacancy.objects.create(external_id=2, title='Vacancy 2', state_id=2, owner=5631,
                                                  description='Vacancy description long text')
        self.vacancy_obj.save()

        self.ability_obj = AbilityTest.objects.create(slug='slug-test-1', title='test 1', description='desc')
        self.ability_obj.save()
        self.ability_obj.vacancy.set([1])
        self.ability_obj = AbilityTest.objects.create(slug='slug-test-2', title='test 2', description='desc')
        self.ability_obj.save()
        self.ability_obj.vacancy.set([2])

        self.vacancy_sync_test_data = [
            {
                "id": 3,
                "title": "Vacancy 1",
                "description": None,
                "state": "ARCHIVE",
                "owner": None,
            },
            {
                "id": 4,
                "title": "Vacancy 2",
                "description": "Vacancy description long text",
                "state": "ACTIVE",
                "owner": 5601,
            },
            {
                "id": 5,
                "title": "Vacancy 3",
                "description": "Vacancy description long text",
                "state": "ACTIVE",
                "owner": 56010,
            },
            {
                "id": 6,
                "title": "Vacancy 4",
                "description": "Vacancy description long text",
                "state": "LOCK",
                "owner": 56010,
            }
        ]

        self.respose_sync_test_data = [{"id": 1, "vacancy_id": 1, "candidate_id": 62312},
                                       {"id": 2, "vacancy_id": 1, "candidate_id": 65311},
                                       {"id": 3, "vacancy_id": 2, "candidate_id": 65311}]

    def test_vacancy_sync(self):
        vacancy_sync(self.vacancy_sync_test_data)

        db_statment = Vacancy.objects.in_bulk()
        for i in db_statment:
            if i > 2:
                self.assertEqual(db_statment[i].title, self.vacancy_sync_test_data[i - 3]['title'])
                self.assertEqual(db_statment[i].owner, self.vacancy_sync_test_data[i - 3]['owner'])
                self.assertEqual(db_statment[i].state.status, self.vacancy_sync_test_data[i - 3]['state'])
                self.assertEqual(db_statment[i].description, self.vacancy_sync_test_data[i - 3]['description'])
            else:
                self.assertEqual(db_statment[i].state.status, "ARCHIVE")

    def test_response_sync(self):
        response_sync(self.respose_sync_test_data)

        ability_db = AbilityTest_Response.objects.in_bulk()
        responce_db = Responce.objects.in_bulk()

        self.assertEqual(len(ability_db) == 3, True)
        for i in responce_db:
            self.assertEqual(responce_db[i].external_id, self.respose_sync_test_data[i - 1]['id'])
            self.assertEqual(responce_db[i].vacancy.id, self.respose_sync_test_data[i - 1]['vacancy_id'])
            self.assertEqual(responce_db[i].candidate_id, self.respose_sync_test_data[i - 1]['candidate_id'])
