"""
Mice-sleeper Test Cases
"""

import os
import lab
import sys
import copy
import pickle
import doctest

import pytest

sys.setrecursionlimit(50_000)

TEST_DIRECTORY = os.path.dirname(__file__)

TESTDOC_FLAGS = doctest.NORMALIZE_WHITESPACE | doctest.REPORT_ONLY_FIRST_FAILURE
TESTDOC_SKIP = ["lab"]


###########
# HELPERS #
###########


def builtin_keys(d):
    return {
        k: v for k, v in d.items() if k in ("board", "dimensions", "state", "visible")
    }


def compare_games(d1, d2):
    return builtin_keys(d1) == builtin_keys(d2)


def find_mice(board):
    out = set()

    def helper(board, sofar=()):
        if board == "m":
            out.add(sofar)
        elif isinstance(board, list):
            for ix, subboard in enumerate(board):
                helper(subboard, sofar + (ix,))

    helper(board)
    return out


class SpoofedPRNG:
    original_random_coordinates = lab.random_coordinates

    def __init__(self, values):
        self.values = values

    def random_coordinates(self, dimensions):
        while True:
            yield from self.values

    def __enter__(self):
        lab.random_coordinates = self.random_coordinates

    def __exit__(self, exc_type, exc_value, traceback):
        lab.random_coordinates = SpoofedPRNG.original_random_coordinates


class SetSeed:
    def __init__(self, seed):
        self.seed = seed

    def __enter__(self):
        lab.random_coordinates.seed = self.seed

    def __exit__(self, exc_type, exc_value, traceback):
        lab.random_coordinates.seed = None


def compare_renders(got, expected, full=False):
    out = []
    if len(got) != len(expected) or not all(
        len(i) == len(j) for i, j in zip(got, expected)
    ):
        out.append("incorrect length of rendered output!")
    for r, erow in enumerate(expected):
        for c, exp in enumerate(erow):
            try:
                sub = got[r][c]
            except:
                continue
            if sub != exp:
                out.append(
                    f"incorrect value at ({r},{c}): got {sub!r} but expected {exp!r}"
                )
    if out:
        return (
            f"your result for render_2d(game, all_visible={full}) produced incorrect results:\n\n"
            + "\n".join(out)
        )


def format_error_message(seed, nrows, ncols, mice, moves_so_far, phrase=None):
    output = [phrase] if phrase else []
    output.extend(
        [
            "\nthe following code was run before the test case failed.",
            "the last call in this sequence was the one that caused the error.",
            "you can test this sequence of moves directly in code.\n",
        ]
    )
    if seed is not None:
        output.append(f"random_coordinates.seed = {seed}")
    output.append(f"game = new_game_2d({nrows}, {ncols}, {mice})")
    for m, loc in moves_so_far:
        output.append(
            f"{'reveal_2d' if m == 'd' else 'toggle_bed_2d'}(game, {loc[0]}, {loc[1]})"
        )
    return "\n" + "\n".join(output) + "\n\n"


#######################################
# HIGH-LEVEL TESTS: ORGANIZATION, ETC #
#######################################


def test_all_docstrings_exist():
    """Checking if docstrings have been written for everything in lab.py"""
    tests = doctest.DocTestFinder(exclude_empty=False).find(lab)
    for test in tests:
        if test.name in TESTDOC_SKIP:
            continue
        assert test.docstring, f"Oh no, '{test.name}' has no docstring!"


##########################
# 2-D MICE-SLEEPER TESTS #
##########################


def test_new_game_2d():
    for nrows in (10, 20, 30):
        for ncols in (8, 16, 24):
            expected = {
                "board": [[0] * ncols for _ in range(nrows)],
                "dimensions": (nrows, ncols),
                "visible": [[False] * ncols for _ in range(nrows)],
                "state": "ongoing",
            }
            for num_mice in range(0, 20):
                result = lab.new_game_2d(
                    nrows,
                    ncols,
                    num_mice,
                )
                for name in expected:
                    assert result[name] == expected[name]


@pytest.mark.parametrize("testnum", ["00", "01", "10", "11"])
def test_2d_place_mice(testnum):
    input_file = os.path.join(
        TEST_DIRECTORY, "test_inputs", "test_2d_place_mice_%s.pickle" % testnum
    )
    with open(input_file, "rb") as f:
        seed, nrows, ncols, nmice, disallowed = pickle.load(f)
        original_disallowed = copy.deepcopy(disallowed)

    with SetSeed(seed):
        g = lab.new_game_2d(nrows, ncols, nmice)
        lab.place_mice_2d(g, nmice, disallowed)
        result = g["board"]

    output_file = os.path.join(
        TEST_DIRECTORY, "test_outputs", "test_2d_place_mice_%s.pickle" % testnum
    )
    with open(output_file, "rb") as f:
        expected = pickle.load(f)

    assert len((placed := find_mice(result))) == nmice, (
        f"expected {nmice} mice, got {len(placed)}"
    )
    assert placed.isdisjoint(original_disallowed), (
        f"oops!  mice added in disallowed spots: {disallowed & placed}"
    )
    assert result == expected


