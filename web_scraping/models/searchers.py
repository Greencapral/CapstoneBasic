from django.db import models
from web_scraping.models import BaseModel
from custom_user_app.models import CustomUser


class Searchers(BaseModel):

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )

    query = models.CharField(
        max_length=100, verbose_name="Поисковый запрос"
    )