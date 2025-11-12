from fastapi import APIRouter, Depends, HTTPException
from database import SessionDepends
from sqlalchemy import text
from utils.dependencias import get_current_user_dependency

router = APIRouter(prefix="/admin", tags=["Admin"])

def verify_admin(current_user: dict = Depends(get_current_user_dependency)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador")
    return current_user

# ==================== ESTADÍSTICAS ====================
@router.get("/stats")
async def get_stats(
    db: SessionDepends,
    admin: dict = Depends(verify_admin)
):
    try:
        # Total de usuarios
        total_users = db.execute(text("SELECT COUNT(*) as count FROM users")).fetchone()
        
        # Total de sonidos
        total_sounds = db.execute(text("SELECT COUNT(*) as count FROM sounds")).fetchone()
        
        # Total de puntos
        total_points = db.execute(text("SELECT COUNT(*) as count FROM point")).fetchone()
        
        # Promedio de decibeles
        avg_decibels = db.execute(text("SELECT AVG(decibels) as avg FROM sounds")).fetchone()
        
        # Sonidos de hoy
        sounds_today = db.execute(text("""
            SELECT COUNT(*) as count FROM sounds 
            WHERE DATE(date) = CURRENT_DATE
        """)).fetchone()
        
        # Top 5 áreas más ruidosas
        top_noisy = db.execute(text("""
            SELECT p.area, AVG(s.decibels) as avg_decibels, COUNT(s.id) as count
            FROM sounds s
            JOIN point p ON s.id_point = p.id
            GROUP BY p.area
            ORDER BY avg_decibels DESC
            LIMIT 5
        """)).fetchall()
        
        return {
            "total_users": total_users.count,
            "total_sounds": total_sounds.count,
            "total_points": total_points.count,
            "avg_decibels": round(avg_decibels.avg or 0, 2),
            "sounds_today": sounds_today.count,
            "top_noisy_areas": [
                {
                    "area": row.area,
                    "avg_decibels": round(row.avg_decibels, 2),
                    "count": row.count
                }
                for row in top_noisy
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")

# ==================== USUARIOS ====================
@router.get("/users")
async def get_users(
    db: SessionDepends,
    admin: dict = Depends(verify_admin),
    limit: int = 100,
    offset: int = 0
):
    try:
        users = db.execute(text("""
            SELECT id, name, email, role    
            FROM users 
            LIMIT :limit OFFSET :offset
        """), {"limit": limit, "offset": offset}).fetchall()
        
        total = db.execute(text("SELECT COUNT(*) as count FROM users")).fetchone()
        
        return {
            "users": [
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                }
                for user in users
            ],
            "total": total.count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener usuarios: {str(e)}")

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: SessionDepends,
    admin: dict = Depends(verify_admin)
):
    try:
        # Verificar que el usuario existe
        user = db.execute(text("SELECT id FROM users WHERE id = :id"), {"id": user_id}).fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # No permitir que se elimine a sí mismo
        if user_id == admin.get("user_id"):
            raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")
        
        # Eliminar usuario
        db.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
        db.commit()
        
        return {"message": "Usuario eliminado exitosamente"}
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar usuario: {str(e)}")

@router.put("/users/{user_id}/role")
async def change_user_role(
    user_id: int,
    role: str,
    db: SessionDepends,
    admin: dict = Depends(verify_admin)
):
    try:
        if role not in ["user", "admin"]:
            raise HTTPException(status_code=400, detail="Rol inválido")
        
        user = db.execute(text("SELECT id FROM users WHERE id = :id"), {"id": user_id}).fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        db.execute(text("UPDATE users SET role = :role WHERE id = :id"), {"role": role, "id": user_id})
        db.commit()
        
        return {"message": "Rol actualizado exitosamente", "user_id": user_id, "new_role": role}
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar rol: {str(e)}")

# ==================== SONIDOS ====================
@router.get("/sounds")
async def get_sounds(
    db: SessionDepends,
    admin: dict = Depends(verify_admin),
    limit: int = 100,
    offset: int = 0
):
    try:
        sounds = db.execute(text("""
            SELECT s.id, s.decibels, s.date, s.id_point, 
                   p.floor, p.area
            FROM sounds s
            LEFT JOIN point p ON s.id_point = p.id
            ORDER BY s.date DESC
            LIMIT :limit OFFSET :offset
        """), {"limit": limit, "offset": offset}).fetchall()
        
        total = db.execute(text("SELECT COUNT(*) as count FROM sounds")).fetchone()
        
        return {
            "sounds": [
                {
                    "id": sound.id,
                    "decibels": sound.decibels,
                    "date": sound.date.isoformat(),
                    "id_point": sound.id_point,
                    "point": {
                        "floor": sound.floor,
                        "area": sound.area
                    } if sound.area else None
                }
                for sound in sounds
            ],
            "total": total.count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener sonidos: {str(e)}")

@router.delete("/sounds/{sound_id}")
async def delete_sound(
    sound_id: int,
    db: SessionDepends,
    admin: dict = Depends(verify_admin)
):
    try:
        # Verificar que el sonido existe
        sound = db.execute(text("SELECT id FROM sounds WHERE id = :id"), {"id": sound_id}).fetchone()
        
        if not sound:
            raise HTTPException(status_code=404, detail="Sonido no encontrado")
        
        # Eliminar sonido
        db.execute(text("DELETE FROM sounds WHERE id = :id"), {"id": sound_id})
        db.commit()
        
        return {"message": "Sonido eliminado exitosamente"}
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar sonido: {str(e)}")