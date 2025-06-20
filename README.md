# AI Project

This project consists of two main components:
- Fast API for Backend
- React for the frontend

## Prerequisites

Before running the project, ensure you have the following installed:
- Docker & Docker Compose
- Node.js (v16 or higher)
- Python: > 3.8, < 3.13
- pip
- npm

## Project Structure

project/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── ...
├── frontend/
│   ├── package.json
│   ├── src/
│   └── ...


## Access faiss_TF_index.bin file
    Download faiss_TF_index.bin file from following drive link in backend folder
    https://drive.google.com/file/d/1whX1h2jF3_ljNDiZm02lx99ukETGUzpc/view?usp=sharing

## Backend Setup (Without Docker)

1. Navigate to the backend directory:
   cd backend

2. Create a .env file in the backend root with the necessary environment variables:

    OPENAI_API_KEY=<your_openai_api_key>
    API_TOKEN=<your_api_token>


3. Create a virtual environment:
    python3 -m venv venv
    source venv/bin/activate


4. Install dependencies:
    pip install -r requirements.txt


5. Run the Fast server:
    uvicorn main:app --reload
    The backend will be available at `http://localhost:8000`

## Frontend Setup (Without Docker)

1. Navigate to the frontend directory:
   cd frontend


2. Install dependencies:
   npm install


3. Start the development server:
   npm run dev

   The frontend will be available at `http://localhost:5173/`

## Docker Setup (Alternative Method)

1. Build and run the containers:
   # Backend:
   - cd backend
   - docker build -t backend-app .
   - docker run -p 8000:8000 backend-app
   The backend will be available at `http://localhost:8000`

   # Frontend:
   - cd frontend
   - docker build -t frontend-app .
   - docker run -p 8080:8080 frontend-app
   - The frontend will be available at `http://localhost:8080/`

2. To stop the applications:
   docker stop <container_id>