def test_2d_tiny_real_game_mice_placement():
    # (for this board, the random number generator will want to put the mouse
    # at (52, 51))

    # click elsewhere, mouse should end up at (52, 51)
    g = lab.new_game_2d(100, 100, 1)
    with SetSeed(None):
        lab.reveal_2d(g, 0, 0)
        assert find_mice(g["board"]) == {(52, 51)}

    # click directly where the mouse would be, it should end up elsewhere
    g = lab.new_game_2d(100, 100, 1)
    with SetSeed(None):
        lab.reveal_2d(g, 52, 51)
        assert find_mice(g["board"]) == {(5, 46)}

    # click on a neighbor of the mouse's home, it should end up elsewhere
    g = lab.new_game_2d(100, 100, 1)
    with SetSeed(None):
        lab.reveal_2d(g, 51, 51)
        assert find_mice(g["board"]) == {(5, 46)}

    # make sure we're using the right number of mice
    g = lab.new_game_2d(100, 100, 1)
    g2 = lab.new_game_2d(100, 100, 10_000)
    with SetSeed(None):
        lab.reveal_2d(g, 51, 52)
        assert find_mice(g["board"]) == {(5, 46)}


@pytest.mark.parametrize(
    "params", ["000", "001", "010", "011", "100", "101", "110", "111"]
)
def test_2d_real_game_mice_placement(params):
    input_fname = os.path.join(
        TEST_DIRECTORY, "test_inputs", f"test_2d_mice_placement_{params}.pickle"
    )
    output_fname = os.path.join(
        TEST_DIRECTORY, "test_outputs", f"test_2d_mice_placement_{params}.pickle"
    )
    with open(input_fname, "rb") as f:
        seed, rows, cols, nmice, click = pickle.load(f)

    with SetSeed(seed):
        game = lab.new_game_2d(rows, cols, nmice)
        start = copy.deepcopy(game)
        count = lab.reveal_2d(game, *click)
        with open(output_fname, "rb") as f:
            orig, revealed, result = pickle.load(f)

        assert start["board"], orig["board"]
        assert game["board"], result["board"]


def _do_test_2d_integration(test):
    """reveal, render, and render_2d_board on boards"""
    exp_fname = os.path.join(
        TEST_DIRECTORY, "test_outputs", f"test_2d_integration_{test:02d}.pickle"
    )
    inp_fname = os.path.join(
        TEST_DIRECTORY, "test_inputs", f"test_2d_integration_{test:02d}.pickle"
    )
    with open(inp_fname, "rb") as f:
        seed, inputs, moves = pickle.load(f)
    with open(exp_fname, "rb") as f:
        expected = pickle.load(f)
    with SetSeed(seed):
        game = lab.new_game_2d(*inputs)
        moves_so_far = []
        for location, exp in zip(moves, expected):
            moves_so_far.append(("d", location))
            num, g, render, renderx = exp
            reveal_res = lab.reveal_2d(game, *location)
            assert reveal_res == num, format_error_message(
                seed,
                *inputs,
                moves_so_far,
                f"incorrect return value from reveal_2d: got {reveal_res!r} but expected {num!r}",
            )
            myrender = lab.render_2d(game, all_visible=False)
            assert myrender == render, (
                compare_renders(myrender, render, False)
                + "\n\n"
                + format_error_message(seed, *inputs, moves_so_far, "")
            )
            myrender = lab.render_2d(game, all_visible=True)
            assert myrender == renderx, (
                compare_renders(render, renderx, True)
                + "\n\n"
                + format_error_message(seed, *inputs, moves_so_far, "")
            )
            assert game["state"] == g["state"], format_error_message(
                seed,
                *inputs,
                moves_so_far,
                f"incorrect state: got {game['state']!r} but expected {g['state']!r}",
            )

        last_state = game["state"]
        if last_state in {"won", "lost"}:
            for r in range(game["dimensions"][0]):
                for c in range(game["dimensions"][1]):
                    assert lab.reveal_2d(game, r, c) == 0
                    assert game["state"] == last_state
        else:
            for r in range(game["dimensions"][0]):
                for c in range(game["dimensions"][1]):
                    if game["visible"][r][c]:
                        assert lab.reveal_2d(game, r, c) == 0
                        assert game["state"] == "ongoing"


