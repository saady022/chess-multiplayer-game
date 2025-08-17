import socket
import threading
import json
import pygame
import chess
import sys
import time
import os
import argparse

class ChessClient:
    def __init__(self, host='127.0.0.1', port=5555, mode="player"):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.mode = mode
        self.connect()
        self.board = chess.Board()
        self.color = None
        self.game_id = None
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Multiplayer Chess")
        self.clock = pygame.time.Clock()
        self.chat_messages = []
        self.input_text = ""
        self.selected_square = None
        self.running = True
        self.disconnected = False

        # Load background image
        self.background = pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets', 'sky_background.jpg')).convert()
        self.background = pygame.transform.scale(self.background, (800, 600))

        # Load chess piece images
        self.piece_images = {}
        assets_path = os.path.join(os.path.dirname(__file__), 'assets')
        print(f"Looking for assets in: {assets_path}")
        piece_symbols = {
            'p': 'p', 'r': 'r', 'n': 'n', 'b': 'b', 'q': 'q', 'k': 'k'
        }
        for color in ['w', 'b']:
            for symbol, name in piece_symbols.items():
                filename = f"{color}{name}.png"
                filepath = os.path.join(assets_path, filename)
                if os.path.exists(filepath):
                    try:
                        image = pygame.image.load(filepath).convert_alpha()
                        self.piece_images[f"{color}{symbol}"] = pygame.transform.scale(image, (50, 50))
                        print(f"Loaded image: {filename}")
                    except pygame.error as e:
                        print(f"Error loading {filename}: {e}")
                else:
                    print(f"Warning: Image {filename} not found at {filepath}")

    def connect(self):
        try:
            self.client.connect((self.host, self.port))
        except Exception as e:
            print(f"Connection failed: {e}")
            self.running = False

    def send_initial_message(self):
        try:
            self.client.send(json.dumps({"type": self.mode}).encode() + b"\n")
            if self.mode == "spectator":
                data = self.client.recv(1024).decode()
                message = json.loads(data)
                if message.get("action") == "game_list":
                    print("Available games:", message["games"])
                    game_id = input("Enter game ID to spectate (or press Enter to join first available): ")
                    if not game_id:
                        game_id = message["games"][0] if message["games"] else None
                    if game_id:
                        self.game_id = int(game_id)
                        self.client.send(json.dumps({"game_id": int(game_id)}).encode() + b"\n")
        except Exception as e:
            print(f"Error sending initial message: {e}")
            self.running = False

    def draw_board(self):
        square_size = 50
        self.screen.blit(self.background, (0, 0))  # Draw background first
        for row in range(8):
            for col in range(8):
                color = (181, 136, 99) if (row + col) % 2 == 0 else (240, 217, 181)  # Wood-like colors
                pygame.draw.rect(self.screen, color, (col * square_size, row * square_size, square_size, square_size))
                piece = self.board.piece_at(chess.square(col, 7 - row))
                if piece:
                    piece_symbol = piece.symbol().lower()
                    color_symbol = 'w' if piece.color == chess.WHITE else 'b'
                    key = f"{color_symbol}{piece_symbol}"
                    if key in self.piece_images:
                        self.screen.blit(self.piece_images[key], (col * square_size, row * square_size))
                # Add labels for files (a-h) and ranks (1-8)
                font = pygame.font.Font(None, 20)
                if row == 7:
                    text = font.render(chr(97 + col), True, (0, 0, 0))
                    self.screen.blit(text, (col * square_size + 20, 7 * square_size + 5))
                if col == 0:
                    text = font.render(str(8 - row), True, (0, 0, 0))
                    self.screen.blit(text, (5, row * square_size + 20))
        if self.selected_square is not None and self.mode == "player":
            col, row = chess.square_file(self.selected_square), 7 - chess.square_rank(self.selected_square)
            pygame.draw.rect(self.screen, (0, 255, 0, 100), (col * square_size, row * square_size, square_size, square_size), 3)

    def draw_chat(self):
        font = pygame.font.Font(None, 20)  # Reduced font size from 24 to 20
        # Moved chat box up to y=100
        chat_box = pygame.Rect(420, 100, 350, 200)  # Reduced height from 250 to 200
        pygame.draw.rect(self.screen, (255, 255, 255, 200), chat_box)
        y = 110
        for msg in self.chat_messages[-6:]:  # Adjusted to show last 6 messages
            text = font.render(msg, True, (0, 0, 0))
            self.screen.blit(text, (430, y))
            y += 20  # Reduced line spacing
        input_box = pygame.Rect(420, 300, 350, 30)  # Adjusted position to y=300
        pygame.draw.rect(self.screen, (255, 255, 255), input_box)
        input_text = font.render(f"> {self.input_text}", True, (0, 0, 0))
        self.screen.blit(input_text, (430, 305))

    def draw_timers(self):
        font = pygame.font.Font(None, 28)  # Reduced font size from 36 to 28
        white_time = self.board.white_time if hasattr(self.board, 'white_time') else 600
        black_time = self.board.black_time if hasattr(self.board, 'black_time') else 600
        # Adjusted positions below chat box
        white_text = font.render(f"White: {int(white_time)}s", True, (255, 255, 255))
        black_text = font.render(f"Black: {int(black_time)}s", True, (255, 255, 255))
        self.screen.blit(white_text, (420, 340))  # Adjusted to y=340
        self.screen.blit(black_text, (420, 370))  # Adjusted to y=370

    def handle_click(self, pos):
        if self.mode == "player":
            square_size = 50
            col, row = pos[0] // square_size, pos[1] // square_size
            square = chess.square(col, 7 - row)
            if self.selected_square is None:
                if self.board.piece_at(square) and self.board.piece_at(square).color == self.color:
                    self.selected_square = square
            else:
                move = chess.Move(self.selected_square, square)
                if move in self.board.legal_moves and self.game_id is not None:
                    uci_move = move.uci()
                    try:
                        self.client.send(json.dumps({"action": "move", "move": uci_move, "game_id": self.game_id}).encode() + b"\n")
                        print(f"Sent move: {uci_move}")
                    except:
                        self.chat_messages.append("Error: Failed to send move. Reconnecting...")
                        self.reconnect()
                self.selected_square = None

    def reconnect(self):
        self.disconnected = True
        self.client.close()
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect()
        if self.running and self.game_id:
            self.client.send(json.dumps({"action": "reconnect", "game_id": self.game_id}).encode() + b"\n")
            self.disconnected = False

    def receive_messages(self):
        buffer = ""
        while self.running:
            try:
                data = self.client.recv(1024).decode()
                if not data:
                    self.disconnected = True
                    break
                buffer += data
                while "\n" in buffer:
                    message_end = buffer.index("\n")
                    message_str = buffer[:message_end].strip()
                    buffer = buffer[message_end + 1:].strip()
                    if message_str:
                        try:
                            message = json.loads(message_str)
                            print(f"Received ({self.mode}): {message}")
                            action = message.get("action")
                            if action == "start":
                                self.color = chess.WHITE if message["color"] == "white" else chess.BLACK
                                self.game_id = message["game_id"]
                            elif action == "update":
                                self.board = chess.Board(message["state"]["fen"])
                                self.board.white_time = message["state"]["white_time"]
                                self.board.black_time = message["state"]["black_time"]
                                turn = message["state"]["turn"]
                                print(f"Current turn: {turn.capitalize()}")
                            elif action == "chat":
                                self.chat_messages.append(message["message"])
                            elif action == "error":
                                self.chat_messages.append(f"Error: {message['message']}")
                            elif action == "opponent_disconnected":
                                self.chat_messages.append("Opponent disconnected. Waiting for reconnection...")
                                self.disconnected = True
                            elif action == "reconnected":
                                self.chat_messages.append("Reconnected to game!")
                                self.disconnected = False
                            elif action == "game_over":
                                self.chat_messages.append(f"Game Over: {message['reason']}")
                                self.running = False
                        except json.JSONDecodeError as e:
                            print(f"JSON decode error: {e}, Buffer: {message_str[:50]}...")
                            continue
            except Exception as e:
                print(f"Receive error: {e}")
                self.disconnected = True
                break

        if self.disconnected and self.running:
            self.reconnect()

    def run(self):
        self.send_initial_message()
        threading.Thread(target=self.receive_messages, daemon=True).start()
        pygame.init()
        font = pygame.font.Font(None, 36)
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and self.color is not None and not self.disconnected:
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if self.input_text:
                            try:
                                self.client.send(json.dumps({"action": "chat", "message": self.input_text}).encode() + b"\n")
                                self.chat_messages.append(f"You: {self.input_text}")
                                self.input_text = ""
                            except:
                                self.chat_messages.append("Error: Failed to send chat. Reconnecting...")
                                self.reconnect()
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                    else:
                        self.input_text += event.unicode

            self.draw_board()
            self.draw_chat()
            self.draw_timers()
            if self.mode == "spectator":
                font = pygame.font.Font(None, 24)  # Reduced from 30 to 24
                text = font.render("Spectator Mode", True, (255, 255, 255))
                self.screen.blit(text, (420, 90))  # Adjusted to y=90
            pygame.display.flip()
            self.clock.tick(60)

        self.client.close()
        pygame.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multiplayer Chess Client")
    parser.add_argument("--mode", choices=["player", "spectator"], default="player", help="Mode to join as (player or spectator)")
    args = parser.parse_args()
    client = ChessClient(mode=args.mode)
    client.run()