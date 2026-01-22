# reinforcelab-research-agent

Research Agent

## Steps to run locally:

### Backend

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="..."
export PARALLEL_API_KEY="..."
uvicorn server:app --reload --port 8000
```

### Frontend

```bash
cd frontend/reinforce-react-app
npm install
npm run dev
```
