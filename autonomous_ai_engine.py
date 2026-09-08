
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import json
import time
import tempfile
import uuid


ENGINE_NAME = "KHALED Autonomous AI Engine"
ENGINE_VERSION = "1.0.0-stage1"


class Status(str, Enum):
    CREATED = "CREATED"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


@dataclass
class TaskStep:
    name: str
    action: Optional[str] = None
    status: Status = Status.CREATED
    result: Any = None
    error: Optional[str] = None

    def complete(self, result=None):
        self.status = Status.COMPLETED
        self.result = result
        self.error = None

    def fail(self, error):
        self.status = Status.FAILED
        self.error = str(error)


@dataclass
class Task:
    task_id: str
    goal: str
    status: Status = Status.CREATED
    steps: List[TaskStep] = field(default_factory=list)
    result: Any = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def add_step(self, step: TaskStep):
        self.steps.append(step)
        self.updated_at = time.time()

    def set_status(self, status: Status):
        self.status = status
        self.updated_at = time.time()


@dataclass
class Plan:
    plan_id: str
    task_id: str
    goal: str
    steps: List[TaskStep] = field(default_factory=list)
    status: Status = Status.CREATED

    def add_step(self, step: TaskStep):
        self.steps.append(step)


@dataclass
class MemoryEvent:
    event_id: str
    event_type: str
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)


class ExecutionMemory:
    def __init__(self):
        self.events: List[MemoryEvent] = []

    def add(self, event_type: str, data: Dict[str, Any]):
        event = MemoryEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            data=data,
        )
        self.events.append(event)
        return event

    def recent(self, limit: int = 20):
        return self.events[-limit:]

    def clear(self):
        self.events.clear()


class StateManager:
    def __init__(self):
        self._state: Dict[str, Any] = {}

    def set(self, key: str, value: Any):
        self._state[key] = value

    def get(self, key: str, default=None):
        return self._state.get(key, default)

    def delete(self, key: str):
        self._state.pop(key, None)

    def snapshot(self):
        return dict(self._state)

    def restore(self, state: Dict[str, Any]):
        self._state = dict(state)


class PersistentStore:
    def __init__(self, path: Optional[str] = None):
        self.path = Path(path) if path else Path(tempfile.gettempdir()) / "khaled_engine_state.json"

    def save(self, data: Dict[str, Any]):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        temp.replace(self.path)

    def load(self):
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def exists(self):
        return self.path.exists()

    def delete(self):
        if self.path.exists():
            self.path.unlink()


class TaskEngine:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.memory = ExecutionMemory()
        self.state = StateManager()

    def create_task(self, goal: str):
        task = Task(
            task_id=str(uuid.uuid4()),
            goal=goal,
            status=Status.READY,
        )
        self.tasks[task.task_id] = task
        self.memory.add(
            "TASK_CREATED",
            {"task_id": task.task_id, "goal": goal},
        )
        return task

    def get_task(self, task_id: str):
        return self.tasks.get(task_id)

    def start(self, task_id: str):
        task = self.tasks[task_id]
        task.set_status(Status.RUNNING)
        self.memory.add("TASK_STARTED", {"task_id": task_id})
        return task

    def complete(self, task_id: str, result=None):
        task = self.tasks[task_id]
        task.result = result
        task.set_status(Status.COMPLETED)
        self.memory.add(
            "TASK_COMPLETED",
            {"task_id": task_id, "result": result},
        )
        return task

    def fail(self, task_id: str, error):
        task = self.tasks[task_id]
        task.error = str(error)
        task.set_status(Status.FAILED)
        self.memory.add(
            "TASK_FAILED",
            {"task_id": task_id, "error": str(error)},
        )
        return task


class TaskLifecycle:
    def __init__(self, engine: TaskEngine):
        self.engine = engine

    def pause(self, task_id: str):
        return self.engine.tasks[task_id].set_status(Status.PAUSED)

    def cancel(self, task_id: str):
        return self.engine.tasks[task_id].set_status(Status.CANCELLED)

    def resume(self, task_id: str):
        task = self.engine.tasks[task_id]
        task.set_status(Status.RUNNING)
        return task


class PlanExecutor:
    def __init__(self, engine: TaskEngine):
        self.engine = engine

    def execute(self, task: Task, plan: Plan, handlers=None):
        handlers = handlers or {}
        self.engine.start(task.task_id)
        plan.status = Status.RUNNING

        try:
            for step in plan.steps:
                handler = handlers.get(step.action)

                if handler is None:
                    step.complete({
                        "action": step.action,
                        "status": "NO_HANDLER",
                    })
                    task.add_step(step)
                    continue

                result = handler(step)
                step.complete(result)
                task.add_step(step)

            plan.status = Status.COMPLETED
            return self.engine.complete(
                task.task_id,
                {"plan_id": plan.plan_id},
            )

        except Exception as exc:
            plan.status = Status.FAILED
            self.engine.fail(task.task_id, str(exc))
            raise


class AutonomousEngineFoundation:
    def __init__(self, persistence_path=None):
        self.engine = TaskEngine()
        self.lifecycle = TaskLifecycle(self.engine)
        self.executor = PlanExecutor(self.engine)
        self.store = PersistentStore(persistence_path)

    def create_task(self, goal):
        return self.engine.create_task(goal)

    def save(self):
        payload = {
            "version": ENGINE_VERSION,
            "tasks": {
                task_id: asdict(task)
                for task_id, task in self.engine.tasks.items()
            },
            "state": self.engine.state.snapshot(),
            "memory": [
                asdict(event)
                for event in self.engine.memory.events
            ],
        }
        self.store.save(payload)

    def load(self):
        data = self.store.load()

        if not data:
            return False

        self.engine.state.restore(data.get("state", {}))

        for task_id, raw in data.get("tasks", {}).items():
            raw["status"] = Status(raw["status"])
            raw["steps"] = [
                TaskStep(
                    name=s["name"],
                    action=s.get("action"),
                    status=Status(s["status"]),
                    result=s.get("result"),
                    error=s.get("error"),
                )
                for s in raw.get("steps", [])
            ]
            self.engine.tasks[task_id] = Task(**raw)

        return True


