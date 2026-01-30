import logging

from weatherapp.models import City

logger = logging.getLogger('api')


def run():
    # Данные городов Беларуси
    cities_data = [
        # Областные центры
        {"name": "Минск", "latitude": 53.904539, "longitude": 27.561523},
        {"name": "Гомель", "latitude": 52.434500, "longitude": 30.975400},
        {"name": "Могилёв", "latitude": 53.900000, "longitude": 30.333330},
        {"name": "Витебск", "latitude": 55.190400, "longitude": 30.204900},
        {"name": "Гродно", "latitude": 53.688400, "longitude": 23.825800},
        {"name": "Брест", "latitude": 52.097500, "longitude": 23.687700},

        # Крупные города
        {"name": "Бобруйск", "latitude": 53.150000, "longitude": 29.233330},
        {"name": "Барановичи", "latitude": 53.132200, "longitude": 26.013900},
        {"name": "Борисов", "latitude": 54.227900, "longitude": 28.505000},
        {"name": "Пинск", "latitude": 52.114000, "longitude": 26.102000},
        {"name": "Орша", "latitude": 54.507500, "longitude": 30.417200},
        {"name": "Мозырь", "latitude": 52.050000, "longitude": 29.233330},
        {"name": "Солигорск", "latitude": 52.800000, "longitude": 27.533330},
        {"name": "Лида", "latitude": 53.883330, "longitude": 25.299720},
        {"name": "Новополоцк", "latitude": 55.533330, "longitude": 28.650000},
        {"name": "Полоцк", "latitude": 55.485600, "longitude": 28.804200},
        {"name": "Жлобин", "latitude": 52.892200, "longitude": 30.028100},
        {"name": "Светлогорск", "latitude": 52.629200, "longitude": 29.733900},
        {"name": "Речица", "latitude": 52.371700, "longitude": 30.394400},
        {"name": "Жодино", "latitude": 54.098300, "longitude": 28.332500},

        # Средние города
        {"name": "Молодечно", "latitude": 54.316670, "longitude": 26.850000},
        {"name": "Слуцк", "latitude": 53.027500, "longitude": 27.550000},
        {"name": "Кобрин", "latitude": 52.216670, "longitude": 24.366670},
        {"name": "Волковыск", "latitude": 53.159170, "longitude": 24.455280},
        {"name": "Калинковичи", "latitude": 52.133330, "longitude": 29.333330},
        {"name": "Сморгонь", "latitude": 54.483330, "longitude": 26.400000},
        {"name": "Рогачёв", "latitude": 53.095000, "longitude": 30.048600},
        {"name": "Осиповичи", "latitude": 53.299440, "longitude": 28.642220},
        {"name": "Горки", "latitude": 54.283330, "longitude": 30.983330},
        {"name": "Новогрудок", "latitude": 53.600000, "longitude": 25.833330},
        {"name": "Лунинец", "latitude": 52.250000, "longitude": 26.800000},
        {"name": "Щучин", "latitude": 53.604440, "longitude": 24.743060},
        {"name": "Ивацевичи", "latitude": 52.716670, "longitude": 25.333330},
        {"name": "Дзержинск", "latitude": 53.683330, "longitude": 27.150000},
        {"name": "Поставы", "latitude": 55.116670, "longitude": 26.833330},
        {"name": "Лепель", "latitude": 54.883330, "longitude": 28.700000},
        {"name": "Кричев", "latitude": 53.710280, "longitude": 31.714170},
        {"name": "Добруш", "latitude": 52.420280, "longitude": 31.320280},
        {"name": "Глубокое", "latitude": 55.133330, "longitude": 27.683330},
        {"name": "Вилейка", "latitude": 54.491670, "longitude": 26.904170},
        {"name": "Слоним", "latitude": 53.086940, "longitude": 25.321390},
        {"name": "Климовичи", "latitude": 53.608890, "longitude": 31.951940},
        {"name": "Новолукомль", "latitude": 54.661940, "longitude": 29.150830},
        {"name": "Пружаны", "latitude": 52.556670, "longitude": 24.464440},
        {"name": "Марьина Горка", "latitude": 53.508330, "longitude": 28.147220},
        {"name": "Жабинка", "latitude": 52.200000, "longitude": 24.016670},
    ]
    cities_to_create = []
    # 1. Проверяем существующие города чтобы не создавать дубликаты
    existing_city_names = set(City.objects.values_list('name', flat=True))

    for city_data in cities_data:
        city_name = city_data['name']

        # Пропускаем если город уже существует
        if city_name in existing_city_names:
            logger.info(f"город {city_name} уже существует")
            continue

        # Создаем объект City
        city = City(
            name=city_name,
            latitude=city_data['latitude'],
            longitude=city_data['longitude'],
        )
        cities_to_create.append(city)

    created_objects = City.objects.bulk_create(
        cities_to_create,  # Вот это важно!
        batch_size=100
    )
    created_count = len(created_objects)
    logger.info(f"Успешно создано {created_count} городов")