def test_small_2d_operations():
    # single mouse on the board: win on first click
    with SetSeed(None):
        g = lab.new_game_2d(25, 25, 1)
        assert lab.reveal_2d(g, 15, 15) == 624
        assert g["board"][12][18] == "m"
        assert g["state"] == "won"

    # another win on first click: mice _must_ be put into the right-most column
    # given the other constraints on the board, which forces a win immediately
    with SetSeed(None):
        g = lab.new_game_2d(3, 4, 3)
        assert lab.reveal_2d(g, 1, 1) == 9
        assert g["visible"] == [
            [True, True, True, False],
            [True, True, True, False],
            [True, True, True, False],
        ]
        assert g["board"] == [
            [0, 0, 2, "m"],
            [0, 0, 3, "m"],
            [0, 0, 2, "m"],
        ]
        assert g["state"] == "won"

    # small test game
    with SetSeed(None):
        g = lab.new_game_2d(5, 5, 3)

        # this click puts mice at (3, 2), (0, 4), and (2, 1),
        # then reveals 8 squares
        assert lab.reveal_2d(g, 0, 0) == 8
        assert g["board"] == [
            [0, 0, 0, 1, "m"],
            [1, 1, 1, 1, 1],
            [1, "m", 2, 1, 0],
            [1, 2, "m", 1, 0],
            [0, 1, 1, 1, 0],
        ]
        assert g["visible"] == [
            [True, True, True, True, False],
            [True, True, True, True, False],
            [False, False, False, False, False],
            [False, False, False, False, False],
            [False, False, False, False, False],
        ]
        assert g["state"] == "ongoing"


@pytest.mark.parametrize("testnum", range(12))
def test_2d_integration(testnum):
    _do_test_2d_integration(testnum)


@pytest.mark.parametrize("starttest", [i * 4 for i in range(3)])
def test_2d_pingpong(starttest):
    # run multiple tests at the same time and make sure they still behave
    game_nums = [starttest + i for i in range(4)]
    games = []

    def checker_gen(game, inp_iter, exp_iter):
        while True:
            try:
                coords = next(inp_iter)
                output, g, render, render_all = next(exp_iter)
            except StopIteration:
                return

            # run the move and check
            assert lab.reveal_2d(game, *coords) == output
            assert lab.render_2d(game, all_visible=False) == render
            assert lab.render_2d(game, all_visible=True) == render_all
            assert compare_games(g, game)
            yield None

    for ix, test in enumerate(game_nums):
        inp_fname = os.path.join(
            TEST_DIRECTORY, "test_inputs", f"test_2d_integration_{test:02d}.pickle"
        )
        with open(inp_fname, "rb") as f:
            seed, inp, moves = pickle.load(f)
            inputs = iter(moves)
            g = lab.new_game_2d(*inp)

        out_fname = os.path.join(
            TEST_DIRECTORY, "test_outputs", f"test_2d_integration_{test:02d}.pickle"
        )
        with open(out_fname, "rb") as f:
            expected = iter(pickle.load(f))

        with SetSeed(seed):
            games.append(checker_gen(g, inputs, expected))
            for i in games[-1]:
                break

    for i in zip(*games):
        pass


##########################
# N-D MICE-SLEEPER TESTS #
##########################


def test_new_game_nd():
    all_dimensions = [
        (3, 4),
        (5, 6, 7),
        (8, 9, 10, 11),
        (12, 11, 10, 9, 8),
        (7, 6, 5, 4, 3, 2),
    ]
    for ix, dims in enumerate(all_dimensions):
        g = lab.new_game_nd(dims, 20)
        results_fname = os.path.join(
            TEST_DIRECTORY, "test_outputs", f"test_nd_new_game_{ix:02d}.pickle"
        )
        with open(results_fname, "rb") as f:
            assert compare_games(g, pickle.load(f))


@pytest.mark.parametrize("testnum", ["00", "01", "10", "11"])
def test_nd_place_mice(testnum):
    input_file = os.path.join(
        TEST_DIRECTORY, "test_inputs", "test_nd_place_mice_%s.pickle" % testnum
    )
    with open(input_file, "rb") as f:
        seed, dimensions, nmice, disallowed = pickle.load(f)
        original_disallowed = copy.deepcopy(disallowed)

    with SetSeed(seed):
        g = lab.new_game_nd(dimensions, nmice)
        lab.place_mice_nd(g, nmice, disallowed)
        result = g["board"]

    output_file = os.path.join(
        TEST_DIRECTORY, "test_outputs", "test_nd_place_mice_%s.pickle" % testnum
    )
    with open(output_file, "rb") as f:
        expected = pickle.load(f)

    assert len((placed := find_mice(result))) == nmice, (
        f"expected {nmice} mice, got {len(placed)}"
    )
    assert placed.isdisjoint(original_disallowed), (
        f"oops!  mice added in disallowed spots: {disallowed & placed}"
    )
    assert result == expected


