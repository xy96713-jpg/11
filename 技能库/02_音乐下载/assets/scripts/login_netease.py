import time
import qrcode
import os
from pyncm import apis, GetCurrentSession, DumpSessionAsString
import sys

def login_with_qrcode():
    print("Initializing QR Code Login...")
    
    # 1. Get QR Code Key
    # uuid = apis.login.GetCurrentLoginStatus()['account']['anonimousUser'] # Preliminary check removed

    # Pyncm actual login flow
    # Based on pyncm documentation/source behavior:
    # 1. Get Key
    key = apis.login.LoginQrcodeUnikey()['unikey']
    # 2. Get QR Content
    qr_url = f"https://music.163.com/login?codekey={key}"
    
    # 3. Save QR Code image
    qr = qrcode.QRCode()
    qr.add_data(qr_url)
    img = qr.make_image()
    img_path = os.path.join(os.path.dirname(__file__), 'qrcode_login.png')
    img.save(img_path)
    print(f"\nQR Code saved to: {img_path}")
    
    # 4. Check Status Loop
    current_stat = 0
    while True:
        status = apis.login.LoginQrcodeCheck(key)
        code = status['code']
        # 800: Expired, 801: Waiting, 802: Scanned/Confirming, 803: Success
        
        if code == 800:
            print("QR Code expired. Restart script.")
            break
        elif code == 801:
            pass # Waiting
        elif code == 802:
            print("Scanned! Please confirm on your phone.", end='\r')
        elif code == 803:
            print("\nLogin Successful!")
            # Explicitly login with the returned cookie to populate session
            cookie = status.get('cookie')
            if cookie:
                print("Applying cookies...")
                apis.login.LoginViaCookie(cookie)
            
            # Save Session
            with open('netease_session.ncm', 'w') as f:
                f.write(DumpSessionAsString(GetCurrentSession()))
            print("Session saved to 'netease_session.ncm'")
            break
            
        time.sleep(2)

if __name__ == "__main__":
    login_with_qrcode()
