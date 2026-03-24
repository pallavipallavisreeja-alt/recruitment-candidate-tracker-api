# Intelligent API Documentation Keeper

### (Domain: Recruitment Candidate Tracker API)

This project is a backend system built using FastAPI that manages recruitment candidates and automatically generates API documentation.

It combines a real-world API (Candidate Tracker) with an intelligent system to analyze and document APIs.

---

## 🚀 Features

### Recruitment API

* Create candidate
* Get all candidates
* Search candidates by name
* Get candidate by ID
* Update candidate details
* Delete candidate

### Intelligent Documentation (Planned / In Progress)

* Detect API routes automatically
* Extract endpoint details
* Generate API documentation
* Integrate with CI/CD pipeline

---

## 🛠 Tech Stack

* FastAPI
* SQLAlchemy
* SQLite
* Uvicorn
* Python

---

## 📂 Project Structure

```id="9rj2v9"
main.py
database.py
models.py
schemas.py
crud.py
routers/
 └── candidates.py
```

---

## ▶️ How to Run

```id="qjyfkp"
uvicorn main:app --reload
```

---

## 🌐 API Docs

Open:
http://127.0.0.1:8000/docs

---

## 🎯 Project Goal

The main goal of this project is to build an intelligent system that can:

* Automatically analyze APIs
* Generate documentation
* Reduce manual effort for developers

---

## 👩‍💻 Author

Pallavi Dudi
