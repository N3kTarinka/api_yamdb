import csv
from django.core.management.base import BaseCommand
from reviews.models import Category, Genre, Title

class Command(BaseCommand):
    help = 'Загрузка данных из CSV файлов в базу данных'

    def handle(self, *args, **kwargs):
        # Загрузка категорий
        with open('static/data/category.csv', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                Category.objects.get_or_create(
                    name=row['name'],
                    slug=row['slug']
                )
        self.stdout.write(self.style.SUCCESS('Categories loaded successfully.'))

        # Загрузка жанров
        with open('static/data/genre.csv', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                Genre.objects.get_or_create(
                    name=row['name'],
                    slug=row['slug']
                )
        self.stdout.write(self.style.SUCCESS('Genres loaded successfully.'))

        # Загрузка произведений
        with open('static/data/titles.csv', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                category = Category.objects.get(slug=row['category'])
                title, created = Title.objects.get_or_create(
                    name=row['name'],
                    year=row['year'],
                    description=row.get('description', ''),
                    category=category,
                )
                # Если в CSV-файле есть данные о жанрах
                if row.get('genre'):
                    genres = row['genre'].split(',')
                    for genre_slug in genres:
                        genre = Genre.objects.get(slug=genre_slug)
                        title.genre.add(genre)
        self.stdout.write(self.style.SUCCESS('Titles loaded successfully.'))

