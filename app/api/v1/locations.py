"""
Location endpoints.
Geolocation, countries, regions, cities.
"""

from typing import List, Optional
from math import radians, cos, sin, asin, sqrt

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.location import Country, Region, City
from app.models.user import User
from app.schemas.location import (
    CountryResponse,
    CountryCreate,
    RegionResponse,
    RegionCreate,
    CityResponse,
    CityCreate,
    CityWithRegion,
    LocationSuggestion,
    RegionWithCities,
    CountryWithRegions,
)
from app.schemas.common import MessageOut
from app.api.deps import require_admin


router = APIRouter()


def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees).
    """
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r


# ============ Countries ============

@router.get("/countries", response_model=List[CountryResponse])
async def list_countries(
    db: AsyncSession = Depends(get_db),
):
    """Get all countries."""
    result = await db.execute(
        select(Country).where(Country.is_active == True).order_by(Country.sort_order, Country.name)
    )
    countries = result.scalars().all()
    return [CountryResponse.model_validate(c) for c in countries]


@router.get("/countries/{country_id}", response_model=CountryWithRegions)
async def get_country_with_regions(
    country_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get country with all its regions."""
    result = await db.execute(
        select(Country).options(
            selectinload(Country.regions)
        ).where(Country.id == country_id)
    )
    country = result.scalar_one_or_none()
    if not country:
        raise NotFoundError("Country not found", "country", country_id)

    regions = [
        RegionWithCities(
            id=r.id,
            country_id=r.country_id,
            name=r.name,
            slug=r.slug,
            code=r.code,
            cities=[],
        )
        for r in sorted(country.regions, key=lambda x: (x.sort_order, x.name))
        if r.is_active
    ]

    return CountryWithRegions(
        id=country.id,
        name=country.name,
        slug=country.slug,
        code=country.code,
        phone_code=country.phone_code,
        flag_emoji=country.flag_emoji,
        regions=regions,
    )


