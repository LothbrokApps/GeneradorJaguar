# Generador Jaguar - Universidad Freire (Versión Cloud / GitHub)

Sistema automatizado de emisión de reconocimientos y diplomas en la nube para la **Universidad Freire**. Diseñado para procesar lotes de certificados en alta resolución (300 DPI) con máxima compresión PDF y descarga automática instantánea al navegador.

---

## 🚀 Características Principales

1. **Descarga Automática Instantánea:**
   - Al pulsar *"Generar y Descargar Reconocimientos"*, el servidor genera el archivo PDF y el navegador lo descarga inmediatamente sin requerir pasos adicionales.
2. **Vista Previa en Tiempo Real:**
   - La pantalla muestra los cambios al instante conforme se redacta el texto o se agregan renglones.
3. **Manejo Dinámico de Renglones con `Enter`:**
   - Soporte multilínea completo para el *Primer Motivo*, *Nombre del Evento / Programa*, *Segundo Motivo* (ubicado por debajo del evento) y *Fecha y Lugar*. El sistema ajusta automáticamente la posición vertical de las siguientes secciones sin que se encimen.
4. **Normalización Inteligente de Nombres:**
   - Corrige automáticamente mayúsculas y minúsculas a formato de Nombre Propio, respetando tildes y preposiciones (`de la`, `del`, `de`, etc.).
5. **Detector de Desbordamiento Tipográfico (Auto-Fit):**
   - Reduce progresivamente el tamaño de fuente en nombres largos para que nunca se corten ni salgan de los márgenes.
6. **Ejes de Variación Tipográfica Fijos:**
   - Implementa ejes numéricos directos de FreeType (`[Weight=600, Width=50, Slant=12]`) asegurando que las letras no se separen ni expandan en servidores Linux/Docker.
7. **Protección de Plantilla Institucional:**
   - La plantilla PDF está protegida bajo contraseña `UnifreireSystem` impidiendo manipulaciones o alteraciones no autorizadas.
8. **Fecha Automática:**
   - Autocompleta con `Nuevo León, (Mes actual y año actual)`.

---

## 🌐 Despliegue en la Nube (1-Click en Render / Railway)

### Opción A: Despliegue en Render (Recomendado - Gratuito)
1. Crea un repositorio en **GitHub** y sube todos los archivos de esta carpeta.
2. Ingresa a [render.com](https://render.com) y conecta tu cuenta de GitHub.
3. Selecciona **New > Web Service** y elige tu repositorio.
4. Render detectará automáticamente `render.yaml` o configura:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --workers 2 --timeout 120`
5. ¡Listo! Tu plataforma estará en línea en `https://tu-app.onrender.com`.

### Opción B: Despliegue en Railway
1. En [railway.app](https://railway.app), crea un nuevo proyecto desde tu repositorio de GitHub.
2. Railway usará automáticamente el `Dockerfile` o `Procfile`.
3. Tu app estará lista en un dominio público en menos de 2 minutos.

### Opción C: Google Cloud Run / AWS / Docker
```bash
docker build -t generador-jaguar .
docker run -p 8080:8080 generador-jaguar
```

---

## 💻 Ejecución Local

Para probar el servidor localmente en tu computadora:

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Iniciar servidor
python app.py
```

Abre tu navegador en `http://localhost:8080`.

---

## 📁 Estructura del Repositorio

```text
GITHUB/
├── app.py                  # API Flask de generación y vista previa en tiempo real
├── templates/
│   └── index.html          # Interfaz de usuario responsiva
├── static/
│   ├── css/style.css       # Estilos visuales institucionales (#0b5c47, #f4a024)
│   ├── js/main.js          # Control de eventos, live preview y descarga automática
│   └── img/                # Logotipo UniFreire e isotipo
├── Materiales/
│   ├── Acumin Variable Concept.ttf
│   ├── icon.png
│   ├── logo_unifreire.png
│   └── plantilla.pdf       # Plantilla base protegida con contraseña
├── requirements.txt        # Dependencias de Python
├── Procfile                # Archivo de inicio para PaaS
├── render.yaml             # Configuración para Render
├── Dockerfile              # Contenedor estándar para producción
├── .gitignore              # Archivo de exclusión de Git
└── README.md               # Esta documentación
```
