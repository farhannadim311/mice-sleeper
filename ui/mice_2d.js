let confetti = new Confetti("confettisource");
confetti.destroyTarget(false);

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
  lost: "<font color='red'>YOU WOKE UP A MOUSE.  GAME OVER :(</font>",
  won: "<font color='blue'>YOU WIN! :)</font>",
};

function setStatus(status) {
  lastStatus = status;
  document.getElementById("status").innerHTML = statusMessages[status];
  if (status == "won") {
    document.getElementById("confettisource").click();
  }
}

function newGame(rows, cols, mice) {
  clearLog();
  myFetch("/new_game", { rows: rows, cols: cols, mice: mice }).then(
    (response) => {
      renderNewGame(response.render, response.render_full);
      setStatus("ongoing");
      addLog("random_coordinates.seed = " + response.seed);
      addLog(
        "game = new_game_2d(" +
          rows +
          ", " +
          cols +
          ", " +
          mice +
          ")  # initialize new game",
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
  myFetch("/reveal", { row: row, col: col }).then((response) => {
    if (response.state == "lost") {
      renderGameUpdate(response.render, response.revealed);
      renderGameUpdate(response.render_full, undefined, true);
      document.getElementById("thetable").style.backgroundColor = "#ffeeee";
      addLog(
        "reveal_2d(game, " +
          response.revealed[0] +
          ", " +
          response.revealed[1] +
          ")  # " +
          squareCount(response.count) +
          ".  revealed a mouse.  game over :(",
      );
      setStatus("lost");
    } else if (response.state == "won") {
      renderGameUpdate(response.render);
      renderGameUpdate(response.render_full, undefined, true);
      addLog(
        "reveal_2d(game, " +
          response.revealed[0] +
          ", " +
          response.revealed[1] +
          ")  # " +
          squareCount(response.count) +
          " including the last square.  game won! :D",
      );
      setStatus("won");
    } else {
      renderGameUpdate(response.render);
      renderGameUpdate(response.render_full, undefined, true);
      addLog(
        "reveal_2d(game, " +
          response.revealed[0] +
          ", " +
          response.revealed[1] +
          ")  # " +
          squareCount(response.count) +
          ".  game ongoing.",
      );
    }
  });
}

function bed(row, col) {
  if (lastStatus != "ongoing") return;
  myFetch("/bed", { row: row, col: col }).then((response) => {
    renderGameUpdate(response.render);
    if (response.bed === null) {
      addLog(
        "toggle_bed_2d(game, " +
          row +
          ", " +
          col +
          ")  # returned None (invalid bed operation)",
      );
    } else if (response.bed) {
      addLog(
        "toggle_bed_2d(game, " +
          row +
          ", " +
          col +
          ")  # returned True (bed added)",
      );
    } else {
      addLog(
        "toggle_bed_2d(game, " +
          row +
          ", " +
          col +
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

function renderGameUpdate(board, mouse_awake, phantom) {
  var thetable = document.getElementById(phantom ? "phantomtable" : "thetable");
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
      img.title = "(" + r + ", " + c + ")";
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

function renderNewGame(board, fullboard) {
  var oldtable = document.getElementById("thetable");
  var thetable = createBoard(board);
  oldtable.replaceWith(thetable);
  thetable.id = "thetable";
  var oldphantom = document.getElementById("phantomtable");
  var phantomtable = createBoard(fullboard);
  var tablepos = thetable.getBoundingClientRect();
  oldphantom.replaceWith(phantomtable);
  phantomtable.id = "phantomtable";
  showhidephantom();
}

var buttonsP = document.getElementById("buttons");
var buttonNames = ["small", "medium", "large", "huge"];
var numSize = [5, 10, 20, 50];
var numMice = [3, 10, 50, 200];
for (var i = 0; i < buttonNames.length; i++) {
  var newbutton = document.createElement("button");
  newbutton.onclick = (function (index) {
    return () => {
      newGame(numSize[index], numSize[index], numMice[index]);
    };
  })(i);
  newbutton.innerText = "new " + buttonNames[i] + " game";
  buttonsP.append(newbutton);
  if (i != buttonNames.length - 1) {
    buttonsP.append(" ");
  }
}

newGame(5, 5, 3);
function showhidephantom() {
  document.getElementById("phantomtable").style.opacity =
    document.getElementById("xray").checked ? "0.3" : "0";
}

document.getElementById("xray").onclick = showhidephantom;
showhidephantom();

function parseCustomGame() {
  var pattern =
    /^(\s*[^=]*\s*=)?\s*new_game_2d\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)\s*$/;
  var match = document.getElementById("customgame").value.match(pattern);
  if (!match) {
    alert("invalid call to new_game_2d; please try again!");
    return;
  }
  try {
    rows = parseInt(match[2]);
    cols = parseInt(match[3]);
    mice = parseInt(match[4]);
    newGame(rows, cols, mice);
  } catch (e) {
    alert("invalid call to new_game_2d; please try again!!");
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
