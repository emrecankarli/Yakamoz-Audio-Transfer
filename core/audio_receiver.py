# -*- coding: utf-8 -*-

"""
Ağdan gelen ses verisini alıp çalan modül.
"""

import socket
import threading
import collections
import time
import struct
import numpy as np
import soundcard as sc

class AudioReceiver:
    """
    UDP üzerinden gelen ses verisini dinleyen ve varsayılan ses aygıtında çalan sınıf.
    """
    def __init__(self, port=5555, rate=48000, prebuffer=2):
        self.port = port
        self.control_port = port + 1
        self.rate = rate
        self.prebuffer = prebuffer
        self.sock = None
        self.control_sock = None
        self.player = None
        self.speaker = None
        self.listening = False
        self.thread = None
        self.control_thread = None
        self.jitter = None

    def _open_player(self):
        """Varsayılan hoparlörü açar ve player nesnesini döndürür."""
        FRAME = 480  # 10 ms @ 48 kHz
        try:
            spk = sc.default_speaker()
            print(f"🔊  Çıkış → {spk.name}")
            player = spk.player(samplerate=self.rate, blocksize=FRAME, channels=2)
            return spk, player
        except Exception as e:
            print(f"💥  Hoparlör açılırken hata: {e}")
            return None, None

    def _listen_thread(self):
        """Ayrı bir thread'de ağdan ses verisi dinler ve çalar."""
        self.speaker, self.player = self._open_player()
        if not self.player:
            self.listening = False
            return

        self.jitter = collections.deque(maxlen=self.prebuffer + 50)
        last_dev_check = time.time()

        with self.player:
            while self.listening:
                # -------- ağdan oku ----------
                try:
                    pkt, _ = self.sock.recvfrom(4096)
                    pcm = np.frombuffer(pkt[2:], dtype=np.int16)
                    self.jitter.append(pcm.reshape(-1, 2).astype(np.float32) / 32767)
                except BlockingIOError:
                    time.sleep(0.001)  # CPU kullanımını azaltmak için küçük bir bekleme
                except Exception as e:
                    if self.listening:
                        print(f"Socket hatası: {e}")
                    break

                # -------- çal -----------------
                if len(self.jitter) > self.prebuffer:
                    try:
                        self.player.play(self.jitter.popleft())
                    except Exception as e:
                        print(f"Çalma hatası: {e}")


                # -------- aygıt değişti mi? ----
                if time.time() - last_dev_check > 0.5:
                    last_dev_check = time.time()
                    try:
                        cur = sc.default_speaker()
                        if cur.name != self.speaker.name:
                            print("⟳  Varsayılan ses aygıtı değişti!")
                            self.player.close()
                            self.speaker, self.player = self._open_player()
                            if self.player:
                                self.player.__enter__()
                            else:
                                print("Yeni aygıt açılamadı, dinleme durduruluyor.")
                                self.listening = False
                    except Exception as e:
                        print(f"Aygıt kontrol hatası: {e}")
                        self.listening = False

        print("⏹️  Dinleme durduruldu.")

    def _control_listen_thread(self):
        """Kontrol mesajlarını (ping) dinleyen thread."""
        while self.listening:
            try:
                data, addr = self.control_sock.recvfrom(1024)
                if data.startswith(b"PING"):
                    # Gelen ping mesajını hemen pong olarak geri gönder
                    self.control_sock.sendto(b"PONG" + data[4:], addr)
            except Exception as e:
                if self.listening:
                    print(f"Kontrol dinleme hatası: {e}")
                break

    def start_listening(self):
        """Dinlemeyi başlatır."""
        if self.listening:
            print("Zaten dinleniyor.")
            return False

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.control_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.sock.bind(("0.0.0.0", self.port))
            self.control_sock.bind(("0.0.0.0", self.control_port))
        except OSError as e:
            print(f"‼️ Port {self.port} veya {self.control_port} zaten kullanılıyor: {e}")
            return False
            
        self.sock.setblocking(False)
        
        self.listening = True
        
        self.thread = threading.Thread(target=self._listen_thread)
        self.thread.daemon = True
        self.thread.start()

        self.control_thread = threading.Thread(target=self._control_listen_thread)
        self.control_thread.daemon = True
        self.control_thread.start()

        print(f"🎧 Dinleme başladı: Port {self.port}, Kontrol Portu {self.control_port}")
        return True

    def stop_listening(self):
        """Dinlemeyi durdurur."""
        if not self.listening:
            print("Dinleme zaten durdurulmuş.")
            return

        self.listening = False
        if self.sock:
            self.sock.close()
        if self.control_sock:
            self.control_sock.close()

        if self.thread:
            self.thread.join(timeout=1)
        if self.control_thread:
            self.control_thread.join(timeout=1)
        
        self.thread = None
        self.control_thread = None
        self.sock = None
        self.control_sock = None