# Smart SEO AI — Backend (SEO AI demo)

This is a FastAPI-based backend showcasing AI-powered SEO tools.  
It includes five main modules:

1. **Analyzer** – Extracts page title, meta tags, and keyword info  
2. **Scorer** – Computes SEO quality score using extracted features  
3. **Generator** – Creates optimized titles, meta, and article text  
4. **Performance Predictor** – Predicts how content might perform  
5. **Competitor Insights** – Analyzes and compares competitor pages  

---

## 🚀 How to Run (Windows / PowerShell)

1. Open PowerShell in the repo folder  
2. Create a virtual environment and install dependencies:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
   *(If no requirements.txt, run)*  
   ```powershell
   pip install fastapi uvicorn requests beautifulsoup4 scikit-learn joblib lxml textstat
   ```

3. (Optional) Add your OpenAI key for Generator:
   ```powershell
   $env:OPENAI_API_KEY="sk-yourkeyhere"
   ```

4. Run the backend:
   ```powershell
   uvicorn main:app --reload --port 8001
   ```
   Open docs at: http://127.0.0.1:8001/docs

---

## 🧪 Example API Calls (PowerShell)

**Analyze a site:**
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/analyze/" -Method POST -ContentType "application/json" -Body '{"url":"https://example.com"}'
```

**Generate content:**
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/generate/" -Method POST -ContentType "application/json" -Body '{"text":"bakery sourdough cakes","kinds":["title","meta","article"]}'
```

**Competitor analysis:**
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8001/competitor/analyze/" -Method POST -ContentType "application/json" -Body '{"urls":["https://example.com"],"fetch_text":false}'
```

---

## 📘 Notes
- Works even without OpenAI key (uses fallback demo text)
- `.gitignore` should contain `__pycache__/`, `*.pyc`, `.env`, and `scorer/model.joblib`
- Built using **FastAPI + Uvicorn**

---

### 👩‍💻 Project By
**Usha BM** – SEO AI Hackathon Project (Backend Model + API)
