# Pygame Chess

Implimentation of chess in python using Pygame

To start a local game, run this command:
```
python3 ./PygameChess.py
```

To start a hosted chess server, run:
```
python3 ./ChessServer.py --host $HOST_IP --port $PORT -c $MAX_CONNS
```

To connect a client instance to the server:
```
python3 ./ClientBoard.py $HOST_IP $PORT
```
The board will render when the server pairs you to another player