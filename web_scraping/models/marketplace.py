from django.db import models
from web_scraping.models import BaseModel


class Marketplace(BaseModel):
    """
    Модель маркетплейса.
    Описывает торговую площадку для веб‑скрапинга. Наследует общие поля
    и методы от BaseModel (created_at, updated_at). Содержит информацию
    о названии и базовом URL маркетплейса.
    """
    class Meta:
        """Метаданные модели для админ‑панели и интерфейса."""
        verbose_name = "Маркетплейс"  # Человекочитаемое имя модели в единственном числе
        verbose_name_plural = "Маркетплейсы"  # Человекочитаемое имя модели во множественном числе

    """Название маркетплейса. Максимальная длина — 100 символов."""
    name = models.CharField(
        max_length=100,
        verbose_name="Название маркетплейса",
    )

    """Базовый URL маркетплейса. Поле автоматически валидирует корректность URL."""
    base_url = models.URLField(verbose_name="Базовый URL")

    def __repr__(self):
        """
        Возвращает официальное строковое представление объекта.
        Используется для отладки и вывода подробной информации об объекте в консоли.
        Содержит ID, название и базовый URL маркетплейса в структурированном формате.

        Returns:
            str: Строка вида '<Marketplace id=X, name='Name', base_url='URL'>'.
        """
        return f"<Marketplace id={self.pk}, name='{self.name}', base_url='{self.base_url}'>"
