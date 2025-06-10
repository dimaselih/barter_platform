# Barter Platform

Платформа для обмена вещами (бартерная система) на Django.

## Описание

Веб-приложение позволяет пользователям размещать объявления о товарах для обмена, просматривать чужие объявления и отправлять предложения на обмен.

## Функциональности

- Создание, редактирование и удаление объявлений
- Поиск и фильтрация объявлений
- Система обмена предложениями
- Архив обмененных товаров
- Категории товаров
- Статусы объявлений (активно/обменяно)

## Технологии

- Python 3.8+
- Django 4+
- Bootstrap 5
- SQLite/PostgreSQL

## Установка и запуск

1. Клонируйте репозиторий:
```bash
git clone https://github.com/dimaselih/barter-platform
cd barter-platform
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate  # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Примените миграции:
```bash
python manage.py migrate
```

5. Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

6. Запустите сервер:
```bash
python manage.py runserver
```

## Тестирование

Для запуска тестов используйте команду:
```bash
python manage.py test
```

