from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class VacancyStatus(models.Model):
    status = models.CharField(max_length=100)


class Vacancy(models.Model):
    external_id = models.IntegerField(null=True)
    title = models.CharField(max_length=100)
    description = models.TextField(null=True)
    state = models.ForeignKey(VacancyStatus, on_delete=models.DO_NOTHING)
    owner = models.IntegerField(null=True)
    inner_owner = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, default=None)


class AbilityTest(models.Model):
    slug = models.SlugField(null=False)
    title = models.CharField(max_length=250)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    vacancy = models.ManyToManyField(Vacancy, blank=True)


class Responce(models.Model):
    candidate_id = models.IntegerField()
    vacancy = models.ForeignKey(Vacancy, on_delete=models.DO_NOTHING)
    create_at = models.DateTimeField(auto_now_add=True)
    external_id = models.IntegerField(null=True)


class AbilityTest_Response(models.Model):
    abilitytest = models.ForeignKey(AbilityTest, on_delete=models.DO_NOTHING)
    response = models.ForeignKey(Responce, on_delete=models.DO_NOTHING)
    grade = models.IntegerField(null=True)
    solve_at = models.DateTimeField(null=True)