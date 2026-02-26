# Mice-sleeper

Mice-sleeper is a multi-dimensional variation of the classic Minesweeper game, implemented in Python. 
This project was created as part of the MIT 6.1010 (Fundamentals of Programming) course.

## Features

- **2D Gameplay**: The standard Minesweeper experience with a customizable board size and number of mice.
- **N-Dimensional Gameplay**: Play Minesweeper in 3D, 4D, or any arbitrary number of dimensions.
- **Custom Implementations**: Complete logic for generating boards, placing mice, revealing cells, and flooding (revealing multiple safe adjacent cells at once) across any dimension.

## Files

- `lab.py`: Contains the core game logic for the 2D and N-D variants of Mice-sleeper.
- `server.py` & `ui/`: Contains the web-based user interface and HTTP server code to play the game in a browser.
- `test.py`: Comprehensive test suite to verify the game logic for multidimensional rules.

## How to Play

Run the server using Python to play the game via the web UI:
```bash
python3 server.py
```
Open your browser and navigate to the localhost port provided in the terminal.

## Running Tests

To run the unit tests and ensure all logic is functioning correctly:
```bash
pytest test.py
```
