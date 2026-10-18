import os
import httpx
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

EMAIL = "22f3002628@ds.study.iitm.ac.in"
QUESTION_ID = "q-ledger-agent-server"

client = OpenAI(
    base_url="https://aipipe.org/openai/v1",
    api_key=os.environ.get("AIPROXY_TOKEN")
)

class QueryRequest(BaseModel):
    question: str = "What is the total revenue?"

@app.api_route("/", methods=["GET", "POST"])
@app.api_route("/{path:path}", methods=["GET", "POST"])
async def handle_request(request: Request):
    try:
        query_params = dict(request.query_params)
        params = {
            "email": EMAIL,
            "questionId": QUESTION_ID,
            "path": "/",
            **query_params
        }
        
        data_url = "https://exam.sanand.workers.dev/questionData"
        async with httpx.AsyncClient() as client_http:
            response = await client_http.get(data_url, params=params)
            
            # If it's a verification GET request from the platform
            if request.method == "GET":
                if response.status_code == 200:
                    return {"status": "success", "message": "Ready"}
                raise HTTPException(status_code=response.status_code, detail="Unauthorized")
            
            # If it's a POST request with a question
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Failed to fetch ledger data: {response.text}")
            ledger_data = response.json()
        
        # Parse incoming body
        question = "Summarize revenue and orders."
        try:
            body_data = await request.json()
            question = body_data.get("question", question)
        except Exception:
            pass
        
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

Question: {question}
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
