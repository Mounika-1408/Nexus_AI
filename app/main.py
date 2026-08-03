from fastapi import FastAPI

app = FastAPI(
    title="NexusAI API",
    description="Backend API for NexusAI - Intelligent Enterprise Data Platform",
    version="1.0.0"
)

@app.get("/")
def home():
    return {
        "message": "Welcome to NexusAI 🚀"
    }