def run_stage1_tests():
    engine = AutonomousEngineFoundation()

    # Task Engine
    task = engine.create_task("stage 1 test")
    assert task.status == Status.READY
    assert engine.engine.get_task(task.task_id) is task

    # Task Step
    step = TaskStep(name="test-step", action="noop")
    step.complete("ok")
    assert step.status == Status.COMPLETED
    assert step.result == "ok"

    # Plan
    plan = Plan(
        plan_id=str(uuid.uuid4()),
        task_id=task.task_id,
        goal=task.goal,
    )
    plan.add_step(TaskStep(name="step", action="noop"))
    assert len(plan.steps) == 1

    # State
    engine.engine.state.set("x", 123)
    assert engine.engine.state.get("x") == 123

    # Memory
    engine.engine.memory.add("TEST", {"ok": True})
    assert len(engine.engine.memory.recent()) >= 1

    # Lifecycle
    engine.lifecycle.pause(task.task_id)
    assert task.status == Status.PAUSED
    engine.lifecycle.resume(task.task_id)
    assert task.status == Status.RUNNING

    # Executor
    task2 = engine.create_task("executor test")
    plan2 = Plan(
        plan_id=str(uuid.uuid4()),
        task_id=task2.task_id,
        goal=task2.goal,
    )
    plan2.add_step(TaskStep(name="noop", action="noop"))

    result = engine.executor.execute(
        task2,
        plan2,
        {"noop": lambda step: "EXECUTED"},
    )

    assert result.status == Status.COMPLETED
    assert result.steps[-1].result == "EXECUTED"

    # Failure path
    task3 = engine.create_task("failure test")
    plan3 = Plan(
        plan_id=str(uuid.uuid4()),
        task_id=task3.task_id,
        goal=task3.goal,
    )
    plan3.add_step(TaskStep(name="bad", action="bad"))

    try:
        engine.executor.execute(
            task3,
            plan3,
            {"bad": lambda step: 1 / 0},
        )
        raise AssertionError("FAILURE_PATH_NOT_TRIGGERED")
    except ZeroDivisionError:
        pass

    assert task3.status == Status.FAILED

    # Persistence
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "state.json"
        persistent = AutonomousEngineFoundation(str(path))
        persistent_task = persistent.create_task("persistence test")
        persistent.engine.state.set("persistent", True)
        persistent.save()

        assert path.exists()

        restored = AutonomousEngineFoundation(str(path))
        assert restored.load() is True
        assert restored.engine.state.get("persistent") is True
        assert restored.engine.get_task(persistent_task.task_id) is not None

    return True


if __name__ == "__main__":
    run_stage1_tests()
    print("STAGE_1_TESTS=PASSED")

# ============================================================
# STAGE_2_SAFE_MARKER
# KHALED Understanding and Planning Layer
# ============================================================

from enum import Enum as _Stage2Enum
from dataclasses import dataclass as _Stage2Dataclass, field as _Stage2Field
import re as _Stage2Re

class IntentType(_Stage2Enum):
    UNKNOWN = 'UNKNOWN'
    CREATE = 'CREATE'
    MODIFY = 'MODIFY'
    ANALYZE = 'ANALYZE'
    TEST = 'TEST'
    DEBUG = 'DEBUG'
    REPAIR = 'REPAIR'
    RESEARCH = 'RESEARCH'
    GITHUB = 'GITHUB'
    EXECUTE = 'EXECUTE'

@_Stage2Dataclass
class Intent:
    intent_type: IntentType
    goal: str
    confidence: float = 0.0
    requires_llm: bool = False
    requires_network: bool = False

class CommandNormalizer:
    def normalize(self, command):
        if command is None:
            return ''
        return _Stage2Re.sub(r'\s+', ' ', str(command).strip())

class IntentEngine:
    KEYWORDS = {
        IntentType.CREATE: (
            "create", "build", "make", "انشاء", "إنشاء",
            "انشئ", "أنشئ", "ابني", "بناء"
        ),
        IntentType.MODIFY: (
            "modify", "change", "edit", "update",
            "تعديل", "عدل", "تغيير", "غير", "غيّر"
        ),
        IntentType.ANALYZE: (
            "analyze", "analysis", "inspect",
            "حلل", "تحليل", "افحص", "فحص"
        ),
        IntentType.TEST: (
            "test", "tests", "testing",
            "اختبر", "اختبار", "اختبارات"
        ),
        IntentType.DEBUG: (
            "debug", "debugging", "error", "bug",
            "خطأ", "اخطاء", "أخطاء", "تصحيح"
        ),
        IntentType.REPAIR: (
            "repair", "repairs", "fix", "fixing",
            "إصلاح", "اصلاح", "اصلح", "أصلح",
            "تصليح", "إصلاحه", "اصلحه", "أصلحه"
        ),
        IntentType.RESEARCH: (
            "research", "search", "investigate",
            "ابحث", "بحث", "دراسة", "استقصاء"
        ),
        IntentType.GITHUB: (
            "github", "git hub", "repository",
            "repo", "مستودع", "مستودع github"
        ),
        IntentType.EXECUTE: (
            "run", "execute", "launch",
            "شغل", "تشغيل", "نفذ", "تنفيذ"
        ),
    }

    def detect(self, command):
        value = CommandNormalizer().normalize(command)
        low = value.lower()

        scores = {}

        for intent_type, keywords in self.KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in low:
                    score += 1
            scores[intent_type] = score

        priority = (
            IntentType.REPAIR,
            IntentType.DEBUG,
            IntentType.MODIFY,
            IntentType.CREATE,
            IntentType.TEST,
            IntentType.RESEARCH,
            IntentType.GITHUB,
            IntentType.EXECUTE,
            IntentType.ANALYZE,
        )

        best = IntentType.UNKNOWN
        best_score = 0

        for intent_type in priority:
            score = scores.get(intent_type, 0)
            if score > best_score:
                best = intent_type
                best_score = score

        confidence = min(1.0, best_score / 2.0)

        needs_network = best in (
            IntentType.RESEARCH,
            IntentType.GITHUB,
        )

        needs_llm = best in (
            IntentType.ANALYZE,
            IntentType.DEBUG,
            IntentType.REPAIR,
            IntentType.RESEARCH,
        )

        return Intent(
            best,
            value,
            confidence,
            needs_llm,
            needs_network,
        )

class TaskRouter:
    ROUTES = {
        IntentType.CREATE: 'BUILD',
        IntentType.MODIFY: 'MODIFY',
        IntentType.ANALYZE: 'ANALYSIS',
        IntentType.TEST: 'TEST',
        IntentType.DEBUG: 'DEBUG',
        IntentType.REPAIR: 'REPAIR',
        IntentType.RESEARCH: 'RESEARCH',
        IntentType.GITHUB: 'GITHUB',
        IntentType.EXECUTE: 'EXECUTION',
        IntentType.UNKNOWN: 'CLARIFICATION',
    }

    def route(self, intent):
        return self.ROUTES.get(intent.intent_type, 'CLARIFICATION')

class DecisionType(_Stage2Enum):
    LOCAL = 'LOCAL'
    LLM = 'LLM'
    NETWORK = 'NETWORK'
    LLM_NETWORK = 'LLM_NETWORK'
    CLARIFY = 'CLARIFY'

@_Stage2Dataclass
class Decision:
    decision_type: DecisionType
    route: str
    reason: str
    requires_llm: bool
    requires_network: bool

