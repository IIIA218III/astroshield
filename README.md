# 🛰️ AstroShield — Sistema de Optimización Evolutiva de Constelaciones (Entregable 2)

Este repositorio contiene la implementación completa y modular del sistema de búsqueda evolutiva para el diseño y optimización de una constelación de **8 satélites** orientada a la observación de **6 regiones terrestres de interés estratégico**, considerando restricciones severas por acumulación de desechos espaciales (*space debris*) y zonas de exclusión por objetos orbitales preexistentes.

---

## 📋 Cumplimiento de Requerimientos del Entregable 2

| Requerimiento Solicitado | Implementación en el Código | Archivo Responsable |
| :--- | :--- | :--- |
| **1. Generar configuraciones de satélites** | Muestreo esférico uniforme no sesgado mediante proyección equivalente de Lambert: $\phi = \arcsin(U(-1, 1)) \cdot \frac{180^\circ}{\pi}$ y $\lambda \sim U(-180^\circ, 180^\circ)$. | `genetic_algorithm.py` (`create_random_individual`) |
| **2. Evaluar las configuraciones producidas** | Cálculo geodésico exacto con la fórmula del Haversine, evaluación de cobertura efectiva ($d \le 2300\text{ km}$), calidad cenital continua $Q \in [0.5, 1.0]$, ponderación por prioridades y penalización por redundancia. | `evaluator.py` (`evaluate_details`) |
| **3. Ejecutar el proceso evolutivo configurable** | Ciclo generacional completo con selección por torneo ($k=3$), cruce híbrido satelital y blend ($P_c = 0.85$), mutación gaussiana adaptativa ($P_m = 0.25$) y elitismo estricto ($N_{\text{elite}} = 4$). Parámetros configurables vía CLI. | `genetic_algorithm.py` (`evolve`) y `main.py` |
| **4. Conservar información de calidad** | Registro cronológico por época de mejor fitness, fitness promedio, porcentaje de cobertura, cantidad de infracciones, diversidad poblacional y tiempo de cómputo. Exportación automática a `historial_convergencia.csv` y `curva_convergencia.png`. | `genetic_algorithm.py` (`save_history_to_csv`) y `visualizer.py` |
| **5. Considerar restricciones espaciales y objetos** | Detección de invasión en las 3 zonas de desechos espaciales ($12^\circ, 10^\circ, 8^\circ$) y 2 posiciones ocupadas ($5^\circ$). Doble mecanismo: penalización severa con gradiente de penetración y **Operador de Reparación Espacial** radial guiado. | `models.py`, `evaluator.py` y `genetic_algorithm.py` |
| **6. Mostrar la configuración y sus resultados** | Reporte tabular en terminal (coordenadas, asignación satélite-región, distancias mínimas, calidad de señal), exportación en `configuracion_final.json`, y generación del **globo terráqueo 3D interactivo** en `globo_3d_interactivo.html` (Plotly). | `visualizer.py` y `main.py` |

---

## 📂 Estructura Modular del Proyecto

```
astroshield_ev.py/
│
├── main.py                     # Punto de entrada principal con interfaz CLI (argparse)
├── astroshield_ev.py           # Alias de ejecución directa (python astroshield_ev.py)
├── models.py                   # Modelado geodésico, constantes terrestres, regiones y zonas prohibidas
├── evaluator.py                # Evaluador de aptitud, calidad de señal y verificación de restricciones
├── genetic_algorithm.py        # Motor del algoritmo genético, operadores y registro de historial
├── visualizer.py               # Generación de reportes tabulares, gráficas 2D y globo terráqueo 3D
├── README.md                   # Documentación técnica del sistema y guía de uso
└── AstroShield_Evolucion_Constelacion.ipynb # Cuaderno interactivo de análisis
```

---

## 🚀 Guía de Ejecución

### 1. Ejecución con Parámetros por Defecto
Para ejecutar la búsqueda evolutiva con la configuración recomendada (100 generaciones, 80 individuos, restricciones y operador de reparación activos):

```bash
python main.py
```
*(O de forma equivalente:)*
```bash
python astroshield_ev.py
```

### 2. Ejecución con Parámetros Personalizados (CLI)
El sistema admite argumentos opcionales en línea de comandos para experimentar con distintas configuraciones:

```bash
# Ejemplo: 150 generaciones, población de 100 individuos, mayor tasa de mutación
python main.py --generations 150 --pop_size 100 --mutation_rate 0.30

# Ejemplo: Ejecutar en modo Etapa 1 (sin restricciones espaciales)
python main.py --no_constraints --generations 80

# Ejemplo: Desactivar el operador de reparación (solo penalización suave)
python main.py --no_repair

# Ver todas las opciones disponibles
python main.py --help
```

---

## 📊 Archivos y Evidencias Generadas Automáticamente

Al finalizar la ejecución, el sistema genera de forma automática:
1. `historial_convergencia.csv`: Registro numérico generación a generación de la aptitud, cobertura, infracciones y diversidad.
2. `configuracion_final.json`: Coordenadas precisas de los 8 satélites, distancias a cada región y calidad de señal.
3. `curva_convergencia.png`: Gráfica de evolución del fitness y cobertura a lo largo del tiempo.
4. `globo_3d_interactivo.html`: Visualización 3D interactiva sobre la Tierra. Ábrela con doble clic en cualquier navegador (Chrome, Edge, Firefox) para rotar, hacer zoom e inspeccionar la constelación.
