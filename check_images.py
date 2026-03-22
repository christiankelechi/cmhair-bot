import asyncio
import httpx
from datetime import datetime

async def test():
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get("http://localhost:8000/products/?limit=500")
        try:
            items = resp.json().get("items", [])
            # Sort manually by created_at desc
            items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            print(f"Total products fetched: {len(items)}")
            if items:
                print("LATEST 3 PRODUCTS:")
                for item in items[:3]:
                    print(f"Name: {item.get('name')}")
                    print(f"Created: {item.get('created_at')}")
                    print(f"Images: {item.get('images')}")
                    print("---")
        except Exception as e:
            print("Error parsing response:", e)

if __name__ == "__main__":
    asyncio.run(test())
