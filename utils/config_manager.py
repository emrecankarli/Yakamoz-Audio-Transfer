# -*- coding: utf-8 -*-

"""
Uygulama ayarlarını yönetmek için yardımcı fonksiyonlar.
Ayarları bir JSON dosyasında saklar.
"""

import json
import os

CONFIG_FILE = "config.json"

def save_config(data):
    """
    Verilen sözlük verisini config.json dosyasına kaydeder.
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        print(f"Yapılandırma dosyası yazılamadı: {e}")

def load_config():
    """
    config.json dosyasından ayarları yükler.
    Dosya yoksa veya boşsa, boş bir sözlük döndürür.
    """
    if not os.path.exists(CONFIG_FILE):
        return {}
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            # Dosyanın boş olup olmadığını kontrol et
            content = f.read()
            if not content:
                return {}
            return json.loads(content)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Yapılandırma dosyası okunamadı: {e}")
        return {}

def save_setting(key, value):
    """
    Belirli bir ayarı (anahtar-değer çifti) kaydeder.
    """
    config = load_config()
    config[key] = value
    save_config(config)

def load_setting(key, default=None):
    """
    Belirli bir ayarı okur. Bulunamazsa varsayılan değeri döndürür.
    """
    config = load_config()
    return config.get(key, default)