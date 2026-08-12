import sqlite3
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from config.stores import STORE_BRANDS
from config.themes import get_theme_image  # 💡 테마 이미지 함수 임포트
from database import DB_FILE, get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
    username = request.cookies.get("user")
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. 사용자 이름 조회
    cursor.execute("SELECT name FROM users WHERE username = ?", (username,))
    user_row = cursor.fetchone()
    user_name = user_row["name"] if user_row else username

    # 2. 대기 중인 예약 타이머 목록 조회
    if username == "admin":
        cursor.execute("SELECT * FROM reservations WHERE status = '대기중' ORDER BY id DESC")
    else:
        cursor.execute("SELECT * FROM reservations WHERE username = ? AND status = '대기중' ORDER BY id DESC", (username,))
    
    db_reservations = cursor.fetchall()
    conn.close()

    # 3. 💡 DB의 brand, store_code, theme을 이용해 config/themes.py로 이미지 URL 생성
    reservations = []
    for r in db_reservations:
        r_dict = dict(r)
        
        # store_code를 이용해 실제 지점 이름(폴더명) 찾기
        store_name = "default"
        brand_info = next((b for b in STORE_BRANDS if b["key"] == r_dict["brand"]), None)
        if brand_info and "stores" in brand_info:
            store_info = brand_info["stores"].get(r_dict["store_code"])
            if store_info:
                store_name = store_info.get("name", "default")

        # config/themes.py의 함수 호출하여 깃허브 이미지 주소 획득
        r_dict["img"] = get_theme_image(store_name, r_dict["theme"])
        
        reservations.append(r_dict)

    return templates.TemplateResponse(
        request=request, 
        name="main.html", 
        context={
            "brands": STORE_BRANDS,
            "user_name": user_name,
            "reservations": reservations
        }
    )