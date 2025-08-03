# -*- coding: utf-8 -*-

"""
Yerel ağdaki diğer uygulama örneklerini bulmak için ağ keşif mekanizmaları.
UDP broadcast kullanarak çalışır.
"""

import socket
import threading
import time
import json

DISCOVERY_PORT = 5556  # Keşif için ayrı bir port
BROADCAST_ADDR = "<broadcast>"
ANNOUNCE_INTERVAL = 5  # Saniyede bir anons
APP_SIGNATURE = "AUDIO_STREAM_APP"

class Announcer(threading.Thread):
    """
    Belirli aralıklarla ağa varlığını duyuran sınıf (Alıcı tarafında çalışır).
    """
    def __init__(self):
        super().__init__(daemon=True)
        self.running = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def run(self):
        self.running = True
        message = json.dumps({"signature": APP_SIGNATURE, "hostname": socket.gethostname()}).encode('utf-8')
        while self.running:
            try:
                self.sock.sendto(message, (BROADCAST_ADDR, DISCOVERY_PORT))
                # print(f"Duyuru yapıldı: {message}")
            except Exception as e:
                print(f"Duyuru hatası: {e}")
            time.sleep(ANNOUNCE_INTERVAL)

    def stop(self):
        self.running = False

class Listener(threading.Thread):
    """
    Ağdaki duyuruları dinleyen sınıf (Gönderici tarafında çalışır).
    """
    def __init__(self):
        super().__init__(daemon=True)
        self.running = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.found_hosts = {}  # {ip: (hostname, timestamp)}

    def run(self):
        self.running = True
        self.sock.bind(("", DISCOVERY_PORT))
        print(f"Keşif dinleyicisi başlatıldı: Port {DISCOVERY_PORT}")
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                message = json.loads(data.decode('utf-8'))
                if message.get("signature") == APP_SIGNATURE:
                    ip = addr[0]
                    hostname = message.get("hostname", "Bilinmeyen")
                    self.found_hosts[ip] = (hostname, time.time())
                    # print(f"Alıcı bulundu: {hostname} ({ip})")
            except Exception as e:
                if self.running:
                    print(f"Dinleme hatası: {e}")

    def stop(self):
        self.running = False
        # çalışan recvfrom'u kırmak için soketi kapat
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except (socket.error, OSError) as e:
                print(f"Dinleyici soketi kapatılırken hata (muhtemelen zaten kapalı): {e}")
        self.sock = None

    def get_active_hosts(self, timeout=15):
        """
        Son 'timeout' saniye içinde görülen aktif sunucuları döndürür.
        """
        now = time.time()
        return {ip: hostname for ip, (hostname, ts) in self.found_hosts.items() if now - ts < timeout}