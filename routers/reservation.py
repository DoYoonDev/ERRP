import sqlite3
from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from utils.scraper import get_realtime_data
from config.stores import STORE_BRANDS
from database import DB_FILE

router = APIRouter()
templates = Jinja2Templates(directory="templates")
scheduler = AsyncIOScheduler()
scheduler.start()

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def execute_reservation_task(res_id, name, phone, brand, store_code, theme, date, time):
    print(f"[{datetime.now()}] 🎯 [자동화 발사] 브랜드:{brand} / 매장:{store_code} / 테마:{theme} / 날짜:{date} / 시간:{time}")
    
    # DB 상태 완료로 변경
    conn = get_db()
    conn.execute("UPDATE reservations SET status = '완료' WHERE id = ?", (res_id,))
    conn.commit()
    conn.close()

@router.get("/reservation", response_class=HTMLResponse)
async def reservation_page(request: Request, brand: str = "earth", store_code: str = "1"):
    brand_info = next((b for b in STORE_BRANDS if b["key"] == brand), STORE_BRANDS[0])
    store_info = brand_info["stores"].get(store_code, {})
    store_name = store_info.get("name", "지점")
    
    target_date = calculate_target_date(store_info)

    themes = get_realtime_data(brand, store_code, target_date)
    if not themes:
        one_week_ago = (datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")
        themes = get_realtime_data(brand, store_code, one_week_ago)
        for t in themes:
            for slot in t["slots"]:
                slot["status"] = "예약가능"

    # DB에서 현재 활성화된(대기중인) 타이머 목록 조회
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT brand, store_code, theme, date, time FROM reservations WHERE status = '대기중'")
    active_locks = {f"{row['brand']}_{row['store_code']}_{row['theme']}_{row['date']}_{row['time']}" for row in cursor.fetchall()}
    conn.close()

    for t in themes:
        for slot in t["slots"]:
            lock_key = f"{brand}_{store_code}_{t['title']}_{target_date}_{slot['time']}"
            slot["is_locked"] = lock_key in active_locks

    return templates.TemplateResponse(
        request=request, 
        name="reservation.html", 
        context={
            "brand": brand, 
            "store_code": store_code, 
            "store_name": store_name, 
            "date": target_date, 
            "themes": themes
        }
    )

def calculate_target_date(store_info):
    now = datetime.now()
    open_days = store_info.get("open_days", 7)
    open_hour = store_info.get("open_hour", 0)
    today_open_time = now.replace(hour=open_hour, minute=0, second=0, microsecond=0)
    if now >= today_open_time:
        target = now + timedelta(days=open_days)
    else:
        target = now + timedelta(days=open_days - 1)
    return target.strftime("%Y-%m-%d")

from config.themes import get_theme_image # 💡 임포트 추가

@router.post("/reserve_automation")
async def schedule_automation(
    request: Request,
    brand: str = Form(...), 
    store_code: str = Form(...), 
    theme: str = Form(...),
    date: str = Form(...), 
    time: str = Form(...), 
    run_date: str = Form(...), 
    run_time: str = Form(...),
    img: str = Form(default="") # 💡 프론트엔드가 보내준 깃허브 이미지 주소 받기
):
    username = request.cookies.get("user", "admin")
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name, phone FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    name = user["name"] if user else "홍길동"
    phone = user["phone"] if user else "01012345678"

    # 중복 체크
    cursor.execute("""
        SELECT id FROM reservations 
        WHERE brand = ? AND store_code = ? AND theme = ? AND date = ? AND time = ? AND status = '대기중'
    """, (brand, store_code, theme, date, time))
    
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="이미 다른 사용자가 해당 시간대에 타이머를 선점했습니다!")

    # 💡 스크래퍼가 만들어 둔 깃허브 이미지 주소를 DB에 안전하게 저장
    cursor.execute("""
        INSERT INTO reservations (username, brand, store_code, theme, date, time, run_date, run_time, img, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '대기중')
    """, (username, brand, store_code, theme, date, time, run_date, run_time, img))
    
    res_id = cursor.lastrowid
    conn.commit()
    conn.close()

    target_time = datetime.strptime(f"{run_date} {run_time}", "%Y-%m-%d %H:%M")
    scheduler.add_job(execute_reservation_task, 'date', run_date=target_time, 
                      args=[res_id, name, phone, brand, store_code, theme, date, time], id=str(res_id))
    
    return {"status": "success", "message": f"성공! [{target_time}] 정각에 예약을 자동 발사하도록 타이머가 세팅되었습니다."}

# 💡 내 예약 목록 및 취소 라우터
@router.get("/my_reservations", response_class=HTMLResponse)
async def my_reservations(request: Request):
    username = request.cookies.get("user", "guest")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 💡 관리자(admin) 계정인 경우: 모든 사용자의 예약 목록을 전체 조회
    if username == "admin":
        cursor.execute("SELECT * FROM reservations ORDER BY id DESC")
    else:
        # 일반 사용자 계정인 경우: 본인 계정의 예약 목록만 조회
        cursor.execute("SELECT * FROM reservations WHERE username = ? ORDER BY id DESC", (username,))
        
    reservations = cursor.fetchall()
    conn.close()
    
    return templates.TemplateResponse(
        request=request, 
        name="my_reservations.html", 
        context={
            "reservations": reservations,
            "is_admin": (username == "admin")  # 관리자 여부를 템플릿에 전달
        }
    )

@router.post("/cancel_reservation/{res_id}")
async def cancel_reservation(res_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE reservations SET status = '취소됨' WHERE id = ?", (res_id,))
    conn.commit()
    conn.close()
    
    # 스케줄러에서 작업 제거 시도
    try:
        scheduler.remove_job(str(res_id))
    except Exception:
        pass
        
    return RedirectResponse(url="/my_reservations", status_code=303)