class DecisionEngine:
    def decide(self, intent, route):
        if intent.intent_type == IntentType.UNKNOWN:
            return Decision(DecisionType.CLARIFY, route, 'Intent requires clarification.', False, False)
        if intent.requires_llm and intent.requires_network:
            kind = DecisionType.LLM_NETWORK
        elif intent.requires_llm:
            kind = DecisionType.LLM
        elif intent.requires_network:
            kind = DecisionType.NETWORK
        else:
            kind = DecisionType.LOCAL
        return Decision(kind, route, 'Selected execution path.', intent.requires_llm, intent.requires_network)

@_Stage2Dataclass
class PlannedStep:
    step_id: str
    name: str
    action: str
    dependencies: list = _Stage2Field(default_factory=list)

class Planner:
    def create_plan(self, task_id, goal, intent, route):
        steps = [PlannedStep(task_id + ':understand', 'Understand', 'understand')]
        steps.append(PlannedStep(task_id + ':plan', 'Plan', 'plan', [steps[-1].step_id]))
        if intent.requires_network:
            steps.append(PlannedStep(task_id + ':network', 'Network', 'network', [steps[-1].step_id]))
        if intent.requires_llm:
            steps.append(PlannedStep(task_id + ':llm', 'AI Reasoning', 'llm', [steps[-1].step_id]))
        steps.append(PlannedStep(task_id + ':execute', 'Execute', route.lower(), [steps[-1].step_id]))
        steps.append(PlannedStep(task_id + ':verify', 'Verify', 'verify', [steps[-1].step_id]))
        return steps

class Stage2PlanningSystem:
    def __init__(self):
        self.normalizer = CommandNormalizer()
        self.intent_engine = IntentEngine()
        self.router = TaskRouter()
        self.decision_engine = DecisionEngine()
        self.planner = Planner()

    def understand(self, command):
        normalized = self.normalizer.normalize(command)
        intent = self.intent_engine.detect(normalized)
        route = self.router.route(intent)
        decision = self.decision_engine.decide(intent, route)
        return {'command': normalized, 'intent': intent, 'route': route, 'decision': decision}

    def plan(self, task_id, command):
        result = self.understand(command)
        result['steps'] = self.planner.create_plan(task_id, result['command'], result['intent'], result['route'])
        return result

def run_stage2_tests():
    system = Stage2PlanningSystem()
    assert system.normalizer.normalize('  hello    world ') == 'hello world'
    r = system.understand('create a project')
    assert r['intent'].intent_type == IntentType.CREATE
    assert r['route'] == 'BUILD'
    assert r['decision'].decision_type == DecisionType.LOCAL
    r = system.understand('run tests')
    assert r['intent'].intent_type == IntentType.TEST
    r = system.understand('repair the error')
    assert r['intent'].intent_type == IntentType.REPAIR
    assert r['decision'].requires_llm is True
    r = system.understand('research this topic')
    assert r['intent'].intent_type == IntentType.RESEARCH
    assert r['decision'].requires_network is True
    assert r['decision'].requires_llm is True
    r = system.understand('xyz123')
    assert r['intent'].intent_type == IntentType.UNKNOWN
    assert r['decision'].decision_type == DecisionType.CLARIFY
    p = system.plan('stage2-task', 'repair the project error')
    assert len(p['steps']) >= 4
    assert p['steps'][0].action == 'understand'
    assert p['steps'][-1].action == 'verify'
    return True


# ==================== STAGE_3_TOOLS ====================

class ToolPermission:
    READ = "READ"
    WRITE = "WRITE"
    EXECUTE = "EXECUTE"
    NETWORK = "NETWORK"


class ToolResult:
    def __init__(self, success, output="", error="", metadata=None):
        self.success = bool(success)
        self.output = output
        self.error = error
        self.metadata = metadata or {}

    def to_dict(self):
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
        }


class ToolContext:
    def __init__(self, workspace):
        self.workspace = Path(workspace).resolve()
        self.metadata = {}

    def safe_path(self, path):
        candidate = (self.workspace / path).resolve()

        try:
            candidate.relative_to(self.workspace)
        except ValueError:
            raise PermissionError("PATH_OUTSIDE_WORKSPACE")

        return candidate


class Tool:
    name = "tool"
    permissions = ()

    def execute(self, context, **kwargs):
        raise NotImplementedError


class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, tool):
        if not getattr(tool, "name", None):
            raise ValueError("TOOL_NAME_REQUIRED")

        self._tools[tool.name] = tool

    def get(self, name):
        return self._tools.get(name)

    def list(self):
        return sorted(self._tools.keys())


class ToolGovernance:
    def __init__(self):
        self.denied = set()

    def deny(self, tool_name):
        self.denied.add(tool_name)

    def allow(self, tool_name):
        self.denied.discard(tool_name)

    def can_execute(self, tool):
        return tool.name not in self.denied


class ReadFileTool(Tool):
    name = "read_file"
    permissions = (ToolPermission.READ,)

    def execute(self, context, path):
        target = context.safe_path(path)

        if not target.exists():
            return ToolResult(
                False,
                error="FILE_NOT_FOUND",
                metadata={"path": str(target)}
            )

        if not target.is_file():
            return ToolResult(
                False,
                error="NOT_A_FILE",
                metadata={"path": str(target)}
            )

        return ToolResult(
            True,
            output=target.read_text(encoding="utf-8"),
            metadata={"path": str(target)}
        )


class WriteFileTool(Tool):
    name = "write_file"
    permissions = (ToolPermission.WRITE,)

    def execute(self, context, path, content):
        target = context.safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

        return ToolResult(
            True,
            output="FILE_WRITTEN",
            metadata={
                "path": str(target),
                "bytes": target.stat().st_size,
            }
        )


class ToolSystem:
    def __init__(self, workspace):
        self.context = ToolContext(workspace)
        self.registry = ToolRegistry()
        self.governance = ToolGovernance()

        self.registry.register(ReadFileTool())
        self.registry.register(WriteFileTool())

    def execute(self, tool_name, **kwargs):
        tool = self.registry.get(tool_name)

        if tool is None:
            return ToolResult(
                False,
                error="TOOL_NOT_FOUND",
                metadata={"tool": tool_name}
            )

        if not self.governance.can_execute(tool):
            return ToolResult(
                False,
                error="TOOL_DENIED",
                metadata={"tool": tool_name}
            )

        try:
            return tool.execute(self.context, **kwargs)
        except PermissionError as exc:
            return ToolResult(
                False,
                error=str(exc),
                metadata={"tool": tool_name}
            )
        except Exception as exc:
            return ToolResult(
                False,
                error=f"{type(exc).__name__}: {exc}",
                metadata={"tool": tool_name}
            )


