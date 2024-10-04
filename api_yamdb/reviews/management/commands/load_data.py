from reviews.models import Category, Genre, Title
import csv
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Загрузка данных из CSV файлов в базу данных'

    def handle(self, *args, **kwargs):
        # Загрузка категорий
        with open('static/data/category.csv', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                Category.objects.get_or_create(
                    id=row['id'],
                    name=row['name'],
                    slug=row['slug']
                )
        self.stdout.write(self.style.SUCCESS('category.csv загружены.'))

        # Загрузка жанров
        with open('static/data/genre.csv', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                Genre.objects.get_or_create(
                    id=row['id'],
                    name=row['name'],
                    slug=row['slug']
                )
        self.stdout.write(self.style.SUCCESS('genre.csv загружены'))

        # Загрузка произведений
        with open('static/data/titles.csv', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    category = Category.objects.get(id=row['category'])
                    Title.objects.get_or_create(
                        id=row['id'],
                        name=row['name'],
                        year=row['year'],
                        category=category,
                    )
                except Category.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Такой категории'{row['category']}' не существует"))
        self.stdout.write(self.style.SUCCESS('titles.csv загружены'))
