from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import sys


def test_chromedriver():
    print("Запуск теста ChromeDriver...")
    try:
        # Автоматически загружаем и настраиваем ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)

        # Открываем страницу и проверяем заголовок
        driver.get("https://www.google.com")
        print(f"Заголовок страницы: {driver.title}")

        # Проверяем, что браузер открылся
        if "Google" in driver.title:
            print("✅ ChromeDriver работает корректно!")
        else:
            print(
                "⚠️  Браузер открылся, но страница не та."
            )

        driver.quit()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("Проверьте:")
        print("  - Установлен ли Chrome?")
        print(
            "  - Совпадают ли версии Chrome и ChromeDriver?"
        )
        print(
            "  - Добавлен ли ChromeDriver в PATH или указан ли путь в коде?"
        )


if __name__ == "__main__":
    test_chromedriver()
