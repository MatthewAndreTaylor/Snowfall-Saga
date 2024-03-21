const socket = new WebSocket(
  `ws://${document.domain}:${location.port}/chess`,
);

let selectedSquare = null;

function squareClicked(squareId) {
    if (selectedSquare === null) {
        selectedSquare = squareId;
        console.log(squareId);
        document.getElementById(squareId).style.backgroundColor = "red"; // Change background color to red
    } else {
        make_move(selectedSquare, squareId);
        selectedSquare = null;
    }
}

function make_move(startSquare, endSquare) {
    // Reset all squares' background colors
    document.getElementById(startSquare).style.backgroundColor = document.getElementById(startSquare).classList.contains('light') ? '#f0d9b5' : '#b58863';

    // This is where you can handle the move logic
    console.log("Move from " + startSquare + " to " + endSquare);
    socket.send(
    JSON.stringify({
      type: "makeMove",
      move: startSquare + endSquare
    }),
  );
}

document.body.addEventListener('click', function(event) {
    if (!event.target.closest('.chessboard div')) {
        // Reset selectedSquare and restore normal colors of all squares

        if (selectedSquare != null) {
            document.getElementById(selectedSquare).style.backgroundColor = document.getElementById(selectedSquare).classList.contains('light') ? '#f0d9b5' : '#b58863';
        }
        selectedSquare = null;
    }
});

function displayChessBoard(chessBoardString) {
    // Split the string representation into rows
    const rows = chessBoardString.trim().split('\n');

    const chessboardElement = document.getElementById('chessboard');
    chessboardElement.innerHTML = ''; // Clear previous content

    rows.forEach((row, rowIndex) => {
        // Split each row into individual squares
        const squares = row.trim().split(' ');

        squares.forEach((piece, colIndex) => {
            const squareId = String.fromCharCode(97 + colIndex) + (8 - rowIndex);
            const squareElement = document.createElement('div');
            squareElement.id = squareId;
            squareElement.className = (rowIndex + colIndex) % 2 === 0 ? 'light' : 'dark';
            squareElement.textContent = piece === '.' ? '' : piece;
            squareElement.addEventListener('click', () => squareClicked(squareId)); // Attach event listener
            chessboardElement.appendChild(squareElement);
        });
    });
}

// Call the function with the example string

socket.addEventListener("message", (message) => {
  const data = JSON.parse(message.data);

  switch (data.type) {
    case "board":
        displayChessBoard(data.board);
    break;
  }
});
