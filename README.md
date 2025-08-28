# Book Recommendation Bot

![Book Recommendation Bot Screenshot](assets/img.png)

A personalized book recommendation application that provides tailored book suggestions based on user preferences and favorite genres.  
Powered by **Flask**, **ChromaDB**, and **OpenAI** for contextual recommendations.

---

## Features

- **Personalized Recommendations** — Enter your reading preferences and receive tailored suggestions  
- **Interactive Web Interface** — Built with Flask, HTML, CSS (Tailwind), and JavaScript  
- **Function Calling** — OpenAI model selects books and calls backend functions to return complete summaries  
- **Exact Title Bypass** — If you enter an exact title from the database, the app instantly returns its description (no API call needed)  
- **Scalable Vector Database** — ChromaDB manages embeddings and efficient semantic search  

---

## Installation

### Prerequisites
- Python 3.9 or newer  
- pip (Python package manager)

### Install Dependencies
```bash
pip install -r requirements.txt

Dataset – `books.csv`

The book dataset is too large to include in this repository directly. To run the project, please download it manually:

1. Visit the ["Books Dataset" on Kaggle by Elvin Rustam](https://www.kaggle.com/datasets/elvinrustam/books-dataset).  
2. Download the CSV version of the dataset.  
3. Decompress and place the file into the `data/` directory as `books.csv`.

Environment Variables
Create a .env file in the project root and add:

env
Copy code
OPENAI_API_KEY=your_openai_api_key
Build the Book Index
Before running the app, generate the ChromaDB index:


Copy code:
python main.py


Run the Application

Copy code
python app.py


Usage
Open the application in your browser

Enter in the search field:

A free-form prompt (e.g., recommend a book about friendship and magic)

Or an exact title from the database (e.g., Remaking the World: Adventures in Engineering)

Press the Search Book button or use Ctrl+Enter

Receive a recommendation with a complete description

View, copy, or save previous searches



---
