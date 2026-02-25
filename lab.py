#!/usr/bin/env python3
"""
6.101 Lab:
Mice-sleeper
"""

# import typing  # optional import
# import pprint  # optional import
from numpy.testing import clear_and_catch_warnings
import doctest

# NO ADDITIONAL IMPORTS ALLOWED!


def dump(game, all_keys=False):
    """
    Prints a human-readable version of a game (provided as a dictionary)

    By default uses only "board", "dimensions", "state", "visible" keys (used
    by doctests). Setting all_keys=True shows all game keys.
    """
    if all_keys:
        keys = sorted(game)
    else:
        keys = ("board", "dimensions", "state", "visible")
        # Use only default game keys. If you modify this you will need
        # to update the docstrings in other functions!

    for key in keys:
        val = game[key]
        if isinstance(val, list) and val and isinstance(val[0], list):
            print(f"{key}:")
            for inner in val:
                print(f"    {inner}")
        else:
            print(f"{key}:", val)

# HELPER FUNCTION

def get_neighbor(row, col, game):
    """
    Finds all the adjacent neighbor of (row, col)
    """
    dimensions = game['dimensions']
    adjacent = [(-1, 0), (0, -1), (-1,-1), (1,1),(0,1),(1, 0),(1, -1), (-1, 1)]
    ret = []
    for n in adjacent:
        del_row, del_col = row + n[0], col + n[1]
        if((0 <= del_row < dimensions[0]) and (0 <= del_col < dimensions[1])):
            ret.append((del_row, del_col))
    return ret

            

# 2-D IMPLEMENTATION


def new_game_2d(nrows, ncolumns, num_mice):
    """
    Start a new game.

    Return a game state dictionary, with the 'dimensions', 'state', 'board' and
    'visible' fields adequately initialized.

    Parameters:
       nrows (int): Number of rows
       ncolumns (int): Number of columns
       num_mice (int): The number of mice to be added to the board

    Returns:
       A game state dictionary

    >>> dump(new_game_2d(2, 4, 3))
    board:
        [0, 0, 0, 0]
        [0, 0, 0, 0]
    dimensions: (2, 4)
    state: ongoing
    visible:
        [False, False, False, False]
        [False, False, False, False]
    """
    return {
        "dimensions": (nrows, ncolumns),
        'state' : "ongoing",
        "board" : [[0] * ncolumns for _ in range(nrows)],
        "visible": [[False] * ncolumns for _ in range(nrows)], 
        "mice" : num_mice
    }



def place_mice_2d(game, num_mice, disallowed):
    """
    Add mice to the given game, subject to limitations on where they may be
    placed.  The first num_mice valid locations from an appropriate
    random_coordinates generator should be used.

    Parameters:
       game (dict): game state
       num_mice (int): the number of mice to be added
       disallowed (set): a set of (r, c) locations where mice cannot be placed

    This function works by mutating the given game, and it always returns None

    >>> g = new_game_2d(2, 2, 2)
    >>> place_mice_2d(g, 2, set())
    >>> dump(g)
    board:
        [2, 'm']
        [2, 'm']
    dimensions: (2, 2)
    state: ongoing
    visible:
        [False, False]
        [False, False]

    >>> g = new_game_2d(2, 2, 2)
    >>> place_mice_2d(g, 2, {(0, 1), (1, 0)})
    >>> dump(g)
    board:
        ['m', 2]
        [2, 'm']
    dimensions: (2, 2)
    state: ongoing
    visible:
        [False, False]
        [False, False]
    """
    mice_list = set()
    adjacent = [(-1, 0), (0, -1), (-1,-1), (1,1),(0,1),(1, 0),(1, -1), (-1, 1)]
    row, col = game['dimensions']
    for n in random_coordinates(game["dimensions"]):
        if(n not in disallowed):
            if n not in mice_list:
                mice_list.add(n)
        if(len(mice_list) == num_mice):
            break
    for coordinates in mice_list:
        r,c = coordinates
        game['board'][r][c] = 'm'    
    
    for r in range(row):
        for c in range(col):
            count = 0
            if((r,c) in mice_list):
                continue
            for neighbor in adjacent:
                del_r, del_c = neighbor
                if((0 <= (r + del_r) < row) and (0 <= (c + del_c) < col)):
                    if(game['board'][r + del_r][c + del_c] == 'm'):
                        count += 1
            game['board'][r][c] = count

    