def test_nd_tiny_real_game_mice_placement():
    # (for this board, the random number generator will want to put the mouse
    # at (5, 9, 3, 3))

    # click elsewhere, mouse should end up at (5, 9, 3, 3)
    g = lab.new_game_nd((10, 10, 10, 10), 1)
    with SetSeed(None):
        lab.reveal_nd(g, (0, 0, 0, 0))
        assert find_mice(g["board"]) == {(5, 9, 3, 3)}

    # click directly where the mouse would be, it should end up elsewhere
    g = lab.new_game_nd((10, 10, 10, 10), 1)
    with SetSeed(None):
        lab.reveal_nd(g, (5, 9, 3, 3))
        assert find_mice(g["board"]) == {(8, 4, 9, 6)}

    # click on a neighbor of the mouse's home, it should end up elsewhere
    g = lab.new_game_nd((10, 10, 10, 10), 1)
    with SetSeed(None):
        lab.reveal_nd(g, (6, 8, 4, 2))
        assert find_mice(g["board"]) == {(8, 4, 9, 6)}

    # make sure we're using the right number of mice
    g = lab.new_game_nd((10, 10, 10, 10), 1)
    g2 = lab.new_game_nd((10, 10, 10, 10), 10_000)
    with SetSeed(None):
        lab.reveal_nd(g, (6, 8, 4, 2))
        assert find_mice(g["board"]) == {(8, 4, 9, 6)}


@pytest.mark.parametrize(
    "params", ["000", "001", "010", "011", "100", "101", "110", "111"]
)
def test_nd_real_game_mice_placement(params):
    input_fname = os.path.join(
        TEST_DIRECTORY, "test_inputs", f"test_nd_mice_placement_{params}.pickle"
    )
    output_fname = os.path.join(
        TEST_DIRECTORY, "test_outputs", f"test_nd_mice_placement_{params}.pickle"
    )
    with open(input_fname, "rb") as f:
        seed, dims, nmice, click = pickle.load(f)
    with SetSeed(seed):
        game = lab.new_game_nd(dims, nmice)
        start = copy.deepcopy(game)
        count = lab.reveal_nd(game, click)
        with open(output_fname, "rb") as f:
            orig, revealed, result = pickle.load(f)

        assert start["board"], orig["board"]
        assert game["board"], result["board"]


def test_tiny_reveal_nd():
    # super tiny example 1D example
    with SpoofedPRNG([(2,)]):
        game = lab.new_game_nd((4,), 1)
        expected = {
            "dimensions": (4,),
            "state": "ongoing",
            "board": [0, 0, 0, 0],
            "visible": [False, False, False, False],
        }
        for i in ("dimensions", "board", "visible", "state"):
            assert game[i] == expected[i]

        assert lab.reveal_nd(game, (0,)) == 2
        assert game["visible"] == [True, True, False, False]
        assert game["state"] == "ongoing"

        assert lab.reveal_nd(game, (2,)) == 1
        assert game["visible"] == [True, True, True, False]
        assert game["state"] == "lost"

    # reset
    with SpoofedPRNG([(2,)]):
        game = lab.new_game_nd((4,), 1)
        assert lab.reveal_nd(game, (0,)) == 2
        assert game["visible"] == [True, True, False, False]
        assert game["state"] == "ongoing"

        assert lab.reveal_nd(game, (0,)) == 0
        assert game["visible"] == [True, True, False, False]
        assert game["state"] == "ongoing"

        assert lab.reveal_nd(game, (3,)) == 1
        assert game["visible"] == [True, True, False, True]
        assert game["state"] == "won"

        assert lab.reveal_nd(game, (2,)) == 0
        assert game["visible"] == [True, True, False, True]
        assert game["state"] == "won"

    # now test the reveal behavior on a small 1D game
    with SpoofedPRNG([(0,), (7,), (2,)]):
        game = lab.new_game_nd((10,), 3)
        expected = {
            "dimensions": (10,),
            "state": "ongoing",
            "board": ["m", 2, "m", 1, 0, 0, 1, "m", 1, 0],
            "visible": [
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
            ],
        }
        for i in ("dimensions", "visible", "state"):
            assert game[i] == expected[i]
        assert game["board"] == [0] * 10

        # now let's reveal some squares!
        expected_vis = [
            False,
            False,
            False,
            True,
            True,
            True,
            True,
            False,
            False,
            False,
        ]
        assert lab.reveal_nd(game, (5,)) == 4
        assert game["visible"] == expected_vis
        for i in ("dimensions", "board", "state"):
            assert game[i] == expected[i]

        expected_vis = [False, True, False, True, True, True, True, False, False, False]
        assert lab.reveal_nd(game, (1,)) == 1
        assert game["visible"] == expected_vis
        for i in ("dimensions", "board", "state"):
            assert game[i] == expected[i]

        expected_vis = [False, True, False, True, True, True, True, False, True, False]
        assert lab.reveal_nd(game, (8,)) == 1
        assert game["visible"] == expected_vis
        for i in ("dimensions", "board", "state"):
            assert game[i] == expected[i]

        # reveal again
        for c in [1, 3, 4, 5, 6, 8]:
            assert lab.reveal_nd(game, (c,)) == 0
            assert game["visible"] == expected_vis
            for i in ("dimensions", "board", "state"):
                assert game[i] == expected[i]

        # win
        expected_vis = [False, True, False, True, True, True, True, False, True, True]
        assert lab.reveal_nd(game, (9,)) == 1
        assert game["visible"] == expected_vis
        assert game["state"] == "won"
        for i in ("dimensions", "board"):
            assert game[i] == expected[i]

        # reveal again
        for c in range(10):
            assert lab.reveal_nd(game, (c,)) == 0
            assert game["visible"] == expected_vis
            assert game["state"] == "won"
            for i in ("dimensions", "board"):
                assert game[i] == expected[i]

    ## start over
    with SpoofedPRNG([(0,), (7,), (2,)]):
        game = lab.new_game_nd((10,), 3)
        for i in ("dimensions", "visible", "state"):
            assert game[i] == expected[i]
        assert game["board"] == [0] * 10

        # lose
        expected_vis = [False, False, True, True, True, True, True, False, False, False]
        assert lab.reveal_nd(game, (4,)) == 4
        assert lab.reveal_nd(game, (2,)) == 1
        assert game["visible"] == expected_vis
        assert game["state"] == "lost"
        for i in ("dimensions", "board"):
            assert game[i] == expected[i]

        # reveal again
        for c in range(10):
            assert lab.reveal_nd(game, (c,)) == 0
            assert game["visible"] == expected_vis
            assert game["state"] == "lost"
            for i in ("dimensions", "board"):
                assert game[i] == expected[i]


