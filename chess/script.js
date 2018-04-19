var board, game = new Chess();
var sess_id;

/* Shorthand for onready; create a new game session */
$( function() {
    var url = location.protocol + "//" + location.hostname + ":" + location.port + "/new_game";
    $.get(url, (id) => {
        /* Request handler */
        sess_id = id
    });
});

/* board visualization and games state handling */

var onDragStart = function (source, piece, position, orientation) {
    if (game.in_checkmate() === true || game.in_draw() === true ||
        piece.search(/^b/) !== -1) {
        return false;
    }
};

var makeBestMove = function () {

    /* When ready to apply computer's move, request it from flask server */

    // Build GET request
    var url = location.protocol + "//" + location.hostname + ":" + location.port + "/get_move";
    var data = { "sess_id": sess_id };
    var success = (move) => {
        /* Request handler */
        move = JSON.parse(move);
        game.ugly_move(move);
        board.position(game.fen());
        renderMoveHistory(game.history());
        if (game.game_over()) {
            alert('Game over');
        }
    };

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
        if (res == "OK") {
            removeGreySquares();
            if (move === null) {
                return 'snapback';
            }

            renderMoveHistory(game.history());
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
    var data = { "sess_id": sess_id };

    if (target.charAt(1) == "8" && piece.charAt(1) == "P") {
        /* Handle a promotion */

        // Show promotion modal
        $(".center-wrapper").show();

        var handler = function () {
            selected_piece = $("#promotion").val();
            if (selected_piece == "invalid") {
                return;
            }

            var move = game.move({
                from: source,
                to: target,
                promotion: selected_piece
            });

            /* Reset modal */
            $(".center-wrapper").hide();
            $("#promotion").prop("selectedIndex", 0);

            /* Add promotion to move data */
            data["move"] = source + " " + target + " " + selected_piece;
            return sendMove(move, data);
        };

        $("#promotion").change(handler);
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

var onSnapEnd = function () {
    board.position(game.fen());
};

var onMouseoverSquare = function(square, piece) {
    var moves = game.moves({
        square: square,
        verbose: true
    });

    if (moves.length === 0) return;

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

var cfg = {
    draggable: true,
    position: 'start',
    onDragStart: onDragStart,
    onDrop: onDrop,
    onMouseoutSquare: onMouseoutSquare,
    onMouseoverSquare: onMouseoverSquare,
    onSnapEnd: onSnapEnd
};
board = ChessBoard('board', cfg);
