from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import requests
import urllib3
import urllib.parse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = FastAPI()
templates = Jinja2Templates(directory="templates")
scheduler = AsyncIOScheduler()

# [추가됨] 서버가 켜질 때 스케줄러도 함께 작동 시작
@app.on_event("startup")
async def start_scheduler():
    scheduler.start()
    print("타이머(스케줄러)가 시작되었습니다.")

# 1. 메인 화면 띄우기
@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


# 🌟 [분리된 핵심 로직] 실제 예약을 수행하는 함수
def execute_reservation_task(name, phone, people, branch, theme, date, time):
    print(f"[{datetime.now()}] 예약 매크로 실행 시작!")
    
    session = requests.Session()
    base_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    calendar_url = f"https://www.xn--2e0b040a4xj.com/reservation?branch={branch}&theme={theme}&date={date}"
    res_get = session.get(calendar_url, headers=base_headers, verify=False)
    
    raw_token = session.cookies.get('XSRF-TOKEN')
    csrf_token = urllib.parse.unquote(raw_token) if raw_token else ""
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "X-XSRF-TOKEN": csrf_token,
        "X-Requested-With": "XMLHttpRequest",
        "Referer": calendar_url
    }
    
    payload = {
        "name": name, "phone": phone, "people": people,
        "payment_method": "21", "policy": "on",
        "branch": branch, "theme": theme,
        "date": date, "time": time
    }
    
    target_url = "https://www.xn--2e0b040a4xj.com/reservation/payment"
    res = session.post(target_url, data=payload, headers=headers, verify=False)
    
    print(f"[{datetime.now()}] 예약 결과 응답 코드: {res.status_code}")

# 2. [수정됨] 버튼을 누르면 스케줄러에 작업을 등록하는 API
@app.post("/reserve")
async def schedule_reservation(
    name: str = Form(...),
    phone: str = Form(...),
    people: str = Form("2"),
    branch: str = Form("2"),
    theme: str = Form("18"),
    date: str = Form(...),
    time: str = Form(...),
    # 타이머 실행을 위한 타겟 시간 추가 (예: "2026-08-15 12:00:00")
    run_date: str = Form(...),  # 분리된 실행 날짜
    run_time: str = Form(...)   # 분리된 실행 시간
):
    # 문자열을 datetime 객체로 변환
    # 날짜와 시간을 하나의 문자열로 합치기 (예: "2026-08-12 11:10")
    run_datetime_str = f"{run_date} {run_time}"
    
    # 합친 문자열을 파이썬 시간 객체로 변환 ("%Y-%m-%d %H:%M" 포맷 사용)
    target_time = datetime.strptime(run_datetime_str, "%Y-%m-%d %H:%M")
    
    # 스케줄러에 작업 등록 (target_time이 되면 execute_reservation_task를 실행)
    scheduler.add_job(
        execute_reservation_task,
        'date',
        run_date=target_time,
        args=[name, phone, people, branch, theme, date, time]
    )
    
    return {
        "message": f"[{target_time}]에 예약이 자동으로 실행되도록 타이머가 설정되었습니다!"
    }