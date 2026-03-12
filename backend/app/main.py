from fastapi import FastAPI
import app.db.base

from app.api.routes.clients import router as clients_router
from app.api.routes.products import router as products_router
from app.api.routes.stages import router as stages_router
from app.api.routes.product_stages import router as product_stages_router
from app.api.routes.orders import router as orders_router
from app.api.routes.kits import router as kits_router
from app.api.routes.production import router as production_router
from app.api.routes.roles import router as roles_router
from app.api.routes.users import router as users_router

app = FastAPI()

app.include_router(clients_router)
app.include_router(products_router)
app.include_router(stages_router)
app.include_router(product_stages_router)
app.include_router(orders_router)
app.include_router(kits_router)
app.include_router(production_router)
app.include_router(roles_router)
app.include_router(users_router)

@app.get("/")
def root():
    return {"status": "API running"}