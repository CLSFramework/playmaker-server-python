# About
This server is used to receive the state of the RCSSServer from the agent and respond to it with an action. [SoccerSimulationProxy](https://github.com/CLSFramework/soccer-simulation-proxy) is a base that sends the state (World Model) to this server and waits for the action to send it to the RCSSServer. This base is implemented on the helios-base and has all of the features of the helios-base, such as ChainAction (Planner), and the state model of the environment is as same as the WorldModel in the helios-base. The [protobuf](https://github.com/CLSFramework/cross-language-soccer-framework/wiki/Protobuf) that we defined has covered all of the information about the environment.

# RUN
To run this environment with this server connected to the agents you need to have these components installed:

- [RCSSServer](https://github.com/CLSFramework/cross-language-soccer-framework/wiki/Soccer-Simulation-Server)
- [Librcsc](https://github.com/CLSFramework/cross-language-soccer-framework/wiki/Soccer-Simulation-Proxy)
- [SoccerWindow2](https://github.com/CLSFramework/cross-language-soccer-framework/wiki/SoccerWindow2)
- [PROXY Base](https://github.com/CLSFramework/cross-language-soccer-framework/wiki/Soccer-Simulation-Proxy)

In order to run the environment, you need to run the RCSSServer, SoccerWindow2, and this server. After that, you can run the [Proxy base](https://github.com/CLSFramework/cross-language-soccer-framework/wiki/Soccer-Simulation-Proxy). To run them all you can follow these commands:

- run the RCSSServer using the following command:
```bash
rcssserver
```

- run the SoccerWindow2 using the following command:
```bash
soccerwindow2
```

- run the ```server``` using the following command:
```bash
cd path/to/playmaker-server-python
python server.py
```

- run the agents using the following command:
```bash
cd path/to/soccer-simulation-proxy/build/bin/
./start.sh
```
Note that if you want to use the debug tools of the ```soccerwindow2```, you have to run the ```./start-debug.sh``` instead of the ```./start.sh```.

Also, instead of running the ```server``` and the agents separately, you can run the ```server``` and the agents in the same time using the following command:
```bash
cd path/to/playmaker-server-python
./start-team.sh
```
In the competition, the competition manager will use the ```start-team.sh``` to run the server and the agents. Also each player has to connecte to a different ```playermaker-server```.

In addition, there are more ways to install and run the mentioned components. You can find more information about them in the following list:

- [RCSSServer](https://github.com/CLSFramework/cross-language-soccer-framework/wiki/Soccer-Simulation-Server)
- [Librcsc](https://github.com/CLSFramework/cross-language-soccer-framework/wiki/Soccer-Simulation-Proxy)
- [SoccerWindow2](https://github.com/CLSFramework/cross-language-soccer-framework/wiki/SoccerWindow2)
- [PROXY Base](https://github.com/CLSFramework/cross-language-soccer-framework/wiki/Soccer-Simulation-Proxy)

# How It Works?
The [Proxy base](https://github.com/CLSFramework/cross-language-soccer-framework/wiki/Soccer-Simulation-Proxy) is a base that acts as an intermediate connection between the RCSSServer and the ```playmaker-server```. The Proxy base receives the observation and the information of the field from the RCSSServer and send them to the ```playmaker-server```. The ```playmaker-server``` receives the observation and the information of the field as a ```WorldModel``` class in the [```protobuf```](https://github.com/CLSFramework/cross-language-soccer-framework/wiki/Protobuf) from the Proxy base and sends the action to the Proxy base. The Proxy base receives the action from the ```playmaker-server``` and sends it to the RCSSServer, and this happens in each cycle of the game.

# Related Projects:
Also you can find some useful examples in the following repositories:

- [soccer-gym](https://github.com/CLSFramework/soccer-gym)
