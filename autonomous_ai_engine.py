from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional


# ============================================================
# VERSION / CONSTANTS
# ============================================================

ENGINE_NAME = "AUTONOMOUS_AI_ENGINE"
ENGINE_VERSION = "1.0.0-stage1"

SCHEMA_VERSION = 1


class Status(str, Enum):
    CREATED = "CREATED"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    RECOVERING = "RECOVERING"
    VERIFIED = "VERIFIED"


TERMINAL_STATES = {
    Status.VERIFIED,
    Status.BLOCKED,
}


# ============================================================
# HELPERS
# ============================================================

def now() -> float:
    return time.time()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def json_safe(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value

    if isinstance(value, Path):
        return str(value)

    if hasattr(value, "to_dict"):
        return value.to_dict()

    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [json_safe(v) for v in value]

    return value


# ============================================================
# TASK STEP
# ============================================================

@dataclass
class TaskStep:
    name: str
    action: Optional[str] = None
    step_id: str = field(default_factory=lambda: new_id("step"))
    status: Status = Status.CREATED
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Any = None
    error: Optional[str] = None
    attempts: int = 0
    created_at: float = field(default_factory=now)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    def start(self) -> None:
        self.status = Status.RUNNING
        self.started_at = now()
        self.attempts += 1
        self.error = None

    def complete(self, result: Any = None) -> None:
        self.status = Status.COMPLETED
        self.output_data = result
        self.completed_at = now()

    def fail(self, error: Any) -> None:
        self.status = Status.FAILED
        self.error = str(error)
        self.completed_at = now()

    def block(self, reason: Any) -> None:
        self.status = Status.BLOCKED
        self.error = str(reason)
        self.completed_at = now()

    def verify(self) -> None:
        if self.status != Status.COMPLETED:
            raise RuntimeError(
                f"Cannot verify step {self.step_id} from {self.status}"
            )
        self.status = Status.VERIFIED
        self.completed_at = now()

    def to_dict(self) -> Dict[str, Any]:
        return json_safe(asdict(self))


# ============================================================
# TASK
# ============================================================

@dataclass
class Task:
    request: str
    task_id: str = field(default_factory=lambda: new_id("task"))
    status: Status = Status.CREATED
    capability: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)
    steps: List[TaskStep] = field(default_factory=list)
    result: Any = None
    error: Optional[str] = None
    attempts: int = 0
    created_at: float = field(default_factory=now)
    updated_at: float = field(default_factory=now)

    def touch(self) -> None:
        self.updated_at = now()

    def add_step(
        self,
        name: str,
        action: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> TaskStep:
        step = TaskStep(
            name=name,
            action=action,
            input_data=input_data or {},
        )
        self.steps.append(step)
        self.touch()
        return step

    def get_step(self, step_id: str) -> Optional[TaskStep]:
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "task_id": self.task_id,
            "request": self.request,
            "status": self.status.value,
            "capability": self.capability,
            "metadata": json_safe(self.metadata),
            "steps": [step.to_dict() for step in self.steps],
            "result": json_safe(self.result),
            "error": self.error,
            "attempts": self.attempts,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        task = cls(
            request=data["request"],
            task_id=data["task_id"],
            status=Status(data.get("status", Status.CREATED.value)),
            capability=data.get("capability", "general"),
            metadata=data.get("metadata", {}),
            result=data.get("result"),
            error=data.get("error"),
            attempts=int(data.get("attempts", 0)),
            created_at=float(data.get("created_at", now())),
            updated_at=float(data.get("updated_at", now())),
        )

        for raw in data.get("steps", []):
            step = TaskStep(
                name=raw["name"],
                action=raw.get("action"),
                step_id=raw.get("step_id", new_id("step")),
                status=Status(raw.get("status", Status.CREATED.value)),
                input_data=raw.get("input_data", {}),
                output_data=raw.get("output_data"),
                error=raw.get("error"),
                attempts=int(raw.get("attempts", 0)),
                created_at=float(raw.get("created_at", now())),
                started_at=raw.get("started_at"),
                completed_at=raw.get("completed_at"),
            )
            task.steps.append(step)

        return task


# ============================================================
# PLAN
# ============================================================

@dataclass
class Plan:
    task_id: str
    steps: List[TaskStep] = field(default_factory=list)
    plan_id: str = field(default_factory=lambda: new_id("plan"))
    status: Status = Status.CREATED
    created_at: float = field(default_factory=now)

    def add_step(
        self,
        name: str,
        action: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> TaskStep:
        step = TaskStep(
            name=name,
            action=action,
            input_data=input_data or {},
        )
        self.steps.append(step)
        return step

    def next_step(self) -> Optional[TaskStep]:
        for step in self.steps:
            if step.status in {Status.CREATED, Status.READY}:
                return step
        return None

    def is_complete(self) -> bool:
        return all(
            step.status in {Status.COMPLETED, Status.VERIFIED}
            for step in self.steps
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "plan_id": self.plan_id,
            "task_id": self.task_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "steps": [step.to_dict() for step in self.steps],
        }


# ============================================================
# EXECUTION MEMORY
# ============================================================

@dataclass
class MemoryEvent:
    event_id: str
    event_type: str
    task_id: Optional[str]
    data: Dict[str, Any]
    timestamp: float


class ExecutionMemory:
    """
    Lightweight local execution memory.

    No LLM.
    No network.
    No polling.
    """

    def __init__(self, max_events: int = 5000):
        self.max_events = max_events
        self.events: List[MemoryEvent] = []

    def record(
        self,
        event_type: str,
        task_id: Optional[str] = None,
        **data: Any,
    ) -> MemoryEvent:
        event = MemoryEvent(
            event_id=new_id("event"),
            event_type=event_type,
            task_id=task_id,
            data=json_safe(data),
            timestamp=now(),
        )

        self.events.append(event)

        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]

        return event

    def for_task(self, task_id: str) -> List[MemoryEvent]:
        return [
            event for event in self.events
            if event.task_id == task_id
        ]

    def last(self, task_id: Optional[str] = None) -> Optional[MemoryEvent]:
        events = (
            self.events
            if task_id is None
            else self.for_task(task_id)
        )

        return events[-1] if events else None

    def export(self) -> List[Dict[str, Any]]:
        return [
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "task_id": event.task_id,
                "data": json_safe(event.data),
                "timestamp": event.timestamp,
            }
            for event in self.events
        ]


