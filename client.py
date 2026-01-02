import socket
import threading
import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox, filedialog, Listbox
from security_utils import des_encrypt, des_decrypt, lsb_embed

HOST = '127.0.0.1' 
PORT = 12345

# Kullanıcı Anahtarları (Client tarafında bilindiği varsayılıyor)
# Gerçek projede bu anahtarlar veritabanından veya güvenli bir şekilde alınır.
KEYS = {
    "melisa": "12345678",
    "ahmet":  "87654321",
    "mehmet": "abcdefgh"
}

class ChatClient:
    def __init__(self, master):
        self.master = master
        master.title("Güvenli Sohbet Projesi (Final)")
        master.geometry("650x550")
        
        # Giriş
        self.username = simpledialog.askstring("Giriş", "Kullanıcı Adı (melisa, ahmet, mehmet):")
        if not self.username: master.destroy(); return
        
        # Kendi anahtarını belirle
        self.key = KEYS.get(self.username, "12345678")
        
        # --- ARAYÜZ (GUI) ---
        # Sol Panel: Kullanıcı Listesi
        self.left_frame = tk.Frame(master, width=180, bg="#dddddd")
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        tk.Label(self.left_frame, text="Aktif Kullanıcılar", bg="#dddddd", font=("Arial", 10, "bold")).pack(pady=5)
        
        self.user_listbox = Listbox(self.left_frame, height=20)
        self.user_listbox.pack(fill=tk.BOTH, expand=True, padx=5)
        
        self.refresh_btn = tk.Button(self.left_frame, text="Listeyi Yenile 🔄", command=self.request_user_list)
        self.refresh_btn.pack(pady=10)

        # Sağ Panel: Mesajlaşma
        self.right_frame = tk.Frame(master)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.chat_area = scrolledtext.ScrolledText(self.right_frame, state='disabled', height=20)
        self.chat_area.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Mesaj Giriş Alanı
        tk.Label(self.right_frame, text="Mesajınız (Veya 'kullanici:mesaj' formatı):", anchor="w").pack(fill=tk.X)
        self.msg_entry = tk.Entry(self.right_frame, font=("Arial", 11))
        self.msg_entry.pack(fill=tk.X, pady=5)
        self.msg_entry.bind("<Return>", lambda event: self.send_message()) # Enter tuşuyla gönder
        
        # Butonlar
        self.btn_frame = tk.Frame(self.right_frame)
        self.btn_frame.pack(fill=tk.X)
        
        self.send_btn = tk.Button(self.btn_frame, text="GÖNDER ➤", bg="#4CAF50", fg="white", command=self.send_message)
        self.send_btn.pack(side=tk.LEFT, padx=5)

        self.stego_btn = tk.Button(self.btn_frame, text="Resme Parola Gizle (LSB)", command=self.create_stego_image)
        self.stego_btn.pack(side=tk.RIGHT, padx=5)
        
        # Sunucuya Bağlan
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, PORT))
            self.sock.send(self.username.encode('utf-8'))
            
            self.update_chat(f"Hoşgeldin {self.username}! Listeyi yenilemek için butona bas.")
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Hata", f"Sunucuya bağlanılamadı: {e}")
            master.destroy()

    def request_user_list(self):
        """Sunucudan kullanıcı listesini ister (LIST komutu şifreli gider)"""
        try:
            encrypted_cmd = des_encrypt("LIST", self.key)
            self.sock.send(f"SERVER:{encrypted_cmd}".encode('utf-8'))
        except:
            pass

    def create_stego_image(self):
        """Kayıt aşaması için LSB fonksiyonu"""
        file_path = filedialog.askopenfilename(title="Resim Seç (PNG)", filetypes=[("PNG Files", "*.png")])
        if file_path:
            parola = simpledialog.askstring("LSB", "Gizlenecek Parola:")
            if parola:
                save_path = filedialog.asksaveasfilename(defaultextension=".png")
                if save_path:
                    lsb_embed(file_path, parola, save_path)
                    messagebox.showinfo("Başarılı", "Parola resme başarıyla gizlendi!")

    def send_message(self):
        """
        GÜNCELLENDİ: Hem listeden seçimle hem de manuel (ahmet:mesaj) 
        gönderimi destekler (Offline mesajlaşma için gerekli).
        """
        msg = self.msg_entry.get()
        if not msg: return
        
        target_user = None
        message_content = msg

        # 1. YÖNTEM: Manuel Giriş (Örn: ahmet:selam) -> Offline gönderim için ideal
        if ":" in msg:
            parts = msg.split(":", 1)
            possible_user = parts[0].strip()
            # Eğer ilk kısım geçerli bir kullanıcı ise bunu hedef yap
            if possible_user in KEYS:
                target_user = possible_user
                message_content = parts[1].strip()

        # 2. YÖNTEM: Listeden Seçim -> Online gönderim için ideal
        if not target_user:
            try:
                selection = self.user_listbox.curselection()
                if selection:
                    target_user = self.user_listbox.get(selection[0])
            except:
                pass

        # Hedef hala yoksa uyar
        if not target_user:
            messagebox.showwarning("Uyarı", "Lütfen bir kullanıcı seçin veya 'isim:mesaj' formatında yazın!")
            return

        if target_user == self.username:
            messagebox.showwarning("Uyarı", "Kendine mesaj atamazsın.")
            return

        # Req: Mesajı DES ile şifrele
        encrypted = des_encrypt(message_content, self.key)
        final_packet = f"{target_user}:{encrypted}"
        
        try:
            self.sock.send(final_packet.encode('utf-8'))
            self.update_chat(f"Ben -> {target_user}: {message_content}")
            self.msg_entry.delete(0, tk.END)
        except Exception as e:
            self.update_chat(f"Hata: {e}")

    def receive_messages(self):
        """Gelen mesajları dinler ve işler"""
        while True:
            try:
                raw_msg = self.sock.recv(1024).decode('utf-8')
                if not raw_msg: break
                
                # 1. Liste Güncellemesi
                if raw_msg.startswith("AKTIF_KULLANICILAR:"):
                    users_str = raw_msg.split(":")[1]
                    users = users_str.split(",")
                    self.user_listbox.delete(0, tk.END)
                    for user in users:
                        if user: self.user_listbox.insert(tk.END, user)
                    continue

                # 2. Sistem Mesajları (Şifresiz göster)
                if any(x in raw_msg for x in ["---", "HATA", "SERVER"]):
                     self.update_chat(raw_msg)
                
                # 3. Şifreli Kullanıcı Mesajı
                else:
                    try:
                        decrypted = des_decrypt(raw_msg, self.key)
                        if "Şifre Çözme Hatası" in decrypted or "Hata" in decrypted:
                             self.update_chat(f"Sistem: {raw_msg}")
                        else:
                             self.update_chat(f"Gelen: {decrypted}")
                    except:
                        self.update_chat(f"Mesaj: {raw_msg}")

            except Exception as e:
                print(f"Bağlantı koptu: {e}")
                break

    def update_chat(self, msg):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, msg + '\n')
        self.chat_area.yview(tk.END)
        self.chat_area.config(state='disabled')

root = tk.Tk()
client = ChatClient(root)
root.mainloop()