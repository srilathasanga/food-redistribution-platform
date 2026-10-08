from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


@app.get("/")
def home():
    return {
        "message": "Food Redistribution API is running!"
    }


class Restaurant(BaseModel):
    name: str
    phone: str
    address: str


@app.post("/restaurants")
def create_restaurant(restaurant: Restaurant):
    return {
        "message": "Restaurant created successfully",
        "restaurant": restaurant
    }