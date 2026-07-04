# Gerfex Routing Audit V1

## Scope
This audit covers routing between GMA Native and Gerfex Python Core.

Files inspected:
- src/App.jsx
- android/app/src/main/java/com/mashel15/gerfex/GerfexPlugin.java

## Current routing entry point
The main routing decision is in src/App.jsx inside:

askGerfexNative(prompt, modelState = {})

Current behavior:
- If modelState.name is GMA, connected is true, hold is false, mute is false, and gmaNativeChat exists, the message goes to GMA Native.
- Otherwise the message goes to GerfexNative.think, which is the Python Core path.

## Main chat finding
In the main chat handler, modelState is always built with name = GMA.

Therefore, when GMA is connected and not muted/held, most main chat messages go to GMA Native.

This includes both:
- normal chat and factual questions
- possible Gerfex execution commands

## Learning finding
The Learning Session currently builds a forced GMA state with connected=true and sends:

[LEARNING_SESSION]\n + text

to askGerfexNative.

This means Learning Session discussion goes to GMA Native, while real learning approval/storage/governance must remain under Python Core.

## Plugin finding: Python Core
GerfexPlugin.java think() is the official Python Core path.

It:
- receives message and model_state
- starts embedded Python if needed
- imports gerfex_entry
- calls gerfex_entry.think(message, modelStateJson)
- executes native actions from result
- captures post-execution screen verification

## Plugin finding: GMA Native
GerfexPlugin.java gmaNativeChat() is the official GMA Native path.

It:
- receives message
- ensures the GMA model file
- calls GmaLlamaBridge.generateBlocking
- returns ok, engine, stage, bridge_stage, model info, and reply

Thrown exceptions return ok=false with debug metadata.

## Finding 1: routing is too broad
The current App.jsx routing is too broad.

It does not classify the message type before routing.

So commands like:
- افتح اليوتيوب
- افتح كروم
- ابحث عن كذا
- احفظ هذه المعلومة
- نفذ المهمة

may go to GMA Native instead of Python Core when GMA is enabled.

## Finding 2: App.jsx needs controlled routing improvement
The audit confirms that App.jsx is a routing decision point that needs a controlled improvement.

The change should be small:
- no UI redesign
- no JNI change
- no GmaLlamaBridge change
- no Python Core redesign
- add a simple route classifier before calling GMA or think

## Finding 3: GMA error handling can improve
gmaNativeChat() returns ok=false for thrown exceptions.

But if the native bridge returns a textual error as reply, App.jsx may display it as a normal GMA reply.

Examples:
- GMA_LLAMA_ERROR
- GMA_LLAMA_EMPTY_REPLY
- no_backend_loaded
- model_load_null
- context_null

Preferred fix later:
Handle these as structured GMA errors close to the native route, preferably in GerfexPlugin.java.

## Recommended routing policy
Send to GMA Native:
- greetings
- general chat
- factual questions
- explanations
- normal knowledge prompts

Send to Python Core:
- Android/device commands
- opening apps
- search workflows
- memory commands
- learning approval/storage/governance
- execution planning
- mixed tasks requiring orchestration

Mixed execution-heavy prompts should go first to Python Core.

## Next step
Create ROUTING_POLICY_V1.md, then prepare one controlled patch after approval.
