from abc import ABC
from soccer.ttypes import State, Empty, PlayerActions, CoachActions, TrainerActions, ServerParam, PlayerParam, PlayerType, InitMessage, WorldModel, PlayerAction
from src.DecisionMaker import DecisionMaker
from src.IAgent import IAgent
from src.FormationStrategy import FormationStrategy


class SamplePlayerAgent(IAgent, ABC):
    def __init__(self):
        super().__init__()
        self.decisionMaker = DecisionMaker()
        self.strategy = FormationStrategy()
        self.serverParams: ServerParam = None
        self.playerParams: PlayerParam = None
        self.playerTypes: dict[PlayerType] = {}
        self.wm: WorldModel = None
    
    def get_actions(self, wm:WorldModel) -> list[PlayerAction]:
        self.wm = wm
        self.actions.clear()
        self.strategy.update(wm)
        self.decisionMaker.make_decision(self)

        return self.actions
    
    def get_strategy(self):
        return self.strategy
        
    def set_params(self, params):
        if isinstance(params, ServerParam):
            self.serverParams = params
        elif isinstance(params, PlayerParam):
            self.playerParams = params
        elif isinstance(params, PlayerType):
            self.playerTypes[params.id] = params
        else:
            raise Exception("Unknown params type")