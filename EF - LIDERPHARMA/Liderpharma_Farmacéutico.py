import sys
import sqlite3
import csv
from datetime import datetime
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QListWidget, QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
    QFormLayout, QDateEdit, QComboBox, QTextEdit, QFileDialog, QSpinBox
)

DB_FILE = 'farmacia.db'

# ---------- Base de datos: inicialización simple ----------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # usuarios
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                 username TEXT PRIMARY KEY, password TEXT, rol TEXT)''')
    c.execute("INSERT OR IGNORE INTO usuarios(username,password,rol) VALUES('admin','admin','farmaceutico')")
    # categorias
    c.execute('''CREATE TABLE IF NOT EXISTS categorias (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE)''')
    for cat in ['Medicamentos','Vitaminas','Equipos Médicos','Suplementos','Otros']:
        c.execute('INSERT OR IGNORE INTO categorias(nombre) VALUES(?)',(cat,))
    # productos
    c.execute('''CREATE TABLE IF NOT EXISTS productos (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, categoria_id INTEGER,
                 precio REAL DEFAULT 0, FOREIGN KEY(categoria_id) REFERENCES categorias(id))''')
    # stock por lote / vencimiento
    c.execute('''CREATE TABLE IF NOT EXISTS stock (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, producto_id INTEGER, lote TEXT,
                 cantidad INTEGER, fecha_vencimiento TEXT, FOREIGN KEY(producto_id) REFERENCES productos(id))''')
    # clientes
    c.execute('''CREATE TABLE IF NOT EXISTS clientes (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, tipo_doc TEXT, numero TEXT, nombre TEXT,
                 direccion_factura TEXT, direccion_despacho TEXT)''')
    # pedidos
    c.execute('''CREATE TABLE IF NOT EXISTS pedidos (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER, fecha TEXT,
                 condicion_pago TEXT, tipo_documento TEXT, total REAL, FOREIGN KEY(cliente_id) REFERENCES clientes(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS pedido_items (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, pedido_id INTEGER, producto_id INTEGER,
                 lote TEXT, vencimiento TEXT, cantidad INTEGER, precio_unit REAL,
                 FOREIGN KEY(pedido_id) REFERENCES pedidos(id), FOREIGN KEY(producto_id) REFERENCES productos(id))''')
    conn.commit()
    conn.close()

# ---------- Login Widget ----------
class LoginWidget(QWidget):
    def __init__(self, stack):
        super().__init__()
        self.stack = stack
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        title = QLabel('SOMOS LIDER PHARMA S.A.')
        title.setAlignment(QtCore.Qt.AlignCenter)
        user_lbl = QLabel('Usuario:')
        self.user_edit = QLineEdit()
        pass_lbl = QLabel('Contraseña:')
        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.Password)
        btn = QPushButton('Ingresar')
        btn.clicked.connect(self.try_login)
        layout.addWidget(title)
        layout.addSpacing(10)
        form = QFormLayout()
        form.addRow(user_lbl, self.user_edit)
        form.addRow(pass_lbl, self.pass_edit)
        layout.addLayout(form)
        layout.addWidget(btn, alignment=QtCore.Qt.AlignCenter)
        self.setLayout(layout)

    def try_login(self):
        username = self.user_edit.text().strip()
        password = self.pass_edit.text().strip()
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT rol FROM usuarios WHERE username=? AND password=?',(username,password))
        row = c.fetchone()
        conn.close()
        if row:
            # abrir panel principal
            self.stack.setCurrentIndex(1)
        else:
            QMessageBox.warning(self, 'Error', 'Usuario o contraseña inválidos')

# ---------- Consulta de Criterios de Selección (Diálogo) ----------
class ConsultaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Consulta Criterios de Selección')
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        form.addRow('Superior / Igual:', self.date_from)
        form.addRow('Menor o Igual:', self.date_to)
        layout.addLayout(form)
        btns = QHBoxLayout()
        ok = QPushButton('Ok')
        cancel = QPushButton('Cancelar')
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        layout.addLayout(btns)
        self.setLayout(layout)

# ---------- Panel de Farmacéutico ----------
class InventarioPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_categorias()
        self.load_productos()

    def setup_ui(self):
        main = QVBoxLayout()
        header = QLabel('Panel del Inventario Farmacéutico')
        header.setAlignment(QtCore.Qt.AlignCenter)
        main.addWidget(header)
        content = QHBoxLayout()
        # lista de categorias
        left = QVBoxLayout()
        left.addWidget(QLabel('Categorías'))
        self.cat_list = QListWidget()
        self.cat_list.clicked.connect(self.on_categoria_selected)
        left.addWidget(self.cat_list)
        content.addLayout(left,1)
        # tabla productos
        center = QVBoxLayout()
        center.addWidget(QLabel('Disponibilidad de Productos'))
        self.table = QTableWidget(0,6)
        self.table.setHorizontalHeaderLabels(['ID','Producto','Categoría','Stock','Fecha de Caducidad','Estado'])
        center.addWidget(self.table)
        content.addLayout(center,3)
        # acciones rápidas
        right = QVBoxLayout()
        right.addWidget(QLabel('Acciones Rápidas'))
        btn_verificar = QPushButton('Verificar Stock')
        btn_verificar.clicked.connect(self.verificar_stock)
        btn_actualizar = QPushButton('Actualizar mi Inventario')
        btn_actualizar.clicked.connect(self.actualizar_inventario)
        btn_agregar_fecha = QPushButton('Agregar Fecha de Caducidad')
        btn_agregar_fecha.clicked.connect(self.agregar_fecha_cad)
        btn_export = QPushButton('Generar Reporte CSV')
        btn_export.clicked.connect(self.export_csv)
        right.addWidget(btn_verificar)
        right.addWidget(btn_actualizar)
        right.addWidget(btn_agregar_fecha)
        right.addWidget(btn_export)
        right.addStretch()
        content.addLayout(right,1)
        main.addLayout(content)
        self.setLayout(main)

    def load_categorias(self):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT id,nombre FROM categorias ORDER BY nombre')
        self.categorias = c.fetchall()
        conn.close()
        self.cat_list.clear()
        for _id,nombre in self.categorias:
            self.cat_list.addItem(nombre)

    def load_productos(self, categoria_id=None):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        if categoria_id:
            c.execute('''SELECT p.id,p.nombre,c.nombre,IFNULL(SUM(s.cantidad),0) as stock,
                         IFNULL(MIN(s.fecha_vencimiento), '')
                         FROM productos p
                         LEFT JOIN categorias c ON p.categoria_id=c.id
                         LEFT JOIN stock s ON s.producto_id=p.id
                         WHERE p.categoria_id=?
                         GROUP BY p.id''',(categoria_id,))
        else:
            c.execute('''SELECT p.id,p.nombre,c.nombre,IFNULL(SUM(s.cantidad),0) as stock,
                         IFNULL(MIN(s.fecha_vencimiento), '')
                         FROM productos p
                         LEFT JOIN categorias c ON p.categoria_id=c.id
                         LEFT JOIN stock s ON s.producto_id=p.id
                         GROUP BY p.id''')
        rows = c.fetchall()
        conn.close()
        self.table.setRowCount(0)
        for r in rows:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            id_item = QTableWidgetItem(str(r[0]))
            self.table.setItem(row_pos,0,id_item)
            self.table.setItem(row_pos,1,QTableWidgetItem(r[1]))
            self.table.setItem(row_pos,2,QTableWidgetItem(r[2]))
            self.table.setItem(row_pos,3,QTableWidgetItem(str(r[3])))
            self.table.setItem(row_pos,4,QTableWidgetItem(r[4] if r[4] else ''))
            estado = 'OK' if r[3]>0 else 'AGOTADO'
            self.table.setItem(row_pos,5,QTableWidgetItem(estado))

    def on_categoria_selected(self, idx):
        row = idx.row()
        cat_id = self.categorias[row][0]
        self.load_productos(categoria_id=cat_id)

    def verificar_stock(self):
        # muestra simple de productos con stock <= 0 o vencidos
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        hoy = datetime.today().strftime('%Y-%m-%d')
        c.execute('''SELECT p.nombre, IFNULL(SUM(s.cantidad),0) as total, MIN(s.fecha_vencimiento)
                     FROM productos p
                     LEFT JOIN stock s ON s.producto_id=p.id
                     GROUP BY p.id HAVING total<=0 OR MIN(s.fecha_vencimiento)<?''',(hoy,))
        rows = c.fetchall()
        conn.close()
        if not rows:
            QMessageBox.information(self,'Verificar Stock','No se encontraron problemas de stock ni vencimientos próximos')
            return
        txt = '\n'.join([f'{r[0]} - Stock: {r[1]} - Vence: {r[2]}' for r in rows])
        QMessageBox.warning(self,'Problemas detectados',txt)

    def actualizar_inventario(self):
        # diálogo simple para añadir producto y stock
        dlg = QDialog(self)
        dlg.setWindowTitle('Actualizar Inventario')
        layout = QFormLayout()
        nombre = QLineEdit()
        categoria = QComboBox()
        for _id,nombre_cat in self.categorias:
            categoria.addItem(nombre_cat,str(_id))
        lote = QLineEdit()
        cantidad = QSpinBox(); cantidad.setRange(0,100000)
        venc = QDateEdit(); venc.setCalendarPopup(True)
        precio = QLineEdit(); precio.setText('0')
        layout.addRow('Nombre producto:', nombre)
        layout.addRow('Categoría:', categoria)
        layout.addRow('Lote:', lote)
        layout.addRow('Cantidad:', cantidad)
        layout.addRow('Fecha Vencimiento:', venc)
        layout.addRow('Precio unitario:', precio)
        btns = QHBoxLayout()
        ok = QPushButton('Guardar'); cancel = QPushButton('Cancelar')
        ok.clicked.connect(dlg.accept); cancel.clicked.connect(dlg.reject)
        btns.addWidget(ok); btns.addWidget(cancel)
        layout.addRow(btns)
        dlg.setLayout(layout)
        if dlg.exec_()==QDialog.Accepted:
            pname = nombre.text().strip()
            cat_id = int(categoria.currentData())
            lote_t = lote.text().strip()
            cantidad_v = cantidad.value()
            venc_f = venc.date().toString('yyyy-MM-dd')
            precio_v = float(precio.text() or 0)
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            # insertar producto si no existe
            c.execute('SELECT id FROM productos WHERE nombre=?',(pname,))
            row = c.fetchone()
            if row:
                pid = row[0]
                c.execute('UPDATE productos SET categoria_id=?, precio=? WHERE id=?',(cat_id, precio_v, pid))
            else:
                c.execute('INSERT INTO productos(nombre,categoria_id,precio) VALUES(?,?,?)',(pname,cat_id,precio_v))
                pid = c.lastrowid
            # insertar stock
            c.execute('INSERT INTO stock(producto_id,lote,cantidad,fecha_vencimiento) VALUES(?,?,?,?)',
                      (pid,lote_t,cantidad_v,venc_f))
            conn.commit()
            conn.close()
            QMessageBox.information(self,'Inventario','Producto y stock actualizados')
            self.load_productos()

    def agregar_fecha_cad(self):
        # permitir asignar/editar fecha de caducidad de una fila seleccionada
        sel = self.table.currentRow()
        if sel<0:
            QMessageBox.warning(self,'Seleccionar','Seleccione un producto de la tabla')
            return
        prod_id = int(self.table.item(sel,0).text())
        dlg = QDialog(self)
        dlg.setWindowTitle('Agregar/Editar Fecha de Caducidad')
        form = QFormLayout()
        lote = QLineEdit(); fecha = QDateEdit(); fecha.setCalendarPopup(True)
        cantidad = QSpinBox(); cantidad.setRange(0,100000)
        form.addRow('Lote:', lote)
        form.addRow('Fecha Vencimiento:', fecha)
        form.addRow('Cantidad para este lote:', cantidad)
        btns = QHBoxLayout()
        ok = QPushButton('Guardar'); cancel = QPushButton('Cancelar')
        ok.clicked.connect(dlg.accept); cancel.clicked.connect(dlg.reject)
        btns.addWidget(ok); btns.addWidget(cancel)
        form.addRow(btns)
        dlg.setLayout(form)
        if dlg.exec_()==QDialog.Accepted:
            lote_t = lote.text().strip(); f = fecha.date().toString('yyyy-MM-dd'); cant = cantidad.value()
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('INSERT INTO stock(producto_id,lote,cantidad,fecha_vencimiento) VALUES(?,?,?,?)',
                      (prod_id,lote_t,cant,f))
            conn.commit(); conn.close()
            QMessageBox.information(self,'OK','Fecha de caducidad y lote agregados')
            self.load_productos()

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self,'Guardar reporte','reporte_inventario.csv','CSV Files (*.csv)')
        if not path:
            return
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''SELECT p.nombre, c.nombre, IFNULL(SUM(s.cantidad),0) as stock, MIN(s.fecha_vencimiento)
                     FROM productos p
                     LEFT JOIN categorias c ON p.categoria_id=c.id
                     LEFT JOIN stock s ON s.producto_id=p.id
                     GROUP BY p.id''')
        rows = c.fetchall(); conn.close()
        with open(path,'w',newline='',encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Producto','Categoria','Stock','Proximo Vencimiento'])
            for r in rows:
                writer.writerow(r)
        QMessageBox.information(self,'Exportar','Reporte CSV generado')

# ---------- Panel de Despacho (Control de Pedidos) ----------
class DespachoPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        main = QVBoxLayout()
        top = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(QLabel('Resumen'))
        left.addWidget(QLabel('Módulos'))
        # campos cliente
        form = QFormLayout()
        self.cliente_tipo = QComboBox(); self.cliente_tipo.addItems(['DNI','RUC','Otro'])
        self.cliente_num = QLineEdit(); self.cliente_nombre = QLineEdit()
        self.dir_fact = QLineEdit(); self.dir_desp = QLineEdit()
        form.addRow('Tipo doc:', self.cliente_tipo)
        form.addRow('Número:', self.cliente_num)
        form.addRow('Nombre / Razon Social:', self.cliente_nombre)
        form.addRow('Dirección de Factura:', self.dir_fact)
        form.addRow('Dirección de Despacho:', self.dir_desp)
        left.addLayout(form)
        top.addLayout(left,2)
        right = QVBoxLayout()
        self.cond_pago = QComboBox(); self.cond_pago.addItems(['Contado','30% Adelanto','Crédito 30 días'])
        self.tipo_doc = QComboBox(); self.tipo_doc.addItems(['Boleta','Factura','Remito'])
        self.cnt_prod = QSpinBox(); self.cnt_prod.setRange(0,1000)
        right.addWidget(QLabel('Condición de Pago:'))
        right.addWidget(self.cond_pago)
        right.addWidget(QLabel('Tipo de Documento:'))
        right.addWidget(self.tipo_doc)
        right.addWidget(QLabel('Cnt. de Producto'))
        right.addWidget(self.cnt_prod)
        top.addLayout(right,1)
        main.addLayout(top)
        # tabla de composicion de pedido
        self.table = QTableWidget(0,9)
        self.table.setHorizontalHeaderLabels(['#','Producto','Lab','Almacén','Lote','Vencimiento','Cnt. Entero','Cnt. Fracción','Precio x Unidad'])
        main.addWidget(self.table)
        btns = QHBoxLayout()
        btn_add = QPushButton('Agregar fila'); btn_add.clicked.connect(self.add_row)
        btn_save = QPushButton('Guardar Pedido'); btn_save.clicked.connect(self.save_order)
        btn_myorders = QPushButton('Mis Pedidos'); btns.addWidget(btn_add); btns.addWidget(btn_save); btns.addWidget(btn_myorders)
        main.addLayout(btns)
        self.setLayout(main)

    def add_row(self):
        r = self.table.rowCount(); self.table.insertRow(r)
        # celdas editables
        for c in range(1,9):
            self.table.setItem(r,c,QTableWidgetItem(''))
        self.table.setItem(r,0,QTableWidgetItem(str(r+1)))

    def save_order(self):
        # simple: guardar cliente, pedido y items
        tipo = self.cliente_tipo.currentText(); numero = self.cliente_num.text().strip(); nombre = self.cliente_nombre.text().strip()
        if not numero or not nombre:
            QMessageBox.warning(self,'Cliente','Complete número y nombre del cliente')
            return
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('INSERT INTO clientes(tipo_doc,numero,nombre,direccion_factura,direccion_despacho) VALUES(?,?,?,?,?)',
                  (tipo,numero,nombre,self.dir_fact.text(),self.dir_desp.text()))
        cliente_id = c.lastrowid
        fecha = datetime.now().strftime('%Y-%m-%d')
        condicion = self.cond_pago.currentText(); tipo_doc = self.tipo_doc.currentText()
        c.execute('INSERT INTO pedidos(cliente_id,fecha,condicion_pago,tipo_documento,total) VALUES(?,?,?,?,?)',
                  (cliente_id,fecha,condicion, tipo_doc, 0.0))
        pedido_id = c.lastrowid
        total = 0.0
        for r in range(self.table.rowCount()):
            prod = self.table.item(r,1).text() if self.table.item(r,1) else ''
            if not prod: continue
            lote = self.table.item(r,4).text() if self.table.item(r,4) else ''
            venc = self.table.item(r,5).text() if self.table.item(r,5) else ''
            try:
                cantidad = int(self.table.item(r,6).text()) if self.table.item(r,6) else 0
            except:
                cantidad = 0
            try:
                precio = float(self.table.item(r,8).text()) if self.table.item(r,8) else 0.0
            except:
                precio = 0.0
            # buscar o crear producto
            c.execute('SELECT id FROM productos WHERE nombre=?',(prod,))
            pr = c.fetchone()
            if pr:
                prod_id = pr[0]
            else:
                c.execute('INSERT INTO productos(nombre,categoria_id,precio) VALUES(?,?,?)',(prod,1,precio))
                prod_id = c.lastrowid
            c.execute('INSERT INTO pedido_items(pedido_id,producto_id,lote,vencimiento,cantidad,precio_unit) VALUES(?,?,?,?,?,?)',
                      (pedido_id,prod_id,lote,venc,cantidad,precio))
            total += cantidad*precio
        c.execute('UPDATE pedidos SET total=? WHERE id=?',(total,pedido_id))
        conn.commit(); conn.close()
        QMessageBox.information(self,'Pedido','Pedido guardado con éxito')
        # limpiar
        self.table.setRowCount(0)

# ---------- Ventana Principal con StackedWidget ----------
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Sistema de Inventario - Farmacia')
        self.resize(900,600)
        self.stack = QStackedWidget()
        self.login = LoginWidget(self.stack)
        self.inventario = InventarioPanel()
        self.despacho = DespachoPanel()
        self.stack.addWidget(self.login)
        self.stack.addWidget(self.inventario)
        self.stack.addWidget(self.despacho)
        # menú superior para navegar
        menubar = self.menuBar()
        archivo = menubar.addMenu('Archivo')
        inv_menu = menubar.addMenu('Inventario')
        ayuda = menubar.addMenu('Ayuda')
        # acciones
        act_inventario = QtWidgets.QAction('Panel Inventario',self)
        act_inventario.triggered.connect(lambda: self.stack.setCurrentWidget(self.inventario))
        act_despacho = QtWidgets.QAction('Control de Despacho',self)
        act_despacho.triggered.connect(lambda: self.stack.setCurrentWidget(self.despacho))
        inv_menu.addAction(act_inventario); inv_menu.addAction(act_despacho)
        act_consulta = QtWidgets.QAction('Consulta por Fechas',self)
        act_consulta.triggered.connect(self.open_consulta)
        archivo.addAction(act_consulta)
        self.setCentralWidget(self.stack)

    def open_consulta(self):
        dlg = ConsultaDialog(self)
        if dlg.exec_()==QDialog.Accepted:
            dfrom = dlg.date_from.date().toString('yyyy-MM-dd')
            dto = dlg.date_to.date().toString('yyyy-MM-dd')
            # ejemplo: mostrar pedidos en rango de fechas
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('SELECT p.id, c.nombre, p.fecha, p.total FROM pedidos p JOIN clientes c ON p.cliente_id=c.id WHERE p.fecha BETWEEN ? AND ?',(dfrom,dto))
            rows = c.fetchall(); conn.close()
            if not rows:
                QMessageBox.information(self,'Consulta','No se encontraron registros en ese rango')
                return
            txt = '\n'.join([f'Pedido {r[0]} - Cliente: {r[1]} - Fecha: {r[2]} - Total: {r[3]}' for r in rows])
            QMessageBox.information(self,'Resultados',txt)

# ---------- Ejecutar aplicación ----------
if __name__ == '__main__':
    init_db()
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())

