from flask import Flask, render_template, request, redirect, url_for, session, g
import mysql.connector
from flask_session import Session
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "super secret key"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configuración de la base de datos
def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="guerrero2601",
            database="logistica_microempresa"
        )
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Función para hashear y actualizar contraseñas en la base de datos
conexion = mysql.connector.connect(
    host="localhost",
    user="root",
    password="guerrero2601",
    database="logistica_microempresa"
)

def actualizar_password(nombre_usuario, password_plano):
    """
    Hashea la contraseña y actualiza la base de datos.
    """
    bcrypt = Bcrypt()
    hashed_password = bcrypt.generate_password_hash(password_plano).decode('utf-8')
    cursor = conexion.cursor()
    query = "UPDATE usuarios SET password = %s WHERE nombre_usuario = %s"
    values = (hashed_password, nombre_usuario)
    cursor.execute(query, values)
    conexion.commit()
    cursor.close()
    print(f"Contraseña de {nombre_usuario} actualizada en la base de datos.")

if __name__ == "__main__":
    # Actualizar contraseñas
    actualizar_password('mike', '6969')
    actualizar_password('karen', '1010')
    actualizar_password('raz', '2424')

    # Cerrar la conexión a la base de datos
    conexion.close()

    print("Actualización de contraseñas completada.")


# Ruta para agregar categorías
@app.route('/agregar_categoria', methods=['POST'])
def agregar_categoria():
    if request.method == 'POST':
        nombre_categoria = request.form['nombre_categoria']
        db = get_db()
        cursor = db.cursor()
        query = "INSERT INTO categorias (nombre_categoria) VALUES (%s)"
        values = (nombre_categoria,)
        cursor.execute(query, values)
        db.commit()
        cursor.close()
        return redirect(url_for('categorias'))  # Redirige a la página de categorías
    else:
        return "Error: Método no permitido"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/productos')
def productos():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT p.id_producto, p.nombre_producto, c.nombre_categoria, p.stock, p.precio, p.imagen_url "
                   "FROM productos p "
                   "LEFT JOIN categorias c ON p.id_categoria = c.id_categoria")
    productos = cursor.fetchall()
    cursor.close()
    return render_template('productos.html', productos=productos)

@app.route('/categorias')
def categorias():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM categorias")
    categorias = cursor.fetchall()
    cursor.close()
    return render_template('categorias.html', categorias=categorias)

@app.route('/agregar_producto')
def agregar_producto():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM categorias")
    categorias = cursor.fetchall()
    cursor.close()
    return render_template('agregar_producto.html', categorias=categorias)

@app.route('/guardar_producto', methods=['POST'])
def guardar_producto():
    if request.method == 'POST':
        nombre = request.form['nombre']
        stock = request.form['stock']
        precio = request.form['precio']
        descripcion = request.form['descripcion']
        id_categoria = request.form['categoria']
        imagen = request.files.get('imagen')

        imagen_url = None
        if imagen:
            filename = imagen.filename
            upload_path = "uploads/"
            os.makedirs(upload_path, exist_ok=True)
            imagen_path = os.path.join(upload_path, filename)
            imagen.save(imagen_path)
            imagen_url = imagen_path

        db = get_db()
        cursor = db.cursor()
        query = "INSERT INTO productos (nombre_producto, stock, precio, descripcion, id_categoria, imagen_url) VALUES (%s, %s, %s, %s, %s, %s)"
        values = (nombre, stock, precio, descripcion, id_categoria, imagen_url)
        cursor.execute(query, values)
        db.commit()
        cursor.close()
        return redirect(url_for('productos'))

    return "Error al guardar el producto"

@app.route('/pedidos')
def pedidos():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT v.id_venta, v.fecha_venta, u.nombre_usuario, v.total, v.estado "
                    "FROM ventas v "
                    "LEFT JOIN usuarios u ON v.id_usuario = u.id_usuario")
    pedidos = cursor.fetchall()
    cursor.close()
    return render_template('pedidos.html', pedidos=pedidos)

@app.route('/reportes')
def reportes():
    return render_template('reportes.html')

@app.route('/configuraciones')
def configuraciones():
    return render_template('configuraciones.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor(dictionary=True)
        query = "SELECT * FROM usuarios WHERE nombre_usuario = %s"
        values = (username,)
        cursor.execute(query, values)
        user = cursor.fetchone()
        cursor.close()

        if user and bcrypt.check_password_hash(user['password'], password):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Inicio de sesión fallido. Usuario o contraseña incorrectos.")
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.before_request
def before_request():
    if request.endpoint not in ['login', 'static'] and not session.get('logged_in'):
        return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
