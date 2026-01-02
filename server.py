import socket
import threading
import os
from security_utils import des_decrypt, des_encrypt, lsb_extract

HOST = '0.0.0.0'
PORT = 12345

clients = {}  # {username: socket}
offline_messages = {}  # {username: [msg1, msg2]}

# Simülasyon Anahtarları (Kullanıcı veritabanı gibi düşünelim)
USER_KEYS = {
    "melisa": "12345678",
    "ahmet":  "87654321",
    "mehmet": "abcdefgh"
}

# Resim klasörü kontrolü
if not os.path.exists("server_images"):
    os.makedirs("server_images")

def handle_client(client_socket, addr):
    print(f"[+] Bağlantı: {addr}")
    username = None
    try:
        # 1. Giriş ve Kimlik Doğrulama
        username = client_socket.recv(1024).decode('utf-8').strip()
        
        if username not in USER_KEYS:
            client_socket.send("HATA: Kayıtsız Kullanıcı".encode('utf-8'))
            client_socket.close()
            return

        # Req 4: Server görselden parola okuma simülasyonu
        if os.path.exists(f"server_images/{username}.png"):
            extracted_pass = lsb_extract(f"server_images/{username}.png")
            print(f"[{username}] Resimden Parola Okundu: {extracted_pass}")
        
        clients[username] = client_socket
        print(f"[+] {username} sisteme giriş yaptı.")

        # Req 7: Offline mesajları ilet
        if username in offline_messages and offline_messages[username]:
            client_socket.send(f"--- OFFLINE MESAJLAR ---\n".encode('utf-8'))
            for msg in offline_messages[username]:
                client_socket.send(f"{msg}\n".encode('utf-8'))
            del offline_messages[username]
            client_socket.send("------------------------\n".encode('utf-8'))

        # 2. Mesajlaşma Döngüsü
        while True:
            encrypted_msg = client_socket.recv(1024).decode('utf-8')
            if not encrypted_msg: break
            
            # Format: HEDEF:ŞİFRELİ_MESAJ
            if ":" in encrypted_msg:
                target, cipher = encrypted_msg.split(":", 1)
                target = target.strip() # Boşluk temizliği
                
                # ADIM 1: Mesajı GÖNDERENİN anahtarıyla çöz
                sender_key = USER_KEYS[username]
                plain_text = des_decrypt(cipher, sender_key)
                print(f"[{username} -> {target}] Çözülen İçerik: {plain_text}")

                # ADIM 2: Kullanıcı Listesi İsteği mi?
                if target == "SERVER" and plain_text == "LIST":
                    active = ",".join(clients.keys())
                    client_socket.send(f"AKTIF_KULLANICILAR:{active}".encode('utf-8'))
                    continue

                # ADIM 3: Hedefe Yönlendirme
                if target in USER_KEYS:
                    # Mesajı ALICININ anahtarıyla tekrar şifrele
                    target_key = USER_KEYS[target]
                    re_encrypted = des_encrypt(f"{username}: {plain_text}", target_key)
                    
                    if target in clients:
                        try: 
                            clients[target].send(re_encrypted.encode('utf-8'))
                        except:
                            # Gönderim hatası olursa offline'a at
                            if target not in offline_messages: offline_messages[target] = []
                            offline_messages[target].append(f"{username} (Offline): {plain_text}")
                    else:
                        # Req 6: Hedef Offline ise sakla
                        if target not in offline_messages: offline_messages[target] = []
                        offline_messages[target].append(f"{username}: {plain_text}")
                        print(f"[{target}] Çevrimdışı. Mesaj saklandı.")

    except Exception as e:
        print(f"Hata ({username}): {e}")
    finally:
        if username in clients: del clients[username]
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[*] Sunucu {HOST}:{PORT} üzerinde çalışıyor...")
    while True:
        client, addr = server.accept()
        threading.Thread(target=handle_client, args=(client, addr)).start()

if __name__ == "__main__":
    start_server()