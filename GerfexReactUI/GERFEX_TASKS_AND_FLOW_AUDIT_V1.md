# GERFEX TASKS AND FLOW AUDIT V1

## Confirmed runtime path
gerfex_entry.py
-> core/gerfex_core.py
-> brain/brain_router.py
-> brain/brain_manager.py
-> brain/providers/queen_provider.py
-> core/execution_manager.py
-> android/android_bridge.py
-> GerfexPlugin.java
-> Android / Accessibility

## Important finding
Python execution does not execute phone actions directly.
It only creates native_actions.

Java GerfexPlugin executes native_actions after Python returns.

Current UI reply is based on Python decision/execution before final screen verification.

## Current success levels
1. execution_manager.py ok = native action created
2. GerfexPlugin executeAction ok = Android intent/accessibility call returned true
3. Missing: verified result on screen

## Confirmed issue
Search command may say "Gerfex opened Chrome and searched",
but actual phone may only open Chrome or send URL intent without verified search results.

## Broken / suspicious route
core/gerfex_core.py research route imports:
from autonomous.autonomous_loop import run_autonomous_goal

But autonomous/autonomous_loop.py is missing.
Only .pyc or legacy/autonomous files exist.

## Existing capability folders
- research/
- verification/
- observation/
- understanding/
- planner/
- cognitive/
- vision/
- tools/search/
- memory/
- learning/
- runtime/
- android/
- brain/
- core/

## Architectural rule before Queen/external AI
Gerfex Core must remain the manager.
Queen is a brain/advisor provider, not the Android executor.
External AI is optional helper for reasoning/summarization.
Java Plugin is the actual Android executor.
Verification must happen after Java execution and screen observation.

## Next required stage
GERFEX TASK MAP AND ROUTE UNIFICATION V1

Goals:
1. List every Gerfex task.
2. Assign one approved live file/path for each task.
3. Mark legacy/missing/pycache-only paths as inactive.
4. Fix router/core so each route calls the correct live module.
5. Add final verification stage after Java execution.
6. Make UI reply reflect verified outcome, not just planned decision.
