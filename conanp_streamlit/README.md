# Dashboard CONANP conectado a PostgreSQL

Esta versión conserva la interfaz visual del tablero CONANP y consulta directamente la base `registro_recorridos` creada con los archivos de faltas, supervisiones sin faltas y recorridos.

## Configuración

1. Confirma que ya ejecutaste `cargar_postgres.py` y que pgAdmin muestra los esquemas `staging` y `dw`.
2. Copia `.streamlit/secrets.toml.example` como `.streamlit/secrets.toml`.
3. Escribe la contraseña del usuario `postgres` dentro de `secrets.toml`.
4. Instala las dependencias y ejecuta la aplicación.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Datos mostrados

- Indicadores de faltas, recorridos, porcentaje de supervisiones con falta y kilómetros recorridos.
- Filtros por periodo, polígono y tipo de falta.
- Evolución mensual de supervisiones, faltas y recorridos.
- Faltas por categoría, concentración por día y hora, y medidas tomadas.
- Mapa coroplético mediante un GeoJSON cargado por el usuario.
- Tablas separadas de supervisiones y recorridos.
- Controles de calidad del modelo PostgreSQL.

Los recorridos y las supervisiones se mantienen separados porque los archivos originales no contienen una llave que permita relacionarlos de forma confiable.

