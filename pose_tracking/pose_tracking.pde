PShape base, shoulder, upArm, loArm, end;
float rotX, rotY;
float posX = 0, posY = 60, posZ = 0; // Posición inicial del extremo del brazo
float alpha, beta, gamma;
float start_square_y = 60;
float start_square_z = 0;


float F = 50;
float T = 70;
float millisOld, gTime, gSpeed = 2;

float[] Xsphere = new float[20];
float[] Ysphere = new float[20];
float[] Zsphere = new float[20];

// Variables para la rutina basada en CSV
Table physicalTable;
int currentStep = 0;
int stepDelay = 500;  // milisegundos entre cada paso
int lastUpdateTime = 0;

// Variables para interpolar
PVector prevTarget;
PVector nextTarget;

void setup() {
  size(1200, 800, OPENGL);
  
  // Load default point of view configuration
  String[] config = loadStrings("config/viewConfig.txt");
  if (config != null && config.length >= 2) {
    rotX = float(config[0]);
    rotY = float(config[1]);
    println("Vista cargada: rotX =", rotX, "rotY =", rotY);
  }


  base = loadShape("meshes/r5.obj");
  shoulder = loadShape("meshes/r1.obj");
  upArm = loadShape("meshes/r2.obj");
  loArm = loadShape("meshes/r3.obj");
  end = loadShape("meshes/r4.obj");
  
  shoulder.disableStyle();
  upArm.disableStyle();
  loArm.disableStyle(); 
  
  millisOld = millis() / 1000.0;  // Inicializar tiempo
    
  // Cargar el CSV con los resultados físicos del punto rojo
  physicalTable = loadTable("utils/physical_red_results.csv", "header");
  if (physicalTable == null) {
    println("No se pudo cargar physical_red_results.csv");
  }
  lastUpdateTime = millis();

  // Inicializar prevTarget y nextTarget a partir del primer registro (si existe)
  if (physicalTable != null && physicalTable.getRowCount() > 0) {
    TableRow row0 = physicalTable.getRow(0);
    float x0 = row0.getFloat("x");
    float y0 = row0.getFloat("y");
    float z0 = row0.getFloat("z");
    prevTarget = new PVector(x0, y0, z0);
    nextTarget = new PVector(x0, y0, z0);
    posX = x0;
    posY = y0;
    posZ = z0;
  }

}

// Save actual point of view configuration in a text file
void keyPressed() {
  if (key == 's') {
    String[] config = { str(rotX), str(rotY) };
    saveStrings("config/viewConfig.txt", config);
    println("Vista guardada: rotX =", rotX, "rotY =", rotY);
  }
}

void draw() { 

  // Actualiza la posición del efector final (punto rojo) interpolando entre datos del CSV
  updateArmPositionFromCSV();

  // Calcula la cinemática inversa usando la posición actual
  IK();

  //  writePos();
   background(32);
   smooth();
   lights();
   directionalLight(100, 102, 400, -1, 0, 0);
   
   // Actualización del historial de posiciones
   for (int i = 0; i < Xsphere.length - 1; i++) {
       Xsphere[i] = Xsphere[i + 1];
       Ysphere[i] = Ysphere[i + 1];
       Zsphere[i] = Zsphere[i + 1];
   }
   
   Xsphere[Xsphere.length - 1] = posX;
   Ysphere[Xsphere.length - 1] = posY;
   Zsphere[Zsphere.length - 1] = posZ;
   
   noStroke();
   translate(width / 2, height / 2);
   rotateX(rotX);
   rotateY(-rotY);
   scale(-4);
   
   // Dibujar trayectoria como línea continua
   stroke(#D003FF, 150);
   strokeWeight(1);  // Grosor de la línea
   for (int i = 0; i < Xsphere.length - 1; i++) {
       line(-Ysphere[i], -Zsphere[i] - 11, -Xsphere[i],
            -Ysphere[i + 1], -Zsphere[i + 1] - 11, -Xsphere[i + 1]);
   }
   noStroke();
    
   fill(#FFE308);  
   translate(0, -40, 0);   
   shape(base);
     
   translate(0, 4, 0);
   rotateY(gamma);
   shape(shoulder);
      
   translate(0, 25, 0);
   rotateY(PI);
   rotateX(alpha);
   shape(upArm);
      
   translate(0, 0, 50);
   rotateY(PI);
   rotateX(beta);
   shape(loArm);
      
   translate(0, 0, -50);
   rotateY(PI);
   shape(end);
}

void updateArmPositionFromCSV() {
  if (physicalTable == null) return;
  int rowCount = physicalTable.getRowCount();
  if (rowCount == 0) return;
  
  // Calcula el factor de interpolación (t entre 0 y 1)
  float t = (millis() - lastUpdateTime) / float(stepDelay);
  t = constrain(t, 0, 1);
  
  // Interpolación lineal entre prevTarget y nextTarget
  posX = lerp(prevTarget.x, nextTarget.x, t);
  posY = lerp(prevTarget.y, nextTarget.y, t);
  posZ = lerp(prevTarget.z, nextTarget.z, t);
  
  // Si t alcanza 1, pasa al siguiente registro del CSV
  if (t >= 1.0) {
    // Actualiza prevTarget al actual nextTarget
    prevTarget = nextTarget.copy();
    currentStep = (currentStep + 1) % rowCount;
    TableRow row = physicalTable.getRow(currentStep);
    nextTarget = new PVector(row.getFloat("x"), row.getFloat("y"), row.getFloat("z"));
    lastUpdateTime = millis();
  }
  
  println("Interpolated PhysicalRed: ", posX, posY, posZ);
}


void mouseDragged() {
    rotY -= (mouseX - pmouseX) * 0.01;
    rotX -= (mouseY - pmouseY) * 0.01;
}

void IK() {
  float X = posX;
  float Y = posY;
  float Z = posZ;

  float L = sqrt(Y * Y + X * X);
  float dia = sqrt(Z * Z + L * L);

  alpha = PI / 2 - (atan2(L, Z) + acos((T * T - F * F - dia * dia) / (-2 * F * dia)));
  beta = -PI + acos((dia * dia - T * T - F * F) / (-2 * F * T));
  gamma = atan2(Y, X);
}

void setTime() {
  float currentTime = millis() / 1000.0;
  gTime += (currentTime - millisOld) * (gSpeed / 4);
  if (gTime >= 4) gTime = 0;  
  millisOld = currentTime;
}

void writePos() {
  IK();
  setTime();
  
  // float size = 30;  // Tamaño del cuadrado reducido

  // start_square_y = 60;  // Posición inicial en Y
  // start_square_z = 0;   // Posición inicial en Z

  // Movimiento en forma de cuadrado
  //if (gTime < 1) {
  //  posY = start_square_y -size;              // Lado izquierdo
  //  posZ = start_square_z -size + (gTime * 2 * size);
  //} 
  //else if (gTime >= 1 && gTime < 2) {
  //  posY = start_square_y - size + ((gTime - 1) * 2 * size);  // Parte superior
  //  posZ = start_square_z + size;
  //} 
  //else if (gTime >= 2 && gTime < 3) {
  //  posY = start_square_y + size;               // Lado derecho
  //  posZ = start_square_z + size - ((gTime - 2) * 2 * size);
  //} 
  //else if (gTime >= 3 && gTime < 4) {
  //  posY = start_square_y + size - ((gTime - 3) * 2 * size);  // Parte inferior
  //  posZ = start_square_z - size;
  //}
}
