let confetti = new Confetti("confettisource");
confetti.destroyTarget(false);

var CURRENT_RENDERED = null;
var CURRENT_RENDERED_FULL = null;
var CURRENT_GAME_DIMENSIONS = [];
var CURRENT_VIEW_COORDINATES = null;
var C_SELECTORS = [];
var R_SELECTORS = [];
var V_SELECTORS = [];
var R_INDEX = 0;
var C_INDEX = 1;
var DIMENSION_SLICES = {};

function tuplify(x) {
  return JSON.stringify(x)
    .replaceAll("[", "(")
    .replaceAll("]", ")")
    .replaceAll(",", ", ");
}

var allimages = [];
for (var imgname of [
  "1",
  "2",
  "3",
  "4",
  "5",
  "6",
  "7",
  "8",
  "empty",
  "mouse_asleep",
  "mouse_awake",
  "bed",
  "cover",
]) {
  var img = document.createElement("img");
  img.src = "/images/" + imgname + ".png";
  allimages.push(img);
}

async function myFetch(loc, body) {
  try {
    const response = await fetch(loc, {
      method: "POST",
      cache: "no-cache",
      redirect: "follow",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
    if (response.ok) {
      out = await response.json();
      if (typeof out.error !== "undefined") {
        addLog(out.error, true);
      } else {
        return out;
      }
    } else {
      alert(
        "encountered an error when running your code; there may be an error message in the terminal where the server was running.",
      );
      return null;
    }
  } catch (e) {
    alert(
      "could not contact the server; is it running?  this could also be caused by an infinite loop in your code, in which case you will need to restart the server and reload this page.",
    );
    return null;
  }
}

function clearLog() {
  document.getElementById("log").innerHTML = "";
}

function addLog(log, scary) {
  var thelog = document.getElementById("log");
  if (thelog.innerHTML.trim() != "") {
    thelog.append(document.createElement("br"));
  }
  var commentspan = document.createElement("span");
  if (scary) {
    commentspan.classList.add("errormessage");
    commentspan.innerText =
      "# Your code produced an error:\n# " +
      log.trim().replaceAll("\n", "\n# ");
  } else {
    log = log.split("#");
    thelog.append(log[0]);
    if (log.length > 1 && log[1].trim() !== "") {
      commentspan.classList.add("comment");
      commentspan.innerText = "#" + log[1];
    }
  }
  thelog.append(commentspan);
  thelog.scrollTop = thelog.scrollHeight;
}

var lastStatus = "ongoing";
var statusMessages = {
  ongoing: "Game Ongoing",
  lost: "<font color='red'>YOU WOKE UP A MOUSE. GAME OVER :(</font>",
  won: "<font color='blue'>YOU WIN! :)</font>",
};

function setStatus(status) {
  lastStatus = status;
  document.getElementById("status").innerHTML = statusMessages[status];
  if (status == "won") {
    document.getElementById("confettisource").click();
  }
}

function formatMouseList(b) {
  out = "[";
  for (var i = 0; i < b.length; i++) {
    out += "(" + b[i][0] + ", " + b[i][1] + ")";
    if (i < b.length - 1) out += ", ";
  }
  return out + "]";
}

function newGame(dimensions) {
  clearLog();
  var averageDimension =
    dimensions.reduce((a, b) => {
      return a + b;
    }) / dimensions.length;
  var mice = Math.floor(Math.pow(averageDimension, dimensions.length / 2));
  CURRENT_GAME_DIMENSIONS = dimensions;
  myFetch("/new_game_nd", { dimensions: dimensions, mice: mice }).then(
    (response) => {
      CURRENT_RENDERED = response.render;
      CURRENT_RENDERED_FULL = response.render_full;
      renderNewGame(true);
      setStatus("ongoing");
      addLog("random_coordinates.seed = " + response.seed);
      addLog(
        "game = new_game_nd(" +
          tuplify(dimensions) +
          ", " +
          mice +
          ")  # initialized new game",
      );
    },
  );
}

function squareCount(count) {
  if (count == 0) {
    return "did not reveal any squares";
  } else if (count == 1) {
    return "revealed 1 square";
  } else {
    return "revealed " + count + " squares";
  }
}

function reveal(row, col) {
  if (lastStatus != "ongoing") return;
  var coords = CURRENT_VIEW_COORDINATES[[row, col]];
  myFetch("/reveal_nd", { coords: coords }).then((response) => {
    CURRENT_RENDERED = response.render;
    CURRENT_RENDERED_FULL = response.render_full;
    if (response.state == "lost") {
      renderGameUpdate(response.revealed);
      renderGameUpdate(undefined, true);
      document.getElementById("thetable").style.backgroundColor = "#ffeeee";
      addLog(
        "reveal_nd(game, " +
          tuplify(response.revealed) +
          ")  # " +
          squareCount(response.count) +
          ".  revealed a mouse.  game over :(",
      );
      setStatus("lost");
    } else if (response.state == "won") {
      renderGameUpdate();
      renderGameUpdate(undefined, true);
      addLog(
        "reveal_nd(game, " +
          tuplify(response.revealed) +
          ")  # " +
          squareCount(response.count) +
          " including the last square.  game won! :D",
      );
      setStatus("won");
    } else {
      renderGameUpdate();
      renderGameUpdate(undefined, true);
      addLog(
        "reveal_nd(game, " +
          tuplify(response.revealed) +
          ")  # " +
          squareCount(response.count) +
          ".  game ongoing.",
      );
    }
  });
}

function bed(row, col) {
  if (lastStatus != "ongoing") return;
  var coords = CURRENT_VIEW_COORDINATES[[row, col]];
  myFetch("/bed_nd", { coords: coords }).then((response) => {
    CURRENT_RENDERED = response.render;
    CURRENT_RENDERED_FULL = response.render_full;
    renderGameUpdate();
    if (response.bed === null) {
      addLog(
        "toggle_bed_nd(game, " +
          tuplify(coords) +
          ")  # returned None (invalid bed operation)",
      );
    } else if (response.bed) {
      addLog(
        "toggle_bed_nd(game, " +
          tuplify(coords) +
          ")  # returned True (bed added)",
      );
    } else {
      addLog(
        "toggle_bed_2d(game, " +
          tuplify(coords) +
          ")  # returned False (bed removed)",
      );
    }
  });
}

var mice_images = {
  _: "cover",
  B: "bed",
  m: "mouse_asleep",
  " ": "empty",
};

function renderGameUpdate(mouse_awake, phantom) {
  if (phantom) {
    var thetable = document.getElementById("phantomtable");
    var board = getVisibleSlice(CURRENT_RENDERED_FULL);
  } else {
    var thetable = document.getElementById("thetable");
    var board = getVisibleSlice(CURRENT_RENDERED);
  }
  for (var r = 0; r < board.length; r++) {
    var therow = thetable.children[r];
    for (var c = 0; c < board[r].length; c++) {
      var thecell = therow.children[c];
      var contents = board[r][c];
      var img = thecell.children[0];
      if (
        typeof mouse_awake !== "undefined" &&
        mouse_awake[0] == r &&
        mouse_awake[1] == c
      ) {
        var image = "mouse_awake";
      } else {
        var image = mice_images.hasOwnProperty(contents)
          ? mice_images[contents]
          : contents;
      }
      img.src = "/images/" + image + ".png";
      img.classList.add("mice");
    }
  }
}

function getVal(board, dims) {
  next = board;
  for (var i of dims) {
    next = next[i];
  }
  return next;
}

function getVisibleSlice(game) {
  // get the currently-visible slice of the game board as a 2d-array
  var out = [];
  var fullcoords = {};
  console.log(DIMENSION_SLICES);
  for (var r = 0; r < CURRENT_GAME_DIMENSIONS[R_INDEX]; r++) {
    var newrow = [];
    for (var c = 0; c < CURRENT_GAME_DIMENSIONS[C_INDEX]; c++) {
      var coord = [];
      for (var i in CURRENT_GAME_DIMENSIONS) {
        coord.push(i == R_INDEX ? r : i == C_INDEX ? c : DIMENSION_SLICES[i]);
      }
      newrow.push(getVal(game, coord));
      fullcoords[[r, c]] = coord;
    }
    out.push(newrow);
  }
  CURRENT_VIEW_COORDINATES = fullcoords;
  return out;
}

function clearDimensions() {
  for (var i of C_SELECTORS) {
    i.disabled = false;
  }
  for (var i of R_SELECTORS) {
    i.disabled = false;
  }
  for (var i of V_SELECTORS) {
    i.disabled = false;
  }
}

function makeDimensionControls() {
  R_SELECTORS = [];
  C_SELECTORS = [];
  V_SELECTORS = [];
  R_INDEX = 0;
  C_INDEX = 1;
  DIMENSION_SLICES = {};
  var table = document.getElementById("dimension-controls");
  table.innerHTML =
    "<tr><th colspan='4'>adjust display</th><tr><th>dimension</th><th>r?</th><th>c?</th><th>value?</th></tr>";
  for (var i in CURRENT_GAME_DIMENSIONS) {
    var newrow = document.createElement("tr");
    newrow.innerHTML = "<td>" + i + "</td><td></td><td></td><td></td>";
    table.append(newrow);
    var rcell = newrow.children[1];
    var rradio = document.createElement("input");
    rradio.type = "radio";
    rradio.name = "r_select";
    rradio.onchange = (function (ix) {
      return () => {
        R_INDEX = ix;
        for (var j = 0; j < R_SELECTORS.length; j++) {
          C_SELECTORS[j].disabled = j == ix;
          V_SELECTORS[j].disabled = j == R_INDEX || j == C_INDEX;
        }
        renderNewGame();
      };
    })(i);
    R_SELECTORS.push(rradio);
    rcell.append(rradio);
    var ccell = newrow.children[2];
    var cradio = document.createElement("input");
    cradio.type = "radio";
    cradio.name = "c_select";
    cradio.onchange = (function (ix) {
      return () => {
        C_INDEX = ix;
        for (var j = 0; j < C_SELECTORS.length; j++) {
          R_SELECTORS[j].disabled = j == ix;
          V_SELECTORS[j].disabled = j == R_INDEX || j == C_INDEX;
        }
        renderNewGame();
      };
    })(i);
    C_SELECTORS.push(cradio);
    ccell.append(cradio);
    var vcell = newrow.children[3];
    var vcheck = document.createElement("input");
    vcheck.type = "number";
    vcheck.value = 0;
    DIMENSION_SLICES[i] = 0;
    vcheck.min = 0;
    vcheck.max = CURRENT_GAME_DIMENSIONS[i] - 1;
    vcheck.onchange = (function (ix) {
      return () => {
        DIMENSION_SLICES[ix] = parseInt(V_SELECTORS[ix].value);
        renderNewGame();
      };
    })(i);
    V_SELECTORS.push(vcheck);
    vcell.append(vcheck);
  }
  R_SELECTORS[0].checked = true;
  R_SELECTORS[1].disabled = true;
  C_SELECTORS[1].checked = true;
  C_SELECTORS[0].disabled = true;
  V_SELECTORS[0].disabled = true;
}

function createBoard(board) {
  var thetable = document.createElement("table");
  thetable.classList.add("gameboard");
  for (var r = 0; r < board.length; r++) {
    var therow = document.createElement("tr");
    therow.style.height = "32px !important";
    for (var c = 0; c < board[r].length; c++) {
      var thecell = document.createElement("td");
      thecell.style.height = "32px !important";
      thecell.style.width = "32px !important";
      var contents = board[r][c];
      var img = document.createElement("img");
      var image = mice_images.hasOwnProperty(contents)
        ? mice_images[contents]
        : contents;
      img.src = "/images/" + image + ".png";
      img.classList.add("mice");
      img.title = tuplify(CURRENT_VIEW_COORDINATES[[r, c]]);
      img.onclick = (function (nr, nc) {
        return () => reveal(nr, nc);
      })(r, c);
      img.oncontextmenu = (function (nr, nc) {
        return (e) => {
          e.preventDefault();
          bed(nr, nc);
        };
      })(r, c);
      thecell.append(img);
      therow.append(thecell);
    }
    thetable.append(therow);
  }
  return thetable;
}

function renderNewGame(reallyNew) {
  if (reallyNew) {
    makeDimensionControls();
  }
  var oldtable = document.getElementById("thetable");
  var thetable = createBoard(getVisibleSlice(CURRENT_RENDERED));
  oldtable.replaceWith(thetable);
  thetable.id = "thetable";
  var oldphantom = document.getElementById("phantomtable");
  var phantomtable = createBoard(getVisibleSlice(CURRENT_RENDERED_FULL));
  var tablepos = thetable.getBoundingClientRect();
  oldphantom.replaceWith(phantomtable);
  phantomtable.id = "phantomtable";
  showhidephantom();
}

newGame([5, 6, 3]);
function showhidephantom() {
  document.getElementById("phantomtable").style.opacity =
    document.getElementById("xray").checked ? "0.3" : "0";
}

document.getElementById("xray").onclick = showhidephantom;
showhidephantom();

function checkDimensions(x) {
  if (!Array.isArray(x) || x.length < 2) {
    return false;
  }
  for (var i = 0; i < x.length; i++) {
    if (!Number.isInteger(x[i]) || x[i] == 0) {
      return false;
    }
  }
  return true;
}

function parseCustomGame() {
  try {
    dimensions = JSON.parse(
      document
        .getElementById("customgame")
        .value.replaceAll("(", "[")
        .replaceAll(")", "]")
        .replaceAll(" ", "")
        .replaceAll(",]", "]"),
    );
    if (!checkDimensions(dimensions)) {
      throw "bad dimensions list";
    }
    newGame(dimensions);
  } catch (e) {
    console.log(e);
    alert(
      "invalid dimensions (must be of length > 1, with no zeros inside); please try again!",
    );
  }
}

document.getElementById("customstart").onclick = parseCustomGame;

document.getElementById("copytoclipboard").onclick = function () {
  navigator.clipboard.writeText(document.getElementById("log").innerText);
  var feedback = document.getElementById("clipboard_feedback");
  feedback.style.visibility = "visible";
  setTimeout(function () {
    feedback.style.visibility = "hidden";
  }, 500);
};
