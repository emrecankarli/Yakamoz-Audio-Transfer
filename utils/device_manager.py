# -*- coding: utf-8 -*-

"""
Sistemdeki ses aygıtlarını yönetmek için yardımcı fonksiyonlar.
"""

import soundcard as sc

def get_loopback_devices():
    """
    Sistemdeki tüm geri döngü (loopback) ses aygıtlarının bir listesini döndürür.
    """
    try:
        loopback_mics = sc.all_microphones(include_loopback=True)
        # Sadece aygıt adlarını içeren bir liste döndür
        return [mic.name for mic in loopback_mics]
    except Exception as e:
        print(f"Ses aygıtları listelenirken bir hata oluştu: {e}")
        return []