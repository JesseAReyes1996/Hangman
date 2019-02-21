# Hangman

Written using Python 3.6.1

A terminal-based version of the classic multiplayer game Hangman. This project is meant to showcase my knowledge of concurrency (e.g. the Thread-local storage (TLS) concurrency pattern) as well as TCP/IP. The game is run by a server and clients connect to the server via Telnet. The server supports running multiple games at a time.

![](./images/hangman.png)

To run this game open up a minimum of two terminals. One terminal should be in the same directory as server.py.

Run ```python server.py``` in the terminal that is in the same directory as ```server.py```

The other terminal will connect to the server using Telnet.

Use the command ```telnet localhost 8238``` to connect to the server.
