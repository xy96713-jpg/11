
import os
import json
import base64
import sqlite3
import shutil
from datetime import datetime
import win32crypt # pip install pywin32
from Crypto.Cipher import AES # pip install pycryptodome

def get_chrome_datetime(chromedate):
    """Return a `datetime.datetime` object from a chrome format datetime
    Since `chromedate` is formatted as the number of microseconds since January, 1601"""
    if chromedate != 86400000000 and chromedate:
        try:
            return datetime(1601, 1, 1) + datetime.timedelta(microseconds=chromedate)
        except Exception as e:
            # handle very large dates that might cause overflow
            return datetime.now()
    else:
        return ""

def get_encryption_key(browser_path):
    local_state_path = os.path.join(browser_path, "Local State")
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = f.read()
        local_state = json.loads(local_state)

    # decode the encryption key from Base64
    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    # remove DPAPI str
    key = key[5:]
    # return decrypted key that was originally encrypted
    # using a session key derived from current user's logon credentials
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

def decrypt_data(data, key):
    try:
        # get the initialization vector
        iv = data[3:15]
        data = data[15:]
        # generate cipher
        cipher = AES.new(key, AES.MODE_GCM, iv)
        # decrypt password
        return cipher.decrypt(data)[:-16].decode()
    except:
        try:
            return str(win32crypt.CryptUnprotectData(data, None, None, None, 0)[1])
        except:
            # not supported
            return ""

def extract_cookies(browser_name="Chrome"):
    if browser_name == "Chrome":
        user_data_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data")
    elif browser_name == "Edge":
        user_data_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Microsoft", "Edge", "User Data")
    else:
        print("Unsupported browser")
        return None

    # check if browser data exists
    if not os.path.exists(user_data_path):
        print(f"Browser data path not found: {user_data_path}")
        return None

    key = get_encryption_key(user_data_path)
    
    # copy the file to a temp location since the database is locked when browser is open
    db_path = os.path.join(user_data_path, "Default", "Network", "Cookies")
    if not os.path.exists(db_path):
         # Edge might store it elsewhere or under a different profile
         db_path = os.path.join(user_data_path, "Default", "Cookies")

    filename = "Cookies.db"
    
    # Check if the file exists before copying
    if not os.path.exists(db_path):
        # search recursively for 'Cookies' file
        print(f"Searching for Cookies file in {user_data_path}...")
        for root, dirs, files in os.walk(user_data_path):
            if "Cookies" in files:
                db_path = os.path.join(root, "Cookies")
                break
    
    if not os.path.exists(db_path):
        print("Could not find Cookies database.")
        return None

    try:
        shutil.copyfile(db_path, filename)
    except PermissionError:
        print("❌ 错误：无法读取 Cookies 数据库。请关闭 Chrome/Edge 浏览器后再试。")
        return None
    except Exception as e:
        print(f"❌ 复制文件失败: {e}")
        return None
    
    # connect to the database
    db = sqlite3.connect(filename)
    cursor = db.cursor()
    
    # get the cookies
    try:
        cursor.execute("SELECT host_key, name, value, creation_utc, last_access_utc, expires_utc, encrypted_value FROM cookies")
    except sqlite3.OperationalError:
         # Table might be different in very new versions
         print("Error reading cookies table.")
         return None

    cookies_netscape = ""
    
    for host_key, name, value, creation_utc, last_access_utc, expires_utc, encrypted_value in cursor.fetchall():
        if not value:
            decrypted_value = decrypt_data(encrypted_value, key)
        else:
            decrypted_value = value
            
        # Format as Netscape HTTP Cookie File
        # domain  flag  path  secure  expiration  name  value
        flag = "TRUE" if host_key.startswith('.') else "FALSE"
        path = "/"
        secure = "TRUE" # Approximating, need actual secure flag if vital
        
        # expires_utc is microseconds since 1601, netscape wants unix timestamp
        # rough conversion: (expires_utc / 1000000) - 11644473600
        # but 0 means session cookie (expires at 0)
        
        expire_time = 0
        if expires_utc != 0:
            expire_time = int((expires_utc / 1000000) - 11644473600)
            if expire_time < 0: expire_time = 0

        line = f"{host_key}\t{flag}\t{path}\t{secure}\t{expire_time}\t{name}\t{decrypted_value}\n"
        cookies_netscape += line

    db.close()
    try:
        os.remove(filename)
    except:
        pass
        
    return cookies_netscape

if __name__ == "__main__":
    
    # Attempt to extract from Chrome first, then Edge
    cookies = extract_cookies("Chrome")
    if not cookies or len(cookies) < 100: # heuristic check
         print("Chrome cookies empty or failed, trying Edge...")
         cookies = extract_cookies("Edge")
    
    if cookies:
        # Save to a fixed path within the skill scripts directory for easy access by other scripts
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "youtube_cookies.txt")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write("# This file is generated by a script.\n\n")
            f.write(cookies)
        print(f"Successfully exported cookies to {output_path}")
    else:
        print("Failed to export cookies.")
