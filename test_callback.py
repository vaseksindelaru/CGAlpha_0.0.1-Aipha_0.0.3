import asyncio
from cgalpha_v3.infrastructure.binance_websocket_manager import BinanceWebSocketManager
from cgalpha_v3.application.live_adapter import LiveDataFeedAdapter
from cgalpha_v3.infrastructure.signal_detector.triple_coincidence import TripleCoincidenceDetector

def go():
    ws = BinanceWebSocketManager.create_default()
    d = TripleCoincidenceDetector(None)
    adapter = LiveDataFeedAdapter.create_default(ws, d)
    ws.add_callback(adapter.on_ws_message)
    print("Callbacks:", ws.callbacks)
    for cb in ws.callbacks:
        print("Is coro:", asyncio.iscoroutinefunction(cb))

go()
