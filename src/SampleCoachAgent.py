from abc import ABC
from src.IAgent import IAgent
from soccer.ttypes import CoachActions, CoachAction, ChangePlayerType, DoHeliosSubstitute, PlayerParam, PlayerType, ServerParam, WorldModel

class SampleCoachAgent(IAgent, ABC):
    def __init__(self):
        super().__init__()
        self.serverParams: ServerParam = None
        self.playerParams: PlayerParam = None
        self.playerTypes: dict[PlayerType] = {}
        self.wm: WorldModel = None
        self.first_substitution = True
    
    def get_actions(self, wm:WorldModel) -> list[CoachAction]:
        print("SampleCoachAgent.get_actions", wm.cycle)
        self.wm = wm
        actions = []
        actions.append(
            CoachAction(
                do_helios_substitute=DoHeliosSubstitute()
            )
        )
        return actions
        # if (wm.cycle == 0
        #     and self.first_substitution
        #     and self.playerParams is not None
        #     and len(self.playerTypes.keys()) == self.playerParams.player_types):
            
        #     self.first_substitution = False
        #     for i in range(11):
        #         actions.actions.append(
        #             CoachAction(
        #                 change_player_types=ChangePlayerType(
        #                 uniform_number=i+1,
        #                 type=i
        #                 )
        #             )
        #         )


        # coach_actions.actions = actions

    
    def set_params(self, params):
        if isinstance(params, ServerParam):
            self.serverParams = params
        elif isinstance(params, PlayerParam):
            self.playerParams = params
        elif isinstance(params, PlayerType):
            self.playerTypes[params.id] = params
        else:
            raise Exception("Unknown params type")