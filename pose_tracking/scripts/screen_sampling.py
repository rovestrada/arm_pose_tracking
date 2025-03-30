#!/usr/bin/env python
import cv2
import os
import argparse
import numpy as np

def extraer_capturas(video_path, num_capturas, output_folder):
    # Verifica que el archivo de video exista
    if not os.path.exists(video_path):
        print(f"El archivo de video '{video_path}' no existe.")
        return
    
    # Crea la carpeta de salida si no existe
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Abre el video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error al abrir el video.")
        return
    
    # Obtén el total de frames del video
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Total de frames en el video: {total_frames}")
    
    # Si el número de capturas solicitado es mayor que el total de frames,
    # se ajusta para no exceder el total de frames
    if num_capturas > total_frames:
        print("El número de capturas solicitado es mayor que la cantidad de frames del video.")
        num_capturas = total_frames
    
    # Calcula los índices de los frames equidistantes
    indices = np.linspace(0, total_frames - 1, num_capturas, dtype=int)
    print(f"Índices de frames a extraer: {indices}")
    
    # Extrae y guarda cada captura
    for i, frame_idx in enumerate(indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            print(f"Error al leer el frame {frame_idx}.")
            continue
        
        # Construye el nombre de archivo para la captura
        output_path = os.path.join(output_folder, f"captura_{i+1:03d}.jpg")
        cv2.imwrite(output_path, frame)
        print(f"Guardado {output_path}")
    
    cap.release()
    print("Extracción de capturas completada.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extraer capturas equidistantes de un video.")
    parser.add_argument("video", help="Ruta al archivo de video.")
    parser.add_argument("num", type=int, help="Cantidad de capturas a extraer.")
    parser.add_argument("--output", default="screenshots", help="Carpeta de salida para las capturas.")
    args = parser.parse_args()
    
    extraer_capturas(args.video, args.num, args.output)

# example : python3 screen_sampling.py /home/rovestrada/pose_track_ws/pose_tracking/videos/square_drawing.webm 20 --output /home/rovestrada/pose_track_ws/pose_tracking/screenshots
