from django.db import models
from web_scraping.models import BaseModel


class Marketplace(BaseModel):

    name = models.CharField(
        max_length=100,
        verbose_name="Название маркетплейса",
    )

    base_url = models.URLField(verbose_name="Базовый URL")

    class Meta:
        verbose_name = "Маркетплейс"
        verbose_name_plural = "Маркетплейсы"

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Marketplace id={self.id}, name='{self.name}', base_url='{self.base_url}'>"
