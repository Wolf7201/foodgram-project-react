import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов из JSON файла'

    def handle(self, *args, **options):
        json_file_path = 'recipes/management/commands/data/ingredients.json'

        try:
            # Открываем JSON файл для чтения
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            # Проходим по данным JSON и создаем записи в базе данных
            for item in data:
                unit_name = item['measurement_unit']
                ingredient_name = item['name']

                print(f'Из файла получена единица измерения:'
                      f' {unit_name}')
                print(f'Из файла получен ингредиент:'
                      f' {ingredient_name}')

                ingredient, created_ingredient = (
                    Ingredient.
                    objects.get_or_create(
                        name=ingredient_name,
                        measurement_unit=unit_name))
                if created_ingredient:
                    self.stdout.write(self.style.SUCCESS(
                        f'Создан ингредиент: {ingredient_name}'))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'Дубликат ингредиента: {ingredient_name}', ))
                print()

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                'Файл не найден. Пожалуйста,'
                ' убедитесь, что JSON файл существует.')
            )
