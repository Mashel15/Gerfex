# Gerfex Release

Created: 20260611_230731

## Components
- GerfexIntegratedV1: core, brain, memory, learning, runtime, API, Android bridge
- GerfexReactUI: React/Vite user interface

## Run
API:
cd ~/GerfexIntegratedV1
python api/gerfex_api.py

Runner:
cd ~/GerfexIntegratedV1
python runtime/queue_runner.py

UI:
cd ~/GerfexReactUI
npm run dev -- --host
