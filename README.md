# Gerfex

Gerfex is a personal sovereign AI assistant project.

## Components

- GerfexIntegratedV1: core, brain, memory, learning, runtime, API, Android bridge.
- GerfexReactUI: React/Vite user interface.

## Current Status

Release V1 verified.

## Run

API:

```bash
cd GerfexIntegratedV1
python api/gerfex_api.py
cd GerfexIntegratedV1
python runtime/queue_runner.py
cd GerfexReactUI
npm install
npm run dev -- --host
