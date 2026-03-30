from django.db import models


class BaseModel(models.Model):
    class Meta:
        abstract = True

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Создано"
    )

    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Изменено"
    )

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()
