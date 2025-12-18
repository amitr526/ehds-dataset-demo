"""
CSV to HealthDCAT Turtle Converter. 

A Python utility to convert CSV files containing health dataset metadata
into RDF Turtle format according to the HealthDCAT specification.
"""

__version__ = "0.1.0"
__author__ = "amitr526"

from csv_to_healthdcat.converter import CSVToHealthDCAT

__all__ = ["CSVToHealthDCAT"]
