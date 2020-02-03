from __future__ import absolute_import, unicode_literals
from celery import shared_task
import logging
import requests
from url_normalize import url_normalize
from django.core.exceptions import ObjectDoesNotExist

from .models import Vacancy, VacancyStatus, Responce, AbilityTest, AbilityTest_Response

lh = logging.getLogger(__name__)


def vacancy_sync(ready_response):
    new_id = []
    for value in ready_response:
        new_id.append(value['id'])
        status, ok = VacancyStatus.objects.get_or_create(status=value['state'])
        Vacancy.objects.update_or_create(external_id=value['id'], defaults={'title': value['title'],
                                                                            'description': value['description'],
                                                                            'state_id': status.id,
                                                                            'owner': value['owner']})
    try:
        obj = VacancyStatus.objects.get(status="ARCHIVE")
    except ObjectDoesNotExist as err:
        lh.error("Status 'ARCHIVE not found: {}'".format(err))
    Vacancy.objects.exclude(external_id__in=new_id).update(state_id=obj.id)


def response_sync(ready_responce):
    for value in ready_responce:
        candidate_resp = Responce.objects.create(candidate_id=value['candidate_id'],
                                                 vacancy_id=value["vacancy_id"],
                                                 external_id=value["id"])
        candidate_resp.save()
        tests_list = AbilityTest.objects.filter(vacancy=value["vacancy_id"]).exclude(is_active=False)
        if tests_list is None:
            lh.warning("Ability tests for vacancy {} not configured".format(value["vacancy_id"]))
            continue

        for test in tests_list:
            a_obj = AbilityTest_Response.objects.create(abilitytest_id=test.id, response_id=candidate_resp.id)
            a_obj.save()


def request_to_service(host):
    try:
        r = requests.get(host)
        r.raise_for_status()
    except requests.exceptions.ReadTimeout:
        lh.error("request read timeout")
        return
    except requests.exceptions.ConnectTimeout:
        lh.error("request connection timeout")
        return
    except requests.exceptions.ConnectionError as err:
        lh.error("connection error: {}".format(err))
        return
    except requests.exceptions.HTTPError as err:
        lh.error("HTTP error. {}".format(err))
        return
    except requests.exceptions as err:
        lh.error("Unhandled error: {}", err)
        return
    return r.json()


@shared_task()
def get_vacancy_list(**kwargs):
    host = kwargs['host']

    ready_response = request_to_service(host)

    vacancy_sync(ready_response)


@shared_task()
def get_response_list(**kwargs):
    host = url_normalize('{}/{}/applications/'.format(kwargs['host'], kwargs['vacancy_id']))

    ready_response = request_to_service(host)

    response_sync(ready_response)
