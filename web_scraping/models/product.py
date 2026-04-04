from django.db import models
from web_scraping.models import BaseModel


class Product(BaseModel):

    name = models.CharField(max_length=100, verbose_name="Название товара")

    marketplace = models.ForeignKey(
        "Marketplace",
        on_delete=models.CASCADE,
        verbose_name="Маркетплейс",
    )

    product_id = models.CharField(
        max_length=255,
        verbose_name="ID товара на маркетплейсе",
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Текущая цена",
    )

    image_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="URL изображения",
    )

    url = models.URLField(verbose_name="Ссылка на товар")

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return self.name

    def __repr__(self):
        return (
            f"<Product id={self.id}, name='{self.name}', price={self.price}>"
        )
