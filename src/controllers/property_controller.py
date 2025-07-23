# src/controllers/property_controller.py

from typing import List
from fastapi import APIRouter, Depends, Query
from src.use_cases.property_use_cases import PropertyUseCases
from src.domain.models.property_models import Property, PropertyFilter, PropertyType, CondoScheme
from src.app.startup import get_property_use_cases

router = APIRouter(prefix="/properties", tags=["Properties"])

@router.get("/", response_model=List[Property])
async def find_properties_endpoint(
    property_type: PropertyType | None = Query(None),
    min_bedrooms: int | None = Query(None, gt=0),
    max_bedrooms: int | None = Query(None, gt=0),
    min_price: float | None = Query(None, gt=0),
    max_price: float | None = Query(None, gt=0),
    condo_scheme: CondoScheme | None = Query(None),
    region: str | None = Query(None),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    """
    Finds and filters approved properties.
    This endpoint is designed for the future web app.
    
    Example: `/properties?property_type=Condominium&min_price=5000000&max_price=10000000`
    """
    # No try/except needed! The FastAPI exception handler will catch errors.
    filters = PropertyFilter(
        property_type=property_type,
        min_bedrooms=min_bedrooms,
        max_bedrooms=max_bedrooms,
        min_price=min_price,
        max_price=max_price,
        condominium_scheme=condo_scheme,
        location_region=region
    )
    properties = await prop_cases.find_properties(filters)
    return properties


@router.get("/{property_id}", response_model=Property)
async def get_property_by_id_endpoint(
    property_id: str,
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    """
    Gets the details for a single property by its ID.
    Will return a 404 error if the property is not found.
    """
    # No try/except needed! The handler will catch PropertyNotFoundError.
    prop = await prop_cases.get_property_details(property_id)
    return prop