from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from config.stores import STORE_BRANDS

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/store", response_class=HTMLResponse)
async def store_page(request: Request, brand: str = "earth"):
    selected_brand = next((b for b in STORE_BRANDS if b["key"] == brand), STORE_BRANDS[0])
    
    # 👇 최신 방식 적용
    return templates.TemplateResponse(
        request=request, 
        name="store.html", 
        context={
            "brand": brand, 
            "brand_name": selected_brand["brand_name"],
            "stores": selected_brand["stores"]
        }
    )