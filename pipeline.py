from rag import retrieve_context
import os
import json
import pandas as pd
from dotenv import load_dotenv
from groq import Groq
from prompts.classification_prompt import CLASSIFICATION_SYSTEM_PROMPT
from prompts.response_prompt import RESPONSE_SYSTEM_PROMPT

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL_NAME = "llama-3.3-70b-versatile"

SUBJECT_COL = "subject"
BODY_COL = "body"

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
def main():
    df = pd.read_csv("tickets.csv")
    results = []

    for idx, row in df.iterrows():
        subject = str(row[SUBJECT_COL])
        body = str(row[BODY_COL])

        print(f"Processing ticket {idx}...")
        try:
            classification = classify_ticket(subject, body)

            # Retrieve relevant knowledge base chunks
            query = f"{subject} {body}"
            retrieved_docs, sources = retrieve_context(query, n_results=2)

            reply = generate_response(subject, body, classification, retrieved_docs)
        except Exception as e:
            print(f"Error on ticket {idx}: {e}")
            continue

        results.append({
            "subject": subject,
            "body": body,
            "classification": classification,
            "retrieved_sources": sources,
            "draft_reply": reply
        })

    with open("results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"Done. Processed {len(results)} tickets. Check results.json")

if __name__ == "__main__":
    main()