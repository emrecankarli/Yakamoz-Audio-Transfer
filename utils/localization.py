# -*- coding: utf-8 -*-

"""
Dil çevirilerini yöneten modül.
"""

TRANSLATIONS = {
    "en": {
        "app_title": "Yakamoz - PC to PC Audio Transfer",
        "sender_button": "Sender",
        "receiver_button": "Receiver",
        "target_ip_label": "Target IP Address:",
        "audio_device_label": "Audio Device:",
        "device_not_found": "Device not found",
        "discovered_receivers_label": "Discovered Receivers:",
        "scanning": "Scanning...",
        "receiver_not_found": "Receiver not found...",
        "start_broadcast_button": "Start Broadcast",
        "stop_broadcast_button": "Stop Broadcast",
        "return_to_main_menu_button": "Return to Main Menu",
        "listening_status_passive": "Listening status: Passive",
        "listening_status_active": "Listening status: Active",
        "start_listening_button": "Start Listening",
        "stop_listening_button": "Stop Listening",
        "ping_label": "Ping: -",
        "ping_na": "Ping: N/A",
        "yakamoz_title": "Yakamoz",
        "yakamoz_subtitle": "PC to PC Audio Transfer"
    },
    "tr": {
        "app_title": "Yakamoz - PC'den PC'ye Ses Aktarımı",
        "sender_button": "Gönderici",
        "receiver_button": "Alıcı",
        "target_ip_label": "Hedef IP Adresi:",
        "audio_device_label": "Ses Aygıtı:",
        "device_not_found": "Aygıt bulunamadı",
        "discovered_receivers_label": "Bulunan Alıcılar:",
        "scanning": "Taranıyor...",
        "receiver_not_found": "Alıcı bulunamadı...",
        "start_broadcast_button": "Yayını Başlat",
        "stop_broadcast_button": "Yayını Durdur",
        "return_to_main_menu_button": "Ana Menüye Dön",
        "listening_status_passive": "Dinleme durumu: Pasif",
        "listening_status_active": "Dinleme durumu: Aktif",
        "start_listening_button": "Dinlemeyi Başlat",
        "stop_listening_button": "Dinlemeyi Durdur",
        "ping_label": "Ping: -",
        "ping_na": "Ping: N/A",
        "yakamoz_title": "Yakamoz",
        "yakamoz_subtitle": "PC'den PC'ye Ses Aktarımı"
    }
}

class I18n:
    def __init__(self, language="tr"):
        self.language = language

    def get(self, key):
        return TRANSLATIONS.get(self.language, {}).get(key, key)

# Global instance
i18n = I18n()

def set_language(language):
    i18n.language = language