"""
Unit tests for the CSV to HealthDCAT converter. 

This module contains comprehensive tests including mock CSV data
to ensure the converter works correctly.
"""

import io
from pathlib import Path
from typing import Iterator

import pytest
from rdflib import URIRef

from csv_to_healthdcat.converter import CSVToHealthDCAT


@pytest.fixture
def sample_csv_data() -> str:
    """Fixture providing sample CSV data for testing."""
    return """title,description,publisher,issued,modified,license,theme,keyword,landing_page,id
Blood Pressure Dataset,Anonymized blood pressure readings from 2023,Health Authority,2023-01-01,2024-01-01,http://creativecommons.org/licenses/by/4.0/,HEALTH,blood;pressure;cardiology,http://example.org/bp-dataset,bp-001
COVID-19 Epidemiological Data,Epidemiological data on COVID-19 cases and outcomes,Public Health Agency,2020-01-01,2024-12-18,http://creativecommons.org/licenses/by-sa/4.0/,HEALTH,covid;epidemiology;pandemic,http://example.org/covid-data,covid-001
Diabetes Registry,Patient registry for Type 2 diabetes management,Hospital System,2022-06-15,2024-12-18,http://creativecommons.org/licenses/by-nc/4.0/,HEALTH,diabetes;registry;patients,http://example.org/diabetes,diabetes-001"""


@pytest.fixture
def converter() -> CSVToHealthDCAT:
    """Fixture providing a converter instance."""
    return CSVToHealthDCAT(base_uri="http://test.example.org/")


@pytest.fixture
def temp_csv_file(tmp_path: Path, sample_csv_data: str) -> Path:
    """Fixture providing a temporary CSV file."""
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text(sample_csv_data)
    return csv_file


