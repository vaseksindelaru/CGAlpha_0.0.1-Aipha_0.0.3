import asyncio
import sys
from cgalpha_v3.infrastructure.binance_websocket_manager import BinanceWebSocketManager

async def test():
    print("Iniciando Diag WS (20s)...")
    ws = BinanceWebSocketManager.create_default()
    def sync_cb(d):
        print(f"🔥 TICK: {d.get('e') or d.get('stream')}", flush=True)
    
    ws.add_callback(sync_cb)
    await ws.start()
    
    # El manager.start() crea una task, así que esperamos nosotros
    for i in range(20):
        await asyncio.sleep(1)
        if i % 5 == 0: print(f"Esperando... {i}s")

asyncio.run(test())
