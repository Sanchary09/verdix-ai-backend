from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from utils import check_fake_news
from models import AnalysisResult

app = FastAPI(title="VerdiX AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NewsInput(BaseModel):
    text: str

@app.get("/")
def home():
    return {"message": "VerdiX AI Fake News Checker API is running!"}

@app.post("/analyze", response_model=AnalysisResult)
def analyze_news(news: NewsInput):
    return check_fake_news(news.text)