class TestCSVToHealthDCAT:
    """Test suite for CSVToHealthDCAT converter."""

    def test_converter_initialization(self, converter: CSVToHealthDCAT) -> None:
        """Test that converter initializes correctly."""
        assert converter.base_uri == "http://test.example.org/"
        assert converter.graph is not None
        assert len(converter.graph) == 0

    def test_convert_csv_basic(self, converter: CSVToHealthDCAT, temp_csv_file: Path) -> None:
        """Test basic CSV conversion functionality."""
        graph = converter.convert_csv(str(temp_csv_file))
        assert graph is not None
        assert len(graph) > 0

    def test_convert_csv_dataset_count(
        self, converter: CSVToHealthDCAT, temp_csv_file: Path
    ) -> None:
        """Test that all datasets from CSV are converted."""
        graph = converter.convert_csv(str(temp_csv_file))
        # Each dataset should have at least 2 triples (type + title)
        assert len(graph) >= 6

    def test_convert_csv_datasets_have_titles(
        self, converter: CSVToHealthDCAT, temp_csv_file: Path
    ) -> None:
        """Test that all datasets have titles in RDF."""
        graph = converter. convert_csv(str(temp_csv_file))
        from rdflib. namespace import DCTERMS

        titles = list(graph.objects(predicate=DCTERMS.title))
        assert len(titles) >= 3
        assert any("Blood Pressure" in str(title) for title in titles)

    def test_convert_csv_datasets_have_descriptions(
        self, converter: CSVToHealthDCAT, temp_csv_file: Path
    ) -> None:
        """Test that datasets have descriptions."""
        graph = converter.convert_csv(str(temp_csv_file))
        from rdflib.namespace import DCTERMS

        descriptions = list(graph.objects(predicate=DCTERMS.description))
        assert len(descriptions) >= 3

    def test_convert_csv_with_publisher(
        self, converter: CSVToHealthDCAT, temp_csv_file: Path
    ) -> None:
        """Test that publisher information is included."""
        graph = converter.convert_csv(str(temp_csv_file))
        from rdflib.namespace import DCTERMS

        publishers = list(graph.objects(predicate=DCTERMS.publisher))
        assert len(publishers) >= 3

    def test_convert_csv_with_license(
        self, converter: CSVToHealthDCAT, temp_csv_file: Path
    ) -> None:
        """Test that license information is included."""
        graph = converter.convert_csv(str(temp_csv_file))
        from rdflib.namespace import DCTERMS

        licenses = list(graph.objects(predicate=DCTERMS.license))
        assert len(licenses) >= 3

    def test_convert_csv_with_theme(
        self, converter: CSVToHealthDCAT, temp_csv_file: Path
    ) -> None:
        """Test that theme information is included."""
        graph = converter.convert_csv(str(temp_csv_file))
        from csv_to_healthdcat.converter import DCAT

        themes = list(graph.objects(predicate=DCAT.theme))
        assert len(themes) >= 3
        # Check that themes are valid EU Data Theme URIs
        for theme in themes:
            assert "publications.europa.eu" in str(theme)

    def test_convert_csv_with_keywords(
        self, converter: CSVToHealthDCAT, temp_csv_file: Path
    ) -> None:
        """Test that keywords are properly parsed and added."""
        graph = converter.convert_csv(str(temp_csv_file))
        from csv_to_healthdcat.converter import DCAT

        keywords = list(graph.objects(predicate=DCAT.keyword))
        assert len(keywords) >= 3

    def test_missing_required_column_raises_error(
        self, converter: CSVToHealthDCAT, tmp_path: Path
    ) -> None:
        """Test that missing required columns raise ValueError."""
        invalid_csv = tmp_path / "invalid.csv"
        invalid_csv.write_text("publisher,issued\nTest,2023-01-01")

        with pytest.raises(ValueError, match="missing required columns"):
            converter.convert_csv(str(invalid_csv))

    def test_nonexistent_file_raises_error(self, converter: CSVToHealthDCAT) -> None:
        """Test that nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            converter.convert_csv("/nonexistent/file.csv")

    def test_empty_csv_returns_empty_graph(
        self, converter: CSVToHealthDCAT, tmp_path: Path
    ) -> None:
        """Test handling of empty CSV file."""
        empty_csv = tmp_path / "empty.csv"
        empty_csv.write_text("title,description")

        graph = converter.convert_csv(str(empty_csv))
        assert len(graph) == 0

    def test_theme_uri_mapping(self) -> None:
        """Test theme string to URI mapping."""
        test_cases = [
            ("HEALTH", "HEAL"),
            ("MEDICINE", "HEAL"),
            ("SCIENCE", "SCIE"),
            ("UNKNOWN", "HEAL"),  # Should default to HEAL
        ]

        for input_theme, expected_code in test_cases:
            uri = CSVToHealthDCAT._get_theme_uri(input_theme)
            assert expected_code in str(uri)

    def test_graph_serialization(
        self, converter: CSVToHealthDCAT, temp_csv_file: Path, tmp_path: Path
    ) -> None:
        """Test that graph can be serialized to Turtle format."""
        graph = converter.convert_csv(str(temp_csv_file))
        output_file = tmp_path / "output.ttl"

        graph.serialize(destination=str(output_file), format="turtle")
        assert output_file.exists()
        assert output_file.stat().st_size > 0

        # Verify Turtle format
        content = output_file.read_text()
        assert "@prefix" in content
        assert "a" in content or "rdf: type" in content

    def test_custom_base_uri(self, temp_csv_file: Path) -> None:
        """Test converter with custom base URI."""
        custom_uri = "http://custom.example.org/data/"
        converter = CSVToHealthDCAT(base_uri=custom_uri)
        graph = converter.convert_csv(str(temp_csv_file))

        from rdflib.namespace import DCTERMS

        # Check that URIs use custom base
        subjects = list(graph.subjects(predicate=DCTERMS. title))
        assert len(subjects) > 0
        assert custom_uri in str(subjects[0])

    def test_datasets_are_typed_as_dcat_dataset(
        self, converter:  CSVToHealthDCAT, temp_csv_file: Path
    ) -> None:
        """Test that all datasets are typed as dcat:Dataset."""
        graph = converter.convert_csv(str(temp_csv_file))
        from csv_to_healthdcat.converter import DCAT
        from rdflib import RDF

        datasets = list(graph.subjects(predicate=RDF.type, object=DCAT.Dataset))
        assert len(datasets) >= 3
