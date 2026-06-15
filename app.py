import os
import json
from flask import Flask, render_template, request
from dotenv import load_dotenv
from groq import Groq
from prompts.classification_prompt import CLASSIFICATION_SYSTEM_PROMPT
from prompts.response_prompt import RESPONSE_SYSTEM_PROMPT
from rag import retrieve_context

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL_NAME = "llama-3.3-70b-versatile"

app = Flask(__name__)

def classify_ticket(subject, body):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        max_tokens=200,
        messages=[
            {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
            {"role": "user", "content": f"Subject: {subject}\nBody: {body}"}
        ]
    )
    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        text = text.strip("`").replace("json", "", 1).strip()
    return json.loads(text)

def generate_response(subject, body, classification, retrieved_docs):
    context_text = "\n\n".join(retrieved_docs)
    prompt_content = (
        f"Relevant company policy/knowledge base information:\n{context_text}\n\n"
        f"---\n\n"
        f"Ticket subject: {subject}\n"
        f"Ticket body: {body}\n"
        f"Category: {classification['category']}\n"
        f"Urgency: {classification['urgency']}\n\n"
        f"Using the policy information above where relevant, write the reply."
    )
    response = client.chat.completions.create(
        model=MODEL_NAME,
        max_tokens=300,
        messages=[
            {"role": "system", "content": RESPONSE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt_content}
        ]
    )
    return response.choices[0].message.content.strip()

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None

    if request.method == "POST":
        subject = request.form.get("subject", "").strip()
        body = request.form.get("body", "").strip()

        if not subject or not body:
            error = "Please fill in both subject and body."
        else:
            try:
                classification = classify_ticket(subject, body)
                query = f"{subject} {body}"
                retrieved_docs, sources = retrieve_context(query, n_results=2)
                reply = generate_response(subject, body, classification, retrieved_docs)

                result = {
                    "subject": subject,
                    "body": body,
                    "classification": classification,
                    "sources": sources,
                    "reply": reply
                }
            except Exception as e:
                error = f"Error processing ticket: {e}"

    return render_template("index.html", result=result, error=error)

if __name__ == "__main__":
    app.run(debug=True)