def reveal_2d(game, row, col):
    """
    Reveal the cell at (row, col), and, in some cases, recursively reveal its
    neighboring squares.

    Update game['visible'] to reveal (row, col).  Then, if (row, col) has no
    adjacent mice (including diagonally), then recursively reveal its eight
    neighbors.  Return an integer indicating how many new squares were revealed
    in total, including neighbors, and neighbors of neighbors, and so on.

    If this is the first reveal performed in a game, then before performing
    the reveal operation, we add the appropriate number of mice to the game
    (the number given at initialization time).  No mice should be placed in
    the location to be revealed, nor in any of its neighbors.

    The state of the game should be changed to 'lost' when at least one mouse
    is visible on the board, 'won' when all safe squares (squares that do not
    contain a mouse) and no mice are visible, and 'ongoing' otherwise.

    If the game is not ongoing, or if the given square has already been
    revealed, reveal_2d should not reveal any squares.

    Parameters:
       game (dict): Game state
       row (int): Where to start revealing cells (row)
       col (int): Where to start revealing cells (col)

    Returns:
       int: the number of new squares revealed

    >>> game = new_game_2d(2, 4, 3)
    >>> reveal_2d(game, 0, 3)
    4
    >>> dump(game)
    board:
        [3, 'm', 2, 0]
        ['m', 'm', 2, 0]
    dimensions: (2, 4)
    state: ongoing
    visible:
        [False, False, True, True]
        [False, False, True, True]
    >>> reveal_2d(game, 0, 0)
    1
    >>> dump(game)
    board:
        [3, 'm', 2, 0]
        ['m', 'm', 2, 0]
    dimensions: (2, 4)
    state: won
    visible:
        [True, False, True, True]
        [False, False, True, True]
    """
    #If game is not ongoing or the square is already revealed
    if(game['state'] != 'ongoing' or game['visible'][row][col] == True):
        return 0

    #If it is first time playing
    visible = game['visible']
    first_time = True
    dimensions = game['dimensions']
    disallowed = set()
    adjacent = [(-1, 0), (0, -1), (-1,-1), (1,1),(0,1),(1, 0),(1, -1), (-1, 1)]
    num_mice = game['mice']
    for r in range(len(visible)):
        for c in range(len(visible[0])):
            if(visible[r][c] == True):
                first_time = False
    
    if(first_time):
        disallowed.add((row, col))
        for change in adjacent:
            del_row, del_col = row + change[0], col + change[1]
            if(0 <= del_row < dimensions[0] and 0 <= del_col < dimensions[1]):
                disallowed.add((del_row, del_col))
    
        place_mice_2d(game, num_mice, disallowed)

    if(game['board'][row][col] == 'm'):
        game['visible'][row][col] = True
        game['state'] = "lost"
        return 1
    
    #Flood Fill Step
    visited = {(row, col)}
    count = 0
    def flood_fill(r, c):
        nonlocal count
        if(game["visible"][r][c] == False):
            game["visible"][r][c] = True
            count += 1
        if(game['board'][r][c] != 0):
            return
        for neighbor in get_neighbor(r, c, game):
            if(neighbor not in visited):
                visited.add(neighbor)
                flood_fill(neighbor[0], neighbor[1])
    #Check if we won the game
    flood_fill(row, col)
    all_mice_loc = set()
    won = True
    for r in range(len(game['board'])):
        for c in range(len(game['board'][0])):
            if(game['board'][r][c] == 'm'):
                all_mice_loc.add((r ,c))
    for r in range(len(game['visible'])):
        for c in range(len(game['visible'][0])):
            if((r, c) not in all_mice_loc):
                if(game['visible'][r][c] == False):
                    won = False
                    break
    if(won == True):
        game['state'] = "won"
    

    return count






