import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId
from database import get_db
import motor.motor_asyncio

app = FastAPI()

db = get_db()

class ProductCreate(BaseModel):
    name: str
    size: str
    price: float
    description: Optional[str] = None

class ProductOut(ProductCreate):
    id: str = Field(..., alias="_id")

class OrderCreate(BaseModel):
    user_id: str
    product_ids: List[str]
    total: float

class OrderOut(OrderCreate):
    id: str = Field(..., alias="_id")

# Helper to convert ObjectId
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid objectid')
        return str(v)


@app.post("/products", status_code=201)
async def create_product(product: ProductCreate):
    prod = product.dict()
    result = await db.products.insert_one(prod)
    prod["_id"] = str(result.inserted_id)
    return prod

@app.get("/products", status_code=200)
async def list_products(
    name: Optional[str] = Query(None),
    size: Optional[str] = Query(None),
    limit: int = Query(10),
    offset: int = Query(0)
):
    query = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    if size:
        query["size"] = size
    cursor = db.products.find(query).skip(offset).limit(limit)
    products = []
    async for prod in cursor:
        prod["_id"] = str(prod["_id"])
        products.append(prod)
    return products

@app.post("/orders", status_code=201)
async def create_order(order: OrderCreate):
    ord = order.dict()
    result = await db.orders.insert_one(ord)
    ord["_id"] = str(result.inserted_id)
    return ord

@app.get("/orders/{user_id}", status_code=200)
async def list_orders(
    user_id: str = Path(...),
    limit: int = Query(10),
    offset: int = Query(0)
):
    cursor = db.orders.find({"user_id": user_id}).skip(offset).limit(limit)
    orders = []
    async for ord in cursor:
        ord["_id"] = str(ord["_id"])
        orders.append(ord)
    return orders