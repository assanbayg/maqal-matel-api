# Maqal-matel API 🇰🇿🛖

This is the public API for Kazakh proverbs aka maqal-matels, built with FastAPI. It provides endpoints for browsing, searching, and filtering proverbs by topic.

📚 Data source: [Bilim All](https://bilim-all.kz)  
🛠️ Built with: FastAPI + SQLite + Pydantic  
🎯 Purpose: Make Kazakh cultural knowledge accessible via an easy-to-use API.

While there are many online resources for learning Kazakh proverbs, I wanted to use my own API for future projects. 

## ⚙️ Running Locally

```bash
git clone https://github.com/assanbayg/maqal-matel-api.git
cd maqal-matel-api
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```