@pytest.mark.parametrize("test", range(12))
def test_nd_integration(test):
    exp_fname = os.path.join(
        TEST_DIRECTORY, "test_outputs", f"test_nd_integration_{test:02d}.pickle"
    )
    inp_fname = os.path.join(
        TEST_DIRECTORY, "test_inputs", f"test_nd_integration_{test:02d}.pickle"
    )
    with open(exp_fname, "rb") as f:
        expected = pickle.load(f)
    with open(inp_fname, "rb") as f:
        seed, inputs, moves = pickle.load(f)
    with SetSeed(seed):
        g = lab.new_game_nd(*inputs)
        for location, results in zip(moves, expected):
            squares_revealed, game, rendered, rendered_all_visible = results
            res = lab.reveal_nd(g, location)
            assert res == squares_revealed
            for i in ("dimensions", "board", "visible", "state"):
                assert g[i] == game[i]
            assert lab.render_nd(g) == rendered
            assert lab.render_nd(g, True) == rendered_all_visible

        # reveal again
        res = lab.reveal_nd(g, location)
        assert res == 0
        for i in ("dimensions", "board", "visible", "state"):
            assert g[i] == game[i]
        assert lab.render_nd(g) == rendered
        assert lab.render_nd(g, True) == rendered_all_visible


########################
# TESTS INVOLVING BEDS #
########################


def tiny_toggle_bed_tester(new_game_func, toggle_func, render_func):
    exp = {"visible": [[False]], "dimensions": (1, 1), "state": "ongoing"}

    render_nobed = [["_"]]
    render_withbed = [["B"]]

    for (
        board,
        nmice,
    ) in [([[0]], 0), ([[0]], 1)]:
        g = new_game_func((1, 1), nmice)
        exp["board"] = board

        for i in range(10):
            res = toggle_func(g, (0, 0))
            for key in exp:
                assert g[key] == exp[key], f"Right-click should not modify game[{key}]"
            if i % 2 == 0:
                assert res, f"Bed should be toggled ON after {i + 1} right click(s)"
                assert render_func(g) == render_withbed
            else:
                assert not res, (
                    f"Bed should be toggled OFF after {i + 1} right click(s)"
                )
                assert render_func(g) == render_nobed


def test_tiny_toggle_bed_2d_1():
    with SpoofedPRNG([(0, 0)]):
        game = lab.new_game_2d(2, 3, 1)  # 2 rows, 3 columns, 1 mouse
        # click the bottom right square
        assert lab.reveal_2d(game, 1, 2) == 4
        assert game["board"] == [['m', 1, 0], [1, 1, 0]]
        assert game["visible"] == [[False, True, True], [False, True, True]]

        # put a bed on a spot with a mouse
        assert lab.toggle_bed_2d(game, 0, 0) is True
        assert lab.render_2d(game) == [['B', '1', ' '], ['_', '1', ' ']]

        # put a bed on a spot without a mouse
        assert lab.toggle_bed_2d(game, 1, 0) is True
        assert lab.render_2d(game) == [['B', '1', ' '], ['B', '1', ' ']]

        # cannot put a bed on a spot that has been revealed
        assert lab.toggle_bed_2d(game, 1, 2) is None
        assert lab.toggle_bed_2d(game, 1, 1) is None
        assert lab.toggle_bed_2d(game, 0, 1) is None
        assert lab.toggle_bed_2d(game, 0, 2) is None
        assert lab.render_2d(game) == [['B', '1', ' '], ['B', '1', ' ']]

        # click on a bed should not reveal a square
        assert lab.reveal_2d(game, 0, 0) == 0
        assert game["board"] == [['m', 1, 0], [1, 1, 0]]
        assert game["visible"] == [[False, True, True], [False, True, True]]

        assert lab.reveal_2d(game, 1, 0) == 0
        assert game["board"] == [['m', 1, 0], [1, 1, 0]]
        assert game["visible"] == [[False, True, True], [False, True, True]]

        # toggle off flag
        assert lab.toggle_bed_2d(game, 1, 0) is False
        assert lab.render_2d(game) == [['B', '1', ' '], ['_', '1', ' ']]

        assert lab.toggle_bed_2d(game, 0, 0) is False
        assert lab.render_2d(game) == [['_', '1', ' '], ['_', '1', ' ']]

        # lose game
        assert lab.reveal_2d(game, 0, 0) == 1
        assert game["board"] == [['m', 1, 0], [1, 1, 0]]
        assert game["visible"] == [[True, True, True], [False, True, True]]
        assert game["state"] == "lost"

        # game is over, cannot toggle flag
        assert lab.toggle_bed_2d(game, 1, 0) is None
        assert lab.toggle_bed_2d(game, 0, 0) is None
        assert lab.toggle_bed_2d(game, 1, 1) is None


