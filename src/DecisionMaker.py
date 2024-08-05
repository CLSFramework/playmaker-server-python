from soccer.ttypes import HeliosGoalie, HeliosPenalty, HeliosSetPlay, GameModeType, PlayerAction
from src.IDecisionMaker import IDecisionMaker
from src.DM_PlayOn import PlayOnDecisionMaker
from src.DM_SetPlay import SetPlayDecisionMaker
from src.IAgent import IAgent


class DecisionMaker(IDecisionMaker):
    def __init__(self):
        self.playOnDecisionMaker = PlayOnDecisionMaker()
        self.setPlayDecisionMaker = SetPlayDecisionMaker()
    
    def make_decision(self, agent: IAgent):
        if agent.wm.myself.is_goalie:
            print("make_decision: is_goalie")
            agent.add_action(PlayerAction(helios_goalie=HeliosGoalie()))
        else:
            print("make_decision: not is_goalie")
            if agent.wm.game_mode_type == GameModeType.PlayOn:
                print("make_decision: PlayOnDecisionMaker")
                self.playOnDecisionMaker.make_decision(agent)
            elif agent.wm.is_penalty_kick_mode:
                print("make_decision: PenaltyKickDecisionMaker")
                agent.add_action(PlayerAction(helios_penalty=HeliosPenalty()))
            else:
                print("make_decision: SetPlayDecisionMaker")
                agent.add_action(PlayerAction(helios_set_play=HeliosSetPlay()))