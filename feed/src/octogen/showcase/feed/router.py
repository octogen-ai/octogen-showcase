from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Request
from octogen.shop_agent.checkpointer import ShopAgentInMemoryCheckpointSaver
from octogen.shop_agent.crud import (
    delete_thread,
    get_chat_history_for_thread,
    list_threads_for_user,
)
from octogen.shop_agent.schemas import ChatHistory, Thread
from octogen.showcase.feed.schema import AgentResponse

# Create router for chat history endpoints
history_router = APIRouter(prefix="/showcase/feed/history", tags=["history"])


def get_checkpointer(request: Request) -> ShopAgentInMemoryCheckpointSaver:
    checkpointer: ShopAgentInMemoryCheckpointSaver = request.app.state.checkpointer
    return checkpointer


CheckpointerDep = Annotated[ShopAgentInMemoryCheckpointSaver, Depends(get_checkpointer)]


@history_router.get("/showcase/feed/threads/{user_id}", response_model=List[Thread])
async def get_threads(user_id: str, checkpointer: CheckpointerDep) -> List[Thread]:
    """List all conversation threads for a user."""
    return await list_threads_for_user(user_id, checkpointer=checkpointer)


@history_router.get(
    "/showcase/feed/threads/{user_id}/{thread_id}", response_model=ChatHistory
)
async def get_chat_history(
    user_id: str, thread_id: str, checkpointer: CheckpointerDep
) -> ChatHistory:
    """Get full chat history for a specific thread."""
    return await get_chat_history_for_thread(
        user_id=user_id,
        thread_id=thread_id,
        checkpointer=checkpointer,
        response_model_class=AgentResponse,
    )


@history_router.delete("/showcase/feed/threads/{user_id}/{thread_id}")
async def remove_thread(
    user_id: str, thread_id: str, checkpointer: CheckpointerDep
) -> dict[str, bool | int]:
    """Delete a conversation thread."""
    deleted_count = await delete_thread(user_id, thread_id, checkpointer=checkpointer)
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Thread not found")
    return {"deleted": True, "count": deleted_count}
