#!/usr/bin/env python3
"""
AiphaLab Assistant - Helper class for CLI commands that need to analyze components and ideas.
Enhanced with LLM capabilities for deep analysis and self-improvement.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import uuid

logger = logging.getLogger(__name__)

# Configuración LLM (Modelos gratuitos via HuggingFace)
LLM_CONFIG = {
    "model": "Qwen/Qwen2.5-Coder-32B-Instruct",
    "base_url": "https://router.huggingface.co/v1",
    "max_tokens": 1000,  # Reducido para pruebas
    "temperature": 0.1,
    "timeout": 60
}

# Configuración alternativa para pruebas sin API key
TEST_CONFIG = {
    "model": "gpt-4o-mini",  # Modelo gratuito de prueba
    "base_url": "https://api.openai.com/v1",
    "max_tokens": 500,
    "temperature": 0.1,
    "timeout": 30
}


class AiphaAssistant:
    """Assistant for CLI commands that need to analyze system components and user ideas."""
    
    def __init__(self, root_path: Path, use_llm: bool = True):
        """
        Initialize the assistant with the project root path.
        
        Args:
            root_path: Path to the Aipha_0.0.2 project root
            use_llm: Whether to use LLM for enhanced analysis
        """
        self.root_path = Path(root_path)
        self.use_llm = use_llm
        self.components = self._discover_components()
        self._llm_client = None
        
        if use_llm:
            self._llm_client = self._init_llm_client()
    
    def _discover_components(self) -> Dict[str, Dict[str, Any]]:
        """
        Discover and catalog all major components in the system.
        
        Returns:
            Dictionary mapping component names to their metadata
        """
        components = {}
        
        # Core components
        core_components = {
            'context_sentinel': {
                'file': 'core/context_sentinel.py',
                'target': 'ContextSentinel',
                'purpose': 'Manages persistent memory and state tracking'
            },
            'orchestrator': {
                'file': 'core/orchestrator.py', 
                'target': 'CentralOrchestrator',
                'purpose': 'Coordinates the self-improvement cycle'
            },
            'change_proposer': {
                'file': 'core/change_proposer.py',
                'target': 'ChangeProposer',
                'purpose': 'Generates improvement proposals based on metrics'
            },
            'change_evaluator': {
                'file': 'core/change_evaluator.py',
                'target': 'ChangeEvaluator', 
                'purpose': 'Evaluates proposals for risk and impact'
            },
            'atomic_update_system': {
                'file': 'core/atomic_update_system.py',
                'target': 'AtomicUpdateSystem',
                'purpose': 'Safely applies code changes with rollback capability'
            }
        }
        
        # Trading components
        trading_components = {
            'potential_capture_engine': {
                'file': 'trading_manager/building_blocks/labelers/potential_capture_engine.py',
                'target': 'PotentialCaptureEngine',
                'purpose': 'Labels trades and manages risk/reward parameters'
            },
            'key_candle_detector': {
                'file': 'trading_manager/building_blocks/detectors/key_candle_detector.py',
                'target': 'KeyCandleDetector',
                'purpose': 'Detects key candlestick patterns for trading signals'
            }
        }
        
        # Data components
        data_components = {
            'data_processor': {
                'file': 'data_processor/data_system/main.py',
                'target': 'DataProcessor',
                'purpose': 'Fetches and processes market data'
            }
        }
        
        components.update(core_components)
        components.update(trading_components)
        components.update(data_components)
        
        return components
    
    def get_component_info(self, component_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a component.
        
        Args:
            component_name: Name of the component to analyze
            
        Returns:
            Dictionary with component information or None if not found
        """
        if component_name not in self.components:
            return {
                'error': f'Component "{component_name}" not found. Available: {", ".join(self.components.keys())}'
            }
        
        component = self.components[component_name]
        file_path = self.root_path / component['file']
        
        if not file_path.exists():
            return {
                'error': f'File not found: {file_path}'
            }
        
        try:
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract module docstring
            module_doc = self._extract_module_docstring(content)
            
            # Extract target class/function docstring
            target_doc = self._extract_target_docstring(content, component['target'])
            
            # Find dependencies
            dependencies = self._find_dependencies(content)
            
            return {
                'name': component_name,
                'file': str(file_path),
                'target': component['target'],
                'purpose': component['purpose'],
                'module_doc': module_doc,
                'target_doc': target_doc,
                'dependencies': dependencies,
                'content': content
            }
            
        except Exception as e:
            return {
                'error': f'Failed to analyze component: {str(e)}'
            }
    
    def _init_llm_client(self):
        """Inicializa cliente LLM usando misma configuración que LLMProposer."""
        try:
            from openai import OpenAI
            
            api_key = os.getenv("HUGGINGFACE_API_KEY")
            if not api_key or api_key.startswith("your_"):
                # Fallback: check MISTRAL_API_KEY for HF key
                mistral_key = os.getenv("MISTRAL_API_KEY")
                if mistral_key and mistral_key.startswith("hf_"):
                    api_key = mistral_key
            
            return OpenAI(
                base_url=LLM_CONFIG["base_url"],
                api_key=api_key
            )
        except ImportError:
            logger.warning("openai package not installed. Run: pip install openai")
            return None
        except Exception as e:
            logger.warning(f"LLM client initialization failed: {e}")
            return None
    
    def analyze_idea(self, text: str) -> Dict[str, Any]:
        """
        Analyze a user idea and suggest relevant components.
        
        Args:
            text: User's idea text
            
        Returns:
            Dictionary with analysis results
        """
        text_lower = text.lower()
        
        # Define concept mappings
        concepts = {}
        
        # Risk-related concepts
        risk_keywords = ['risk', 'stop', 'loss', 'sl', 'drawdown', 'dd']
        if any(keyword in text_lower for keyword in risk_keywords):
            concepts['risk'] = [kw for kw in risk_keywords if kw in text_lower]
        
        # Profit-related concepts
        profit_keywords = ['profit', 'target', 'tp', 'take', 'reward', 'rr']
        if any(keyword in text_lower for keyword in profit_keywords):
            concepts['profit'] = [kw for kw in profit_keywords if kw in text_lower]
        
        # Volatility concepts
        volatility_keywords = ['volatility', 'atr', 'vol', 'range', 'bollinger']
        if any(keyword in text_lower for keyword in volatility_keywords):
            concepts['volatility'] = [kw for kw in volatility_keywords if kw in text_lower]
        
        # Trade concepts
        trade_keywords = ['trade', 'position', 'entry', 'exit', 'signal']
        if any(keyword in text_lower for keyword in trade_keywords):
            concepts['trade'] = [kw for kw in trade_keywords if kw in text_lower]
        
        return {
            'original': text,
            'concepts': concepts,
            'suggestions': self._generate_suggestions(concepts)
        }
    
    def analyze_component_llm(self, component_name: str) -> Dict[str, Any]:
        """Análisis profundo de componente usando LLM."""
        # Primero intentar como componente del sistema
        basic_info = self.get_component_info(component_name)
        
        # Si no es un componente del sistema, intentar como archivo CLI
        if 'error' in basic_info:
            cli_info = self._analyze_cli_file(component_name)
            if 'error' not in cli_info:
                basic_info = cli_info
            else:
                return basic_info
        
        # Si no hay LLM disponible, retornar análisis estático
        if not self.use_llm or not self._llm_client:
            return basic_info
        
        try:
            # Construir prompt para análisis profundo
            prompt = self._build_component_analysis_prompt(basic_info)
            
            # Llamar al LLM
            response = self._llm_client.chat.completions.create(
                model=LLM_CONFIG["model"],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=LLM_CONFIG["max_tokens"],
                temperature=LLM_CONFIG["temperature"]
            )
            
            llm_analysis = response.choices[0].message.content
            
            # Parsear respuesta JSON
            llm_data = self._parse_llm_response(llm_analysis)
            
            # Combinar resultados
            return {
                **basic_info,
                'llm_analysis': llm_analysis,
                'llm_insights': llm_data.get('insights', {}),
                'llm_suggestions': llm_data.get('suggestions', []),
                'analysis_source': 'llm'
            }
            
        except Exception as e:
            logger.warning(f"LLM analysis failed for {component_name}: {e}")
            return {**basic_info, 'llm_error': str(e), 'analysis_source': 'static'}
    
    def analyze_cli_self(self) -> Dict[str, Any]:
        """Auto-análisis del CLI usando LLM."""
        cli_components = ['aiphalab/cli.py', 'aiphalab/assistant.py', 'aiphalab/formatters.py']
        
        analysis = {}
        for component_path in cli_components:
            component_name = Path(component_path).stem
            analysis[component_name] = self.analyze_component_llm(component_name)
        
        return analysis
    
    def _analyze_cli_file(self, filename: str) -> Dict[str, Any]:
        """Analiza un archivo del CLI directamente."""
        # Mapear nombres cortos a rutas completas
        cli_files = {
            'cli': 'aiphalab/cli.py',
            'assistant': 'aiphalab/assistant.py',
            'formatters': 'aiphalab/formatters.py'
        }
        
        if filename not in cli_files:
            return {'error': f'CLI file "{filename}" not found. Available: {", ".join(cli_files.keys())}'}
        
        file_path = self.root_path / cli_files[filename]
        
        if not file_path.exists():
            return {'error': f'File not found: {file_path}'}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extraer información básica
            module_doc = self._extract_module_docstring(content)
            dependencies = self._find_dependencies(content)
            
            return {
                'name': filename,
                'file': str(file_path),
                'target': 'CLI Module',
                'purpose': f'CLI component: {filename}',
                'module_doc': module_doc,
                'target_doc': 'CLI command module',
                'dependencies': dependencies,
                'content': content,
                'is_cli_file': True
            }
            
        except Exception as e:
            return {'error': f'Failed to analyze CLI file: {str(e)}'}
    
    def suggest_cli_improvements(self) -> Dict[str, Any]:
        """Sugerir mejoras para el CLI usando LLM."""
        if not self.use_llm or not self._llm_client:
            return {'error': 'LLM not available', 'suggestions': []}
        
        try:
            # Obtener análisis actual del CLI
            cli_analysis = self.analyze_cli_self()
            
            # Construir prompt para sugerencias de mejora
            prompt = self._build_improvement_suggestion_prompt(cli_analysis)
            
            # Llamar al LLM
            response = self._llm_client.chat.completions.create(
                model=LLM_CONFIG["model"],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=LLM_CONFIG["max_tokens"],
                temperature=LLM_CONFIG["temperature"]
            )
            
            suggestions_text = response.choices[0].message.content
            
            # Parsear sugerencias
            suggestions_data = self._parse_llm_response(suggestions_text)
            
            return {
                'cli_analysis': cli_analysis,
                'improvement_suggestions': suggestions_data.get('suggestions', []),
                'implementation_plan': suggestions_data.get('implementation_plan', {}),
                'priority_assessment': suggestions_data.get('priority_assessment', {}),
                'suggestions_source': 'llm'
            }
            
        except Exception as e:
            logger.error(f"Failed to generate CLI improvements: {e}")
            return {'error': str(e), 'suggestions': []}
    
    def _build_component_analysis_prompt(self, component_info: Dict[str, Any]) -> str:
        """Construye prompt para análisis profundo de componente."""
        return f"""
        Analiza profundamente este componente del sistema Aipha_0.0.2:

        COMPONENTE: {component_info['name']}
        ARCHIVO: {component_info['file']}
        PROPÓSITO: {component_info['purpose']}
        
        CÓDIGO:
        ```python
        {component_info['content'][:5000]}  # Limitar a 5000 chars para no saturar
        ```
        
        DEPENDENCIAS: {component_info['dependencies']}
        
        Por favor, proporciona un análisis detallado que incluya:
        
        1. **Arquitectura y Diseño**:
           - Patrones de diseño utilizados
           - Calidad del código (legibilidad, complejidad, cohesión)
           - Cumplimiento de principios SOLID
           - Estructura y organización
        
        2. **Funcionalidad**:
           - Qué hace el componente y cómo lo hace
           - Interacciones con otros componentes
           - Puntos fuertes y debilidades
           - Posibles bugs o problemas de performance
        
        3. **Integración**:
           - Cómo se integra con el sistema global
           - Interfaces y contratos
           - Dependencias críticas
           - Impacto de cambios
        
        4. **Mejoras Sugeridas**:
           - Optimizaciones de performance
           - Mejoras de arquitectura
           - Refactoring recomendado
           - Nuevas funcionalidades posibles
        
        Formato de respuesta (en JSON):
        {{
            "insights": {{
                "architecture": "string",
                "functionality": "string",
                "integration": "string",
                "quality": "string"
            }},
            "suggestions": [
                {{
                    "type": "performance|architecture|refactoring|feature",
                    "description": "string",
                    "priority": "high|medium|low",
                    "effort": "low|medium|high"
                }}
            ],
            "risks": ["string"],
            "opportunities": ["string"]
        }}
        """
    
    def _build_improvement_suggestion_prompt(self, cli_analysis: Dict[str, Any]) -> str:
        """Construye prompt para sugerencias de mejora del CLI."""
        return f"""
        Basado en este análisis del CLI de AiphaLab, sugiere mejoras específicas:

        ANÁLISIS ACTUAL:
        {json.dumps(cli_analysis, indent=2)}
        
        Por favor, proporciona un plan de mejoras que incluya:
        
        1. **Nuevas Funcionalidades**:
           - Comandos faltantes
           - Mejoras de UX
           - Integraciones posibles
        
        2. **Optimizaciones**:
           - Performance
           - Usabilidad
           - Mantenibilidad
        
        3. **Arquitectura**:
           - Reorganización del código
           - Mejores prácticas
           - Patrones de diseño
        
        4. **Implementación**:
           - Plan paso a paso
           - Prioridades
           - Esfuerzos estimados
        
        Formato de respuesta (en JSON):
        {{
            "suggestions": [
                {{
                    "category": "functionality|performance|architecture|ux",
                    "title": "string",
                    "description": "string",
                    "priority": "high|medium|low",
                    "effort": "low|medium|high",
                    "impact": "high|medium|low"
                }}
            ],
            "implementation_plan": {{
                "phase_1": ["string"],
                "phase_2": ["string"],
                "phase_3": ["string"]
            }},
            "priority_assessment": {{
                "quick_wins": ["string"],
                "high_impact": ["string"],
                "long_term": ["string"]
            }}
        }}
        """
    
    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Extrae JSON de la respuesta del LLM."""
        try:
            # Buscar JSON en la respuesta
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
        
        # Fallback: intentar extraer estructura básica
        try:
            lines = content.split('\n')
            suggestions = []
            for line in lines:
                if 'sugerencia' in line.lower() or 'suggestion' in line.lower():
                    suggestions.append(line.strip())
            
            return {
                "insights": {"general": content[:500]},
                "suggestions": [{"description": s, "priority": "medium"} for s in suggestions[:5]],
                "raw_response": content
            }
        except Exception:
            return {"error": "Could not parse LLM response", "raw_response": content}
    
    def _extract_module_docstring(self, content: str) -> str:
        """Extract the module-level docstring from Python code."""
        lines = content.split('\n')
        in_docstring = False
        docstring_lines = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if not in_docstring:
                    in_docstring = True
                    # Remove the opening quotes
                    docstring_lines.append(stripped[3:].strip())
                else:
                    # Closing docstring
                    break
            elif in_docstring:
                docstring_lines.append(stripped)
            elif stripped and not stripped.startswith('#'):
                # First non-comment, non-docstring line
                break
        
        return '\n'.join(docstring_lines).strip()
    
    def _extract_target_docstring(self, content: str, target_name: str) -> str:
        """Extract the docstring from a specific class or function."""
        lines = content.split('\n')
        target_found = False
        in_docstring = False
        docstring_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Look for class or function definition
            if (stripped.startswith(f'class {target_name}') or 
                stripped.startswith(f'def {target_name}(')):
                target_found = True
                continue
            
            # If we found the target, look for its docstring
            if target_found:
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    if not in_docstring:
                        in_docstring = True
                        # Remove the opening quotes
                        docstring_lines.append(stripped[3:].strip())
                    else:
                        # Closing docstring
                        break
                elif in_docstring:
                    docstring_lines.append(stripped)
                elif stripped and not stripped.startswith('#'):
                    # First non-comment line after docstring
                    break
        
        return '\n'.join(docstring_lines).strip()
    
    def _find_dependencies(self, content: str) -> List[str]:
        """Find import statements in Python code."""
        dependencies = []
        lines = content.split('\n')
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                # Extract the module name
                if stripped.startswith('import '):
                    module = stripped[7:].split()[0]
                else:  # from import
                    parts = stripped.split()
                    if len(parts) >= 3 and parts[1] != '*':
                        module = parts[1]
                    else:
                        continue
                
                # Only include local modules (not standard library or external)
                if '.' in module and not module.startswith('core.') and not module.startswith('trading_manager.'):
                    continue
                
                if module not in dependencies:
                    dependencies.append(module)
        
        return dependencies[:10]  # Limit to first 10 dependencies
    
    def _generate_suggestions(self, concepts: Dict[str, List[str]]) -> List[str]:
        """Generate suggestions based on detected concepts."""
        suggestions = []
        
        if 'risk' in concepts:
            suggestions.append("Consider modifying 'sl_factor' in potential_capture_engine")
            suggestions.append("Check ChangeProposer rules for 'Tighten Risk'")
        
        if 'profit' in concepts:
            suggestions.append("Consider modifying 'tp_factor' in potential_capture_engine")
            suggestions.append("Review reward-to-risk ratios in trading strategies")
        
        if 'volatility' in concepts:
            suggestions.append("Review 'atr_period' settings in potential_capture_engine")
            suggestions.append("Consider adding volatility filters to ConfigManager")
        
        if 'trade' in concepts:
            suggestions.append("Check trading strategy implementation in trading_manager")
            suggestions.append("Review position sizing algorithms")
        
        return suggestions


def main():
    """Test the AiphaAssistant."""
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    assistant = AiphaAssistant(project_root)
    
    print("=== AiphaAssistant Test ===")
    print(f"Discovered {len(assistant.components)} components")
    
    # Test component info
    print("\n=== Testing Component Info ===")
    info = assistant.get_component_info('context_sentinel')
    if info and 'error' not in info:
        print(f"✓ Found: {info['name']}")
        print(f"  File: {info['file']}")
        print(f"  Purpose: {info['purpose']}")
    else:
        print(f"✗ Error: {info.get('error', 'Unknown error')}")
    
    # Test idea analysis
    print("\n=== Testing Idea Analysis ===")
    test_ideas = [
        "I want to reduce risk by tightening stop losses",
        "The system should take more profits when volatility is high",
        "We need better trade entry signals"
    ]
    
    for idea in test_ideas:
        result = assistant.analyze_idea(idea)
        print(f"\nIdea: {idea}")
        print(f"Concepts: {list(result['concepts'].keys())}")
        print(f"Suggestions: {len(result['suggestions'])}")


if __name__ == '__main__':
    main()