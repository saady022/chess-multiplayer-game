# ♟️ Multiplayer Chess Game

A real-time multiplayer chess game developed as a semester project.
Built with **Python**, **Pygame** for the graphical interface, and the **python-chess** library for game logic.  
The project uses a **client-server architecture with TCP sockets**, enabling two players to play online while spectators can join and watch.  

The game includes a clean GUI with a sky-themed background, chat system, and timers for an engaging experience.

---

## 🚀 Features
- 🔗 Real-time gameplay with synchronized moves between two players  
- 👀 Spectator mode to watch live games  
- 💬 Chat functionality for in-game communication  
- ⏱️ Timers tracking each player’s remaining time  
- 🎨 Custom GUI with a chessboard, labeled squares, and sky background  

---

## 📦 Prerequisites
- **Python 3.x**  
- Required libraries:  
  ```bash
  pip install pygame python-chess
##project structure
MultiplayerChess/
│── server.py         # Manages client connections, game creation, and synchronization
│── client.py         # Pygame GUI, user input, and communication with the server
│── chess_logic.py    # Core chess logic using python-chess
│── assets/           # Chess piece images and background image

🖼️ Assets

Place the following inside the assets/ folder:

Chess Pieces

White: wp.png, wr.png, wn.png, wb.png, wq.png, wk.png

Black: bp.png, br.png, bn.png, bb.png, bq.png, bk.png

Background

sky_background.jpg (recommended size: 800x600)

⚠️ Make sure file names match exactly.

▶️ How to Run
1. Run the Server
cd MultiplayerChess
python server.py


Server runs on port 5555 (keep terminal open).

2. Run Clients

Open another terminal for each client (two for players, optional more for spectators).

python client.py


Players will be paired automatically (assigned White or Black).

To run as a spectator:

python client.py --mode spectator

3. Gameplay

🎮 Players click squares to select and move pieces.

💬 Type messages + press Enter to chat.

👀 Spectators can join, watch the match, and chat (but not move pieces).

⏱️ Timers update based on turn.
