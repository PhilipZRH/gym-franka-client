from gymnasium.envs.registration import register
from gym_franka.core.franka_env import FrankaEnv


def register_env():
    import os

    SERVER_IP = os.getenv("GYM_FRANKA_SERVER_IP")

    register(
        id="Franka-v1",
        entry_point=FrankaEnv,
        max_episode_steps=100,
        kwargs={
            "server_address": SERVER_IP,
            "server_port": 8888,
            "enable_gripper": True,
        },
    )


register_env()
