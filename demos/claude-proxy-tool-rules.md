# Claude Code Proxy Tool Rules

When using a non-Anthropic model through the local proxy, be strict about tool inputs:

- Never call a tool with `{}` if its schema has required fields.
- For `Bash`, always include `command` as a non-empty string.
- For `Read`, always include `file_path` as a non-empty string.
- For `Grep`, always include `pattern`.
- For `Glob`, always include `pattern`.
- If a required parameter is unknown, ask for clarification instead of calling the tool.
- Return tool input as one complete JSON object that matches the tool schema.
