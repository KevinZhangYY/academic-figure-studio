"""Windows portable launcher. The browser editor stays on a stable local origin."""
import argparse
import json
import os
import sys
import threading
import webbrowser
from pathlib import Path
from urllib.request import urlopen
import server

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--headless', action='store_true', help='Run without launcher/browser (build smoke tests)')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    server.DATA.mkdir(parents=True, exist_ok=True)
    address = f'http://127.0.0.1:{args.port}'
    try:
        httpd = server.ThreadingHTTPServer(('127.0.0.1', args.port), server.Handler)
    except OSError:
        try:
            with urlopen(address+'/api/health', timeout=2) as response:
                health = json.load(response)
            if health.get('name') == 'Academic Figure Studio' and health.get('version') == server.VERSION:
                if not args.headless:
                    webbrowser.open(address)
                return
        except Exception:
            pass
        raise RuntimeError(f'端口 {args.port} 已被占用。请先关闭旧版工作台，再启动此版本。')
    if args.headless:
        httpd.serve_forever()
        return
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.title('Academic Figure Studio '+server.VERSION)
    root.geometry('520x250')
    tk.Label(root, text='学术组图工作台', font=('Microsoft YaHei', 18)).pack(pady=(20,8))
    tk.Label(root, text=f'版本 {server.VERSION} · Windows x64\n工作台在浏览器中运行。关闭此窗口会停止服务。\n退出前请在工作台保存项目。', font=('Microsoft YaHei', 10)).pack(pady=8)
    tk.Button(root, text='打开工作台', command=lambda: webbrowser.open(address), width=22).pack(pady=8)
    def close():
        if messagebox.askokcancel('退出工作台', '请确认已保存项目。是否停止服务并退出？'):
            httpd.shutdown()
            httpd.server_close()
            root.destroy()
    root.protocol('WM_DELETE_WINDOW', close)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    root.after(300, lambda: webbrowser.open(address))
    root.mainloop()

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        if '--headless' in sys.argv:
            raise
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk(); root.withdraw()
        messagebox.showerror('Academic Figure Studio', str(error))
        root.destroy()
        sys.exit(1)
