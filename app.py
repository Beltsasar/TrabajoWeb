from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd # pandas se mantiene para alguna lógica si es necesaria, pero no para la DB directamente
from datetime import datetime
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid

app = Flask(__name__)

# Configuración de la base de datos
# Render automáticamente inyecta la DATABASE_URL para PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost:5432/mydatabase')

# Si estás ejecutando localmente y quieres un SQLite simple para pruebas sin Render DB
# DATABASE_URL = 'sqlite:///local_test.db' # Para pruebas locales rápidas sin Docker o PostgreSQL

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Definición de modelos para la base de datos
class Alumno(Base):
    __tablename__ = 'alumnos'
    Id = Column(Integer, primary_key=True, autoincrement=True)
    Tipo_documento = Column(String(50))
    Documento = Column(String(50), unique=True, nullable=False) # RUT debe ser único
    Nombre = Column(String(100), nullable=False)
    ApellidoM = Column(String(100))
    ApellidoP = Column(String(100))
    Mail = Column(String(100))
    Telefono = Column(String(50))
    Producto = Column(String(100))
    RutEmpresa = Column(String(50))
    Asistencia = Column(Integer, default=0)
    Nota = Column(Text)
    FechaDeCurso = Column(DateTime)
    Solicitud = Column(String(100))
    N_OP = Column(String(50))

class Asistencia(Base):
    __tablename__ = 'asistencias'
    Id = Column(Integer, primary_key=True, autoincrement=True)
    AlumnoID = Column(Integer, nullable=False) # Foreign Key simulada
    Curso = Column(String(100))
    Fecha = Column(DateTime, nullable=False)
    Hora = Column(String(20), nullable=False) # Guardamos la hora como string para simplicidad, o podrías usar Time

# Asegura que las tablas se creen si no existen
def create_tables():
    Base.metadata.create_all(engine)

# Función para limpiar y formatear RUT
def clean_rut(rut):
    # Elimina puntos y guiones, convierte a mayúsculas
    return rut.replace('.', '').replace('-', '').upper()

def validate_rut(rut):
    rut = rut.upper().replace(".", "").replace("-", "")
    
    if not rut[:-1].isdigit():
        return False
    if len(rut) < 2:
        return False
        
    dv = rut[-1]
    body = int(rut[:-1])

    s = 1
    m = 0
    while body > 0:
        m = m + (body % 10) * s
        s = s + 1
        if s == 8:
            s = 2
        body = int(body / 10)

    res = 11 - (m % 11)

    if res == 10:
        return dv == 'K'
    elif res == 11:
        return dv == '0'
    else:
        return dv == str(res)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/Asistencias')
def course_attendance_summary():
    return render_template('Asistencias.html')

@app.route('/RegistroExitoso')
def success():
    return render_template('RegistroExitoso.html')

@app.route('/VistaAdmin')
def admin():
    return render_template('VistaAdmin.html')

@app.route('/register_attendance', methods=['POST'])
def register_attendance():
    data = request.get_json()
    rut_raw = data.get('rut')

    if not rut_raw:
        return jsonify({'error': 'RUT no proporcionado.'}), 400

    if not validate_rut(rut_raw):
        return jsonify({'error': 'RUT inválido. Formato o dígito verificador incorrecto.'}), 400

    rut_cleaned = clean_rut(rut_raw)

    session = Session()
    try:
        alumno_found = session.query(Alumno).filter_by(Documento=rut_cleaned).first()

        if not alumno_found:
            return jsonify({'error': 'RUT no encontrado en la base de datos de alumnos.'}), 404

        # Registrar asistencia
        current_time = datetime.now()
        new_attendance = Asistencia(
            AlumnoID=alumno_found.Id,
            Curso='Curso por Defecto', # Asume un curso por defecto, o agrégalo a la lógica
            Fecha=current_time,
            Hora=current_time.strftime('%H:%M:%S')
        )
        session.add(new_attendance)
        
        # Incrementar asistencia del alumno
        alumno_found.Asistencia = (alumno_found.Asistencia or 0) + 1
        session.commit()

        return jsonify({
            'message': 'Asistencia registrada con éxito.',
            'nombre': f"{alumno_found.Nombre} {alumno_found.ApellidoP or ''}".strip(),
            'fecha': current_time.strftime('%Y-%m-%d'),
            'hora': current_time.strftime('%H:%M:%S')
        }), 200

    except Exception as e:
        session.rollback()
        print(f"Error al registrar asistencia: {e}")
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500
    finally:
        session.close()

