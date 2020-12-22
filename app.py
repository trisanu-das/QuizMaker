import os
import random
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["FLASK_DEBUG"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


app.debug = True
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

qna = []
rows = []


@app.route('/')
@login_required
def index():
    db = SQL("sqlite:///quiz.db")
    unp = {}
    u = db.execute("SELECT username FROM users ORDER BY username")
    tests = db.execute('SELECT username, papername FROM users JOIN papers ON users.id = papers.user_id')
    for i in u:
        temp = []
        for j in tests:
            if j['username'] == i['username']:
                temp.append(j['papername'])
        unp[i['username']] = temp
    return render_template('index.html', unp=unp)


@app.route('/makequiz', methods=["GET", "POST"])
@login_required
def make_quiz():
    db = SQL("sqlite:///quiz.db")
    if request.method == 'GET':
        return render_template('makequiz.html')
    else:
        db.execute("INSERT INTO papers (papername, user_id) VALUES(:paper, :user)", paper=request.form.get("quizname"),
                   user=session['user_id'])
        return redirect(url_for('index'))


@app.route('/takequiz', methods=["GET", "POST"])
@login_required
def take_quiz():
    db = SQL("sqlite:///quiz.db")
    if request.method == 'GET':
        return render_template('takequiz.html')
    else:
        global qna
        id = db.execute('SELECT id FROM papers WHERE papername = :papername', papername=request.form.get('test'))[0]['id']
        qnas = db.execute('SELECT question, answer, wa1, wa2, wa3 FROM questions WHERE paper_id = :p_id', p_id=id)
        qna = []
        c = 1
        for i in qnas:
            qna.append({'id': c, 'question': i['question'],
                        'answers': random.sample([i['answer'], i['wa1'], i['wa2'], i['wa3']], 4),
                        'correct': i['answer']})
            c += 1
        return redirect(url_for('quiz', quizname=request.form.get('test')))


@app.route('/quiz.html', methods=['GET', 'POST'])
@login_required
def quiz():
    if request.method == 'POST':
        result = 0
        total = 0
        perf = ''
        for question in qna:
            if request.form.get(str(question['id'])) == question['correct']:
                result += 1
            total += 1
        if result >= int(total * 0.75):
            perf = 'Excellent! Keep it up!'
        elif result >= int(total * 0.5):
            perf = 'Very Good!'
        elif result >= int(total * 0.25):
            perf = 'Good.'
        else:
            perf = 'Needs improvement.'
        return render_template('results.html', result=result, total=total, performance=perf)
    else:
        return render_template("quiz.html", data=qna, quiztitle=request.args.get('quizname'))


# @app.route('/quiz/<total>/<result>/<quizname>')
# @login_required
# def quiz2(total, result, quizname):
#     return redirect(url_for('results', total = total, result = result, quizname = quizname))


# @app.route('/results/<int:result>/<int:total>/<string:quizname>/')
# @login_required
# def results(result, total, quizname):
#     return render_template('results.html', total=total, result=result, quiztitle=quizname)


@app.route('/add', methods=['POST', 'GET'])
@login_required
def add_question():
    db = SQL("sqlite:///quiz.db")
    if request.method == 'GET':
        rows = []
        for i in db.execute('SELECT papername FROM papers WHERE user_id = :user', user = session['user_id']):
            rows.append(i['papername'])
        return render_template('addquestion.html', papers = rows)
    else:
        id = db.execute('SELECT id FROM papers WHERE papername = :papername', papername=request.form.get('paper'))[0][
            'id']
        db.execute(
            'INSERT INTO questions(question, answer, wa1, wa2, wa3, paper_id) VALUES (:question, :answer, :wa1, :wa2, :wa3, :paper_id)',
            question=request.form.get('question'), answer=request.form.get('answer'), wa1=request.form.get('wa1'),
            wa2=request.form.get('wa2'), wa3=request.form.get('wa3'), paper_id=id)
        return redirect(url_for('index'))


# @app.route('/editques2', methods = ['GET', 'POST'])
# @login_required
# def editp2():
#     db = SQL("sqlite:///quiz.db")
#     if request.method == 'GET':
#         data = []
#         for i in db.execute('SELECT papername FROM papers WHERE user_id = :user_id', user_id = session['user_id']):
#             data.append(i['papername'])
#         return render_template('editAndDeleteQuestion.html', data=data)
#     else:
#         j = {}
#         global rows
#         rows = []
#         c = 1
#         for i in db.execute('SELECT question, answer, wa1, wa2, wa3 FROM questions WHERE paper_id = (SELECT id FROM papers WHERE papername == :paper)', paper = request.form.get('paper')):
#             j = i
#             j['qid'] = c
#             rows.append(j)
#             c += 1
#         return redirect(url_for('viewques', rows=rows, paper=request.form.get('paper')))
#
#
# @app.route('/viewques', methods = ['GET', 'POST'])
# @login_required
# def viewques():
#     db = SQL("sqlite:///quiz.db")
#     if request.method == 'GET':
#         return render_template('viewAllQues.html', rows=request.form.get('rows'))
#     if request.method == 'POST':
#         if request.form.get('editp'):
#             return redirect(url_for('editquiz', paper = request.form.get('paper')))
#         if request.form.get('editq'):
#             return redirect(url_for('editques', paper = request.form.get('paper')))
#         if request.form.get('delq'):
#             return redirect(url_for('delques', paper = request.form.get('paper')))
#         if request.form.get('delp'):
#             paperid = db.execute('SELECT id FROM papers WHERE papername = :paper AND user_id = :user', paper =  request.form.get('paper'), user = session['user_id'])[0]['id']
#             db.execute('DELETE FROM papers WHERE papername = :paper AND user_id = :user', paper = request.form.get('paper'), user = session['user_id'])
#             db.execute('DELETE FROM questions WHERE paper_id = :paperid', paperid = paperid)
#             return redirect(url_for('index'))
#         if request.form.get('addq'):
#             return redirect(url_for('add_question', paper=request.form.get('paper')))
#
#
# @app.route('/editquiz', methods = ['GET', 'POST'])
# @login_required
# def editquiz():
#     db = SQL("sqlite:///quiz.db")
#     if request.method == 'POST':
#         db.execute('UPDATE papers SET papername = :npaper WHERE papername = :opaper', npaper = request.form.get('name'), opaper = request.form.get('paper'))
#         return redirect(url_for('index'))
#     else:
#         return render_template('changePapername.html')
#
#
# @app.route('/editques', methods = ['GET', 'POST'])
# @login_required
# def editques():
#     db = SQL("sqlite:///quiz.db")
#     if request.method == 'POST':
#         ques = ''
#         for i in rows:
#             if i['qid'] == int(request.form.get('id')):
#                 ques = i['question']
#                 break
#         db.execute('UPDATE questions SET question = :question, answer = :answer, wa1 = :wa1, wa2 = :wa2, wa3 = :wa3, paper_id = :paperid WHERE question = :question', question = request.form.get('ques'), answer = request.form.get('ans'), wa1 = request.form.get('wa1'), wa2 = request.form.get('wa2'), wa3 = request.form.get('wa3'), paperid = db.execute('SELECT id FROM papers WHERE papername = :paper AND user_id = :user', paper =  request.form.get('paper'), user = session['user_id'])[0]['id'])
#         return redirect(url_for('index'))
#     else:
#         return render_template('editQuestion.html', ids = rows)
#
#
# @app.route('/delques', methods = ['GET', 'POST'])
# @login_required
# def delques():
#     db = SQL("sqlite:///quiz.db")
#     if request.method == 'POST':
#         ques = ''
#         for i in rows:
#             if i['qid'] == int(request.form.get('id')):
#                 ques = i['question']
#                 break
#         db.execute('DELETE FROM questions WHERE question = :question', question = ques)
#         return redirect(url_for('index'))
#     else:
#         return render_template('deleteQuestion.html', ids = rows)



@app.route("/login", methods=["GET", "POST"])
def login():
    db = SQL("sqlite:///quiz.db")
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    db = SQL("sqlite:///quiz.db")
    """Register user"""
    if request.method == "POST":
        # Ensure username was submitted
        if request.form.get("username") == '':
            return apology("must provide username", 400)
        # Ensure password was submitted
        elif request.form.get("password") == '':
            return apology("must provide password", 400)
        elif request.form.get("confirmation") == '':
            return apology("must provide password confirmation", 400)
        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("passwords do not match", 400)
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))
        if len(rows) > 0:
            return apology("Username already taken")
        hashed = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users(username, hash) VALUES(:user, :hash)", user=request.form.get("username"),
                   hash=hashed)
        # Redirect user to home page
        return redirect("/")
    elif request.method == 'GET':
        return render_template("register.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
