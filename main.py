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
    question: str

@app.post("/")
async def answer_question(request: Request, body: QueryRequest):
    try:
        # Capture the quizSign sent dynamically by the exam grader
        quiz_sign = request.query_params.get("quizSign", "")
        
        # Construct the authorized data URL
        data_url = f"https://exam.sanand.workers.dev/questionData?email={EMAIL}&quizSign={quiz_sign}&questionId={QUESTION_ID}&path=/"
        
        async with httpx.AsyncClient() as client_http:
            response = await client_http.get(data_url)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Failed to fetch ledger data: {response.text}")
            ledger_data = response.json()
        
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
