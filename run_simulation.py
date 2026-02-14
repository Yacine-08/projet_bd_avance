
import json
import time
from models.node import Node, NodeRole
from models.account import Account
from simulation.network_simulator import NetworkSimulator
from simulation.partition_simulator import PartitionSimulator
from simulation.daily_load_simulator import DailyLoadSimulator
from services.transfer_service import TransferService
from services.balance_service import BalanceService
from services.history_service import HistoryService
from services.payment_service import PaymentService
from strategies.pure_cp_strategy import PureCPStrategy
from strategies.adaptive_strategy import AdaptiveStrategy
from analysis.metrics_collector import MetricsCollector
from analysis.visualizer import Visualizer

def load_initial_data():
    # Charger données initiales
    with open('data/users.json', 'r') as f:
        users_data = json.load(f)
    
    with open('data/initial_transactions.json', 'r') as f:
        transactions_data = json.load(f)
    
    return users_data, transactions_data

def initialize_nodes(users_data, transactions_data):
    # Initialiser les nœuds avec données
    # Créer nœuds
    dakar = Node('DAKAR', 'Dakar', NodeRole.MASTER, (14.7167, -17.4677))
    saint_louis = Node('SAINT_LOUIS', 'Saint-Louis', NodeRole.REPLICA_RW, (16.0179, -16.5119))
    ziguinchor = Node('ZIGUINCHOR', 'Ziguinchor', NodeRole.REPLICA_ANALYTICS, (12.5833, -16.2667))
    
    # Charger comptes sur tous les nœuds
    for node in [dakar, saint_louis, ziguinchor]:
        for user in users_data:
            node.accounts[user['user_id']] = user['balance']
        
        for tx in transactions_data:
            node.transactions.append(tx)
    
    # Initialiser can_reach (tous peuvent se joindre au début)
    for node in [dakar, saint_louis, ziguinchor]:
        node.can_reach = {
            'DAKAR': True,
            'SAINT_LOUIS': True,
            'ZIGUINCHOR': True
        }
    
    return dakar, saint_louis, ziguinchor

