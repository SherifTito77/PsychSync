import asyncio
import httpx

async def test():
    # First, try to login or use existing session
    try:
        async with httpx.AsyncClient() as client:
            # Try to execute the prompt
            response = await client.post(
                'http://localhost:8000/api/v1/product-management/prompts/execute',
                json={'prompt_id': 'ux_002', 'use_ai': False},
                headers={'Content-Type': 'application/json'},
                timeout=10.0
            )
            
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ Success! Response keys: {list(data.keys())}")
                print(f"\nPrompt object keys: {list(data.get('prompt', {}).keys())}")
                print(f"\nHas outputs in prompt: {'outputs' in data.get('prompt', {})}")
                if 'outputs' in data.get('prompt', {}):
                    print(f"Outputs: {data['prompt']['outputs']}")
                print(f"\nFull response:")
                print(json.dumps(data, indent=2))
            else:
                print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

asyncio.run(test())
