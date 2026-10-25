"""
Motor del Algoritmo Genético - Proyecto AstroShield
Implementa la representación cromosómica, inicialización esférica no sesgada,
operadores genéticos (torneo, cruce satelital/aritmético, mutación gaussiana,
elitismo), operador de reparación espacial y registro histórico de convergencia.
"""

import math
import random
import csv
import json
import time
from typing import List, Dict, Tuple, Any, Optional

from models import NUM_SATELLITES, haversine_distance
from evaluator import ConstellationEvaluator


class AstroShieldGA:
    def __init__(
        self,
        evaluator: ConstellationEvaluator,
        pop_size: int = 80,
        generations: int = 120,
        crossover_rate: float = 0.85,
        mutation_rate: float = 0.25,
        elite_size: int = 4,
        tournament_size: int = 3,
        use_repair_operator: bool = True,
        seed: Optional[int] = 42,
    ):
        self.evaluator = evaluator
        self.num_satellites = NUM_SATELLITES
        self.chromosome_len = self.num_satellites * 2  # 16 variables continuas
        self.pop_size = pop_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elite_size = elite_size
        self.tournament_size = tournament_size
        self.use_repair_operator = use_repair_operator

        if seed is not None:
            random.seed(seed)

        # Estructura para conservar información de cómo cambia la calidad de las soluciones
        self.history: List[Dict[str, Any]] = []

    def create_random_individual(self) -> List[float]:
        """
        Genera un individuo utilizando la proyección de área equivalente de Lambert
        para garantizar un muestreo esférico uniforme sin sesgo en los polos.
        """
        chromosome = []
        for _ in range(self.num_satellites):
            u = random.uniform(-1.0, 1.0)
            lat = math.degrees(math.asin(u))
            lon = random.uniform(-180.0, 180.0)
            chromosome.extend([lat, lon])

        if self.use_repair_operator:
            chromosome = self.repair_individual(chromosome)

        return chromosome

    def repair_individual(self, chromosome: List[float]) -> List[float]:
        """
        Operador de Reparación Espacial:
        Si un satélite cae dentro de una zona de desechos o posición ocupada,
        lo empuja radialmente hacia el borde exterior con un margen de seguridad de +2.0°.
        """
        satellites = self.evaluator.decode_chromosome(chromosome)

        for sat in satellites:
            # 1. Verificar zonas de desechos
            for dz in self.evaluator.debris_zones:
                _, dist_deg = haversine_distance(sat['lat'], sat['lon'], dz.lat, dz.lon)
                if dist_deg < dz.radius_deg:
                    margin = dz.radius_deg + 2.0
                    bearing = random.uniform(0.0, 360.0)
                    rad_b = math.radians(bearing)
                    sat['lat'] = max(-88.0, min(88.0, dz.lat + margin * math.cos(rad_b)))
                    sat['lon'] = ((dz.lon + margin * math.sin(rad_b) + 180.0) % 360.0) - 180.0

            # 2. Verificar posiciones ocupadas
            for op in self.evaluator.occupied_positions:
                _, dist_deg = haversine_distance(sat['lat'], sat['lon'], op.lat, op.lon)
                if dist_deg < op.radius_deg:
                    margin = op.radius_deg + 2.0
                    bearing = random.uniform(0.0, 360.0)
                    rad_b = math.radians(bearing)
                    sat['lat'] = max(-88.0, min(88.0, op.lat + margin * math.cos(rad_b)))
                    sat['lon'] = ((op.lon + margin * math.sin(rad_b) + 180.0) % 360.0) - 180.0

        repaired_chrom = []
        for s in satellites:
            repaired_chrom.extend([s['lat'], s['lon']])
        return repaired_chrom

    def tournament_selection(self, population: List[List[float]], fitnesses: List[float]) -> List[float]:
        """Selecciona el mejor individuo entre k candidatos elegidos al azar."""
        selected_indices = random.sample(range(len(population)), self.tournament_size)
        best_idx = max(selected_indices, key=lambda idx: fitnesses[idx])
        return list(population[best_idx])

    def crossover(self, parent1: List[float], parent2: List[float]) -> Tuple[List[float], List[float]]:
        """
        Cruce híbrido: Intercambio de satélites enteros combinado con cruce aritmético local.
        """
        if random.random() > self.crossover_rate:
            return list(parent1), list(parent2)

        child1 = list(parent1)
        child2 = list(parent2)

        for i in range(0, self.chromosome_len, 2):
            r = random.random()
            if r < 0.50:
                # Intercambiar las coordenadas del satélite completo
                child1[i:i + 2] = parent2[i:i + 2]
                child2[i:i + 2] = parent1[i:i + 2]
            elif r < 0.75:
                # Cruce aritmético / blend
                alpha = random.uniform(0.2, 0.8)
                child1[i] = alpha * parent1[i] + (1.0 - alpha) * parent2[i]
                child2[i] = (1.0 - alpha) * parent1[i] + alpha * parent2[i]
                child1[i + 1] = alpha * parent1[i + 1] + (1.0 - alpha) * parent2[i + 1]
                child2[i + 1] = (1.0 - alpha) * parent1[i + 1] + alpha * parent2[i + 1]

        return child1, child2

    def mutate(self, chromosome: List[float]) -> List[float]:
        """
        Mutación gaussiana adaptativa (σ_lat=6°, σ_lon=12°) con saltos ocasionales de exploración global.
        Asegura el acotamiento en latitud [-90, 90] y continuidad toroidal en longitud [-180, 180].
        """
        mutated = list(chromosome)

        for i in range(0, self.chromosome_len, 2):
            if random.random() < self.mutation_rate:
                if random.random() < 0.85:
                    # Ajuste fino local
                    mutated[i] += random.gauss(0.0, 6.0)     # Latitud
                    mutated[i + 1] += random.gauss(0.0, 12.0) # Longitud
                else:
                    # Salto exploratorio global
                    u = random.uniform(-1.0, 1.0)
                    mutated[i] = math.degrees(math.asin(u))
                    mutated[i + 1] = random.uniform(-180.0, 180.0)

            # Restricciones de frontera geográfica
            mutated[i] = max(-90.0, min(90.0, mutated[i]))
            mutated[i + 1] = ((mutated[i + 1] + 180.0) % 360.0) - 180.0

        if self.use_repair_operator and random.random() < 0.50:
            mutated = self.repair_individual(mutated)

        return mutated

    def compute_population_diversity(self, population: List[List[float]]) -> float:
        """
        Métrica de dispersión genética: promedio de desviaciones estándar por gen.
        """
        if not population:
            return 0.0

        num_vars = len(population[0])
        total_std = 0.0

        for var_idx in range(num_vars):
            vals = [ind[var_idx] for ind in population]
            mean_val = sum(vals) / len(vals)
            var_val = sum((v - mean_val)**2 for v in vals) / len(vals)
            total_std += math.sqrt(var_val)

        return total_std / num_vars

    def evolve(self, verbose: bool = True, log_interval: int = 10) -> Tuple[List[float], Dict[str, Any], List[Dict[str, Any]]]:
        """
        Ejecuta el proceso evolutivo completo durante la cantidad configurada de generaciones.
        Conserva información histórica y retorna la mejor solución final obtenida.
        """
        start_time = time.time()
        self.history.clear()

        # 1. Población Inicial
        population = [self.create_random_individual() for _ in range(self.pop_size)]

        best_overall_chrom = None
        best_overall_fitness = -float('inf')
        best_overall_details = None

        if verbose:
            print("=" * 78)
            print("🚀 INICIANDO BÚSQUEDA EVOLUTIVA - ASTROSHIELD")
            print(f"Población: {self.pop_size} | Generaciones: {self.generations} | "
                  f"Cruce: {self.crossover_rate:.2f} | Mutación: {self.mutation_rate:.2f} | "
                  f"Reparación: {'Activada' if self.use_repair_operator else 'Desactivada'}")
            print("=" * 78)

        for gen in range(self.generations):
            # Evaluación
            fitnesses = [self.evaluator.fitness(ind) for ind in population]

            # Ordenar población de mayor a menor fitness
            pop_fitness_pairs = sorted(zip(population, fitnesses), key=lambda x: x[1], reverse=True)
            population = [pair[0] for pair in pop_fitness_pairs]
            fitnesses = [pair[1] for pair in pop_fitness_pairs]

            best_gen_fitness = fitnesses[0]
            mean_gen_fitness = sum(fitnesses) / len(fitnesses)
            details = self.evaluator.evaluate_details(population[0])

            if best_gen_fitness > best_overall_fitness:
                best_overall_fitness = best_gen_fitness
                best_overall_chrom = list(population[0])
                best_overall_details = details

            diversity = self.compute_population_diversity(population)
            elapsed = time.time() - start_time

            # Registrar en el historial de calidad de soluciones
            gen_record = {
                'generation': gen,
                'best_fitness': round(best_gen_fitness, 4),
                'mean_fitness': round(mean_gen_fitness, 4),
                'coverage_score': round(details['coverage_score'], 2),
                'violations': details['num_violations'],
                'diversity': round(diversity, 2),
                'elapsed_sec': round(elapsed, 2),
            }
            self.history.append(gen_record)

            if verbose and (gen % log_interval == 0 or gen == self.generations - 1):
                print(f"Gen {gen:3d} | Mejor Fit: {best_gen_fitness:7.2f} | "
                      f"Cob: {details['coverage_score']:5.1f}% | "
                      f"Infracciones: {details['num_violations']:1d} | "
                      f"Div: {diversity:5.2f} | Tiempo: {elapsed:5.1f}s")

            # 2. Nueva Generación con Elitismo
            new_population = []

            # Clonar los N mejores individuos (Elitismo)
            for e in range(self.elite_size):
                new_population.append(list(population[e]))

            # Reproducción (Selección + Cruce + Mutación)
            while len(new_population) < self.pop_size:
                p1 = self.tournament_selection(population, fitnesses)
                p2 = self.tournament_selection(population, fitnesses)
                c1, c2 = self.crossover(p1, p2)
                c1 = self.mutate(c1)
                c2 = self.mutate(c2)

                new_population.append(c1)
                if len(new_population) < self.pop_size:
                    new_population.append(c2)

            population = new_population

        if verbose:
            print("=" * 78)
            print(f"🏁 PROCESO EVOLUTIVO FINALIZADO EN {time.time() - start_time:.2f} SEGUNDOS")
            print(f"Mejor Fitness Global: {best_overall_fitness:.2f} | "
                  f"Cobertura Ponderada: {best_overall_details['coverage_score']:.2f}% | "
                  f"Infracciones de Seguridad: {best_overall_details['num_violations']}")
            print("=" * 78)

        return best_overall_chrom, best_overall_details, self.history

    def save_history_to_csv(self, filepath: str) -> None:
        """Exporta el historial generacional a un archivo CSV."""
        if not self.history:
            return

        fieldnames = ['generation', 'best_fitness', 'mean_fitness', 'coverage_score',
                      'violations', 'diversity', 'elapsed_sec']

        with open(filepath, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.history)
