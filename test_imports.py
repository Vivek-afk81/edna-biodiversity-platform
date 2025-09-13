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
    from app.classifier import UnsupervisedClassifier
    print("✅ UnsupervisedClassifier import successful")
except Exception as e:
    print(f"❌ UnsupervisedClassifier import failed: {e}")

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
    from backend.app.app import app
    print("✅ Flask app import successful")
except Exception as e:
    print(f"❌ Flask app import failed: {e}")
