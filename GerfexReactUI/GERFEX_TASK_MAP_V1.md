# GERFEX TASK MAP V1

## Active intents found
- open_app
- web_search
- news_research_pipeline
- cognitive

## Active action types found
- open_app
- open_url
- wait
- observe_screen / dump_ui
- tap
- type_text
- press_home
- press_back

## Confirmed active path
User goal
-> gerfex_entry.py
-> core/gerfex_core.py
-> brain/brain_router.py
-> brain/brain_manager.py
-> brain/providers/queen_provider.py
-> core/execution_manager.py
-> android/android_bridge.py
-> GerfexPlugin.java
-> Android / Accessibility

## Main problem
Some capabilities exist but are not connected to the active path.

## Must be unified before Queen/external AI
1. App control
2. Web search
3. Search verification
4. Screen observation
5. Tap/type planning
6. Result reading
7. Memory
8. Learning
9. Voice
10. Final verified reply

## Route status
- android: partially working
- queen: simple provider only
- research: broken/suspicious because autonomous_loop.py is missing
- cognitive: exists but not clearly connected to main command flow
- verification: exists but not connected after Java execution

## Rule
No task should be marked successful until Java execution and screen verification confirm it.
