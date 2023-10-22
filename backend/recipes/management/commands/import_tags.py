import json

from django.core.management.base import BaseCommand

from recipes.models import Tag


class Command(BaseCommand):
    help = 'Импорт ингредиентов из JSON файла'

    def handle(self, *args, **options):
        json_file_path = 'recipes/management/commands/data/tags.json'

        try:
            # Открываем JSON файл для чтения
            with open(json_file_path, 'r', encoding='utf-8') as file:
                tags = json.load(file)

            # Проходим по данным JSON и создаем записи в базе данных
            for tag in tags:
                Tag.objects.create(
                    name=tag['name'],
                    color_code=tag['color'],
                    slug=tag['slug']
                )

                self.stdout.write(self.style.SUCCESS(
                    f"Создан тег: {tag['name']}"))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                'Файл не найден. Пожалуйста,'
                ' убедитесь, что JSON файл существует.')
            )
