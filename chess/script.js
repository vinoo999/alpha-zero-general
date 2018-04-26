var board, game = new Chess();
var sess_id, player1, player2, game_mode;

/* Shorthand for onready; create a new game session */
$( function() {
    $("#game-mode-wrapper").show()
});

var selectPlayers = function () {
    player1 = $("#player-1").val()
    player2 = $("#player-2").val()

    if (player1 == "invalid" || player2 == "invalid") {
        alert("Invalid player selection!")
        return;
    }

    $("#condom").show();
    $("#game-mode-wrapper").hide()

    // Render loading modal
    $("#loading-text").text("Initializing new game...");
    $("#loading-wrapper").show();

    /** 
     * Initialize game based on player1 and player2. If player1 is human and player2 
     * is human, assign onDrop() and wait, if 
    **/

    if (player1 == "human" && player2 == "human") {
        game_mode = "HH"
    } else if (player1 == "human" && player2 != "human") {
        game_mode = "HR"
    } else if (player1 != "human" && player2 == "human") {
        game_mode = "RH"
    } else {
        game_mode = "RR"
    }

    var cfg = {
        draggable: true,
        position: 'start',
        onDragStart: onDragStart,
        onDrop: onDrop,
        onMouseoutSquare: onMouseoutSquare,
        onMouseoverSquare: onMouseoverSquare,
        onSnapEnd: onSnapEnd
    };

    // Random player so no need for onDrop handler
    if (game_mode == "RR") {
        cfg.onDrop = null;
    }

    board = ChessBoard('board', cfg);
    $(".info").show()

    var url = location.protocol + "//" + location.hostname + ":" + location.port + "/new_game";
    var data = { "player1": player1, "player2": player2, "game_mode": game_mode }
    var success = (id) => {
        $("#loading-wrapper").hide();
        $("#loading-text").text("Thinking...");

        // Set our session id
        sess_id = id;

        // Start the game
        if (game_mode == "RH" || game_mode == "RR") {
            $("#loading-wrapper").show();
            makeBestMove();
        } else {
            $("#condom").hide();

            // Wait for human input...
        }
    };

    $.ajax({
        type: "GET",
        url: url,
        data: data,
        success: success
    });
}

/* board visualization and games state handling */

var gameOver = function (result) {
    message = "";
    if (result == 1) {
        message = "Player 1 wins!";
    } else if (result == -1) {
        message = "Player 2 wins!";
    } else {
        message = "Draw!"
    }

    $("#loading-wrapper").hide();
    alert("Game Over!  " + message);
}

var makeBestMove = function () {

    /* When ready to apply computer's move, request it from flask server */

    // Build GET request
    var url = location.protocol + "//" + location.hostname + ":" + location.port + "/get_move";
    var data = { "sess_id": sess_id, "turn": game.turn() };
    var success = (move) => {
        move = JSON.parse(move);

        $("#condom").hide();
        $("#loading-wrapper").hide();

        /* Request handler */
        game.ugly_move(move);
        board.position(game.fen());
        renderMoveHistory(game.history());

        if (move.result != null) {
            /* Game over */
            $("#condom").show();
            return gameOver(move.result);
        }

        if (game_mode == "RR") {
            return window.setTimeout(makeBestMove, 250);
        }
    };

    // Render loading modal
    $("#condom").show();
    $("#loading-wrapper").show();

    // Send request to flask server 
    $.ajax({
        type: "GET",
        url: url,
        data: data,
        success: success
    });
};

var renderMoveHistory = function (moves) {
    var historyElement = $('#move-history').empty();
    historyElement.empty();
    for (var i = 0; i < moves.length; i = i + 2) {
        historyElement.append('<span>' + moves[i] + ' ' + ( moves[i + 1] ? moves[i + 1] : ' ') + '</span><br>')
    }
    historyElement.scrollTop(historyElement[0].scrollHeight);

};

var sendMove = function (move, data) {
    // Build POST request
    var url = location.protocol + "//" + location.hostname + ":" + location.port + "/make_move";
    var success = (res) => {
        temp = JSON.parse(res);

        removeGreySquares();
        if (move === null) {
            return 'snapback';
        }

        renderMoveHistory(game.history());

        if (temp.result != null) {
            /* Game over */
            $("#condom").show();
            return gameOver(temp.result);
        }

        if (game_mode != "HH") {
            window.setTimeout(makeBestMove, 250);
        }
    }

    // Send request to flask server 
    $.ajax({
        type: "POST",
        url: url,
        data: data,
        success: success
    });
}

var onDrop = function (source, target, piece) {

    /* On player move, send move to server */
    var data = { "sess_id": sess_id, "turn": game.turn()};

    if (piece.charAt(1) == "P" && (target.charAt(1) == "8" || target.charAt(1) == "1")) {
        /* Handle a promotion */

        // Show promotion modal
        $("#promotion-wrapper").show();

        // Set source and target data to parent closure so we can reference 
        // it dynamically from within the event handler
        this.source = source;
        this.target = target;
        var self = this;

        /* Wait until user selects their desired promotion piece */
        $("#promotion").on("change", function promotionEvent() {
            selected_piece = $("#promotion").val();
            if (selected_piece == "invalid") {
                return;
            }

            var move = game.move({
                from: self.source,
                to: self.target,
                promotion: selected_piece
            });

            /* Reset modal */
            $(".center-wrapper").hide();
            $("#promotion").prop("selectedIndex", 0);

            /* Add promotion to move data */
            data["move"] = self.source + " " + self.target + " " + selected_piece;
            return sendMove(move, data);
        });
    } 
    else {
        /* Normal move */
        var move = game.move({
            from: source,
            to: target
        });

        data["move"] = source + " " + target;
        return sendMove(move, data);
    }
};

var human_move = function () {
    if (game_mode == "HH") {
        return true;
    } else if (game_mode == "HR" && game.turn() == "w") {
        return true;
    } else if (game_mode == "RH" && game.turn() == "b") {
        return true;
    } else {
        return false;
    }
}

var onDragStart = function (source, piece, position, orientation) {
    if (game.in_checkmate() === true || game.in_draw() === true || 
        human_move() === false) {
        return false;
    }
};

var onSnapEnd = function () {
    board.position(game.fen());
};

var onMouseoverSquare = function(square, piece) {
    var moves = game.moves({
        square: square,
        verbose: true
    });

    if (moves.length === 0) {
        // game.flip_turn();
        // moves = game.moves({
        //     square: square,
        //     verbose: true
        // });
        // game.flip_turn();
        return;
    };

    greySquare(square);

    for (var i = 0; i < moves.length; i++) {
        greySquare(moves[i].to);
    }
};

var onMouseoutSquare = function(square, piece) {
    removeGreySquares();
};

var removeGreySquares = function() {
    $('#board .square-55d63').css('background', '');
};

var greySquare = function(square) {
    var squareEl = $('#board .square-' + square);

    var background = '#a9a9a9';
    if (squareEl.hasClass('black-3c85d') === true) {
        background = '#696969';
    }

    squareEl.css('background', background);
};

// var cfg = {
//     draggable: true,
//     position: 'start',
//     onDragStart: onDragStart,
//     onDrop: onDrop,
//     onMouseoutSquare: onMouseoutSquare,
//     onMouseoverSquare: onMouseoverSquare,
//     onSnapEnd: onSnapEnd
// };

// board = ChessBoard('board', cfg);
