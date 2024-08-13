from abc import ABC
from src.IAgent import IAgent
from soccer.ttypes import TrainerActions, TrainerAction, DoMoveBall, ServerParam, PlayerParam, PlayerType, WorldModel, RpcVector2D

class SampleTrainerAgent(IAgent, ABC):
    def __init__(self):
        super().__init__()
        self.serverParams: ServerParam = None
        self.playerParams: PlayerParam = None
        self.playerTypes: dict[PlayerType] = {}
        self.wm: WorldModel = None
        self.first_substitution = True
    
    def get_actions(self, wm:WorldModel) -> TrainerActions:
        self.wm = wm
        
        actions = TrainerActions()
        print(f'cycle: {self.wm.cycle}')
        print(f'cycle: {self.wm.ball.position.x}, {self.wm.ball.position.y}')
        
        if self.wm.cycle % 100 == 0:
            actions.actions.append(
                TrainerAction(
                    do_move_ball=DoMoveBall(
                        position=RpcVector2D(
                            x=0,
                            y=0
                        ),
                        velocity=RpcVector2D(
                            x=0,
                            y=0
                        ),
                    )
                )
            )
        return actions
    
    def set_params(self, params):
        if isinstance(params, ServerParam):
            self.serverParams = params
        elif isinstance(params, PlayerParam):
            self.playerParams = params
        elif isinstance(params, PlayerType):
            self.playerTypes[params.id] = params
        else:
            raise Exception("Unknown params type")