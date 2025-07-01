import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(title="MCP Python Orchestration")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])

@app.get("/")
async def root():
    return {"status": "online", "service": "MCP Python Orchestration", "port": 8000}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/orchestrate")
async def orchestrate(data: dict):
    return {"success": True, "result": f"Processed: {data.get('task', 'unknown')}", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
