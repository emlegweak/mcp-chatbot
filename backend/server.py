from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio
from chatbot_setup import create_chat_session

# initialize fastAPI app instance
app = FastAPI()

# CORS configuration - allow cross-origin requests from any frontend client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# single ChatSession instance used across all requests
chat_session = create_chat_session()


@app.on_event("startup")
async def startup_event():
    """
    Called once when the FastAPI app starts up. 
    Initializes all MCP servers and prepares the chat session with system context.
    """
    await chat_session.initialize()


@app.on_event("shutdown")
async def shutdown_event():
    """
    Called when the FastAPI app shuts down. 
    Ensures all server subprocesses and resources are cleaned up.
    """
    await chat_session.cleanup_servers()


@app.post("/chat")
async def chat(request: Request):
    """
    POST endpoint for interacting with the chatbot. 
    Expects a JSON payload like {"message": "Hi!"}
    Streams the assistant's reply word by word using a StreamingResponse
    """
    if not chat_session.system_message:
        logging.warning("ChatSession not initialized before first request")

    body = await request.json()
    user_input = body.get("message", "")

    async def streamer():
        """
        Async generator that returns the assistant's response word by word.
        Simulates real-time streaming behavior. 
        """
        # send user's full message to LLM + tool execution
        async for message in chat_session.chat_once(user_input):
            for word in message.split():
                yield word + " "
                await asyncio.sleep(0.05)  # simulate streaming response
    # generator function passed to StreamingResponse
    # client receives output word by word as soon as the first one is available
    return StreamingResponse(streamer(), media_type="text/plain")
