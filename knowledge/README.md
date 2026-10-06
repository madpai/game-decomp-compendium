# Field notes (this repository's own)

Agent-written notes in the same format as [universal-modder](https://github.com/rehan-remade/universal-modder)'s `knowledge/` (so any of them can be offered upstream, with the user's approval). Each note records versions, route, what the engine really does, how it was verified, and numbered gotchas (symptom -> cause -> fix). They are indexed into `skills/gamedecomp-library/data/local-notes.json` and searched by `hub.py` together with the upstream notes.

Add a note whenever you learned something the next agent would lose an hour to, including dead ends. Template and rules: `skills/gamedecomp-library/references/agent-method.md`. Hard rules: no game files or assets, no pasted decompiled code, no addresses/tables dumped from executables, no secrets, honest status, name the agent.

Rebuild the index after editing: `python3 skills/gamedecomp-library/scripts/refresh/index_local_notes.py`.
