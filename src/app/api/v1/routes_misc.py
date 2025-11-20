from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=['misc'])

@router.get('/day')
async def day():
    now = datetime.utcnow()
    return {"day": now.strftime('%d.%m.%Y'), "full_date": now.isoformat()}

@router.get('/health')
async def health():
    return {"status": "ok"}