def test_tiny_toggle_bed_2d_2():
    with SpoofedPRNG([(0, 0)]):
        game = lab.new_game_2d(2, 3, 1)  # 2 rows, 3 columns, 1 mouse

        # flag locations on
        assert lab.toggle_bed_2d(game, 0, 0) is True
        assert lab.render_2d(game) == [['B', '_', '_'], ['_', '_', '_']]

        assert lab.toggle_bed_2d(game, 0, 2) is True
        assert lab.render_2d(game) == [['B', '_', 'B'], ['_', '_', '_']]

        # flag locations off
        assert lab.toggle_bed_2d(game, 0, 0) is False
        assert lab.render_2d(game) == [['_', '_', 'B'], ['_', '_', '_']]

        assert lab.toggle_bed_2d(game, 0, 2) is False
        assert lab.render_2d(game) == [['_', '_', '_'], ['_', '_', '_']]

        # flag locations on
        assert lab.toggle_bed_2d(game, 0, 0) is True
        assert lab.render_2d(game) == [['B', '_', '_'], ['_', '_', '_']]

        assert lab.toggle_bed_2d(game, 0, 2) is True
        assert lab.render_2d(game) == [['B', '_', 'B'], ['_', '_', '_']]

        assert lab.toggle_bed_2d(game, 0, 1) is True
        assert lab.render_2d(game) == [['B', 'B', 'B'], ['_', '_', '_']]

        # first click on bed doesn't work
        assert lab.reveal_2d(game, 0, 1) == 0
        assert game["visible"] == [[False, False, False], [False, False, False]]

        # first click on a corner without bed does not reveal squares with
        # beds, but mice can get placed under bed
        assert lab.reveal_2d(game, 1, 2) == 2
        assert game["board"] == [['m', 1, 0], [1, 1, 0]]
        assert game["visible"] == [[False, False, False], [False, True, True]]


def test_tiny_toggle_bed_2d_3():
    def toggle(game, coords):
        return lab.toggle_bed_2d(game, coords[0], coords[1])

    tiny_toggle_bed_tester(
        (lambda dims, mice: lab.new_game_2d(*dims, mice)),
        (lambda game, coords: lab.toggle_bed_2d(game, *coords)),
        lab.render_2d
    )


def test_beds_2d_1():
    for testnum in range(1, 5):
        _test_bed_2d(testnum)


def test_beds_2d_2():
    for testnum in range(6, 10):
        _test_bed_2d(testnum)


def test_beds_2d_3():
    for testnum in range(10, 14):
        _test_bed_2d(testnum)


