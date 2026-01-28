"""
Vehicle reference endpoints.
Provides cascading selection for vehicle types, brands, models, generations, modifications.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import NotFoundError, ConflictError
from app.models.vehicle import (
    VehicleType,
    Brand,
    Model,
    Generation,
    Modification,
    BodyType,
    Transmission,
    FuelType,
    DriveType,
    Color,
)
from app.models.user import User
from app.schemas.vehicle import (
    VehicleTypeResponse,
    VehicleTypeCreate,
    BrandResponse,
    BrandCreate,
    ModelResponse,
    ModelCreate,
    GenerationResponse,
    GenerationCreate,
    ModificationResponse,
    ModificationCreate,
    BodyTypeResponse,
    TransmissionResponse,
    FuelTypeResponse,
    DriveTypeResponse,
    ColorResponse,
    VehicleFullHierarchy,
)
from app.schemas.common import MessageOut
from app.api.deps import require_admin


router = APIRouter()


# ============ Vehicle Types ============

@router.get("/types", response_model=List[VehicleTypeResponse])
async def list_vehicle_types(
    db: AsyncSession = Depends(get_db),
):
    """
    Get all vehicle types.
    """
    result = await db.execute(
        select(VehicleType).where(
            VehicleType.is_active == True
        ).order_by(VehicleType.sort_order, VehicleType.name)
    )
    types = result.scalars().all()
    return [VehicleTypeResponse.model_validate(t) for t in types]


@router.post("/types", response_model=VehicleTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle_type(
    data: VehicleTypeCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Create vehicle type (admin only)."""
    vehicle_type = VehicleType(**data.model_dump())
    db.add(vehicle_type)
    await db.commit()
    await db.refresh(vehicle_type)
    return VehicleTypeResponse.model_validate(vehicle_type)


# ============ Brands ============

