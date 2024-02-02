import sqlite3
import json


class TriviaDB:
    """A class to interact with the trivia database.

    Attributes:
        conn: A SQLite connection object.
        cursor: A SQLite cursor object.
    """

    def __init__(self, db_path):
        """Initializes TriviaDB with a connection to the SQLite database.

        Args:
            db_path: A string path to the SQLite database file.
        """
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def close(self):
        # Close the database connection
        self.conn.close()

    def get_categories(self):
        # Retrieve all the categories from the database
        query = "SELECT DISTINCT category FROM questions_data"
        self.cursor.execute(query)
        result = self.cursor.fetchall()
        return [row[0] for row in result]

    def get_question(self):
        # Retrieve a random question from the database
        query = "SELECT question, options, answer FROM questions_data ORDER BY RANDOM() LIMIT 1"
        self.cursor.execute(query)
        result = self.cursor.fetchone()

        # If a question is found, parse it into the desired format
        if result:
            question, options_json, answer = result
            options = json.loads(options_json)

            # Construct the dictionary to return
            question_dict = {
                'question': question,
                'option1': options[0],
                'option2': options[1],
                'option3': options[2],
                'option4': options[3],
                # Correct option is dynamically determined from the answer index
                'correct': f'option{answer}'
            }
            return question_dict
        else:
            # Return None or raise an exception if no question is found
            return None

    def get_question_by_category(self, category):
        # Retrieve a random question from the database for the given category
        query = """
        SELECT question, options, answer FROM questions_data 
        WHERE category = ? ORDER BY RANDOM() LIMIT 1
        """
        self.cursor.execute(query, (category,))
        result = self.cursor.fetchone()

        # If a question is found, parse it into the desired format
        if result:
            question, options_json, answer = result
            options = json.loads(options_json)

            # Construct the dictionary to return
            question_dict = {
                'question': question,
                'option1': options[0],
                'option2': options[1],
                'option3': options[2],
                'option4': options[3],
                # Correct option is dynamically determined from the answer index
                'correct': f'option{answer}'
            }
            return question_dict
        else:
            # Return None or raise an exception if no question is found
            return None

    def _insert_question(self, category, question, options, answer):
        """Inserts a new question into the database.

        Args:
            category: A string representing the category of the question.
            question: A string containing the question text.
            options: A list of strings containing the question options.
            answer: An integer representing the index of the correct answer in the options.

        Returns:
            A boolean value. True if the question was inserted successfully, False otherwise.
        """
        options_json = json.dumps(options)
        insert_stmt = """
        INSERT INTO questions_data (category, question, options, answer)
        VALUES (?, ?, ?, ?)
        """
        try:
            self.cursor.execute(
                insert_stmt, (category, question, options_json, answer)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            return False

# Example usage:
# db = TriviaDB('./backend/trivia_db.db')
# db.<method_name>(<args>)
# db.close()
