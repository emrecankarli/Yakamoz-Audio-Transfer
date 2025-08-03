# -*- coding: utf-8 -*-

"""
Uygulamanın ana arayüz penceresi.
"""

import customtkinter
from core.audio_sender import AudioSender
from core.audio_receiver import AudioReceiver
from utils.device_manager import get_loopback_devices
from utils.config_manager import load_setting, save_setting
from core.network_discovery import Announcer, Listener
from utils.localization import i18n, set_language
import threading
from PIL import Image
import pystray

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title(i18n.get("app_title"))
        self.geometry("500x450") # Pencereyi biraz büyütelim

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.current_frame = None
        
        # Dil ayarını yükle
        lang = load_setting("language", "tr")
        set_language(lang)

        self.show_main_menu()

        self.audio_sender = None
        self.audio_receiver = None
        self.announcer = None
        self.listener = None
        self.tray_icon = None
        self.setup_tray_icon()

    def setup_tray_icon(self):
        try:
            image = Image.open("favicon.ico")
            menu = (pystray.MenuItem('Göster', self.show_window, default=True),
                    pystray.MenuItem('Çıkış', self.quit_app))
            self.tray_icon = pystray.Icon("Yakamoz", image, "Yakamoz", menu)
            
            # pystray'i ayrı bir thread'de çalıştır
            tray_thread = threading.Thread(target=self.tray_icon.run)
            tray_thread.daemon = True
            tray_thread.start()
        except Exception as e:
            print(f"Tray icon oluşturulamadı: {e}")

    def show_window(self):
        self.tray_icon.stop()
        self.after(0, self.deiconify)

    def hide_window(self):
        self.withdraw()
        self.setup_tray_icon()

    def quit_app(self):
        if self.tray_icon:
            self.tray_icon.stop()
        self.on_closing(force_quit=True)

    def change_language(self, language):
        set_language(language)
        save_setting("language", language)
        self.title(i18n.get("app_title"))
        # Arayüzü yeniden çiz
        self.show_frame(self.current_frame.__class__)

    def show_frame(self, frame_class):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = frame_class(self)
        self.current_frame.grid(row=0, column=0, sticky="nsew")

    def show_main_menu(self):
        self.show_frame(MainMenuFrame)

    def start_sender(self, ip_address, device_name):
        if not self.audio_sender:
            self.audio_sender = AudioSender(dest_ip=ip_address, device=device_name)
            if self.audio_sender.start_streaming():
                print("Gönderim başladı.")
                return True
        return False

    def stop_sender(self):
        if self.audio_sender:
            self.audio_sender.stop_streaming()
            self.audio_sender = None
            print("Gönderim durduruldu.")

    def start_receiver(self):
        if not self.audio_receiver:
            self.audio_receiver = AudioReceiver()
            if self.audio_receiver.start_listening():
                print("Dinleme başladı.")
                # Duyuruyu başlat
                if not self.announcer:
                    self.announcer = Announcer()
                    self.announcer.start()
                return True
        return False

    def stop_receiver(self):
        if self.audio_receiver:
            self.audio_receiver.stop_listening()
            self.audio_receiver = None
            print("Dinleme durduruldu.")
        # Duyuruyu durdur
        if self.announcer:
            self.announcer.stop()
            self.announcer = None

    def on_closing(self, force_quit=False):
        if not force_quit:
            self.hide_window()
        else:
            self.stop_sender()
            self.stop_receiver()
            if self.listener:
                self.listener.stop()
            self.destroy()

class MainMenuFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1, 2, 3), weight=1)

        # Yakamoz Title
        self.title_label = customtkinter.CTkLabel(self, text=i18n.get("yakamoz_title"), font=customtkinter.CTkFont(size=50, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 0))

        # Subtitle
        self.subtitle_label = customtkinter.CTkLabel(self, text=i18n.get("yakamoz_subtitle"), font=customtkinter.CTkFont(size=14), text_color="gray")
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 40))

        # Button Frame
        button_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        self.sender_button = customtkinter.CTkButton(button_frame, text=i18n.get("sender_button"), command=lambda: master.show_frame(SenderFrame))
        self.sender_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.receiver_button = customtkinter.CTkButton(button_frame, text=i18n.get("receiver_button"), command=lambda: master.show_frame(ReceiverFrame))
        self.receiver_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # Language Selection
        lang_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        lang_frame.grid(row=3, column=0, pady=(20, 20))
        
        self.lang_label = customtkinter.CTkLabel(lang_frame, text="Dil/Language:")
        self.lang_label.pack(side="left", padx=(0, 10))

        self.lang_menu = customtkinter.CTkOptionMenu(lang_frame, values=["Türkçe", "English"],
                                                     command=self.change_language_ui)
        
        current_lang_ui = "Türkçe" if i18n.language == "tr" else "English"
        self.lang_menu.set(current_lang_ui)
        self.lang_menu.pack(side="left")

    def change_language_ui(self, choice):
        lang_code = "tr" if choice == "Türkçe" else "en"
        self.master.change_language(lang_code)

class SenderFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.grid_columnconfigure(0, weight=1)

        self.ip_label = customtkinter.CTkLabel(self, text=i18n.get("target_ip_label"))
        self.ip_label.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        self.ip_entry = customtkinter.CTkEntry(self, placeholder_text="192.168.1.100")
        self.ip_entry.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        last_ip = load_setting("last_ip", "")
        if last_ip:
            self.ip_entry.insert(0, last_ip)

        self.device_label = customtkinter.CTkLabel(self, text=i18n.get("audio_device_label"))
        self.device_label.grid(row=2, column=0, padx=20, pady=(10, 5), sticky="w")
        self.devices = get_loopback_devices()
        self.device_menu = customtkinter.CTkOptionMenu(self, values=self.devices if self.devices else [i18n.get("device_not_found")])
        self.device_menu.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        if not self.devices:
            self.device_menu.configure(state="disabled")

        # Bulunan Alıcılar
        self.discovery_label = customtkinter.CTkLabel(self, text=i18n.get("discovered_receivers_label"))
        self.discovery_label.grid(row=4, column=0, padx=20, pady=(10, 5), sticky="w")
        self.discovery_menu = customtkinter.CTkOptionMenu(self, values=[i18n.get("scanning")], command=self.select_discovered_host)
        self.discovery_menu.grid(row=5, column=0, padx=20, pady=5, sticky="ew")

        self.start_button = customtkinter.CTkButton(self, text=i18n.get("start_broadcast_button"), command=self.start_sending)
        self.start_button.grid(row=6, column=0, padx=20, pady=10)
        if not self.devices:
            self.start_button.configure(state="disabled")

        self.stop_button = customtkinter.CTkButton(self, text=i18n.get("stop_broadcast_button"), command=self.stop_sending, state="disabled")
        self.stop_button.grid(row=7, column=0, padx=20, pady=10)

        self.ping_label = customtkinter.CTkLabel(self, text=i18n.get("ping_label"))
        self.ping_label.grid(row=8, column=0, padx=20, pady=5)
        
        self.back_button = customtkinter.CTkButton(self, text=i18n.get("return_to_main_menu_button"), command=self.go_back)
        self.back_button.grid(row=9, column=0, padx=20, pady=(20, 0))

        self.ping_update_job = None
        self.start_discovery()

        # Eğer zaten bir gönderim işlemi varsa arayüzü güncelle
        if self.master.audio_sender and self.master.audio_sender.streaming:
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.device_menu.configure(state="disabled")
            self.discovery_menu.configure(state="disabled")
            self.ip_entry.delete(0, "end")
            self.ip_entry.insert(0, self.master.audio_sender.dest_ip)

    def start_discovery(self):
        if not self.master.listener:
            self.master.listener = Listener()
            self.master.listener.start()
        self.after(1000, self.update_discovery_list)

    def update_discovery_list(self):
        if self.master.listener:
            active_hosts = self.master.listener.get_active_hosts()
            if active_hosts:
                # Format: "hostname (ip)"
                host_list = [f"{hostname} ({ip})" for ip, hostname in active_hosts.items()]
                self.discovery_menu.configure(values=host_list)
            else:
                self.discovery_menu.configure(values=[i18n.get("receiver_not_found")])
            self.after(3000, self.update_discovery_list) # 3 saniyede bir güncelle

    def select_discovered_host(self, selected_host):
        # "hostname (ip)" formatından IP'yi ayıkla
        try:
            ip = selected_host.split('(')[-1].strip(')')
            self.ip_entry.delete(0, "end")
            self.ip_entry.insert(0, ip)
        except IndexError:
            pass # "Taranıyor..." gibi bir seçenekte hata vermesin

    def start_sending(self):
        ip = self.ip_entry.get()
        device = self.device_menu.get()
        if ip and device != i18n.get("device_not_found") and self.master.start_sender(ip, device):
            save_setting("last_ip", ip)
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.device_menu.configure(state="disabled")
            self.discovery_menu.configure(state="disabled")
            self.update_ping_label()

    def stop_sending(self):
        if self.ping_update_job:
            self.after_cancel(self.ping_update_job)
            self.ping_update_job = None
        self.master.stop_sender()
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        if self.devices:
            self.device_menu.configure(state="normal")
        self.discovery_menu.configure(state="normal")
        self.ping_label.configure(text=i18n.get("ping_label"))

    def update_ping_label(self):
        if self.master.audio_sender and self.master.audio_sender.streaming:
            ping = self.master.audio_sender.ping_ms
            if ping >= 0:
                self.ping_label.configure(text=f"Ping: {ping:.2f} ms")
            else:
                self.ping_label.configure(text=i18n.get("ping_na"))
            self.ping_update_job = self.after(1000, self.update_ping_label)

    def go_back(self):
        if self.master.listener:
            self.master.listener.stop()
            self.master.listener = None
        self.master.show_main_menu()

class ReceiverFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.grid_columnconfigure(0, weight=1)

        self.status_label = customtkinter.CTkLabel(self, text=i18n.get("listening_status_passive"))
        self.status_label.grid(row=0, column=0, padx=20, pady=20)

        self.start_button = customtkinter.CTkButton(self, text=i18n.get("start_listening_button"), command=self.start_listening)
        self.start_button.grid(row=1, column=0, padx=20, pady=10)

        self.stop_button = customtkinter.CTkButton(self, text=i18n.get("stop_listening_button"), command=self.stop_listening, state="disabled")
        self.stop_button.grid(row=2, column=0, padx=20, pady=10)

        self.back_button = customtkinter.CTkButton(self, text=i18n.get("return_to_main_menu_button"), command=self.go_back)
        self.back_button.grid(row=3, column=0, padx=20, pady=(20, 0))

    def start_listening(self):
        if self.master.start_receiver():
            self.status_label.configure(text=i18n.get("listening_status_active"))
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")

    def stop_listening(self):
        self.master.stop_receiver()
        self.status_label.configure(text=i18n.get("listening_status_passive"))
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")

    def go_back(self):
        self.master.stop_receiver()
        self.master.show_main_menu()