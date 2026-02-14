
class NetworkConfig:
    # Configuration des nœuds et latences
    
    # Nœuds du système
    NODES = {
        'DAKAR': {
            'name': 'Dakar',
            'role': 'master',
            'location': (14.7167, -17.4677),  # Coordonnées GPS
            'capacity': 10000  # transactions/sec
        },
        'SAINT_LOUIS': {
            'name': 'Saint-Louis',
            'role': 'replica_rw',  # Read-Write replica
            'location': (16.0179, -16.5119),
            'capacity': 5000
        },
        'ZIGUINCHOR': {
            'name': 'Ziguinchor',
            'role': 'replica_analytics',  # Backup + Analytics
            'location': (12.5833, -16.2667),
            'capacity': 3000
        }
    }
    
    # Latences réseau (millisecondes)
    LATENCIES = {
        # Temps normal
        'normal': {
            ('DAKAR', 'SAINT_LOUIS'): 50,
            ('DAKAR', 'ZIGUINCHOR'): 150,
            ('SAINT_LOUIS', 'ZIGUINCHOR'): 200,
        },
        # Avec congestion réseau
        'congested': {
            ('DAKAR', 'SAINT_LOUIS'): 200,
            ('DAKAR', 'ZIGUINCHOR'): 600,
            ('SAINT_LOUIS', 'ZIGUINCHOR'): 800,
        },
        # Partition réseau (communication impossible)
        'partitioned': {
            ('DAKAR', 'ZIGUINCHOR'): float('inf'),  # Coupé
            ('DAKAR', 'SAINT_LOUIS'): 50,
            ('SAINT_LOUIS', 'ZIGUINCHOR'): float('inf'),
        }
    }
    
    # Taux de perte de paquets (%)
    PACKET_LOSS = {
        'normal': 0.1,
        'congested': 5.0,
        'partitioned': 100.0  # Entre nœuds partitionnés
    }
    
    # Timeouts (millisecondes)
    TIMEOUTS = {
        'transfer': 5000,      # 5 secondes max pour transfert
        'payment': 10000,      # 10 secondes pour paiement (API externe)
        'balance': 2000,       # 2 secondes pour consulter solde
        'history': 3000,       # 3 secondes pour historique
        'heartbeat': 1000      # 1 seconde pour heartbeat
    }
    
    # Cache TTL (secondes)
    CACHE_TTL = {
        'balance': 60,         # Solde en cache 60s
        'history': 300,        # Historique 5 minutes
        'profile': 3600        # Profil utilisateur 1h
    }

class LoadProfile:
    # Transactions par seconde selon l'heure
    HOURLY_LOAD = {
        0: 10,    # Minuit
        1: 8,
        2: 5,     # Creux de la nuit
        3: 5,
        4: 5,
        5: 8,
        6: 50,    # Début activité
        7: 200,
        8: 500,   # Début journée travail
        9: 800,
        10: 600,
        11: 700,
        12: 900,  # Midi (pause)
        13: 800,
        14: 600,
        15: 700,
        16: 800,
        17: 1000, # Fin journée
        18: 5000, # PIC - sortie bureau
        19: 4000,
        20: 2000,
        21: 800,
        22: 400,
        23: 100
    }
    
    # Latence réseau selon l'heure (ms)
    HOURLY_LATENCY = {
        0: 20,
        2: 15,   # Meilleure latence la nuit
        8: 50,
        12: 100,
        18: 800, # Pire latence heure de pointe
        20: 200,
        23: 30
    }
    
    @classmethod
    def get_load(cls, hour):
        # Obtenir charge pour une heure donnée
        return cls.HOURLY_LOAD.get(hour, 100)
    
    @classmethod
    def get_latency(cls, hour):
        # Obtenir latence pour une heure donnée
        return cls.HOURLY_LATENCY.get(hour, 50)