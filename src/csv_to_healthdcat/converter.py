"""
CSV to HealthDCAT RDF converter module.

This module provides the core functionality for converting CSV metadata
to RDF Turtle format according to HealthDCAT specification. 
"""

import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import pandas as pd
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF

logger = logging.getLogger(__name__)

# Define namespaces
DCAT = Namespace("http://www.w3.org/ns/dcat#")
DCATAP = Namespace("http://data.europa.eu/r5r/")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
ADMS = Namespace("http://www.w3.org/ns/adms#")


class CSVToHealthDCAT:
    """
    Converter class for transforming CSV files to HealthDCAT RDF format. 

    This class reads CSV files containing dataset metadata and converts them
    to RDF Turtle format compliant with the HealthDCAT specification.
    """

    def __init__(self, base_uri: str = "http://example.org/") -> None:
        """
        Initialize the converter.

        Args:
            base_uri: Base URI for RDF resources (default: http://example.org/)
        """
        self.base_uri = base_uri
        self.graph:  Graph = Graph()
        self._bind_namespaces()

    def _bind_namespaces(self) -> None:
        """Bind common namespaces to the graph."""
        self.graph.bind("dcat", DCAT)
        self.graph.bind("dct", DCTERMS)
        self.graph.bind("dcatap", DCATAP)
        self.graph.bind("vcard", VCARD)
        self.graph.bind("foaf", FOAF)
        self.graph.bind("adms", ADMS)
        self.graph.bind("rdf", RDF)

    def convert_csv(self, csv_path: str) -> Graph:
        """
        Convert a CSV file to HealthDCAT RDF format. 

        Args:
            csv_path: Path to the input CSV file

        Returns:
            RDFlib Graph object containing the converted metadata

        Raises:
            FileNotFoundError: If the CSV file doesn't exist
            ValueError:  If the CSV is missing required columns or is malformed
        """
        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            raise ValueError(f"Failed to read CSV file: {e}") from e

        if df.empty:
            logger.warning("CSV file is empty")
            return self.graph

        # Required columns
        required_columns = {"title", "description"}
        missing_columns = required_columns - set(df.columns)
        if missing_columns:
            raise ValueError(f"CSV is missing required columns: {missing_columns}")

        logger.info(f"Processing {len(df)} dataset(s) from CSV")

        # Process each row in the CSV
        for idx, row in df.iterrows():
            self._add_dataset_to_graph(row, idx)

        return self.graph

    def _add_dataset_to_graph(self, row: pd.Series, row_index: int) -> None:
        """
        Add a single dataset from a CSV row to the RDF graph. 

        Args:
            row:  Pandas series representing a CSV row
            row_index: Index of the row (used for URI generation)
        """
        # Generate dataset URI
        dataset_id = row. get("id", f"dataset-{row_index + 1}")
        dataset_uri = URIRef(urljoin(self.base_uri, f"dataset/{dataset_id}"))

        # Add dataset type
        self.graph.add((dataset_uri, RDF.type, DCAT.Dataset))

        # Add mandatory properties
        title = str(row.get("title", "Unknown"))
        self.graph.add((dataset_uri, DCTERMS.title, Literal(title)))

        description = str(row.get("description", ""))
        if description: 
            self.graph.add((dataset_uri, DCTERMS.description, Literal(description)))

        # Add optional properties
        if "publisher" in row and pd.notna(row["publisher"]):
            publisher_name = str(row["publisher"])
            publisher_uri = URIRef(
                urljoin(self.base_uri, f"organization/{publisher_name. replace(' ', '-').lower()}")
            )
            self.graph.add((dataset_uri, DCTERMS.publisher, publisher_uri))
            self.graph.add((publisher_uri, RDF.type, FOAF.Organization))
            self.graph.add((publisher_uri, FOAF.name, Literal(publisher_name)))

        if "issued" in row and pd.notna(row["issued"]):
            self.graph.add(
                (dataset_uri, DCTERMS.issued, Literal(str(row["issued"])))
            )

        if "modified" in row and pd.notna(row["modified"]):
            self.graph.add(
                (dataset_uri, DCTERMS.modified, Literal(str(row["modified"])))
            )

        if "license" in row and pd.notna(row["license"]):
            license_uri = URIRef(str(row["license"]))
            self.graph.add((dataset_uri, DCTERMS.license, license_uri))

        if "theme" in row and pd.notna(row["theme"]):
            theme_value = str(row["theme"]).upper()
            # Map theme to EU Data Theme vocabulary
            theme_uri = self._get_theme_uri(theme_value)
            self.graph.add((dataset_uri, DCAT.theme, theme_uri))

        if "keyword" in row and pd.notna(row["keyword"]):
            keywords = str(row["keyword"]).split(";")
            for keyword in keywords: 
                self.graph.add(
                    (dataset_uri, DCAT.keyword, Literal(keyword.strip()))
                )

        if "landing_page" in row and pd. notna(row["landing_page"]):
            landing_page_uri = URIRef(str(row["landing_page"]))
            self.graph.add((dataset_uri, DCAT.landingPage, landing_page_uri))

        logger.debug(f"Added dataset to graph: {dataset_uri}")

    @staticmethod
    def _get_theme_uri(theme: str) -> URIRef:
        """
        Map a theme string to the corresponding EU Data Theme URI.

        Args:
            theme: Theme string

        Returns:
            URIRef for the EU Data Theme

        References:
            https://publications.europa.eu/resource/authority/data-theme/
        """
        theme_mapping = {
            "HEALTH":  "HEAL",
            "HEAL": "HEAL",
            "MEDICINE": "HEAL",
            "SCIENCE": "SCIE",
            "EDUCATION": "EDUC",
            "ENVIRONMENT": "ENVI",
            "TECHNOLOGY":  "TECH",
        }

        mapped_theme = theme_mapping.get(theme, "HEAL")  # Default to HEAL
        return URIRef(
            f"http://publications.europa.eu/resource/authority/data-theme/{mapped_theme}"
        )
