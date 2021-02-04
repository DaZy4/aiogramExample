import sqlite3


class DataBase:
    def __init__(self, db_name):
        self.db = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.db.cursor()

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            tg_id INT,
            full_name TEXT,
            state INT,
            birthday TEXT,
            residence_place TEXT,
            study_work TEXT,
            balance FLOAT,
            currency TEXT,
            lang TEXT,
            lang_msg_id INT,
            admin_pay_msg_id INT,
            pay_sum FLOAT
            )""")

    def user_exists(self, id):
        self.cursor.execute(f"SELECT tg_id FROM users WHERE tg_id = {id}")
        return False if self.cursor.fetchone() is None else True

    def new_user(self, id):
        self.cursor.execute(f"INSERT INTO users VALUES ({id}, '', 7, '', '', '', 0.0, '', '', 0, 0, 0.0)")
        self.db.commit()

    def change_state(self, id, state_id):
        self.cursor.execute(f"UPDATE users SET state = {state_id} WHERE tg_id = {id}")
        self.db.commit()

    def set_full_name(self, id, full_name):
        self.cursor.execute(f"UPDATE users SET full_name = \"{full_name}\" WHERE tg_id = {id}")
        self.db.commit()

    def set_place_of_residence(self, id, place):
        self.cursor.execute(f"UPDATE users SET residence_place = \"{place}\" WHERE tg_id = {id}")
        self.db.commit()

    def set_place_of_work(self, id, place):
        self.cursor.execute(f"UPDATE users SET study_work = \"{place}\" WHERE tg_id = {id}")
        self.db.commit()

    def set_birthday_date(self, id, birthday):
        self.cursor.execute(f"UPDATE users SET birthday = \"{birthday}\" WHERE tg_id = {id}")
        self.db.commit()

    def set_currency(self, id, currency):
        self.cursor.execute(f"UPDATE users SET currency = \"{currency}\" WHERE tg_id = {id}")
        self.db.commit()

    def set_lang(self, id, language):
        self.cursor.execute(f"UPDATE users SET lang = \"{language}\" WHERE tg_id = {id}")
        self.db.commit()

    def get_lang(self, id):
        self.cursor.execute(f"SELECT * FROM users WHERE tg_id = {id}")
        return self.cursor.fetchone()[8]

    def get_currency(self, id):
        self.cursor.execute(f"SELECT * FROM users WHERE tg_id = {id}")
        return self.cursor.fetchone()[7]

    def get_state(self, id):
        self.cursor.execute(f"SELECT * FROM users WHERE tg_id = {id}")
        return self.cursor.fetchone()[2]

    def get_users(self):
        self.cursor.execute("SELECT * FROM users")
        return self.cursor.fetchall()
        
    def get_balance(self, id):
        self.cursor.execute(f"SELECT * FROM users WHERE tg_id = {id}")
        return self.cursor.fetchone()[6]

    def add_balance(self, id, amount):
        self.cursor.execute(f"UPDATE users SET balance = balance + {amount} WHERE tg_id = {id}")
        self.db.commit()

    """
    state identifier's:
        0 - nothing selected
        1 - selecting language
        2 - selecting full name
        3 - selecting place of residence
        4 - selecting place of study/work
        5 - selecting birthday date
        6 - selecting currency
        7 - set sum of pay
        8 - set sum of top-up amount
    """
