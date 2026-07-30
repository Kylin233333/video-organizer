import os
import re
import time
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ===== 配置区 =====
EXCEL_PATH = "工作簿1.xlsx"          # Excel 文件路径
OUTPUT_DIR = "./downloads"     # 视频保存目录
API_BASE = "http://192.168.0.100:8080/api/hybrid/video_data"
SLEEP_INTERVAL = 3                   # 每次请求间隔秒数
MAX_RETRIES = 3                      # 每个链接的最大重试次数
# =================

# 创建保存目录
os.makedirs(OUTPUT_DIR, exist_ok=True)

def sanitize_filename(name):
    """过滤文件名中的非法字符"""
    illegal_chars = r'[<>:"/\\|?*]'
    name = re.sub(illegal_chars, '_', name)
    name = name.strip('. ')
    if len(name) > 120:
        name = name[:120]
    return name or "untitled"

def download_video(url_list, save_path, max_retries=MAX_RETRIES):
    """视频下载函数"""
    session = requests.Session()
    retries = Retry(total=max_retries, backoff_factor=1,
                    status_forcelist=[500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.douyin.com/',
        'Accept': '*/*',
        'Accept-Encoding': 'identity',
        'Connection': 'keep-alive',
    }

    for idx, video_url in enumerate(url_list):
        print(f"  尝试链接 {idx+1}/{len(url_list)}")
        for attempt in range(max_retries):
            try:
                resp = session.get(video_url, headers=headers, stream=True, timeout=30)
                resp.raise_for_status()
                with open(save_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"  ✅ 下载成功 (使用链接 {idx+1})")
                return True
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    print(f"  ⚠️ 链接 {idx+1} 尝试 {attempt+1}/{max_retries} 返回 403")
                else:
                    print(f"  ⚠️ 链接 {idx+1} HTTP错误: {e}")
                time.sleep(2)
            except Exception as e:
                print(f"  ⚠️ 链接 {idx+1} 下载异常: {e}")
                time.sleep(2)
    print(f"  ❌ 所有链接尝试失败: {save_path}")
    return False

def get_video_info(share_url):
    """调用本地API获取视频信息"""
    params = {"url": share_url, "minimal": "false"}
    try:
        resp = requests.get(API_BASE, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") == 200:
            return data.get("data")
        else:
            print(f"API返回错误: {data}")
            return None
    except Exception as e:
        print(f"API请求异常: {e}")
        return None

def main():
    # -------- 用户输入起始序号 --------
    while True:
        try:
            start_num = int(input("请输入起始序号（整数）: "))
            break
        except ValueError:
            print("输入无效，请输入整数。")

    # -------- 读取 Excel --------
    df = pd.read_excel(EXCEL_PATH, engine='openpyxl', dtype={2: str})
    # A列->作品名，B列->抖音链接，C列->日期
    title_col = df.columns[0]   # 第一列
    url_col = df.columns[1]     # 第二列
    date_col = df.columns[2]    # 第三列

    seq = start_num   # 序号计数器

    for idx, row in df.iterrows():
        share_url = row[url_col]
        # 跳过空链接或非字符串
        if pd.isna(share_url) or not isinstance(share_url, str):
            continue

        # 获取作品名（原Excel A列）
        raw_title = row[title_col] if not pd.isna(row[title_col]) else f"video_{idx}"
        safe_title = sanitize_filename(str(raw_title))

        # 获取日期（原Excel C列），为空则用 "0000"
        raw_date = row[date_col] if not pd.isna(row[date_col]) else "0000"
        date_str = str(raw_date).strip()

        # 生成序号（三位数，补零）
        seq_str = f"{seq:03d}"

        print(f"\n处理第 {idx+2} 行: {share_url} | 序号: {seq_str} | 日期: {date_str}")

        # 调用API获取下载链接
        video_data = get_video_info(share_url)
        if not video_data:
            seq += 1   # 即使失败也递增序号（可按需调整，建议保持顺序）
            continue

        # 获取无水印视频链接列表
        video_info = video_data.get("video", {})
        play_addr = video_info.get("play_addr", {})
        url_list = play_addr.get("url_list", [])
        if not url_list:
            print("未找到视频下载链接")
            seq += 1
            continue

        # 生成最终文件名：序号_日期_作品名.mp4
        filename = f"{seq_str}_{date_str}_{safe_title}.mp4"
        save_path = os.path.join(OUTPUT_DIR, filename)

        # 下载视频
        print(f"下载到: {save_path}")
        success = download_video(url_list, save_path, max_retries=MAX_RETRIES)
        if success:
            print("下载完成")
        else:
            print("下载失败")

        # 序号递增（无论成败，保持连续序号）
        seq += 1

        # 避免请求过快
        time.sleep(SLEEP_INTERVAL)

    print("\n所有任务处理完毕！")

if __name__ == "__main__":
    main()