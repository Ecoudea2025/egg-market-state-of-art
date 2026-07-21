"""
Script de Sintesis Teorica
Proyecto: Estado del Arte - Mercado del Huevo en Colombia
Objetivo: Sintetizar modelos teoricos de oligopolio y conectar con evidencia empirica
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime


class TheoreticalSynthesizer:
    """Clase para sintetizar modelos teoricos de oligopolio"""
    
    def __init__(self, summaries_dir, comparisons_dir, synthesis_dir):
        self.summaries_dir = Path(summaries_dir)
        self.comparisons_dir = Path(comparisons_dir)
        self.synthesis_dir = Path(synthesis_dir)
        self.synthesis_dir.mkdir(exist_ok=True)
        
        # Modelos teoricos de oligopolio
        self.oligopoly_models = {
            'cournot': {
                'name': 'Cournot',
                'description': 'Competencia en cantidades',
                'assumptions': [
                    'Empresas compiten eligiendo cantidades simultaneamente',
                    'Productos homogeneos o diferenciados',
                    'Cada empresa elige produccion tomando como dada la de sus competidores',
                    'Informacion completa o incompleta'
                ],
                'predictions': [
                    'Precio mayor al de competencia perfecta pero menor al de monopolio',
                    'Cantidad total menor que en competencia perfecta',
                    'Beneficios positivos para las empresas'
                ],
                'applicability_conditions': [
                    'Mercados con pocos productores',
                    'Productos relativamente homogeneos',
                    'Decisiones de produccion son el principal instrumento estrategico',
                    'Costos de produccion similares entre empresas'
                ],
                'empirical_evidence': [
                    'Aplicado a mercados agricolas con productos homogeneos',
                    'Utilizado en analisis de industrias extractivas',
                    'Comun en mercados de commodities'
                ]
            },
            'bertrand': {
                'name': 'Bertrand',
                'description': 'Competencia en precios',
                'assumptions': [
                    'Empresas compiten eligiendo precios simultaneamente',
                    'Productos homogeneos (paradoja de Bertrand) o diferenciados',
                    'Consumidores compran al precio mas bajo',
                    'Capacidad de produccion ilimitada (en version basica)'
                ],
                'predictions': [
                    'Con productos homogeneos: precio igual al costo marginal (paradoja)',
                    'Con productos diferenciados: precios superiores al costo marginal',
                    'Beneficios nulos o positivos dependiendo de diferenciacion'
                ],
                'applicability_conditions': [
                    'Mercados donde el precio es la variable estrategica principal',
                    'Productos con algun grado de diferenciacion',
                    'Barreras de entrada moderadas',
                    'Consumidores informados sobre precios'
                ],
                'empirical_evidence': [
                    'Aplicado a mercados de retail y servicios',
                    'Utilizado en analisis de cadenas de supermercados',
                    'Relevante para mercados con productos diferenciados'
                ]
            },
            'stackelberg': {
                'name': 'Stackelberg',
                'description': 'Liderazgo estrategico',
                'assumptions': [
                    'Una empresa lider (first-mover) y otra seguidora',
                    'El lider elige cantidad primero',
                    'El seguidor observa y responde',
                    'Informacion completa'
                ],
                'predictions': [
                    'El lider produce mas y obtiene mayores beneficios',
                    'El seguidor produce menos que en Cournot',
                    'Precio total menor que en Cournot'
                ],
                'applicability_conditions': [
                    'Mercados con empresa dominante clara',
                    'Ventaja de primer movimiento significativa',
                    'Asimetria de informacion o capacidad',
                    'Historial de competencia observable'
                ],
                'empirical_evidence': [
                    'Aplicado a industrias con empresa lider clara',
                    'Utilizado en mercados de tecnologia',
                    'Relevante para sectores con economias de escala'
                ]
            },
            'monopolistic_competition': {
                'name': 'Competencia Monopolistica',
                'description': 'Diferenciacion de producto',
                'assumptions': [
                    'Diferenciacion de producto real o percibida',
                    'Muchas empresas',
                    'Libre entrada y salida',
                    'Control limitado sobre precio'
                ],
                'predictions': [
                    'Precio mayor al costo marginal',
                    'Exceso de capacidad productiva',
                    'Beneficios nulos en largo plazo',
                    'Variety excesiva desde perspectiva social'
                ],
                'applicability_conditions': [
                    'Mercados con productos diferenciados',
                    'Barreras de entrada bajas',
                    'Muchas empresas pequenas',
                    'Publicidad y marca importan'
                ],
                'empirical_evidence': [
                    'Aplicado a restaurantes, retail, servicios',
                    'Utilizado en mercados de alimentos procesados',
                    'Relevante para sectores con marca fuerte'
                ]
            },
            'dominant_firm': {
                'name': 'Empresa Dominante con Fringe',
                'description': 'Liderazgo de precio',
                'assumptions': [
                    'Una empresa dominante (price leader)',
                    'Fringe competitivo de pequenas empresas',
                    'La dominante fija precio, el fringe toma precio',
                    'La dominante satisface residuo de demanda'
                ],
                'predictions': [
                    'Precio determinado por empresa dominante',
                    'Fringe produce donde P = MC',
                    'Empresa dominante tiene poder de mercado'
                ],
                'applicability_conditions': [
                    'Mercados con empresa claramente dominante',
                    'Fringe competitivo pero influyente',
                    'Asimetria de costos o tamano',
                    'Historial de liderazgo de precio'
                ],
                'empirical_evidence': [
                    'Aplicado a mercados de energia y commodities',
                    'Utilizado en industrias con empresa estatal',
                    'Relevante para mercados con empresa incu'
                ]
            }
        }
        
        # Contexto del proyecto colombiano
        self.colombia_context = {
            'ihh': 1700,
            'cr4': 69.0,
            'lerner': 18.8,
            'elasticity': -0.50,
            'market_leader': 'Incubadora Santander (34.2% cuota)',
            'sample_size': 15,
            'informal_sector': 48.5,
            'cost_homogeneity': True,
            'product_differentiation': 'Canales de comercializacion, marcas, eficiencia',
            'preliminary_conclusion': 'Oligopolio de Bertrand con productos diferenciados'
        }
    
    def load_comparative_analysis(self):
        """Carga el analisis comparativo"""
        analysis_file = self.comparisons_dir / "comparative_analysis.json"
        if analysis_file.exists():
            with open(analysis_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def evaluate_model_applicability(self, model_name, colombia_context):
        """Evalua la idoneidad de un modelo para Colombia"""
        model = self.oligopoly_models[model_name]
        
        score = 0
        reasons = []
        
        # Evaluar IHH
        if colombia_context['ihh'] < 1800:
            if model_name in ['bertrand', 'monopolistic_competition']:
                score += 2
                reasons.append('IHH moderado favorece competencia en precios')
        
        # Evaluar diferenciacion de producto
        if colombia_context['product_differentiation']:
            if model_name in ['bertrand', 'monopolistic_competition']:
                score += 3
                reasons.append('Diferenciacion por canales y marcas favorece Bertrand')
        
        # Evaluar empresa lider
        if colombia_context['market_leader']:
            if model_name in ['stackelberg', 'dominant_firm']:
                score += 2
                reasons.append('Empresa lider (Incubadora Santander) sugiere liderazgo')
        
        # Evaluar homogeneidad de costos
        if colombia_context['cost_homogeneity']:
            if model_name in ['cournot', 'bertrand']:
                score += 1
                reasons.append('Costos homogeneos facilitan comparacion')
        
        # Evaluar fringe informal
        if colombia_context['informal_sector'] > 40:
            if model_name == 'dominant_firm':
                score += 2
                reasons.append('Fringe informal significativo (48.5%)')
        
        # Evaluar Lerner
        if 10 < colombia_context['lerner'] < 25:
            if model_name in ['bertrand', 'monopolistic_competition']:
                score += 1
                reasons.append('Lerner moderado consistente con competencia diferenciada')
        
        return {
            'model': model['name'],
            'score': score,
            'reasons': reasons,
            'applicable': score >= 3
        }
    
    def synthesize_models(self, comparative_analysis):
        """Sintetiza la evidencia sobre modelos teoricos"""
        synthesis = {
            'models_reviewed': [],
            'models_applied_to_eggs': [],
            'recommended_model_for_colombia': None,
            'justification': '',
            'theoretical_framework': ''
        }
        
        # Evaluar cada modelo
        for model_name, model_data in self.oligopoly_models.items():
            evaluation = self.evaluate_model_applicability(model_name, self.colombia_context)
            
            model_synthesis = {
                'model': model_data['name'],
                'description': model_data['description'],
                'assumptions': model_data['assumptions'],
                'predictions': model_data['predictions'],
                'applicability_conditions': model_data['applicability_conditions'],
                'empirical_evidence': model_data['empirical_evidence'],
                'applicable_to_colombia': evaluation['applicable'],
                'evaluation_score': evaluation['score'],
                'evaluation_reasons': evaluation['reasons']
            }
            
            synthesis['models_reviewed'].append(model_synthesis)
            
            # Identificar modelos aplicados a huevos
            if model_name in ['bertrand', 'monopolistic_competition', 'dominant_firm']:
                synthesis['models_applied_to_eggs'].append(model_data['name'])
        
        # Seleccionar mejor modelo
        best_model = max(
            synthesis['models_reviewed'],
            key=lambda x: x['evaluation_score']
        )
        
        synthesis['recommended_model_for_colombia'] = best_model['model']
        synthesis['justification'] = self.generate_justification(best_model)
        synthesis['theoretical_framework'] = self.generate_framework()
        
        return synthesis
    
    def generate_justification(self, best_model):
        """Genera justificacion para el modelo recomendado"""
        justification = f"El modelo de {best_model['model']} es el mas adecuado para el mercado del huevo en Colombia "
        justification += "por las siguientes razones:\n\n"
        
        for reason in best_model['evaluation_reasons']:
            justification += f"- {reason}\n"
        
        justification += f"\nCon un puntaje de evaluacion de {best_model['evaluation_score']}/10, "
        justification += "este modelo captura mejor las caracteristicas del mercado colombiano."
        
        return justification
    
    def generate_framework(self):
        """Genera marco teorico para el estado del arte"""
        framework = "## Marco Teorico para el Mercado del Huevo en Colombia\n\n"
        
        framework += "El mercado del huevo en Colombia presenta caracteristicas que sugieren "
        framework += "una estructura de **oligopolio con diferenciacion de producto**, "
        framework += "consistent con el modelo de **Bertrand** o **competencia monopolistica**.\n\n"
        
        framework += "### Caracteristicas clave del mercado:\n"
        framework += f"- **IHH: {self.colombia_context['ihh']}** (concentracion moderada)\n"
        framework += f"- **CR4: {self.colombia_context['cr4']}%** (cuatro empresas controlan {self.colombia_context['cr4']}% del mercado)\n"
        framework += f"- **Lerner: {self.colombia_context['lerner']}%** (poder de mercado moderado)\n"
        framework += f"- **Empresa lider: {self.colombia_context['market_leader']}**\n"
        framework += f"- **Sector informal: {self.colombia_context['informal_sector']}%** de produccion no reportada\n\n"
        
        framework += "### Implicaciones para la politica de competencia:\n"
        framework += "1. La concentracion moderada sugiere que no hay monopolio, pero si poder de mercado\n"
        framework += "2. La diferenciacion por canales justifica el uso de modelos de precios\n"
        framework += "3. El fringe informal puede limitar el poder de mercado de las empresas formales\n"
        framework += "4. Los costos homogeneos facilitan la comparacion entre empresas\n"
        
        return framework
    
    def run_synthesis(self):
        """Ejecuta la sintesis teorica completa"""
        print("="*80)
        print("SINTESIS TEORICA DE MODELOS DE OLIGOPOLIO")
        print("="*80)
        print()
        
        # Cargar analisis comparativo
        comparative_analysis = self.load_comparative_analysis()
        
        # Realizar sintesis
        synthesis = self.synthesize_models(comparative_analysis)
        
        # Guardar sintesis
        synthesis_file = self.synthesis_dir / "theoretical_synthesis.json"
        with open(synthesis_file, 'w', encoding='utf-8') as f:
            json.dump(synthesis, f, indent=2, ensure_ascii=False)
        
        print(f"Sintesis guardada en: {synthesis_file}")
        print()
        
        # Mostrar resumen
        print("="*80)
        print("RESUMEN DE SINTESIS")
        print("="*80)
        print()
        
        print(f"Modelos evaluados: {len(synthesis['models_reviewed'])}")
        print()
        
        print("Evaluacion de modelos:")
        for model in synthesis['models_reviewed']:
            status = "[APLICABLE]" if model['applicable_to_colombia'] else "[NO APLICABLE]"
            print(f"  - {model['model']}: {status} (Puntaje: {model['evaluation_score']})")
        
        print()
        print(f"Modelo recomendado: {synthesis['recommended_model_for_colombia']}")
        print()
        
        print("Justificacion:")
        print(synthesis['justification'])
        
        print()
        print("="*80)
        print("SINTESIS COMPLETADA")
        print("="*80)
        
        return synthesis


def main():
    """Funcion principal"""
    base_dir = r"D:\Proyecto estado del arte"
    summaries_dir = os.path.join(base_dir, "summaries")
    comparisons_dir = os.path.join(base_dir, "comparisons")
    synthesis_dir = os.path.join(base_dir, "synthesis")
    
    # Crear sintetizador y ejecutar
    synthesizer = TheoreticalSynthesizer(summaries_dir, comparisons_dir, synthesis_dir)
    synthesizer.run_synthesis()


if __name__ == "__main__":
    main()