def render_2d(game, all_visible=False):
    """
    Prepare a game for display.

    Returns a two-dimensional array (list of lists) of '_' (hidden squares),
    'm' (mice), ' ' (empty squares), or '1', '2', etc. (squares neighboring
    mice).  game['visible'] indicates which squares should be visible.  If
    all_visible is True (the default is False), game['visible'] is ignored and
    all cells are shown.

    Parameters:
       game (dict): Game state
       all_visible (bool): Whether to reveal all tiles or just the ones allowed
                    by game['visible']

    Returns:
       A 2D array (list of lists)

    >>> game = new_game_2d(2, 4, 3)
    >>> reveal_2d(game, 0, 0)
    4
    >>> render_2d(game, False)
    [[' ', '1', '_', '_'], [' ', '1', '_', '_']]
    >>> render_2d(game, True)
    [[' ', '1', 'm', 'm'], [' ', '1', '3', 'm']]
    >>> reveal_2d(game, 0, 3)
    1
    >>> render_2d(game, False)
    [[' ', '1', '_', 'm'], [' ', '1', '_', '_']]
    """
    nrows = game['dimensions'][0]
    ncols = game['dimensions'][1]
    res = [[0] * ncols for _ in range(nrows)]
    if(all_visible):
        for row in range(len(game['board'])):
            for col in range(len(game['board'][0])):
                if(game['board'][row][col] == 0):
                    res[row][col] = ' '
                else:
                    res[row][col] = str(game['board'][row][col])
    else:
        for row in range(len(game['board'])):
            for col in range(len(game['board'][0])):
                if(game['visible'][row][col] == False):
                    res[row][col] = "_"
                else:
                    if(game['board'][row][col] == 0):
                        res[row][col] = ' '
                    else:
                        res[row][col] = str(game['board'][row][col])
    
    return res






def get_cross(coordinates):
    """
    Gets the cross lists for all combinations of coordinates
    """
    adjacent = [-1,0,1]
    res = []
    for c in coordinates:
        tmp = []
        for adj in adjacent:
            tmp.append(c + adj)
        
        res.append(tmp)
    return res
  




def get_n(cross):
    """
    Gets all neighbors
    """
    def get_combinations(cross):
        """
        Helper func
        """
        if not cross:
            return [[]]
        else:
            first = cross[0]
            rest = get_combinations(cross[1:])
            first_seq = []
            for seq in rest:
                for items in first:
                    if(seq != []):
                        if(type(seq) != int):
                            first_seq.append((items, *seq))
                        else:
                            first_seq.append((items, seq))
                    else:
                        first_seq.append(items)
            return first_seq
    return get_combinations(cross)










def in_bound(coordinate, game):
    """
    Checks if a coordinate is in bound
    """
    dimension = game['dimensions']
    for d,c in zip(dimension, coordinate):
        if(not(0 <= c  < d)):
            return False
    return True



def get_coordinate(coordinate, game, board):
    """
    Gets the cell from a coordinate
    """
    if(len(coordinate) == 1):
        game[board][coordinate]
    curr_board = game[board]
    for i in range(len(coordinate) -1):
        curr_board = curr_board[coordinate[i]]
    return curr_board[coordinate[-1]]
   
             

def set_coordinate(coordinate, game, thingtoSet, board):
    """
    Sets the coordinate to the value specified by the user
    """
    if(len(coordinate) == 1):
        game[board][coordinate] = thingtoSet
        return
    curr_board = game[board]
    for i in range(len(coordinate) - 1):
        curr_board = curr_board[coordinate[i]]
    curr_board[coordinate[-1]] = thingtoSet
   



