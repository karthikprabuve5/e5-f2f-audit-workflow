import os
from dotenv import load_dotenv
from botocore.config import Config
from langchain_aws import ChatBedrockConverse
from utils import format_messages
from deepagents.backends.utils import create_file_data
from deepagents.backends import StateBackend, FilesystemBackend, CompositeBackend
from deepagents import create_deep_agent
import json
import logging
import asyncio
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware  # ← add this



app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["null"],          # or ["null"] to be specific to file:// origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def process_f2f(
    file: UploadFile = File(...),
    code: str = Form(...),
    description: str = Form(...)
):
    load_dotenv()

    # boto_config = Config(
    #     read_timeout=1000,        # seconds — generous headroom for long generations
    #     connect_timeout=60,
    #     retries={"max_attempts": 3, "mode": "adaptive"},  # rides out throttling
    # )

    openai_model = ChatBedrockConverse(
        model=os.getenv("MODEL_OPENAI"),
        provider="openai",
        temperature=0.0
    )

    anthropic_model = ChatBedrockConverse(
        model=os.getenv("MODEL_ANTHROPIC"),
        provider="anthropic",
        temperature=0.0
    )

    def read_prompt_from_file(file_path):
        with open(file_path, "r") as f:
            return f.read()
        

    classification_agent = create_deep_agent(
        model = anthropic_model,
        system_prompt= read_prompt_from_file("prompts/classification_agent_system_prompt.md"),
        backend=CompositeBackend(
            default= StateBackend(),
            routes={
                "/skills/": FilesystemBackend(root_dir="/home/ubuntu/projects/e5-f2f/e5-f2f-workflow-agent/skills", virtual_mode=True)
            }
        ),
        skills = ["skills"],
    )
    if not file.filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="Please upload a Markdown (.md) file.")

    file_content = (await file.read()).decode("utf-8")

    files = {"/documents/F2F.md": create_file_data(file_content)}

    classification_agent_result = classification_agent.invoke({
        "messages": [{"role": "user", "content": "split the encounters"}],
        "files": files
    })

    result = json.loads(classification_agent_result['files']["/documents/F2F_classification_results.json"]['content'])

    return JSONResponse(status_code=200, content={"classification_result": result})


# ── Logging setup ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler()]  # prints to terminal
)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