def run_stage3_tests():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        system = ToolSystem(tmp)

        assert "read_file" in system.registry.list()
        assert "write_file" in system.registry.list()

        write = system.execute(
            "write_file",
            path="hello.txt",
            content="KHALED STAGE 3"
        )

        assert write.success is True

        read = system.execute(
            "read_file",
            path="hello.txt"
        )

        assert read.success is True
        assert read.output == "KHALED STAGE 3"

        missing = system.execute(
            "read_file",
            path="missing.txt"
        )

        assert missing.success is False
        assert missing.error == "FILE_NOT_FOUND"

        outside = system.execute(
            "read_file",
            path="../outside.txt"
        )

        assert outside.success is False
        assert outside.error == "PATH_OUTSIDE_WORKSPACE"

        system.governance.deny("read_file")

        denied = system.execute(
            "read_file",
            path="hello.txt"
        )

        assert denied.success is False
        assert denied.error == "TOOL_DENIED"

    return True

# ==================== END STAGE_3_TOOLS ====================

# ===== STAGE_3_EXECUTION_LAYER =====
class ToolExecutionError(Exception):
    pass

class ToolExecutionLayer:
    def __init__(self, tool_system):
        self.tool_system = tool_system
        self.execution_count = 0

    def execute(self, tool_name, context, **kwargs):
        self.execution_count += 1

        if not hasattr(self.tool_system, 'registry'):
            raise ToolExecutionError('TOOL_REGISTRY_NOT_AVAILABLE')

        tool = self.tool_system.registry.get(tool_name)
        if tool is None:
            raise ToolExecutionError(f'TOOL_NOT_FOUND:{tool_name}')

        if hasattr(self.tool_system, 'governance'):
            governance = self.tool_system.governance
            if hasattr(governance, 'is_allowed'):
                allowed = governance.is_allowed(tool, context)
                if not allowed:
                    raise ToolExecutionError(f'TOOL_NOT_ALLOWED:{tool_name}')

        try:
            if hasattr(tool, 'execute'):
                result = tool.execute(context, **kwargs)
            elif callable(tool):
                result = tool(context, **kwargs)
            else:
                raise ToolExecutionError(f'TOOL_NOT_EXECUTABLE:{tool_name}')
        except ToolExecutionError:
            raise
        except Exception as exc:
            raise ToolExecutionError(
                f'TOOL_EXECUTION_FAILED:{tool_name}:{type(exc).__name__}:{exc}'
            ) from exc

        if isinstance(result, ToolResult):
            return result

        return ToolResult(
            success=True,
            output=result,
            tool_name=tool_name,
        )

    def execute_many(self, calls, context):
        results = []
        for call in calls:
            name = call.get('tool_name')
            kwargs = call.get('kwargs', {})
            results.append(self.execute(name, context, **kwargs))
        return results

def run_stage3_execution_tests():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        context = ToolContext(root)
        system = ToolSystem(root)

        if hasattr(system, 'register'):
            try:
                system.register(ReadFileTool())
                system.register(WriteFileTool())
            except TypeError:
                pass

        layer = ToolExecutionLayer(system)

        write_result = layer.execute(
            'write_file',
            context,
            path='execution_test.txt',
            content='KHALED EXECUTION VERIFIED'
        )

        assert write_result.success is True
        assert (root / 'execution_test.txt').read_text() == 'KHALED EXECUTION VERIFIED'

        read_result = layer.execute(
            'read_file',
            context,
            path='execution_test.txt'
        )

        assert read_result.success is True
        assert read_result.output == 'KHALED EXECUTION VERIFIED'

        try:
            layer.execute(
                'missing_tool',
                context
            )
            raise AssertionError('MISSING_TOOL_NOT_BLOCKED')
        except ToolExecutionError as exc:
            assert 'TOOL_NOT_FOUND' in str(exc)

        assert layer.execution_count == 3
        return True


# ===== STAGE_4_RESEARCH_CONNECTIVITY =====

from dataclasses import dataclass as _Stage4Dataclass
from enum import Enum as _Stage4Enum
from typing import Any as _Stage4Any

class NetworkMode(_Stage4Enum):
    LOCAL_ONLY = 'local_only'
    ALLOW_NETWORK = 'allow_network'
    DISABLED = 'disabled'

@_Stage4Dataclass(frozen=True)
class NetworkBudget:
    max_requests: int = 10
    used_requests: int = 0

    def can_request(self):
        return self.used_requests < self.max_requests

    def consume(self, count=1):
        if count < 0:
            raise ValueError('INVALID_REQUEST_COUNT')
        if self.used_requests + count > self.max_requests:
            raise RuntimeError('NETWORK_BUDGET_EXCEEDED')
        return NetworkBudget(
            max_requests=self.max_requests,
            used_requests=self.used_requests + count,
        )

class LocalFirstRouter:
    def __init__(self, network_mode=NetworkMode.LOCAL_ONLY, budget=None):
        self.network_mode = network_mode
        self.budget = budget or NetworkBudget()

    def should_use_network(self, network_required=False):
        if self.network_mode in (NetworkMode.DISABLED, NetworkMode.LOCAL_ONLY):
            return False
        if not network_required:
            return False
        return self.budget.can_request()

    def consume_network(self):
        self.budget = self.budget.consume()

class ResearchResult:
    def __init__(self, query, results=None, source='local', success=True, error=None):
        self.query = query
        self.results = list(results or [])
        self.source = source
        self.success = success
        self.error = error

    def to_dict(self):
        return {
            'query': self.query,
            'results': self.results,
            'source': self.source,
            'success': self.success,
            'error': self.error,
        }

class WebResearch:
    def __init__(self, router=None, fetcher=None):
        self.router = router or LocalFirstRouter()
        self.fetcher = fetcher

    def search(self, query, network_required=False):
        query = str(query).strip()
        if not query:
            return ResearchResult(
                query='',
                source='local',
                success=False,
                error='EMPTY_QUERY',
            )

        if not self.router.should_use_network(network_required):
            return ResearchResult(
                query=query,
                source='local',
                success=True,
                results=[],
            )

        if self.fetcher is None:
            return ResearchResult(
                query=query,
                source='network',
                success=False,
                error='NO_NETWORK_FETCHER',
            )

        self.router.consume_network()

        try:
            results = self.fetcher(query)
            return ResearchResult(
                query=query,
                source='network',
                success=True,
                results=results or [],
            )
        except Exception as exc:
            return ResearchResult(
                query=query,
                source='network',
                success=False,
                error=f'{type(exc).__name__}:{exc}',
            )

