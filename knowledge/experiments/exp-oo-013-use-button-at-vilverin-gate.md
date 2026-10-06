---
id: EXP-OO-013
title: "USE does nothing at the Vilverin hall gate: touch overlay layout and the same-cell door handler"
project: openoblivion
result: partial
level: inferred
why_level: inferred
scope: project
status: final
date: 2026-10-01
agents: ["Claude Code (Sonnet 5.5), recorded from project docs"]
about: [problem:touch-overlay-blocks-actions, subsystem:input-ui, engine:openmw]
games: [game:oblivion]
tags: [touch, overlay, use, activation, door, hit-testing]
related: [EXP-OO-009]
---

# USE does nothing at the Vilverin hall gate: touch overlay layout and the same-cell door handler

## Symptom
Phone report on build 0.10-touch-name: the player came down the Vilverin hall stairs and stopped at the gate while the centre ray read `Gate` (a DOOR record); the log has no activation line. The thirteen-button touch overlay covered the right half of the screen, including USE.

## Hypothesis
Two causes. The USE button was covered or hard to reach, so the activation never arrived. Separately, the engine's activation handler for a same-cell door has no animation: it hides the object for five seconds and shows it again, so even a delivered activation does not look like opening.

## Environment
OpenOblivion phone build 0.10, owner's phone report with log; the 0.51 activation handler; the touch layout test on four screen sizes.

## Change
The closed overlay was reduced to a move stick plus USE, JUMP, ATK and MORE (the rest on a tray), and the packer rewrites the same-cell door handler into a toggle (first USE hides the closed mesh until the next USE). A successful USE logs `OPENOBLIVION_DOOR`. Playing the original Open and Close sequences came later as separate work.

## Oracle
The presence of an `OPENOBLIVION_DOOR` line in the phone log after USE, and a layout test that checks the button cluster on four resolutions. Tap logging (`OPENOBLIVION_UI tap`) separates a tap that never arrived from a tap that did nothing.

## Result
Partial. The layout change and the toggle are in and tested at the layout level. No phone retest was recorded when this was written, so it is not established that the covered button was the blocker.

## Why
Inferred from the missing log line and the layout. The door handler's behaviour was read from the engine's own handler. Neither cause was reproduced independently.

## Next
When a touch action does nothing, check in this order: is there an action log line at all (event never arrived versus handler did nothing), do overlay hit areas cover or swallow the control, and what does the engine's default handler for that object type do. Retest on the phone with the reduced overlay.

## Unverified
Whether the overlay was the blocker; whether USE reaches the handler on the phone; other door types.
