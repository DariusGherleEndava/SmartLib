
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI
import os
import json
import re
import logging

# ---------- Flask & env ----------
app = Flask(__name__)
load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
print(f"OpenAI API Key present: {bool(openai_api_key)}")
if not openai_api_key:
    raise ValueError("Please set the OPENAI_API_KEY environment variable")

# ---------- Vector store ----------
persist_dir = os.getenv("CHROMA_DB_DIR", "chromadb_data")
collection_name = "books_index"

embeddings = OpenAIEmbeddings(api_key=openai_api_key, model="text-embedding-3-small")
vectorstore = Chroma(
    collection_name=collection_name,
    embedding_function=embeddings,
    persist_directory=persist_dir,
)

# ---------- Utils pentru matching de titlu ----------
QUOTES_RE = re.compile(r'^[\s"\']*(.*?)[\s"\']*$')

def _normalize_title(s: str) -> str:
    
    if not s:
        return ""
    s = QUOTES_RE.sub(r"\1", s.strip())
    return s.casefold()

def find_exact_title_summary(user_text: str):
    
    norm = _normalize_title(user_text)
    if not norm:
        return False, None

    # cautare semantica + verificare egalitate stricta pe titlu
    results = vectorstore.similarity_search(user_text, k=12)
    for doc in results:
        meta_title = (doc.metadata.get("title") or "")
        if _normalize_title(meta_title) == norm:
            return True, doc.page_content
    return False, None

# ---------- Function calling tool ----------
def get_summary_by_title(title: str) -> str:
    """Returneaza descrierea completa din Chroma pentru un titlu exact."""
    results = vectorstore.similarity_search(title, k=8)
    for doc in results:
        if (doc.metadata.get("title", "").lower() == title.lower()):
            return doc.page_content
    return "Nu am gasit rezumat pentru acest titlu."

tools = [{
    "type": "function",
    "function": {
        "name": "get_summary_by_title",
        "description": "Returneaza rezumatul complet pentru titlul cartii recomandate.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Titlul exact al cartii"
                }
            },
            "required": ["title"]
        }
    }
}]

# ---------- Routes ----------
@app.route("/")
def home():
    return render_template("index.html") if os.path.exists("templates/index.html") else """
    <html>
      <body>
        <h3>Book Recommendation Bot</h3>
        <form onsubmit="event.preventDefault(); fetch('/recommend', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({user_input: document.getElementById('q').value})
        }).then(r=>r.json()).then(d=>{
            document.getElementById('out').innerText = d.error ? ('Error: ' + d.error) : d.recommendation;
        }).catch(e=>{ document.getElementById('out').innerText = 'Network error: '+e; });">
          <input id="q" style="width:400px" placeholder="ex: recomanda ceva cu prietenie si magie" />
          <button>Find Books!</button>
        </form>
        <pre id="out"></pre>
      </body>
    </html>
    """

@app.route("/recommend", methods=["POST"])
def recommend():
    try:
        data = request.get_json(silent=True) or {}
        user_input = data.get("user_input")
        if not user_input or not isinstance(user_input, str):
            return jsonify({"error": "Invalid input"}), 400

        # 0) BYPASS: daca inputul este EXACT un titlu din csv, returnam direct descrierea
        is_exact, summary = find_exact_title_summary(user_input)
        if is_exact:
            return jsonify({"recommendation": summary})

        # 1) RAG: semantic search context
        emb = embeddings.embed_query(user_input)
        results = vectorstore.similarity_search_by_vector(emb, k=5)
        context = "\n\n".join([doc.page_content for doc in results])

        # 2) Initial Chat Call cu function tool (OpenAI Python v1: chat.completions)
        client = OpenAI(api_key=openai_api_key)
        sys_prompt = (
            "Esti un asistent care recomanda o carte potrivita pe baza contextului RAG.\n"
            "Contextul vine dintr-o baza de date de carti.\n"
            "Alege o singura carte si apoi APELEAZA functia get_summary_by_title cu titlul exact.\n"
            "Raspunsul final va include de ce e potrivita si rezumatul complet."
        )
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_input},
            {"role": "system", "content": "Context RAG:\n" + context},
        ]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.3,
        )

        message = response.choices[0].message

        # 3) Daca LLM apeleaza tool-ul
        if getattr(message, "tool_calls", None):
            for tool_call in message.tool_calls:
                if tool_call.function.name == "get_summary_by_title":
                    args = json.loads(tool_call.function.arguments or "{}")
                    title_arg = args.get("title", "") or ""
                    summary = get_summary_by_title(title_arg)

                    # 4) Follow-up cu rezultatul tool-ului (corect: chat.completions.create)
                    followup = client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages + [
                            message,
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": summary
                            }
                        ],
                        temperature=0.2,
                    )
                    return jsonify({"recommendation": followup.choices[0].message.content})

        # Fallback
        return jsonify({"recommendation": message.content})

    except Exception as e:
        app.logger.exception("recommend failed")
        return jsonify({"error": str(e)}), 500

# ---------- Main ----------
if __name__ == "__main__":
    # log basic config
    logging.basicConfig(level=logging.INFO)
    app.run(host="0.0.0.0", port=5000, debug=True)
