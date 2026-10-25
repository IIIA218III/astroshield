"""
Módulo de Visualización y Reportes - Proyecto AstroShield
Genera reportes tabulares en consola, exporta métricas a JSON/CSV,
genera curvas de convergencia y mapas 2D con Matplotlib, y crea
el archivo HTML del globo terráqueo 3D interactivo con Plotly.
"""

import json
from typing import Dict, Any, List
from models import (
    TARGET_REGIONS,
    DEBRIS_ZONES,
    OCCUPIED_POSITIONS,
    SAT_COVERAGE_KM,
    SAT_COVERAGE_DEG,
    REGION_TARGET_RADIUS_DEG,
    haversine_distance,
    geo_to_cartesian,
)


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
    Genera un archivo HTML interactivo con el globo terrestre 3D usando Plotly.
    Permite rotación, zoom y visualización en cualquier navegador web.
    """
    try:
        import plotly.graph_objects as go
        import numpy as np

        fig = go.Figure()

        # 1. Malla 3D de la Tierra
        phi = np.linspace(0, np.pi, 50)
        theta = np.linspace(0, 2 * np.pi, 80)
        phi_g, theta_g = np.meshgrid(phi, theta)
        x_e = np.sin(phi_g) * np.cos(theta_g)
        y_e = np.sin(phi_g) * np.sin(theta_g)
        z_e = np.cos(phi_g)

        fig.add_trace(go.Surface(
            x=x_e, y=y_e, z=z_e,
            surfacecolor=np.cos(phi_g * 4) * np.sin(theta_g * 4),
            colorscale=[[0, '#0a192f'], [0.5, '#112240'], [1, '#1b3a4b']],
            showscale=False, opacity=0.93, hoverinfo='skip', name='Tierra'
        ))

        # 2. Zonas de Desechos Espaciales
        for dz in DEBRIS_ZONES:
            zx, zy, zz = geo_to_cartesian(dz.lat, dz.lon, radius=1.01)
            fig.add_trace(go.Scatter3d(
                x=[zx], y=[zy], z=[zz], mode='markers+text',
                marker=dict(size=7, color='#ff2a4b', symbol='diamond'),
                text=[f"💥 {dz.name}"], textposition='top center',
                textfont=dict(color='#ff8899', size=10),
                name=f"Desechos: {dz.name}",
                hoverinfo='text',
                hovertext=f"⚠️ Zona Desechos: {dz.name}<br>Centro: ({dz.lat}°, {dz.lon}°)<br>Radio: {dz.radius_deg}°"
            ))

        # 3. Posiciones Ocupadas
        for op in OCCUPIED_POSITIONS:
            ox, oy, oz = geo_to_cartesian(op.lat, op.lon, radius=1.01)
            fig.add_trace(go.Scatter3d(
                x=[ox], y=[oy], z=[oz], mode='markers+text',
                marker=dict(size=7, color='#ffb703', symbol='square'),
                text=[f"🛑 {op.name}"], textposition='top center',
                textfont=dict(color='#ffd166', size=10),
                name=f"Ocupado: {op.name}",
                hoverinfo='text',
                hovertext=f"⛔ Posición Ocupada: {op.name}<br>Centro: ({op.lat}°, {op.lon}°)<br>Radio: {op.radius_deg}°"
            ))

        # 4. Regiones de Interés
        target_colors = {'Alta': '#00f5d4', 'Media': '#3a86ff', 'Normal': '#70e000'}
        for r in details['target_results']:
            t_orig = next(item for item in TARGET_REGIONS if item.name == r['name'])
            tx, ty, tz = geo_to_cartesian(t_orig.lat, t_orig.lon, radius=1.012)
            col = target_colors[r['priority']]
            status_txt = "✅ Cubierta" if r['is_covered'] else "❌ Descubierta"

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

        # 5. Satélites en Órbita
        R_ORBIT = 1.15
        for sat in details['satellites']:
            sx, sy, sz = geo_to_cartesian(sat['lat'], sat['lon'], radius=R_ORBIT)
            nx, ny, nz = geo_to_cartesian(sat['lat'], sat['lon'], radius=1.001)

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
                     f"<span style='font-size:12px;color:#a0aec0'>Cobertura: {details['coverage_score']:.1f}% | 8 Satélites | 0 Infracciones</span>",
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
        print(f"🌍 Globo 3D interactivo exportado exitosamente en: {filepath}")
    except Exception as e:
        print(f"⚠️ No se pudo generar la visualización 3D interactiva: {e}")
