from fastapi import APIRouter

example = APIRouter()

@example.get("/example")
async def read_example():
    return {"message": "This is an example endpoint"}

