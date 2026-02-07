"""
Générateur de graphiques
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict
import os

class Visualizer:
    """Génère les graphiques de visualisation"""
    
    def __init__(self, output_dir='outputs'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Style
        try:
            plt.style.use('seaborn-v0_8-darkgrid')
        except:
            try:
                plt.style.use('seaborn-darkgrid')
            except:
                plt.style.use('default')
    
    def compare_strategies(self, metrics_cp, metrics_ad):
        """
        Graphique comparaison stratégies Pure CP vs Adaptive
        """
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Comparaison Stratégies: Pure CP vs Adaptive\nDurant Partition Réseau',
                    fontsize=16, fontweight='bold')
        
        operations = ['transfer', 'balance', 'history', 'payment']
        phases = ['before', 'during', 'after']
        
        for idx, operation in enumerate(operations):
            ax = axes[idx // 2, idx % 2]
            
            # Données
            cp_avail = [metrics_cp.get_availability(operation, p) for p in phases]
            ad_avail = [metrics_ad.get_availability(operation, p) for p in phases]
            
            x = np.arange(len(phases))
            width = 0.35
            
            # Barres
            bars1 = ax.bar(x - width/2, cp_avail, width, label='Pure CP', color='#e74c3c', alpha=0.8)
            bars2 = ax.bar(x + width/2, ad_avail, width, label='Adaptive', color='#3498db', alpha=0.8)
            
            ax.set_xlabel('Phase')
            ax.set_ylabel('Disponibilité (%)')
            ax.set_title(f'{operation.capitalize()}')
            ax.set_xticks(x)
            ax.set_xticklabels(['Avant', 'Durant', 'Après'])
            ax.legend()
            ax.set_ylim([0, 105])
            ax.grid(axis='y', alpha=0.3)
            
            # Ajouter valeurs sur barres
            for i, v in enumerate(cp_avail):
                if v > 0:  # Only show non-zero values
                    ax.text(i - width/2, v + 2, f'{v:.0f}%', ha='center', fontsize=9)
            for i, v in enumerate(ad_avail):
                if v > 0:  # Only show non-zero values
                    ax.text(i + width/2, v + 2, f'{v:.0f}%', ha='center', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/comparison_strategies.png', dpi=300, bbox_inches='tight')
        print(f"✓ Graphique sauvegardé: {self.output_dir}/comparison_strategies.png")
        plt.close()
    
    def plot_availability_comparison(self, metrics_cp, metrics_ad):
        """
        Graphique global de disponibilité
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Calculer disponibilité moyenne durant partition
        operations = ['transfer', 'balance', 'history', 'payment']
        
        cp_during = [metrics_cp.get_availability(op, 'during') for op in operations]
        ad_during = [metrics_ad.get_availability(op, 'during') for op in operations]
        
        x = np.arange(len(operations))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, cp_during, width, label='Pure CP',
                      color='#e74c3c', alpha=0.8)
        bars2 = ax.bar(x + width/2, ad_during, width, label='Adaptive',
                      color='#3498db', alpha=0.8)
        
        ax.set_xlabel('Opération', fontsize=12)
        ax.set_ylabel('Disponibilité Durant Partition (%)', fontsize=12)
        ax.set_title('Impact Partition Réseau sur Disponibilité\nPure CP vs Adaptive',
                    fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([op.capitalize() for op in operations])
        ax.legend(fontsize=11)
        ax.set_ylim([0, 105])
        ax.grid(axis='y', alpha=0.3)
        
        # Valeurs sur barres
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                       f'{height:.0f}%', ha='center', va='bottom', fontsize=10)
        
        # Ligne disponibilité globale moyenne
        cp_avg = np.mean(cp_during)
        ad_avg = np.mean(ad_during)
        
        ax.axhline(y=cp_avg, color='#e74c3c', linestyle='--', alpha=0.5,
                  label=f'Moy. CP: {cp_avg:.0f}%')
        ax.axhline(y=ad_avg, color='#3498db', linestyle='--', alpha=0.5,
                  label=f'Moy. Adaptive: {ad_avg:.0f}%')
        
        ax.legend(fontsize=10)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/availability_comparison.png', dpi=300, bbox_inches='tight')
        print(f"✓ Graphique sauvegardé: {self.output_dir}/availability_comparison.png")
        plt.close()
    
    def plot_24h_evolution(self, hourly_metrics: List[Dict]):
        """
        Graphique évolution CAP sur 24h
        """
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10))
        fig.suptitle('Évolution CAP sur 24 Heures - Wave Mobile Money',
                    fontsize=16, fontweight='bold')
        
        hours = [m['hour'] for m in hourly_metrics]
        loads = [m['expected_load'] for m in hourly_metrics]
        latencies = [m['network_latency'] for m in hourly_metrics]
        success_rates = [m['success_rate'] for m in hourly_metrics]
        
        # Graphique 1: Charge
        ax1.plot(hours, loads, marker='o', linewidth=2, color='#3498db', label='Charge (tx/sec)')
        ax1.fill_between(hours, loads, alpha=0.3, color='#3498db')
        ax1.set_ylabel('Transactions/sec', fontsize=11)
        ax1.set_title('Charge du Système', fontsize=12, fontweight='bold')
        ax1.grid(alpha=0.3)
        ax1.legend()
        
        # Zones heures de pointe
        ax1.axvspan(17, 19, alpha=0.2, color='red', label='Heure de pointe')
        ax1.axvspan(2, 5, alpha=0.2, color='green', label='Heure creuse')
        
        # Graphique 2: Latence
        ax2.plot(hours, latencies, marker='s', linewidth=2, color='#e74c3c', label='Latence réseau')
        ax2.fill_between(hours, latencies, alpha=0.3, color='#e74c3c')
        ax2.set_ylabel('Latence (ms)', fontsize=11)
        ax2.set_title('Latence Réseau', fontsize=12, fontweight='bold')
        ax2.grid(alpha=0.3)
        ax2.legend()
        
        # Graphique 3: Taux de succès
        ax3.plot(hours, success_rates, marker='^', linewidth=2, color='#2ecc71',
                label='Taux de succès')
        ax3.fill_between(hours, success_rates, alpha=0.3, color='#2ecc71')
        ax3.set_xlabel('Heure du jour', fontsize=11)
        ax3.set_ylabel('Taux de succès (%)', fontsize=11)
        ax3.set_title('Taux de Succès des Transactions', fontsize=12, fontweight='bold')
        ax3.set_ylim([0, 105])
        ax3.grid(alpha=0.3)
        ax3.legend()
        
        # Annotations positions CAP
        cap_positions = {
            3: 'CA',
            9: 'CP',
            18: 'AP',
            22: 'CP'
        }
        
        for hour, cap in cap_positions.items():
            ax3.annotate(f'Position: {cap}',
                        xy=(hour, success_rates[hour]),
                        xytext=(hour, success_rates[hour] - 15),
                        arrowprops=dict(arrowstyle='->', color='black', lw=1),
                        fontsize=9, ha='center',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/24h_evolution.png', dpi=300, bbox_inches='tight')
        print(f"✓ Graphique sauvegardé: {self.output_dir}/24h_evolution.png")
        plt.close()
    
    def plot_latency_comparison(self, metrics_cp, metrics_ad):
        """
        Graphique comparaison latences
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        operations = ['transfer', 'balance', 'history', 'payment']
        phases = ['before', 'during', 'after']
        
        # Données CP
        cp_data = []
        for op in operations:
            cp_data.append([metrics_cp.get_average_latency(op, p) for p in phases])
        
        # Données Adaptive
        ad_data = []
        for op in operations:
            ad_data.append([metrics_ad.get_average_latency(op, p) for p in phases])
        
        x = np.arange(len(phases))
        width = 0.15
        
        for i, op in enumerate(operations):
            offset = (i - 1.5) * width
            ax.bar(x + offset, cp_data[i], width, label=f'{op} (CP)', alpha=0.7)
            ax.bar(x + offset + width*4, ad_data[i], width, label=f'{op} (AD)', alpha=0.7)
        
        ax.set_xlabel('Phase')
        ax.set_ylabel('Latence moyenne (ms)')
        ax.set_title('Comparaison Latences: Pure CP vs Adaptive')
        ax.set_xticks(x + width*1.5)
        ax.set_xticklabels(['Avant', 'Durant', 'Après'])
        ax.legend(ncol=2, fontsize=9)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/latency_comparison.png', dpi=300, bbox_inches='tight')
        print(f"✓ Graphique sauvegardé: {self.output_dir}/latency_comparison.png")
        plt.close()