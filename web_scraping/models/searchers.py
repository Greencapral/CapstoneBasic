from django.core.validators import MinLengthValidator
from django.db import models
from web_scraping.models import (
    BaseModel,
    Product,
    Marketplace,
)
from custom_user_app.models import CustomUser


class Searchers(BaseModel):

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )

    query = models.CharField(
        max_length=100,
        verbose_name="Поисковый запрос",
        validators=[MinLengthValidator(2)],
    )

    products = models.ManyToManyField(
        Product,
        related_name="searches",
        verbose_name="Найденные товары",
    )

    marketplaces = models.ManyToManyField(
        Marketplace,
        related_name="searches",
        verbose_name="Маркетплейсы для поиска",
    )
