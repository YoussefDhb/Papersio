import asyncio
import json
import websockets

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            
            request = {
                "query": "What is the capital of France?",
                "use_search": False, # Faster test
                "mode": "ultra"
            }
            await websocket.send(json.dumps(request))
            print(f"Sent request: {request}")
            
            status_count = 0
            
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                
                if data["type"] == "status":
                    print(f"STATUS: [{data['stage']}] {data['details']}")
                    status_count += 1
                elif data["type"] == "result":
                    print(f"RESULT RECEIVED")
                    print(f"Answer: {data['answer'][:100]}...")
                    if status_count > 0:
                         print("Verification Successful: Received status updates before result.")
                    else:
                         print("Verification Failed: No status updates received.")
                    break
                elif data["type"] == "error":
                    print(f"ERROR: {data['content']}")
                    break
                    
    except Exception as e:
        print(f"Connection failed: {e}")
        print("Make sure the backend is running (python backend/main.py)")

if __name__ == "__main__":
    try:
        asyncio.run(test_websocket())
    except KeyboardInterrupt:
        pass
