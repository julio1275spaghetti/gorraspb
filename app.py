from flask import Flask, render_template, request, redirect, url_for, session, make_response
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import qrcode
import io
import base64

app = Flask(__name__)
app.secret_key = "gorras_secret"

USUARIOS = {"admin": "1234"}
IVA = 0.12

CATALOGO = [
    {"id": 1, "nombre": "Gorra Ranch Life",                         "precio": 275.00, "imagen": "imagen/gorra1.jpg", "stock": 10, "video": "videos/gorra1.mp4", "descripcion": "Inspiración rústica y moderna. Con tonos tierra y textura de yute, esta gorra es el accesorio ideal para los amantes del estilo outdoor."},
    {"id": 2, "nombre": "Gorra New Era Versión Yankees",            "precio": 360.00, "imagen": "imagen/gorra2.jpg", "stock": 10, "video": "videos/gorra2.mp4", "descripcion": "La corona del streetwear. Un diseño sobrio en color negro con el emblemático logo bordado en blanco, ideal para quienes buscan un look clásico y versátil."},
    {"id": 3, "nombre": "Gorra New Era Versión Los Angeles",        "precio": 450.00, "imagen": "imagen/gorra3.jpg", "stock": 10, "video": "videos/gorra3.mp4", "descripcion": "Celebra la historia con esta edición especial. Con un parche conmemorativo lateral, es la pieza perfecta para coleccionistas y fanáticos de los Dodgers."},
    {"id": 4, "nombre": "Gorra Goorin Bros",                        "precio": 650.00, "imagen": "imagen/gorra4.jpg", "stock": 10, "video": "videos/gorra4.mp4", "descripcion": "Estilo trucker auténtico. Con su icónico parche de gorila y malla transpirable, es la gorra definitiva para un estilo relajado y con personalidad."},
    {"id": 5, "nombre": "Gorra Adidas colaboración NBA CHAMPS",     "precio": 400.00, "imagen": "imagen/gorra5.jpg", "stock": 10, "video": "videos/gorra5.mp4", "descripcion": "Un tributo a los campeones. Con bordados de alta densidad que celebran la gloria del baloncesto, combinando la calidad de Adidas con el espíritu NBA."},
    {"id": 6, "nombre": "Gorra Puma colaboración Ferrari",          "precio": 350.00, "imagen": "imagen/gorra6.jpg", "stock": 10, "video": "videos/gorra6.mp4", "descripcion": "Siente la adrenalina de la Fórmula 1. Diseño aerodinámico en color negro con el legendario Scudetto de Ferrari al frente."},
    {"id": 7, "nombre": "Gorra 31 Hats x El Mago",                  "precio": 1200.00, "imagen": "imagen/gorra7.jpg", "stock": 10, "video": "videos/gorra7.mp4", "descripcion": "La joya de la corona. Una colaboración de lujo con detalles en pedrería roja y bordados artesanales para quienes no temen ser el centro de atención."},
    {"id": 8, "nombre": "Gorra Adidas Clásica",                     "precio": 300.00, "imagen": "imagen/gorra8.jpg", "stock": 10, "video": "videos/gorra8.mp4", "descripcion": "El balance perfecto entre funcionalidad y diseño. Con gráficos retro en rojo y blanco, es una pieza esencial para cualquier outfit deportivo."},
    {"id": 9, "nombre": "Gorra New Era Black MBL",                  "precio": 299.00, "imagen": "imagen/gorra9.jpg", "stock": 10, "video": "videos/gorra9.mp4", "descripcion": "Elegancia deportiva en negro y dorado. El contraste del logo bordado en oro sobre el fondo oscuro ofrece un toque de distinción único."},
]

carrito = []

def generar_qr(url):
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode()

@app.route('/')
def inicio():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    mensaje = ""
    if request.method == 'POST':
        usuario = request.form['usuario']
        contraseña = request.form['contraseña']
        if usuario in USUARIOS and USUARIOS[usuario] == contraseña:
            session['usuario'] = usuario
            return redirect(url_for('catalogo'))
        else:
            mensaje = "Usuario o contraseña incorrectos"
    return render_template('login.html', mensaje=mensaje)

@app.route('/catalogo')
def catalogo():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('catalogo.html', catalogo=CATALOGO)

@app.route('/producto/<int:id>')
def producto(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    gorra = next((g for g in CATALOGO if g['id'] == id), None)
    if not gorra:
        return redirect(url_for('catalogo'))
    url_producto = request.host_url + f"producto/{id}"
    qr_base64 = generar_qr(url_producto)
    return render_template('producto.html', gorra=gorra, qr=qr_base64)

@app.route('/agregar/<int:id>')
def agregar(id):
    gorra = next((g for g in CATALOGO if g['id'] == id), None)
    if gorra and gorra['stock'] > 0:
        encontrado = False
        for item in carrito:
            if item['id'] == gorra['id']:
                item['cantidad'] += 1
                encontrado = True
                break
        if not encontrado:
            carrito.append({"id": gorra['id'], "nombre": gorra['nombre'], "precio": gorra['precio'], "cantidad": 1})
        gorra['stock'] -= 1
    return redirect(url_for('catalogo'))

@app.route('/carrito')
def ver_carrito():
    subtotal = sum(i['precio'] * i['cantidad'] for i in carrito)
    iva = subtotal * IVA
    total = subtotal + iva
    return render_template('carrito.html', carrito=carrito, subtotal=subtotal, iva=iva, total=total)

@app.route('/factura')
def factura():
    if not carrito:
        return redirect(url_for('ver_carrito'))
    subtotal = sum(i['precio'] * i['cantidad'] for i in carrito)
    iva = subtotal * IVA
    total = subtotal + iva
    numero = datetime.now().strftime("%Y%m%d%H%M%S")
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elementos = []
    titulo = Paragraph("<b>GORRAS S.A. — FACTURA ELECTRÓNICA</b>", styles['Title'])
    elementos.append(titulo)
    elementos.append(Spacer(1, 0.2 * inch))
    info = Paragraph(f"No. Factura: <b>{numero}</b><br/>Fecha: {fecha}<br/>Cliente: {session.get('usuario', 'Cliente')}", styles['Normal'])
    elementos.append(info)
    elementos.append(Spacer(1, 0.3 * inch))
    datos = [["Producto", "Cant.", "Precio Unit.", "Subtotal"]]
    for item in carrito:
        datos.append([item['nombre'], str(item['cantidad']), f"Q{item['precio']:.2f}", f"Q{item['precio']*item['cantidad']:.2f}"])
    datos.append(["", "", "Subtotal:", f"Q{subtotal:.2f}"])
    datos.append(["", "", "IVA (12%):", f"Q{iva:.2f}"])
    datos.append(["", "", "TOTAL:", f"Q{total:.2f}"])
    tabla = Table(datos, colWidths=[3*inch, 0.8*inch, 1.5*inch, 1.5*inch])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#111827')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-4), 0.5, colors.grey),
        ('FONTNAME', (2,-3), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (2,-1), (-1,-1), 13),
        ('TEXTCOLOR', (2,-1), (-1,-1), colors.HexColor('#0369a1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-4), [colors.whitesmoke, colors.white]),
    ]))
    elementos.append(tabla)
    elementos.append(Spacer(1, 0.5 * inch))
    elementos.append(Paragraph("<i>¡Gracias por su compra! — Gorras S.A.</i>", styles['Normal']))
    doc.build(elementos)
    buffer.seek(0)
    carrito.clear()
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=factura_{numero}.pdf'
    return response

@app.route('/logout')
def logout():
    session.clear()
    carrito.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
