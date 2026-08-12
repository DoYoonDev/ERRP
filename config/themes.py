# config/themes.py
import os
import re
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv()

repo_owner = os.getenv("REPO_OWNER", "DoYoonDev")
repo_name = os.getenv("REPO_NAME", "ERRP")
branch = os.getenv("BRANCH", "main")
GITHUB_BASE = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{branch}/static/images/"

def get_theme_image(store_folder: str, theme_name: str) -> str:
    """
    지점 폴더명과 테마 이름을 받아:
    1. 특수기호를 모두 삭제하고
    2. 띄어쓰기를 언더바(_)로 바꾸어
    완벽한 깃허브 이미지 URL을 반환합니다.
    """
    safe_store = store_folder.strip()
    
    # 💡 [핵심] 한글, 영문, 숫자, 띄어쓰기, 하이픈(-)을 제외한 모든 특수기호(!, ?, [, ], (, ), ~ 등) 삭제
    cleaned_theme = re.sub(r'[^가-힣a-zA-Z0-9\s-]', '', theme_name)
    
    # 띄어쓰기를 언더바(_)로 변경하고 .jpg 붙이기
    safe_theme = cleaned_theme.strip().replace(" ", "_") + ".jpg"
    
    # 한글 및 경로가 깨지지 않도록 안전하게 URL 인코딩
    encoded_path = quote(f"{safe_store}/{safe_theme}")
    
    return f"{GITHUB_BASE}{encoded_path}"