# ============================================================
# STATE MANAGER
# ============================================================

class StateManager:
    """
    Central in-memory state manager.

    State transitions are explicit and auditable.
    """

    ALLOWED = {
        Status.CREATED: {
            Status.READY,
            Status.BLOCKED,
            Status.FAILED,
        },
        Status.READY: {
            Status.RUNNING,
            Status.BLOCKED,
            Status.FAILED,
        },
        Status.RUNNING: {
            Status.COMPLETED,
            Status.FAILED,
            Status.BLOCKED,
            Status.RECOVERING,
        },
        Status.COMPLETED: {
            Status.VERIFIED,
            Status.FAILED,
        },
        Status.FAILED: {
            Status.RECOVERING,
            Status.BLOCKED,
        },
        Status.RECOVERING: {
            Status.READY,
            Status.FAILED,
            Status.BLOCKED,
        },
        Status.VERIFIED: set(),
        Status.BLOCKED: set(),
    }

    def __init__(self):
        self._tasks: Dict[str, Task] = {}

    def save(self, task: Task) -> Task:
        task.touch()
        self._tasks[task.task_id] = task
        return task

    def get(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def require(self, task_id: str) -> Task:
        task = self.get(task_id)
        if task is None:
            raise KeyError(f"Task not found: {task_id}")
        return task

    def transition(self, task: Task, new_status: Status) -> Task:
        current = task.status

        if current == new_status:
            return task

        allowed = self.ALLOWED.get(current, set())

        if new_status not in allowed:
            raise ValueError(
                f"Invalid transition: {current.value} -> {new_status.value}"
            )

        task.status = new_status
        task.touch()
        self.save(task)
        return task

    def all(self) -> List[Task]:
        return list(self._tasks.values())


# ============================================================
# TASK ENGINE
# ============================================================

class TaskEngine:
    """
    Lightweight task creation and planning foundation.
    """

    def __init__(
        self,
        state: Optional[StateManager] = None,
        memory: Optional[ExecutionMemory] = None,
    ):
        self.state = state or StateManager()
        self.memory = memory or ExecutionMemory()

    def create(
        self,
        request: str,
        capability: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Task:
        if not isinstance(request, str) or not request.strip():
            raise ValueError("Task request must be a non-empty string")

        task = Task(
            request=request.strip(),
            capability=capability,
            metadata=metadata or {},
        )

        self.state.save(task)

        self.memory.record(
            "TASK_CREATED",
            task.task_id,
            request=task.request,
            capability=task.capability,
        )

        return task

    def prepare(self, task: Task) -> Task:
        if task.status == Status.CREATED:
            self.state.transition(task, Status.READY)

        self.memory.record(
            "TASK_READY",
            task.task_id,
        )

        return task

    def add_step(
        self,
        task: Task,
        name: str,
        action: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> TaskStep:
        step = task.add_step(
            name=name,
            action=action,
            input_data=input_data,
        )

        self.state.save(task)

        self.memory.record(
            "STEP_CREATED",
            task.task_id,
            step_id=step.step_id,
            name=step.name,
        )

        return step


# ============================================================
# PERSISTENT STORE
# ============================================================

class PersistentStore:
    """
    Local JSON persistence.

    Standard library only.
    Atomic write strategy.
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.tasks_dir = self.root / "tasks"
        self.memory_file = self.root / "memory.json"

        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def save_task(self, task: Task) -> Path:
        destination = self.tasks_dir / f"{task.task_id}.json"
        temporary = destination.with_suffix(".tmp")

        temporary.write_text(
            json.dumps(
                task.to_dict(),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        temporary.replace(destination)
        return destination

    def load_task(self, task_id: str) -> Task:
        path = self.tasks_dir / f"{task_id}.json"

        if not path.exists():
            raise FileNotFoundError(path)

        data = json.loads(
            path.read_text(encoding="utf-8")
        )

        return Task.from_dict(data)

    def save_memory(self, memory: ExecutionMemory) -> Path:
        temporary = self.memory_file.with_suffix(".tmp")

        temporary.write_text(
            json.dumps(
                memory.export(),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        temporary.replace(self.memory_file)
        return self.memory_file


# ============================================================
# TASK LIFECYCLE
# ============================================================

class TaskLifecycle:
    """
    Persistent lifecycle facade.

    Keeps task state, history and persistence together.
    """

    def __init__(
        self,
        store: Optional[PersistentStore] = None,
        state: Optional[StateManager] = None,
        memory: Optional[ExecutionMemory] = None,
    ):
        self.store = store
        self.state = state or StateManager()
        self.memory = memory or ExecutionMemory()

    def create(
        self,
        request: str,
        capability: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Task:
        engine = TaskEngine(self.state, self.memory)

        task = engine.create(
            request=request,
            capability=capability,
            metadata=metadata,
        )

        engine.prepare(task)

        self.persist(task)

        return task

    def persist(self, task: Task) -> None:
        self.state.save(task)

        if self.store:
            self.store.save_task(task)
            self.store.save_memory(self.memory)

    def load(self, task_id: str) -> Task:
        if self.store:
            task = self.store.load_task(task_id)
            self.state.save(task)
            return task

        return self.state.require(task_id)

    def transition(
        self,
        task: Task,
        status: Status,
    ) -> Task:
        self.state.transition(task, status)

        self.memory.record(
            "STATE_TRANSITION",
            task.task_id,
            status=status.value,
        )

        self.persist(task)
        return task

    def history(self, task_id: str) -> List[Dict[str, Any]]:
        return [
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "task_id": event.task_id,
                "data": event.data,
                "timestamp": event.timestamp,
            }
            for event in self.memory.for_task(task_id)
        ]


# ============================================================
# PLAN EXECUTOR FOUNDATION
# ============================================================

class PlanExecutor:
    """
    Local deterministic executor.

    It accepts Python callables.
    No LLM and no network are required.
    """

    def __init__(self, lifecycle: TaskLifecycle):
        self.lifecycle = lifecycle

    def execute(
        self,
        task: Task,
        plan: Plan,
        actions: Optional[Dict[str, Callable[..., Any]]] = None,
    ) -> Task:
        actions = actions or {}

        if task.status == Status.CREATED:
            self.lifecycle.transition(task, Status.READY)

        self.lifecycle.transition(task, Status.RUNNING)
        task.attempts += 1

        try:
            for step in plan.steps:
                if step.status in {Status.COMPLETED, Status.VERIFIED}:
                    continue

                step.start()

                try:
                    action = actions.get(step.action or "")

                    if action is None:
                        result = step.input_data
                    else:
                        result = action(step.input_data)

                    step.complete(result)

                    self.lifecycle.memory.record(
                        "STEP_COMPLETED",
                        task.task_id,
                        step_id=step.step_id,
                    )

                except Exception as exc:
                    step.fail(exc)

                    self.lifecycle.memory.record(
                        "STEP_FAILED",
                        task.task_id,
                        step_id=step.step_id,
                        error=str(exc),
                    )

                    self.lifecycle.transition(task, Status.FAILED)
                    task.error = str(exc)
                    self.lifecycle.persist(task)
                    return task

            task.result = {
                "steps": len(plan.steps),
                "completed": sum(
                    1
                    for step in plan.steps
                    if step.status == Status.COMPLETED
                ),
            }

            self.lifecycle.transition(task, Status.COMPLETED)
            return task

        except Exception as exc:
            task.error = str(exc)

            if task.status == Status.RUNNING:
                self.lifecycle.transition(task, Status.FAILED)

            self.lifecycle.persist(task)
            return task


# ============================================================
# FOUNDATION API
# ============================================================

class AutonomousEngineFoundation:
    """
    Single-file Stage-1 foundation.

    Later stages can attach:
        - intent
        - planner
        - tools
        - research
        - LLM providers
        - context/token control
        - recovery
        - hot swap
        - verification
        - autonomous orchestration
    without changing the persistence contract.
    """

    def __init__(
        self,
        data_dir: Optional[str | Path] = None,
    ):
        self.data_dir = (
            Path(data_dir)
            if data_dir is not None
            else Path(".engine_data")
        )

        self.store = PersistentStore(self.data_dir)
        self.state = StateManager()
        self.memory = ExecutionMemory()

        self.lifecycle = TaskLifecycle(
            store=self.store,
            state=self.state,
            memory=self.memory,
        )

        self.task_engine = TaskEngine(
            state=self.state,
            memory=self.memory,
        )

        self.plan_executor = PlanExecutor(
            lifecycle=self.lifecycle,
        )

    def create_task(
        self,
        request: str,
        capability: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Task:
        return self.lifecycle.create(
            request=request,
            capability=capability,
            metadata=metadata,
        )

    def create_plan(self, task: Task) -> Plan:
        plan = Plan(task_id=task.task_id)
        return plan

    def status(self, task_id: str) -> str:
        return self.lifecycle.load(task_id).status.value

    def history(self, task_id: str) -> List[Dict[str, Any]]:
        return self.lifecycle.history(task_id)


# ============================================================
# STAGE 1 SELF TESTS
# ============================================================

def run_stage1_tests() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as temp:
        engine = AutonomousEngineFoundation(temp)

        # 1. Task creation
        task = engine.create_task(
            "Build and verify an autonomous task engine",
            capability="general",
        )

        assert task.status == Status.READY
        assert task.task_id
        assert task.request

        # 2. Plan creation
        plan = engine.create_plan(task)

        plan.add_step(
            "Initialize",
            action="initialize",
            input_data={"ok": True},
        )

        plan.add_step(
            "Verify",
            action="verify",
            input_data={"verified": True},
        )

        assert len(plan.steps) == 2
        assert plan.task_id == task.task_id

        # 3. Deterministic local execution
        def initialize(data):
            assert data["ok"] is True
            return {"initialized": True}

        def verify(data):
            assert data["verified"] is True
            return {"verified": True}

        result = engine.plan_executor.execute(
            task,
            plan,
            actions={
                "initialize": initialize,
                "verify": verify,
            },
        )

        assert result.status == Status.COMPLETED
        assert all(
            step.status == Status.COMPLETED
            for step in plan.steps
        )

        # 4. Persistence
        loaded = engine.lifecycle.load(task.task_id)

        assert loaded.task_id == task.task_id
        assert loaded.status == Status.COMPLETED

        # 5. Verification transition
        engine.lifecycle.transition(
            loaded,
            Status.VERIFIED,
        )

        verified = engine.lifecycle.load(task.task_id)

        assert verified.status == Status.VERIFIED

        # 6. History
        history = engine.history(task.task_id)

        assert history
        assert any(
            item["event_type"] == "TASK_CREATED"
            for item in history
        )

        # 7. Failure path
        failed_task = engine.create_task(
            "Failure test",
            capability="general",
        )

        failed_plan = engine.create_plan(failed_task)
        failed_plan.add_step(
            "Fail",
            action="fail",
        )

        def fail(_):
            raise RuntimeError("intentional-test-error")

        failed_result = engine.plan_executor.execute(
            failed_task,
            failed_plan,
            actions={"fail": fail},
        )

        assert failed_result.status == Status.FAILED
        assert failed_result.error == "intentional-test-error"

        # 8. Persistence after failure
        failed_loaded = engine.lifecycle.load(
            failed_task.task_id
        )

        assert failed_loaded.status == Status.FAILED

    print("STAGE_1_TESTS=PASSED")
    print("TASK_ENGINE=VERIFIED")
    print("TASK_STEP=VERIFIED")
    print("PLAN=VERIFIED")
    print("STATE_MANAGER=VERIFIED")
    print("EXECUTION_MEMORY=VERIFIED")
    print("TASK_LIFECYCLE=VERIFIED")
    print("PERSISTENT_STORE=VERIFIED")
    print("PLAN_EXECUTOR_FOUNDATION=VERIFIED")
    print("FAILURE_PATH=VERIFIED")
    print("PERSISTENCE_PATH=VERIFIED")
    print("LLM_REQUIRED_FOR_STAGE_1=NO")
    print("NETWORK_REQUIRED_FOR_STAGE_1=NO")
    print("STAGE_1_EXTERNAL_EXECUTION=NOT_VERIFIED")


if __name__ == "__main__":
    run_stage1_tests()
