from flask               import Flask, session, render_template, request, redirect, url_for, flash

import sqlite3
from flask_sqlalchemy    import SQLAlchemy
from flask_migrate       import Migrate

from flask_login         import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security   import generate_password_hash, check_password_hash
from login               import db, User
from pathlib             import Path

########################################
app = Flask(__name__)

app.config['SECRET_KEY'] = 'my_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'

db.init_app(app) #db = SQLAlchemy(app)
migrate = Migrate(app, db)

BASE_DIR = Path(__file__).resolve().parent
# Direct path to the database file
DB_PATH = BASE_DIR / 'instance' / 'user.db'
print(DB_PATH)

########################################
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


#I need the user id here.  I see it in the session variables.  I can pass it in
#to make sure I only get a single users order for pedals.
#I need to set up transaction record
#INSERT 4 records based on the four products available.  Delete when purchase is made.

###############################################################################
@app.route("/", methods = ['GET', 'POST'])
@app.route("/<int:total>", methods = ['GET', 'POST'])
@login_required  #send the user to the login page based on login_manager.login_view = 'login'
def home(total=0):
    l_product_string = []
    get_total   = 0
    total_units = 0
    print('home')

    #####################################
    try:
        conn = sqlite3.connect(DB_PATH)
        print('connection made')
    except Exception as e:
        print(e)
        cur.close()
        conn.close()

    cur = conn.cursor()
    cur.execute('''select product, description, amount, image_name 
                     from products''')
    rows = cur.fetchall()
    for row in rows:
        if row[0] not in session: #initalize all session variables so logic executes successfully when new users_id or new session enters.
           session[row[0]] = 0
        else:
            print(session[row[0]])
    #####################################
    # print(session)
    if request.method != 'POST':
        for item in rows:
            session_key = item[0]
            # print('session_key', session_key)
            output_str = f'{session_key} Delay pedal $ {session[item[0]] * item[2]}.00  | {session[item[0]]} units'
            l_product_string.append({'key': session_key, 'output_str': output_str, 'description': item[1],
                                     'amount': item[2], 'image': item[3]})
            get_total = get_total + (session[item[0]] * item[2])
            total_units   = total_units  +  session[item[0]]
        session['total_units'] = total_units
        session['get_total'] = get_total
    if request.method == 'POST':
        for item in rows:
            session_key = item[0]
            if session_key in request.form:
                session[item[0]] = int(request.form.get(session_key, 0))
                output_str = f'{session_key} Delay pedal $ {session[item[0]] * item[2]}.00  | {session[item[0]]} units'
                l_product_string.append({'key': session_key , 'output_str': output_str, 'description': item[1],
                                         'amount': item[2]  , 'image': item[3]})
                get_total = get_total + (session[item[0]] * item[2])
                total_units = total_units + session[item[0]]
            else:
                output_str = f'{session_key} Delay pedal $ {session[item[0]] * item[2]}.00  | {session[item[0]]} units'
                l_product_string.append({'key': session_key , 'output_str': output_str, 'description': item[1],
                                         'amount': item[2]  , 'image': item[3]})

                get_total = get_total + (session[item[0]] * item[2])
                total_units = total_units + session[item[0]]
        session['total_units'] = total_units
        session['get_total'] = get_total
    cur.close()
    conn.close()
    return render_template('index_2.html',l_product_string=l_product_string)


@app.route('/cart', methods = ['GET', 'POST'] )
@login_required
def cart():

    cart_submit = {'dummy_value' : 0}
    l_cart_submit = []
    #####################################
    try:
        conn = sqlite3.connect(DB_PATH)
        print('connection made')
    except Exception as e:
        print(e)
        cur.close()
        conn.close()

    cur = conn.cursor()
    cur.execute('''select product, description, amount, image_name
                   from products''')
    rows = cur.fetchall()
    #####################################

    l_product_string = []

    if request.method == 'POST':
        l_product_string = []
        cart_submit = request.form.to_dict()
        l_cart_submit.append(cart_submit)
        cur.execute('''insert into receipts (customer_name, address, city,
                                             state, total_cost, units, user_id)
                        values(?, ?, ?, ?, ?, ?, ?);''', (l_cart_submit[0]['customerName'], l_cart_submit[0]['streetAddress'],l_cart_submit[0]['city'], l_cart_submit[0]['state'], session['get_total'], session['total_units'], session['_user_id'])
        )
        conn.commit()
    else:
        l_cart_submit.append('empty')  #use to hide the receipt section until an order has been submitted

    for item in rows:
        session_key = item[0]
        #print(session_key)
        output_str = f'{session_key} Delay pedal $ {session[item[0]] * item[2]}.00  | {session[item[0]]} units'
        l_product_string.append({'output_str': output_str})

    if request.method == 'POST':
        for item in rows:
            session[item[0]] = 0

    total       = session['get_total']
    total_units = session['total_units']
    cur.close()
    conn.close()

    return render_template('cart.html',
                           p_total_price    = total,
                           p_total_units    = total_units,
                           l_product_string = l_product_string,
                           l_cart_submit    = l_cart_submit
                           )


@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Username already exists')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_pw)

        db.session.add(new_user)
        db.session.commit()

        flash('Account created!, Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():

    logout_user()
    flash("You've been logged out.")
    return redirect(url_for('login'))


###############################################################################
if __name__ == '__main__':
    print(__name__)
    print('call function app.run()');print()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
    print("past app.run()");print()