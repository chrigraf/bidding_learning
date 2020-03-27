# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 10:05:17 2020

@author: Viktor
"""

###### Versuch mit 2 agents ########################

import sys
#import gym
import numpy as np
#import pandas as pd
import matplotlib.pyplot as plt
from DDPG02_ import DDPGagent02
from utils_ import OUNoise, Memory
from EnMarketEnv06_ import EnMarketEnv06 




env = EnMarketEnv06(CAP = np.array([400,500,600]), costs = np.array([100,100,100]))



agent0 = DDPGagent02(env)
agent1 = DDPGagent02(env)
agent2 = DDPGagent02(env)
noise = OUNoise(env.action_space)
batch_size = 128
rewards = []
avg_rewards = []

for episode in range(50):
    state = env.reset()
    noise.reset()
    episode_reward = 0
    
    for step in range(500):
        
        action0 = agent0.get_action(state)
        action0 = noise.get_action(action0, step)
        action1 = agent1.get_action(state)
        action1 = noise.get_action(action1, step)
        action2 = agent2.get_action(state)
        action2 = noise.get_action(action2, step)
        
        action = np.concatenate([action0, action1, action2])
        new_state, reward, done, _ = env.step(action)   
        
        agent0.memory.push(state, np.array([action[0]]), np.array([reward[0]]), new_state, done)
        agent1.memory.push(state, np.array([action[1]]), np.array([reward[1]]), new_state, done)
        agent2.memory.push(state, np.array([action[2]]), np.array([reward[2]]), new_state, done)


        
        if len(agent0.memory) > batch_size:            
            agent0.update(batch_size)
            agent1.update(batch_size)
            agent2.update(batch_size) 
        
        state = new_state
        episode_reward += reward

        if done:
            sys.stdout.write("episode: {}, reward: {}, average _reward: {} \n".format(episode, np.round(episode_reward, decimals=2), np.mean(rewards[-10:])))
            env.render()
            break

    rewards.append(episode_reward)
    avg_rewards.append(np.mean(rewards[-10:]))

plt.plot(rewards)
plt.plot(avg_rewards)
plt.plot()
plt.xlabel('Episode')
plt.ylabel('Reward')
plt.show()


