from django.db import models
from web_scraping.models import BaseModel
from web_scraping.models.product import Product
from web_scraping.models.searchers import Searchers

class SearchersProduct(BaseModel):

    Searchers = models.ForeignKey(
        Searchers,
        on_delete=models.CASCADE,
        verbose_name="Поисковый запрос",
    )
    Product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name="Название товара"
    )
