import cv2
import numpy as np
import csv
import os

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
                        # Dibujar y etiquetar el punto
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

def pixel_to_physical(pixel_coord):
    """
    Convierte una coordenada en píxeles (relativa al punto verde) a coordenadas físicas
    en Processing (en metros) para el punto rojo, usando un mapeo lineal obtenido:
      physical_y = -0.3745*p_x - 0.01281*p_y - 29.15
      physical_z =  0.03843*p_x + 0.2577*p_y + 60.96
      Se asume physical_x = 0.
    """
    p_x, p_y = pixel_coord
    physical_y = -0.3745 * p_x - 0.01281 * p_y - 29.15
    physical_z =  0.03843 * p_x + 0.2577 * p_y + 60.96
    physical_x = 0
    return [physical_x, physical_y, physical_z]

def process_image(image_path, color_ranges, multi_detection_colors):
    """
    Lee la imagen en 'image_path', detecta los marcadores y calcula la posición física
    del punto rojo (PhysicalRed) a partir de la posición relativa respecto al punto verde.
    Devuelve la lista [x, y, z] o None si falla la detección.
    """
    frame = cv2.imread(image_path)
    if frame is None:
        print("No se pudo cargar la imagen:", image_path)
        return None
    
    detected_points, _ = detect_color_points(frame, color_ranges, multi_detection_colors)
    
    if "green" not in detected_points:
        print("No se detectó el punto verde en:", image_path)
        return None
    base = detected_points["green"]
    
    if "red" not in detected_points:
        print("No se detectó el punto rojo en:", image_path)
        return None
    red = detected_points["red"]
    # Calcula la posición relativa (en píxeles) del rojo respecto al verde
    red_rel = (red[0] - base[0], red[1] - base[1])
    red_phys = pixel_to_physical(red_rel)
    return red_phys

def main():
    # Define los rangos HSV para cada color
    color_ranges = {
        "red": [((0, 100, 100), (10, 255, 255)), ((170, 100, 100), (179, 255, 255))],  # ff0000
        "pink": [((140, 100, 100), (160, 255, 255))],   # f900ff
        "blue": [((110, 100, 100), (130, 255, 255))],   # 0000ff
        "white": [((0, 0, 200), (180, 30, 255))],         # ffffff
        "celeste": [((85, 100, 100), (95, 255, 255))],   # 00fff7
        "green": [((50, 100, 100), (70, 255, 255))]      # 12ff00
    }
    multi_detection_colors = ["celeste"]

    # Archivo CSV de entrada (con columna "path")
    input_csv = "/home/rovestrada/pose_track_ws/pose_tracking/utils/image_paths.csv"
    # Archivo CSV de salida
    output_csv = "/home/rovestrada/pose_track_ws/pose_tracking/utils/physical_red_results.csv"
    
    results = []  # Cada elemento: [point, x, y, z]
    
    # Abrir el CSV de entrada y procesar cada imagen
    with open(input_csv, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for idx, row in enumerate(reader, start=1):
            image_path = row["path"]
            # Si el path es relativo, se asume que es relativo al directorio actual
            image_path = os.path.normpath(image_path)
            red_phys = process_image(image_path, color_ranges, multi_detection_colors)
            if red_phys is not None:
                results.append([idx, red_phys[0], red_phys[1], red_phys[2]])
                print(f"Imagen {idx}: PhysicalRed =", red_phys)
            else:
                print(f"Imagen {idx}: No se pudo obtener la posición física del rojo.")
    
    # Escribir resultados en el CSV de salida
    with open(output_csv, "w", newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["point", "x", "y", "z"])
        for row in results:
            writer.writerow(row)
    
    print("Proceso completado. Resultados guardados en", output_csv)

if __name__ == "__main__":
    main()
