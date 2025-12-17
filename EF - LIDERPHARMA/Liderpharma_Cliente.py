import sys
import sqlite3
from datetime import datetime, timedelta
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QListWidget, QTableWidget, QTableWidgetItem, QMessageBox, QStackedWidget,
    QFormLayout, QComboBox, QFileDialog, QSpinBox, QTextEdit
)

DB_FILE = 'farmacia_shop.db'
LOGO_PATH = '/mnt/data/81ce647f-fb6f-4037-bd4c-8bdbf49ef336.png'
SAMPLE_PRODUCT_IMG = '/mnt/data/b60e5956-6871-469a-89c9-d63a08a1e6ea.png'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()


    c.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            categoria_id INTEGER,
            descripcion TEXT,
            precio REAL,
            stock INTEGER,
            imagen TEXT,
            caducidad TEXT,
            FOREIGN KEY(categoria_id) REFERENCES categorias(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            cliente TEXT,
            documento TEXT,
            direccion TEXT,
            total REAL,
            estado TEXT,
            metodo_entrega TEXT,
            horario_entrega TEXT,
            ruta_optima TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS pedido_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER,
            producto_id INTEGER,
            cantidad INTEGER,
            precio REAL,
            FOREIGN KEY(pedido_id) REFERENCES pedidos(id),
            FOREIGN KEY(producto_id) REFERENCES productos(id)
        )
    ''')
    c.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES ('Medicamentos')")
    c.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES ('Vitaminas y Suplementos')")
    c.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES ('Cuidado de la Piel')")
    c.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES ('Higiene Personal')")
    c.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES ('Salud Infantil')")
    conn.commit()

       
    c.execute('SELECT COUNT(*) FROM productos')
    if c.fetchone()[0] == 0:

        c.execute('SELECT id, nombre FROM categorias')
        catmap = {nombre: id for id, nombre in c.fetchall()}

        def detectar_categoria(nombre):
            n = nombre.upper()
            if any(x in n for x in ["CREMA", "JABON", "ACNOMEL"]):
                return catmap["Cuidado de la Piel"]
            if any(x in n for x in ["ACEITE", "JOHNSON"]):
                return catmap["Higiene Personal"]
            if any(x in n for x in ["AEROCAMARA", "PEDIATR", "LACTANTES", "GOTAS"]):
                return catmap["Salud Infantil"]
            if "FOLICO" in n:
                return catmap["Vitaminas y Suplementos"]
            return catmap["Medicamentos"]

        from datetime import datetime, timedelta
        hoy = datetime.now()
        cad_larga = (hoy + timedelta(days=720)).strftime('%Y-%m-%d')
        cad_media = (hoy + timedelta(days=540)).strftime('%Y-%m-%d')
        cad_corta = (hoy + timedelta(days=365)).strftime('%Y-%m-%d')

        productos_base = [
            ('Paracetamol 500mg Tableta', 'Medicamentos', 'Analgésico y antipirético.', 10.0, cad_media),
            ('Multivitamínico - 30 cápsulas', 'Vitaminas y Suplementos', 'Complejo vitamínico.', 25.0, cad_larga),
            ('Crema Hidratante 100ml', 'Cuidado de la Piel', 'Hidratación profunda.', 15.0, cad_corta),
            ('NOALERGYM 10mg (CETIRIZINA)', 'Medicamentos', 'Antihistamínico.', 31.27, cad_media),
            ('NOALERGYM CB (CETIRIZINA)', 'Medicamentos', 'Cápsulas antihistamínicas.', 35.00, cad_media),
            ('NOALERGYM JBE (CETIRIZINA)', 'Salud Infantil', 'Jarabe antihistamínico.', 11.01, cad_corta),
            ('NODIAL CREMA', 'Cuidado de la Piel', 'Antifúngico y antiinflamatorio.', 5.22, cad_corta),
            ('NOFERTYL', 'Medicamentos', 'Tratamiento hormonal.', 13.67, cad_larga),
        ]

        for nombre, cat, desc, precio, cad in productos_base:
            c.execute(
                '''INSERT INTO productos
                (nombre,categoria_id,descripcion,precio,stock,imagen,caducidad)
                VALUES (?,?,?,?,?,?,?)''',
                (nombre, catmap[cat], desc, precio, 50, SAMPLE_PRODUCT_IMG, cad)
            )

        productos_extra = [
            ("AMP00513","MEDIFARMA","AB-BRONCOL NF 1000 AMPICILINA",21.21),
            ("MED02220","MEGALABS","ABRILAR JARABE",30.54),
            ("OTC00698","ALKO","ACEITE DE ALMENDRAS 30ML",11.04),
            ("OTC00279","JOHNSON","ACEITE JOHNSON 50ML",7.92),
            ("MED01599","GENFAR","ACETILCISTEINA 200mg",28.08),
            ("MED02330","LABOGEN","ACETILCISTEINA 600mg",34.56),
            ("FPL00391","PORTUGAL","ACICLOVIR CREMA 5%",1.50),
            ("FPL00005","FARMINDUSTRIA","ACICLOVIR CREMA 5%",2.10),
            ("MED02090","AVSA","ACIDO FOLICO 0.5mg",7.47),
            ("OTC01036","FARPASA","ACNOMEL JABON CARBON",8.22),
            ("OTC00113","BAXLEY","AEROCAMARA LACTANTES",6.33),
            ("OTC01048","QUIROZ","AEROCAMARA PEDIATRICA",5.73),
            ("MED02133","DUPE","ACTERIL GOTAS SALBUTAMOL",14.11),
        ]

        for code, lab, name, price in productos_extra:
            c.execute(
                '''INSERT INTO productos
                (nombre,categoria_id,descripcion,precio,stock,imagen,caducidad)
                VALUES (?,?,?,?,?,?,?)''',
                (
                    name,
                    detectar_categoria(name),
                    f"Laboratorio: {lab}\nCódigo: {code}",
                    price,
                    20,
                    SAMPLE_PRODUCT_IMG,
                    cad_corta
                )
            )


    conn.commit()





class HomePanel(QWidget):
    def __init__(self, app_window):
        super().__init__()
        self.app_window = app_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.logo_lbl = QLabel()
        pix = QtGui.QPixmap(LOGO_PATH)
        if not pix.isNull():
            self.logo_lbl.setPixmap(pix.scaledToHeight(70, QtCore.Qt.SmoothTransformation))
        self.logo_lbl.setAlignment(QtCore.Qt.AlignLeft)
        top = QHBoxLayout()
        top.addWidget(self.logo_lbl)
        btn_cart = QPushButton('Carrito de Compras')
        btn_cart.clicked.connect(lambda: self.app_window.open_cart())
        top.addStretch()
        top.addWidget(btn_cart)
        layout.addLayout(top)
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit(); self.search_edit.setPlaceholderText('Buscar producto...')
        btn_search = QPushButton('Buscar'); btn_search.clicked.connect(self.on_search)
        search_layout.addWidget(QLabel('Vea nuestras categorías:'))
        self.cat_combo = QComboBox(); self.cat_combo.addItem('-- Todas --',0)
        conn = sqlite3.connect(DB_FILE); c = conn.cursor(); c.execute('SELECT id,nombre FROM categorias');
        for _id,name in c.fetchall():
            self.cat_combo.addItem(name,_id)
        conn.close()
        search_layout.addWidget(self.cat_combo)
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(btn_search)
        layout.addLayout(search_layout)
        filters = QHBoxLayout()
        for label in ['Más Vendidos','Precio: Menor a Mayor','Precio: Mayor a Menor','Alfabético']:
            b = QPushButton(label); b.clicked.connect(lambda _,lbl=label: self.on_filter(lbl))
            filters.addWidget(b)
        layout.addLayout(filters)
        layout.addStretch()
        self.setLayout(layout)

    def on_search(self):
        term = self.search_edit.text().strip()
        cat_id = self.cat_combo.currentData()
        self.app_window.open_products(search=term, category_id=cat_id)

    def on_filter(self, label):
        if label=='Alfabético': order='name'
        elif label=='Precio: Menor a Mayor': order='price_asc'
        elif label=='Precio: Mayor a Menor': order='price_desc'
        else: order=None
        self.app_window.open_products(order=order)


class ProductsPanel(QWidget):
    def __init__(self, app_window):
        super().__init__()
        self.app_window = app_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        header = QHBoxLayout()
        header.addWidget(QLabel('CATEGORÍAS'), alignment=QtCore.Qt.AlignCenter)
        header.addStretch()
        layout.addLayout(header)
        main = QHBoxLayout()
        self.cat_list = QListWidget(); self.cat_list.setMaximumWidth(200)
        self.cat_list.itemClicked.connect(self.on_cat_click)
        main.addWidget(self.cat_list)
        center = QVBoxLayout()
        self.table = QTableWidget(0,5)
        self.table.setHorizontalHeaderLabels(['ID','Producto','Precio','Stock',''])
        self.table.setColumnHidden(0, True)
        self.table.cellDoubleClicked.connect(self.on_product_open)
        center.addWidget(self.table)
        main.addLayout(center,1)
        layout.addLayout(main)
        self.setLayout(layout)
        self.load_categories()
        self.load_products()

    def load_categories(self):
        conn = sqlite3.connect(DB_FILE); c = conn.cursor(); c.execute('SELECT id,nombre FROM categorias');
        self.cat_list.clear(); self.cat_map = {}
        for _id,name in c.fetchall():
            self.cat_list.addItem(name); self.cat_map[name]=_id
        conn.close()

    def load_products(self, category_id=None, search=None, order=None):
        conn = sqlite3.connect(DB_FILE); c = conn.cursor()
        q = 'SELECT id,nombre,precio,stock FROM productos'
        params = []
        clauses = []
        if category_id and category_id!=0:
            clauses.append('categoria_id=?'); params.append(category_id)
        if search:
            clauses.append('nombre LIKE ?'); params.append(f'%{search}%')
        if clauses:
            q += ' WHERE ' + ' AND '.join(clauses)
        if order=='name': q += ' ORDER BY nombre COLLATE NOCASE'
        elif order=='price_asc': q += ' ORDER BY precio ASC'
        elif order=='price_desc': q += ' ORDER BY precio DESC'
        c.execute(q,params)
        rows = c.fetchall(); conn.close()
        self.table.setRowCount(0)
        for r in rows:
            row = self.table.rowCount(); self.table.insertRow(row)
            self.table.setItem(row,0,QTableWidgetItem(str(r[0])))
            self.table.setItem(row,1,QTableWidgetItem(r[1]))
            self.table.setItem(row,2,QTableWidgetItem(f'S/ {r[2]:.2f}'))
            self.table.setItem(row,3,QTableWidgetItem(str(r[3])))
            btn = QPushButton('Ver')
            pid = r[0]
            btn.clicked.connect(lambda _,pid=pid: self.app_window.open_product_detail(pid))
            self.table.setCellWidget(row,4,btn)

    def on_cat_click(self,item):
        catname = item.text(); catid = self.cat_map[catname]
        self.load_products(category_id=catid)

    def on_product_open(self,row,col):
        id_item = self.table.item(row,0)
        if id_item:
            try:
                pid = int(id_item.text())
                self.app_window.open_product_detail(pid)
            except:
                pass


class ProductDetailPanel(QWidget):
    def __init__(self, app_window):
        super().__init__()
        self.app_window = app_window
        self.prod_id = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.name_lbl = QLabel("Nombre del Producto")
        self.name_lbl.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.desc_lbl = QLabel("Descripción del Producto")
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setStyleSheet("font-size: 14px;")

        self.price_lbl = QLabel("Precio: S/ 0.00")
        self.price_lbl.setStyleSheet("font-size: 16px; color: green;")

        self.stock_lbl = QLabel("Stock: -")
        self.stock_lbl.setStyleSheet("font-size: 14px; color: #444;")

        self.exp_lbl = QLabel("Fecha de Caducidad: --/--/----")
        self.exp_lbl.setStyleSheet("font-size: 14px; color: #AA0000;")

        opts = QHBoxLayout()
        self.delivery_combo = QComboBox(); self.delivery_combo.addItems(['Envío a Domicilio','Retiro en Droguería'])
        self.qty_spin = QSpinBox(); self.qty_spin.setRange(1,1000); self.qty_spin.setValue(1)
        opts.addWidget(self.delivery_combo); opts.addWidget(QLabel('Cantidad:')); opts.addWidget(self.qty_spin)

        btn_add = QPushButton('Agregar al Carrito')
        btn_add.setStyleSheet("padding: 8px; background-color: #0078d7; color: white;")
        btn_add.clicked.connect(self.add_to_cart)

        layout.addWidget(self.name_lbl)
        layout.addWidget(self.desc_lbl)
        layout.addWidget(self.price_lbl)
        layout.addWidget(self.stock_lbl)
        layout.addWidget(self.exp_lbl)
        layout.addLayout(opts)
        layout.addWidget(btn_add)
        layout.addStretch()

    def load_product(self, product_id):
        self.prod_id = product_id
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()


        try:
            c.execute("SELECT id,nombre,descripcion,precio,stock,imagen,caducidad FROM productos WHERE id=?", (product_id,))
            row = c.fetchone()
        except Exception:
            c.execute("SELECT id,nombre,descripcion,precio,stock,imagen FROM productos WHERE id=?", (product_id,))
            row = c.fetchone()

        conn.close()

        if not row:
            return

        if len(row) >= 7:
            _, nombre, desc, precio, stock, imagen, cad = row
        else:
            _, nombre, desc, precio, stock, imagen = row
            cad = None

        self.name_lbl.setText(f'<b>{nombre}</b>')
        self.desc_lbl.setText(desc if desc else '')
        try:
            self.price_lbl.setText(f'S/ {float(precio):.2f}')
        except:
            self.price_lbl.setText(f'S/ {precio}')
        self.stock_lbl.setText(f'Disponibilidad: {stock}')
        self.exp_lbl.setText(f'Caducidad: {cad if cad else "No registrada"}')

        pix = QtGui.QPixmap(imagen) if imagen else QtGui.QPixmap()
        if not pix.isNull():
            pass

    def add_to_cart(self):
        if not self.prod_id:
            QMessageBox.warning(self, 'Error', 'No hay producto seleccionado')
            return

        qty = self.qty_spin.value()
        delivery = self.delivery_combo.currentText()
        self.app_window.cart_add(self.prod_id, qty, delivery)
        QMessageBox.information(self, 'Carrito', 'Producto agregado al carrito')


class CartPanel(QWidget):
    def __init__(self, app_window):
        super().__init__()
        self.app_window = app_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        header = QHBoxLayout(); header.addWidget(QLabel('<b>CARRITO DE COMPRAS</b>')); header.addStretch()
        layout.addLayout(header)
        self.table = QTableWidget(0,5)
        self.table.setHorizontalHeaderLabels(['#','Producto','Cantidad','Método de Entrega','SubTotal'])
        layout.addWidget(self.table)
        btns = QHBoxLayout()
        btn_edit = QPushButton('Editar Cantidad'); btn_edit.clicked.connect(self.edit_quantity)
        btn_remove = QPushButton('Eliminar'); btn_remove.clicked.connect(self.remove_item)
        btn_checkout = QPushButton('Proceder al Pago'); btn_checkout.clicked.connect(lambda: self.app_window.open_checkout())
        btns.addWidget(btn_edit); btns.addWidget(btn_remove); btns.addStretch(); btns.addWidget(btn_checkout)
        layout.addLayout(btns)
        self.total_lbl = QLabel('Total: S/ 0.00')
        layout.addWidget(self.total_lbl, alignment=QtCore.Qt.AlignRight)
        self.setLayout(layout)

    def refresh(self):
        cart = self.app_window.cart
        self.table.setRowCount(0)
        total = 0.0
        conn = sqlite3.connect(DB_FILE); c = conn.cursor()
        for i,item in enumerate(cart, start=1):
            pid = item['product_id']
            c.execute('SELECT nombre,precio FROM productos WHERE id=?',(pid,)); r=c.fetchone()
            if not r: continue
            nombre,precio = r
            subtotal = precio*item['qty']
            total += subtotal
            row = self.table.rowCount(); self.table.insertRow(row)
            self.table.setItem(row,0,QTableWidgetItem(str(i)))
            self.table.setItem(row,1,QTableWidgetItem(nombre))
            self.table.setItem(row,2,QTableWidgetItem(str(item['qty'])))
            self.table.setItem(row,3,QTableWidgetItem(item.get('delivery','')))
            self.table.setItem(row,4,QTableWidgetItem(f'S/ {subtotal:.2f}'))
        conn.close()
        self.total_lbl.setText(f'Total: S/ {total:.2f}')

    def edit_quantity(self):
        r = self.table.currentRow()
        if r<0: return
        qty,ok = QtWidgets.QInputDialog.getInt(self,'Editar Cantidad','Nueva cantidad:',int(self.table.item(r,2).text()),1,1000)
        if ok:
            idx = int(self.table.item(r,0).text())-1
            self.app_window.cart[idx]['qty'] = qty
            self.refresh()

    def remove_item(self):
        r = self.table.currentRow()
        if r<0: return
        idx = int(self.table.item(r,0).text())-1
        del self.app_window.cart[idx]
        self.refresh()


class CheckoutPanel(QWidget):
    def __init__(self, app_window):
        super().__init__()
        self.app_window = app_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel('<b>DATOS DEL PAGO</b>'))
        form = QFormLayout()
        self.name = QLineEdit(); self.doc = QLineEdit(); self.address = QLineEdit()
        self.method = QComboBox(); self.method.addItems(['Tarjeta de crédito','Transferencia','Pago en tienda'])
        self.card_number = QLineEdit(); self.card_holder = QLineEdit(); self.amount_lbl = QLabel('S/ 0.00')
        form.addRow('Nombre:', self.name)
        form.addRow('Documento:', self.doc)
        form.addRow('Dirección de entrega:', self.address)
        form.addRow('Método de pago:', self.method)
        form.addRow('Número de tarjeta:', self.card_number)
        form.addRow('Titular:', self.card_holder)
        layout.addLayout(form)
        btn_pay = QPushButton('Pagar ahora'); btn_pay.clicked.connect(self.process_payment)
        layout.addWidget(self.amount_lbl, alignment=QtCore.Qt.AlignRight)
        layout.addWidget(btn_pay, alignment=QtCore.Qt.AlignCenter)
        self.setLayout(layout)

    def load_amount(self):
        total = 0.0
        conn = sqlite3.connect(DB_FILE); c = conn.cursor()
        for item in self.app_window.cart:
            c.execute('SELECT precio FROM productos WHERE id=?',(item['product_id'],)); r=c.fetchone()
            if r: total += r[0]*item['qty']
        conn.close()
        self.amount_lbl.setText(f'S/ {total:.2f}')

    def process_payment(self):
        if not self.app_window.cart:
            QMessageBox.warning(self, 'Carrito vacío', 'Agrega productos antes de pagar')
            return
        if not self.name.text().strip() or not self.doc.text().strip():
            QMessageBox.warning(self,'Datos faltantes','Complete nombre y documento')
            return

        total = 0
        conn = sqlite3.connect(DB_FILE); c = conn.cursor()
        for item in self.app_window.cart:
            c.execute("SELECT precio FROM productos WHERE id=?", (item['product_id'],))
            r = c.fetchone()
            if r:
                total += r[0]*item['qty']

        entrega = self.method.currentText()
        horario_entrega, ok = QtWidgets.QInputDialog.getText(
            self, "Horario de entrega", "Indique horario :"
        )
        if not ok:
            conn.close()
            return

        ruta = "Ruta optimizada generada automáticamente"

        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        c.execute("""
            INSERT INTO pedidos (fecha,cliente,documento,direccion,total,estado,
                                 metodo_entrega,horario_entrega,ruta_optima)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            fecha,
            self.name.text(),
            self.doc.text(),
            self.address.text(),
            total,
            "Pendiente",    
            entrega,
            horario_entrega,
            ruta
        ))

        pedido_id = c.lastrowid

        for item in self.app_window.cart:
            c.execute("SELECT precio FROM productos WHERE id=?", (item['product_id'],))
            price = c.fetchone()[0]
            c.execute("""
                INSERT INTO pedido_items (pedido_id,producto_id,cantidad,precio)
                VALUES (?,?,?,?)
            """, (pedido_id, item['product_id'], item['qty'], price))

            c.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (item['qty'], item['product_id']))

        conn.commit()
        conn.close()

        QMessageBox.information(self, 'Pedido creado',
                                f"Pedido #{pedido_id} registrado correctamente.\n"
                                f"Estado: Pendiente\n"
                                f"Ruta óptima asignada.")

        self.app_window.cart.clear()
        self.app_window.open_home()


class OrdersPanel(QWidget):
    def __init__(self, app_window):
        super().__init__()
        self.app_window = app_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>LISTA DE PEDIDOS</b>"))

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "ID","Cliente","Total","Estado","Entrega","Horario"
        ])
        layout.addWidget(self.table)

        btn_refresh = QPushButton("Actualizar")
        btn_refresh.clicked.connect(self.load_orders)
        layout.addWidget(btn_refresh)

        self.setLayout(layout)

    def load_orders(self):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT id,cliente,total,estado,metodo_entrega,horario_entrega FROM pedidos ORDER BY id DESC")
        rows = c.fetchall()
        conn.close()

        self.table.setRowCount(0)
        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col,value in enumerate(r):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Sistema de Inventario - Farmacia / Tienda')
        self.resize(1000,700)
        init_db()
        self.cart = [] 
        self.stack = QStackedWidget(); self.setCentralWidget(self.stack)
        self.home = HomePanel(self)
        self.products = ProductsPanel(self)
        self.detail = ProductDetailPanel(self)
        self.cart_panel = CartPanel(self)
        self.checkout = CheckoutPanel(self)
        self.orders = OrdersPanel(self)

        self.stack.addWidget(self.home)
        self.stack.addWidget(self.products)
        self.stack.addWidget(self.detail)
        self.stack.addWidget(self.cart_panel)
        self.stack.addWidget(self.checkout)
        self.stack.addWidget(self.orders)

        menubar = self.menuBar(); menu = menubar.addMenu('Navegar')
        menu.addAction('Inicio', lambda: self.open_home())
        menu.addAction('Productos', lambda: self.open_products())
        menu.addAction('Carrito', lambda: self.open_cart())
        menu.addAction('Pedidos', lambda: self.open_orders())

    def open_home(self):
        self.stack.setCurrentWidget(self.home)

    def open_products(self, search=None, category_id=None, order=None):
        self.products.load_products(category_id=category_id, search=search, order=order)
        self.stack.setCurrentWidget(self.products)

    def open_product_detail(self, product_id):
        self.detail.load_product(product_id)
        self.stack.setCurrentWidget(self.detail)

    def cart_add(self, product_id, qty, delivery):
        for it in self.cart:
            if it['product_id']==product_id and it.get('delivery','')==delivery:
                it['qty'] += qty
                break
        else:
            self.cart.append({'product_id':product_id,'qty':qty,'delivery':delivery})

    def open_cart(self):
        self.cart_panel.refresh()
        self.stack.setCurrentWidget(self.cart_panel)

    def open_checkout(self):
        self.checkout.load_amount()
        self.stack.setCurrentWidget(self.checkout)

    def open_orders(self):
        self.orders.load_orders()
        self.stack.setCurrentWidget(self.orders)

if __name__=='__main__':
    app = QApplication(sys.argv)
    mw = MainWindow(); mw.show()
    sys.exit(app.exec_())

