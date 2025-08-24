# API Analysis - Rust Agent Workflow

## Endpoint
`POST https://agent-workflow-993464051590.us-central1.run.app/v1/responses`

## Request Format
```json
{
    "input": "Can Tokio be used for non-networking applications?",
    "temperature": 0,
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 8192,
    "use_rag": true,
    "stream": true
}
```

## Response Format
- Uses Server-Sent Events (SSE) format with `data:` prefix
- Each response is a JSON object with these fields:

### Fields:
- **`is_final`**: Boolean - indicates if this is the final response
- **`event`**: String - event type (e.g., "workflow.started", "workflow.prompt", "workflow.cargo_check")  
- **`progress`**: Float - progress percentage (0.0-100.0)
- **`message`**: String - human-readable status message
- **`metadata`**: Object - additional context (session_id, timestamp, etc.)

### Event Types Observed:
1. `workflow.started` - Initial event (progress: 0.0)
2. `workflow.prompt` - Prompt processing stages (progress: 5.0-10.0)
3. `workflow.cargo_check` - Rust compilation check (potentially slow)
4. `response` - Final response generation (potentially slow)

### Display Strategy:
- Show `event`, `progress`, and `message` for intermediate steps (`is_final=false`)
- Only show final content when `is_final=true`
- `metadata` can be ignored for UI display
- Progress bar could use the `progress` field