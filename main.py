import os
import random
import threading
from pyghthouse import Pyghthouse
from time import sleep, time
from tetromino import Tetromino, Field
import curses
import math

USER_NAME = os.environ.get('USER_NAME')
API_TOKEN = os.environ.get('API_TOKEN')

GRID_WIDTH = 10
SCREEN_WIDTH = 28
GRID_HEIGHT = SCREEN_HEIGHT = 14

def printInstructions(stdscr):
    stdscr.clear()

    instructions = """
    Welcome to Pyghthouse Tetris!
    The goal of the game is to clear as many rows as possible.
    You can clear a row by filling it completely with tetrominos.
    The game is over when a tetromino reaches the top of the grid.
    The game gets faster as you clear more rows.

    ==============================================================

    Use the arrow keys to move the tetromino.
    Use the up arrow key to rotate the tetromino.
    Press 'R' to restart the game.
    Press 'Q' to quit the game.

    Press any key to start the game...
    """

    stdscr.addstr(0, 0, instructions)
    stdscr.refresh()
    stdscr.getch()

def printGameOver(stdscr):
    stdscr.clear()

    gameOver = """
    Game Over!
    Press 'R' to restart the game.
    Press 'Q' to quit the game.
    """

    stdscr.addstr(0, 0, gameOver)
    stdscr.refresh()

def initialiseGrid():
    return [[[0, 0, 0] for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

def getRainbowColour(t, total_steps):
    frequency = 0.1
    red = int(math.sin(frequency * t + 0) * 127 + 128)
    green = int(math.sin(frequency * t + 2) * 127 + 128)
    blue = int(math.sin(frequency * t + 4) * 127 + 128)
    return [red, green, blue]

def render(grid, field, current_tetromino, next_tetromino, frame, stdscr):
    image = [[[0, 0, 0] for _ in range(SCREEN_WIDTH)] for _ in range(SCREEN_HEIGHT)]
    
    # Create terminal grid using curses
    stdscr.clear()

    for y in range(GRID_HEIGHT + 2):  # Include borders
        for x in range(GRID_WIDTH + 2):
            if y == 0 or y == GRID_HEIGHT + 1:
                stdscr.addstr(y, x * 2, "□", curses.color_pair(1))
            elif x == 0 or x == GRID_WIDTH + 1:
                stdscr.addstr(y, x * 2, "□", curses.color_pair(1))
            else:
                # Check if there is a tetromino block in the grid
                block = None
                for tetromino in field.tetrominos:
                    if (x - 1, y - 1) in tetromino.shape:  # Adjust for border offset
                        block = tetromino.colour
                if (x - 1, y - 1) in current_tetromino.shape:
                    block = current_tetromino.colour

                if block:
                    stdscr.addstr(y, x * 2, "■", curses.color_pair(1))  # Block
                else:
                    stdscr.addstr(y, x * 2, "  ")  # Empty space

    # Display next tetromino on the side
    stdscr.addstr(0, (GRID_WIDTH + 2) * 2 + 3, "Next Tetromino:")
    for (x, y) in next_tetromino.shape:
        stdscr.addstr(y + 2, (GRID_WIDTH + 2) * 2 + 3 + (x * 2), "■", curses.color_pair(1))

    stdscr.refresh()

    # Display the score and level below the next tetromino
    stdscr.addstr(10, (GRID_WIDTH + 2) * 2 + 3, f"Score: {field.score}")
    stdscr.addstr(11, (GRID_WIDTH + 2) * 2 + 3, f"Level: {field.level}")

    # Render tetrominos on Pyghthouse
    for tetromino in field.tetrominos:
        for (x, y) in tetromino.shape:
            if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                image[y][x] = tetromino.colour

    for (x, y) in current_tetromino.shape:
        if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
            image[y][x] = current_tetromino.colour

    # Rainbow effect for Pyghthouse right border (columns 10 and 11)
    for x in range(10, 12):
        for y in range(GRID_HEIGHT):
            colour = getRainbowColour((y + frame) % 256, 256)
            image[y][x] = colour

    # Display next tetromino on Pyghthouse
    center_x = GRID_WIDTH + ((SCREEN_WIDTH - GRID_WIDTH) // 2) - next_tetromino.width // 2 - 3
    center_y = SCREEN_HEIGHT // 2 - next_tetromino.height // 2 - 1
    for (x, y) in next_tetromino.shape:
        if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
            image[center_y + y][center_x + x - 1] = next_tetromino.colour

    return image

def check_game_over(tetromino, field):
    for block in tetromino.shape:
        for other in field.tetrominos:
            if block in other.shape:
                return True
    return False

def game_tick(field, currentTetromino, nextTetromino, speed, stop_thread, pause_flag, stdscr):
    while not stop_thread.is_set():
        # If the game is paused, skip game tick
        if pause_flag.is_set():
            sleep(0.1)
            continue
        
        currentTetromino[0].move("DOWN")

        if currentTetromino[0].hasCollidedBottom():
            field.tetrominos.append(currentTetromino[0])

            field.clearCompletedRows()

            currentTetromino[0] = nextTetromino[0]
            nextTetromino[0] = Tetromino(field)

            if check_game_over(currentTetromino[0], field):
                printGameOver(stdscr)
                stop_thread.set()

        sleep(speed)

def main(stdscr):
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)

    curses.curs_set(0)
    stdscr.nodelay(False)

    printInstructions(stdscr)
    
    stdscr.nodelay(True)
    stdscr.timeout(200)

    pyghthouse = Pyghthouse(USER_NAME, API_TOKEN)
    pyghthouse.start()

    quit_game = False
    restart_game = True
    stop_thread = threading.Event()
    pause_flag = threading.Event()

    while not quit_game:
        if restart_game:
            restart_game = False

            # Initialize game elements
            grid = initialiseGrid()
            field = Field()
            currentTetromino = [Tetromino(field)]
            nextTetromino = [Tetromino(field)]
            speed = 1.0 / (1 + field.level * 0.1)
            frame = 0

            stop_thread.clear()

            # Start the game thread
            game_thread = threading.Thread(target=game_tick, args=(field, currentTetromino, nextTetromino, speed, stop_thread, pause_flag, stdscr))
            game_thread.start()

        # Handle key presses
        key = stdscr.getch()

        if key == ord('q'):
            quit_game = True
            stop_thread.set()
            game_thread.join()  # Ensure the thread terminates
        elif key == curses.KEY_LEFT:
            currentTetromino[0].move("LEFT")
        elif key == curses.KEY_RIGHT:
            currentTetromino[0].move("RIGHT")
        elif key == curses.KEY_DOWN:
            currentTetromino[0].move("DOWN")
        elif key == curses.KEY_UP:
            currentTetromino[0].rotate()
        elif key == ord('r'):
            stop_thread.set()
            game_thread.join()
            restart_game = True

        # Render the game
        image = render(grid, field, currentTetromino[0], nextTetromino[0], frame, stdscr)
        pyghthouse.set_image(image)

        frame += 1
        speed = 1.0 / (1 + field.level * 0.1)

    pyghthouse.stop()

if __name__ == '__main__':
    curses.wrapper(main)
