# Cross Language Soccer Framework

Cross Language Soccer Framework (CLSFramework) is a new approach to enhance the flexibility and interoperability of RoboCup Soccer Simulation 2D (SS2D). 
This framework is designed to allow the development of RoboCup Soccer Simulation 2D agents in different programming languages.
The Soccer Simulation Proxy is an extended version of the Helios base that can send decision-making information to a PlayMaker Server. It can receive high-level/low-level actions from the PlayMaker Server and send them to the RoboCup Soccer Simulation Server and/or SoccerWindow2.
On the other hand, the PlayMaker Server receives information from the client(Modified version of Helios base/Soccer Simulation Proxy) and selects the appropriate actions to be sent back to the client. We have implemented some sample servers in C\#, Python, and JavaScript, but it can also be implemented in other languages to make use of their features.

To learn more about the framework, how to build, and how to run it please check the [wiki pages](https://github.com/CLSFramework/cross-language-soccer-framework/wiki).

Also, you can check the following repositories to find sample playmaker servers in PYTHON:
- [PlaymakerServer-Python](https://github.com/CLSFramework/playmaker-server-python)
-  - [Sample-PlaymakerServer-Python-GRPC](https://github.com/CLSFramework/sample-playmaker-server-python-grpc)
-  - [Sample-PlaymakerServer-Python-THRIFT](https://github.com/CLSFramework/sample-playmaker-server-python-thrift)
-  - [Starter-PlaymakerServer-Python-THRIFT](https://github.com/CLSFramework/starter-playmaker-server-python-thrift)

![image](https://github.com/user-attachments/assets/0c22d0e5-a1ad-4a43-8cba-a9fc70c6ed5b)

![image](https://github.com/Cross-Language-Soccer-Framework/cross-language-soccer-framework/assets/25696836/7b0b1d49-7001-479c-889f-46a96a8802c4)

![image](https://github.com/user-attachments/assets/b4484095-0913-4434-bf1f-35f11e8bf629)

![image](https://github.com/user-attachments/assets/bc1b9c86-f772-4df8-a420-438e363c59b5)


# About
RoboCup is an international competition aimed at advancing autonomous robotics and AI through tasks like soccer and rescue. The RoboCup Soccer Simulation 2D league focuses on developing intelligent agents that play soccer in a simulated 2D environment. This league is ideal for testing and developing AI and ML algorithms, including reinforcement learning and multi-agent systems. [more details](https://github.com/CLSFramework/cross-language-soccer-framework/wiki/Definitions)

![image](https://github.com/Cross-Language-Soccer-Framework/cross-language-soccer-framework/assets/25696836/7b0b1d49-7001-479c-889f-46a96a8802c4)

![image](https://github.com/Cross-Language-Soccer-Framework/cross-language-soccer-framework/assets/25696836/d152797b-53f0-490f-a8dd-b8c0ef667317)

To run a game in the RoboCup Soccer Simulation 2D, you need to operate the rcssserver for hosting games, rcssmonitor to display them, and engage 12 agents (11 players and a coach) per team. Each cycle, agents receive data from the server and must execute actions such as dash and kick. Developing a team can be complex due to the environment's intricacy, typically necessitating C++ programming. However, our framework allows for Python development, leveraging the helios-base features. It introduces the playmaker-server, a Python-implemented server that interacts with the rcssserver via a proxy, managing environment states and agent actions based on the WorldModel from helios-base. Our defined protobuf schema ensures all environmental data is comprehensively covered, facilitating smooth communication between the playmaker server and the rcssserver.

To find more information about the framework, you can visit the [CLSFramework Wiki Pages](https://github.com/CLSFramework/cross-language-soccer-framework/wiki)

# RUN
To run a game by using the playmaker-server, you need to run rcssserver, rcssmonitor, soccer-simulation-proxy team, and the playmaker-server. To run each of them there some different solutions, you can find more information about them in the following list:

- [RCSSServer](https://github.com/CLSFramework/cross-language-soccer-framework/wiki/RoboCup-Soccer-Simulation-Server)
- [Rcssmonitor](https://github.com/CLSFramework/cross-language-soccer-framework/wiki/Soccer-Simulation-Monitor)
- [Soccer-Simulation-Proxy](https://github.com/CLSFramework/cross-language-soccer-framework/wiki/Soccer-Simulation-Proxy)

In this page, we will show the simplest way to start a game.

### Clone the repository
```bash
git clone git@github.com:CLSFramework/playmaker-server-python.git
cd playmaker-server-python
```

### Install ubuntu and python dependencies
```bash
sudo apt-get install fuse
python3 -m pip install -r requirements.txt
```

### Download rcssserver and soccer-simulation-proxy AppImages
```bash
chmod 777 download-server-proxy.sh
./download-server-proxy.sh
```

These commands will download the rcssserver and soccer-simulation-proxy AppImages. The rcssserver app-image is available in rcssserver directory and the soccer-simulation-proxy app-image is available in soccer-simulation-proxy directory. You can download the AppImages manually from the following links:
- [rcssserver](https://github.com/CLSFramework/rcssserver/releases)
- [soccer-simulation-proxy](https://github.com/CLSFramework/soccer-simulation-proxy/releases)

You can also build them from source code. You can find more information about building the rcssserver and the soccer-simulation-proxy in the following links:
- [rcssserver](https://github.com/CLSFramework/cross-language-soccer-framework/wiki/RoboCup-Soccer-Simulation-Server)
- [soccer-simulation-proxy](https://github.com/CLSFramework/cross-language-soccer-framework/wiki/Soccer-Simulation-Proxy)

### Run the rcssserver
The server should be run before the soccer-simulation-proxy agents.

```bash
cd rcssserver
./rcssserver-x86_64.AppImage
```

### Run Playmaker-Server (Python)
It would be better to run the Playmaker-Server in a separate terminal and before running the soccer-simulation-proxy agents.
```bash
python3 server.py
```

### Run the soccer-simulation-proxy
```bash
cd soccer-simulation-proxy
./start.sh
```

#### Some Notes:
Note that if you want to use the debug tools of the ```soccerwindow2```, you have to run the ```./start-debug.sh``` instead of the ```./start.sh```.

### Run all components in one command
```bash
./start-team.sh
```


Note: In the competition, the competition manager will use the ```start-team.sh``` to run the server and the agents. Also each player has to connecte to a different ```playermaker-server```.

# How It Works?
The [soccer-simulation-proxy](https://github.com/CLSFramework/cross-language-soccer-framework/wiki/Soccer-Simulation-Proxy) is a base that acts as an intermediate connection between the RCSSServer and the ```playmaker-server```. The soccer-simulation-proxy receives the observation and the information of the field from the RCSSServer and send them to the ```playmaker-server```. The ```playmaker-server``` receives the observation and the information of the field as a ```WorldModel``` class in the [```protobuf```](https://github.com/CLSFramework/cross-language-soccer-framework/wiki/Protobuf) from the Proxy base and sends the action to the Proxy base. The Proxy base receives the action from the ```playmaker-server``` and sends it to the RCSSServer, and this happens in each cycle of the game.

# Related Projects:
Also you can find some useful examples in the following repositories:

- [soccer-gym](https://github.com/CLSFramework/soccer-gym)
