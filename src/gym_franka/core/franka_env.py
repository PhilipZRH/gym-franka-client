import gymnasium as gym
import time
import numpy as np
from gym_franka.core.websocket_client import WebSocketClient
from scipy.spatial.transform import Rotation


class FrankaEnv(gym.Env):
    def __init__(
        self,
        server_address,
        server_port,
        enable_gripper=True,
    ):
        # Statespace (internal)
        self.position_origin = np.array([0.3, 0, 0.5])
        self.position_low = np.array([0.3, -0.5, 0])
        self.position_high = np.array([0.8, 0.5, 0.5])
        self.rotation_origin = Rotation.from_quat([0, -1, 0, 0]).as_quat()
        self.position_gain = 0.05
        self.rotation_gain = np.pi / 10
        self.position = self.position_origin.copy()
        self.rotation = self.rotation_origin.copy()
        self.previous_position = self.position
        self.previous_rotation = self.rotation
        self.gripper_action = 1

        self.websocket_client = WebSocketClient(server_address, server_port)
        self.require_full_reset = True

        self.enable_gripper = enable_gripper
        self.action_space = gym.spaces.Box(low=-1, high=1, shape=(7,), dtype=float)
        self.observation_space = gym.spaces.Dict(
            {
                "q": gym.spaces.Box(low=-np.inf, high=np.inf, shape=(7,), dtype=float),
                "dq": gym.spaces.Box(low=-np.inf, high=np.inf, shape=(7,), dtype=float),
            }
        )

        self.reward_function = lambda *args, **kwargs: 0

    def connect_to_server(self):
        connected = self.websocket_client.connect()
        self.require_full_reset = not connected
        if not connected:
            time.sleep(1)
        return connected

    def reset(self, seed=None, options=None):
        self._reset()
        return self._get_obs(), {}

    def _reset(self):
        while self.require_full_reset:
            self.connect_to_server()

        self.websocket_client.reset()
        self.position = self.position_origin.copy()
        self.rotation = self.rotation_origin.copy()
        self.previous_position = self.position
        self.previous_rotation = self.rotation

    def close_gripper(self):
        self.websocket_client.run_coroutine(self.websocket_client.close_gripper())

    def open_gripper(self):
        self.websocket_client.run_coroutine(self.websocket_client.open_gripper())

    def send_move_command(self, wait=True):
        response = self.websocket_client.move(
            pose={
                "position": {
                    "x": self.position[0],
                    "y": self.position[1],
                    "z": self.position[2],
                },
                "rotation": {
                    "x": self.rotation[0],
                    "y": self.rotation[1],
                    "z": self.rotation[2],
                    "w": self.rotation[3],
                },
            },
            gripper_action=float(self.gripper_action),
            wait=wait,
        )
        if response["status"] == "Reflex":
            print("[FrankaEnv] Reflex corrected.")
            self.roll_back()
            return False
        return True

    def roll_back(self):
        self.position = self.previous_position
        self.rotation = self.previous_rotation

    def step(self, action):
        action = np.array(action)
        action = np.clip(action, -1, 1)
        if not self.enable_gripper:
            action[-1] = 1

        delta_position = action[:3] * self.position_gain
        delta_rotation = Rotation.from_euler(
            "xyz",
            [
                action[3] * self.rotation_gain,
                action[4] * self.rotation_gain,
                action[5] * self.rotation_gain,
            ],
        ).as_quat()

        new_position = self.position + delta_position
        new_rotation = (
            Rotation.from_quat(delta_rotation) * Rotation.from_quat(self.rotation)
        ).as_quat()

        self.previous_position = self.position
        self.position = new_position.clip(self.position_low, self.position_high)

        self.previous_rotation = self.rotation
        self.rotation = new_rotation
        self.gripper_action = action[6]

        self.step_success = self.send_move_command(wait=True)
        if not self.step_success:
            self.require_full_reset = True

        return self.get_step_return()

    def get_step_return(self):
        obs = self._get_obs()
        reward = self.reward_function()
        is_success = reward > 0
        terminated = is_success
        truncated = False
        return (
            obs,
            reward,
            terminated,
            truncated,
            {"is_success": is_success, "step_success": self.step_success},
        )

    def _get_obs(self):
        state = self.websocket_client.get_state()
        if state is not None:
            return {
                "q": np.array(state["state"]["q"]),
                "dq": np.array(state["state"]["dq"]),
            }
        return {}
