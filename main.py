import os
import re
import time
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def sanitize_filename(name):
    illegal_chars = r'[<>:"/\\|?*]'
    name = re.sub(illegal_chars, '_', name)
    name = name.strip('. ')
    if len(name) > 120:
        name = name[:120]
    return name or "untitled"


def download_video(url_list, save_path, max_retries=3, log_callback=print):
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
        log_callback(f"  尝试链接 {idx+1}/{len(url_list)}")
        for attempt in range(max_retries):
            try:
                resp = session.get(video_url, headers=headers, stream=True, timeout=30)
                resp.raise_for_status()
                with open(save_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                log_callback(f"  ✅ 下载成功 (使用链接 {idx+1})")
                return True
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    log_callback(f"  ⚠️ 链接 {idx+1} 尝试 {attempt+1}/{max_retries} 返回 403")
                else:
                    log_callback(f"  ⚠️ 链接 {idx+1} HTTP错误: {e}")
                time.sleep(2)
            except Exception as e:
                log_callback(f"  ⚠️ 链接 {idx+1} 下载异常: {e}")
                time.sleep(2)
    log_callback(f"  ❌ 所有链接尝试失败: {save_path}")
    return False


def get_video_info(share_url, api_base, log_callback=print):
    params = {"url": share_url, "minimal": "false"}
    try:
        resp = requests.get(api_base, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") == 200:
            return data.get("data")
        else:
            log_callback(f"API返回错误: {data}")
            return None
    except Exception as e:
        log_callback(f"API请求异常: {e}")
        return None


def main(config, log_callback=print, progress_callback=None, stop_event=None):
    excel_path = config.get("excel_path", "工作簿1.xlsx")
    output_dir = config.get("output_dir", "./downloads")
    api_base = config.get("api_base", "http://192.168.0.100:8080/api/hybrid/video_data")
    sleep_interval = config.get("sleep_interval", 3)
    max_retries = config.get("max_retries", 3)
    start_num = config.get("start_num", 1)

    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_excel(excel_path, engine='openpyxl', dtype={2: str})
    title_col = df.columns[0]
    url_col = df.columns[1]
    date_col = df.columns[2]

    total = len(df)
    seq = start_num
    stopped = False

    for idx, row in df.iterrows():
        if stop_event and stop_event.is_set():
            log_callback("\n⏹ 用户已停止")
            stopped = True
            break

        share_url = row[url_col]
        if pd.isna(share_url) or not isinstance(share_url, str):
            if progress_callback:
                progress_callback(idx + 1, total)
            continue

        raw_title = row[title_col] if not pd.isna(row[title_col]) else f"video_{idx}"
        safe_title = sanitize_filename(str(raw_title))

        raw_date = row[date_col] if not pd.isna(row[date_col]) else "0000"
        date_str = str(raw_date).strip()

        seq_str = f"{seq:03d}"

        log_callback(f"\n处理第 {idx+2} 行: {share_url} | 序号: {seq_str} | 日期: {date_str}")

        if progress_callback:
            progress_callback(idx + 1, total, f"{seq_str}_{date_str}_{safe_title}.mp4")

        video_data = get_video_info(share_url, api_base, log_callback)
        if not video_data:
            seq += 1
            if progress_callback:
                progress_callback(idx + 1, total)
            continue

        video_info = video_data.get("video", {})
        play_addr = video_info.get("play_addr", {})
        url_list = play_addr.get("url_list", [])
        if not url_list:
            log_callback("未找到视频下载链接")
            seq += 1
            if progress_callback:
                progress_callback(idx + 1, total)
            continue

        filename = f"{seq_str}_{date_str}_{safe_title}.mp4"
        save_path = os.path.join(output_dir, filename)

        log_callback(f"下载到: {save_path}")
        success = download_video(url_list, save_path, max_retries, log_callback)
        log_callback("下载完成" if success else "下载失败")

        seq += 1
        if progress_callback:
            progress_callback(idx + 1, total)
        time.sleep(sleep_interval)

    if not stopped:
        log_callback("\n所有任务处理完毕！")
