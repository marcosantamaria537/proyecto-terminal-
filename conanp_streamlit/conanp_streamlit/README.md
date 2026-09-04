# Dashboard de vigilancia CONANP en Streamlit

Aplicación descriptiva para explorar recorridos de supervisión y faltas registradas en el Área de Protección de Flora y Fauna Costa Occidental de Isla Mujeres, Punta Cancún y Punta Nizuc.

## Funciones incluidas

- Carga de Excel (incluidas varias hojas), CSV o SQLite.
- Carga de polígonos en GeoJSON o dentro de un ZIP.
- Filtros globales por periodo, polígono y tipo de falta.
- KPI de faltas, recorridos, tasa de infracción y kilómetros recorridos.
- Tendencia mensual, categorías de faltas, matriz hora–día y medidas tomadas.
- Mapa de calor y coroplético cuando existen coordenadas o polígonos.
- Tabla filtrada y descarga CSV con embarcaciones anonimizadas.
- Resumen de calidad de datos.
- Datos sintéticos automáticos para comprobar la interfaz sin usar información institucional.

## Ejecutar en Windows

Abre PowerShell dentro de la carpeta del proyecto y ejecuta:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

La aplicación se abrirá normalmente en `http://localhost:8501`.

## Columnas reconocidas

El proceso de carga normaliza mayúsculas, acentos y espacios. Reconoce, entre otros, los siguientes campos:

| Campo estándar | Ejemplos aceptados |
| --- | --- |
| `fecha` | `FECHA`, `FECHA_SUPERVISION`, `FECHA_SUPERVICION`, `FECHA_CAPTURA` |
| `tipo_falta` | `TIPO_FALTA`, `FALTA`, `TIPO_INFRACCION` |
| `poligono` | `POLIGONO`, `ZONA`, `ANP` |
| `subzona` | `SUBZONA`, `SUB_ZONA` |
| `recorrido_id` | `ID_RECORRIDO`, `FOLIO_RECORRIDO`, `FOLIO` |
| `km_recorridos` | `KM_RECORRIDOS`, `KILOMETRAJE`, `KM` |
| coordenadas | `LATITUD`/`LONGITUD`, `LAT`/`LON` |

Si los nombres reales son distintos, agrégalos en `ALIASES`, dentro de `src/data.py`.

## Uso de la bodega SQLite

La aplicación inspecciona las tablas y carga aquellas que contengan una columna de fecha reconocible. Si la bodega usa un esquema en estrella con claves sustitutas, conviene crear una vista SQL que reúna la tabla de hechos con las dimensiones y cargar esa vista como una fuente del dashboard.

## Seguridad y despliegue

- No subas las bases institucionales a GitHub ni a un despliegue público.
- La tabla visible sustituye la embarcación por un hash estable y no exporta el nombre original.
- Para activar una contraseña simple, copia `.streamlit/secrets.toml.example` como `.streamlit/secrets.toml` y cambia el valor.
- Antes de usar Streamlit Community Cloud con información real, define el control de acceso autorizado por la CONANP y valida dónde se almacenan/procesan los datos.

## Validación recomendada

Compara los KPI del tablero contra consultas directas de la bodega para el mismo periodo y polígono. Después confirma que todas las visualizaciones cambien de manera consistente al modificar cada filtro.
