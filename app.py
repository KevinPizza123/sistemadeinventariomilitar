import os
import bcrypt
from flask import Flask, jsonify, render_template, request, redirect, session, url_for
import psycopg2
from dotenv import load_dotenv


load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

# Configuración de la base de datos
DATABASE_URL = 'postgresql://postgres:herbye25@localhost/gestion_locales' # Reemplaza con tus datos

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn
# Panel de control
@app.route('/dashboard')
def dashboard():
    if 'vendedor_id' not in session:
        return redirect(url_for('login'))
    if session['es_admin']:
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('vendedor_dashboard'))

@app.route('/admin')
def admin_dashboard():
    if 'vendedor_id' not in session or not session['es_admin']:
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')

@app.route('/vendedor')
def vendedor_dashboard():
    if 'vendedor_id' not in session or session['es_admin']:
        return redirect(url_for('login'))
    return render_template('vendedor_dashboard.html')

# Funciones de autenticación
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')



def check_password(password, hashed_password):
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

@app.route('/')
def index():
    if 'vendedor_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nombre = request.form['nombre']
        password = request.form['password']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT vendedor_id, contraseña, es_admin FROM Vendedores WHERE nombre = %s;', (nombre,))
        vendedor = cur.fetchone()
        cur.close()
        conn.close()
        if vendedor and check_password(password, vendedor[1]):
            session['vendedor_id'] = vendedor[0]
            session['es_admin'] = vendedor[2]
            return redirect(url_for('dashboard'))
        else:
            return 'Usuario o contraseña incorrectos'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('vendedor_id', None)
    session.pop('es_admin', None)
    return redirect(url_for('login'))




# Funciones auxiliares
def get_locales_vendedor(vendedor_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT local_id
        FROM Vendedores_Locales
        WHERE vendedor_id = %s;
    ''', (vendedor_id,))
    locales = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return locales

@app.route('/admin/registrar_vendedor', methods=['GET', 'POST'])
def registrar_vendedor():
    if 'vendedor_id' not in session or not session['es_admin']:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        nombre = request.form['nombre']
        password = request.form['password']
        locales_ids = request.form.getlist('locales') #obtener lista de locales seleccionados.
        hashed_password = hash_password(password)
        cur.execute('INSERT INTO Vendedores (nombre, contraseña, es_admin) VALUES (%s, %s, FALSE) RETURNING vendedor_id;', (nombre, hashed_password))
        vendedor_id = cur.fetchone()[0]
        for local_id in locales_ids:
            cur.execute('INSERT INTO Vendedores_Locales (vendedor_id, local_id) VALUES (%s, %s);', (vendedor_id, local_id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('admin_locales'))
    cur.execute('SELECT local_id, nombre FROM Locales;')
    locales = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('registrar_vendedor.html', locales=locales)

@app.route('/admin/productos')
def admin_productos():
    if 'vendedor_id' not in session or not session['es_admin']:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT p.nombre, l.nombre, i.cantidad
        FROM Productos p
        JOIN Inventario i ON p.producto_id = i.producto_id
        JOIN Locales l ON i.local_id = l.local_id;
    ''')
    resultados = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin_productos.html', resultados=resultados)

