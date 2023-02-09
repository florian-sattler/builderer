import redis.asyncio as redis
from fastapi import FastAPI


app = FastAPI(root_path="/api/")
db = redis.from_url("redis://database")


@app.post("/store")
async def save_item(item: str):
    try:
        await db.set("item", item)
        return {"success": True}
    except Exception:
        return {"success": False}


@app.get("/store")
async def read_item():
    try:
        return await db.get("item")
    except Exception:
        return None
