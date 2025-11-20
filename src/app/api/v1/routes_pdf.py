from fastapi import APIRouter, Response
from pydantic import BaseModel
from app.services.pdf.pdf_service import generate_report_pdf, generate_sale_summary_pdf

router = APIRouter(prefix='/pdf', tags=['pdf'])

class ReportPayload(BaseModel):
    config: dict

class SaleSummaryPayload(BaseModel):
    config: dict
    amount: float
    currency: str = 'EUR'

@router.post('')
def create_report(payload: ReportPayload):
    try:
        pdf = generate_report_pdf(payload.config)
    except ValueError as e:
        return Response(content=str(e).encode(), status_code=400)
    return Response(content=pdf, media_type='application/pdf', headers={'Content-Disposition':'attachment; filename="apartment-report.pdf"'})

@router.post('/sale-summary')
def create_sale_summary(payload: SaleSummaryPayload):
    try:
        pdf = generate_sale_summary_pdf(payload.config, payload.amount, payload.currency.upper())
    except ValueError as e:
        return Response(content=str(e).encode(), status_code=400)
    return Response(content=pdf, media_type='application/pdf', headers={'Content-Disposition':'attachment; filename="sale-summary.pdf"'})

