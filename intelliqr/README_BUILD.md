# Compilar IntelliQR a .exe (Windows)

Este documento explica los tres cambios necesarios para que el `.exe`
funcione igual que en desarrollo: **ícono de la app**, **códigos de
barras sin pedir instalar nada aparte**, y el resto de dependencias que
ya tenías bien resueltas (pyzbar, qrcode, PIL, etc.).

## 1. Generar el ícono (una sola vez)

Windows necesita un `.ico` (no sirve un `.jpeg`) para el ícono del `.exe`.
Con tu logo ya instalado Pillow (`pip install pillow`):

```
python scripts\make_icon.py "C:\Users\Ashleidy\Desktop\IntelliQR\intelliqr\LOGO.jpeg"
```

Esto crea `LOGO.ico` junto al `.jpeg`. Guárdalo en la raíz del proyecto,
junto a `LOGO.jpeg` (o donde prefieras, solo ajusta la ruta abajo).

## 2. Empaquetar Ghostscript (necesario para TODOS los códigos de barra)

Todo el motor de códigos de barra (`treepoem`/BWIPP) llama internamente al
programa Ghostscript — no es opcional para ningún tipo, ni siquiera
Code 128. Si la persona que instale tu `.exe` no tiene Ghostscript, va a
ver siempre el aviso rojo que mostraste. La app ya sabe encontrar una
copia de Ghostscript empaquetada junto al `.exe` (`core/barcode_engine/gs_locator.py`),
así que solo falta incluirla al compilar:

1. Instala Ghostscript normal en tu máquina de compilación (la tuya, no la
   del usuario final): https://www.ghostscript.com/releases/gsdnld.html
   — instala la versión de 64 bits.
2. Anota la carpeta donde quedó instalado, típicamente:
   `C:\Program Files\gs\gs10.03.1` (el número de versión puede variar).
3. Usa esa carpeta completa (con sus subcarpetas `bin`, `lib`, `Resource`)
   en el `--add-data` de abajo — la app la busca exactamente en
   `ghostscript\bin` al lado del `.exe`.

**Importante:** Ghostscript es software libre bajo licencia AGPL. Antes de
distribuir tu `.exe` con una copia embebida, conviene revisar qué implica
esa licencia para tu caso (por ejemplo, incluir el aviso de licencia junto
a la app). No es un tema técnico que yo pueda resolver por ti, pero sí
vale la pena que lo tengas presente.

## 3. También faltaba: los datos internos de treepoem

Aparte de Ghostscript, `treepoem` trae un archivo interno
(`postscriptbarcode/barcode.ps`, ~800 KB) con el código BWIPP que dibuja
los códigos. Ese archivo es un dato, no código Python, así que PyInstaller
no lo incluye solo — hace falta `--collect-data treepoem`. Sin esto, los
códigos de barra fallarían igual aunque Ghostscript sí estuviera bien
instalado.

## Comando completo corregido

Ajusta solo las dos rutas que dependen de tu máquina (`LOGO.ico` y la
carpeta de Ghostscript que instalaste en el paso 2):

```
python -m PyInstaller --onefile --noconsole --clean --name "IntelliQR" ^
  --icon "C:\Users\Ashleidy\Desktop\IntelliQR\intelliqr\LOGO.ico" ^
  --add-data "C:\Users\Ashleidy\Desktop\IntelliQR\intelliqr\LOGO.ico;." ^
  --add-data "C:\Users\Ashleidy\Desktop\IntelliQR\intelliqr\LOGO.jpeg;." ^
  --add-data "C:\Program Files\gs\gs10.03.1;ghostscript" ^
  --add-binary "C:\Users\Ashleidy\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\pyzbar\libiconv.dll;pyzbar" ^
  --add-binary "C:\Users\Ashleidy\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\pyzbar\libzbar-64.dll;pyzbar" ^
  --collect-all qrcode --collect-all PIL --collect-all reportlab ^
  --collect-data treepoem ^
  --collect-submodules sqlalchemy --hidden-import cv2 ^
  --paths "." --exclude-module tkinter --exclude-module matplotlib ^
  --exclude-module PyQt5 --exclude-module PyQt6 --exclude-module PySide2 ^
  --distpath "..\dist" --workpath "..\build" --specpath ".." "app\main.py"
```

Qué cambió respecto a tu comando original:

| Cambio | Por qué |
|---|---|
| `--icon "...\LOGO.ico"` | Fija el ícono del propio archivo `.exe` (Explorador, barra de tareas). Con `--add-data` solo se copiaba el archivo, nada lo usaba como ícono. |
| `--add-data "...\LOGO.ico;."` | Para que la app lo cargue en tiempo de ejecución como ícono de ventana (`app/resources.py` ya lo busca ahí). |
| `--add-data "...\gs10.03.1;ghostscript"` | Empaqueta Ghostscript completo dentro del `.exe`. Sin esto, los códigos de barra piden instalarlo en cada equipo donde se use la app. |
| `--collect-data treepoem` | Incluye el archivo interno de BWIPP que faltaba; sin él, fallaría igual aunque Ghostscript esté presente. |

## Qué ya no hace falta cambiar

Tu manejo de `pyzbar`, `qrcode`, `PIL`, `reportlab`, `sqlalchemy`, `cv2` y
los `--exclude-module` ya estaba bien — no los toqué.

## Si el ícono no aparece en la barra de tareas

Windows agrupa las apps por un identificador interno ("App User Model ID").
Sin uno propio, tu app quedaba agrupada bajo el ID genérico de Python, y
Windows reutilizaba el ícono que tuviera cacheado para ese ID — casi
siempre el genérico — sin importar qué ícono le pusiéramos a la ventana.
Ya se corrigió en `app/main.py` (`_fix_windows_taskbar_icon`), fijando un
ID propio antes de crear cualquier ventana.

Si después de recompilar sigue sin verse, es la caché de íconos de Windows
(no tu app): cierra la app, borra `IconCache.db` en
`%LocalAppData%\Microsoft\Windows\Explorer` (o simplemente reinicia
"Explorador de Windows" desde el Administrador de tareas) y vuelve a
abrirla.

## Verificar antes de distribuir

En la máquina de compilación (o en una limpia, ideal), corre el `.exe` y
prueba:
- Que el ícono aparece en el Explorador y en la barra de tareas al abrir
  la app.
- Generar un Code 128 o EAN-13 simple.
- Generar uno de los tipos "difíciles" (Data Matrix, PDF417, GS1-128).
