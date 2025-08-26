# GPT-OSS Chat Demo

This example provides a minimal chat application that talks to a locally running GPT-OSS model via a Flask backend and a React frontend built with Vite.

## Prerequisites
- [Ollama](https://ollama.com/) installed
- Pull the model:
  ```bash
  ollama pull gpt-oss:20b
  ```

## Backend (Flask)
1. Install dependencies and start the server:
   ```bash
   cd backend
   pip install -r requirements.txt
   python app.py
   ```
   The backend listens on `http://localhost:5000` and forwards requests to `http://localhost:11434`.

## Frontend (React + Vite)
1. Install dependencies and run the dev server:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   The app will be available at `http://localhost:5173` and will call the backend for responses.