@app.route('/admin/productos/filtrar')
def admin_productos_filtrar():
    if 'vendedor_id' not in session or not session['es_admin']:
        return jsonify([])
    cliente = request.args.get('cliente', '')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT p.nombre, l.nombre, i.cantidad
        FROM Productos p
        JOIN Inventario i ON p.producto_id = i.producto_id
        JOIN Locales l ON i.local_id = l.local_id
        WHERE p.nombre ILIKE %s;
    ''', ('%' + cliente + '%',))
    resultados = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(resultados)

@app.route('/admin/agregar_producto', methods=['GET', 'POST'])
def admin_agregar_producto():
    if 'vendedor_id' not in session or not session['es_admin']:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio = request.form['precio']
        local_id = request.form['local_id']
        cantidad = request.form['cantidad']
        cur.execute('INSERT INTO Productos (nombre, descripcion, precio) VALUES (%s, %s, %s) RETURNING producto_id;', (nombre, descripcion, precio))
        producto_id = cur.fetchone()[0]
        cur.execute('INSERT INTO Inventario (local_id, producto_id, cantidad) VALUES (%s, %s, %s);', (local_id, producto_id, cantidad))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('admin_productos'))
    cur.execute('SELECT local_id, nombre FROM Locales;')
    locales = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin_agregar_producto.html', locales=locales)

@app.route('/admin/agregar_local', methods=['GET', 'POST'])
def agregar_local():
    if 'vendedor_id' not in session or not session['es_admin']:
        return redirect(url_for('login'))
    if request.method == 'POST':
        nombre = request.form['nombre']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO Locales (nombre) VALUES (%s);', (nombre,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('admin_locales'))
    return render_template('agregar_local.html')

@app.route('/admin/eliminar_local/<int:local_id>')
def eliminar_local(local_id):
    if 'vendedor_id' not in session or not session['es_admin']:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM Locales WHERE local_id = %s;', (local_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('admin_locales'))

@app.route('/admin/editar_local/<int:local_id>', methods=['GET', 'POST'])
def editar_local(local_id):
    if 'vendedor_id' not in session or not session['es_admin']:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        nombre = request.form['nombre']
        cur.execute('UPDATE Locales SET nombre = %s WHERE local_id = %s;', (nombre, local_id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('admin_locales'))
    cur.execute('SELECT nombre FROM Locales WHERE local_id = %s;', (local_id,))
    local = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('editar_local.html', local=local, local_id=local_id)

@app.route('/admin/locales')
def admin_locales():
    if 'vendedor_id' not in session or not session['es_admin']:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM Locales;')
    locales = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin_locales.html', locales=locales)

@app.route('/vendedor/productos')
def vendedor_productos():
    if 'vendedor_id' not in session:
        return redirect(url_for('login'))
    locales = get_locales_vendedor(session['vendedor_id'])
    conn = get_db_connection()
    cur = conn.cursor()
    productos_por_tienda = {}
    for local_id in locales:
        cur.execute('''
            SELECT p.nombre, l.nombre, i.cantidad, l.nombre AS nombre_local
            FROM Productos p
            JOIN Inventario i ON p.producto_id = i.producto_id
            JOIN Locales l ON i.local_id = l.local_id
            WHERE l.local_id = %s;
        ''', (local_id,))
        productos = cur.fetchall()
        if productos:
            nombre_local = productos[0][3]  # Obtiene el nombre del local
            productos_por_tienda[nombre_local] = productos
    cur.execute('''
        SELECT p.nombre, l.nombre, i.cantidad
        FROM Productos p
        JOIN Inventario i ON p.producto_id = i.producto_id
        JOIN Locales l ON i.local_id = l.local_id;
    ''')
    todos_los_productos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('vendedor_productos.html', productos_por_tienda=productos_por_tienda, todos_los_productos=todos_los_productos)

@app.route('/vendedor/productos/filtrar')
def vendedor_productos_filtrar():
    if 'vendedor_id' not in session:
        return jsonify([])
    cliente = request.args.get('cliente', '')
    locales = get_locales_vendedor(session['vendedor_id'])
    conn = get_db_connection()
    cur = conn.cursor()
    productos_por_tienda = {}
    for local_id in locales:
        cur.execute('''
            SELECT p.nombre, l.nombre, i.cantidad
            FROM Productos p
            JOIN Inventario i ON p.producto_id = i.producto_id
            JOIN Locales l ON i.local_id = l.local_id
            WHERE l.local_id = %s AND p.nombre ILIKE %s;
        ''', (local_id, '%' + cliente + '%'))
        productos_por_tienda[local_id] = cur.fetchall()
    cur.execute('''
        SELECT p.nombre, l.nombre, i.cantidad
        FROM Productos p
        JOIN Inventario i ON p.producto_id = i.producto_id
        JOIN Locales l ON i.local_id = l.local_id
        WHERE p.nombre ILIKE %s;
    ''', ('%' + cliente + '%',))
    todos_los_productos = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify({'productos_por_tienda': productos_por_tienda, 'todos_los_productos': todos_los_productos})

@app.route('/vendedor/agregar_producto', methods=['GET', 'POST'])
def vendedor_agregar_producto():
    if 'vendedor_id' not in session:
        return redirect(url_for('login'))
    locales = get_locales_vendedor(session['vendedor_id'])
    if not locales:
        return "No tienes locales asignados"
    local_id = locales[0]
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio = request.form['precio']
        cantidad = request.form['cantidad']
        cur.execute('INSERT INTO Productos (nombre, descripcion, precio) VALUES (%s, %s, %s) RETURNING producto_id;', (nombre, descripcion, precio))
        producto_id = cur.fetchone()[0]
        cur.execute('INSERT INTO Inventario (local_id, producto_id, cantidad) VALUES (%s, %s, %s);', (local_id, producto_id, cantidad))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('vendedor_productos'))
    return render_template('vendedor_agregar_producto.html')

def get_locales_vendedor(vendedor_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT local_id
        FROM Vendedores_Locales
        WHERE vendedor_id = %s;
    ''', (vendedor_id,))
    locales = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return locales

