from flask import Flask, render_template, request, g, session, redirect, url_for
from database import get_db, connect_db
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3


app=Flask( __name__ , template_folder="templates")
app.config['SECRET_KEY'] = os.urandom(24)


emailList=[]
passwordList=[]
wholeCredentials=[]
email = ""
password = ""
name = ""
authentic = ""

class Question:
    question= ""
    option1= ""
    option2= ""
    option3= ""
    option4= ""
    correct= ""
    qnum= ""


class Score:
    name= ""
    email= ""
    score= ""
 
    
def making_marks(data):
    name, email, score = data
    return "{} {} {}".format(name, email, score)        
    
 
#function to spearate username and password     
def getField(line,field): 
    storedField=""
    c=''
    idx=0
    commaFound=0   
    while ( commaFound < field+1 and idx < len(line)):
        c=line[idx]   
        if c == ',':
            commaFound+=1
        elif commaFound == field:
            storedField=storedField+str(c)
        idx+=1    
    return storedField


def making_objects(listElement ,number):
    p=Question()
    p.question= getField(listElement, 0)
    p.option1= getField(listElement, 1)
    p.option2= getField(listElement, 2)
    p.option3= getField(listElement, 3)
    p.option4= getField(listElement, 4)
    p.correct= getField(listElement, 5)
    p.qnum= number
    return p


def making_marks(listElement):
    s= Score()
    s.name= getField(listElement , 0)
    s.email= getField(listElement , 1)
    s.score= getField(listElement , 3)
    return s
    


@app.route("/index")
def home():
    global email
    global password
    if email=="admin@host.local" and password == "12789":
        return render_template("admin.html")
    elif verify(email , password):
        return render_template("user.html" , var=authentic)
    return render_template("index.html")


def verify(email, pw):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, pw))
    result = c.fetchone()
    conn.close()
    if result:
        authentic = result[3]
        print(authentic)
        return True
    else:
        return False
    


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()
def get_current_user():
    user_result = None
    if 'user' in session:
        user = session['user']
        db = get_db()
        user_cur = db.execute('select id, name, email, password, score, attempt, total from users where name = ?', [user])
        user_result = user_cur.fetchone()
    return user_result



@app.route("/onsignup", methods=["GET", "POST"])
def submit():
    if request.method == "POST":
        db = get_db() 
        existing_user_cur = db.execute('select id from users where name = ?', [request.form['email']])
        existing_user = existing_user_cur.fetchone()
        if existing_user:
            return render_template('register.html', error = 'Username already taken, Try different username.')
        hashed_password = generate_password_hash(request.form['password'], method='sha256')
        db.execute('insert into users (name, email, password, score, attempt, total ) values (?, ?, ?, ?, ?, ?)', [request.form['name'], request.form['email'], hashed_password, '0', '0', '0'])
        db.commit()
        return render_template('index.html')
    return render_template('index.html')

    

@app.route('/onlogin', methods=['GET', 'POST'])
def userVerify():
    error = None
    if request.method == 'POST':
        db = get_db()
        email = request.form['email']
        password = request.form['password']
        user_cur = db.execute('select id, email, password from users where  email=? ', [email])
        user_result = user_cur.fetchone()
        if user_result:
            if check_password_hash(user_result['password'], password):
                return render_template('user.html')
        elif email=="admin@host.local" and password== "12789":
            return render_template('admin.html')     
    else:
        error = 'Username or password did not match. Try again.'
    return render_template('invalid.html', error = error)



@app.route("/quiz", methods=["POST", "GET"])
def quiz():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM questions")
    results = c.fetchall()
    whole_quiz = []
    for i, row in enumerate(results):
        q = Question()
        q.question = row[1]
        q.option1 = row[2]
        q.option2 = row[3]
        q.option3 = row[4]
        q.option4 = row[5]
        q.correct = row[6]
        q.qnum = i + 1

        whole_quiz.append(q)
    conn.close()
    return render_template("quiz.html", array=whole_quiz)



@app.route("/addquestion" , methods=["POST","GET"])
def add_question():
    
    if request.method == 'POST':
        connection = sqlite3.connect('data.db')
        cursor = connection.cursor()
        
        ques = request.form['question']
        opt1 = request.form['op1']
        opt2 = request.form['op2']
        opt3 = request.form['op3']
        opt4 = request.form['op4']
        cor = request.form['corop']
        
        cursor.execute("INSERT INTO questions (question, option1, option2, option3, option4, correct) VALUES (?, ?, ?, ?, ?, ?)", [ques, opt1, opt2, opt3, opt4, cor ])
        connection.commit()
        connection.close()
    return render_template('admin.html')   



@app.route("/submit" , methods=["POST","GET"])
def submit_quiz():
    
    global email
    wholeCredentials = []
    score = 0
    
    # Length of the table
    connection = sqlite3.connect('data.db')
    cursor = connection.cursor()
    cursor.execute("SELECT * from questions;")
    questions = cursor.fetchall()
    cursor.close()
    connection.close()

    total = len(questions)

    for idx in range(0, total):
        ans = questions[idx]
        mcq="mcq"+str(idx+1)
        if (ans[6] == request.form.get(mcq)):
            score += 1
    
    print("Your score is", score)
    
    # Insert into the users table
    connection = sqlite3.connect('data.db')
    cursor = connection.cursor()

    # Find current user in the table    
    id = 8
    update_query = f"UPDATE users set score = {score}, total = {total}, attempt = {total} where id = {id};"
    cursor.execute(update_query)
    connection.commit()
    connection.close()
    
    return render_template("user.html")




@app.route("/show", methods=["POST","GET"])
def results():
    global email
    score = 0
    attempt = 0
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT score, attempt FROM users WHERE email=?", (email,))
    result = cursor.fetchone()
    if result:
        score = result[0]
        attempt = result[1]
    conn.close()
    return render_template("result.html", var1=score, var2=attempt)



@app.route("/showall", methods=["POST","GET"])
def showall():
    objects_list = []
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, email, score FROM users")
    results = cursor.fetchall()
    for result in results:
        obj = making_marks(result)
        objects_list.append(obj)
    conn.close()
    return render_template("showall.html", list=objects_list)



@app.route("/login" , methods=["POST","GET"])
def validation():
    return render_template("login.html")



@app.route("/register" , methods=["POST","GET"])
def register():
    return render_template("register.html")



@app.route("/quizstrt" , methods=["POST","GET"])
def strt():
    return render_template("quizstrt.html")



@app.route("/add" , methods=["POST","GET"])
def add():
    return render_template("addques.html")



@app.route("/logout" , methods=["POST","GET"])
def logout():
    global email
    global password
    email = ""
    password= ""
    return render_template("index.html")



if __name__ == "__main__":
    app.run(debug= True , host="0.0.0.0")