class GitHubReadOnly:
    def __init__(self, fetcher=None):
        self.fetcher = fetcher

    def get_file(self, repo, path, ref='main'):
        if self.fetcher is None:
            return {
                'success': False,
                'repo': repo,
                'path': path,
                'ref': ref,
                'error': 'NO_GITHUB_FETCHER',
            }

        try:
            data = self.fetcher(repo, path, ref)
            return {
                'success': True,
                'repo': repo,
                'path': path,
                'ref': ref,
                'data': data,
            }
        except Exception as exc:
            return {
                'success': False,
                'repo': repo,
                'path': path,
                'ref': ref,
                'error': f'{type(exc).__name__}:{exc}',
            }

class UniversalConnector:
    def __init__(self):
        self.connectors = {}

    def register(self, name, connector):
        if not name:
            raise ValueError('CONNECTOR_NAME_REQUIRED')
        self.connectors[name] = connector

    def available(self, name):
        return name in self.connectors

    def get(self, name):
        return self.connectors.get(name)

def run_stage4_tests():
    budget = NetworkBudget(max_requests=2)
    assert budget.can_request() is True
    budget = budget.consume()
    assert budget.used_requests == 1
    budget = budget.consume()
    assert budget.used_requests == 2
    assert budget.can_request() is False

    router = LocalFirstRouter(NetworkMode.LOCAL_ONLY, budget)
    assert router.should_use_network(True) is False

    research = WebResearch(router=router)
    result = research.search('test query', network_required=True)
    assert result.success is True
    assert result.source == 'local'
    assert result.results == []

    calls = []
    def fake_fetch(query):
        calls.append(query)
        return [{'title': 'verified'}]

    network_router = LocalFirstRouter(
        NetworkMode.ALLOW_NETWORK,
        NetworkBudget(max_requests=1),
    )
    live_research = WebResearch(
        router=network_router,
        fetcher=fake_fetch,
    )
    live = live_research.search('hello', network_required=True)
    assert live.success is True
    assert live.source == 'network'
    assert live.results[0]['title'] == 'verified'
    assert calls == ['hello']
    assert network_router.budget.used_requests == 1

    github = GitHubReadOnly(
        fetcher=lambda repo, path, ref: 'content'
    )
    gh = github.get_file('owner/repo', 'README.md', 'main')
    assert gh['success'] is True
    assert gh['data'] == 'content'

    connector = UniversalConnector()
    connector.register('test', object())
    assert connector.available('test') is True
    assert connector.available('missing') is False

    return True


# ===== STAGE_5_UNIVERSAL_AI_GATEWAY =====

class AIProvider:
    def __init__(self, name, model=None, executor=None, enabled=True):
        self.name = name
        self.model = model
        self.executor = executor
        self.enabled = enabled

    def available(self):
        return self.enabled and self.executor is not None

    def execute(self, prompt, **kwargs):
        if not self.enabled:
            raise RuntimeError('PROVIDER_DISABLED')
        if self.executor is None:
            raise RuntimeError('PROVIDER_NOT_CONFIGURED')
        return self.executor(prompt, **kwargs)

class ProviderRegistry:
    def __init__(self):
        self.providers = {}

    def register(self, provider):
        if not provider.name:
            raise ValueError('PROVIDER_NAME_REQUIRED')
        self.providers[provider.name] = provider

    def get(self, name):
        return self.providers.get(name)

    def list_available(self):
        return [
            name for name, provider in self.providers.items()
            if provider.available()
        ]

class ModelSelector:
    def select(self, registry, preferred=None):
        if preferred:
            provider = registry.get(preferred)
            if provider is not None and provider.available():
                return provider
        for provider in registry.providers.values():
            if provider.available():
                return provider
        return None

class AIGateway:
    def __init__(self, registry=None, selector=None):
        self.registry = registry or ProviderRegistry()
        self.selector = selector or ModelSelector()

    def register(self, provider):
        self.registry.register(provider)

    def providers(self):
        return self.registry.list_available()

    def execute(self, prompt, provider=None, **kwargs):
        if provider is not None:
            selected = self.registry.get(provider)
            if selected is None:
                raise RuntimeError('NO_AI_PROVIDER_AVAILABLE')
            if not selected.available():
                raise RuntimeError('NO_AI_PROVIDER_AVAILABLE')
        else:
            selected = self.selector.select(self.registry)

        if selected is None:
            raise RuntimeError('NO_AI_PROVIDER_AVAILABLE')

        return selected.execute(prompt, **kwargs)

def run_stage5_tests():
    registry = ProviderRegistry()

    fake = AIProvider(
        name='test-provider',
        model='test-model',
        executor=lambda prompt, **kwargs: 'AI:' + prompt
    )

    registry.register(fake)
    assert registry.get('test-provider') is fake
    assert registry.list_available() == ['test-provider']

    selector = ModelSelector()
    selected = selector.select(registry, 'test-provider')
    assert selected is fake

    gateway = AIGateway(registry, selector)
    result = gateway.execute('hello', provider='test-provider')
    assert result == 'AI:hello'

    disabled = AIProvider(
        name='disabled-provider',
        model='disabled-model',
        executor=lambda prompt: 'bad',
        enabled=False
    )
    registry.register(disabled)
    assert registry.get('disabled-provider').available() is False

    try:
        gateway.execute('hello', provider='disabled-provider')
        raise AssertionError('DISABLED_PROVIDER_NOT_BLOCKED')
    except RuntimeError as exc:
        assert str(exc) == 'NO_AI_PROVIDER_AVAILABLE'

    empty = AIGateway()
    try:
        empty.execute('hello')
        raise AssertionError('EMPTY_GATEWAY_NOT_BLOCKED')
    except RuntimeError as exc:
        assert str(exc) == 'NO_AI_PROVIDER_AVAILABLE'

    return True


# ===== STAGE_6_CONTEXT_RESOURCE_INTELLIGENCE =====

class ContextItem:
    def __init__(self, key, value, priority=0, size=None):
        self.key = str(key)
        self.value = value
        self.priority = int(priority)
        self.size = self._estimate(value) if size is None else int(size)

    @staticmethod
    def _estimate(value):
        if value is None:
            return 0
        if isinstance(value, str):
            return len(value)
        if isinstance(value, (list, tuple, set, dict)):
            return len(str(value))
        return len(str(value))

