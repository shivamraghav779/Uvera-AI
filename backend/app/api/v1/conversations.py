import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import (
    CurrentPrincipal,
    PaginationDep,
    get_conversation_service,
    get_current_principal,
)
from app.api.schemas import ApiResponse, ErrorResponse
from app.domains.conversation.schemas import MessageCreate, MessageRead
from app.domains.conversation.service import ConversationService

router = APIRouter(
    prefix="/workspaces/{workspace_id}/messages",
    tags=["Conversations"],
    dependencies=[Depends(get_current_principal)],
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Unknown workspace."}
    },
)

ConversationServiceDep = Annotated[ConversationService, Depends(get_conversation_service)]


@router.get("", summary="List messages", description="Messages of a workspace, oldest first.")
async def list_messages(
    workspace_id: uuid.UUID,
    service: ConversationServiceDep,
    principal: CurrentPrincipal,
    pagination: PaginationDep,
) -> ApiResponse[list[MessageRead]]:
    messages = await service.list_messages(
        principal, workspace_id, limit=pagination.limit, offset=pagination.offset
    )
    return ApiResponse(data=[MessageRead.model_validate(message) for message in messages])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Add a message",
    description=(
        "Stores a message in the workspace's conversation without generating a UI. "
        "Use `POST /ui/generate` or `POST /ui/mutate` to send an instruction."
    ),
)
async def create_message(
    workspace_id: uuid.UUID,
    payload: MessageCreate,
    service: ConversationServiceDep,
    principal: CurrentPrincipal,
) -> ApiResponse[MessageRead]:
    message = await service.add_message(principal, workspace_id, payload)
    return ApiResponse(data=MessageRead.model_validate(message))
