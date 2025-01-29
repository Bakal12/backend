from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import mysql.connector, json
from mysql.connector import Error

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todos los orígenes
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos
    allow_headers=["*"],  # Permite todos los headers
)

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'dml'
}

class Repuesto(BaseModel):
    codigo: str
    descripcion: str
    cantidad_disponible: str
    numero_estanteria: str
    numero_estante: str
    numero_BIN: str
    posicion_BIN: str

class Ficha(BaseModel):
    numero_ficha: int
    cliente: str
    serie: str
    modelo: str
    nº_bat: str
    nº_cargador: str
    diagnóstico: str
    tipo: str
    observaciones: str
    reparación: str
    repuestos_colocados: Dict[str, int]
    repuestos_faltantes: Dict[str, int]
    nº_ciclos: str
    estado: str

class UpdateStockParams(BaseModel):
    action: str


def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

def sanitize_data(data):
    """
    Reemplaza valores no válidos en el JSON (NaN, Infinity, -Infinity) por None.
    """
    if isinstance(data, dict):
        return {k: sanitize_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_data(v) for v in data]
    elif isinstance(data, float):
        if data != data or data in [float("inf"), float("-inf")]:
            return None
    return data

@app.get("/repuestos")
async def get_repuestos():
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM repuestos ORDER BY codigo ASC")
        repuestos = cursor.fetchall()
        return repuestos
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.post("/repuestos")
async def create_repuesto(repuesto: Repuesto):
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor()
        query = """INSERT INTO repuestos 
                   (codigo, descripción, cantidad_disponible, nº_estantería, nº_estante, nº_BIN, posición_BIN) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        values = (repuesto.codigo, repuesto.descripcion, repuesto.cantidad_disponible, 
                  repuesto.numero_estanteria, repuesto.numero_estante, repuesto.numero_BIN, repuesto.posicion_BIN)
        cursor.execute(query, values)
        connection.commit()

        # Obtener el ID generado automáticamente
        new_id = cursor.lastrowid
        
        return {"message": "Repuesto creado exitosamente", "id": new_id}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.put("/repuestos/{id}")
async def update_repuesto(id: int, repuesto: Dict[str, Any]):
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor()
        
        # Construir la consulta de actualización dinámicamente
        update_fields = []
        values = []
        for key, value in repuesto.items():
            update_fields.append(f"{key} = %s")
            values.append(value)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        query = f"UPDATE repuestos SET {', '.join(update_fields)} WHERE ID = %s"
        values.append(id)
        
        cursor.execute(query, tuple(values))
        connection.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Repuesto no encontrado")
        return {"message": "Repuesto actualizado exitosamente"}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.delete("/repuestos/{id}")
async def delete_repuesto(id: int):
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor()
        query = "DELETE FROM repuestos WHERE id = %s"
        cursor.execute(query, (id,))
        connection.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Repuesto no encontrado")
        return {"message": "Repuesto eliminado exitosamente"}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.get("/repuestos/search")
async def search_repuestos(term: str):
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = """SELECT * FROM repuestos 
                   WHERE codigo LIKE %s 
                   OR descripción LIKE %s 
                   OR cantidad_disponible LIKE %s 
                   OR nº_estantería LIKE %s 
                   OR nº_estante LIKE %s 
                   OR nº_BIN LIKE %s 
                   OR posición_BIN LIKE %s"""
        search_term = f"%{term}%"
        values = (search_term,) * 7
        cursor.execute(query, values)
        repuestos = cursor.fetchall()
        return repuestos
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

## --------------------- MAQUINAS --------------------- ##

@app.get("/fichas")
async def get_fichas():
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM maquinas ORDER BY numero_ficha ASC")
        fichas = cursor.fetchall()
        for ficha in fichas:
            ficha['repuestos_colocados'] = json.loads(ficha['repuestos_colocados'])
            ficha['repuestos_faltantes'] = json.loads(ficha['repuestos_faltantes'])
        return fichas
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.post("/fichas")
async def create_ficha(ficha: Ficha):
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor()
        query = """INSERT INTO maquinas 
                   (numero_ficha, cliente, serie, modelo, nº_bat, nº_cargador, diagnóstico, tipo, observaciones, reparación, repuestos_colocados, repuestos_faltantes, nº_ciclos, estado) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        values = (ficha.numero_ficha, ficha.cliente, ficha.serie, ficha.modelo, ficha.nº_bat, ficha.nº_cargador, 
                  ficha.diagnóstico, ficha.tipo, ficha.observaciones, ficha.reparación, json.dumps(ficha.repuestos_colocados), 
                  json.dumps(ficha.repuestos_faltantes), ficha.nº_ciclos, ficha.estado)
        cursor.execute(query, values)
        connection.commit()
        
        new_id = cursor.lastrowid
        return {"message": "Ficha creada exitosamente", "id": new_id}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.put("/fichas/{id}")
