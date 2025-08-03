# -*- coding: utf-8 -*-

"""
Ses verisini yakalayıp ağ üzerinden gönderen modül.
"""

import socket
import struct
import threading
import time
import numpy as np
import soundcard as sc

class AudioSender:
    """
    Sistem sesini yakalayıp UDP üzerinden belirli bir hedefe gönderen sınıf.
    """
    def __init__(self, dest_ip, dest_port=5555, rate=48000, device=None):
        self.dest_ip = dest_ip
        self.dest_port = dest_port
        self.control_port = dest_port + 1
        self.rate = rate
        self.device_substr = device
        self.loop_mic = None
        self.sock = None
        self.control_sock = None
        self.seq = 0
        self.streaming = False
        self.thread = None
        self.control_thread = None
        self.ping_ms = -1

    def _find_loopback(self):
        """Belirtilen ada sahip geri döngü mikrofonunu bulur."""
        # Not: Arayüzden tam aygıt adı geldiği için artık alt dize kontrolü yerine
        # doğrudan isimle arama yapıyoruz.
        try:
            # `get_microphone` tam ad eşleşmesi bekler.
            return sc.get_microphone(self.device_substr, include_loopback=True)
        except Exception as e:
            print(f"Aygıt bulunurken hata: {e}")
            # Alternatif olarak, listeden de arayabiliriz.
            for mic in sc.all_microphones(include_loopback=True):
                if self.device_substr == mic.name:
                    return mic
            return None

    def _stream_mic_thread(self):
        """Ses verisini ayrı bir thread'de yakalar ve gönderir."""
        FRAME = 480 if self.rate == 48_000 else 882  # 10 ms frame

        try:
            with self.loop_mic.recorder(samplerate=self.rate, blocksize=FRAME, channels=2) as rec:
                print(f"⏺️  Akış başladı: {self.dest_ip}:{self.dest_port}")
                while self.streaming:
                    data = rec.record(numframes=FRAME)
                    pcm = (data * 32767).astype(np.int16).tobytes()
                    header = struct.pack("!H", self.seq)
                    self.sock.sendto(header + pcm, (self.dest_ip, self.dest_port))
                    self.seq = (self.seq + 1) & 0xFFFF
        except Exception as e:
            print(f"💥  Akış sırasında hata: {e}")
        finally:
            print("⏹️  Akış durduruldu.")

    def _control_thread_func(self):
        """Ping gönderip yanıtları dinleyen thread."""
        while self.streaming:
            try:
                # Ping gönder
                timestamp = time.time()
                msg = struct.pack("!d", timestamp)
                self.control_sock.sendto(b"PING" + msg, (self.dest_ip, self.control_port))

                # Pong bekle
                self.control_sock.settimeout(1)
                data, _ = self.control_sock.recvfrom(1024)
                if data.startswith(b"PONG"):
                    rtt = time.time() - timestamp
                    self.ping_ms = rtt * 1000
                
            except socket.timeout:
                self.ping_ms = -1 # Zaman aşımı
            except Exception as e:
                if self.streaming:
                    print(f"Kontrol soketi hatası: {e}")
                break
            
            time.sleep(1) # Her saniye ping gönder

    def start_streaming(self):
        """Akışı başlatır."""
        if self.streaming:
            print("Zaten akış yapılıyor.")
            return False

        self.loop_mic = self._find_loopback()
        if self.loop_mic is None:
            print("‼️ Geri döngü aygıtı bulunamadı.")
            return False

        print(f"🎧 Kullanılan aygıt: '{self.loop_mic.name}' @ {self.rate} Hz")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.control_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.seq = 0
        self.streaming = True
        
        self.thread = threading.Thread(target=self._stream_mic_thread)
        self.thread.daemon = True
        self.thread.start()

        self.control_thread = threading.Thread(target=self._control_thread_func)
        self.control_thread.daemon = True
        self.control_thread.start()

        return True

    def stop_streaming(self):
        """Akışı durdurur."""
        if not self.streaming:
            print("Akış zaten durdurulmuş.")
            return

        self.streaming = False
        if self.thread:
            self.thread.join(timeout=1)
        if self.control_thread:
            self.control_thread.join(timeout=1)
            
        if self.sock:
            self.sock.close()
        if self.control_sock:
            self.control_sock.close()

        self.thread = None
        self.control_thread = None
        self.sock = None
        self.control_sock = None
        self.ping_ms = -1