import sqlite3
import hashlib

from flask import Flask, request

app = Flask(__name__)


def connect():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    c = conn.cursor()
    c.execute("CREATE TABLE users (username TEXT, password TEXT, rank TEXT)")
    c.execute("INSERT INTO users VALUES ('admin', 'e1568c571e684e0fb1724da85d215dc0', 'admin')")
    c.execute("INSERT INTO users VALUES ('bob', '2b903105b59299c12d6c1e2ac8016941', 'user')")
    c.execute("INSERT INTO users VALUES ('alice', 'd8578edf8458ce06fbc5bb76a58c5ca4', 'moderator')")

    c.execute("CREATE TABLE SSN(user_id INTEGER, number TEXT)")
    c.execute("INSERT INTO SSN VALUES (1, '480-62-10043')")
    c.execute("INSERT INTO SSN VALUES (2, '690-10-6233')")
    c.execute("INSERT INTO SSN VALUES (3, '401-09-1516')")

    conn.commit()
    return conn


CONNECTION = connect()


@app.route("/login")
def login():
    username = request.args.get('username', '')
    password = request.args.get('password', '')
    md5 = hashlib.new('md5', password.encode('utf-8'))
    password = md5.hexdigest()
    c = CONNECTION.cursor()
    c.execute("SELECT * FROM users WHERE username = ? and password = ?", (username, password))
    data = c.fetchone()
    if data is None:
        return 'Incorrect username and password.'
    else:
        return 'Welcome %s! Your rank is %s.' % (username, data[2])


@app.route("/users")
def list_users():
    rank = request.args.get('rank', 'user')
    if rank == 'admin':
        return "Can't list admins!"
    c = CONNECTION.cursor()
    c.execute("SELECT username, rank FROM users WHERE rank = '{0}'".format(rank))
    data = c.fetchall()
    return str(data)


if __name__ == '__main__':
    app.run(debug=True)
