import os
import io
import time
import datetime
import fitz
from PIL import Image, ImageFont, ImageDraw
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory

app = Flask(__name__)

PDF_PASSWORD = "UnifreireSystem"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MATERIALES_DIR = os.path.join(BASE_DIR, "Materiales")

PLANTILLA_PATH = os.path.join(MATERIALES_DIR, "plantilla.pdf")

# Fuentes estáticas para garantizar renderizado perfecto sin separación de letras en Vercel, Linux y Docker
FONT_NAME_PATH = os.path.join(MATERIALES_DIR, "Acumin-ExtraCondensedSemiboldItalic.ttf")
FONT_REG_PATH = os.path.join(MATERIALES_DIR, "Acumin-SemiCondensedMedium.ttf")
FONT_BLD_PATH = os.path.join(MATERIALES_DIR, "Acumin-SemiCondensedBold.ttf")
FONT_VAR_PATH = os.path.join(MATERIALES_DIR, "Acumin Variable Concept.ttf")

# Diccionario fonético y ortográfico exhaustivo en español para nombres y apellidos
TILDE_DICT = {
    'maria': 'María', 'jose': 'José', 'jesus': 'Jesús', 'sofia': 'Sofía', 'angel': 'Ángel',
    'sebastian': 'Sebastián', 'joaquin': 'Joaquín', 'martin': 'Martín', 'ramon': 'Ramón',
    'raul': 'Raúl', 'andres': 'Andrés', 'monica': 'Mónica', 'veronica': 'Verónica',
    'rene': 'René', 'victor': 'Víctor', 'hector': 'Héctor', 'cesar': 'César', 'oscar': 'Óscar',
    'ruben': 'Rubén', 'ivan': 'Iván', 'fabian': 'Fabián', 'damian': 'Damián', 'adrian': 'Adrián',
    'julian': 'Julián', 'alvaro': 'Álvaro', 'inigo': 'Íñigo', 'matias': 'Matías', 'tomas': 'Tomás',
    'lucia': 'Lucía', 'ines': 'Inés', 'belen': 'Belén', 'agustin': 'Agustín', 'valentin': 'Valentín',
    'cristobal': 'Cristóbal', 'elias': 'Elías', 'moises': 'Moisés', 'isaias': 'Isaías',
    'salome': 'Salomé', 'noemi': 'Noemí', 'miriam': 'Míriam',
    'martinez': 'Martínez', 'perez': 'Pérez', 'gonzalez': 'González', 'rodriguez': 'Rodríguez',
    'gomez': 'Gómez', 'sanchez': 'Sánchez', 'hernandez': 'Hernández', 'lopez': 'López',
    'ramirez': 'Ramírez', 'alvarez': 'Álvarez', 'fernandez': 'Fernández', 'gutierrez': 'Gutiérrez',
    'garcia': 'García', 'diaz': 'Díaz', 'juarez': 'Juárez', 'munoz': 'Muñoz', 'nunez': 'Núñez',
    'dominguez': 'Domínguez', 'vazquez': 'Vázquez', 'velazquez': 'Velázquez', 'jimenez': 'Jiménez',
    'mendez': 'Méndez', 'benitez': 'Benítez', 'castano': 'Castaño', 'marquez': 'Márquez',
    'avila': 'Ávila', 'cortes': 'Cortés', 'pena': 'Peña', 'cardenas': 'Cárdenas', 'rios': 'Ríos',
    'moron': 'Morón', 'ibanez': 'Ibáñez', 'quinones': 'Quiñones', 'ortega': 'Ortega',
    'montanez': 'Montañez', 'godinez': 'Godínez', 'valdes': 'Valdés', 'solis': 'Solís'
}

def get_font(path, fallback_path, size):
    target = path if os.path.exists(path) else fallback_path
    return ImageFont.truetype(target, int(size))

def get_fecha_lugar_default():
    meses = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    now = datetime.datetime.now()
    mes_actual = meses[now.month - 1]
    return f"Nuevo León, {mes_actual} {now.year}"

def corregir_ortografia_nombre(raw_name):
    """
    Normaliza y aplica corrección ortográfica estricta en español:
    - Inyecta tildes y diacríticos en nombres y apellidos comunes.
    - Limpia signos de puntuación accidentales (puntos finales, comas).
    - Preserva y formatea títulos académicos (Dr., Dra., Lic., Ing., Mtro.).
    - Respeta preposiciones y conectores en minúscula (de la, del, y).
    - Elimina dobles espacios y normaliza guiones.
    """
    raw = raw_name.strip().rstrip(".,;")
    tokens = [t.strip() for t in raw.split() if t.strip()]
    if not tokens:
        return ""
    LOWER_WORDS = {"de", "del", "la", "las", "los", "y", "e", "en", "da", "do", "das", "dos", "van", "von", "der"}
    TITLES = {
        "dr": "Dr.", "dra": "Dra.", "lic": "Lic.", "ing": "Ing.", 
        "mtro": "Mtro.", "mtra": "Mtra.", "prof": "Prof.", "profa": "Profa."
    }
    result = []
    for i, token in enumerate(tokens):
        subtokens = token.split("-")
        clean_subs = []
        for j, st in enumerate(subtokens):
            st_clean = st.strip(".,;").lower()
            if st_clean in TITLES:
                clean_subs.append(TITLES[st_clean])
            elif (i > 0 or j > 0) and st_clean in LOWER_WORDS:
                clean_subs.append(st_clean)
            elif st_clean in TILDE_DICT:
                clean_subs.append(TILDE_DICT[st_clean])
            else:
                clean_subs.append(st.capitalize())
        result.append("-".join(clean_subs))
    return " ".join(result)

