"""
Módulo Evaluador de Aptitud y Restricciones Espaciales - Proyecto AstroShield
Evalúa la calidad de observación de la constelación, verifica infracciones espaciales
y computa la función de aptitud (fitness) multi-criterio.
"""

from typing import List, Dict, Any
from models import (
    TargetRegion,
    RestrictedZone,
    TARGET_REGIONS,
    DEBRIS_ZONES,
    OCCUPIED_POSITIONS,
    MAX_EFFECTIVE_DIST_KM,
    NUM_SATELLITES,
    haversine_distance,
)


class ConstellationEvaluator:
    def __init__(
        self,
        targets: List[TargetRegion] = None,
        debris_zones: List[RestrictedZone] = None,
        occupied_positions: List[RestrictedZone] = None,
        enable_constraints: bool = True,
    ):
        self.targets = targets if targets is not None else TARGET_REGIONS
        self.debris_zones = debris_zones if debris_zones is not None else DEBRIS_ZONES
        self.occupied_positions = occupied_positions if occupied_positions is not None else OCCUPIED_POSITIONS
        self.enable_constraints = enable_constraints

        # Suma de pesos totales para normalizar la cobertura ponderada
        self.total_target_weight = sum(t.weight for t in self.targets)

    @staticmethod
    def decode_chromosome(chromosome: List[float]) -> List[Dict[str, Any]]:
        """
        Decodifica un vector 1D de 16 variables continuas en una lista de 8 satélites:
        [{'id': 1, 'lat': ..., 'lon': ...}, ...]
        """
        satellites = []
        for i in range(0, len(chromosome), 2):
            satellites.append({
                'id': (i // 2) + 1,
                'lat': float(chromosome[i]),
                'lon': float(chromosome[i + 1]),
            })
        return satellites

    def check_constraints(self, satellites: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detecta y cuantifica las violaciones a zonas de desechos espaciales
        y posiciones ocupadas por objetos preexistentes.
        """
        if not self.enable_constraints:
            return []

        violations = []
        for sat in satellites:
            # 1. Zonas de Desechos
            for dz in self.debris_zones:
                _, dist_deg = haversine_distance(sat['lat'], sat['lon'], dz.lat, dz.lon)
                if dist_deg < dz.radius_deg:
                    violations.append({
                        'sat_id': sat['id'],
                        'zone_type': dz.zone_type,
                        'zone_name': dz.name,
                        'sat_lat': sat['lat'],
                        'sat_lon': sat['lon'],
                        'zone_lat': dz.lat,
                        'zone_lon': dz.lon,
                        'dist_deg': dist_deg,
                        'limit_deg': dz.radius_deg,
                        'penetration_deg': dz.radius_deg - dist_deg,
                    })

            # 2. Posiciones Ocupadas
            for op in self.occupied_positions:
                _, dist_deg = haversine_distance(sat['lat'], sat['lon'], op.lat, op.lon)
                if dist_deg < op.radius_deg:
                    violations.append({
                        'sat_id': sat['id'],
                        'zone_type': op.zone_type,
                        'zone_name': op.name,
                        'sat_lat': sat['lat'],
                        'sat_lon': sat['lon'],
                        'zone_lat': op.lat,
                        'zone_lon': op.lon,
                        'dist_deg': dist_deg,
                        'limit_deg': op.radius_deg,
                        'penetration_deg': op.radius_deg - dist_deg,
                    })

        return violations

    def evaluate_details(self, chromosome: List[float]) -> Dict[str, Any]:
        """
        Evaluación exhaustiva de una configuración candidata.
        Computa cobertura ponderada, calidad geométrica, penalizaciones y fitness neto.
        """
        satellites = self.decode_chromosome(chromosome)
        target_results = []
        weighted_quality_sum = 0.0

        for t in self.targets:
            best_dist_km = float('inf')
            best_sat_id = None

            for sat in satellites:
                d_km, _ = haversine_distance(sat['lat'], sat['lon'], t.lat, t.lon)
                if d_km < best_dist_km:
                    best_dist_km = d_km
                    best_sat_id = sat['id']

            is_covered = (best_dist_km <= MAX_EFFECTIVE_DIST_KM)
            if is_covered:
                # Calidad decrece linealmente desde el cenit (d=0 -> 1.0) hasta el borde (d=max -> 0.5)
                quality = 1.0 - 0.5 * (best_dist_km / MAX_EFFECTIVE_DIST_KM)
            else:
                quality = 0.0

            weighted_quality_sum += t.weight * quality

            target_results.append({
                'name': t.name,
                'priority': t.priority,
                'weight': t.weight,
                'nearest_sat': best_sat_id,
                'min_dist_km': best_dist_km,
                'is_covered': is_covered,
                'quality': quality,
            })

        # Cobertura ponderada en porcentaje [0, 100]
        coverage_score = (weighted_quality_sum / self.total_target_weight) * 100.0

        # Verificación de restricciones
        violations = self.check_constraints(satellites)

        # Penalización por redundancia (evita que múltiples satélites se apilen a menos de 800 km)
        redundancy_penalty = 0.0
        for i in range(len(satellites)):
            for j in range(i + 1, len(satellites)):
                d_km, _ = haversine_distance(
                    satellites[i]['lat'], satellites[i]['lon'],
                    satellites[j]['lat'], satellites[j]['lon']
                )
                if d_km < 800.0:
                    redundancy_penalty += (800.0 - d_km) / 200.0

        # Penalización por infracción de restricciones espaciales
        constraint_penalty = 0.0
        for v in violations:
            # Penalización severa de 200 puntos base + gradiente de penetración hacia el núcleo
            constraint_penalty += 200.0 + 50.0 * (v['penetration_deg'] / v['limit_deg'])

        # Fitness neto
        fitness = coverage_score - redundancy_penalty - constraint_penalty

        return {
            'fitness': fitness,
            'coverage_score': coverage_score,
            'redundancy_penalty': redundancy_penalty,
            'constraint_penalty': constraint_penalty,
            'num_violations': len(violations),
            'violations': violations,
            'target_results': target_results,
            'satellites': satellites,
            'is_valid': (len(violations) == 0),
        }

    def fitness(self, chromosome: List[float]) -> float:
        """Función de aptitud simplificada y rápida para el ciclo evolutivo."""
        res = self.evaluate_details(chromosome)
        return res['fitness']
