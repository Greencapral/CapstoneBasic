from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import (
    ActionChains,
)
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from django.db import transaction
import time
import random

from web_scraping.models import (
    Product,
    Marketplace,
)
from config import is_docker_container

class Parser:
    def __init__(self, name_mp, headless=True):
        self.headless = headless
        self.driver = None
        self.sb = None
        self.marketplace = None
        self.search_query = None
        self.marketplace = Marketplace.objects.get(name=name_mp)
        print(
            f"Marketplace найден: {self.marketplace}, ID: {self.marketplace.id}"
        )

    def setup_driver(self):
        options = Options()
        if self.headless:
            options.add_argument("--headless")

        # Базовые опции для обхода защиты
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option(
            "excludeSwitches", ["enable-automation"]
        )
        options.add_experimental_option("useAutomationExtension", False)

        # Дополнительные опции для маскировки
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")

        # Разрешение экрана и User-Agent
        options.add_argument("--window-size=1920,1080")
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        options.add_argument(f"--user-agent={user_agent}")

        try:
            service = Service(ChromeDriverManager().install())
            if is_docker_container():
                self.driver = webdriver.Remote(command_executor='http://selenium:4444/wd/hub', options=options)
            else:
                self.driver = webdriver.Chrome(service=service, options=options)

            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

        except Exception as e:
            print(f"Ошибка инициализации драйвера: {e}")
            raise

    @transaction.atomic
    def save_products_to_db(self, products_data):
        saved_count = 0
        all_product_ids = []

        if self.marketplace is None:
            print(
                "Ошибка: marketplace не инициализирован. Запускаем setup_driver()"
            )
            self.setup_driver()

        for product_data in products_data:
            try:
                all_product_ids.append(product_data["product_id"])
                try:
                    existing_product = Product.objects.get(
                        product_id=product_data["product_id"],
                        marketplace=self.marketplace,
                    )
                    if existing_product.price == product_data["price"]:
                        print(
                            f"Цена не изменилась для товара '{product_data['name']}' (ID: {product_data['product_id']}), пропускаем сохранение"
                        )
                        continue
                    else:
                        print(
                            f"Цена изменилась для товара '{product_data['name']}' (ID: {product_data['product_id']}): "
                            f"{existing_product.price} → {product_data['price']}"
                        )
                        existing_product.name = product_data["name"]
                        existing_product.image_url = product_data.get("image_url")
                        existing_product.url = product_data.get("url")
                        existing_product.price = product_data["price"]
                        existing_product.save()
                        saved_count += 1

                except Product.DoesNotExist:
                    new_product = Product.objects.create(
                        product_id=product_data["product_id"],
                        marketplace=self.marketplace,
                        name=product_data["name"],
                        price=product_data["price"],
                        image_url=product_data.get("image_url"),
                        url=product_data.get("url"),
                    )
                    saved_count += 1
                    print(
                        f"Добавлен новый товар: '{product_data['name']}' (ID: {product_data['product_id']})"
                    )

                except Exception as save_error:
                    print(
                        f"Ошибка сохранения товара {product_data.get('name', 'Unknown')}: {save_error}"
                    )
                    continue

            except Exception as e:
                print(f"Ошибка обработки товара: {e}")
                continue
        print(f"Успешно сохранено/обновлено {saved_count} товаров")
        return {
            "saved_count": saved_count,
            "total_found": len(products_data),
            "search_query": self.search_query,
            "product_ids": all_product_ids  # Возвращаем список ID
        }

    def close(self):
        """Безопасное закрытие драйвера"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def human_like_actions(self):
        try:
            window_size = self.driver.get_window_size()
            max_x = window_size["width"] - 100
            max_y = window_size["height"] - 100

            if max_x < 100 or max_y < 100:
                print("Окно слишком маленькое для имитации действий")
                return

            actions = ActionChains(self.driver)

            body = self.driver.find_element(By.TAG_NAME, "body")

            for _ in range(random.randint(2, 5)):
                x = random.randint(50, max_x)
                y = random.randint(50, max_y)

                try:
                    actions.move_to_element_with_offset(body, x, y).perform()
                    time.sleep(random.uniform(0.3, 1.2))
                    actions.reset_actions()  # сброс действий
                except Exception as e:
                    print(f"Ошибка движения мыши в позиции ({x}, {y}): {e}")
                    continue

            scroll_height = self.driver.execute_script("return document.body.scrollHeight;")
            current_scroll = 0

            while current_scroll < scroll_height:
                scroll_step = random.randint(100, 300)
                current_scroll += scroll_step

                if current_scroll > scroll_height:
                    current_scroll = scroll_height

                self.driver.execute_script(f"window.scrollTo(0, {current_scroll});")
                time.sleep(random.uniform(0.8, 2.0))

                if random.random() < 0.3:  # 30% шанс
                    x = random.randint(50, max_x)
                    y = random.randint(50, max_y)
                    try:
                        actions.move_to_element_with_offset(body, x, y).perform()
                        time.sleep(random.uniform(0.2, 0.8))
                        actions.reset_actions()
                    except:
                        pass

            center_x = window_size["width"] // 2
            center_y = window_size["height"] // 2
            try:
                actions.move_to_element_with_offset(body, center_x, center_y).perform()
                actions.reset_actions()
            except:
                pass

        except Exception as e:
            print(f"Критическая ошибка имитации действий: {e}")

