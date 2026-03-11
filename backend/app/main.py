from fastapi import FastAPI
from app.api.routes.clients import router as clients_router

app = FastAPI()

app.include_router(clients_router)

@app.get("/")
def root():
    return {"status": "API running"}