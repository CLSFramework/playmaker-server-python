import service_pb2 as pb2
from src.IDecisionMaker import IDecisionMaker
from src.IAgent import IAgent


class DecisionMaker(IDecisionMaker):
    def __init__(self):
        pass
    
    def make_decision(self, agent: IAgent):
        if agent.wm.self.is_goalie:
            agent.add_action(pb2.PlayerAction(helios_goalie=pb2.HeliosGoalie()))
        else:
            if agent.wm.game_mode_type == pb2.GameModeType.PlayOn:
                if agent.wm.self.is_kickable:
                    if agent.wm.ball.position.x < 30:
                        agent.add_action(pb2.PlayerAction(helios_chain_action=pb2.HeliosChainAction(cross=False, 
                                                                                                    direct_pass=True, 
                                                                                                    through_pass=True, 
                                                                                                    lead_pass=True,
                                                                                                    short_dribble=True,
                                                                                                    simple_dribble=True,
                                                                                                    simple_pass=True,
                                                                                                    simple_shoot=False,
                                                                                                    long_dribble=False)))
                    else:
                        agent.add_action(pb2.PlayerAction(helios_chain_action=pb2.HeliosChainAction(cross=True, 
                                                                                                    direct_pass=True, 
                                                                                                    through_pass=True, 
                                                                                                    lead_pass=True,
                                                                                                    short_dribble=True,
                                                                                                    simple_dribble=True,
                                                                                                    simple_pass=True,
                                                                                                    simple_shoot=True,
                                                                                                    long_dribble=True)))
                        agent.add_action(pb2.PlayerAction(helios_shoot=pb2.HeliosShoot()))
                else:
                    agent.add_action(pb2.PlayerAction(helios_basic_move=pb2.HeliosBasicMove()))
            elif agent.wm.is_penalty_kick_mode:
                agent.add_action(pb2.PlayerAction(helios_penalty=pb2.HeliosPenalty()))
            else:
                agent.add_action(pb2.PlayerAction(helios_set_play=pb2.HeliosSetPlay()))