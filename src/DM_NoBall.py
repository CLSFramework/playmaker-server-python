from src.IDecisionMaker import IDecisionMaker
from src.IAgent import IAgent
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from src.BHV_Block import BHV_Block
from soccer.ttypes import LoggerLevel, PlayerAction, Body_Intercept, Neck_TurnToBall, Body_GoToPoint, DebugClient, ThriftVector2D

class NoBallDecisionMaker(IDecisionMaker):
    def __init__(self):
        pass
    
    def make_decision(self, agent: IAgent):
        teammate_reach_steps = agent.wm.intercept_table.first_teammate_reach_steps
        self_reach_steps = agent.wm.intercept_table.self_reach_steps
        our_reach_steps = min(teammate_reach_steps, self_reach_steps)
        opponent_reach_steps = agent.wm.intercept_table.first_opponent_reach_steps
        
        if our_reach_steps < opponent_reach_steps and self_reach_steps < teammate_reach_steps:
            agent.add_action(PlayerAction(body_intercept=Body_Intercept(save_recovery=False,
                                                                          face_point=ThriftVector2D( x=agent.wm.ball.position.x,
                                                                       y=agent.wm.ball.position.y))))
            agent.add_action(PlayerAction(neck_turn_to_ball=Neck_TurnToBall()))
            return
        
        pos = agent.get_strategy().getPosition(agent.wm.myself.uniform_number)
        agent.add_log_text(LoggerLevel.TEAM, f"opponent_reach_steps: {opponent_reach_steps} "
                                                 f"our_reach_steps: {our_reach_steps}")
        if opponent_reach_steps < our_reach_steps:
            if BHV_Block().execute(agent):
                return
            
        agent.add_action(PlayerAction(body_go_to_point=Body_GoToPoint(target_point=ThriftVector2D(x=pos.x(), y=pos.y()),
                                                                        distance_threshold=1,
                                                                        max_dash_power=100)))
        agent.add_action(PlayerAction(neck_turn_to_ball=Neck_TurnToBall()))
        agent.add_action(PlayerAction(debug_client=DebugClient(message=f"go to : {pos.x()}, {pos.y()}")))
        