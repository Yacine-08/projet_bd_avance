from typing import Dict, List

class MetricsCollector:
    """Collecte et agrège les métriques des simulations"""
    
    def __init__(self, strategy_name: str):
        self.strategy_name = strategy_name
        self.metrics = {
            'transfer': {'before': [], 'during': [], 'after': []},
            'balance': {'before': [], 'during': [], 'after': []},
            'history': {'before': [], 'during': [], 'after': []},
            'payment': {'before': [], 'during': [], 'after': []}
        }
    
    def record_transfer(self, result: Dict, phase: str):
        # Enregistrer résultat de transfert
        self.metrics['transfer'][self._normalize_phase(phase)].append(result)
    
    def record_balance_query(self, result: Dict, phase: str):
        # Enregistrer consultation solde
        self.metrics['balance'][self._normalize_phase(phase)].append(result)
    
    def record_history_query(self, result: Dict, phase: str):
        # Enregistrer consultation historique
        self.metrics['history'][self._normalize_phase(phase)].append(result)
    
    def record_payment(self, result: Dict, phase: str):
        # Enregistrer paiement
        self.metrics['payment'][self._normalize_phase(phase)].append(result)
    
    def _normalize_phase(self, phase: str) -> str:
        if 'before' in phase:
            return 'before'
        elif 'during' in phase:
            return 'during'
        elif 'after' in phase:
            return 'after'
        return 'before'
    
    def get_availability(self, operation: str, phase: str) -> float:
        # Calculer taux de disponibilité
        results = self.metrics[operation][phase]
        if not results:
            return 0.0
        
        success = sum(1 for r in results if r.get('success', False))
        return (success / len(results)) * 100
    
    def get_average_latency(self, operation: str, phase: str) -> float:
        # Calculer latence moyenne
        results = self.metrics[operation][phase]
        latencies = [r.get('latency_ms', 0) for r in results if r.get('success')]
        
        if not latencies:
            return 0.0
        
        return sum(latencies) / len(latencies)
    
    def print_summary(self):
        # Afficher résumé des métriques
        print(f"\n{'='*60}")
        print(f" MÉTRIQUES - {self.strategy_name}")
        print(f"{'='*60}\n")
        
        for operation in ['transfer', 'balance', 'history', 'payment']:
            print(f"{operation.upper()}:")
            for phase in ['before', 'during', 'after']:
                avail = self.get_availability(operation, phase)
                latency = self.get_average_latency(operation, phase)
                count = len(self.metrics[operation][phase])
                
                print(f"  {phase.capitalize():12} - "
                      f"Dispo: {avail:5.1f}% | "
                      f"Latence: {latency:6.0f}ms | "
                      f"Count: {count}")
            print()
    
    def export_to_dict(self) -> Dict:
        # Exporter métriques en dictionnaire
        return {
            'strategy': self.strategy_name,
            'availability': {
                op: {
                    phase: self.get_availability(op, phase)
                    for phase in ['before', 'during', 'after']
                }
                for op in ['transfer', 'balance', 'history', 'payment']
            },
            'latency': {
                op: {
                    phase: self.get_average_latency(op, phase)
                    for phase in ['before', 'during', 'after']
                }
                for op in ['transfer', 'balance', 'history', 'payment']
            }
        }