def run_partition_comparison():
    """
    Simulation complète: Comparaison stratégie Pure CP vs Adaptive
    lors d'une partition réseau
    """
    print("\n" + "="*80)
    print(" SIMULATION: PARTITION RÉSEAU - STRATÉGIE PURE CP VS ADAPTIVE")
    print("="*80 + "\n")
    
    # Charger données
    users_data, transactions_data = load_initial_data()
    
    # ==================== SIMULATION 1: PURE CP ====================
    print("\n" + "-"*80)
    print(" SIMULATION 1: STRATÉGIE PURE CP")
    print("-"*80 + "\n")
    
    # Initialiser
    dakar_cp, saint_louis_cp, ziguinchor_cp = initialize_nodes(users_data, transactions_data)
    network_cp = NetworkSimulator('normal')
    
    # Services
    transfer_cp = TransferService(network_cp)
    balance_cp = BalanceService(network_cp)
    history_cp = HistoryService(network_cp)
    payment_cp = PaymentService(network_cp)
    
    strategy_cp = PureCPStrategy(transfer_cp, balance_cp, history_cp, payment_cp)
    
    # Métriques
    metrics_cp = MetricsCollector("Pure CP")
    
    # Avant partition
    print("\n[Phase 1] AVANT PARTITION - Opérations normales\n")
    
    result = strategy_cp.execute_transfer(
        'user_001', 'user_002', 3000,
        saint_louis_cp, dakar_cp, [saint_louis_cp, ziguinchor_cp]
    )
    metrics_cp.record_transfer(result, phase='before_partition')
    
    result = strategy_cp.execute_balance_query('user_001', saint_louis_cp, dakar_cp)
    metrics_cp.record_balance_query(result, phase='before_partition')
    
    result = strategy_cp.execute_history_query('user_001', saint_louis_cp, dakar_cp)
    metrics_cp.record_history_query(result, phase='before_partition')
    
    result = strategy_cp.execute_payment(
        'user_001', 'SENELEC', 6000,
        saint_louis_cp, dakar_cp, [saint_louis_cp, ziguinchor_cp]
    )
    metrics_cp.record_payment(result, phase='before_partition')
    
    # CRÉER PARTITION
    print("\n[Phase 2] CRÉATION PARTITION Dakar ↔ Ziguinchor\n")
    partition_cp = PartitionSimulator(network_cp, [dakar_cp, saint_louis_cp, ziguinchor_cp])
    partition_cp.create_partition('DAKAR', 'ZIGUINCHOR')
    
    time.sleep(1)
    
    # Pendant partition (depuis Ziguinchor isolé)
    print("\n[Phase 3] DURANT PARTITION - Tentatives depuis Ziguinchor\n")
    
    result = strategy_cp.execute_transfer(
        'user_003', 'user_004', 2000,
        ziguinchor_cp, dakar_cp, [saint_louis_cp, ziguinchor_cp]
    )
    metrics_cp.record_transfer(result, phase='during_partition')
    
    result = strategy_cp.execute_balance_query('user_003', ziguinchor_cp, dakar_cp)
    metrics_cp.record_balance_query(result, phase='during_partition')
    
    result = strategy_cp.execute_history_query('user_003', ziguinchor_cp, dakar_cp)
    metrics_cp.record_history_query(result, phase='during_partition')
    
    result = strategy_cp.execute_payment(
        'user_003', 'SENELEC', 6000,
        ziguinchor_cp, dakar_cp, [saint_louis_cp, ziguinchor_cp]
    )
    metrics_cp.record_payment(result, phase='during_partition')
    
    # Résoudre partition
    time.sleep(2)
    partition_cp.heal_partition('DAKAR', 'ZIGUINCHOR')
    
    # Après partition
    print("\n[Phase 4] APRÈS PARTITION - Opérations normales reprennent\n")
    
    result = strategy_cp.execute_transfer(
        'user_003', 'user_004', 2000,
        ziguinchor_cp, dakar_cp, [saint_louis_cp, ziguinchor_cp]
    )
    metrics_cp.record_transfer(result, phase='after_partition')
    
    result = strategy_cp.execute_balance_query('user_003', ziguinchor_cp, dakar_cp)
    metrics_cp.record_balance_query(result, phase='after_partition')
    
    result = strategy_cp.execute_history_query('user_003', ziguinchor_cp, dakar_cp)
    metrics_cp.record_history_query(result, phase='after_partition')
    
    result = strategy_cp.execute_payment(
        'user_003', 'SENELEC', 6000,
        ziguinchor_cp, dakar_cp, [saint_louis_cp, ziguinchor_cp]
    )
    metrics_cp.record_payment(result, phase='after_partition')
    
    # ==================== SIMULATION 2: ADAPTIVE ====================
    print("\n" + "-"*80)
    print(" SIMULATION 2: STRATÉGIE ADAPTIVE")
    print("-"*80 + "\n")
    
    # Réinitialiser
    dakar_ad, saint_louis_ad, ziguinchor_ad = initialize_nodes(users_data, transactions_data)
    network_ad = NetworkSimulator('normal')
    
    # Services
    transfer_ad = TransferService(network_ad)
    balance_ad = BalanceService(network_ad)
    history_ad = HistoryService(network_ad)
    payment_ad = PaymentService(network_ad)
    
    strategy_ad = AdaptiveStrategy(transfer_ad, balance_ad, history_ad, payment_ad)
    
    # Métriques
    metrics_ad = MetricsCollector("Adaptive")
    
    # Avant partition
    print("\n[Phase 1] AVANT PARTITION - Opérations normales\n")
    
    result = strategy_ad.execute_transfer(
        'user_001', 'user_002', 3000,
        saint_louis_ad, dakar_ad, [saint_louis_ad, ziguinchor_ad]
    )
    metrics_ad.record_transfer(result, phase='before_partition')
    
    result = strategy_ad.execute_balance_query(
        'user_001', saint_louis_ad, dakar_ad, context='display'
    )
    metrics_ad.record_balance_query(result, phase='before_partition')
    
    result = strategy_ad.execute_history_query('user_001', saint_louis_ad, dakar_ad)
    metrics_ad.record_history_query(result, phase='before_partition')
    
    result = strategy_ad.execute_payment(
        'user_001', 'Orange', 6000,
        saint_louis_ad, dakar_ad, [saint_louis_ad, ziguinchor_ad]
    )
    metrics_ad.record_payment(result, phase='before_partition')
    
    # CRÉER PARTITION
    print("\n[Phase 2] CRÉATION PARTITION Dakar ↔ Ziguinchor\n")
    partition_ad = PartitionSimulator(network_ad, [dakar_ad, saint_louis_ad, ziguinchor_ad])
    partition_ad.create_partition('DAKAR', 'ZIGUINCHOR')
    
    time.sleep(1)
    
    # Pendant partition (depuis Ziguinchor isolé)
    print("\n[Phase 3] DURANT PARTITION - Tentatives depuis Ziguinchor\n")
    
    result = strategy_ad.execute_transfer(
        'user_003', 'user_004', 2000,
        ziguinchor_ad, dakar_ad, [saint_louis_ad, ziguinchor_ad]
    )
    metrics_ad.record_transfer(result, phase='during_partition')
    
    result = strategy_ad.execute_balance_query(
        'user_003', ziguinchor_ad, dakar_ad, context='display'
    )
    metrics_ad.record_balance_query(result, phase='during_partition')
    
    result = strategy_ad.execute_history_query('user_003', ziguinchor_ad, dakar_ad)
    metrics_ad.record_history_query(result, phase='during_partition')
    
    result = strategy_ad.execute_payment(
        'user_003', 'Orange', 6000,  # Montant >5000 pour tester CP strict en partition
        ziguinchor_ad, dakar_ad, [saint_louis_ad, ziguinchor_ad]
    )
    metrics_ad.record_payment(result, phase='during_partition')
    
    # Résoudre partition
    time.sleep(2)
    partition_ad.heal_partition('DAKAR', 'ZIGUINCHOR')
    
    # Après partition
    print("\n[Phase 4] APRÈS PARTITION - Opérations normales reprennent\n")
    
    result = strategy_ad.execute_transfer(
        'user_003', 'user_004', 2000,
        ziguinchor_ad, dakar_ad, [saint_louis_ad, ziguinchor_ad]
    )
    metrics_ad.record_transfer(result, phase='after_partition')
    
    result = strategy_ad.execute_balance_query(
        'user_003', ziguinchor_ad, dakar_ad, context='display'
    )
    metrics_ad.record_balance_query(result, phase='after_partition')
    
    result = strategy_ad.execute_history_query('user_003', ziguinchor_ad, dakar_ad)
    metrics_ad.record_history_query(result, phase='after_partition')
    
    result = strategy_ad.execute_payment(
        'user_003', 'Orange', 6000,
        ziguinchor_ad, dakar_ad, [saint_louis_ad, ziguinchor_ad]
    )
    metrics_ad.record_payment(result, phase='after_partition')
    
    # ==================== COMPARAISON ====================
    print("\n" + "="*80)
    print(" COMPARAISON DES RÉSULTATS")
    print("="*80 + "\n")
    
    # Afficher métriques
    metrics_cp.print_summary()
    print()
    metrics_ad.print_summary()
    
    # Générer graphiques
    visualizer = Visualizer()
    visualizer.compare_strategies(metrics_cp, metrics_ad)
    visualizer.plot_availability_comparison(metrics_cp, metrics_ad)
    
    print("\n✓ Simulation terminée - Graphiques générés dans /outputs/")