@app.route('/api/alumnos', methods=['GET'])
def get_alumnos():
    session = Session()
    try:
        search_rut = request.args.get('rut')
        query = session.query(Alumno)

        if search_rut:
            query = query.filter(Alumno.Documento.ilike(f"%{clean_rut(search_rut)}%"))

        alumnos = query.all()
        
        alumnos_list = []
        for alumno in alumnos:
            alumno_dict = {col.name: getattr(alumno, col.name) for col in alumno.__table__.columns}
            
            # Formatear FechaDeCurso a YYYY-MM-DD o None
            if alumno_dict['FechaDeCurso']:
                alumno_dict['FechaDeCurso'] = alumno_dict['FechaDeCurso'].strftime('%Y-%m-%d')
            else:
                alumno_dict['FechaDeCurso'] = None
            
            # Ajustar nombres de columnas si son diferentes de JS (ej: Teléfono vs Telefono)
            alumno_dict['Teléfono'] = alumno_dict.pop('Telefono', None) # Renombrar si es necesario para el frontend
            alumno_dict['N° OP'] = alumno_dict.pop('N_OP', None) # Renombrar si es necesario
            
            alumnos_list.append(alumno_dict)

        return jsonify(alumnos_list)
    except Exception as e:
        print(f"Error al obtener alumnos: {e}")
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500
    finally:
        session.close()

@app.route('/api/alumnos/<int:alumno_id>', methods=['PUT'])
def update_alumno(alumno_id):
    data = request.get_json()
    session = Session()
    
    try:
        alumno = session.query(Alumno).filter_by(Id=alumno_id).first()

        if not alumno:
            return jsonify({'error': 'Alumno no encontrado.'}), 404

        for key, value in data.items():
            # Mapear nombres de columnas del frontend al backend si son diferentes
            db_key = key
            if key == 'Teléfono':
                db_key = 'Telefono'
            elif key == 'N° OP':
                db_key = 'N_OP'

            if hasattr(alumno, db_key):
                if db_key == 'Documento' and value:
                    setattr(alumno, db_key, clean_rut(value))
                elif db_key == 'FechaDeCurso' and value:
                    try:
                        setattr(alumno, db_key, datetime.strptime(value, '%Y-%m-%d'))
                    except ValueError:
                        setattr(alumno, db_key, None) # Si el formato es incorrecto, establecer como None
                else:
                    # Convertir Asistencia a int si es necesario
                    if db_key == 'Asistencia' and value is not None:
                        setattr(alumno, db_key, int(value))
                    elif value == "": # Manejar strings vacíos como None para columnas que pueden ser nulas
                        setattr(alumno, db_key, None)
                    else:
                        setattr(alumno, db_key, value)
        
        session.commit()
        return jsonify({'message': 'Alumno actualizado con éxito.'}), 200

    except Exception as e:
        session.rollback()
        print(f"Error al actualizar alumno: {e}")
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500
    finally:
        session.close()

@app.route('/api/Asistencias', methods=['GET'])
def get_course_attendance():
    session = Session()
    try:
        asistencias = session.query(Asistencia).all()
        
        course_counts = {}
        for asistencia in asistencias:
            curso = asistencia.Curso if asistencia.Curso else 'Sin Curso Asignado'
            course_counts[curso] = course_counts.get(curso, 0) + 1

        return jsonify(course_counts)
    except Exception as e:
        print(f"Error al obtener asistencias por curso: {e}")
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500
    finally:
        session.close()
 
# Dentro de app.py, después de la definición de modelos
def load_initial_data_from_excel_to_db():
    try:
        df_alumnos_excel = pd.read_excel('alumnos.xlsx', sheet_name='Alumnos')
        session = Session()
        for index, row in df_alumnos_excel.iterrows():
            # Limpiar y convertir datos del Excel
            rut = clean_rut(str(row.get('Documento', '')))
            
            fecha_curso = row.get('FechaDeCurso')
            if pd.isna(fecha_curso): # Check for NaT or NaNs
                fecha_curso = None
            elif isinstance(fecha_curso, (datetime, pd.Timestamp)):
                fecha_curso = fecha_curso.to_pydatetime()
            else: # Try to parse string dates
                try:
                    fecha_curso = datetime.strptime(str(fecha_curso), '%Y-%m-%d')
                except (ValueError, TypeError):
                    fecha_curso = None


            alumno = Alumno(
                Tipo_documento=row.get('Tipo documento'),
                Documento=rut,
                Nombre=row.get('Nombre'),
                ApellidoM=row.get('ApellidoM'),
                ApellidoP=row.get('ApellidoP'),
                Mail=row.get('Mail'),
                Telefono=row.get('Teléfono'), # Asegúrate que el nombre de la columna en tu Excel sea 'Teléfono' o ajusta aquí
                Producto=row.get('Producto'),
                RutEmpresa=row.get('RutEmpresa'),
                Asistencia=int(row.get('Asistencia', 0)),
                Nota=row.get('Nota'),
                FechaDeCurso=fecha_curso,
                Solicitud=row.get('Solicitud'),
                N_OP=row.get('N° OP') # Asegúrate que el nombre de la columna en tu Excel sea 'N° OP' o ajusta aquí
            )
            session.add(alumno)
        session.commit()
        print("Datos de alumnos cargados exitosamente desde Excel a PostgreSQL.")
    except Exception as e:
        session.rollback()
        print(f"Error al cargar datos desde Excel: {e}")
    finally:
        session.close()

# Luego, en el if __name__ == '__main__': block:
if __name__ == '__main__':
    create_tables()
    # Descomenta la siguiente línea SOLO si quieres cargar los datos del Excel por PRIMERA VEZ
    # load_initial_data_from_excel_to_db() 
    app.run(debug=True, port=os.getenv('PORT', 5000))