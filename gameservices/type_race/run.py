from app import create_type_race_app

app = create_type_race_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8003)