def deepcopy(x):
    """
    Creates a deepcopy of a nested list, this will
    probably only work for this lab as it assumes if the 
    first number is not a list, rest won't be
    """
    res = []
    if(not x):
        return []
    if not(isinstance(x[0], list)):
        return x.copy()
    else:
        first = deepcopy(x[0])
        rest = deepcopy(x[1:])
        rest.append(first.copy())
        return rest
        

def check_first_nd(game):
    """
    This checks if the game is played first time
    """
    if(not game):
        return True
    if not(isinstance(x[0] , list)):
        for i in range(len(x)):
            if(x[i] == True):
                return False
        return True
    else:
        first = check_won_nd(game[0])
        rest = check_won_nd(game[1:])
        return first and rest

def gen_coordinates(cross):
    """
    Generates all possible coordinates of arbitrary depth
    """
    res = []
    if (len(cross) ==  1):
        for i in range(cross[0]):
            res.append((i,))
        return res
    else:
        first = cross[0]
        rest = gen_coordinates(cross[1:])
        first_seq = []
        for seq in rest:
            for i in range(first):
                first_seq.append((i, *seq))
        return first_seq
coordinates = (2,4,2)
print(gen_coordinates(coordinates))




# N-D IMPLEMENTATION


def new_game_nd(dimensions, num_mice):
    """
    Start a new game.

    Return a game state dictionary, with the 'dimensions', 'state', 'board' and
    'visible' fields adequately initialized.

    Parameters:
       dimensions (sequence): Dimensions of the board
       num_mice (int): The number of mice to be added to the board

    Returns:
       A game state dictionary

    >>> g = new_game_nd((2, 4, 2), 3)
    >>> dump(g)
    board:
        [[0, 0], [0, 0], [0, 0], [0, 0]]
        [[0, 0], [0, 0], [0, 0], [0, 0]]
    dimensions: (2, 4, 2)
    state: ongoing
    visible:
        [[False, False], [False, False], [False, False], [False, False]]
        [[False, False], [False, False], [False, False], [False, False]]
    """
    lstDim = list(dimensions)
    def recurList(x, lstDim):
        """
        Returns a list of arbitary depth
        """
        res = []
        if not lstDim:
            return x.copy()
        else:
            a = lstDim[0]
            dim = recurList(x.copy(), lstDim[1:]) 
            for j in range(a):
                tmp = deepcopy(dim)
                res.append(tmp[::-1])
        return res.copy()
        
    board = recurList([0] * dimensions[-1], lstDim[0 : len(dimensions) - 1])
    visible = recurList([False] * dimensions[-1], lstDim[0 : len(dimensions) - 1])
    return {
        "dimensions" : dimensions,
        "state" : "ongoing",
        "board" : board,
        "visible" : visible,
        "mice" : num_mice
    }

#print(new_game_nd((2,4,2), 2))

def place_mice_nd(game, num_mice, disallowed):
    """
    Add mice to the given game, subject to limitations on where they may be
    placed.  The first num_mice valid locations from an appropriate
    random_coordinates generator should be used.

    Parameters:
       game (dict): game state
       num_mice (int): the number of mice to be added
       disallowed (set): a set of tuples, each representing a location where
                         mice cannot be placed

    This function works by mutating the given game, and it always returns None

    >>> g = new_game_nd((2, 2, 2), 2)
    >>> place_mice_nd(g, 2, set())
    >>> dump(g)
    board:
        [[2, 2], [2, 2]]
        [['m', 'm'], [2, 2]]
    dimensions: (2, 2, 2)
    state: ongoing
    visible:
        [[False, False], [False, False]]
        [[False, False], [False, False]]


    >>> g = new_game_nd((2, 2, 2), 2)
    >>> place_mice_nd(g, 2, {(1, 0, 0), (0, 1, 1)})
    >>> dump(g)
    board:
        [[2, 2], [2, 2]]
        [[2, 'm'], ['m', 2]]
    dimensions: (2, 2, 2)
    state: ongoing
    visible:
        [[False, False], [False, False]]
        [[False, False], [False, False]]
    """
    mice_list = set()
    for n in random_coordinates(game["dimensions"]):
        if(n not in disallowed):
            if n not in mice_list:
                mice_list.add(n)
        if(len(mice_list) == num_mice):
            break
    #Placing the mice
    print(len(mice_list))
    for coordinates in mice_list:
        set_coordinate(coordinates, game, 'm', 'board')

    for coordinates in mice_list:
        cross = get_cross(coordinates)
        neighbors = get_n(cross)
        for c in neighbors:
            if(in_bound(c, game) and c != coordinates):
                num = get_coordinate(c, game, "board")
                if(num != 'm'):
                    num += 1
                    set_coordinate(c, game, num, 'board')



    
    



