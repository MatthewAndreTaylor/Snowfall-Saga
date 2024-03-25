from app import create_chess_app

app = create_chess_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8004)
