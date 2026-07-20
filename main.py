# import os
# import time

# from fastapi import FastAPI, HTTPException
# from fastapi.staticfiles import StaticFiles
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import FileResponse

# from app.models import ChatRequest, ChatResponse, ResetRequest
# from app.memory.session_memory import session_memory
# from app.graph import compiled_graph
# from app.logging_config import logger

# app = FastAPI(title="DigitalSofts AI Customer Success Agent")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# METRICS = {"total_requests": 0, "total_retries": 0, "agent_usage": {}}

# FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
# if os.path.isdir(FRONTEND_DIR):
#     app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# @app.get("/")
# def serve_index() -> FileResponse:
#     return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# @app.get("/style.css")
# def serve_css() -> FileResponse:
#     return FileResponse(os.path.join(FRONTEND_DIR, "style.css"))


# @app.get("/script.js")
# def serve_js() -> FileResponse:
#     return FileResponse(os.path.join(FRONTEND_DIR, "script.js"))


# @app.post("/chat", response_model=ChatResponse)
# def chat(request: ChatRequest) -> ChatResponse:
#     if not request.message.strip():
#         raise HTTPException(status_code=400, detail="Message cannot be empty")
#     try:
#         session = session_memory.get(request.session_id)
#         session_memory.add_message(request.session_id, "user", request.message)

#         state = {
#             "session_id": request.session_id,
#             "message": request.message,
#             "profile": session.profile.model_dump(),
#             "agent": "",
#             "response": "",
#             "confidence": 0.0,
#             "retry_count": 0,
#             "retry_reason": "",
#         }
#         result = compiled_graph.invoke(state)

#         session_memory.update_profile(request.session_id, **result["profile"])
#         session_memory.add_message(request.session_id, "assistant", result["response"])

#         METRICS["total_requests"] += 1
#         METRICS["agent_usage"][result["agent"]] = METRICS["agent_usage"].get(result["agent"], 0) + 1
#         if result["retry_count"] > 0:
#             METRICS["total_retries"] += 1

#         updated_profile = session_memory.get(request.session_id).profile
#         return ChatResponse(
#             session_id=request.session_id,
#             reply=result["response"],
#             agent=result["agent"],
#             confidence=result["confidence"],
#             client_profile=updated_profile.model_dump(),
#         )
#     except HTTPException:
#         raise
#     except Exception as exc:
#         logger.error("Chat processing failed: %s", exc)
#         raise HTTPException(status_code=500, detail="Internal error processing chat request") from exc


# @app.post("/reset-session")
# def reset_session(request: ResetRequest) -> dict:
#     session_memory.reset(request.session_id)
#     logger.info("Session %s reset", request.session_id)
#     return {"status": "reset", "session_id": request.session_id}


# @app.get("/health")
# def health() -> dict:
#     return {"status": "ok", "timestamp": time.time()}


# @app.get("/metrics")
# def metrics() -> dict:
#     return {
#         "total_requests": METRICS["total_requests"],
#         "total_retries": METRICS["total_retries"],
#         "agent_usage": METRICS["agent_usage"],
#         "active_sessions": len(session_memory.all_sessions()),
#     }


import os
import time


from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse


from app.models import ChatRequest, ChatResponse, ResetRequest
from app.memory.session_memory import session_memory
from app.graph import compiled_graph
from app.logging_config import logger


app = FastAPI(title="DigitalSofts AI Customer Success Agent")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


METRICS = {"total_requests": 0, "total_retries": 0, "agent_usage": {}}


FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")




@app.get("/")
def serve_index() -> FileResponse:
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))




@app.get("/style.css")
def serve_css() -> FileResponse:
    return FileResponse(os.path.join(FRONTEND_DIR, "style.css"))




@app.get("/script.js")
def serve_js() -> FileResponse:
    return FileResponse(os.path.join(FRONTEND_DIR, "script.js"))




@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    try:
        session = session_memory.get(request.session_id)
        session_memory.add_message(request.session_id, "user", request.message)


        state = {
            "session_id": request.session_id,
            "message": request.message,
            "profile": session.profile.model_dump(),
            "agent": "",
            "active_agent": session.active_agent,
            "response": "",
            "confidence": 0.0,
            "retry_count": 0,
            "retry_reason": "",
        }
        result = compiled_graph.invoke(state)


        session_memory.update_profile(request.session_id, **result["profile"])
        session_memory.set_active_agent(request.session_id, result.get("active_agent"))
        session_memory.add_message(request.session_id, "assistant", result["response"])


        METRICS["total_requests"] += 1
        METRICS["agent_usage"][result["agent"]] = METRICS["agent_usage"].get(result["agent"], 0) + 1
        if result["retry_count"] > 0:
            METRICS["total_retries"] += 1


        updated_profile = session_memory.get(request.session_id).profile
        return ChatResponse(
            session_id=request.session_id,
            reply=result["response"],
            agent=result["agent"],
            confidence=result["confidence"],
            client_profile=updated_profile.model_dump(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Chat processing failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal error processing chat request") from exc




@app.post("/reset-session")
def reset_session(request: ResetRequest) -> dict:
    session_memory.reset(request.session_id)
    logger.info("Session %s reset", request.session_id)
    return {"status": "reset", "session_id": request.session_id}




@app.get("/health")
def health() -> dict:
    return {"status": "ok", "timestamp": time.time()}




@app.get("/metrics")
def metrics() -> dict:
    return {
        "total_requests": METRICS["total_requests"],
        "total_retries": METRICS["total_retries"],
        "agent_usage": METRICS["agent_usage"],
        "active_sessions": len(session_memory.all_sessions()),
    }