def reveal_nd(game, coordinates):
    """
    Recursively reveal square at coords and neighboring squares.

    Update the visible to reveal square at the given coordinates; then
    recursively reveal its neighbors, as long as coords does not contain and is
    not adjacent to a mouse.  Return a number indicating how many squares were
    revealed.  No action should be taken (and 0 should be returned) if the
    incoming state of the game is not 'ongoing', or if the given square has
    already been revealed.

    If this is the first reveal performed in a game, then before performing
    the reveal operation, we add the appropriate number of mice to the game
    (the number given at initialization time).  No mice should be placed in
    the location to be revealed, nor in any of its neighbors.


    The updated state is 'lost' when at least one mouse is visible on the
    board, 'won' when all safe squares (squares that do not contain a mouse)
    and no mice are visible, and 'ongoing' otherwise.

    Parameters:
       coordinates (tuple): Where to start revealing squares

    Returns:
       int: number of squares revealed

    >>> g = new_game_nd((2, 4, 2), 3)
    >>> reveal_nd(g, (0, 3, 0))
    8
    >>> dump(g)
    board:
        [['m', 3], ['m', 3], [1, 1], [0, 0]]
        [['m', 3], [3, 3], [1, 1], [0, 0]]
    dimensions: (2, 4, 2)
    state: ongoing
    visible:
        [[False, False], [False, False], [True, True], [True, True]]
        [[False, False], [False, False], [True, True], [True, True]]
    >>> reveal_nd(g, (0, 0, 1))
    1
    >>> dump(g)
    board:
        [['m', 3], ['m', 3], [1, 1], [0, 0]]
        [['m', 3], [3, 3], [1, 1], [0, 0]]
    dimensions: (2, 4, 2)
    state: ongoing
    visible:
        [[False, True], [False, False], [True, True], [True, True]]
        [[False, False], [False, False], [True, True], [True, True]]
    >>> reveal_nd(g, (0, 0, 0))
    1
    >>> dump(g)
    board:
        [['m', 3], ['m', 3], [1, 1], [0, 0]]
        [['m', 3], [3, 3], [1, 1], [0, 0]]
    dimensions: (2, 4, 2)
    state: lost
    visible:
        [[True, True], [False, False], [True, True], [True, True]]
        [[False, False], [False, False], [True, True], [True, True]]
    """
     #If game is not ongoing or the square is already revealed
    if(game['state'] != 'ongoing' or get_coordinate(coordinates, game, "visible") == True):
        return 0

    #If it is first time playing
    visible = game['visible']
    first_time = True
    dimensions = game['dimensions']
    disallowed = set()
    num_mice = game['mice']
    first_time = check_first_nd(visible)
    
    if(first_time):
        disallowed.add(coordinates)
        cross = get_cross(coordinates)
        for neighbor in get_n(cross):
            disallowed.add(neighbor)
    
        place_mice_2d(game, num_mice, disallowed)

    if(get_coordinate(coordinate, game, 'board') == 'm'):
        set_coordinate(coordinates, game, True, "visible")
        game['state'] = "lost"
        return 1
    
    #Flood Fill Step
    visited = {coordinates}
    count = 0
    def flood_fill(c):
        nonlocal count
        if(get_coordinate(c, game, 'visible') == False):
            set_coordinate(c, game, True, 'visible')
            count += 1
        if(get_coordinate(c, game, 'board') != 0):
            return
        cross = get_cross(c)
        for neighbor in get_n(cross):
            if(neighbor not in visited and neighbor != c):
                visited.add(neighbor)
                flood_fill(neighbor)
    #Check if we won the game
    flood_fill(coordinates)
    all_mice_loc = set()
    won = True
    for r in range(len(game['board'])):
        for c in range(len(game['board'][0])):
            if(game['board'][r][c] == 'm'):
                all_mice_loc.add((r ,c))
    for r in range(len(game['visible'])):
        for c in range(len(game['visible'][0])):
            if((r, c) not in all_mice_loc):
                if(game['visible'][r][c] == False):
                    won = False
                    break
    if(won == True):
        game['state'] = "won"
    

    return count

    


