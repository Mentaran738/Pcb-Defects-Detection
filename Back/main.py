
import asyncio
from Recs.ImageProc import process_images
from Recs.database import init_db

async def main():
    await init_db()
    await process_images()

if __name__ == "__main__":
    asyncio.run(main())