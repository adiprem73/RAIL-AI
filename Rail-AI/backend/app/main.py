from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .routers import data, planning

app = FastAPI(
    title="Rake Formation Decision Support System",
    description="API for railway rake formation planning and optimization",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data.router)
app.include_router(planning.router)

@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
async def root():
    return {
        "message": "Rake Formation DSS API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
