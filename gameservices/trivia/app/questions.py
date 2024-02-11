import pandas as pd


class TriviaDB:
    """A class to interact with the trivia database.

    Attributes:
        db_path: A string path to the csv file.
    """

    def __init__(self, db_path: str):
        """Initializes TriviaDB with a questions csv files

        Args:
            db_path: A string path to the csv file.
        """
        self.db_path = db_path
        self.df = pd.read_csv(db_path, on_bad_lines="skip")

    def get_categories(self):
        # Retrieve all the categories from the csv
        return self.df["Category"].unique().tolist()

    def get_question(self):
        # Retrieve a random question from the database
        result = self.df.sample(n=1).squeeze()

        # If a question is found, parse it into the desired format
        if result is not None:
            subjects = ["Question", "Options", "Answer"]
            question, options_str, answer = result[subjects]
            options = options_str.split(",")
            question_dict = {
                "question": question,
                "option1": options[0],
                "option2": options[1],
                "option3": options[2],
                "option4": options[3],
                "correct": f"option{answer}",
            }
            return question_dict
        return None

    def get_question_by_category(self, category: str):
        # Retrieve a random question from the database for the given category
        category_df = self.df[self.df["Category"] == category]
        result = category_df.sample(n=1).squeeze()

        # If a question is found, parse it into the desired format
        if result is not None:
            question, options_str, answer = result[["Question", "Options", "Answer"]]
            options = options_str.split(",")
            question_dict = {
                "question": question,
                "option1": options[0],
                "option2": options[1],
                "option3": options[2],
                "option4": options[3],
                "correct": f"option{answer}",
            }
            return question_dict
        return None


# Example usage
# db = TriviaDB('trivia_questions.csv')
# print(db.get_categories())
# print(db.get_question())
# print(db.get_question_by_category('sports'))
