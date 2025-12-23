from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import clients, portals, settings, services, organizations
from .database import engine
from . import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:3000",  # Your frontend's URL for local development
    "http://app.datainvestigo.com",  # Replace with your actual frontend URL
    "https://app.datainvestigo.com",  # For HTTPS
    "https://login-api.datainvestigo.com",
    "*",
    "http://localhost:8081",
    "http://localhost:8080",
    "https://domain-api.datainvestigo.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clients.router, prefix="/clients", tags=["clients"])
app.include_router(portals.router, prefix="/portals", tags=["portals"])
app.include_router(settings.router, prefix="/settings", tags=["settings"])
app.include_router(services.router, prefix="/services", tags=["services"])
app.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