def run_daily_simulation():
    # Simulation: Évolution CAP sur 24h

    print("\n" + "="*80)
    print(" SIMULATION: ÉVOLUTION CAP SUR 24 HEURES")
    print("="*80 + "\n")
    
    # Initialiser
    users_data, transactions_data = load_initial_data()
    dakar, saint_louis, ziguinchor = initialize_nodes(users_data, transactions_data)
    network = NetworkSimulator('normal')
    
    # Services
    transfer = TransferService(network)
    balance = BalanceService(network)
    
    strategy = AdaptiveStrategy(
        transfer, balance,
        HistoryService(network),
        PaymentService(network)
    )
    
    # Simulateur
    load_sim = DailyLoadSimulator()
    
    # Fonction d'exécution de transaction
    def execute_sample_transaction(hour, index):
        # Varier les opérations
        if index % 3 == 0:
            # Transfert
            return strategy.execute_transfer(
                'user_001', 'user_002', 1000,
                saint_louis, dakar, [saint_louis, ziguinchor]
            )
        elif index % 3 == 1:
            # Balance
            return strategy.execute_balance_query(
                'user_001', saint_louis, dakar, context='display'
            )
        else:
            # Historique
            return strategy.execute_history_query('user_001', saint_louis, dakar)
    
    # Simuler 24h
    hourly_metrics = load_sim.simulate_24h(execute_sample_transaction, transactions_per_sample=5)
    
    # Visualiser
    visualizer = Visualizer()
    visualizer.plot_24h_evolution(hourly_metrics)
    
    print("\nSimulation 24h terminée - Graphiques dans /outputs/")

if __name__ == "__main__":
    print("\n" + "="*80)
    print(" WAVE CAP SIMULATION - MENU PRINCIPAL")
    print("="*80 + "\n")
    
    print("Simulations disponibles:")
    print("  1. Partition réseau - Comparaison CP vs Adaptive")
    print("  2. Évolution CAP sur 24 heures")
    print("  3. Les deux simulations")
    print()
    
    choice = input("Votre choix (1/2/3): ").strip()
    
    if choice == '1':
        run_partition_comparison()
    elif choice == '2':
        run_daily_simulation()
    elif choice == '3':
        run_partition_comparison()
        print("\n" + "="*80 + "\n")
        run_daily_simulation()
    else:
        print("Choix invalide!")