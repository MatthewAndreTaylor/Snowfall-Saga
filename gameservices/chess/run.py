from app import create_chess_app

app = create_chess_app()

if __name__ == "__main__":
    app.run(debug=True, port=8888)
