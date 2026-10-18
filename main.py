import os
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

EMAIL = "22f3002628@ds.study.iitm.ac.in"
QUESTION_ID = "q-ledger-agent-server"
BASE_DATA_URL = f"https://exam.sanand.workers.dev/questionData?email={EMAIL}&quizSign=&questionId={QUESTION_ID}&path="

client = OpenAI(
    base_url="https://aiproxy.sanand.workers.dev/openai/v1",
    api_key=os.environ.get("AIPROXY_TOKEN")
)

class QueryRequest(BaseModel):
    question: str

async def fetch_ledger_data(path: str = ""):
    async with httpx.AsyncClient() as client_http:
        response = await client_http.get(BASE_DATA_URL + path)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch ledger data.")
        return response.json()

@app.post("/")
async def answer_question(body: QueryRequest):
    try:
        ledger_data = await fetch_ledger_data()
        
        prompt = f"""
You are a precise data analyst assistant for Acme Appliances.
Here is the order ledger data:
{ledger_data}

Answer the user's question accurately.
Rules:
- Numbers can be plain numbers.
- Money must be in USD, correct to the cent (e.g., 1500.50).
- Product names must match the API's spelling exactly.
- Reply with the direct answer or a JSON response containing the answer.

Question: {body.question}
"""
        
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        
        answer_text = completion.choices[0].message.content.strip()
        return {"answer": answer_text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