async def update_ficha(id: int, ficha: Dict[str, Any]):
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor()
        
        update_fields = []
        values = []
        for key, value in ficha.items():
            if key in ['repuestos_colocados', 'repuestos_faltantes']:
                update_fields.append(f"{key} = %s")
                values.append(json.dumps(value))
            else:
                update_fields.append(f"{key} = %s")
                values.append(value)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        query = f"UPDATE maquinas SET {', '.join(update_fields)} WHERE item = %s"
        values.append(id)
        
        cursor.execute(query, tuple(values))
        connection.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ficha no encontrada")
        return {"message": "Ficha actualizada exitosamente"}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.delete("/fichas/{id}")
async def delete_ficha(id: int):
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor()
        query = "DELETE FROM maquinas WHERE item = %s"
        cursor.execute(query, (id,))
        connection.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ficha no encontrada")
        return {"message": "Ficha eliminada exitosamente"}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.get("/fichas/search")
async def search_fichas(term: str):
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT * FROM maquinas 
        WHERE numero_ficha LIKE %s 
        OR cliente LIKE %s 
        OR serie LIKE %s 
        OR modelo LIKE %s 
        OR nº_bat LIKE %s 
        OR nº_cargador LIKE %s 
        OR diagnóstico LIKE %s 
        OR tipo LIKE %s 
        OR observaciones LIKE %s 
        OR reparación LIKE %s 
        OR nº_ciclos LIKE %s 
        OR estado LIKE %s
        """
        search_term = f"%{term}%"
        values = (search_term,) * 12
        cursor.execute(query, values)
        fichas = cursor.fetchall()
        for ficha in fichas:
            ficha['repuestos_colocados'] = json.loads(ficha['repuestos_colocados'])
            ficha['repuestos_faltantes'] = json.loads(ficha['repuestos_faltantes'])
        return fichas
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.put("/update_stock/{ficha_id}/{repuesto_codigo}")
async def update_stock(ficha_id: int, repuesto_codigo: str, params: UpdateStockParams):
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get the current ficha and repuesto
        cursor.execute("SELECT repuestos_colocados FROM maquinas WHERE item = %s", (ficha_id,))
        ficha = cursor.fetchone()
        
        cursor.execute("SELECT cantidad_disponible FROM repuestos WHERE codigo = %s", (repuesto_codigo,))
        repuesto = cursor.fetchone()
        
        if not ficha or not repuesto:
            raise HTTPException(status_code=404, detail="Ficha or Repuesto not found")
        
        repuestos_colocados = json.loads(ficha['repuestos_colocados'])
        
        if repuesto_codigo not in repuestos_colocados:
            raise HTTPException(status_code=400, detail="Repuesto not found in repuestos_colocados")
        
        cantidad = repuestos_colocados[repuesto_codigo]
        stock_actual = int(repuesto['cantidad_disponible'])
        
        if params.action == "decrease":
            new_stock = stock_actual - cantidad
            if new_stock < 0:
                raise HTTPException(status_code=400, detail="Not enough stock")
        elif params.action == "increase":
            new_stock = stock_actual + cantidad
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        # Update the repuesto stock
        cursor.execute("UPDATE repuestos SET cantidad_disponible = %s WHERE codigo = %s", (new_stock, repuesto_codigo))
        
        connection.commit()
        
        return {"message": "Stock updated successfully", "new_stock": new_stock}
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

