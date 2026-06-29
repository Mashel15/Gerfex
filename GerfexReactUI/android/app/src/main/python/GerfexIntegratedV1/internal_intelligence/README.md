# Internal Intelligence

This folder contains the internal intelligence layer for Gerfex.

The active internal intelligence provider is replaceable.

System-wide code must refer to this layer as:
internal_intelligence / الذكاء الداخلي

Version-specific provider files must stay inside the provider layer.

Learning rule:
- Pending lessons may be proposed silently.
- No lesson affects behavior until Mashel explicitly approves it.
- Approved knowledge is stored separately.
- Provider version names must not leak into user-facing areas unless explicitly intended.