@app.route('/')
def lista_locales():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM Locales;')
    locales = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('lista_locales.html', locales=locales)

@app.route('/productos/<int:local_id>')
def lista_productos(local_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT p.producto_id, p.nombre, i.cantidad
        FROM Productos p
        JOIN Inventario i ON p.producto_id = i.producto_id
        WHERE i.local_id = %s;
    ''', (local_id,))
    productos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('lista_productos.html', productos=productos, local_id=local_id)

@app.route('/agregar_producto', methods=['GET', 'POST'])
def agregar_producto():
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio = request.form['precio']
        local_id = request.form['local_id']
        cantidad = request.form['cantidad']
        cur.execute('INSERT INTO Productos (nombre, descripcion, precio) VALUES (%s, %s, %s) RETURNING producto_id;', (nombre, descripcion, precio))
        producto_id = cur.fetchone()[0]
        cur.execute('INSERT INTO Inventario (local_id, producto_id, cantidad) VALUES (%s, %s, %s);', (local_id, producto_id, cantidad))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('lista_productos', local_id=local_id))
    cur.execute('SELECT local_id, nombre FROM Locales;')
    locales = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('agregar_producto.html', locales=locales)

@app.route('/editar_producto/<int:producto_id>/<int:local_id>', methods=['GET', 'POST'])
def editar_producto(producto_id, local_id):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        cantidad = request.form['cantidad']
        cur.execute('UPDATE Inventario SET cantidad = %s WHERE producto_id = %s AND local_id = %s;', (cantidad, producto_id, local_id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('lista_productos', local_id=local_id))
    cur.execute('SELECT nombre, cantidad FROM Productos JOIN Inventario ON Productos.producto_id = Inventario.producto_id WHERE Productos.producto_id = %s AND local_id = %s;', (producto_id, local_id))
    producto = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('editar_producto.html', producto=producto, producto_id=producto_id, local_id=local_id)

@app.route('/buscar_cliente')
def buscar_cliente():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT p.nombre, l.nombre, i.cantidad
        FROM Productos p
        JOIN Inventario i ON p.producto_id = i.producto_id
        JOIN Locales l ON i.local_id = l.local_id;
    ''')
    resultados = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('buscar_cliente.html', resultados=resultados)

@app.route('/buscar_cliente/filtrar')
def buscar_cliente_filtrar():
    cliente = request.args.get('cliente', '')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT p.nombre, l.nombre, i.cantidad
        FROM Productos p
        JOIN Inventario i ON p.producto_id = i.producto_id
        JOIN Locales l ON i.local_id = l.local_id
        WHERE p.nombre ILIKE %s;
    ''', ('%' + cliente + '%',))
    resultados = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(resultados)


@app.route('/eliminar_producto/<int:producto_id>/<int:local_id>')
def eliminar_producto(producto_id, local_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM Inventario WHERE producto_id = %s AND local_id = %s;', (producto_id, local_id))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('lista_productos', local_id=local_id))

if __name__ == '__main__':
    app.run(debug=True)

    