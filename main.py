# -*- coding: utf-8 -*-

"""
Ana uygulama giriş noktası.
"""

from ui.main_window import App
if __name__ == "__main__":
    app = App()
    try:
        app.iconbitmap("favicon.ico")
    except Exception as e:
        print(f"Ikon ayarlanamadı: {e}")
    app.protocol("WM_DELETE_WINDOW", lambda: app.on_closing())
    app.mainloop()