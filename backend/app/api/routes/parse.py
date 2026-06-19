from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.schemas.project import (
    ParseTaskCreateRequest,
    ParseTaskCreateResponse,
    ParseTaskRead,
    ParseTaskResultRead,
)
from app.services.parse_tasks import (
    create_parse_task,
    get_active_project_parse_task,
    get_parse_task,
    run_parse_task,
)

router = APIRouter(tags=["parse-tasks"])


@router.post("/parse/tasks", response_model=ParseTaskCreateResponse, status_code=202)
def create_task(payload: ParseTaskCreateRequest, background_tasks: BackgroundTasks) -> ParseTaskCreateResponse:
    if not payload.source_text and not payload.source_file_id and payload.project_id is None:
        raise HTTPException(status_code=422, detail="请提供 source_text、source_file_id 或 project_id。")

    active_task = get_active_project_parse_task(payload.project_id)
    if active_task is not None:
        return ParseTaskCreateResponse(task_id=active_task.id)

    task = create_parse_task(
        source_text=payload.source_text,
        source_file_id=payload.source_file_id,
        project_id=payload.project_id,
    )
    background_tasks.add_task(run_parse_task, task.id)
    return ParseTaskCreateResponse(task_id=task.id)


@router.get("/parse/tasks/{task_id}", response_model=ParseTaskRead)
def get_task(task_id: str) -> ParseTaskRead:
    task = get_parse_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="解析任务不存在。")
    return ParseTaskRead(
        task_id=task.id,
        status=task.status,
        progress=task.progress,
        message=task.message,
        error=task.error_message,
        raw_response=task.raw_response,
        failed_chunks=task.failed_chunks,
    )


@router.get("/parse/tasks/{task_id}/result", response_model=ParseTaskResultRead)
def get_task_result(task_id: str) -> ParseTaskResultRead:
    task = get_parse_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="解析任务不存在。")
    if task.status not in {"completed", "completed_with_warnings"}:
        raise HTTPException(status_code=409, detail="解析任务尚未完成。")
    return ParseTaskResultRead(
        task_id=task.id,
        result_json=task.result_json,
        result_yaml=task.result_yaml,
        failed_chunks=task.failed_chunks,
    )
