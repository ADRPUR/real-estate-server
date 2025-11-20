from fastapi import APIRouter, HTTPException
import app.main as main_module

router = APIRouter(tags=['rates'])

@router.get('/rates')
async def get_rates():
    try:
        return main_module.fetch_all_rates(use_cache=False)
    except Exception as ex:
        raise HTTPException(status_code=502, detail=str(ex))
