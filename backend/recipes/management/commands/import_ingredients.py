import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient, MeasurementUnit


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

                print(f'Из файла получена единица измерения: {unit_name}')
                print(f'Из файла получен ингредиент: {ingredient_name}')

                unit, created_unit = MeasurementUnit.objects.get_or_create(abbreviation=unit_name)
                if created_unit:
                    self.stdout.write(self.style.SUCCESS(f'Создана единица измерения: {unit_name}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Дубликат единицы измерения: {unit_name}'))

                ingredient, created_ingredient = Ingredient.objects.get_or_create(name=ingredient_name,
                                                                                  measurement_unit=unit)
                if created_ingredient:
                    self.stdout.write(self.style.SUCCESS(f'Создан ингредиент: {ingredient_name}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Дубликат ингредиента: {ingredient_name}', ))
                print()

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('Файл не найден. Пожалуйста, убедитесь, что JSON файл существует.'))