def test_tiny_toggle_bed_nd_1():
    with SpoofedPRNG([(0, 0)]):
        game = lab.new_game_nd((2, 3), 1)  # 2 rows, 3 columns, 1 mouse
        # click the bottom right square
        assert lab.reveal_nd(game, (1, 2)) == 4
        assert game["board"] == [['m', 1, 0], [1, 1, 0]]
        assert game["visible"] == [[False, True, True], [False, True, True]]

        # put a bed on a spot with a mouse
        assert lab.toggle_bed_nd(game, (0, 0)) is True
        assert lab.render_nd(game) == [['B', '1', ' '], ['_', '1', ' ']]

        # put a bed on a spot without a mouse
        assert lab.toggle_bed_nd(game, (1, 0)) is True
        assert lab.render_nd(game) == [['B', '1', ' '], ['B', '1', ' ']]

        # cannot put a bed on a spot that has been revealed
        assert lab.toggle_bed_nd(game, (1, 2)) is None
        assert lab.toggle_bed_nd(game, (1, 1)) is None
        assert lab.toggle_bed_nd(game, (0, 1)) is None
        assert lab.toggle_bed_nd(game, (0, 2)) is None
        assert lab.render_nd(game) == [['B', '1', ' '], ['B', '1', ' ']]

        # click on a bed should not reveal a square
        assert lab.reveal_nd(game, (0, 0)) == 0
        assert game["board"] == [['m', 1, 0], [1, 1, 0]]
        assert game["visible"] == [[False, True, True], [False, True, True]]

        assert lab.reveal_nd(game, (1, 0)) == 0
        assert game["board"] == [['m', 1, 0], [1, 1, 0]]
        assert game["visible"] == [[False, True, True], [False, True, True]]

        # toggle off flag
        assert lab.toggle_bed_nd(game, (1, 0)) is False
        assert lab.render_nd(game) == [['B', '1', ' '], ['_', '1', ' ']]

        assert lab.toggle_bed_nd(game, (0, 0)) is False
        assert lab.render_nd(game) == [['_', '1', ' '], ['_', '1', ' ']]

        # win game
        assert lab.reveal_nd(game, (1, 0)) == 1
        assert game["board"] == [['m', 1, 0], [1, 1, 0]]
        assert game["visible"] == [[False, True, True], [True, True, True]]
        assert game["state"] == "won"

        # game is over, cannot toggle flag
        assert lab.toggle_bed_nd(game, (1, 0)) is None
        assert lab.toggle_bed_nd(game, (0, 0)) is None
        assert lab.toggle_bed_nd(game, (1, 1)) is None


def test_tiny_toggle_bed_nd_2():
    with SpoofedPRNG([(0, 0)]):
        game = lab.new_game_nd((2, 3), 1)  # 2 rows, 3 columns, 1 mouse

        # flag locations on
        assert lab.toggle_bed_nd(game, (0, 0)) is True
        assert lab.render_nd(game) == [['B', '_', '_'], ['_', '_', '_']]

        assert lab.toggle_bed_nd(game, (0, 2)) is True
        assert lab.render_nd(game) == [['B', '_', 'B'], ['_', '_', '_']]

        # flag locations off
        assert lab.toggle_bed_nd(game, (0, 0)) is False
        assert lab.render_nd(game) == [['_', '_', 'B'], ['_', '_', '_']]

        assert lab.toggle_bed_nd(game, (0, 2)) is False
        assert lab.render_nd(game) == [['_', '_', '_'], ['_', '_', '_']]

        # flag locations on
        assert lab.toggle_bed_nd(game, (0, 0)) is True
        assert lab.render_nd(game) == [['B', '_', '_'], ['_', '_', '_']]

        assert lab.toggle_bed_nd(game, (0, 2)) is True
        assert lab.render_nd(game) == [['B', '_', 'B'], ['_', '_', '_']]

        assert lab.toggle_bed_nd(game, (0, 1)) is True
        assert lab.render_nd(game) == [['B', 'B', 'B'], ['_', '_', '_']]

        # first click on bed doesn't work
        assert lab.reveal_nd(game, (0, 1)) == 0
        assert game["visible"] == [[False, False, False], [False, False, False]]

        # first click on a corner without bed does not reveal squares with
        # beds, but mice can get placed under bed
        assert lab.reveal_nd(game, (1, 2)) == 2
        assert game["board"] == [['m', 1, 0], [1, 1, 0]]
        assert game["visible"] == [[False, False, False], [False, True, True]]


def test_tiny_toggle_bed_nd_3():
    tiny_toggle_bed_tester(lab.new_game_nd, lab.toggle_bed_nd, lab.render_nd)