@router.post("/countries", response_model=CountryResponse, status_code=status.HTTP_201_CREATED)
async def create_country(
    data: CountryCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Create country (admin only)."""
    country = Country(**data.model_dump())
    db.add(country)
    await db.commit()
    await db.refresh(country)
    return CountryResponse.model_validate(country)


# ============ Regions ============

@router.get("/regions", response_model=List[RegionResponse])
async def list_regions(
    country_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get regions for a country."""
    result = await db.execute(
        select(Region).where(
            Region.country_id == country_id,
            Region.is_active == True,
        ).order_by(Region.sort_order, Region.name)
    )
    regions = result.scalars().all()
    return [RegionResponse.model_validate(r) for r in regions]


@router.get("/regions/{region_id}", response_model=RegionWithCities)
async def get_region_with_cities(
    region_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get region with all its cities."""
    result = await db.execute(
        select(Region).options(
            selectinload(Region.cities)
        ).where(Region.id == region_id)
    )
    region = result.scalar_one_or_none()
    if not region:
        raise NotFoundError("Region not found", "region", region_id)

    cities = [
        CityResponse.model_validate(c)
        for c in sorted(region.cities, key=lambda x: (-x.is_major, x.sort_order, x.name))
        if c.is_active
    ]

    return RegionWithCities(
        id=region.id,
        country_id=region.country_id,
        name=region.name,
        slug=region.slug,
        code=region.code,
        cities=cities,
    )


@router.post("/regions", response_model=RegionResponse, status_code=status.HTTP_201_CREATED)
async def create_region(
    data: RegionCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Create region (admin only)."""
    region = Region(**data.model_dump())
    db.add(region)
    await db.commit()
    await db.refresh(region)
    return RegionResponse.model_validate(region)


# ============ Cities ============

@router.get("/cities", response_model=List[CityResponse])
async def list_cities(
    region_id: int,
    major_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Get cities for a region."""
    query = select(City).where(
        City.region_id == region_id,
        City.is_active == True,
    )

    if major_only:
        query = query.where(City.is_major == True)

    query = query.order_by(City.is_major.desc(), City.sort_order, City.name)

    result = await db.execute(query)
    cities = result.scalars().all()
    return [CityResponse.model_validate(c) for c in cities]


@router.get("/cities/{city_id}", response_model=CityWithRegion)
async def get_city(
    city_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get city with region info."""
    result = await db.execute(
        select(City).options(
            selectinload(City.region).selectinload(Region.country)
        ).where(City.id == city_id)
    )
    city = result.scalar_one_or_none()
    if not city:
        raise NotFoundError("City not found", "city", city_id)

    return CityWithRegion(
        id=city.id,
        region_id=city.region_id,
        name=city.name,
        slug=city.slug,
        latitude=city.latitude,
        longitude=city.longitude,
        is_major=city.is_major,
        region_name=city.region.name,
        country_name=city.region.country.name,
    )


@router.post("/cities", response_model=CityResponse, status_code=status.HTTP_201_CREATED)
async def create_city(
    data: CityCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Create city (admin only)."""
    city = City(**data.model_dump())
    db.add(city)
    await db.commit()
    await db.refresh(city)
    return CityResponse.model_validate(city)


# ============ Search & Suggestions ============

@router.get("/search", response_model=List[LocationSuggestion])
async def search_locations(
    q: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Search cities and regions by name.
    Used for autocomplete.
    """
    search_term = f"%{q}%"

    # Search cities
    cities_result = await db.execute(
        select(City).options(
            selectinload(City.region)
        ).where(
            City.name.ilike(search_term),
            City.is_active == True,
        ).order_by(City.is_major.desc(), City.population.desc().nullsfirst()).limit(limit)
    )
    cities = cities_result.scalars().all()

    suggestions = []
    for city in cities:
        suggestions.append(LocationSuggestion(
            id=city.id,
            name=city.name,
            full_name=f"{city.name}, {city.region.name}",
            type="city",
        ))

    return suggestions


@router.get("/nearby", response_model=List[CityWithRegion])
async def get_nearby_cities(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: int = Query(50, ge=1, le=500),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Get cities within radius of coordinates.
    Uses Haversine formula for distance calculation.
    """
    # Get all cities with coordinates
    result = await db.execute(
        select(City).options(
            selectinload(City.region).selectinload(Region.country)
        ).where(
            City.latitude.isnot(None),
            City.longitude.isnot(None),
            City.is_active == True,
        )
    )
    all_cities = result.scalars().all()

    # Calculate distances and filter
    nearby = []
    for city in all_cities:
        distance = haversine(longitude, latitude, city.longitude, city.latitude)
        if distance <= radius_km:
            nearby.append((city, distance))

    # Sort by distance and limit
    nearby.sort(key=lambda x: x[1])
    nearby = nearby[:limit]

    return [
        CityWithRegion(
            id=city.id,
            region_id=city.region_id,
            name=city.name,
            slug=city.slug,
            latitude=city.latitude,
            longitude=city.longitude,
            is_major=city.is_major,
            region_name=city.region.name,
            country_name=city.region.country.name,
        )
        for city, _ in nearby
    ]


@router.get("/major-cities", response_model=List[CityWithRegion])
async def get_major_cities(
    country_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Get major cities, optionally filtered by country.
    """
    query = select(City).options(
        selectinload(City.region).selectinload(Region.country)
    ).where(
        City.is_major == True,
        City.is_active == True,
    )

    if country_id:
        query = query.join(Region).where(Region.country_id == country_id)

    query = query.order_by(City.population.desc().nullsfirst()).limit(limit)

    result = await db.execute(query)
    cities = result.scalars().all()

    return [
        CityWithRegion(
            id=city.id,
            region_id=city.region_id,
            name=city.name,
            slug=city.slug,
            latitude=city.latitude,
            longitude=city.longitude,
            is_major=city.is_major,
            region_name=city.region.name,
            country_name=city.region.country.name,
        )
        for city in cities
    ]

