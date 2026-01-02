import socket
import threading
import os
from security_utils import des_decrypt, des_encrypt, lsb_extract

HOST = '0.0.0.0'
PORT = 12345

clients = {}  # {username: socket}
offline_messages = {}  # {username: [msg1, msg2]}

# Kullanıcı Anahtarları (8 Karakter)
USER_KEYS = {
    "melisa": "12345678",
    "ahmet":  "87654321",
    "mehmet": "abcdefgh"
}

# Sunucu tarafında resim klasörü kontrolü
if not os.path.exists("server_images"):
    os.makedirs("server_images")

def handle_client(client_socket, addr):
    print(f"[+] Bağlantı: {addr}")
    username = None
    try:
        # 1. Kullanıcı Adını Al
        username = client_socket.recv(1024).decode('utf-8').strip()
        
        if username not in USER_KEYS:
            client_socket.send("HATA: Kayıtsız Kullanıcı".encode('utf-8'))
            client_socket.close()
            return

        # Req 4: Server görselden parola okuma simülasyonu
        # (Server klasöründe kullanıcının resmi varsa parolasını oradan okur)
        if os.path.exists(f"server_images/{username}.png"):
            extracted_pass = lsb_extract(f"server_images/{username}.png")
            print(f"[{username}] Resimden Parola: {extracted_pass}")
        
        clients[username] = client_socket
        print(f"[+] {username} bağlandı.")

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
            
            if ":" in encrypted_msg:
                target, cipher = encrypted_msg.split(":", 1)
                
                # Req 10: Server gönderenin anahtarıyla çözer
                sender_key = USER_KEYS[username]
                plain_text = des_decrypt(cipher, sender_key)
                print(f"[{username} -> {target}]: {plain_text}")

                if target == "SERVER" and plain_text == "LIST":
                    active = ",".join(clients.keys())
                    client_socket.send(f"SERVER:{des_encrypt('Aktif: ' + active, sender_key)}".encode('utf-8'))
                    continue

                if target in USER_KEYS:
                    # Req 11: Alıcının anahtarıyla tekrar şifrele
                    target_key = USER_KEYS[target]
                    re_encrypted = des_encrypt(f"{username}: {plain_text}", target_key)
                    
                    if target in clients:
                        try: 
                            clients[target].send(re_encrypted.encode('utf-8'))
                        except:
                            # Hata olursa offline yap
                            if target not in offline_messages: offline_messages[target] = []
                            offline_messages[target].append(f"{username}: {plain_text}")
                    else:
                        # Req 6: Offline sakla
                        if target not in offline_messages: offline_messages[target] = []
                        offline_messages[target].append(f"{username}: {plain_text}")
                        print(f"[{target}] Offline, mesaj saklandı.")

    except Exception as e:
        print(f"Hata ({username}): {e}")
    finally:
        if username in clients: del clients[username]
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[*] Sunucu {HOST}:{PORT} çalışıyor...")
    while True:
        client, addr = server.accept()
        threading.Thread(target=handle_client, args=(client, addr)).start()

if __name__ == "__main__":
    start_server()