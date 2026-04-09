from django.core.validators import MinLengthValidator
from django.db import models
from web_scraping.models import (
    BaseModel,
    Product,
    Marketplace,
)
from custom_user_app.models import CustomUser


class Searchers(BaseModel):
    """
    Модель поискового запроса пользователя.
    Описывает запрос, сделанный пользователем для поиска товаров на маркетплейсах.
    Наследует общие поля и методы от BaseModel (created_at, updated_at).
    Содержит информацию о пользователе, тексте запроса, найденных товарах и маркетплейсах,
    на которых производился поиск.
    """

    class Meta:
        """Метаданные модели для админ‑панели и интерфейса."""
        verbose_name = "Запрос"  # Человекочитаемое имя модели в единственном числе
        verbose_name_plural = "Запросы"  # Человекочитаемое имя модели во множественном числе

    """Связь с моделью CustomUser. Указывает, какой пользователь сделал запрос.
    При удалении пользователя все его поисковые запросы также будут удалены (CASCADE)."""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )

    """Текст поискового запроса. Максимальная длина — 100 символов.
    Минимальное количество символов — 2 (проверяется валидатором MinLengthValidator)."""
    query = models.CharField(
        max_length=100,
        verbose_name="Поисковый запрос",
        validators=[MinLengthValidator(2)],
    )

    """Связь многие‑ко‑многим с моделью Product. Указывает на товары,
    найденные по данному запросу. related_name позволяет обращаться
    к запросам из объекта Product через атрибут 'searches'."""
    products = models.ManyToManyField(
        Product,
        related_name="searches",
        verbose_name="Найденные товары",
    )

    """Связь многие‑ко‑многим с моделью Marketplace. Указывает,
    на каких маркетплейсах производился поиск по запросу.
    related_name позволяет обращаться к запросам из объекта Marketplace
    через атрибут 'searches'."""
    marketplaces = models.ManyToManyField(
        Marketplace,
        related_name="searches",
        verbose_name="Маркетплейсы для поиска",
    )


    def __str__(self):
        """
        Возвращает строковое представление объекта.
        Используется в админ‑панели, шаблонах и при выводе объектов в списках.
        В качестве представления выступает комбинация имени пользователя и текста запроса.

        Returns:
            str: Строка вида 'Пользователь - Поисковый запрос'.
        """
        return f'{self.user} - {self.query}'
