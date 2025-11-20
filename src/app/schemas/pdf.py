"""
Pydantic schemas for PDF generation endpoints.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class PDFGenerationRequest(BaseModel):
    """Request model for PDF generation."""

    surface: float = Field(..., description="Apartment surface in square meters", gt=0)
    price: float = Field(..., description="Apartment price", gt=0)
    currency: str = Field("EUR", description="Price currency (EUR, USD, MDL, RON)")
    parking: Optional[float] = Field(None, description="Parking price")
    parking_currency: Optional[str] = Field(None, description="Parking currency")

    class Config:
        json_schema_extra = {
            "example": {
                "surface": 75.5,
                "price": 95000,
                "currency": "EUR",
                "parking": 15000,
                "parking_currency": "EUR"
            }
        }


class SaleSummaryRequest(BaseModel):
    """Request model for sale summary PDF generation."""

    sale_price_eur: float = Field(..., description="Sale price in EUR", gt=0)
    seller_name: Optional[str] = Field(None, description="Seller name")
    buyer_name: Optional[str] = Field(None, description="Buyer name")
    property_address: Optional[str] = Field(None, description="Property address")
    surface: Optional[float] = Field(None, description="Property surface in sqm", gt=0)

    class Config:
        json_schema_extra = {
            "example": {
                "sale_price_eur": 95000,
                "seller_name": "Ion Popescu",
                "buyer_name": "Maria Ionescu",
                "property_address": "str. Stefan cel Mare 123, Chisinau",
                "surface": 75.5
            }
        }


class PDFResponse(BaseModel):
    """Response model for PDF generation (file download)."""

    filename: str = Field(..., description="Generated PDF filename")
    content_type: str = Field("application/pdf", description="MIME type")
    size_bytes: Optional[int] = Field(None, description="File size in bytes")

