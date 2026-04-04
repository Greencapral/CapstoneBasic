from django.core.management.base import BaseCommand
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from web_scraping.scrapy_app.scrapy_app.spiders.wb_spider import (
    WbSearchSpider,
)


class Command(BaseCommand):
    help = "Запускает скрапинг товаров с Wildberries"

    def add_arguments(self, parser):
        parser.add_argument("search_query", type=str, help="Строка поиска")
        parser.add_argument(
            "--max-pages",
            type=int,
            default=3,
            help="Количество страниц для скрапинга",
        )
        # parser.add_argument('--marketplace-id', type=int, required=True, help='ID маркетплейса в базе данных')

    def handle(self, *args, **options):
        search_query = options["search_query"]
        max_pages = options["max_pages"]
        # marketplace_id = options['marketplace_id']

        process = CrawlerProcess(get_project_settings())
        process.crawl(
            WbSearchSpider,
            search_query=search_query,
            max_pages=max_pages,
            marketplace_id=1,
        )
        process.start()
        self.stdout.write(self.style.SUCCESS("Скрапинг завершён!"))
