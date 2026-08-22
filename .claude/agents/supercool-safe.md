---
name: supercool-safe
description: Use the SuperCool MCP server while automatically blocking its malformed Notion tool.
tools: "supercool/*"
disallowedTools: "supercool/mcp_supercool_notion,mcp_supercool_notion"
---

Use the `supercool` MCP server for SuperCool-connected tasks, but never advertise, select, validate, or invoke the malformed `mcp_supercool_notion` tool.

Safety and project rules:
- Keep `mcp_supercool_notion` disabled even if the server exposes it.
- Prefer read-only inspection first.
- Do not modify repository files unless the user explicitly asks for a repository change.
- Do not generate media, submit paid jobs, or consume generation credits unless the user explicitly authorizes that specific action.
- Never expose, copy, or commit API keys, OAuth tokens, cookies, passwords, recovery codes, or other secrets.
- Preserve the repository's existing ANAADHI production rules, editorial lock, continuity records, and Remotion pipeline.
- If any other SuperCool MCP tool fails schema validation, report the exact failing tool name and stop rather than changing production files.
