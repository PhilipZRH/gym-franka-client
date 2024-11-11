import asyncio
import websockets
import time
import json


class WebSocketClient:
    def __init__(self, server_address, server_port):
        self.server_address = server_address
        self.server_port = server_port
        self.websocket = None
        self.loop = asyncio.get_event_loop()

    def connect(self):
        return self.loop.run_until_complete(self._async_connect())

    def reset(self):
        return self.loop.run_until_complete(self._async_reset())

    def move(
        self,
        pose: dict,
        gripper_action: float,
        wait=True,
    ):
        return self.loop.run_until_complete(
            self.send_command(
                {
                    "command": "move",
                    "pose": pose,
                    "gripper_action": gripper_action,
                    "wait": wait,
                }
            )
        )

    def get_state(self):
        return self.loop.run_until_complete(self.send_command({"command": "state"}))

    async def _async_connect(self):
        print("[Gym Franka Client] Connecting to server...")
        try:
            self.websocket = await websockets.connect(
                f"ws://{self.server_address}:{self.server_port}",
                ping_interval=None,
            )
            print("[Gym Franka Client] Connected to server.")
            return True
        except Exception as e:
            print(f"[Gym Franka Client] Connection failed: {e}")
            self.websocket = None
            return False

    async def send_command(self, command):
        timestamp = time.time_ns()
        command["timestamp"] = timestamp
        json_command = json.dumps(command)
        await self.websocket.send(json_command)
        return await self.wait_for_response(timestamp)

    async def wait_for_response(self, timestamp):
        while True:
            try:
                data = await self.websocket.recv()
                recv_message = json.loads(data)
                if recv_message.get("timestamp") == timestamp:
                    return recv_message
            except Exception as e:
                print(f"[Gym Franka Client] Error receiving message: {e}")
                return False

    async def _async_reset(self):
        return await self.send_command({"command": "reset"})

    async def _async_move(self, pose: dict, gripper_action: float, wait=True):
        command = {
            "command": "move",
            "pose": pose,
            "gripper_action": gripper_action,
            "wait": wait,
        }
        return await self.send_command(command)

    async def close_gripper(self):
        return await self.send_command({"action": "Grasp"})

    async def open_gripper(self):
        return await self.send_command({"action": "Open"})
