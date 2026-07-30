import swoopyui
from swoopyui import *
import threading
import subprocess
from main import main as download_main


def build_ui(view):
    log_field_ref = [None]
    progress_text_ref = [None]
    log_toggle_ref = [None]
    start_btn_text_ref = [None]
    is_running = [False]
    stop_event = threading.Event()

    config_fields = {}

    def browse_file():
        try:
            result = subprocess.run(
                ['osascript', '-e', 'POSIX path of (choose file with prompt "选择Excel文件")'],
                capture_output=True, text=True, timeout=10
            )
            path = result.stdout.strip()
            if path and not result.returncode:
                f = config_fields.get('excel')
                if f:
                    f.content = path
                    f.vdata['props']['content'] = path
                    f.update()
        except Exception:
            pass

    def browse_folder():
        try:
            result = subprocess.run(
                ['osascript', '-e', 'POSIX path of (choose folder with prompt "选择输出目录")'],
                capture_output=True, text=True, timeout=10
            )
            path = result.stdout.strip()
            if path and not result.returncode:
                f = config_fields.get('output')
                if f:
                    f.content = path
                    f.vdata['props']['content'] = path
                    f.update()
        except Exception:
            pass

    def toggle_log(toggle):
        log_field = log_field_ref[0]
        if not log_field:
            return
        if toggle.active:
            log_field.height = 200
            log_field.vdata['props']['height'] = 200
        else:
            log_field.height = 0
            log_field.vdata['props']['height'] = 0
        log_field.update()

    def start_download(btn):
        if is_running[0]:
            return
        is_running[0] = True

        try:
            interval = int(config_fields['interval'].content) if config_fields.get('interval') and config_fields['interval'].content else 3
        except ValueError:
            interval = 3
        try:
            retries = int(config_fields['retries'].content) if config_fields.get('retries') and config_fields['retries'].content else 3
        except ValueError:
            retries = 3
        try:
            start_num = int(config_fields['start_num'].content) if config_fields.get('start_num') and config_fields['start_num'].content else 1
        except ValueError:
            start_num = 1

        config = {
            "excel_path": config_fields['excel'].content if config_fields.get('excel') else "工作簿1.xlsx",
            "output_dir": config_fields['output'].content if config_fields.get('output') else "./downloads",
            "api_base": config_fields['api'].content if config_fields.get('api') else "http://192.168.0.100:8080/api/hybrid/video_data",
            "sleep_interval": interval,
            "max_retries": retries,
            "start_num": start_num,
        }

        stop_event.clear()
        log_field = log_field_ref[0]
        progress_text = progress_text_ref[0]
        start_btn_text = start_btn_text_ref[0]
        log_toggle = log_toggle_ref[0]

        if start_btn_text:
            start_btn_text.content = "⏳ 运行中..."
            start_btn_text.update()

        if log_toggle:
            log_toggle.active = True
            log_toggle.vdata['props']['activated'] = True
            log_toggle.update()
            if log_field:
                log_field.height = 200
                log_field.vdata['props']['height'] = 200
                log_field.update()

        if log_field:
            log_field.content = ""
            log_field.vdata['props']['content'] = ""
            log_field.update()

        if progress_text:
            progress_text.content = "0 / ?"
            progress_text.update()

        def log_callback(msg):
            if log_field:
                log_field.content += msg + "\n"
                log_field.vdata['props']['content'] = log_field.content
                log_field.update()

        def progress_callback(current, total, filename=""):
            if progress_text:
                progress_text.content = f"{current} / {total}"
                progress_text.update()

        def run():
            try:
                download_main(config, log_callback=log_callback, progress_callback=progress_callback, stop_event=stop_event)
            except Exception as e:
                log_callback(f"❌ 错误: {e}")
            finally:
                if progress_text:
                    progress_text.content = "完成 ✅"
                    progress_text.update()
                if start_btn_text:
                    start_btn_text.content = "▶ 开始下载"
                    start_btn_text.update()
                is_running[0] = False

        threading.Thread(target=run, daemon=True).start()

    def stop_download(btn):
        stop_event.set()

    nav = NavigationStack(title="抖音视频批量下载")
    view.add([nav])

    scroll = ScrollView()
    nav.add([scroll])

    root = VStack(padding=20)
    scroll.add([root])

    root.add([Text("⚙️ 配置", size=22, bold=True)])
    root.add([Spacer()])

    row = HStack()
    root.add([row])
    row.add([Text("Excel 文件:", size=14)])
    excel_field = TextField(content="工作簿1.xlsx", width=180, height=28)
    row.add([excel_field])
    browse_file_btn = Button(width=55, height=28, corner_radius=6, on_click=lambda btn: browse_file())
    browse_file_btn.add([Text("浏览", size=12)])
    row.add([browse_file_btn])
    config_fields['excel'] = excel_field

    row = HStack()
    root.add([row])
    row.add([Text("输出目录:", size=14)])
    output_field = TextField(content="./downloads", width=180, height=28)
    row.add([output_field])
    browse_dir_btn = Button(width=55, height=28, corner_radius=6, on_click=lambda btn: browse_folder())
    browse_dir_btn.add([Text("浏览", size=12)])
    row.add([browse_dir_btn])
    config_fields['output'] = output_field

    row = HStack()
    root.add([row])
    row.add([Text("API 地址:", size=14)])
    api_field = TextField(content="http://192.168.0.100:8080/api/hybrid/video_data", width=280, height=28)
    row.add([api_field])
    config_fields['api'] = api_field

    row = HStack()
    root.add([row])
    row.add([Text("间隔(秒):", size=14)])
    interval_field = TextField(content="3", width=55, height=28)
    row.add([interval_field])
    row.add([Spacer()])
    row.add([Text("重试次数:", size=14)])
    retries_field = TextField(content="3", width=55, height=28)
    row.add([retries_field])
    config_fields['interval'] = interval_field
    config_fields['retries'] = retries_field

    row = HStack()
    root.add([row])
    row.add([Text("起始序号:", size=14)])
    start_num_field = TextField(content="1", width=55, height=28)
    row.add([start_num_field])
    config_fields['start_num'] = start_num_field

    root.add([Spacer()])

    row = HStack()
    root.add([row])
    start_btn = Button(width=130, height=40, corner_radius=10, on_click=start_download)
    start_btn_text = Text("▶ 开始下载", size=16, bold=True)
    start_btn.add([start_btn_text])
    start_btn_text_ref[0] = start_btn_text
    stop_btn = Button(width=100, height=40, corner_radius=10, on_click=stop_download)
    stop_btn.add([Text("■ 停止", size=16)])
    row.add([start_btn, stop_btn])

    root.add([Spacer()])

    root.add([Text("进度", size=18, bold=True)])
    progress_text = Text("0 / ?", size=14)
    root.add([progress_text])
    progress_text_ref[0] = progress_text

    root.add([Spacer()])

    log_toggle = Toggle(content="📋 运行日志", on_change=toggle_log)
    root.add([log_toggle])
    log_toggle_ref[0] = log_toggle

    log_field = TextField(placeholder="", content="", resizeable=True, width=400, height=0)
    root.add([log_field])
    log_field_ref[0] = log_field


def main():
    swoopyui.app(target=build_ui, base_name="抖音视频批量下载", debug=False)


if __name__ == "__main__":
    main()
