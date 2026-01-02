from PIL import Image
from Crypto.Cipher import DES
import base64
import os

# --- LSB (RESİM İÇİNE GİZLEME VE OKUMA) ---
def lsb_embed(image_path, secret_text, output_path):
    try:
        img = Image.open(image_path)
        img = img.convert("RGB")
        pixels = img.load()
        
        secret_text += "#####" # Bitiş işareti
        # Türkçe karakterler için encode işlemi
        binary_secret = ''.join(format(byte, '08b') for byte in secret_text.encode('utf-8'))
        data_len = len(binary_secret)
        
        width, height = img.size
        idx = 0
        
        for y in range(height):
            for x in range(width):
                if idx < data_len:
                    r, g, b = pixels[x, y]
                    bit = int(binary_secret[idx])
                    r = (r & ~1) | bit
                    pixels[x, y] = (r, g, b)
                    idx += 1
                else:
                    break
        img.save(output_path)
        return True
    except Exception as e:
        print(f"LSB Embed Hatası: {e}")
        return False

def lsb_extract(image_path):
    try:
        img = Image.open(image_path)
        img = img.convert("RGB")
        pixels = img.load()
        
        width, height = img.size
        binary_data = ""
        
        # Büyük resimlerde donmayı engellemek için sınır koyabiliriz
        # ama şimdilik tüm piksellere bakalım
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                binary_data += str(r & 1)

        # Binary veriyi byte'lara çevir
        all_bytes = bytearray()
        for i in range(0, len(binary_data), 8):
            byte_str = binary_data[i:i+8]
            if len(byte_str) < 8: break
            all_bytes.append(int(byte_str, 2))
            
            # Performans için: Her karakterde bitiş kontrolü yap
            # (utf-8 decode hatası almamak için try-except)
            try:
                current_text = all_bytes.decode('utf-8')
                if current_text.endswith("#####"):
                    return current_text[:-5]
            except:
                continue # Henüz tam karakter oluşmadıysa devam et
                
        return ""
    except Exception as e:
        return ""

# --- DES ŞİFRELEME (GÜNCELLENMİŞ VERSİYON) ---
def pad(text_bytes):
    # Byte olarak padding yapalım (UTF-8 uyumlu)
    while len(text_bytes) % 8 != 0:
        text_bytes += b' '
    return text_bytes

def des_encrypt(text, key):
    try:
        des = DES.new(key.encode('utf-8'), DES.MODE_ECB)
        # Önce metni byte'a çevir, SONRA padding yap
        raw_data = text.encode('utf-8')
        padded_data = pad(raw_data)
        encrypted_text = des.encrypt(padded_data)
        return base64.b64encode(encrypted_text).decode('utf-8')
    except Exception as e:
        print(f"Şifreleme Hatası: {e}")
        return ""

def des_decrypt(encrypted_text_base64, key):
    try:
        # Eğer gelen veri zaten şifreli değilse (HATA mesajı vb.) hata fırlatır
        # Biz de bunu yakalarız.
        des = DES.new(key.encode('utf-8'), DES.MODE_ECB)
        encrypted_bytes = base64.b64decode(encrypted_text_base64)
        decrypted_text = des.decrypt(encrypted_bytes).decode('utf-8')
        return decrypted_text.strip()
    except Exception as e:
        # Bu hata mesajını döndürmek yerine ham metni döndürelim mi?
        # Hayır, kullanıcı hata olduğunu bilsin.
        return f"Şifre Çözme Hatası: {e}"