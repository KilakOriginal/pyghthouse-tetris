import random
import logging

logging.basicConfig(level=logging.WARNING)

GRID_WIDTH = 10
GRID_HEIGHT = 14

COLOURS = { "RED" : [239, 86, 91],
            "PINK" : [220, 55, 186],
            "DARK_BLUE" : [31, 74, 202],
            "ORANGE" : [232, 128, 65],
            "YELLOW" : [215, 231, 81],
            "LIGHT_BLUE" : [82, 215, 232],
            "GREEN" : [76, 237, 79] }

SHAPES = { "T" : [(0, 0), (1, 0), (2, 0), (1, 1)],
           "O" : [(0, 0), (0, 1), (1, 0), (1, 1)],
           "J" : [(1, 0), (1, 1), (1, 2), (0, 2)],
           "L" : [(0, 0), (0, 1), (0, 2), (1, 2)],
           "S" : [(1, 0), (2, 0), (0, 1), (1, 1)],
           "Z" : [(0, 0), (1, 0), (1, 1), (2, 1)],
           "I" : [(0, 0), (0, 1), (0, 2), (0, 3)] }

DIRECTIONS = { "DOWN" : (0, 1),
               "LEFT" : (-1, 0),
               "RIGHT" : (1, 0) }

class Field:
    tetrominos: list
    score: int
    level: int
    currentLines: int

    def __init__(self):
        self.tetrominos = []
        self.level = 1
        self.score = 0
        self.currentLines = 0

    def clearCompletedRows(self):
        grid = [[0] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
        
        # Place blocks on the grid
        for tetromino in self.tetrominos:
            for x, y in tetromino.shape:
                if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                    grid[y][x] = 1
    
        completedRows = [y for y in range(GRID_HEIGHT) if all(grid[y])]
        
        if not completedRows:
            return
    
        # Update score and level
        match len(completedRows):
            case 1:
                self.score += 40 * self.level
            case 2:
                self.score += 100 * self.level
            case 3:
                self.score += 300 * self.level
            case 4:
                self.score += 1200 * self.level
    
        self.currentLines += len(completedRows)
    
        if self.currentLines >= 10:
            self.level += 1
            self.currentLines -= 10

        # Remove cleared rows and move down tetrominos above the cleared rows
        new_tetrominos = []
        for tetromino in self.tetrominos:
            newShape = []
            for (x, y) in tetromino.shape:
                # If the block is above the completed rows, move it down by the number of cleared rows
                if y < min(completedRows):
                    newShape.append((x, y + len(completedRows)))
                elif y not in completedRows:
                    newShape.append((x, y))
    
            if newShape:
                tetromino.shape = newShape
                new_tetrominos.append(tetromino)
    
        self.tetrominos = new_tetrominos

class Tetromino:
    colour: list[int]
    shape: list[tuple[int]]
    width: int
    height: int
    field: Field

    def __init__(self, field: Field):
        self.shape = [(x + 4, y) for (x, y) in random.choice(list(SHAPES.values()))]
        self.colour = random.choice(list(COLOURS.values()))
        self.width = self.__getWidth()
        self.height = self.__getHeight()
        self.field = field

    def rotate(self):
        # Find the bounding box for the current shape
        min_x = min(x for x, y in self.shape)
        min_y = min(y for x, y in self.shape)
        max_x = max(x for x, y in self.shape)
        max_y = max(y for x, y in self.shape)

        # Calculate the center of the bounding box
        center_x = (min_x + max_x) // 2
        center_y = (min_y + max_y) // 2

        # Rotate each block around the center
        newShape = []
        for x, y in self.shape:
            # Translate block to origin
            trans_x = x - center_x
            trans_y = y - center_y
            # Rotate 90 degrees clockwise
            new_x = trans_y
            new_y = -trans_x
            # Translate block back
            newShape.append((new_x + center_x, new_y + center_y + 1))

        # Check if the new shape is within the bounds of the grid and does not collide with other tetrominos
        if self.__isValidPosition(newShape):
            self.shape = newShape
            self.width, self.height = self.height, self.width
        else:
            logging.debug("Cannot rotate")

    def move(self, direction: str):
        match direction:
            case "DOWN":
                if not self.hasCollidedBottom():
                    self.shape = [tuple(map(lambda x, y: x + y, p, DIRECTIONS["DOWN"])) for p in self.shape]
                else:
                    logging.debug("Cannot move down")
                return
            case "LEFT":
                if not self.hasCollidedLeft():
                    self.shape = [tuple(map(lambda x, y: x + y, p, DIRECTIONS["LEFT"])) for p in self.shape]
                else:
                    logging.debug("Cannot move left")
                return
            case "RIGHT":
                if not self.hasCollidedRight():
                    self.shape = [tuple(map(lambda x, y: x + y, p, DIRECTIONS["RIGHT"])) for p in self.shape]
                else:
                    logging.debug("Cannot move right")
                return
            case _:
                logging.debug("Invalid direction")

    def __getWidth(self):
        return abs(min(self.shape, key=lambda x: x[0])[0] - max(self.shape, key=lambda x: x[0])[0])

    def __getHeight(self):
        return abs(min(self.shape, key=lambda y: y[1])[1] - max(self.shape, key=lambda y: y[1])[1])

    def __hasCollidedBottom(self, other):
        candidates = {p[0] for p in other.shape} & {p[0] for p in self.shape}

        if not candidates:
            return False

        for p in self.shape:
            x1, y1 = p
            if x1 in candidates:
                for q in other.shape:
                    x2, y2 = q
                    if x1 == x2 and y1 + 1 == y2:
                        return True

        return False

    def __hasCollidedRight(self, other):
        candidates = {p[1] for p in other.shape} & {p[1] for p in self.shape}

        if not candidates:
            return False

        for p in self.shape:
            x1, y1 = p
            if y1 in candidates:
                for q in other.shape:
                    x2, y2 = q
                    if y1 == y2 and x1 + 1 == x2:
                        return True

        return False

    def __hasCollidedLeft(self, other):
        candidates = {p[1] for p in other.shape} & {p[1] for p in self.shape}

        if not candidates:
            return False

        for p in self.shape:
            x1, y1 = p
            if y1 in candidates:
                for q in other.shape:
                    x2, y2 = q
                    if y1 == y2 and x1 - 1 == x2:
                        return True

        return False

    def __isValidPosition(self, shape):
        for (x, y) in shape:
            if not (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT):
                return False

        for tetromino in self.field.tetrominos:
            if (x, y) in tetromino.shape:
                return False

        return True

    def hasCollidedBottom(self):
        for block in self.shape:
            if  block[1] >= 13:
                return True

        for tetromino in self.field.tetrominos:
            if self.__hasCollidedBottom(tetromino):
                return True
        return False

    def hasCollidedRight(self):
        for block in self.shape:
            if block[0] >= 9:
                return True

        for tetromino in self.field.tetrominos:
            if self.__hasCollidedRight(tetromino):
                return True
        return False

    def hasCollidedLeft(self):
        for block in self.shape:
            if block[0] <= 0:
                return True

        for tetromino in self.field.tetrominos:
            if self.__hasCollidedLeft(tetromino):
                return True
        return False