@router.get("/brands", response_model=List[BrandResponse])
async def list_brands(
    vehicle_type_id: Optional[int] = None,
    popular_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """
    Get brands, optionally filtered by vehicle type.
    """
    query = select(Brand).where(Brand.is_active == True)

    if vehicle_type_id:
        query = query.where(Brand.vehicle_type_id == vehicle_type_id)

    if popular_only:
        query = query.where(Brand.is_popular == True)

    query = query.order_by(Brand.sort_order, Brand.name)

    result = await db.execute(query)
    brands = result.scalars().all()
    return [BrandResponse.model_validate(b) for b in brands]


@router.get("/brands/{brand_id}", response_model=BrandResponse)
async def get_brand(
    brand_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get brand by ID."""
    result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = result.scalar_one_or_none()
    if not brand:
        raise NotFoundError("Brand not found", "brand", brand_id)
    return BrandResponse.model_validate(brand)


@router.post("/brands", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
async def create_brand(
    data: BrandCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Create brand (admin only)."""
    brand = Brand(**data.model_dump())
    db.add(brand)
    await db.commit()
    await db.refresh(brand)
    return BrandResponse.model_validate(brand)


# ============ Models ============

@router.get("/models", response_model=List[ModelResponse])
async def list_models(
    brand_id: int,
    popular_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """
    Get models for a specific brand.
    """
    query = select(Model).where(
        Model.brand_id == brand_id,
        Model.is_active == True,
    )

    if popular_only:
        query = query.where(Model.is_popular == True)

    query = query.order_by(Model.sort_order, Model.name)

    result = await db.execute(query)
    models = result.scalars().all()
    return [ModelResponse.model_validate(m) for m in models]


@router.get("/models/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get model by ID."""
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise NotFoundError("Model not found", "model", model_id)
    return ModelResponse.model_validate(model)


@router.post("/models", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    data: ModelCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Create model (admin only)."""
    model = Model(**data.model_dump())
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return ModelResponse.model_validate(model)


# ============ Generations ============

@router.get("/generations", response_model=List[GenerationResponse])
async def list_generations(
    model_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get generations for a specific model.
    """
    result = await db.execute(
        select(Generation).where(
            Generation.model_id == model_id,
            Generation.is_active == True,
        ).order_by(Generation.year_start.desc(), Generation.sort_order)
    )
    generations = result.scalars().all()
    return [GenerationResponse.model_validate(g) for g in generations]


@router.get("/generations/{generation_id}", response_model=GenerationResponse)
async def get_generation(
    generation_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get generation by ID."""
    result = await db.execute(select(Generation).where(Generation.id == generation_id))
    generation = result.scalar_one_or_none()
    if not generation:
        raise NotFoundError("Generation not found", "generation", generation_id)
    return GenerationResponse.model_validate(generation)


@router.post("/generations", response_model=GenerationResponse, status_code=status.HTTP_201_CREATED)
async def create_generation(
    data: GenerationCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Create generation (admin only)."""
    generation = Generation(**data.model_dump())
    db.add(generation)
    await db.commit()
    await db.refresh(generation)
    return GenerationResponse.model_validate(generation)


# ============ Modifications ============

@router.get("/modifications", response_model=List[ModificationResponse])
async def list_modifications(
    generation_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get modifications for a specific generation.
    Includes full technical specifications.
    """
    result = await db.execute(
        select(Modification).options(
            selectinload(Modification.fuel_type),
            selectinload(Modification.transmission),
            selectinload(Modification.drive_type),
            selectinload(Modification.body_type),
        ).where(
            Modification.generation_id == generation_id,
            Modification.is_active == True,
        ).order_by(Modification.sort_order, Modification.name)
    )
    modifications = result.scalars().all()

    result_list = []
    for mod in modifications:
        mod_dict = ModificationResponse.model_validate(mod).model_dump()
        if mod.fuel_type:
            mod_dict["fuel_type_name"] = mod.fuel_type.name
        if mod.transmission:
            mod_dict["transmission_name"] = mod.transmission.name
        if mod.drive_type:
            mod_dict["drive_type_name"] = mod.drive_type.name
        if mod.body_type:
            mod_dict["body_type_name"] = mod.body_type.name
        result_list.append(ModificationResponse(**mod_dict))

    return result_list


@router.get("/modifications/{modification_id}", response_model=ModificationResponse)
async def get_modification(
    modification_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get modification by ID with full specs."""
    result = await db.execute(
        select(Modification).options(
            selectinload(Modification.fuel_type),
            selectinload(Modification.transmission),
            selectinload(Modification.drive_type),
            selectinload(Modification.body_type),
        ).where(Modification.id == modification_id)
    )
    modification = result.scalar_one_or_none()
    if not modification:
        raise NotFoundError("Modification not found", "modification", modification_id)

    mod_dict = ModificationResponse.model_validate(modification).model_dump()
    if modification.fuel_type:
        mod_dict["fuel_type_name"] = modification.fuel_type.name
    if modification.transmission:
        mod_dict["transmission_name"] = modification.transmission.name
    if modification.drive_type:
        mod_dict["drive_type_name"] = modification.drive_type.name
    if modification.body_type:
        mod_dict["body_type_name"] = modification.body_type.name

    return ModificationResponse(**mod_dict)


@router.post("/modifications", response_model=ModificationResponse, status_code=status.HTTP_201_CREATED)
async def create_modification(
    data: ModificationCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Create modification (admin only)."""
    modification = Modification(**data.model_dump())
    db.add(modification)
    await db.commit()
    await db.refresh(modification)
    return ModificationResponse.model_validate(modification)


# ============ Reference Data ============

@router.get("/body-types", response_model=List[BodyTypeResponse])
async def list_body_types(
    db: AsyncSession = Depends(get_db),
):
    """Get all body types."""
    result = await db.execute(
        select(BodyType).where(BodyType.is_active == True).order_by(BodyType.sort_order, BodyType.name)
    )
    body_types = result.scalars().all()
    return [BodyTypeResponse.model_validate(bt) for bt in body_types]


@router.get("/transmissions", response_model=List[TransmissionResponse])
async def list_transmissions(
    db: AsyncSession = Depends(get_db),
):
    """Get all transmission types."""
    result = await db.execute(
        select(Transmission).where(Transmission.is_active == True).order_by(Transmission.sort_order)
    )
    transmissions = result.scalars().all()
    return [TransmissionResponse.model_validate(t) for t in transmissions]


@router.get("/fuel-types", response_model=List[FuelTypeResponse])
async def list_fuel_types(
    db: AsyncSession = Depends(get_db),
):
    """Get all fuel types."""
    result = await db.execute(
        select(FuelType).where(FuelType.is_active == True).order_by(FuelType.sort_order)
    )
    fuel_types = result.scalars().all()
    return [FuelTypeResponse.model_validate(ft) for ft in fuel_types]


@router.get("/drive-types", response_model=List[DriveTypeResponse])
async def list_drive_types(
    db: AsyncSession = Depends(get_db),
):
    """Get all drive types."""
    result = await db.execute(
        select(DriveType).where(DriveType.is_active == True).order_by(DriveType.sort_order)
    )
    drive_types = result.scalars().all()
    return [DriveTypeResponse.model_validate(dt) for dt in drive_types]


@router.get("/colors", response_model=List[ColorResponse])
async def list_colors(
    db: AsyncSession = Depends(get_db),
):
    """Get all colors."""
    result = await db.execute(
        select(Color).where(Color.is_active == True).order_by(Color.sort_order, Color.name)
    )
    colors = result.scalars().all()
    return [ColorResponse.model_validate(c) for c in colors]


@router.get("/references", response_model=VehicleFullHierarchy)
async def get_all_references(
    db: AsyncSession = Depends(get_db),
):
    """
    Get all reference data for forms.
    Useful for caching on client side.
    """
    # Fetch all reference data in parallel
    vehicle_types_result = await db.execute(
        select(VehicleType).where(VehicleType.is_active == True).order_by(VehicleType.sort_order)
    )
    brands_result = await db.execute(
        select(Brand).where(Brand.is_active == True, Brand.is_popular == True).order_by(Brand.sort_order)
    )
    body_types_result = await db.execute(
        select(BodyType).where(BodyType.is_active == True).order_by(BodyType.sort_order)
    )
    transmissions_result = await db.execute(
        select(Transmission).where(Transmission.is_active == True).order_by(Transmission.sort_order)
    )
    fuel_types_result = await db.execute(
        select(FuelType).where(FuelType.is_active == True).order_by(FuelType.sort_order)
    )
    drive_types_result = await db.execute(
        select(DriveType).where(DriveType.is_active == True).order_by(DriveType.sort_order)
    )
    colors_result = await db.execute(
        select(Color).where(Color.is_active == True).order_by(Color.sort_order)
    )

    return VehicleFullHierarchy(
        vehicle_types=[VehicleTypeResponse.model_validate(vt) for vt in vehicle_types_result.scalars().all()],
        brands=[BrandResponse.model_validate(b) for b in brands_result.scalars().all()],
        body_types=[BodyTypeResponse.model_validate(bt) for bt in body_types_result.scalars().all()],
        transmissions=[TransmissionResponse.model_validate(t) for t in transmissions_result.scalars().all()],
        fuel_types=[FuelTypeResponse.model_validate(ft) for ft in fuel_types_result.scalars().all()],
        drive_types=[DriveTypeResponse.model_validate(dt) for dt in drive_types_result.scalars().all()],
        colors=[ColorResponse.model_validate(c) for c in colors_result.scalars().all()],
    )

