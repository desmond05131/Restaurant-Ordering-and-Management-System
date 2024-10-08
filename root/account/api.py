from fastapi import FastAPI, status, Depends, HTTPException, APIRouter

account_router = APIRouter(
    prefix='/account',
    tags=['account']
)

# FastAPI app setup
app = FastAPI()
app.include_router(account_router)