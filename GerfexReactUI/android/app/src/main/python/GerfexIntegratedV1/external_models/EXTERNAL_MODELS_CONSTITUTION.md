# External Models Constitution V1

External Models are an independent subsystem inside Gerfex.

## Core Rule
External models must not directly access, modify, or call Gerfex core subsystems.

Forbidden direct access includes:
- core
- brain
- memory
- runtime
- android
- voice
- learning
- safety
- vision

## Approved Path
Every external model request must follow this path:

External Model
→ external_models request
→ Gerfex External Gateway
→ target subsystem
→ Gerfex External Gateway
→ external_models
→ External Model

## Identity Rule
When Internal Brain is OFF and an external model responds directly, it must speak using its own provider name.
It must not claim to be Gerfex.
It must not claim to be Internal Brain.

## Permission Rule
If an external model needs a Gerfex capability, it must submit a request first.
Gerfex decides whether to allow, deny, or route the request.

## Debug Rule
Any issue must be traceable through:
external_models → Gerfex gateway → subsystem → Gerfex gateway → external_models
