from functools import wraps
from flask import redirect, session
import datetime as dt
import random

QUOTES = ['“A reader lives a thousand lives before he dies . . . The man who never reads lives only one.” - George R.R. Martin','“Until I feared I would lose it, I never loved to read. One does not love breathing.” - Harper Lee',\
    '“Never trust anyone who has not brought a book with them.” - Lemony Snicket','“You can never get a cup of tea large enough or a book long enough to suit me.” - C.S. Lewis','“Reading is essential for those who seek to rise above the ordinary.” - Jim Rohn',\
        '“I find television very educating. Every time somebody turns on the set, I go into the other room and read a book.” - Groucho Marx','“Classic – a book which people praise and dont read.” - Mark Twain','“You dont have to burn books to destroy a culture. Just get people to stop reading them.” - Ray Bradbury',\
            '“So please, oh please, we beg, we pray, go throw your TV set away, and in its place you can install a lovely bookshelf on the wall.” - Roald Dahl','“Think before you speak. Read before you think.” - Fran Lebowitz']

def set_quote(quotes):
        return [dt.date.today(),random.choice(quotes)]

QUOTE = set_quote(QUOTES)

def login_required(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args,**kwargs)
    return decorated_function

