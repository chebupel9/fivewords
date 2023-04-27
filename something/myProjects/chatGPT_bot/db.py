import sqlite3


class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    def user_exists(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchall()
            return bool(len(result))

    def add_user(self, user_id):
        with self.connection:
            self.cursor.execute("INSERT INTO users (user_id, chat) VALUES (?, ?)", (user_id, '[]'))
            self.cursor.execute("UPDATE users SET reg_date = DATE('now') WHERE user_id = ?", (user_id,))

    def get_user_chat(self, user_id):
        with self.connection:
            chat = self.cursor.execute("SELECT chat FROM users WHERE user_id = ?", (user_id,)).fetchone()
            chat = str(chat[0]).replace('"', '``').replace("'", '"')
            return chat

    def update_user_chat(self, chat, user_id):
        with self.connection:
            self.cursor.execute("UPDATE users SET chat = ? WHERE user_id = ?", (chat, user_id,))
