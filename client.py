import socket
import threading
import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox, filedialog
from security_utils import des_encrypt, des_decrypt, lsb_embed

HOST = '127.0.0.1' # Kendi kendine deneyeceksen localhost
PORT = 12345

# Kullanıcının kendi anahtarı (Normalde sunucudan güvenli alınır veya bilinir)
MY_KEY = "12345678" # Varsayılan olarak 'melisa' anahtarı

class ChatClient:
    def __init__(self, master):
        self.master = master
        master.title("Güvenli Sohbet (DES + LSB)")
        
        self.username = simpledialog.askstring("Giriş", "Kullanıcı Adı (melisa, ahmet, mehmet):")
        if not self.username: master.destroy(); return
        
        # Anahtar seçimi (Basitlik için hardcode ettik, kullanıcıya göre değişmeli)
        if self.username == "ahmet": self.key = "87654321"
        elif self.username == "mehmet": self.key = "abcdefgh"
        else: self.key = "12345678" # melisa
        
        # GUI Elemanları
        self.chat_area = scrolledtext.ScrolledText(master, state='disabled')
        self.chat_area.pack(padx=10, pady=10)
        
        self.msg_entry = tk.Entry(master, width=50)
        self.msg_entry.pack(padx=10, pady=5)
        
        self.send_btn = tk.Button(master, text="Gönder", command=self.send_message)
        self.send_btn.pack(pady=5)

        self.stego_btn = tk.Button(master, text="Parolayı Resme Gizle (LSB)", command=self.create_stego_image)
        self.stego_btn.pack(pady=5)
        
        # Sunucuya Bağlan
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, PORT))
            self.sock.send(self.username.encode('utf-8'))
            
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Hata", f"Sunucuya bağlanılamadı: {e}")
            master.destroy()

    def create_stego_image(self):
        # Req 3: Parolayı görüntü içine gizleme
        file_path = filedialog.askopenfilename(title="Resim Seç (PNG)", filetypes=[("PNG Files", "*.png")])
        if file_path:
            parola = simpledialog.askstring("LSB", "Gizlenecek Parola:")
            if parola:
                save_path = filedialog.asksaveasfilename(defaultextension=".png")
                if save_path:
                    lsb_embed(file_path, parola, save_path)
                    messagebox.showinfo("Başarılı", "Parola resme gizlendi!")

    def send_message(self):
        msg = self.msg_entry.get()
        if not msg: return
        
        # Format: "ALICI:MESAJ"
        if ":" in msg:
            target, text = msg.split(":", 1)
            # Req 8: Mesajı DES ile şifrele
            encrypted = des_encrypt(text, self.key)
            final_packet = f"{target}:{encrypted}"
            self.sock.send(final_packet.encode('utf-8'))
            self.update_chat(f"Ben -> {target}: {text}")
            self.msg_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Format", "Mesajı şu formatta yazın: ALICI:MESAJ\nÖrn: ahmet:merhaba")

    def receive_messages(self):
        while True:
            try:
                encrypted_msg = self.sock.recv(1024).decode('utf-8')
                if not encrypted_msg: break
                
                # Şifreli mi yoksa düz metin (sistem mesajı) mi?
                # Basit bir kontrol: İçinde ':' yoksa veya sunucu mesajıysa
                if "---" in encrypted_msg or "AKTIF_KULLANICILAR" in encrypted_msg:
                     self.update_chat(encrypted_msg)
                else:
                    # Gelen şifreli mesajı çöz (Req 10-11 mantığı)
                    # Gelen format normalde şöyledir -> DES_SIFRELI_DATA
                    # Ancak basitlik için sunucudan plain text simülasyonu da gelebilir.
                    # Biz sunucunun tekrar şifrelediğini varsayıyoruz.
                    try:
                        decrypted = des_decrypt(encrypted_msg, self.key)
                        self.update_chat(f"Gelen: {decrypted}")
                    except:
                        self.update_chat(f"Sistem: {encrypted_msg}")
            except:
                break

    def update_chat(self, msg):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, msg + '\n')
        self.chat_area.yview(tk.END)
        self.chat_area.config(state='disabled')

root = tk.Tk()
client = ChatClient(root)
root.mainloop()