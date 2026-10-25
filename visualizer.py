"""
Módulo de Visualización y Reportes - Proyecto AstroShield
Genera reportes tabulares en consola, exporta métricas a JSON/CSV,
genera curvas de convergencia y mapas 2D con Matplotlib, y crea
el archivo HTML del globo terráqueo 3D interactivo con Plotly incluyendo
los continentes y países del mundo claramente visibles.
"""

import os
import json
from typing import Dict, Any, List
from models import (
    TARGET_REGIONS,
    DEBRIS_ZONES,
    OCCUPIED_POSITIONS,
    SAT_COVERAGE_KM,
    SAT_COVERAGE_DEG,
    TARGET_RADIUS_DEG,
    haversine_distance,
    geo_to_cartesian,
)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_world_borders() -> tuple:
    """Carga los límites continentales y fronteras de países desde world_borders.json."""
    json_path = os.path.join(CURRENT_DIR, "world_borders.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('lats', []), data.get('lons', [])
        except Exception:
            pass
    return [], []


def display_terminal_report(details: Dict[str, Any], history: List[Dict[str, Any]] = None) -> None:
    """
    Imprime en la terminal un reporte tabular claro y detallado
    con los resultados de la constelación y el estado de cada región.
    """
    print("\n" + "=" * 90)
    print("🛰️  CONFIGURACIÓN FINAL DE LA CONSTELACIÓN (8 SATÉLITES)")
    print("=" * 90)
    print(f"{'Satélite':^10} | {'Latitud (°)':^14} | {'Longitud (°)':^14} | {'Radio Cobertura':^18} | {'Estado':^15}")
    print("-" * 90)

    for sat in details['satellites']:
        print(f"   S{sat['id']:<6} | {sat['lat']:>12.2f}° | {sat['lon']:>12.2f}° | {SAT_COVERAGE_KM:>10.0f} km   | {'Activo':^15}")

    print("\n" + "=" * 90)
    print("🎯  ESTADO DE COBERTURA POR REGIÓN DE INTERÉS")
    print("=" * 90)
    print(f"{'Región':<30} | {'Prioridad':^10} | {'Sat. Más Cercano':^16} | {'Distancia':^12} | {'Calidad':^10} | {'Estado':^12}")
    print("-" * 90)

    for r in details['target_results']:
        status_symbol = "✅ CUBIERTA" if r['is_covered'] else "❌ DESCUBIERTA"
        sat_str = f"S{r['nearest_sat']}" if r['nearest_sat'] is not None else "Ninguno"
        dist_str = f"{r['min_dist_km']:.1f} km"
        qual_str = f"{r['quality']*100:.1f}%"
        print(f"{r['name']:<30} | {r['priority']:^10} | {sat_str:^16} | {dist_str:^12} | {qual_str:^10} | {status_symbol:^12}")

    print("\n" + "=" * 90)
    print("📊  RESUMEN GLOBAL DE RENDIMIENTO")
    print("=" * 90)
    print(f" • Puntaje de Cobertura Ponderada : {details['coverage_score']:.2f}%")
    print(f" • Fitness Neto de la Configuración: {details['fitness']:.2f}")
    print(f" • Infracciones de Restricciones  : {details['num_violations']} (Zonas de peligro evitadas)")
    print(f" • Penalización por Redundancia   : {details['redundancy_penalty']:.2f}")
    print(f" • Viabilidad de la Constelación  : {'✅ 100% VIABLE Y SEGURA' if details['is_valid'] else '⚠️ CONTIENE INFRACCIONES'}")
    print("=" * 90 + "\n")


def save_results_json(details: Dict[str, Any], filepath: str) -> None:
    """Guarda la configuración final y el desglose de métricas en formato JSON."""
    clean_details = {
        'fitness': details['fitness'],
        'coverage_score': details['coverage_score'],
        'redundancy_penalty': details['redundancy_penalty'],
        'constraint_penalty': details['constraint_penalty'],
        'num_violations': details['num_violations'],
        'is_valid': details['is_valid'],
        'satellites': details['satellites'],
        'target_results': details['target_results'],
        'violations': details['violations'],
    }
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(clean_details, f, indent=2, ensure_ascii=False)


def save_convergence_plot(history: List[Dict[str, Any]], filepath: str = "curva_convergencia.png") -> None:
    """Genera y guarda la gráfica de convergencia y diversidad usando Matplotlib."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        generations = [h['generation'] for h in history]
        best_fit = [h['best_fitness'] for h in history]
        mean_fit = [h['mean_fitness'] for h in history]
        coverage = [h['coverage_score'] for h in history]
        diversity = [h['diversity'] for h in history]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Panel 1: Curva de Fitness
        ax1.plot(generations, best_fit, label='Mejor Fitness', color='#1f77b4', lw=2.2)
        ax1.plot(generations, mean_fit, label='Fitness Promedio', color='#aec7e8', lw=1.5, linestyle='--')
        ax1.set_title('Convergencia del Algoritmo Genético', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Generación')
        ax1.set_ylabel('Fitness')
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # Panel 2: Cobertura Ponderada y Diversidad
        ax2.plot(generations, coverage, label='Cobertura Ponderada (%)', color='#2ca02c', lw=2.2)
        ax2.plot(generations, diversity, label='Diversidad Poblacional', color='#ff7f0e', lw=1.8)
        ax2.set_title('Evolución de Cobertura y Diversidad Genética', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Generación')
        ax2.set_ylabel('Valor')
        ax2.grid(True, alpha=0.3)
        ax2.legend()

        plt.tight_layout()
        plt.savefig(filepath, dpi=200)
        plt.close(fig)
        print(f"📊 Gráfica de convergencia guardada en: {filepath}")
    except Exception as e:
        print(f"⚠️ No se pudo generar la gráfica de convergencia: {e}")


def save_3d_interactive_globe(details: Dict[str, Any], filepath: str = "globo_3d_interactivo.html") -> None:
    """
    Genera un archivo HTML interactivo con el globo terrestre 3D usando Plotly,
    con los CONTINENTES, PAÍSES Y COSTAS claramente visibles.
    """
    try:
        import plotly.graph_objects as go
        import numpy as np

        fig = go.Figure()

        # 1. Esfera Oceánica Base (Azul Marino Oscuro / Espacio)
        phi = np.linspace(0, np.pi, 60)
        theta = np.linspace(0, 2 * np.pi, 90)
        phi_g, theta_g = np.meshgrid(phi, theta)
        x_e = np.sin(phi_g) * np.cos(theta_g)
        y_e = np.sin(phi_g) * np.sin(theta_g)
        z_e = np.cos(phi_g)

        fig.add_trace(go.Surface(
            x=x_e, y=y_e, z=z_e,
            surfacecolor=np.ones_like(x_e),
            colorscale=[[0, '#061325'], [1, '#0a1d37']],
            showscale=False, opacity=0.98, hoverinfo='skip', name='Océano'
        ))

        # 2. CONTINENTES Y PAÍSES (Límites Territoriales Reales del Mundo)
        b_lats, b_lons = load_world_borders()
        if b_lats and b_lons:
            bx, by, bz = [], [], []
            for la, lo in zip(b_lats, b_lons):
                if la is None or lo is None:
                    bx.append(None)
                    by.append(None)
                    bz.append(None)
                else:
                    cx, cy, cz = geo_to_cartesian(la, lo, radius=1.002)
                    bx.append(cx)
                    by.append(cy)
                    bz.append(cz)

            fig.add_trace(go.Scatter3d(
                x=bx, y=by, z=bz, mode='lines',
                line=dict(color='#38bdf8', width=2),  # Azul cian visible para costas y fronteras
                hoverinfo='skip',
                name='Continentes y Países'
            ))

        # 3. Paralelos y Meridianos Guía
        for lat in [-60, -30, 0, 30, 60]:
            lons = np.linspace(-180, 180, 80)
            gx, gy, gz = geo_to_cartesian(np.full_like(lons, lat), lons, radius=1.001)
            fig.add_trace(go.Scatter3d(
                x=gx, y=gy, z=gz, mode='lines',
                line=dict(color='#1e293b', width=1),
                hoverinfo='skip', showlegend=False
            ))

        # 4. Zonas de Desechos Espaciales (Debris)
        for dz in DEBRIS_ZONES:
            # Dibujar perímetro circular de la zona de restricción
            bearings = np.linspace(0, 2 * np.pi, 40)
            clats, clons = [], []
            d_r = np.radians(dz.radius_deg)
            c_lat_r, c_lon_r = np.radians(dz.lat), np.radians(dz.lon)
            for b in bearings:
                la_r = np.arcsin(np.sin(c_lat_r) * np.cos(d_r) + np.cos(c_lat_r) * np.sin(d_r) * np.cos(b))
                lo_r = c_lon_r + np.arctan2(np.sin(b) * np.sin(d_r) * np.cos(c_lat_r), np.cos(d_r) - np.sin(c_lat_r) * np.sin(la_r))
                clats.append(np.degrees(la_r))
                clons.append(np.degrees(lo_r))
            
            perim_x, perim_y, perim_z = geo_to_cartesian(np.array(clats), np.array(clons), radius=1.006)
            fig.add_trace(go.Scatter3d(
                x=perim_x, y=perim_y, z=perim_z, mode='lines',
                line=dict(color='#ff2a4b', width=3),
                hoverinfo='text',
                text=f"⚠️ Zona Desechos: {dz.name}<br>Centro: ({dz.lat}°, {dz.lon}°)<br>Radio: {dz.radius_deg}°",
                name=f"Desechos: {dz.name}"
            ))

            zx, zy, zz = geo_to_cartesian(dz.lat, dz.lon, radius=1.01)
            fig.add_trace(go.Scatter3d(
                x=[zx], y=[zy], z=[zz], mode='markers+text',
                marker=dict(size=7, color='#ff2a4b', symbol='diamond'),
                text=[f"💥 {dz.name}"], textposition='top center',
                textfont=dict(color='#ff8899', size=10),
                hoverinfo='skip', showlegend=False
            ))

        # 5. Posiciones Ocupadas
        for op in OCCUPIED_POSITIONS:
            bearings = np.linspace(0, 2 * np.pi, 30)
            clats, clons = [], []
            d_r = np.radians(op.radius_deg)
            c_lat_r, c_lon_r = np.radians(op.lat), np.radians(op.lon)
            for b in bearings:
                la_r = np.arcsin(np.sin(c_lat_r) * np.cos(d_r) + np.cos(c_lat_r) * np.sin(d_r) * np.cos(b))
                lo_r = c_lon_r + np.arctan2(np.sin(b) * np.sin(d_r) * np.cos(c_lat_r), np.cos(d_r) - np.sin(c_lat_r) * np.sin(la_r))
                clats.append(np.degrees(la_r))
                clons.append(np.degrees(lo_r))
            
            perim_x, perim_y, perim_z = geo_to_cartesian(np.array(clats), np.array(clons), radius=1.006)
            fig.add_trace(go.Scatter3d(
                x=perim_x, y=perim_y, z=perim_z, mode='lines',
                line=dict(color='#ffb703', width=3),
                hoverinfo='text',
                text=f"⛔ Posición Ocupada: {op.name}<br>Centro: ({op.lat}°, {op.lon}°)<br>Radio: {op.radius_deg}°",
                name=f"Ocupado: {op.name}"
            ))

            ox, oy, oz = geo_to_cartesian(op.lat, op.lon, radius=1.01)
            fig.add_trace(go.Scatter3d(
                x=[ox], y=[oy], z=[oz], mode='markers+text',
                marker=dict(size=7, color='#ffb703', symbol='square'),
                text=[f"🛑 {op.name}"], textposition='top center',
                textfont=dict(color='#ffd166', size=10),
                hoverinfo='skip', showlegend=False
            ))

        # 6. Regiones de Interés
        target_colors = {'Alta': '#00f5d4', 'Media': '#3b82f6', 'Normal': '#22c55e'}
        for r in details['target_results']:
            t_orig = next(item for item in TARGET_REGIONS if item.name == r['name'])
            tx, ty, tz = geo_to_cartesian(t_orig.lat, t_orig.lon, radius=1.012)
            col = target_colors[r['priority']]
            status_txt = "✅ Cubierta" if r['is_covered'] else "❌ Descubierta"

            # Perímetro de 300 km de la región
            bearings = np.linspace(0, 2 * np.pi, 25)
            clats, clons = [], []
            d_r = np.radians(TARGET_RADIUS_DEG)
            c_lat_r, c_lon_r = np.radians(t_orig.lat), np.radians(t_orig.lon)
            for b in bearings:
                la_r = np.arcsin(np.sin(c_lat_r) * np.cos(d_r) + np.cos(c_lat_r) * np.sin(d_r) * np.cos(b))
                lo_r = c_lon_r + np.arctan2(np.sin(b) * np.sin(d_r) * np.cos(c_lat_r), np.cos(d_r) - np.sin(c_lat_r) * np.sin(la_r))
                clats.append(np.degrees(la_r))
                clons.append(np.degrees(lo_r))
            
            t_px, t_py, t_pz = geo_to_cartesian(np.array(clats), np.array(clons), radius=1.008)
            fig.add_trace(go.Scatter3d(
                x=t_px, y=t_py, z=t_pz, mode='lines',
                line=dict(color=col, width=3),
                hoverinfo='skip', showlegend=False
            ))

            hover_str = (
                f"🎯 <b>{r['name']}</b><br>"
                f"Prioridad: {r['priority']} (Peso: {r['weight']})<br>"
                f"Estado: {status_txt}<br>"
                f"Satélite asignado: S{r['nearest_sat']}<br>"
                f"Distancia mínima: {r['min_dist_km']:.1f} km<br>"
                f"Calidad cenital: {r['quality']*100:.1f}%"
            )

            fig.add_trace(go.Scatter3d(
                x=[tx], y=[ty], z=[tz], mode='markers+text',
                marker=dict(size=9, color=col, symbol='circle'),
                text=[f"📍 {r['name']}"], textposition='top center',
                textfont=dict(color='white', size=11),
                name=f"Región: {r['name']}",
                hoverinfo='text', hovertext=hover_str
            ))

        # 7. Satélites en Órbita y Huellas
        R_ORBIT = 1.15
        for sat in details['satellites']:
            sx, sy, sz = geo_to_cartesian(sat['lat'], sat['lon'], radius=R_ORBIT)
            nx, ny, nz = geo_to_cartesian(sat['lat'], sat['lon'], radius=1.001)

            # Huella circular en superficie
            bearings = np.linspace(0, 2 * np.pi, 35)
            clats, clons = [], []
            d_r = np.radians(SAT_COVERAGE_DEG)
            s_lat_r, s_lon_r = np.radians(sat['lat']), np.radians(sat['lon'])
            for b in bearings:
                la_r = np.arcsin(np.sin(s_lat_r) * np.cos(d_r) + np.cos(s_lat_r) * np.sin(d_r) * np.cos(b))
                lo_r = s_lon_r + np.arctan2(np.sin(b) * np.sin(d_r) * np.cos(s_lat_r), np.cos(d_r) - np.sin(s_lat_r) * np.sin(la_r))
                clats.append(np.degrees(la_r))
                clons.append(np.degrees(lo_r))
            
            h_x, h_y, h_z = geo_to_cartesian(np.array(clats), np.array(clons), radius=1.004)
            fig.add_trace(go.Scatter3d(
                x=h_x, y=h_y, z=h_z, mode='lines',
                line=dict(color='#00e5ff', width=1.5, dash='solid'),
                hoverinfo='skip', showlegend=False
            ))

            # Línea de nadir
            fig.add_trace(go.Scatter3d(
                x=[sx, nx], y=[sy, ny], z=[sz, nz], mode='lines',
                line=dict(color='#00e5ff', width=2, dash='dot'),
                hoverinfo='skip', showlegend=False
            ))

            # Satélite
            fig.add_trace(go.Scatter3d(
                x=[sx], y=[sy], z=[sz], mode='markers+text',
                marker=dict(size=9, color='#ffffff', symbol='diamond', line=dict(color='#00e5ff', width=2)),
                text=[f"🛰️ S{sat['id']}"], textposition='top center',
                textfont=dict(color='#00e5ff', size=11),
                name=f"Satélite S{sat['id']}",
                hoverinfo='text',
                hovertext=f"🛰️ <b>Satélite S{sat['id']}</b><br>Latitud: {sat['lat']:.2f}°<br>Longitud: {sat['lon']:.2f}°"
            ))

        fig.update_layout(
            title=dict(
                text=f"<b>AstroShield — Simulación 3D de la Constelación</b><br>"
                     f"<span style='font-size:12px;color:#a0aec0'>Cobertura: {details['coverage_score']:.1f}% | 8 Satélites | Continentes y Países Visibles</span>",
                x=0.5, y=0.95, font=dict(family='Arial', size=18, color='white')
            ),
            paper_bgcolor='#070b19',
            scene=dict(
                xaxis=dict(showbackground=False, showgrid=False, zeroline=False, showticklabels=False, title=''),
                yaxis=dict(showbackground=False, showgrid=False, zeroline=False, showticklabels=False, title=''),
                zaxis=dict(showbackground=False, showgrid=False, zeroline=False, showticklabels=False, title=''),
                bgcolor='#070b19', aspectmode='data',
                camera=dict(eye=dict(x=1.6, y=1.4, z=1.1))
            ),
            margin=dict(l=0, r=0, b=0, t=60)
        )

        fig.write_html(filepath)
        print(f"🌍 Globo 3D interactivo con continentes exportado en: {filepath}")
    except Exception as e:
        print(f"⚠️ No se pudo generar la visualización 3D interactiva: {e}")
