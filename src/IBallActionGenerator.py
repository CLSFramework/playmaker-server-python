from src.IBallAction import BallAction
from src.IAgent import IAgent
from soccer.ttypes import LoggerLevel

class BallActionGenerator:
    def __init__(self):
        self.candidateActions: list[BallAction] = []
        self.debug_list = []
        
    def log_debug(self, agent: IAgent, log_level: LoggerLevel):
        for item in self.debug_list:
            same_index = float(item[3])
            agent.add_log_circle(log_level, item[1].x(), item[1].y() + 0.05 * same_index, 0.2, "blue" if item[2] else "red", False)
            agent.add_log_message(log_level, f"{item[0]}", item[1].x(), item[1].y() - 0.1 * same_index, "blue" if item[2] else "red")
        