from datetime import datetime
from fastapi import HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.orm import Session
from configuracion import ALLOWED_AUDIO_TYPES, MAX_FILE_SIZE

class SoundService:
    @staticmethod
    def obtener_puntos(db: Session):
        try:
            consulta = db.execute(text("SELECT * FROM point ORDER BY floor, area")).fetchall()

            puntos = [
                {
                    "id": columna.id,
                    "floor": columna.floor,
                    "area": columna.area
                }
                for columna in consulta
            ]
            return {
                "puntos": puntos,
                "cuenta": len(puntos)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"error al obtener los puntos: {str(e)}")

    @staticmethod
    async def crear_audio(db: Session, audio: UploadFile, decibels: float, id_point: int):
        try:
            # Validar tipo de archivo
            if audio.content_type not in ALLOWED_AUDIO_TYPES:
                raise HTTPException(status_code=400, detail="tipo de archivo no permitido")
            
            # Leer el audio
            audio_data = await audio.read()
            tamaño_archivo = len(audio_data)
            
            # Validar tamaño
            if tamaño_archivo > MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail="Mano ese archivo es muuuy grande. Maximo 20Mb")
            
            # Verificar que el punto existe
            verificar_punto = db.execute(
                text("SELECT id FROM point WHERE id = :id"), 
                {"id": id_point}
            ).fetchone()

            if not verificar_punto:
                raise HTTPException(status_code=404, detail=f"El punto con id {id_point} no existe")

            # Insertar el audio
            consulta = db.execute(
                text("INSERT INTO sounds (sound, decibels, date, id_point) VALUES (:sound, :decibels, :date, :id_point) RETURNING id, date"),
                {
                    "sound": audio_data,
                    "decibels": decibels,
                    "date": datetime.utcnow(),
                    "id_point": id_point
                }
            )

            db.commit()
            insertado = consulta.fetchone()

            return {
                "mesagge": "Audio guardado como era",
                "id": insertado.id,
                "decibels": decibels,
                "id_point": id_point,
                "Tamaño_archivo": tamaño_archivo,
                "content_type": audio.content_type,
                "date": insertado.date.isoformat()
            }
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"error al guardar el audio {str(e)}")