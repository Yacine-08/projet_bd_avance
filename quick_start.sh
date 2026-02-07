#!/bin/bash

echo "=========================================="
echo " WAVE CAP SIMULATION - Installation"
echo "=========================================="

# Créer environnement virtuel
echo "Création environnement virtuel..."
python3 -m venv venv

# Activer
echo "Activation environnement..."
source venv/bin/activate

# Mettre à jour pip
echo "Mise à jour pip..."
pip install --upgrade pip

# Installer setuptools et wheel d'abord
echo "Installation outils de build..."
pip install setuptools wheel

# Installer dépendances
echo "Installation dépendances..."
pip install matplotlib numpy

# Créer répertoires
echo "Création répertoires..."
mkdir -p outputs data config models services strategies simulation analysis tests

# Créer fichiers __init__.py
echo "Création fichiers __init__.py..."
touch config/__init__.py
touch models/__init__.py
touch services/__init__.py
touch strategies/__init__.py
touch simulation/__init__.py
touch analysis/__init__.py

echo ""
echo "✓ Installation terminée!"
echo ""
echo "Pour lancer la simulation:"
echo "  source venv/bin/activate"
echo "  python run_simulation.py"
echo ""