def get_fitted_font(text, initial_size, max_width, draw, min_size=14):
    target_path = FONT_NAME_PATH if os.path.exists(FONT_NAME_PATH) else FONT_VAR_PATH
    size = float(initial_size)
    while size > min_size:
        try:
            f = ImageFont.truetype(target_path, int(size))
            if not os.path.exists(FONT_NAME_PATH):
                try: f.set_variation_by_axes([600, 50, 12])
                except Exception: pass
            bbox = draw.textbbox((0, 0), text, font=f)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                return f
            size -= 1.5
        except Exception:
            break
    f = ImageFont.truetype(target_path, int(size))
    if not os.path.exists(FONT_NAME_PATH):
        try: f.set_variation_by_axes([600, 50, 12])
        except Exception: pass
    return f

def draw_centered_multiline(draw, text, font, color, center_x, start_y, spacing=4):
    if not text or not text.strip():
        return start_y
    bbox = draw.multiline_textbbox((0, 0), text, font=font, align='center', spacing=spacing)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw_x = center_x - (w / 2.0) - bbox[0]
    draw_y = start_y - bbox[1]
    draw.multiline_text((draw_x, draw_y), text, font=font, fill=color, align='center', spacing=spacing)
    return start_y + h

@app.route("/static/<path:filename>")
def serve_static(filename):
    static_folder = os.path.join(BASE_DIR, "static")
    return send_from_directory(static_folder, filename)

_PREVIEW_BASE_IMG = None

def get_preview_base_image():
    global _PREVIEW_BASE_IMG
    if _PREVIEW_BASE_IMG is None:
        doc = fitz.open(PLANTILLA_PATH)
        if doc.is_encrypted:
            doc.authenticate(PDF_PASSWORD)
        page = doc[0]
        pix = page.get_pixmap(dpi=72)
        c_mode = "RGBA" if pix.alpha else "RGB"
        _PREVIEW_BASE_IMG = Image.frombytes(c_mode, [pix.width, pix.height], pix.samples)
        doc.close()
    return _PREVIEW_BASE_IMG.copy()

@app.route("/")
def index():
    return render_template("index.html", fecha_default=get_fecha_lugar_default())

