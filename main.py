"""
Sistema Evolutivo AstroShield - Entregable 2
Punto de entrada principal para ejecutar el proceso de búsqueda,
evaluar configuraciones, respetar restricciones espaciales y generar reportes.
"""

import sys
import os
import argparse

# Asegurar que el directorio actual esté en sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from models import TARGET_REGIONS, DEBRIS_ZONES, OCCUPIED_POSITIONS
from evaluator import ConstellationEvaluator
from genetic_algorithm import AstroShieldGA
from visualizer import (
    display_terminal_report,
    save_results_json,
    save_convergence_plot,
    save_3d_interactive_globe,
)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="AstroShield: Sistema de Optimización Evolutiva de Constelaciones de Satélites."
    )
    parser.add_argument(
        "--generations", type=int, default=100,
        help="Número de generaciones/iteraciones a evolucionar (por defecto: 100)"
    )
    parser.add_argument(
        "--pop_size", type=int, default=80,
        help="Tamaño de la población de constelaciones (por defecto: 80)"
    )
    parser.add_argument(
        "--crossover_rate", type=float, default=0.85,
        help="Probabilidad de cruce entre progenitores (por defecto: 0.85)"
    )
    parser.add_argument(
        "--mutation_rate", type=float, default=0.25,
        help="Probabilidad de mutación genética (por defecto: 0.25)"
    )
    parser.add_argument(
        "--elite_size", type=int, default=4,
        help="Número de mejores individuos transferidos intactos por generación (por defecto: 4)"
    )
    parser.add_argument(
        "--tournament_size", type=int, default=3,
        help="Tamaño del torneo para selección de padres (por defecto: 3)"
    )
    parser.add_argument(
        "--no_repair", action="store_true",
        help="Desactiva el operador de reparación espacial (usa únicamente penalización suave)"
    )
    parser.add_argument(
        "--no_constraints", action="store_true",
        help="Ejecuta la optimización sin restricciones espaciales (Modo Etapa 1 base)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Semilla aleatoria para reproducibilidad científica (por defecto: 42)"
    )
    parser.add_argument(
        "--output_dir", type=str, default=CURRENT_DIR,
        help="Directorio donde se guardarán los reportes, gráficas y archivos generados"
    )
    return parser.parse_args()


def main():
    args = parse_arguments()

    print("\n" + "=" * 78)
    print("      🛰️   SISTEMA EVOLUTIVO ASTROSHIELD — ENTREGABLE 2   🛰️")
    print("=" * 78)
    print(f"Directorio de salida: {args.output_dir}")
    print(f"Modo de restricciones: {'Desactivadas (Etapa 1)' if args.no_constraints else 'Activadas (Etapa 2 con Zonas de Peligro)'}")

    # 1. Instanciar el Evaluador
    evaluator = ConstellationEvaluator(
        targets=TARGET_REGIONS,
        debris_zones=[] if args.no_constraints else DEBRIS_ZONES,
        occupied_positions=[] if args.no_constraints else OCCUPIED_POSITIONS,
        enable_constraints=(not args.no_constraints),
    )

    # 2. Instanciar y Configurar el Algoritmo Genético
    ga = AstroShieldGA(
        evaluator=evaluator,
        pop_size=args.pop_size,
        generations=args.generations,
        crossover_rate=args.crossover_rate,
        mutation_rate=args.mutation_rate,
        elite_size=args.elite_size,
        tournament_size=args.tournament_size,
        use_repair_operator=(not args.no_repair and not args.no_constraints),
        seed=args.seed,
    )

    # 3. Ejecutar el Proceso de Búsqueda
    best_chrom, best_details, history = ga.evolve(verbose=True, log_interval=15)

    # 4. Mostrar Resultados en Consola
    display_terminal_report(best_details, history)

    # 5. Conservar Información y Exportar Resultados
    os.makedirs(args.output_dir, exist_ok=True)

    # A) Historial de Convergencia (CSV)
    csv_path = os.path.join(args.output_dir, "historial_convergencia.csv")
    ga.save_history_to_csv(csv_path)
    print(f"📁 Historial de convergencia exportado a: {csv_path}")

    # B) Configuración Final Óptima (JSON)
    json_path = os.path.join(args.output_dir, "configuracion_final.json")
    save_results_json(best_details, json_path)
    print(f"📁 Configuración final guardada en: {json_path}")

    # C) Gráfica de Convergencia (PNG)
    plot_path = os.path.join(args.output_dir, "curva_convergencia.png")
    save_convergence_plot(history, plot_path)

    # D) Simulación 3D Interactiva del Globo (HTML)
    globe_path = os.path.join(args.output_dir, "globo_3d_interactivo.html")
    save_3d_interactive_globe(best_details, globe_path)

    print("\n✅ Todos los entregables y evidencias fueron generados satisfactoriamente.\n")


if __name__ == "__main__":
    main()
