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
        binary_secret = ''.join(format(ord(i), '08b') for i in secret_text)
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
        
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                binary_data += str(r & 1)

        all_text = ""
        for i in range(0, len(binary_data), 8):
            byte = binary_data[i:i+8]
            if len(byte) < 8: break
            char = chr(int(byte, 2))
            all_text += char
            if all_text.endswith("#####"):
                return all_text[:-5]
        return ""
    except Exception as e:
        return ""

# --- DES ŞİFRELEME ---
def pad(text):
    while len(text) % 8 != 0:
        text += ' '
    return text

def des_encrypt(text, key):
    try:
        des = DES.new(key.encode('utf-8'), DES.MODE_ECB)
        padded_text = pad(text)
        encrypted_text = des.encrypt(padded_text.encode('utf-8'))
        return base64.b64encode(encrypted_text).decode('utf-8')
    except Exception as e:
        print(f"Şifreleme Hatası: {e}")
        return ""

def des_decrypt(encrypted_text_base64, key):
    try:
        des = DES.new(key.encode('utf-8'), DES.MODE_ECB)
        encrypted_bytes = base64.b64decode(encrypted_text_base64)
        decrypted_text = des.decrypt(encrypted_bytes).decode('utf-8')
        return decrypted_text.strip()
    except Exception as e:
        return f"Hata: {e}"