def _test_bed_2d(test_number):
    # test cases for small 2d boards

    # load inputs and expected outputs
    exp_fname = os.path.join(
        TEST_DIRECTORY, "test_outputs", f"test_2d_beds_%02d.pickle" % test_number
    )
    inp_fname = os.path.join(
        TEST_DIRECTORY, "test_inputs", f"test_2d_beds_%02d.pickle" % test_number
    )
    import pprint
    with open(exp_fname, "rb") as f:
        exp = pickle.load(f)
    with open(inp_fname, "rb") as f:
        inp = pickle.load(f)
    nrows, ncols, mice, moves = inp
    boards, visibles, states, outputs, renders, full_renders = exp

    mice = [tuple(i) for i in mice]
    nmice = len(mice)
    with SpoofedPRNG(mice):
        # force new game to generate nmice in specified mice locations
        test_game = lab.new_game_2d(nrows, ncols, nmice)

        for i, move in enumerate(moves):
            move_type, (row, col) = move
            prev_game = copy.deepcopy(test_game)
            if move_type == "f": # toggle a bed
                result = lab.toggle_bed_2d(test_game, row, col)
                expected = outputs[i]
                msg = f"\n# Unexpected result from the following toggle_bed_2d command:\n"
                msg += f"test_game = {prev_game}\n"
                msg += f"result = toggle_bed_2d(test_game, {row}, {col})\n"
                msg += "print(f'{result=}')\n"

                err_msg = msg + f"# Got result = {result!r} but expected = {expected!r}"
                assert result == expected, err_msg
            else: # reveal a square
                result = lab.reveal_2d(test_game, row, col)
                expected = outputs[i]
                msg = f"\n# Unexpected result from the following reveal_2d command:\n"
                msg += f"test_game = {prev_game}\n"
                msg += f"result = reveal_2d(test_game, {row}, {col})\n"
                msg += "print(f'{result=}')\n"
                err_msg = msg + f"# Got result = {result!r} but expected = {expected!r}"
                assert result == expected, err_msg

            err_msg = msg + f"'''\nGot game['board'] =\n{pprint.pformat(test_game['board'])}"
            err_msg += f"\nExpected board = \n{pprint.pformat(boards[i])}\n'''"
            assert test_game["board"] == boards[i], err_msg

            err_msg = msg + f"'''\nGot game['visible'] =\n{pprint.pformat(test_game['visible'])}"
            err_msg += f"\nExpected visible = \n{pprint.pformat(visibles[i])}\n'''"
            assert test_game["visible"] == visibles[i], err_msg

            err_msg = msg + f"dump(test_game)\n# Got game['state'] = {test_game['state']!r} but expected {states[i]!r}"
            assert test_game["state"] == states[i], err_msg


            result = lab.render_2d(test_game, all_visible=False)
            err_msg = f"\n# Unexpected result from the following render_2d command with all_visible=False:\n"
            err_msg += f"test_game = {test_game}\nresult = render_2d(test_game, all_visible=False)\n"
            err_msg += "import pprint\npprint.pp(result)\n"
            err_msg += f"'''\nGot result =\n{pprint.pformat(result)}\n"
            err_msg += f"But expected = \n{pprint.pformat(renders[i])}\n'''"
            assert result == renders[i], err_msg

            result = lab.render_2d(test_game, all_visible=True)
            err_msg = f"\n# Unexpected result from the following render_2d command with all_visible=True:\n"
            err_msg += f"test_game = {test_game}\nresult = render_2d(test_game, all_visible=True)\n"
            err_msg += "import pprint\npprint.pp(result)\n"
            err_msg += f"'''\nGot result =\n{pprint.pformat(result)}\n"
            err_msg += f"But expected = \n{pprint.pformat(full_renders[i])}\n'''"
            assert result == full_renders[i], err_msg


@pytest.mark.parametrize("test_number", range(10))
def test_full_integration(test_number):
    exp_fname = os.path.join(
        TEST_DIRECTORY, "test_outputs", f"full_integration_%02d.pickle" % test_number
    )
    inp_fname = os.path.join(
        TEST_DIRECTORY, "test_inputs", f"full_integration_%02d.pickle" % test_number
    )
    with open(exp_fname, "rb") as f:
        exp = pickle.load(f)
    with open(inp_fname, "rb") as f:
        inp = pickle.load(f)

    seed, dimensions, mice, moves = inp
    with SetSeed(seed):
        game = lab.new_game_nd(dimensions, mice)
        outputs, renders, states = exp

        for i, move in enumerate(moves):
            move_type, coords = move
            if move_type == "f":
                assert lab.toggle_bed_nd(game, coords) == outputs[i]
            else:
                assert lab.reveal_nd(game, coords) == outputs[i]
            assert lab.render_nd(game, all_visible=False) == renders[i]
            assert game["state"] == states[i]


@pytest.mark.parametrize("starttest", range(7))
def test_full_pingpong(starttest):
    # run multiple games simultaneously and make sure they still behave as expected
    game_nums = [starttest + i for i in range(4)]
    games = []

    def checker_gen(game, inp_iter, exp_iter):
        while True:
            try:
                move_type, coords = next(inp_iter)
                output, render, state = next(exp_iter)
            except StopIteration:
                return

            # run the move and check
            assert (lab.toggle_bed_nd if move_type == "f" else lab.reveal_nd)(
                game, coords
            ) == output
            assert lab.render_nd(game, all_visible=False) == render
            assert game["state"] == state
            yield move_type

    for ix, test in enumerate(game_nums):
        # initialize the game and run until the first dig to get the mice
        # placed down so that we know the seed is respected
        inp_fname = os.path.join(
            TEST_DIRECTORY, "test_inputs", f"full_integration_{test:02d}.pickle"
        )
        with open(inp_fname, "rb") as f:
            seed, dimensions, mice, moves = pickle.load(f)
            inputs = iter(moves)

        out_fname = os.path.join(
            TEST_DIRECTORY, "test_outputs", f"full_integration_{test:02d}.pickle"
        )
        with open(out_fname, "rb") as f:
            expected = zip(*pickle.load(f))  # out, render, state

        with SetSeed(seed):
            g = lab.new_game_nd(dimensions, mice)
            games.append(checker_gen(g, inputs, expected))
            for i in games[-1]:
                if i != "f":
                    break

    for i in zip(*games):
        pass
