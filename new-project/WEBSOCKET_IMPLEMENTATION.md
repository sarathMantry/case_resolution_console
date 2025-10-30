# WebSocket Implementation for Real-Time Triage Streaming

## Overview
Implemented WebSocket support to stream triage execution updates in real-time, replacing the static REST API fetch with progressive data streaming.

## Backend Changes

### 1. Dependencies (`backend/requirements.txt`)
- Added `websockets>=11.0.0` package for WebSocket support

### 2. Triage Routes (`backend/app/routes/triage_routes.py`)
Added new WebSocket endpoint:
```python
@router.websocket("/ws/{alert_id}")
async def triage_stream(websocket: WebSocket, alert_id: str)
```

#### WebSocket Message Types:
1. **status**: Connection status and progress messages
2. **alert**: Alert basic information (id, customer_id, status, created_at)
3. **risk**: Risk assessment and recommended action
4. **transaction**: Transaction details
5. **reasons**: Risk reasons array
6. **tool_call**: Individual tool execution (sent twice: once as "running", once completed)
7. **citations**: Policy citations
8. **complete**: Final completion message with latency
9. **error**: Error messages

#### Streaming Behavior:
- Sends messages progressively with realistic delays (0.2-1.0 seconds)
- Simulates tool execution by sending each tool call twice:
  - First with `status: "running"` (before execution simulation)
  - Then with actual completion data after delay
- Uses actual duration_ms from database to simulate realistic timing
- Properly handles connection lifecycle (accept, send, close)

## Frontend Changes

### 3. TriageDrawer Component (`frontend/src/components/TriageDrawer.tsx`)

#### New State Variables:
- `wsRef`: React ref to hold WebSocket connection
- `streamingMessage`: Current streaming status message
- `runningToolIndex`: Index of currently executing tool call

#### WebSocket Connection:
```typescript
const ws = new WebSocket(`ws://localhost:3000/api/triage/ws/${alertId}`);
```

#### Key Features:
1. **Progressive Data Loading**: Updates UI as each message arrives
2. **Running Tool Animation**: 
   - Shows pulsing blue background for currently executing tool
   - Displays "running..." label next to tool name
   - Animated ping effect on status dot
3. **Status Messages**: Shows real-time progress messages during streaming
4. **Connection Management**: 
   - Opens connection when drawer opens
   - Closes connection when drawer closes
   - Cleans up on unmount

#### Visual Indicators:
- **Loading State**: Spinner with streaming message below
- **Running Tools**: Blue pulsing background with animated dot
- **Completed Tools**: Green (success) or red (error) background
- **Streaming Messages**: Displayed in Tool Execution header with blue pulse

#### Message Handling:
```typescript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  switch (message.type) {
    case 'status': setStreamingMessage(message.message); break;
    case 'alert': // Update alert data
    case 'risk': // Update risk assessment
    case 'tool_call': // Add/update tool execution
    // ... etc
  }
}
```

## User Experience Improvements

### Before (REST API):
- Static loading spinner
- All data appears at once
- No visibility into what's happening
- No sense of progress

### After (WebSocket):
1. **Connection Phase**: "Connecting..."
2. **Alert Loading**: "Connected. Starting triage..."
3. **Risk Analysis**: "Alert loaded. Analyzing risk..."
4. **Transaction Data**: "Risk assessed. Loading transaction..."
5. **Reason Analysis**: "Transaction loaded. Analyzing reasons..."
6. **Tool Execution**: "Reasons identified. Executing tools..."
   - Each tool appears one by one
   - Running tools show animated status
   - Duration displayed after completion
7. **Policy Citations**: "Loading policy citations..."
8. **Completion**: All data loaded, streaming stops

## Testing Results

### Backend Logs:
```
INFO: WebSocket /api/triage/ws/e887b64f-7e6b-4964-8a3f-e9b29e5bf3e4 [accepted]
INFO: connection open
INFO: connection closed
```

### Observations:
- WebSocket connections established successfully
- Messages streamed progressively as designed
- Clean connection open/close cycle
- No connection errors or timeouts
- Tool calls appear one by one with running animation

## Technical Benefits

1. **Real-Time Updates**: Users see progress as it happens
2. **Better UX**: Visual feedback shows system is working
3. **Scalable**: WebSocket handles multiple concurrent connections
4. **Efficient**: Binary protocol, less overhead than polling
5. **Interactive**: Enables future features like live status updates

## Future Enhancements

Potential improvements:
1. **True Async Execution**: Run actual triage analysis asynchronously and stream results
2. **Cancellation**: Allow users to cancel running triage
3. **Reconnection**: Auto-reconnect on connection drops
4. **Batch Triage**: Stream multiple alerts simultaneously
5. **Live Alerts**: New alerts appear in real-time without refresh

## Configuration

### Ports:
- Backend WebSocket: `ws://localhost:3000/api/triage/ws/{alert_id}`
- Frontend: `http://localhost:5173`

### Dependencies:
- Backend: FastAPI WebSocket support, websockets>=11.0.0
- Frontend: Native browser WebSocket API (no additional packages needed)

## Deployment Notes

1. Ensure WebSocket support is enabled in reverse proxy (nginx, etc.)
2. Configure WebSocket timeout appropriately (default 60s may be too short)
3. Consider adding heartbeat/ping-pong for long connections
4. Monitor WebSocket connection metrics in production
