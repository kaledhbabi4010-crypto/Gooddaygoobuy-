
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

