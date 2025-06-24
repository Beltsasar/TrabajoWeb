from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd
from datetime import datetime
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
# from sqlalchemy.dialects.postgresql import UUID # Descomenta si realmente usas UUIDs en algún modelo
# import uuid # Descomenta si realmente usas UUIDs en algún modelo

app = Flask(__name__)

# Configuración de la base de datos
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost:5432/mydatabase')

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Definición de modelos para la base de datos
class Alumno(Base):
    __tablename__ = 'alumnos'
    Id = Column(Integer, primary_key=True, autoincrement=True)
    Tipo_documento = Column(String(50))
    Documento = Column(String(50), unique=True, nullable=False)
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
    AlumnoID = Column(Integer, nullable=False)
    Curso = Column(String(100))
    Fecha = Column(DateTime, nullable=False)
    Hora = Column(String(20), nullable=False)

def create_tables():
    print("INFO: Intentando crear tablas de la base de datos...")
    try:
        Base.metadata.create_all(engine)
        print("INFO: Creación de tablas intentada.")
    except Exception as e:
        print(f"ERROR: No se pudieron crear las tablas: {e}")


# Función para limpiar y formatear RUT
def clean_rut(rut):
    return str(rut).replace('.', '').replace('-', '').upper() # Asegurar que 'rut' es string

def validate_rut(rut):
    # Ya tienes la función aquí, la he omitido para concisión
    rut = str(rut).upper().replace(".", "").replace("-", "")
    
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

        current_time = datetime.now()
        new_attendance = Asistencia(
            AlumnoID=alumno_found.Id,
            Curso='Curso por Defecto',
            Fecha=current_time,
            Hora=current_time.strftime('%H:%M:%S')
        )
        session.add(new_attendance)
        
        alumno_found.Asistencia = (alumno_found.Asistencia or 0) + 1
        session.commit()

        # Asegúrate de que new_attendance.Fecha y new_attendance.Hora son cadenas formateadas
        # El error original era porque estabas tratando new_attendance como un diccionario,
        # pero es un objeto Asistencia.
        return jsonify({
            'message': 'Asistencia registrada con éxito.',
            'nombre': f"{alumno_found.Nombre} {alumno_found.ApellidoP or ''}".strip(),
            'fecha': new_attendance.Fecha.strftime('%Y-%m-%d'), # Acceder a los atributos del objeto
            'hora': new_attendance.Hora
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
            
            if alumno_dict['FechaDeCurso']:
                alumno_dict['FechaDeCurso'] = alumno_dict['FechaDeCurso'].strftime('%Y-%m-%d')
            else:
                alumno_dict['FechaDeCurso'] = None
            
            alumno_dict['Teléfono'] = alumno_dict.pop('Telefono', None)
            alumno_dict['N° OP'] = alumno_dict.pop('N_OP', None)
            
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
                        setattr(alumno, db_key, None)
                else:
                    if db_key == 'Asistencia' and value is not None:
                        setattr(alumno, db_key, int(value))
                    elif value == "":
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
        session.rollback()
        print(f"Error al obtener asistencias por curso: {e}")
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500
    finally:
        session.close()
 
def load_initial_data_from_excel_to_db():
    session = None # Inicializamos session a None
    try:
        df_alumnos_excel = pd.read_excel('alumnos.xlsx', sheet_name='Alumnos')
        session = Session() # Solo creamos la sesión si la lectura del Excel es exitosa
        for index, row in df_alumnos_excel.iterrows():
            rut = clean_rut(str(row.get('Documento', '')))
            
            existing_alumno = session.query(Alumno).filter_by(Documento=rut).first()
            if existing_alumno:
                print(f"INFO: Alumno con RUT {rut} ya existe. Saltando inserción para evitar duplicados.")
                continue

            fecha_curso = row.get('FechaDeCurso')
            if pd.isna(fecha_curso):
                fecha_curso = None
            elif isinstance(fecha_curso, (datetime, pd.Timestamp)):
                fecha_curso = fecha_curso.to_pydatetime()
            else:
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
                Telefono=row.get('Teléfono'),
                Producto=row.get('Producto'),
                RutEmpresa=row.get('RutEmpresa'),
                Asistencia=int(row.get('Asistencia', 0)),
                Nota=row.get('Nota'),
                FechaDeCurso=fecha_curso,
                Solicitud=row.get('Solicitud'),
                N_OP=row.get('N° OP')
            )
            session.add(alumno)
        session.commit()
        print("Datos de alumnos cargados exitosamente desde Excel a PostgreSQL.")
    except Exception as e:
        # Solo intenta hacer rollback si la sesión se creó
        if session:
            session.rollback()
        print(f"Error al cargar datos desde Excel: {e}")
    finally:
        # Solo intenta cerrar la sesión si se creó
        if session:
            session.close()

# Esto es lo que Gunicorn ejecutará al cargar tu aplicación
create_tables() # Siempre se ejecuta para crear tablas si no existen

# Manejo de errores para la carga inicial de datos desde Excel
# Esto es importante para que la aplicación no falle al iniciar si el Excel no se puede leer
try:
    load_initial_data_from_excel_to_db()
except Exception as e:
    print(f"CRÍTICO: Falló la carga inicial de datos. La aplicación podría no funcionar correctamente. Error: {e}")

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv('PORT', 5000))