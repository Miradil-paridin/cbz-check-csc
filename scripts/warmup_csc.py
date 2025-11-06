# warmup_csc.py
from checker.csc import load_csc_model
m = load_csc_model()
print("CSC model:", "OK" if m else "NOT LOADED")
