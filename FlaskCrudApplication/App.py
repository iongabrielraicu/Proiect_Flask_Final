from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import stripe
import pyodbc
import os


app = Flask(__name__)
public_key = "pk_test_6pRNASCoBOKtIshFeQd4XMUh"
stripe.api_key = "sk_test_BQokikJOvBiI2HlWgH4olfQ2"
app.secret_key = 'your_secret_key'  # Change this to a random secret key
app.config['UPLOAD_FOLDER'] = 'static/uploads'
# For simplicity, using a hardcoded username and password
VALID_USERNAME = 'admin'
VALID_PASSWORD = 'password'

def check_credentials(username, password):
    return username == VALID_USERNAME and password == VALID_PASSWORD

def is_user_authenticated():
    return 'username' in session

@app.route('/')
def index():
    if is_user_authenticated():
        # Fetch all products from the database
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM dbo.Produse")
        products = cursor.fetchall()

        connection.close()

        return render_template('index.html', products=products)
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if check_credentials(username, password):
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Please check your username and password.', 'error')

    return render_template('login.html')


# Database connection parameters
server = 'DESKTOP-T6KR4SO\SQLEXPRESS'
database = 'Proiect'
username = 'sa'
password = 'sa1234'

# Create a connection string
connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

# Function to get a database connection
def get_db_connection():
    return pyodbc.connect(connection_string)
@app.route('/logout')
def logout():
    flash('Logout successful!', 'success')
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/insert', methods=['POST'])
def insert():
    # Example: Insert data into the database
    if request.method == 'POST':
      flash("Produs inserat cu succes")
      nume= request.form['nume']
      cantitate= request.form['cantitate']
      pret= request.form['pret']
    connection = get_db_connection()
    cur =connection.cursor()
    cur.execute("INSERT INTO Produse (nume,cantitate,pret) VALUES (?,?,?)",(nume,cantitate,pret))
    connection.commit()
    connection.close()
    return redirect(url_for('index'))
@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')
@app.route('/update', methods=['POST', 'GET'])
def update():
    if request.method == 'POST':
        id = request.form['id']
        nume= request.form['nume']
        cantitate= request.form['cantitate']
        pret= request.form['pret']
        connection = get_db_connection()
        cur=connection.cursor()
        cur.execute("""
            UPDATE Produse SET nume=?, cantitate=?, pret=? WHERE id=?
        """, (nume.replace("'", "''"), cantitate, pret, id))
        flash("Update realizat cu succes")
        connection.commit()
        return redirect(url_for('index'))

@app.route('/delete/<string:id>', methods=['POST', 'GET'])
def delete(id):

    flash(f"Produsul cu id: {id} a fost sters")
    connection = get_db_connection()
    cur=connection.cursor()
    cur.execute("DELETE FROM Produse WHERE id = ?", (id))
    connection.commit()
    return redirect(url_for('index'))

@app.route('/cart/<int:product_id>')
def cart(product_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Retrieve product information based on the product ID
    cursor.execute("SELECT id, nume,pret, img_path FROM Produse WHERE id=?", (product_id,))
    result = cursor.fetchone()

    if result:
        product_info = {
            'id': result[0],
            'nume': result[1],
            'pret': result[2],
            'img_path': result[3],
        }
        connection.close()
        return render_template('cart.html', product_info=product_info)
    else:
        connection.close()
        return "Product not found", 404
@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):

    if 'cart' in session:
        if product_id in session['cart']:
            session['cart'].remove(product_id)

    return redirect(url_for('index'))
@app.route('/afisare_payment/<float:pret>', methods=['POST'])
def afisare_payment(pret):
    pret=pret


    return render_template('afisare_payment.html', public_key=public_key, pret=pret)

@app.route('/payment', methods=['POST'])
def payment():
    # CUSTOMER INFO
    customer = stripe.Customer.create(email=request.form['stripeEmail'],
                                      source=request.form['stripeToken'])

    # PAYMENT INFO
    charge = stripe.Charge.create(
        customer=customer.id,
        amount=1999, # 19.99
        currency='ron',
        description='Donation'
    )
    return render_template('afisare_payment.html')
@app.route('/upload', methods=['POST'])
def upload():
    if request.method =='POST':
        image_file = request.files['image']
        product_id = request.form['product_id']
        image_path = image_file.filename
        image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename))
        connection = get_db_connection()
        image_path_final=f'static/uploads/{image_file.filename}'
        cur = connection.cursor()
        cur.execute("""
                UPDATE Produse SET img_path=? WHERE id=?
            """, (image_path_final, product_id))
        flash(f"Poza incarcata pentru id {product_id}")
        connection.commit()
    return redirect(url_for('index'))


@app.route('/show_image/<int:product_id>')
def show_image(product_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT img_path FROM Produse WHERE id=?", (product_id,))
    result = cursor.fetchone()

    img_path = None

    if result:
        img_path = result[0]
    connection.close()
    print(img_path)
    if img_path:
        return send_file(img_path)
    return "Image not found", 404
if __name__ == '__main__':
    app.run(debug=True)

