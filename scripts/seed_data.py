"""
Seed script to populate the database with initial data.
Includes categories, vehicle types, brands, body types, etc.
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.models.category import Category
from app.models.vehicle import (
    VehicleType,
    Brand,
    Model,
    Generation,
    BodyType,
    Transmission,
    FuelType,
    DriveType,
    Color,
)
from app.models.location import Country, Region, City
from app.models.user import User, UserRole
from app.core.security import hash_password


async def seed_categories(db: AsyncSession):
    """Seed categories."""
    categories = [
        {"name": "Автомобили", "slug": "auto", "icon": "car", "sort_order": 1},
        {"name": "Грузовики и спецтехника", "slug": "trucks", "icon": "truck", "sort_order": 2},
        {"name": "Мотоциклы", "slug": "motorcycles", "icon": "motorcycle", "sort_order": 3},
        {"name": "Лодки и катера", "slug": "boats", "icon": "boat", "sort_order": 4},
        {"name": "DIY проекты", "slug": "diy", "icon": "tools", "sort_order": 5},
        {"name": "Кастом автомобили", "slug": "custom", "icon": "custom", "sort_order": 6},
        {"name": "Аренда", "slug": "rent", "icon": "key", "sort_order": 7},
        {"name": "Ещё", "slug": "more", "icon": "more", "sort_order": 8},
    ]

    for cat_data in categories:
        category = Category(**cat_data)
        db.add(category)

    await db.commit()
    print(f"Seeded {len(categories)} categories")


async def seed_vehicle_types(db: AsyncSession):
    """Seed vehicle types."""
    types = [
        {"name": "Легковые", "slug": "passenger", "sort_order": 1},
        {"name": "Внедорожники", "slug": "suv", "sort_order": 2},
        {"name": "Коммерческие", "slug": "commercial", "sort_order": 3},
        {"name": "Мотоциклы", "slug": "motorcycle", "sort_order": 4},
        {"name": "Спецтехника", "slug": "special", "sort_order": 5},
    ]

    for type_data in types:
        vt = VehicleType(**type_data)
        db.add(vt)

    await db.commit()
    print(f"Seeded {len(types)} vehicle types")


async def seed_body_types(db: AsyncSession):
    """Seed body types."""
    body_types = [
        {"name": "Седан", "slug": "sedan", "sort_order": 1},
        {"name": "Хэтчбек", "slug": "hatchback", "sort_order": 2},
        {"name": "Универсал", "slug": "wagon", "sort_order": 3},
        {"name": "Кроссовер", "slug": "crossover", "sort_order": 4},
        {"name": "Внедорожник", "slug": "suv", "sort_order": 5},
        {"name": "Купе", "slug": "coupe", "sort_order": 6},
        {"name": "Кабриолет", "slug": "convertible", "sort_order": 7},
        {"name": "Минивэн", "slug": "minivan", "sort_order": 8},
        {"name": "Пикап", "slug": "pickup", "sort_order": 9},
        {"name": "Фургон", "slug": "van", "sort_order": 10},
        {"name": "Лифтбек", "slug": "liftback", "sort_order": 11},
    ]

    for bt_data in body_types:
        bt = BodyType(**bt_data)
        db.add(bt)

    await db.commit()
    print(f"Seeded {len(body_types)} body types")


async def seed_transmissions(db: AsyncSession):
    """Seed transmission types."""
    transmissions = [
        {"name": "Механическая", "slug": "manual", "short_name": "МТ", "sort_order": 1},
        {"name": "Автоматическая", "slug": "automatic", "short_name": "АТ", "sort_order": 2},
        {"name": "Роботизированная", "slug": "robot", "short_name": "РКП", "sort_order": 3},
        {"name": "Вариатор", "slug": "cvt", "short_name": "CVT", "sort_order": 4},
    ]

    for t_data in transmissions:
        t = Transmission(**t_data)
        db.add(t)

    await db.commit()
    print(f"Seeded {len(transmissions)} transmissions")


async def seed_fuel_types(db: AsyncSession):
    """Seed fuel types."""
    fuel_types = [
        {"name": "Бензин", "slug": "petrol", "sort_order": 1},
        {"name": "Дизель", "slug": "diesel", "sort_order": 2},
        {"name": "Гибрид", "slug": "hybrid", "sort_order": 3},
        {"name": "Электро", "slug": "electric", "sort_order": 4},
        {"name": "Газ", "slug": "gas", "sort_order": 5},
        {"name": "Газ-бензин", "slug": "gas-petrol", "sort_order": 6},
    ]

    for ft_data in fuel_types:
        ft = FuelType(**ft_data)
        db.add(ft)

    await db.commit()
    print(f"Seeded {len(fuel_types)} fuel types")


async def seed_drive_types(db: AsyncSession):
    """Seed drive types."""
    drive_types = [
        {"name": "Передний", "slug": "fwd", "short_name": "FWD", "sort_order": 1},
        {"name": "Задний", "slug": "rwd", "short_name": "RWD", "sort_order": 2},
        {"name": "Полный", "slug": "awd", "short_name": "AWD", "sort_order": 3},
        {"name": "Подключаемый полный", "slug": "4wd", "short_name": "4WD", "sort_order": 4},
    ]

    for dt_data in drive_types:
        dt = DriveType(**dt_data)
        db.add(dt)

    await db.commit()
    print(f"Seeded {len(drive_types)} drive types")


async def seed_colors(db: AsyncSession):
    """Seed colors."""
    colors = [
        {"name": "Белый", "slug": "white", "hex_code": "#FFFFFF", "sort_order": 1},
        {"name": "Чёрный", "slug": "black", "hex_code": "#000000", "sort_order": 2},
        {"name": "Серый", "slug": "gray", "hex_code": "#808080", "sort_order": 3},
        {"name": "Серебристый", "slug": "silver", "hex_code": "#C0C0C0", "sort_order": 4},
        {"name": "Синий", "slug": "blue", "hex_code": "#0000FF", "sort_order": 5},
        {"name": "Красный", "slug": "red", "hex_code": "#FF0000", "sort_order": 6},
        {"name": "Зелёный", "slug": "green", "hex_code": "#008000", "sort_order": 7},
        {"name": "Коричневый", "slug": "brown", "hex_code": "#8B4513", "sort_order": 8},
        {"name": "Бежевый", "slug": "beige", "hex_code": "#F5F5DC", "sort_order": 9},
        {"name": "Жёлтый", "slug": "yellow", "hex_code": "#FFFF00", "sort_order": 10},
        {"name": "Оранжевый", "slug": "orange", "hex_code": "#FFA500", "sort_order": 11},
        {"name": "Фиолетовый", "slug": "purple", "hex_code": "#800080", "sort_order": 12},
        {"name": "Золотой", "slug": "gold", "hex_code": "#FFD700", "sort_order": 13},
    ]

    for c_data in colors:
        c = Color(**c_data)
        db.add(c)

    await db.commit()
    print(f"Seeded {len(colors)} colors")


async def seed_brands(db: AsyncSession):
    """Seed popular car brands."""
    # Get passenger vehicle type
    from sqlalchemy import select
    result = await db.execute(select(VehicleType).where(VehicleType.slug == "passenger"))
    passenger_type = result.scalar_one()

    brands = [
        {"name": "Toyota", "slug": "toyota", "country": "Japan", "is_popular": True},
        {"name": "BMW", "slug": "bmw", "country": "Germany", "is_popular": True},
        {"name": "Mercedes-Benz", "slug": "mercedes", "country": "Germany", "is_popular": True},
        {"name": "Audi", "slug": "audi", "country": "Germany", "is_popular": True},
        {"name": "Volkswagen", "slug": "volkswagen", "country": "Germany", "is_popular": True},
        {"name": "Honda", "slug": "honda", "country": "Japan", "is_popular": True},
        {"name": "Nissan", "slug": "nissan", "country": "Japan", "is_popular": True},
        {"name": "Mazda", "slug": "mazda", "country": "Japan", "is_popular": True},
        {"name": "Hyundai", "slug": "hyundai", "country": "South Korea", "is_popular": True},
        {"name": "Kia", "slug": "kia", "country": "South Korea", "is_popular": True},
        {"name": "LADA", "slug": "lada", "country": "Russia", "is_popular": True},
        {"name": "Ford", "slug": "ford", "country": "USA", "is_popular": True},
        {"name": "Chevrolet", "slug": "chevrolet", "country": "USA", "is_popular": True},
        {"name": "Lexus", "slug": "lexus", "country": "Japan", "is_popular": True},
        {"name": "Subaru", "slug": "subaru", "country": "Japan", "is_popular": False},
        {"name": "Mitsubishi", "slug": "mitsubishi", "country": "Japan", "is_popular": False},
        {"name": "Skoda", "slug": "skoda", "country": "Czech Republic", "is_popular": True},
        {"name": "Renault", "slug": "renault", "country": "France", "is_popular": True},
        {"name": "Peugeot", "slug": "peugeot", "country": "France", "is_popular": False},
        {"name": "Volvo", "slug": "volvo", "country": "Sweden", "is_popular": False},
    ]

    for i, b_data in enumerate(brands):
        b_data["vehicle_type_id"] = passenger_type.id
        b_data["sort_order"] = i
        b = Brand(**b_data)
        db.add(b)

    await db.commit()
    print(f"Seeded {len(brands)} brands")


async def seed_locations(db: AsyncSession):
    """Seed locations (Russia)."""
    # Create Russia
    russia = Country(
        name="Россия",
        slug="russia",
        code="RU",
        phone_code="+7",
        flag_emoji="🇷🇺",
        sort_order=1,
    )
    db.add(russia)
    await db.flush()

    # Create regions and cities
    regions_cities = [
        {
            "name": "Москва и Московская область",
            "slug": "moscow-region",
            "cities": [
                {"name": "Москва", "slug": "moscow", "is_major": True, "latitude": 55.7558, "longitude": 37.6173, "population": 12600000},
                {"name": "Подольск", "slug": "podolsk", "is_major": False, "latitude": 55.4242, "longitude": 37.5547},
                {"name": "Мытищи", "slug": "mytishchi", "is_major": False, "latitude": 55.9116, "longitude": 37.7308},
            ],
        },
        {
            "name": "Санкт-Петербург и Ленинградская область",
            "slug": "spb-region",
            "cities": [
                {"name": "Санкт-Петербург", "slug": "spb", "is_major": True, "latitude": 59.9343, "longitude": 30.3351, "population": 5400000},
                {"name": "Гатчина", "slug": "gatchina", "is_major": False, "latitude": 59.5762, "longitude": 30.1286},
            ],
        },
        {
            "name": "Краснодарский край",
            "slug": "krasnodar-region",
            "cities": [
                {"name": "Краснодар", "slug": "krasnodar", "is_major": True, "latitude": 45.0355, "longitude": 38.9753, "population": 900000},
                {"name": "Сочи", "slug": "sochi", "is_major": True, "latitude": 43.6028, "longitude": 39.7342, "population": 400000},
                {"name": "Новороссийск", "slug": "novorossiysk", "is_major": False, "latitude": 44.7234, "longitude": 37.7687},
            ],
        },
        {
            "name": "Республика Татарстан",
            "slug": "tatarstan",
            "cities": [
                {"name": "Казань", "slug": "kazan", "is_major": True, "latitude": 55.7887, "longitude": 49.1221, "population": 1250000},
                {"name": "Набережные Челны", "slug": "naberezhnye-chelny", "is_major": False, "latitude": 55.7427, "longitude": 52.3992},
            ],
        },
        {
            "name": "Свердловская область",
            "slug": "sverdlovsk-region",
            "cities": [
                {"name": "Екатеринбург", "slug": "ekaterinburg", "is_major": True, "latitude": 56.8389, "longitude": 60.6057, "population": 1500000},
                {"name": "Нижний Тагил", "slug": "nizhny-tagil", "is_major": False, "latitude": 57.9068, "longitude": 59.9644},
            ],
        },
        {
            "name": "Новосибирская область",
            "slug": "novosibirsk-region",
            "cities": [
                {"name": "Новосибирск", "slug": "novosibirsk", "is_major": True, "latitude": 55.0084, "longitude": 82.9357, "population": 1600000},
            ],
        },
    ]

    for i, reg_data in enumerate(regions_cities):
        region = Region(
            country_id=russia.id,
            name=reg_data["name"],
            slug=reg_data["slug"],
            sort_order=i,
        )
        db.add(region)
        await db.flush()

        for j, city_data in enumerate(reg_data["cities"]):
            city = City(
                region_id=region.id,
                name=city_data["name"],
                slug=city_data["slug"],
                latitude=city_data.get("latitude"),
                longitude=city_data.get("longitude"),
                population=city_data.get("population"),
                is_major=city_data.get("is_major", False),
                sort_order=j,
            )
            db.add(city)

    await db.commit()
    print(f"Seeded locations for Russia")


async def seed_admin_user(db: AsyncSession):
    """Seed admin user."""
    admin = User(
        email="admin@avtolaif.ru",
        phone="+79001234567",
        password_hash=hash_password("admin123"),
        name="Admin",
        role=UserRole.ADMIN,
        email_verified=True,
        phone_verified=True,
    )
    db.add(admin)
    await db.commit()
    print("Seeded admin user (email: admin@avtolaif.ru, password: admin123)")


async def main():
    """Run all seed functions."""
    print("Starting database seeding...")

    async with async_session_maker() as db:
        await seed_categories(db)
        await seed_vehicle_types(db)
        await seed_body_types(db)
        await seed_transmissions(db)
        await seed_fuel_types(db)
        await seed_drive_types(db)
        await seed_colors(db)
        await seed_brands(db)
        await seed_locations(db)
        await seed_admin_user(db)

    print("Database seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())

