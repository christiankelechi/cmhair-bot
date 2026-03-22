from dotenv import load_dotenv
load_dotenv()
import asyncio
import api
import httpx
from config import ADMIN_EMAIL, ADMIN_PASSWORD

async def test():
    try:
        # Use exact admin email
        res = await api.login_user(ADMIN_EMAIL, ADMIN_PASSWORD)
        token = res["token"]
        print("Logged in. Token:", token[:10])
    except Exception as e:
        print("Login failed:", e)
        return
        
    gif_bytes = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
    try:
        url = await api.upload_image(gif_bytes, token, "test.gif")
        print("Uploaded URL:", url)
    except Exception as e:
        print("Upload Error:", e)

if __name__ == "__main__":
    asyncio.run(test())
