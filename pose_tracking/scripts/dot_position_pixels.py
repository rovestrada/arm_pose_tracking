import cv2
import numpy as np

def detect_color_points(frame, color_ranges, multi_detection_colors=None):
    """
    Detecta los puntos de color en la imagen y devuelve un diccionario.
    Para los colores listados en multi_detection_colors se retornará una lista
    de centroides; para el resto se retorna un único punto (el de mayor área).
    Además, se dibuja el punto y se etiqueta el color.
    """
    if multi_detection_colors is None:
        multi_detection_colors = []
    
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    detected_points = {}
    
    for color, ranges in color_ranges.items():
        mask = None
        # Combina todos los rangos para ese color (por ejemplo, el rojo usa 2 rangos)
        for (lower, upper) in ranges:
            lower = np.array(lower, dtype=np.uint8)
            upper = np.array(upper, dtype=np.uint8)
            current_mask = cv2.inRange(hsv, lower, upper)
            if mask is None:
                mask = current_mask
            else:
                mask = cv2.bitwise_or(mask, current_mask)
        
        # Encontrar contornos en la máscara
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Si el color debe tener múltiples detecciones, se procesan todos los contornos
        if color in multi_detection_colors:
            points = []
            for cnt in contours:
                if cv2.contourArea(cnt) > 10:  # Umbral para evitar falsos positivos (ajustable)
                    M = cv2.moments(cnt)
                    if M["m00"] != 0:
                        cX = int(M["m10"] / M["m00"])
                        cY = int(M["m01"] / M["m00"])
                        points.append((cX, cY))
                        # Dibujar el punto y etiquetar con el nombre del color
                        cv2.circle(frame, (cX, cY), 5, (255, 255, 255), -1)
                        cv2.putText(frame, color, (cX + 5, cY + 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            if points:
                detected_points[color] = points
        else:
            # Para otros colores se toma el contorno de mayor área
            if contours:
                c = max(contours, key=cv2.contourArea)
                M = cv2.moments(c)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    detected_points[color] = (cX, cY)
                    cv2.circle(frame, (cX, cY), 5, (255, 255, 255), -1)
                    cv2.putText(frame, color, (cX + 5, cY + 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    return detected_points, frame

def main():
    # Rangos HSV basados en los colores proporcionados:
    # Los valores pueden necesitar ajuste dependiendo de las condiciones de iluminación.
    color_ranges = {
        "red": [((0, 100, 100), (10, 255, 255)), ((170, 100, 100), (179, 255, 255))],  # ff0000
        "pink": [((140, 100, 100), (160, 255, 255))],   # f900ff
        "blue": [((110, 100, 100), (130, 255, 255))],   # 0000ff
        "white": [((0, 0, 200), (180, 30, 255))],         # ffffff
        "celeste": [((85, 100, 100), (95, 255, 255))],   # 00fff7
        "green": [((50, 100, 100), (70, 255, 255))]      # 12ff00
    }
    
    # Se especifica que se desea detectar múltiples puntos para "celeste"
    multi_detection_colors = ["celeste"]
    
    # Ruta de la imagen
    image_path = "/home/rovestrada/pose_track_ws/pose_tracking/screenshots/dotted/captura_001_dotted.jpg"
    frame = cv2.imread(image_path)
    if frame is None:
        print("No se pudo cargar la imagen desde:", image_path)
        return
    
    # Detectar puntos de color
    detected_points, annotated_frame = detect_color_points(frame, color_ranges, multi_detection_colors)
    print("Puntos detectados:", detected_points)
    
    # Calcular posiciones relativas respecto al origen (punto verde)
    relative_positions = {}
    if "green" in detected_points:
        base = detected_points["green"]
        for color, points in detected_points.items():
            if isinstance(points, list):
                relative_positions[color] = [(p[0] - base[0], p[1] - base[1]) for p in points]
            else:
                relative_positions[color] = (points[0] - base[0], points[1] - base[1])
        print("Posiciones relativas (en píxeles):", relative_positions)
    else:
        print("No se detectó el punto verde de la base.")
    
    # Imprimir (anotar) en la imagen las posiciones relativas
    # Se utiliza la información en detected_points para posicionar el texto
    for color, rel in relative_positions.items():
        if isinstance(rel, list):
            # Para colores con múltiples detecciones (ej. celeste)
            for idx, (dx, dy) in enumerate(rel):
                # Obtener posición original para ubicar el texto
                (x, y) = detected_points[color][idx]
                text = f"{color}:({dx},{dy})"
                cv2.putText(annotated_frame, text, (x + 5, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        else:
            (dx, dy) = rel
            (x, y) = detected_points[color]
            text = f"{color}:({dx},{dy})"
            cv2.putText(annotated_frame, text, (x + 5, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    cv2.imshow("Marcadores detectados y posiciones relativas", annotated_frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
