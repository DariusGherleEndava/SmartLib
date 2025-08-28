from dotenv import load_dotenv
import langchain_community.vectorstores
from langchain_openai import OpenAIEmbeddings
import os
import csv
import re

# Load env
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
print(f"OpenAI API Key present: {bool(openai_api_key)}")
if not openai_api_key:
    raise ValueError("Please set the OPENAI_API_KEY environment variable")

# Embeddings + Chroma persist dir
embeddings = OpenAIEmbeddings(api_key=openai_api_key, model="text-embedding-3-small")
persist_dir = os.getenv("CHROMA_DB_DIR", "chromadb_data")
collection_name = "books_index"

AUTHOR_PREFIX = re.compile(r"^\s*By\s+", flags=re.IGNORECASE)

def load_documents_from_csv(file_path: str):
    texts, metas = [], []
    with open(file_path, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            title = (row.get("Title") or "").strip()
            authors_raw = (row.get("Authors") or "").strip()
            authors = AUTHOR_PREFIX.sub("", authors_raw)
            desc = (row.get("Description") or "").strip()
            category = (row.get("Category") or "").strip()
            publisher = (row.get("Publisher") or "").strip()
            pub_date = (row.get("Publish Date") or "").strip()
            price = (row.get("Price") or "").strip()

            if not title or not desc:
                continue

            content = (
                f"Title: {title}\n"
                f"Authors: {authors}\n"
                f"Category: {category}\n"
                f"Publisher: {publisher}\n"
                f"Publish Date: {pub_date}\n"
                f"Description: {desc}"
            )

            texts.append(content)
            metas.append({
                "title": title,
                "authors": authors,
                "category": category,
                "publisher": publisher,
                "publish_date": pub_date,
                "price": price,
                "row_id": i
            })
    return texts, metas

# Load book data
texts, metas = load_documents_from_csv("data/books.csv")

# Create / overwrite a Chroma collection with our texts
vectorstore = langchain_community.vectorstores.Chroma.from_texts(
    texts=texts,
    metadatas=metas,
    embedding=embeddings,
    collection_name=collection_name,
    persist_directory=persist_dir,
)

vectorstore.persist()
print(f"Book data indexed successfully into Chroma at: {persist_dir} (collection='{collection_name}')")
