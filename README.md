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


## Ejecutar en Windows

Abre visual y dentro abre la carpeta donde descargaste el proyecto del proyecto y ejecuta en una terminal los siguientes comandos:

```terminal
python --version
```
```terminal
python -m venv .venv
```
```terminal
.\.venv\Scripts\Activate.ps1
```
```terminal
python -m pip install -r requirements.txt
```
```terminal
python -m streamlit run app.py
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


## Validación recomendada

Compara los KPI del tablero contra consultas directas de la bodega para el mismo periodo y polígono. Después confirma que todas las visualizaciones cambien de manera consistente al modificar cada filtro.
