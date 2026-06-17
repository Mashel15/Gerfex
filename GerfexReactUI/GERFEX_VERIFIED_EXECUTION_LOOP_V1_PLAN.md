# GERFEX VERIFIED EXECUTION LOOP V1 PLAN

## Problem
Gerfex currently replies based on planned decision or native action creation.

This is not enough.

## Current flow
Python creates native_actions.
Java GerfexPlugin executes native_actions.
UI receives the original Python reply.
No final screen verification is used.

## Required flow
Plan
-> Execute by Java Plugin
-> Observe screen
-> Verify result
-> Return verified reply

## First implementation target
GerfexPlugin.java

After executeFromResult(result):
1. Capture screen text again.
2. Add plugin verification stage to trace.
3. Return verification info to UI.
4. Later update UI reply to prefer verified outcome.

## Rule
No web_search task should be called successful until screen text confirms the target/search result.
No open_app task should be called successful until execution is confirmed by Java Plugin.
