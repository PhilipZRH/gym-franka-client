# Gym Franka Client
A gymnasium interface for the Franka Emika Panda Robot Arm. The server-side code is avaliable [here](https://github.com/philipzrh/gym-franka-server).

## System Architecture
The client-side gymnasium environment communicates with the server-side interface through WebSocket. The server communicates with the robot arm using ```franka_ros```.

## Getting started
Install the pip package with:
```bash
pip install -e .
```

## Additional setups
Change the environment variables to point to the ROS machine running ```gym-franka-server```.
```bash
export GYM_FRANKA_SERVER_IP=192.168.xx.xx
```

## Example
```
import gymnasium as gym
import gym_franka

e = gym.make('Franka-v1')
e.reset()
e.step(e.action_space.sample())
```