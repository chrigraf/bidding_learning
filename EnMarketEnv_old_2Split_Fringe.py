# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 10:05:34 2020

@author: Viktor
"""

#### Environment für 2 Player#####



import random
import gym
from gym import spaces
import numpy as np


from collections import deque
from market_clearing import market_clearing, converter


#C = 30
#CAP = 300
#env = EnMarketEnv02(CAP = np.array([100,100]), costs = 30)

#env.observation_space.shape[:]
#env.action_space.shape[0]-1

class BiddingMarket_energy(gym.Env):
    
    """
    Energy Market environment for OpenAI gym
    market_clearing included
    
    Rewards = 0: Default, Reward is (price-costs)*acceptedCAP 
    Rewards = 1: Reward is (price-costs)*acceptedCAP - (price*unsoldCAP)
    Rewards = 2: Reward is ((price-costs)*acceptedCAP)/(cost*maxCAP)
    Rewards = 3: Reward is ((price-costs)*acceptedCAP - (price*unsoldCAP))/(cost*maxCAP)
    Rewards = 4: Reward is ((price-costs)*acceptedCAP - (price*unsoldCAP))/((ownBid-cost)*maxCAP)

    
    """
    metadata = {'render.modes': ['human']}   ### ?

    def __init__(self, CAP, costs, Fringe=0, Rewards=0, Split=0, past_action = 1):              
        super(EnMarketEnv07_Split2_, self).__init__()
        
        self.CAP = CAP
        self.costs = costs
        self.Fringe = Fringe
        self.Rewards = Rewards
        self.Split = Split
        self.past_action = past_action
        
        # Continous action space for bids
        self.action_space = spaces.Box(low=np.array([0]), high=np.array([10000]), dtype=np.float16)
        self.observation_space = spaces.Box(low=0, high=10000, shape=(7,1), dtype=np.float16)
        
        # if Split Bids are allowed
        if self.Split == 1:
            self.action_space = spaces.Box(low=np.array([0,0,0]), high=np.array([10000,10000,1]), dtype=np.float16)
            self.observation_space = spaces.Box(low=0, high=10000, shape=(10,1), dtype=np.float16)
            
            # if played with Fringe player and Split Bids
            #if self.Fringe == 1:
             #   self.observation_space = spaces.Box(low=0, high=10000, shape=(8,1), dtype=np.float16)
        
        # Without containing past_actions in observation_space
        if self.past_action == 0:
            self.observation_space = spaces.Box(low=0, high=10000, shape=(4,1), dtype=np.float16)
            
        # Discrete Demand opportunities
        self.reward_range = (0, 1000000)

        
    def _next_observation(self, last_action):
        
        """
        Get State:
            includes the current Demand  -> Q
            - the Capacitys of all Players -> self.CAP[], (Maybe will change to: sold Capcitys from the Round before)
            - Memory of the Bids from the round before of all Players -> last_action[]
            (Consideration: of including Memory from more played rounds)
        
        Output:
            State as np.array of shape [7,1] 
    
        """
        
        #Q = np.array([500, 1000, 1500])
        #Q = np.array([800])
        #Q = random.choice(Q)
        
        Q = np.random.randint(900, 1100, 1)
        
        if self.Fringe == 1:
            #self.CAP[2] = self.fringe[0,2]
            self.CAP[2] = 500
        
        obs = np.array([Q[0], self.CAP[0], self.CAP[1], self.CAP[2], last_action[0], last_action[1], last_action[2]])

        if self.Split == 1:
            obs = np.array([Q[0], self.CAP[0], self.CAP[1], self.CAP[2], last_action[0], last_action[1], last_action[3],
                            last_action[4], last_action[6], last_action[7]])
  
        if self.past_action == 0:
            obs = np.array([Q[0], self.CAP[0], self.CAP[1], self.CAP[2]])


        return obs

    def step(self, action, last_action):
        
        self.current_step += 1
        
        # get current state, which includes Memory of the bids from the round before        
        obs = self._next_observation(last_action)
            
        Demand = obs[0]
        q = obs[0]
         
        Sup0 = np.array([int(0), self.CAP[0], action[0], self.costs[0], self.CAP[0]])
        Sup1 = np.array([int(1), self.CAP[1], action[1], self.costs[1], self.CAP[1]])
        
        #Decision on Strategic or Fringe Player 
        if self.Fringe == 1:
            Sup2 = self.fringe[0,:]
            self.fringe = self.fringe[1:,:] 
        else:
            Sup2 = np.array([int(2), self.CAP[2], action[2], self.costs[2], self.CAP[2]])
            
        # Which Position are Costs and main CAP (not sold CAP) in the array
        pos_cost = 3
        pos_cap = 4
        All = np.stack((Sup0, Sup1, Sup2))

        if self.Split == 1:
            Sup0 = np.array([int(0), self.CAP[0], action[0], action[1], action[2], self.costs[0], self.CAP[0]])
            Sup1 = np.array([int(1), self.CAP[1], action[3], action[4], action[5], self.costs[1], self.CAP[1]])
            Sup2 = np.array([int(2), self.CAP[2], action[6], action[7], action[8], self.costs[2], self.CAP[2]])
            pos_cost = 5
            pos_cap = 6
            # Converts the additional Bid/Split actions of the Suppliers 
            #into the required form for the market clearing
            All = converter(Sup0, Sup1, Sup2)
             #Decision on Strategic or Fringe Player 
            if self.Fringe == 1:
                Sup2 = self.fringe[0,:]
                self.fringe = self.fringe[1:,:]
                All = converter(Sup0, Sup1, Sup2)

        # Returns all Players orderd by lowest bid and assigns to them their quantities they can sell
        # (Output: [0]= price, [1]= Orderd Player lists, [2]= quantities to sell in original order)
        
        market = market_clearing(q, All)
        p = market[0]
        sold_quantities = market[2]
        
        if self.Split == 1:
            sold_quantities = np.array([(sold_quantities[0]+sold_quantities[1]), (sold_quantities[2]+sold_quantities[3]), 
                                        (sold_quantities[4]+sold_quantities[5])])

     
        #### rewards
        reward0, reward1, reward2 = self.reward_function(Sup0, Sup1, Sup2, sold_quantities, p, pos_cap, pos_cost, self.Rewards)
        
        

        if self.Fringe == 1:
            reward = np.append(reward0, reward1)
        else:
            reward = np.append(reward0, reward1)
            reward = np.append(reward, reward2)

        

        ## Render Commands 
        self.safe(action, self.current_step)
        
        self.sum_q += Demand
        self.avg_q = self.sum_q/self.current_step
        self.sum_action += action
        self.avg_action = self.sum_action/self.current_step
        self.current_q = Demand
        self.last_rewards = reward
        self.last_bids = action
        self.sum_rewards += reward
        self.avg_rewards = self.sum_rewards/self.current_step
        
        #### DONE and new_State
        if self.Fringe == 1:
            done = self.fringe.size == 0
            
            last_action = np.append(action, Sup2[2])            
            obs = self._next_observation(last_action)
            
        else:
            done = self.current_step == 128#256#128 
             
            last_action = action 
            obs = self._next_observation(last_action)
        


        return obs, reward, done, {}
    
    
    def safe(self, action, current_step):
        
        Aktionen = (action, current_step)
        self.AllAktionen.append(Aktionen)
        
    def reward_function(self, Sup0, Sup1, Sup2, sold_quantities, p, pos_cap, pos_cost, Penalty):
        '''
        Different Options of calculating the Reward
        
        '''
        
        reward0 = (p - Sup0[pos_cost]) * sold_quantities[0]                    
        reward1 = (p - Sup1[pos_cost]) * sold_quantities[1]  
        reward2 = (p - Sup2[pos_cost]) * sold_quantities[2] 


        if Penalty == 1:
            reward0 = reward0 - (Sup0[pos_cost] * (Sup0[pos_cap] - sold_quantities[0]))
            reward1 = reward1 - (Sup1[pos_cost] * (Sup1[pos_cap] - sold_quantities[1]))
            reward2 = reward2 - (Sup2[pos_cost] * (Sup2[pos_cap] - sold_quantities[2]))        
        
        if Penalty == 2:
            reward0 = reward0 / (Sup0[pos_cost] * Sup0[pos_cap])            
            reward1 = reward1 / (Sup1[pos_cost] * Sup1[pos_cap])           
            reward2 = reward2 / (Sup2[pos_cost] * Sup2[pos_cap])
            
        if Penalty == 3:            
            reward0 = reward0 - (Sup0[pos_cost] * (Sup0[pos_cap] - sold_quantities[0]))           
            reward1 = reward1 - (Sup1[pos_cost] * (Sup1[pos_cap] - sold_quantities[1]))            
            reward2 = reward2 - (Sup2[pos_cost] * (Sup2[pos_cap] - sold_quantities[2]))
                        
            reward0 = reward0 / (Sup0[pos_cost] * Sup0[pos_cap])           
            reward1 = reward1 / (Sup1[pos_cost] * Sup1[pos_cap])            
            reward2 = reward2 / (Sup2[pos_cost] * Sup2[pos_cap])            
        
        if Penalty == 4:              
            reward0 = reward0 - (Sup0[pos_cost] * (Sup0[pos_cap] - sold_quantities[0]))           
            reward1 = reward1 - (Sup1[pos_cost] * (Sup1[pos_cap] - sold_quantities[1]))           
            reward2 = reward2 - (Sup2[pos_cost] * (Sup2[pos_cap] - sold_quantities[2]))
            
            
            # 4a               
            expWin0 = (Sup0[2]-Sup0[pos_cost]) * sold_quantities[0] # oder * maxCAP
            expWin1 = (Sup1[2]-Sup1[pos_cost]) * sold_quantities[1]
            expWin2 = (Sup2[2]-Sup2[pos_cost]) * sold_quantities[2]            
            expWin0 = np.clip(expWin0, 0.000001, 10000)
            expWin1 = np.clip(expWin1, 0.000001, 10000)
            expWin2 = np.clip(expWin2, 0.000001, 10000)
            
            '''
            
            expWin0 = (Sup0[2]) * sold_quantities[0]
            expWin1 = (Sup1[2]) * sold_quantities[1]
            expWin2 = (Sup2[2]) * sold_quantities[2]
            
            # is this a correct way to avoid producig nan
            if expWin0 == 0:
                expWin0 = 0.0000000000001
            if expWin1 == 0:
                expWin1 = 0.0000000000001
            if expWin2 == 0:
                expWin2 = 0.0000000000001
            
            '''
            reward0 = reward0 / expWin0
            reward1 = reward1 / expWin1
            reward2 = reward2 / expWin2
        
        
        return reward0, reward1, reward2
    
    def reset(self):
        # Reset the state of the environment to an initial state
        self.current_step = 0
        self.avg_action = 0
        self.sum_action = 0
        self.sum_q = 0
        self.sum_rewards = 0
        self.AllAktionen = deque(maxlen=500)
        self.start_action = np.zeros(9)
       
        
        #Fringe or Strategic Player
        #        # Test move to init
        #Readout fringe players from other.csv (m)
        #Readout fringe players from other.csv (m)
        read_out = np.genfromtxt("others.csv",delimiter=";",autostrip=True,comments="#",skip_header=1,usecols=(0,1))
        #Readout fringe switched to conform with format; finge[0]=quantity fringe[1]=bid
        self.fringe = np.fliplr(read_out)
        self.fringe = np.pad(self.fringe,((0,0),(1,2)),mode='constant', constant_values=(2, 0))
        if self.Split == 1:
            self.fringe = np.pad(self.fringe,((0,0),(1,3)),mode='constant', constant_values=(2, 0))
        #self.fringe = np.pad(self.fringe,((0,0),(1,0)),mode='constant')
        
        return self._next_observation(self.start_action)
    
    def render(self, mode='human', close=False):
        # Render the environment to the screen
        print(f'Step: {self.current_step}')
        print(f'AllAktionen: {self.AllAktionen}')
        print(f'Last Demand of this Episode: {self.current_q}')
        print(f'Last Bid of this Episode: {self.last_bids}')
        print(f'Last Reward of this Episode: {self.last_rewards}')
        print(f'Average Demand: {self.avg_q}')
        print(f'Average Bid: {self.avg_action}')
        print(f'Average Reward: {self.avg_rewards}')
        
        