def render_nd(game, all_visible=False):
    """
    Prepare the game for display.

    Returns an N-dimensional array (nested lists) of '_' (hidden squares), 'm'
    (mice), ' ' (empty squares), or '1', '2', etc. (squares neighboring mice).
    The game['visible'] array indicates which squares should be visible.  If
    all_visible is True (the default is False), the game['visible'] array is
    ignored and all cells are shown.

    Parameters:
       all_visible (bool): Whether to reveal all tiles or just the ones allowed
                           by game['visible']

    Returns:
       An n-dimensional array of strings (nested lists)

    >>> g = new_game_nd((2, 4, 2), 3)
    >>> reveal_nd(g, (0, 3, 0))
    8
    >>> render_nd(g, False)
    [[['_', '_'], ['_', '_'], ['1', '1'], [' ', ' ']],
     [['_', '_'], ['_', '_'], ['1', '1'], [' ', ' ']]]
    >>> render_nd(g, True)
    [[['m', '3'], ['m', '3'], ['1', '1'], [' ', ' ']],
     [['m', '3'], ['3', '3'], ['1', '1'], [' ', ' ']]]
    """
    raise NotImplementedError


def random_coordinates(dimensions):
    """
    Given a tuple representing the dimensions of a game board, return an
    infinite generator that yields pseudo-random coordinates within the board.
    For a given tuple of dimensions and seed, the output sequence will always
    be the same.
    """

    def prng(state):
        # see https://en.wikipedia.org/wiki/Lehmer_random_number_generator
        while True:
            yield (state := state * 48271 % 0x7FFFFFFF) / 0x7FFFFFFF

    prng_gen = prng(
        seed
        if (seed := getattr(random_coordinates, "seed", None)) is not None
        else (sum(dimensions) + 61016101)
    )
    while True:
        yield tuple(int(dim * val) for val, dim in zip(prng_gen, dimensions))


if __name__ == "__main__":
    # Test with doctests. Helpful to debug individual lab.py functions.
    #_doctest_flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    #doctest.testmod(optionflags=_doctest_flags)  # runs ALL doctests

    # Alternatively, can run the doctests JUST for specified function/methods,
    # e.g., for render_2d or any other function you might want.  To do so,
    # comment out the above line, and uncomment the below line of code.  This
    # may be useful as you write/debug individual doctests or functions.  Also,
    # the verbose flag can be set to True to see all test results, including
    # those that pass.
    #
    #doctest.run_docstring_examples(
        #place_mice_2d,
       #globals(),
        #optionflags=_doctest_flags,
        #verbose=False
     #)
    #print(new_game_nd((2,4,2),1))
    #g = new_game_nd((4, 4, 4, 3), 13)
    #place_mice_nd(g, 13, {(0,0,1,1)})
    #print(g['board'])
    pass