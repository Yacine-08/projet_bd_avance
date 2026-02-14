
import time
from typing import Dict, List
from datetime import datetime
from config.network_config import LoadProfile

class DailyLoadSimulator:
    # Simule la charge sur 24h avec variations horaires
    
    def __init__(self):
        self.current_hour = 0
        self.metrics_by_hour = {}
        
        print("[LoadSim] Daily Load Simulator initialized")
    
    def get_current_load(self, hour: int = None) -> int:
        """
        Obtenir charge actuelle (transactions/sec)
        
        Args:
            hour: Heure (0-23), si None utilise heure système
        
        Returns:
            Transactions par seconde
        """
        if hour is None:
            hour = datetime.now().hour
        
        return LoadProfile.get_load(hour)
    
    def get_current_latency(self, hour: int = None) -> float:
        """
        Obtenir latence réseau actuelle selon l'heure
        
        Args:
            hour: Heure (0-23)
        
        Returns:
            Latence en millisecondes
        """
        if hour is None:
            hour = datetime.now().hour
        
        return LoadProfile.get_latency(hour)
    
    def simulate_24h(self, transaction_executor, 
                    transactions_per_sample: int = 10) -> List[Dict]:
        """
        Simuler une journée complète de 24h
        
        Args:
            transaction_executor: Fonction qui exécute des transactions
            transactions_per_sample: Nombre de transactions par heure à simuler
        
        Returns:
            Métriques par heure
        """
        print(f"\n{'='*60}")
        print("[LoadSim] Starting 24-hour simulation")
        print(f"{'='*60}\n")
        
        hourly_metrics = []
        
        for hour in range(24):
            print(f"\n[LoadSim] Hour {hour:02d}:00")
            
            # Obtenir paramètres de l'heure
            load = self.get_current_load(hour)
            latency = self.get_current_latency(hour)
            
            print(f"[LoadSim]   Expected load: {load} tx/sec")
            print(f"[LoadSim]   Network latency: {latency}ms")
            
            # Simuler transactions pour cette heure
            hour_results = {
                'hour': hour,
                'expected_load': load,
                'network_latency': latency,
                'transactions': [],
                'success_count': 0,
                'failure_count': 0,
                'total_latency': 0
            }
            
            for i in range(transactions_per_sample):
                # Exécuter transaction
                result = transaction_executor(hour, i)
                
                hour_results['transactions'].append(result)
                
                if result.get('success'):
                    hour_results['success_count'] += 1
                    hour_results['total_latency'] += result.get('latency_ms', 0)
                else:
                    hour_results['failure_count'] += 1
            
            # Calculer métriques
            total = hour_results['success_count'] + hour_results['failure_count']
            hour_results['success_rate'] = (
                hour_results['success_count'] / total * 100 if total > 0 else 0
            )
            hour_results['avg_latency'] = (
                hour_results['total_latency'] / hour_results['success_count']
                if hour_results['success_count'] > 0 else 0
            )
            
            print(f"[LoadSim]   Results: {hour_results['success_count']}/{total} success "
                  f"({hour_results['success_rate']:.1f}%)")
            print(f"[LoadSim]   Avg latency: {hour_results['avg_latency']:.0f}ms")
            
            hourly_metrics.append(hour_results)
        
        print(f"\n{'='*60}")
        print("[LoadSim] 24-hour simulation complete")
        print(f"{'='*60}\n")
        
        return hourly_metrics
    
    def get_cap_position(self, hour: int) -> str:
        """
        Déterminer position CAP selon l'heure
        
        Returns:
            'CP' ou 'AP' ou 'CA'
        """
        load = self.get_current_load(hour)
        latency = self.get_current_latency(hour)
        
        # Nuit (charge faible, latence faible) → CA
        if 2 <= hour <= 5:
            return 'CA'
        
        # Heure de pointe (charge élevée) → AP prioritaire
        elif 17 <= hour <= 19:
            return 'AP'
        
        # Normal → CP
        else:
            return 'CP'