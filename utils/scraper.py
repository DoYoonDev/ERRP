import os
import base64
import requests
from requests.utils import quote
from bs4 import BeautifulSoup
import urllib3
from dotenv import load_dotenv
from config.stores import STORE_BRANDS

# .env 파일 로드
load_dotenv()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
REPO_OWNER = os.getenv("REPO_OWNER", "DoYoonDev")
REPO_NAME = os.getenv("REPO_NAME", "ERRP")
BRANCH = os.getenv("BRANCH", "main")

# 메모리 캐시: 중복 API 호출 방지 및 속도 향상
IMAGE_CACHE = {}

def upload_image_to_github(image_url, brand_key, store_name, theme_title):
    if not image_url:
        return ""
    
    safe_store_name = "".join(c for c in store_name if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
    safe_theme_title = "".join(c for c in theme_title if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
    cache_key = f"{safe_store_name}_{safe_theme_title}"
    
    # 1. 이미 캐시에 있다면 API 확인 없이 즉시 경로 반환
    if cache_key in IMAGE_CACHE:
        return IMAGE_CACHE[cache_key]
    
    file_path_in_repo = f"static/images/{safe_store_name}/{safe_theme_title}.jpg"
    encoded_file_path = quote(file_path_in_repo)
    
    github_raw_url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{encoded_file_path}"
    
    try:
        token_str = str(GITHUB_TOKEN).encode("ascii", "ignore").decode("ascii")
        headers = {
            "Authorization": f"Bearer {token_str}",
            "Accept": "application/vnd.github+json"
        }
        
        api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{encoded_file_path}"
        
        # 2. 파일이 GitHub에 이미 있는지 체크 (타임아웃 10초로 상향)
        check_res = requests.get(api_url, headers=headers, timeout=10)
        if check_res.status_code == 200:
            IMAGE_CACHE[cache_key] = github_raw_url
            return github_raw_url

        # 3. 파일이 없다면 원본 이미지 다운로드 후 업로드
        if image_url.startswith("//"):
            image_url = "https:" + image_url
            
        img_res = requests.get(image_url, verify=False, timeout=10)
        if img_res.status_code != 200:
            return image_url
            
        encoded_content = base64.b64encode(img_res.content).decode("utf-8")
        
        data = {
            "message": f"Upload theme image: {safe_theme_title}", 
            "content": encoded_content,
            "branch": BRANCH
        }
        
        put_res = requests.put(api_url, headers=headers, json=data, timeout=15)
        if put_res.status_code in [201, 200]:
            print(f"[{safe_store_name} / {theme_title}] GitHub 업로드 성공!")
            IMAGE_CACHE[cache_key] = github_raw_url
            return github_raw_url

    except requests.exceptions.Timeout:
        print(f"이미지 처리 중 타임아웃 발생 [{theme_title}]: 네트워크가 지연되었습니다.")
    except Exception as e:
        print(f"이미지 처리 중 오류 발생 [{theme_title}]: {e}")
    
    return image_url

def get_realtime_data(brand_key, store_code, date):
    brand_info = next((b for b in STORE_BRANDS if b["key"] == brand_key), None)
    if not brand_info:
        return []

    store_info = brand_info["stores"].get(store_code, {})
    store_name = store_info.get("name", f"store_{store_code}")

    base_url = brand_info["base_url"]
    url = f"{base_url}/reservation?branch={store_code}&date={date}"
    
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        themes_data = []
        items = soup.select(".res-item")
        for item in items:
            title_el = item.select_one(".eve-mopa h2")
            img_el = item.select_one("figure img")
            
            title = title_el.text.strip() if title_el else "테마 이름"
            raw_img_url = img_el["src"] if img_el and "src" in img_el.attrs else ""
            
            # GitHub 자동 업로드 및 캐시 확인
            github_img_path = upload_image_to_github(raw_img_url, brand_key, store_name, title)
            
            slots = []
            for btn in item.select(".res-times-btn button"):
                time_span = btn.select_one("span")
                label = btn.select_one("label")
                
                time_val = time_span.text.strip() if time_span else ""
                status = label.text.strip() if label else ""
                
                if time_val:
                    slots.append({"time": time_val, "status": status})
            
            themes_data.append({"title": title, "img": github_img_path, "slots": slots})
        return themes_data
    except Exception as e:
        print(f"크롤링 에러 [{brand_key}]: {e}")
        return []