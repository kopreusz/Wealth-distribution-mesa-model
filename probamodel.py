
import mesa
import numpy as np
import matplotlib as plt
import random
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.modules import ChartModule
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter


def compute_gini(model):
    agent_wealths = []
    j = 0
    for i in range(len(model.schedule.agents)):
        if isinstance(model.schedule.agents[i],MoneyAgent): # a gini indexet csak a mozgougynokok vagyona alapjan szeretnenk szamolni
            
            agent_wealths.append(model.schedule.agents[i].wealth)
            j += 1

    x = sorted(agent_wealths)
    N = j
    B = sum(xi * (N - i) for i, xi in enumerate(x)) / (N * sum(x))
    return 1 + (1 / N) - 2 * B

def starvation(model):
    starving = 0 
    j = 0
    for i in range(len(model.schedule.agents)):
        if isinstance(model.schedule.agents[i],MoneyAgent): 
            j += 1
            if model.schedule.agents[i].wealth == 0:
                starving += 1
            
    return starving/j
class Capital(mesa.Agent):

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        
        self.wealth = 1
        self.growth = model.growth
   
    def step(self):
        self.wealth += self.growth

class MoneyAgent(mesa.Agent):

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.wealth = 10
        self.life = random.randint(0,100)
        self.consume = model.consume
        
        
    
    def move(self):
        maxi = 0
        ind = -1
        possible_steps = self.model.grid.get_neighbors(
            self.pos, moore=True, include_center=False
        )
        for i in range(len(possible_steps)):
            
                if isinstance(possible_steps[i],Capital) and possible_steps[i].wealth > maxi:
                    maxi = possible_steps[i].wealth
                    ind = i
        new_position = possible_steps[ind].pos
        self.model.grid.move_agent(self, new_position)   
      
    def get_older(self): 
            self.life -= 1
            if self.life <= 0:
                self.wealth = 1
                self.life = random.randint(0,100)

    def eat_something(self): 
            self.wealth -= self.consume
            if self.wealth < 0:
                self.wealth = 1
                self.life = random.randint(0,100)
         
            
    def get_cash(self): 
                cellmates = self.model.grid.get_cell_list_contents([self.pos]) 
                for i in range(len(cellmates)):
                    cash = cellmates[i] 
                    if isinstance(cash,Capital):         
                        self.wealth += cash.wealth 
                        cash.wealth = 0 

    def step(self): 
            self.move()
            self.get_cash()
            self.eat_something()
            self.get_older()

class MoneyModel(mesa.Model):


    def __init__(self, N, width, height,consume,growth):
        self.num_agents = N + width*height
        self.consume = consume
        self.growth = growth
        self.grid = mesa.space.MultiGrid(width, height, True)
        self.schedule = mesa.time.RandomActivation(self)
        self.datacollector = mesa.DataCollector(
                        model_reporters={"Gini": compute_gini,"Starvation":starvation}, agent_reporters={"Wealth": "wealth"}
        )

        y = -1
        for j in range(width*height):
                capital = Capital(j,self)
                self.schedule.add(capital)
                x = j % width
                if j % width == 0:
                    y += 1 
                self.grid.place_agent(capital, (x, y))


        
        for i in range(width*height,self.num_agents): 
            a = MoneyAgent(i, self)
            self.schedule.add(a)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))
        
    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()

class server():
   
    def agent_portrayal(agent):
        portrayal = {"Shape":"circle", "Filled": "true", "r": 0.5}
        if isinstance(agent,Capital):
            portrayal["Color"] = "green"
            portrayal["Layer"] = 0
            portrayal["r"] = 1
        else:    
            if agent.wealth > 10:
                portrayal["Color"] = "blue"
                portrayal["Layer"] = 1
            else:
                portrayal["Color"] = "red"
                portrayal["Layer"] = 2
                portrayal["r"] = 0.2
        return portrayal
    
    grid = CanvasGrid(agent_portrayal,10,10,500,500)

    chart = ChartModule([{
        'Label':'Gini',
        'Color' : 'Black'}],
         data_collector_name = 'datacollector')
  
    starve = ChartModule([{
        'Label':'Starvation',
        'Color' : 'Red'}],
        data_collector_name = 'datacollector')
    modelparams = {
        "N": UserSettableParameter("slider","Number of agents",20,1,200,1),
        "width":10,
        "height":10,
        "consume":UserSettableParameter("slider","Needs",1,1,5,1),
        "growth":UserSettableParameter("slider","Money Growth",1,1,20,1)
        }
    server = ModularServer(MoneyModel,[grid,chart,starve],"Money Model", modelparams)
    server.port = 8521
    server.launch()


