#!/usr/bin/env python3
import sys
import os
sys.path.append('backend')

try:
    from app.file_processor import FastaProcessor
    print("✅ FastaProcessor import successful")
except Exception as e:
    print(f"❌ FastaProcessor import failed: {e}")

try:
    from app.classifier import MockSpeciesClassifier
    print("✅ MockSpeciesClassifier import successful")
except Exception as e:
    print(f"❌ MockSpeciesClassifier import failed: {e}")

try:
    from app.biodiversity import BiodiversityCalculator
    print("✅ BiodiversityCalculator import successful")
except Exception as e:
    print(f"❌ BiodiversityCalculator import failed: {e}")

try:
    from app.database import DatabaseManager
    print("✅ DatabaseManager import successful")
except Exception as e:
    print(f"❌ DatabaseManager import failed: {e}")

try:
    from app.app import app
    print("✅ Flask app import successful")
except Exception as e:
    print(f"❌ Flask app import failed: {e}")