@app.route("/api/preview", methods=["POST"])
def preview():
    try:
        data = request.get_json() or {}
        nombres = [n.strip() for n in data.get("nombres", "").split("\n") if n.strip()]
        primer_nombre = corregir_ortografia_nombre(nombres[0]) if nombres else "Nombre de Alumno / Docente"
        motivo1 = data.get("motivo1", "").strip()
        evento = data.get("evento", "").strip()
        motivo2 = data.get("motivo2", "").strip()
        fecha = data.get("fecha", "").strip() or get_fecha_lugar_default()

        img = get_preview_base_image()

        SCALE = 1.0
        CENTER_X = int(396 * SCALE)
        name_y_px = int(285 * SCALE)
        motivo_y_px = int(350 * SCALE)

        font_desc_reg = get_font(FONT_REG_PATH, FONT_VAR_PATH, 16 * SCALE)
        font_desc_bld = get_font(FONT_BLD_PATH, FONT_VAR_PATH, 16 * SCALE)
        font_desc_small = get_font(FONT_REG_PATH, FONT_VAR_PATH, 8 * SCALE)

        text_color = (1, 61, 27, 255)
        draw = ImageDraw.Draw(img)

        # Nombre con fuente estática ExtraCondensed Italic sin separación
        font_name = get_fitted_font(primer_nombre, int(43 * SCALE), int(640 * SCALE), draw)
        draw.text((CENTER_X, name_y_px), primer_nombre, font=font_name, fill=text_color, anchor="mt")

        # 1. Primer Motivo
        curr_y = draw_centered_multiline(
            draw, motivo1, font_desc_reg, text_color, CENTER_X, motivo_y_px, spacing=int(4 * SCALE)
        )

        # 2. Evento / Programa
        y_evento = curr_y + int(8 * SCALE) if motivo1.strip() else motivo_y_px
        curr_y = draw_centered_multiline(
            draw, evento, font_desc_bld, text_color, CENTER_X, y_evento, spacing=int(4 * SCALE)
        )

        # 3. Segundo Motivo (debajo de Evento)
        if motivo2.strip():
            y_motivo2 = curr_y + int(8 * SCALE)
            curr_y = draw_centered_multiline(
                draw, motivo2, font_desc_reg, text_color, CENTER_X, y_motivo2, spacing=int(4 * SCALE)
            )

        # 4. Fecha y Lugar
        base_fecha_y = int(540 * SCALE)
        y_fecha = max(base_fecha_y, curr_y + int(20 * SCALE))
        draw_centered_multiline(
            draw, fecha, font_desc_small, text_color, CENTER_X, y_fecha, spacing=int(3 * SCALE)
        )

        img_bytes = io.BytesIO()
        if img.mode != 'RGB':
            img_rgb = img.convert('RGB')
        else:
            img_rgb = img
        img_rgb.save(img_bytes, format="JPEG", quality=88)
        img_bytes.seek(0)
        return send_file(img_bytes, mimetype="image/jpeg")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json() or {}
        nombres = [n.strip() for n in data.get("nombres", "").split("\n") if n.strip()]
        if not nombres:
            return jsonify({"error": "Debe proporcionar al menos un nombre."}), 400

        motivo1 = data.get("motivo1", "").strip()
        evento = data.get("evento", "").strip()
        motivo2 = data.get("motivo2", "").strip()
        fecha = data.get("fecha", "").strip() or get_fecha_lugar_default()
        
        batch_index = data.get("batch_index", 1)
        total_batches = data.get("total_batches", 1)

        SCALE = 4.16666667
        CANVAS_W = 3300
        CANVAS_H = 2550
        CENTER_X = int(396 * SCALE)
        name_y_px = int(285 * SCALE)
        motivo_y_px = int(350 * SCALE)

        font_desc_reg = get_font(FONT_REG_PATH, FONT_VAR_PATH, 16 * SCALE)
        font_desc_bld = get_font(FONT_BLD_PATH, FONT_VAR_PATH, 16 * SCALE)
        font_desc_small = get_font(FONT_REG_PATH, FONT_VAR_PATH, 8 * SCALE)

        text_color = (1, 61, 27, 255)

        template_doc = fitz.open(PLANTILLA_PATH)
        if template_doc.is_encrypted:
            template_doc.authenticate(PDF_PASSWORD)

        final_doc = fitz.open()

        for raw_name in nombres:
            name = corregir_ortografia_nombre(raw_name)
            img = Image.new("RGBA", (CANVAS_W, CANVAS_H), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)

            font_name = get_fitted_font(name, int(43 * SCALE), int(640 * SCALE), draw)
            draw.text((CENTER_X, name_y_px), name, font=font_name, fill=text_color, anchor="mt")

            # 1. Primer Motivo
            curr_y = draw_centered_multiline(
                draw, motivo1, font_desc_reg, text_color, CENTER_X, motivo_y_px, spacing=int(4 * SCALE)
            )

            # 2. Evento / Programa
            y_evento = curr_y + int(8 * SCALE) if motivo1.strip() else motivo_y_px
            curr_y = draw_centered_multiline(
                draw, evento, font_desc_bld, text_color, CENTER_X, y_evento, spacing=int(4 * SCALE)
            )

            # 3. Segundo Motivo (debajo de Evento)
            if motivo2.strip():
                y_motivo2 = curr_y + int(8 * SCALE)
                curr_y = draw_centered_multiline(
                    draw, motivo2, font_desc_reg, text_color, CENTER_X, y_motivo2, spacing=int(4 * SCALE)
                )

            # 4. Fecha y Lugar
            base_fecha_y = int(540 * SCALE)
            y_fecha = max(base_fecha_y, curr_y + int(20 * SCALE))
            draw_centered_multiline(
                draw, fecha, font_desc_small, text_color, CENTER_X, y_fecha, spacing=int(3 * SCALE)
            )

            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG", optimize=True)
            img_bytes.seek(0)
            img_data = img_bytes.read()

            final_doc.insert_pdf(template_doc, from_page=0, to_page=0)
            page = final_doc[-1]
            page.insert_image(fitz.Rect(0, 0, 792, 612), stream=img_data)
            
            # Liberación de memoria explícita para evitar OOM
            del img
            del img_bytes
            del img_data

        out_pdf_bytes = io.BytesIO()
        final_doc.save(out_pdf_bytes, garbage=4, deflate=True, clean=True, deflate_images=True)
        final_doc.close()
        template_doc.close()

        out_pdf_bytes.seek(0)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if total_batches > 1:
            download_name = f"Lote_{batch_index:02d}_Reconocimientos_UniFreire_{timestamp}.pdf"
        else:
            download_name = f"Reconocimientos_UniFreire_{timestamp}.pdf"

        return send_file(
            out_pdf_bytes,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=download_name
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    return jsonify({"status": "ok", "app": "Generador Jaguar Cloud", "version": "1.1.0"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
