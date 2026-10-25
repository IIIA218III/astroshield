"""
Módulo de Modelado Físico y Geométrico - Proyecto AstroShield
Define las constantes terrestres, regiones de interés, zonas de desechos espaciales
y posiciones ocupadas, así como el cálculo de distancias geodésicas (Haversine).
"""

import math
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any

# Constantes Planetarias y de Misión
R_EARTH = 6371.0  # Radio medio de la Tierra en kilómetros
NUM_SATELLITES = 8  # Flota total disponible

# Parámetros de Cobertura Educativa
SAT_COVERAGE_KM = 2000.0  # Radio de observación superficial del satélite (~18° geocéntricos)
SAT_COVERAGE_DEG = (SAT_COVERAGE_KM / R_EARTH) * (180.0 / math.pi)

TARGET_RADIUS_KM = 300.0  # Radio de observación del centro de cada región
TARGET_RADIUS_DEG = (TARGET_RADIUS_KM / R_EARTH) * (180.0 / math.pi)
REGION_TARGET_RADIUS_DEG = TARGET_RADIUS_DEG

MAX_EFFECTIVE_DIST_KM = SAT_COVERAGE_KM + TARGET_RADIUS_KM  # 2,300.0 km

# Factores de Ponderación Numérica de Prioridades
PRIORITY_WEIGHTS = {
    'Alta': 3.0,
    'Media': 2.0,
    'Normal': 1.0
}

@dataclass
class TargetRegion:
    name: str
    lat: float
    lon: float
    priority: str
    radius_km: float = TARGET_RADIUS_KM

    @property
    def weight(self) -> float:
        return PRIORITY_WEIGHTS.get(self.priority, 1.0)


@dataclass
class RestrictedZone:
    name: str
    lat: float
    lon: float
    radius_deg: float
    zone_type: str  # 'Debris' u 'Occupied'


# 1. Regiones de Interés Oficiales del Reto
TARGET_REGIONS: List[TargetRegion] = [
    TargetRegion('Península de Yucatán, México', 20.5, -89.0, 'Alta'),
    TargetRegion('Amazonía brasileña', -3.5, -62.0, 'Alta'),
    TargetRegion('California, Estados Unidos', 36.8, -119.4, 'Media'),
    TargetRegion('Región del Sahel, África', 15.0, 0.0, 'Media'),
    TargetRegion('Japón', 36.0, 138.0, 'Media'),
    TargetRegion('Interior de Australia', -25.0, 133.0, 'Normal'),
]

# 2. Zonas Restringidas por Desechos Espaciales (Etapa 2)
DEBRIS_ZONES: List[RestrictedZone] = [
    RestrictedZone('Atlántico Norte', 45.0, -35.0, 12.0, 'Debris'),
    RestrictedZone('Pacífico Sur', -30.0, -120.0, 10.0, 'Debris'),
    RestrictedZone('Región polar norte', 78.0, 30.0, 8.0, 'Debris'),
]

# 3. Posiciones Ocupadas por Objetos Preexistentes (Etapa 2)
OCCUPIED_POSITIONS: List[RestrictedZone] = [
    RestrictedZone('Objeto A', 10.0, 45.0, 5.0, 'Occupied'),
    RestrictedZone('Objeto B', -15.0, 110.0, 5.0, 'Occupied'),
]


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, float]:
    """
    Calcula la distancia geodésica sobre el círculo máximo entre dos puntos esféricos.
    Retorna: (distancia_en_km, distancia_angular_en_grados)
    """
    lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
    lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)

    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a = math.sin(dlat / 2.0)**2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2.0)**2
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.asin(math.sqrt(a))

    dist_km = R_EARTH * c
    dist_deg = math.degrees(c)
    return dist_km, dist_deg


def geo_to_cartesian(lat: float, lon: float, radius: float = 1.0) -> Tuple[float, float, float]:
    """
    Convierte latitud y longitud en grados a coordenadas cartesianas 3D (X, Y, Z).
    """
    lat_r, lon_r = math.radians(lat), math.radians(lon)
    x = radius * math.cos(lat_r) * math.cos(lon_r)
    y = radius * math.cos(lat_r) * math.sin(lon_r)
    z = radius * math.sin(lat_r)
    return x, y, z