class TokenEstimator:
    def estimate(self, value):
        if value is None:
            return 0
        if isinstance(value, str):
            return max(1, (len(value) + 3) // 4)
        return max(1, (len(str(value)) + 3) // 4)

class ContextBudget:
    def __init__(self, max_tokens=4096):
        if int(max_tokens) <= 0:
            raise ValueError('INVALID_CONTEXT_BUDGET')
        self.max_tokens = int(max_tokens)
        self.used_tokens = 0

    def can_fit(self, tokens):
        return self.used_tokens + int(tokens) <= self.max_tokens

    def reserve(self, tokens):
        tokens = int(tokens)
        if tokens < 0:
            raise ValueError('INVALID_TOKEN_COUNT')
        if not self.can_fit(tokens):
            return False
        self.used_tokens += tokens
        return True

    @property
    def remaining(self):
        return self.max_tokens - self.used_tokens

class ContextCache:
    def __init__(self, max_items=128):
        self.max_items = max(1, int(max_items))
        self._items = {}

    def get(self, key, default=None):
        return self._items.get(key, default)

    def set(self, key, value):
        if key in self._items:
            self._items[key] = value
            return
        if len(self._items) >= self.max_items:
            first_key = next(iter(self._items))
            del self._items[first_key]
        self._items[key] = value

    def clear(self):
        self._items.clear()

    def __len__(self):
        return len(self._items)

class SmartContext:
    def __init__(self, estimator=None, budget=None, cache=None):
        self.estimator = estimator or TokenEstimator()
        self.budget = budget or ContextBudget()
        self.cache = cache or ContextCache()

    def add(self, key, value, priority=0):
        tokens = self.estimator.estimate(value)

        if not self.budget.can_fit(tokens):
            return False

        item = ContextItem(
            key=key,
            value=value,
            priority=priority,
            size=tokens,
        )

        self.budget.reserve(tokens)
        self.cache.set(key, item)
        return True

    def get(self, key, default=None):
        item = self.cache.get(key)
        if item is None:
            return default
        return item.value

    def snapshot(self):
        items = []
        for item in self.cache._items.values():
            items.append({
                'key': item.key,
                'value': item.value,
                'priority': item.priority,
                'size': item.size,
            })
        items.sort(
            key=lambda x: (-x['priority'], x['key'])
        )
        return items

class EfficientContextCycle:
    def __init__(self, context):
        self.context = context

    def build(self, items):
        selected = []

        ordered = sorted(
            items,
            key=lambda x: -int(x.get('priority', 0))
        )

        for item in ordered:
            if self.context.add(
                item.get('key'),
                item.get('value'),
                item.get('priority', 0)
            ):
                selected.append(item.get('key'))

        return selected

class ResourceAwareEngine:
    def __init__(self, context=None):
        self.context = context or SmartContext()

    def resource_state(self):
        return {
            'max_tokens': self.context.budget.max_tokens,
            'used_tokens': self.context.budget.used_tokens,
            'remaining_tokens': self.context.budget.remaining,
            'cached_items': len(self.context.cache),
        }

class PersistentResourceGateway:
    def __init__(self, store=None):
        self.store = store

    def save(self, key, value):
        if self.store is None:
            return False

        if hasattr(self.store, 'set'):
            self.store.set(key, value)
            return True

        if hasattr(self.store, 'save'):
            self.store.save(key, value)
            return True

        return False

    def load(self, key, default=None):
        if self.store is None:
            return default

        if hasattr(self.store, 'get'):
            return self.store.get(key, default)

        if hasattr(self.store, 'load'):
            return self.store.load(key, default)

        return default

def run_stage6_tests():
    estimator = TokenEstimator()
    assert estimator.estimate('abcd') == 1
    assert estimator.estimate('abcdefgh') == 2

    budget = ContextBudget(max_tokens=5)
    assert budget.can_fit(3) is True
    assert budget.reserve(3) is True
    assert budget.used_tokens == 3
    assert budget.remaining == 2
    assert budget.reserve(3) is False

    cache = ContextCache(max_items=2)
    cache.set('a', 1)
    cache.set('b', 2)
    cache.set('c', 3)
    assert len(cache) == 2
    assert cache.get('a') is None
    assert cache.get('c') == 3

    context = SmartContext(
        estimator=TokenEstimator(),
        budget=ContextBudget(max_tokens=10),
        cache=ContextCache(),
    )

    assert context.add('important', '123456', priority=10)
    assert context.get('important') == '123456'

    cycle = EfficientContextCycle(
        SmartContext(
            budget=ContextBudget(max_tokens=4)
        )
    )

    selected = cycle.build([
        {'key': 'low', 'value': '12345678', 'priority': 1},
        {'key': 'high', 'value': '12345678', 'priority': 10},
        {'key': 'extra', 'value': '12345678', 'priority': 0},
    ])

    assert selected[:2] == ['high', 'low']
    assert 'extra' not in selected

    resource = ResourceAwareEngine(context)
    state = resource.resource_state()
    assert 'remaining_tokens' in state
    assert state['used_tokens'] > 0

    gateway = PersistentResourceGateway()
    assert gateway.save('x', 1) is False
    assert gateway.load('x', 'default') == 'default'

    return True


# ===== STAGE_7_AUTONOMY_SELF_REPAIR =====

class ErrorAnalysis:
    def __init__(self, error=None, category=None, retryable=True, severity='medium'):
        self.error = error
        self.category = category or self._classify(error)
        self.retryable = bool(retryable)
        self.severity = severity

    @staticmethod
    def _classify(error):
        if error is None:
            return 'none'

        text = str(error).lower()

        if 'permission' in text or 'denied' in text:
            return 'permission'
        if 'timeout' in text:
            return 'timeout'
        if 'network' in text or 'connection' in text:
            return 'network'
        if 'not found' in text or 'missing' in text:
            return 'missing_resource'
        if 'syntax' in text or 'compile' in text:
            return 'syntax'
        if 'validation' in text or 'invalid' in text:
            return 'validation'
        return 'unknown'

    def as_dict(self):
        return {
            'error': None if self.error is None else str(self.error),
            'category': self.category,
            'retryable': self.retryable,
            'severity': self.severity,
        }

class RecoveryAction:
    def __init__(self, name, action=None, max_attempts=1):
        self.name = str(name)
        self.action = action
        self.max_attempts = max(1, int(max_attempts))

    def execute(self):
        if self.action is None:
            return True
        result = self.action()
        return True if result is None else bool(result)

class RecoveryEngine:
    def __init__(self, max_retries=2):
        self.max_retries = max(0, int(max_retries))
        self.history = []

    def recover(self, error, actions=None):
        analysis = error if isinstance(error, ErrorAnalysis) else ErrorAnalysis(error)

        if not analysis.retryable:
            self.history.append({
                'category': analysis.category,
                'status': 'blocked',
            })
            return False

        actions = list(actions or [])

        for action in actions:
            attempts = 0
            while attempts < action.max_attempts:
                attempts += 1
                try:
                    if action.execute():
                        self.history.append({
                            'action': action.name,
                            'attempts': attempts,
                            'status': 'recovered',
                        })
                        return True
                except Exception as exc:
                    self.history.append({
                        'action': action.name,
                        'attempts': attempts,
                        'status': 'failed',
                        'error': str(exc),
                    })

        self.history.append({
            'category': analysis.category,
            'status': 'unrecovered',
        })
        return False

class RepairPlanner:
    def __init__(self):
        self.plan_history = []

    def plan(self, error):
        analysis = error if isinstance(error, ErrorAnalysis) else ErrorAnalysis(error)

        if analysis.category == 'permission':
            actions = ['check_permission', 'retry']
        elif analysis.category == 'network':
            actions = ['retry', 'use_local_fallback']
        elif analysis.category == 'timeout':
            actions = ['retry_with_limit', 'fallback']
        elif analysis.category == 'missing_resource':
            actions = ['verify_resource', 'recover_resource']
        elif analysis.category == 'syntax':
            actions = ['validate_source', 'repair_source']
        elif analysis.category == 'validation':
            actions = ['revalidate', 'repair_input']
        else:
            actions = ['retry', 'diagnose', 'fallback']

        plan = {
            'category': analysis.category,
            'actions': actions,
            'retryable': analysis.retryable,
        }

        self.plan_history.append(plan)
        return plan

class RepairExecutor:
    def __init__(self, recovery=None):
        self.recovery = recovery or RecoveryEngine()
        self.execution_history = []

    def execute(self, plan, handlers=None):
        handlers = dict(handlers or {})

        for action_name in plan.get('actions', []):
            handler = handlers.get(action_name)

            if handler is None:
                continue

            action = RecoveryAction(
                name=action_name,
                action=handler,
                max_attempts=1,
            )

            if self.recovery.recover(
                ErrorAnalysis(
                    category=plan.get('category'),
                    retryable=plan.get('retryable', True),
                ),
                [action],
            ):
                self.execution_history.append({
                    'action': action_name,
                    'status': 'success',
                })
                return True

        self.execution_history.append({
            'status': 'failed',
        })
        return False

class AutonomousLoop:
    def __init__(
        self,
        recovery=None,
        planner=None,
        executor=None,
        max_cycles=3,
    ):
        self.recovery = recovery or RecoveryEngine()
        self.planner = planner or RepairPlanner()
        self.executor = executor or RepairExecutor(self.recovery)
        self.max_cycles = max(1, int(max_cycles))
        self.history = []

    def run(self, task, handlers=None):
        last_error = None

        for cycle in range(1, self.max_cycles + 1):
            try:
                result = task()
                self.history.append({
                    'cycle': cycle,
                    'status': 'success',
                })
                return {
                    'success': True,
                    'result': result,
                    'cycles': cycle,
                }
            except Exception as exc:
                last_error = exc
                analysis = ErrorAnalysis(exc)
                plan = self.planner.plan(analysis)

                self.history.append({
                    'cycle': cycle,
                    'status': 'error',
                    'analysis': analysis.as_dict(),
                })

                if not analysis.retryable:
                    break

                repaired = self.executor.execute(
                    plan,
                    handlers=handlers,
                )

                if not repaired and cycle >= self.max_cycles:
                    break

        return {
            'success': False,
            'error': None if last_error is None else str(last_error),
            'cycles': len(self.history),
        }

def run_stage7_tests():
    analysis = ErrorAnalysis(
        RuntimeError('network timeout'),
    )

    assert analysis.category == 'timeout'
    assert analysis.retryable is True
    assert isinstance(analysis.as_dict(), dict)

    blocked = ErrorAnalysis(
        RuntimeError('permission denied'),
        retryable=False,
    )

    recovery = RecoveryEngine(max_retries=2)
    assert recovery.recover(blocked) is False

    planner = RepairPlanner()
    plan = planner.plan(
        ErrorAnalysis(RuntimeError('network connection failed'))
    )

    assert plan['category'] == 'network'
    assert 'retry' in plan['actions']

    calls = []

    def repair_handler():
        calls.append('repair')
        return True

    executor = RepairExecutor()
    assert executor.execute(
        {'category': 'network', 'actions': ['retry'], 'retryable': True},
        {'retry': repair_handler},
    ) is True

    assert calls == ['repair']

    attempts = {'count': 0}

    def task():
        attempts['count'] += 1
        if attempts['count'] < 2:
            raise RuntimeError('temporary network error')
        return 'SUCCESS'

    loop = AutonomousLoop(max_cycles=3)
    result = loop.run(
        task,
        {'retry': lambda: True},
    )

    assert result['success'] is True
    assert result['result'] == 'SUCCESS'
    assert attempts['count'] == 2

    permanent = AutonomousLoop(max_cycles=2)
    permanent_result = permanent.run(
        lambda: (_ for _ in ()).throw(RuntimeError('permanent failure')),
        {'retry': lambda: True},
    )

    assert permanent_result['success'] is False
    assert permanent_result['cycles'] >= 1

    return True


# ===== STAGE_8_HOT_SWAP_HEALTH_CAPABILITY =====

class ComponentStatus:
    ACTIVE = 'ACTIVE'
    DISABLED = 'DISABLED'
    FAILED = 'FAILED'
    REPLACED = 'REPLACED'
    NOT_CONFIGURED = 'NOT_CONFIGURED'
    UNKNOWN = 'UNKNOWN'

class ManagedComponent:
    def __init__(self, name, component, version='1.0', enabled=True):
        self.name = str(name)
        self.component = component
        self.version = str(version)
        self.enabled = bool(enabled)
        self.status = (
            ComponentStatus.ACTIVE
            if self.enabled
            else ComponentStatus.DISABLED
        )

class ComponentManager:
    def __init__(self):
        self.components = {}
        self.history = []

    def register(self, name, component, version='1.0', enabled=True):
        item = ManagedComponent(
            name=name,
            component=component,
            version=version,
            enabled=enabled,
        )
        self.components[item.name] = item
        self.history.append({
            'operation': 'register',
            'component': item.name,
            'version': item.version,
        })
        return item

    def get(self, name):
        return self.components.get(name)

    def status(self, name):
        item = self.get(name)
        if item is None:
            return ComponentStatus.UNKNOWN
        return item.status

    def disable(self, name):
        item = self.get(name)
        if item is None:
            return False
        item.enabled = False
        item.status = ComponentStatus.DISABLED
        self.history.append({
            'operation': 'disable',
            'component': name,
        })
        return True

    def enable(self, name):
        item = self.get(name)
        if item is None:
            return False
        item.enabled = True
        item.status = ComponentStatus.ACTIVE
        self.history.append({
            'operation': 'enable',
            'component': name,
        })
        return True

    def snapshot(self, name):
        item = self.get(name)
        if item is None:
            return None
        return {
            'name': item.name,
            'component': item.component,
            'version': item.version,
            'enabled': item.enabled,
            'status': item.status,
        }

    def restore(self, snapshot):
        if snapshot is None:
            return False

        item = ManagedComponent(
            name=snapshot['name'],
            component=snapshot['component'],
            version=snapshot['version'],
            enabled=snapshot['enabled'],
        )
        item.status = snapshot['status']
        self.components[item.name] = item

        self.history.append({
            'operation': 'rollback',
            'component': item.name,
            'version': item.version,
        })
        return True

    def replace(self, name, component, version='1.0', verify=None):
        old = self.snapshot(name)

        if old is None:
            return {
                'success': False,
                'status': ComponentStatus.UNKNOWN,
                'rolled_back': False,
            }

        candidate = ManagedComponent(
            name=name,
            component=component,
            version=version,
            enabled=True,
        )

        self.components[name] = candidate

        verified = True

        if verify is not None:
            try:
                verified = bool(verify(candidate.component))
            except Exception:
                verified = False

        if verified:
            candidate.status = ComponentStatus.REPLACED
            self.history.append({
                'operation': 'replace',
                'component': name,
                'version': version,
                'status': 'verified',
            })
            return {
                'success': True,
                'status': ComponentStatus.REPLACED,
                'rolled_back': False,
            }

        self.restore(old)

        return {
            'success': False,
            'status': old['status'],
            'rolled_back': True,
        }

class ComponentHealth:
    def __init__(self):
        self.results = {}

    def check(self, name, component):
        try:
            if hasattr(component, 'health_check'):
                result = bool(component.health_check())
            elif callable(component):
                result = True
            else:
                result = component is not None

            self.results[name] = {
                'healthy': result,
                'status': 'healthy' if result else 'failed',
            }
            return result
        except Exception as exc:
            self.results[name] = {
                'healthy': False,
                'status': 'failed',
                'error': str(exc),
            }
            return False

    def is_healthy(self, name):
        return bool(
            self.results.get(name, {}).get('healthy', False)
        )

class ComponentFallback:
    def __init__(self):
        self.fallbacks = {}
        self.history = []

    def register(self, name, component):
        self.fallbacks[name] = component

    def get(self, name):
        return self.fallbacks.get(name)

    def recover(self, name):
        component = self.get(name)
        if component is None:
            return None
        self.history.append({
            'component': name,
            'status': 'fallback_selected',
        })
        return component

class CapabilityEngine:
    def __init__(self):
        self.capabilities = {}

    def register(self, component_name, capabilities):
        self.capabilities[component_name] = set(capabilities)

    def supports(self, component_name, capability):
        return capability in self.capabilities.get(component_name, set())

    def candidates(self, capability):
        result = []
        for name, capabilities in self.capabilities.items():
            if capability in capabilities:
                result.append(name)
        return result

    def select(self, capability, preferred=None):
        if preferred and self.supports(preferred, capability):
            return preferred

        candidates = self.candidates(capability)
        return candidates[0] if candidates else None

class ComponentRecovery:
    def __init__(
        self,
        manager,
        health=None,
        fallback=None,
        capability=None,
    ):
        self.manager = manager
        self.health = health or ComponentHealth()
        self.fallback = fallback or ComponentFallback()
        self.capability = capability or CapabilityEngine()
        self.history = []

    def recover(self, name, capability=None, verify=None):
        item = self.manager.get(name)

        if item is None:
            self.history.append({
                'component': name,
                'status': 'missing',
            })
            return False

        if self.health.check(name, item.component):
            self.history.append({
                'component': name,
                'status': 'already_healthy',
            })
            return True

        candidate_name = self.capability.select(
            capability,
            preferred=name,
        ) if capability else None

        candidate = (
            self.fallback.get(name)
            if candidate_name is None
            else self.fallback.get(candidate_name)
        )

        if candidate is None:
            self.history.append({
                'component': name,
                'status': 'no_candidate',
            })
            return False

        result = self.manager.replace(
            name,
            candidate,
            version='recovered',
            verify=verify,
        )

        self.history.append({
            'component': name,
            'status': 'recovered' if result['success'] else 'failed',
            'rolled_back': result['rolled_back'],
        })

        return bool(result['success'])

def run_stage8_tests():
    class GoodComponent:
        def health_check(self):
            return True

    class BadComponent:
        def health_check(self):
            return False

    manager = ComponentManager()
    original = GoodComponent()

    manager.register(
        'planner',
        original,
        version='1.0',
    )

    assert manager.status('planner') == ComponentStatus.ACTIVE
    assert manager.get('planner').version == '1.0'

    health = ComponentHealth()
    assert health.check('planner', original) is True
    assert health.is_healthy('planner') is True

    fallback = ComponentFallback()
    replacement = GoodComponent()
    fallback.register('planner', replacement)
    assert fallback.get('planner') is replacement

    capabilities = CapabilityEngine()
    capabilities.register('planner', ['planning', 'execution'])
    capabilities.register('backup', ['planning'])

    assert capabilities.supports('planner', 'planning')
    assert capabilities.select('planning', 'planner') == 'planner'

    # Successful hot swap.
    result = manager.replace(
        'planner',
        replacement,
        version='2.0',
        verify=lambda component: component.health_check(),
    )

    assert result['success'] is True
    assert result['rolled_back'] is False
    assert manager.get('planner').version == '2.0'
    assert manager.get('planner').status == ComponentStatus.REPLACED

    # Failed verification MUST rollback.
    bad = BadComponent()
    failed = manager.replace(
        'planner',
        bad,
        version='broken',
        verify=lambda component: component.health_check(),
    )

    assert failed['success'] is False
    assert failed['rolled_back'] is True
    assert manager.get('planner').version == '2.0'
    assert manager.get('planner').component is replacement

    # Disabled components are represented explicitly.
    assert manager.disable('planner') is True
    assert manager.status('planner') == ComponentStatus.DISABLED
    assert manager.enable('planner') is True
    assert manager.status('planner') == ComponentStatus.ACTIVE

    # Recovery through fallback.
    broken = BadComponent()
    manager.replace(
        'planner',
        broken,
        version='broken',
        verify=lambda component: True,
    )

    # The intentionally broken component is now managed.
    manager.get('planner').status = ComponentStatus.FAILED

    recovery = ComponentRecovery(
        manager=manager,
        health=ComponentHealth(),
        fallback=fallback,
        capability=capabilities,
    )

    assert recovery.recover(
        'planner',
        verify=lambda component: component.health_check(),
    ) is True

    assert manager.get('planner').component is replacement

    # Failed replacement with a bad fallback must rollback.
    bad_fallback = BadComponent()
    fallback.register('planner', bad_fallback)

    manager.replace(
        'planner',
        broken,
        version='broken-again',
        verify=lambda component: True,
    )

    manager.get('planner').status = ComponentStatus.FAILED

    before = manager.snapshot('planner')

    assert recovery.recover(
        'planner',
        verify=lambda component: component.health_check(),
    ) is False

    after = manager.snapshot('planner')
    assert after['component'] is before['component']
    assert after['version'] == before['version']

    return True

