"""
Academic Research Export Service
Provides data export functionality for academic research tools including SPSS, R, and citation generation
"""

import csv
import io
import json
import logging
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from statistics import mean, median, stdev
from typing import Any

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """Supported academic export formats"""

    SPSS_SAV = "spss_sav"
    SPSS_POR = "spss_por"
    R_CSV = "r_csv"
    R_RDS = "r_rds"
    R_JSON = "r_json"
    STATA_DTA = "stata_dta"
    SAS_DAT = "sas_dat"


class CitationStyle(Enum):
    """Supported citation styles"""

    APA = "apa"
    MLA = "mla"
    CHICAGO = "chicago"
    HARVARD = "harvard"
    IEEE = "ieee"
    AMA = "ama"


class DataType(Enum):
    """Data types for export"""

    ASSESSMENT_RESULTS = "assessment_results"
    PERSONALITY_DATA = "personality_data"
    TEAM_ANALYTICS = "team_analytics"
    RESPONSE_DATA = "response_data"
    DEMOGRAPHIC_DATA = "demographic_data"
    TIME_SERIES = "time_series"


class StatisticalMeasure(Enum):
    """Statistical measures to include in exports"""

    MEAN = "mean"
    MEDIAN = "median"
    STANDARD_DEVIATION = "std"
    VARIANCE = "variance"
    MIN = "min"
    MAX = "max"
    QUARTILES = "quartiles"
    SKEWNESS = "skewness"
    KURTOSIS = "kurtosis"
    CORRELATION_MATRIX = "correlation"


@dataclass
class ExportMetadata:
    """Metadata for academic exports"""

    title: str
    description: str
    authors: list[str]
    institution: str
    department: str
    study_date: datetime
    data_type: DataType
    sample_size: int
    variables_count: int
    ethics_approval: str | None = None
    doi: str | None = None
    version: str = "1.0"
    confidentiality_level: str = "confidential"


@dataclass
class VariableDefinition:
    """Variable definition for academic export"""

    name: str
    label: str
    data_type: str  # numeric, string, date, etc.
    measurement_level: str  # nominal, ordinal, interval, ratio
    values: dict[str, str] | None = None  # Value labels
    missing_values: list[str] | None = None
    width: int = 8
    decimals: int = 2
    description: str | None = None


@dataclass
class StatisticalSummary:
    """Statistical summary of variables"""

    variable_name: str
    n: int
    mean: float | None = None
    median: float | None = None
    std: float | None = None
    variance: float | None = None
    min: float | None = None
    max: float | None = None
    q25: float | None = None
    q75: float | None = None
    skewness: float | None = None
    kurtosis: float | None = None
    missing_count: int = 0


@dataclass
class AcademicExportResult:
    """Result of academic data export"""

    format: ExportFormat
    filename: str
    file_content: str | bytes
    metadata: ExportMetadata
    variable_definitions: list[VariableDefinition]
    statistical_summary: list[StatisticalSummary] | None = None
    file_size: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Citation:
    """Academic citation"""

    authors: list[str]
    title: str
    publication_year: int
    source: str
    doi: str | None = None
    url: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    publisher: str | None = None


@dataclass
class MethodologyDocument:
    """Research methodology documentation"""

    title: str
    abstract: str
    introduction: str
    methodology: str
    participants: str
    materials: str
    procedure: str
    data_analysis: str
    results: str
    discussion: str
    conclusion: str
    references: list[str]
    appendices: list[str]
    created_at: datetime = field(default_factory=datetime.utcnow)


class AcademicExportService:
    """Comprehensive academic research export service"""

    def __init__(self):
        self.supported_formats = list(ExportFormat)
        self.citation_styles = list(CitationStyle)

        # Initialize measurement level mappings
        self.measurement_mappings = {
            "nominal": ["nominal", "categorical", "binary"],
            "ordinal": ["ordinal", "likert", "ranking"],
            "interval": ["interval", "scale"],
            "ratio": ["ratio", "continuous", "count"],
        }

        # Personality framework variable mappings
        self.personality_variable_mappings = {
            "big_five": {
                "openness": "OPE_Openness",
                "conscientiousness": "CON_Conscientiousness",
                "extraversion": "EXT_Extraversion",
                "agreeableness": "AGR_Agreeableness",
                "neuroticism": "NEU_Neuroticism",
            },
            "mbti": {
                "ei": "EI_Extroversion_Introversion",
                "sn": "SN_Sensing_Intuition",
                "tf": "TF_Thinking_Feeling",
                "jp": "JP_Judging_Perceiving",
            },
            "enneagram": {"type": "ENNE_Enneagram_Type", "wing": "ENNE_Wing_Type"},
        }

    async def export_to_spss(
        self,
        data: list[dict[str, Any]],
        metadata: ExportMetadata,
        format_type: ExportFormat = ExportFormat.SPSS_SAV,
    ) -> AcademicExportResult:
        """Export data to SPSS format (.sav or .por)"""
        try:
            logger.info(f"Exporting data to SPSS format: {format_type.value}")

            # Analyze data structure and create variable definitions
            variable_definitions = await self._analyze_variables_for_spss(data)

            # Generate statistical summary
            statistical_summary = await self._calculate_statistical_summary(
                data, variable_definitions
            )

            # Create SPSS file content
            if format_type == ExportFormat.SPSS_SAV:
                # For .sav format, we would typically use pyreadstat or similar
                # For this implementation, creating a CSV with SPSS syntax
                file_content = await self._create_spss_syntax_file(
                    data, variable_definitions, metadata
                )
                filename = f"{metadata.title.replace(' ', '_')}_SPSS_syntax.sps"
            else:
                # .por format (portable format)
                file_content = await self._create_spss_portable_format(
                    data, variable_definitions, metadata
                )
                filename = f"{metadata.title.replace(' ', '_')}_SPSS.por"

            return AcademicExportResult(
                format=format_type,
                filename=filename,
                file_content=file_content,
                metadata=metadata,
                variable_definitions=variable_definitions,
                statistical_summary=statistical_summary,
                file_size=len(file_content.encode("utf-8")),
            )

        except Exception as e:
            logger.error(f"Error exporting to SPSS: {e!s}")
            raise

    async def export_to_r(
        self,
        data: list[dict[str, Any]],
        metadata: ExportMetadata,
        format_type: ExportFormat = ExportFormat.R_CSV,
    ) -> AcademicExportResult:
        """Export data to R format"""
        try:
            logger.info(f"Exporting data to R format: {format_type.value}")

            # Analyze data structure
            variable_definitions = await self._analyze_variables_for_r(data)

            # Generate statistical summary
            statistical_summary = await self._calculate_statistical_summary(
                data, variable_definitions
            )

            if format_type == ExportFormat.R_CSV:
                file_content = await self._create_r_csv(
                    data, variable_definitions, metadata
                )
                filename = f"{metadata.title.replace(' ', '_')}_R_data.csv"
            elif format_type == ExportFormat.R_RDS:
                file_content = await self._create_r_rds(
                    data, variable_definitions, metadata
                )
                filename = f"{metadata.title.replace(' ', '_')}_R_data.rds"
            else:  # R_JSON
                file_content = await self._create_r_json(
                    data, variable_definitions, metadata
                )
                filename = f"{metadata.title.replace(' ', '_')}_R_data.json"

            return AcademicExportResult(
                format=format_type,
                filename=filename,
                file_content=file_content,
                metadata=metadata,
                variable_definitions=variable_definitions,
                statistical_summary=statistical_summary,
                file_size=len(file_content.encode("utf-8")),
            )

        except Exception as e:
            logger.error(f"Error exporting to R: {e!s}")
            raise

    async def _analyze_variables_for_spss(
        self, data: list[dict[str, Any]]
    ) -> list[VariableDefinition]:
        """Analyze data and create SPSS variable definitions"""
        if not data:
            return []

        variable_definitions = []
        sample_record = data[0]

        for field_name, value in sample_record.items():
            # Determine data type and measurement level
            data_type, measurement_level = (
                await self._determine_variable_characteristics(data, field_name)
            )

            # Get value labels for categorical variables
            value_labels = None
            if measurement_level in ["nominal", "ordinal"]:
                value_labels = await self._extract_value_labels(data, field_name)

            # Determine width and decimals
            width, decimals = await self._determine_format_specs(
                data, field_name, data_type
            )

            definition = VariableDefinition(
                name=self._clean_variable_name(field_name),
                label=field_name.replace("_", " ").title(),
                data_type=data_type,
                measurement_level=measurement_level,
                values=value_labels,
                width=width,
                decimals=decimals,
                description=f"Variable: {field_name}",
            )

            variable_definitions.append(definition)

        return variable_definitions

    async def _analyze_variables_for_r(
        self, data: list[dict[str, Any]]
    ) -> list[VariableDefinition]:
        """Analyze data and create R variable definitions"""
        return await self._analyze_variables_for_spss(data)  # Similar analysis for R

    async def _determine_variable_characteristics(
        self, data: list[dict[str, Any]], field_name: str
    ) -> Tuple[str, str]:
        """Determine data type and measurement level for a variable"""
        if not data:
            return "string", "nominal"

        values = [
            record.get(field_name)
            for record in data
            if record.get(field_name) is not None
        ]

        if not values:
            return "string", "nominal"

        # Check if numeric
        try:
            numeric_values = [
                float(v)
                for v in values
                if isinstance(v, (int, float)) or str(v).replace(".", "", 1).isdigit()
            ]
            if len(numeric_values) == len(values):
                # All values are numeric
                unique_values = set(numeric_values)
                if len(unique_values) <= 2 and all(v in [0, 1] for v in unique_values):
                    return "numeric", "nominal"  # Binary
                if len(unique_values) <= 10 and all(
                    v.is_integer() for v in unique_values
                ):
                    return "numeric", "ordinal"  # Ordinal with limited values
                return "numeric", "ratio"  # Continuous
        except (ValueError, TypeError):
            pass

        # Check for dates
        try:
            from datetime import datetime

            for v in values[:5]:  # Check first 5 values
                if isinstance(v, str):
                    datetime.fromisoformat(v.replace("Z", "+00:00"))
            return "date", "interval"
        except Exception as e:
            pass

        # Default to string/nominal
        return "string", "nominal"

    async def _extract_value_labels(
        self, data: list[dict[str, Any]], field_name: str
    ) -> dict[str, str] | None:
        """Extract value labels for categorical variables"""
        values = [
            record.get(field_name)
            for record in data
            if record.get(field_name) is not None
        ]
        unique_values = set(str(v) for v in values)

        if (
            len(unique_values) <= 20
        ):  # Only create labels for variables with <= 20 unique values
            return {str(v): str(v) for v in sorted(unique_values)}

        return None

    async def _determine_format_specs(
        self, data: list[dict[str, Any]], field_name: str, data_type: str
    ) -> Tuple[int, int]:
        """Determine width and decimal places for SPSS format"""
        values = [
            record.get(field_name)
            for record in data
            if record.get(field_name) is not None
        ]

        if not values:
            return 8, 0

        if data_type == "numeric":
            try:
                numeric_values = [
                    float(v)
                    for v in values
                    if isinstance(v, (int, float))
                    or str(v).replace(".", "", 1).isdigit()
                ]
                if numeric_values:
                    max_val = max(abs(v) for v in numeric_values)
                    decimals = max(
                        len(str(v).split(".")[1]) if "." in str(v) else 0
                        for v in numeric_values[:10]
                    )
                    width = max(len(str(int(max_val))) + decimals + 1, 8)
                    return width, min(decimals, 2)
            except Exception as e:
                pass

        elif data_type == "string":
            max_length = max(
                len(str(v)) for v in values[:100]
            )  # Check first 100 values
            return min(max(max_length, 8), 255), 0

        return 8, 0

    def _clean_variable_name(self, name: str) -> str:
        """Clean variable name for SPSS compatibility"""
        # Replace invalid characters and ensure it starts with a letter
        cleaned = "".join(c if c.isalnum() or c == "_" else "_" for c in str(name))
        if cleaned and cleaned[0].isdigit():
            cleaned = "VAR_" + cleaned
        return cleaned.upper()[:64]  # SPSS limit is 64 characters

    async def _create_spss_syntax_file(
        self,
        data: list[dict[str, Any]],
        variable_definitions: list[VariableDefinition],
        metadata: ExportMetadata,
    ) -> str:
        """Create SPSS syntax file with data and variable definitions"""
        syntax_lines = []

        # Header comments
        syntax_lines.append("* SPSS Syntax File Generated by PsychSync")
        syntax_lines.append(f"* Title: {metadata.title}")
        syntax_lines.append(f"* Authors: {', '.join(metadata.authors)}")
        syntax_lines.append(
            f"* Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        syntax_lines.append("")

        # Variable definitions
        syntax_lines.append("DATA LIST FREE /")
        var_names = [var.name for var in variable_definitions]
        syntax_lines.append(" " + " ".join(var_names) + ".")
        syntax_lines.append("")

        # Variable labels
        syntax_lines.append("VARIABLE LABELS")
        for var in variable_definitions:
            syntax_lines.append(f" {var.name} '{var.label}'")
        syntax_lines.append(".")
        syntax_lines.append("")

        # Value labels
        for var in variable_definitions:
            if var.values:
                syntax_lines.append(f"VALUE LABELS {var.name}")
                for value, label in var.values.items():
                    syntax_lines.append(f" {value} '{label}'")
                syntax_lines.append(".")
        syntax_lines.append("")

        # Missing values
        for var in variable_definitions:
            if var.missing_values:
                syntax_lines.append(
                    f"MISSING VALUES {var.name} ({', '.join(var.missing_values)})."
                )

        # Variable formats
        syntax_lines.append("")
        syntax_lines.append("FORMATS")
        for var in variable_definitions:
            if var.data_type == "numeric":
                syntax_lines.append(f" {var.name} (F{var.width}.{var.decimals})")
            else:
                syntax_lines.append(f" {var.name} (A{var.width})")
        syntax_lines.append(".")
        syntax_lines.append("")

        # Measurement levels
        syntax_lines.append("VARIABLE LEVEL")
        for var in variable_definitions:
            level = (
                "SCALE"
                if var.measurement_level in ["interval", "ratio"]
                else "ORDINAL" if var.measurement_level == "ordinal" else "NOMINAL"
            )
            syntax_lines.append(f" {var.name} ({level})")
        syntax_lines.append(".")
        syntax_lines.append("")

        # Data
        syntax_lines.append("BEGIN DATA")
        for record in data:
            values = []
            for var in variable_definitions:
                value = record.get(var.name.lower(), "")
                if value is None or value == "":
                    values.append("")
                else:
                    values.append(str(value))
            syntax_lines.append(" " + " ".join(values))
        syntax_lines.append("END DATA.")
        syntax_lines.append("")

        # Execute command
        syntax_lines.append("EXECUTE.")

        return "\n".join(syntax_lines)

    async def _create_spss_portable_format(
        self,
        data: list[dict[str, Any]],
        variable_definitions: list[VariableDefinition],
        metadata: ExportMetadata,
    ) -> str:
        """Create SPSS portable format file"""
        por_lines = []

        # Header
        por_lines.append("EXPORT OUTFILE='*'/TYPE=POR.")

        # Variable definitions for POR format
        for i, var in enumerate(variable_definitions, 1):
            por_lines.append(
                f"/VARIABLE={i} {var.name} {var.data_type[:1]}{var.width}.{var.decimals}"
            )
            por_lines.append(f"/VALLABELS={i} '{var.label}'")

        # Data
        por_lines.append("/DATA")
        for record in data:
            values = []
            for var in variable_definitions:
                value = record.get(var.name.lower(), "")
                if value is None:
                    values.append("")
                else:
                    values.append(str(value))
            por_lines.append(" " + " ".join(values))

        por_lines.append(".")

        return "\n".join(por_lines)

    async def _create_r_csv(
        self,
        data: list[dict[str, Any]],
        variable_definitions: list[VariableDefinition],
        metadata: ExportMetadata,
    ) -> str:
        """Create R-ready CSV file with metadata comments"""
        output = io.StringIO()

        # Write R script header with metadata
        output.write("# R Data File Generated by PsychSync\n")
        output.write(f"# Title: {metadata.title}\n")
        output.write(f"# Authors: {', '.join(metadata.authors)}\n")
        output.write(f"# Institution: {metadata.institution}\n")
        output.write(f"# Sample Size: {metadata.sample_size}\n")
        output.write(
            f"# Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        output.write("\n")

        # Write R code to load data
        output.write("# Load data into R data frame\n")
        output.write("library(readr)\n")
        output.write(
            f"# psychsync_data <- read_csv('{metadata.title.replace(' ', '_')}_data.csv')\n"
        )
        output.write("\n")

        # Write variable descriptions
        output.write("# Variable Descriptions\n")
        output.write("variable_descriptions <- list(\n")
        for var in variable_definitions:
            clean_desc = (
                var.description.replace('"', "'") if var.description else var.label
            )
            output.write(f'  "{var.name}" = "{clean_desc}",\n')
        output.seek(0, 2)  # Go to end
        output.truncate(output.tell() - 2)  # Remove last comma
        output.write("\n)\n")
        output.write("\n")

        # Write data
        output.write("# Data\n")

        writer = csv.writer(output)

        # Header
        headers = [var.name for var in variable_definitions]
        writer.writerow(headers)

        # Data rows
        for record in data:
            row = []
            for var in variable_definitions:
                value = record.get(var.name.lower(), "")
                if value is None:
                    row.append("")
                else:
                    row.append(str(value))
            writer.writerow(row)

        return output.getvalue()

    async def _create_r_rds(
        self,
        data: list[dict[str, Any]],
        variable_definitions: list[VariableDefinition],
        metadata: ExportMetadata,
    ) -> str:
        """Create R RDS format file content (as JSON representation)"""
        # Create R data frame structure
        r_data = {
            "metadata": {
                "title": metadata.title,
                "authors": metadata.authors,
                "institution": metadata.institution,
                "sample_size": metadata.sample_size,
                "generated": datetime.utcnow().isoformat(),
            },
            "variables": {},
            "data": [],
        }

        # Add variable definitions
        for var in variable_definitions:
            r_data["variables"][var.name] = {
                "label": var.label,
                "type": var.data_type,
                "measurement": var.measurement_level,
                "description": var.description,
            }

        # Add data
        for record in data:
            row = {}
            for var in variable_definitions:
                row[var.name] = record.get(var.name.lower())
            r_data["data"].append(row)

        # Generate R code to recreate the data frame
        r_code = f"""
# R Data Frame Recreation Script
# Generated by PsychSync - {datetime.utcnow().strftime('%Y-%m-%d')}

# Load required libraries
library(jsonlite)

# Data
json_data <- {json.dumps(r_data, indent=2)}

# Create data frame
metadata <- json_data$metadata
variables <- json_data$variables
raw_data <- json_data$data

# Convert to data frame
df <- as.data.frame(raw_data)

# Set variable types and labels
for (var_name in names(variables)) {{
    var_info <- variables[[var_name]]

    # Set descriptive label
    attr(df[[var_name]], "label") <- var_info$label

    # Set type if specified
    if (var_info$type == "numeric") {{
        df[[var_name]] <- as.numeric(df[[var_name]])
    }} else if (var_info$type == "factor") {{
        df[[var_name]] <- as.factor(df[[var_name]])
    }}
}}

# Add metadata as attributes
attr(df, "metadata") <- metadata
attr(df, "source") <- "PsychSync Academic Export"

# Display structure
str(df)

# Summary statistics
summary(df)

# Save as RDS if needed
# saveRDS(df, "{metadata.title.replace(' ', '_')}_data.rds")
"""
        return r_code

    async def _create_r_json(
        self,
        data: list[dict[str, Any]],
        variable_definitions: list[VariableDefinition],
        metadata: ExportMetadata,
    ) -> str:
        """Create JSON format suitable for R analysis"""
        json_data = {
            "metadata": {
                "title": metadata.title,
                "description": metadata.description,
                "authors": metadata.authors,
                "institution": metadata.institution,
                "department": metadata.department,
                "study_date": metadata.study_date.isoformat(),
                "sample_size": metadata.sample_size,
                "variables_count": len(variable_definitions),
                "ethics_approval": metadata.ethics_approval,
                "doi": metadata.doi,
                "version": metadata.version,
                "confidentiality_level": metadata.confidentiality_level,
                "generated": datetime.utcnow().isoformat(),
            },
            "variables": [
                {
                    "name": var.name,
                    "label": var.label,
                    "type": var.data_type,
                    "measurement_level": var.measurement_level,
                    "values": var.values,
                    "width": var.width,
                    "decimals": var.decimals,
                    "description": var.description,
                }
                for var in variable_definitions
            ],
            "data": data,
        }

        return json.dumps(json_data, indent=2, default=str)

    async def _calculate_statistical_summary(
        self, data: list[dict[str, Any]], variable_definitions: list[VariableDefinition]
    ) -> list[StatisticalSummary]:
        """Calculate statistical summary for numeric variables"""
        summaries = []

        for var in variable_definitions:
            if var.data_type == "numeric":
                values = []
                missing_count = 0

                for record in data:
                    value = record.get(var.name.lower())
                    if value is None or value == "":
                        missing_count += 1
                    else:
                        try:
                            values.append(float(value))
                        except (ValueError, TypeError):
                            missing_count += 1

                if values:
                    summary = StatisticalSummary(
                        variable_name=var.name,
                        n=len(values),
                        mean=mean(values),
                        median=median(values),
                        std=stdev(values) if len(values) > 1 else 0,
                        variance=stdev(values) ** 2 if len(values) > 1 else 0,
                        min=min(values),
                        max=max(values),
                        q25=(
                            sorted(values)[int(len(values) * 0.25)]
                            if len(values) > 4
                            else min(values)
                        ),
                        q75=(
                            sorted(values)[int(len(values) * 0.75)]
                            if len(values) > 4
                            else max(values)
                        ),
                        missing_count=missing_count,
                    )

                    # Calculate skewness and kurtosis if enough data
                    if len(values) > 3:
                        # Simplified skewness calculation
                        mean_val = summary.mean
                        std_val = summary.std
                        if std_val > 0:
                            skew_val = sum((x - mean_val) ** 3 for x in values) / (
                                len(values) * std_val**3
                            )
                            summary.skewness = skew_val

                            # Simplified kurtosis calculation
                            kurt_val = (
                                sum((x - mean_val) ** 4 for x in values)
                                / (len(values) * std_val**4)
                                - 3
                            )
                            summary.kurtosis = kurt_val

                    summaries.append(summary)

        return summaries

    async def generate_citation(
        self,
        assessment_name: str,
        authors: list[str],
        publication_year: int = None,
        citation_style: CitationStyle = CitationStyle.APA,
    ) -> str:
        """Generate academic citation for assessment"""
        if publication_year is None:
            publication_year = datetime.utcnow().year

        citation = Citation(
            authors=authors,
            title=assessment_name,
            publication_year=publication_year,
            source="PsychSync Assessment Platform",
            url="https://psychsync.com",
            publisher="PsychSync Inc.",
        )

        return await self._format_citation(citation, citation_style)

    async def _format_citation(self, citation: Citation, style: CitationStyle) -> str:
        """Format citation according to specified style"""
        if style == CitationStyle.APA:
            # APA format: Author, A. A. (Year). Title. Source.
            if len(citation.authors) > 2:
                authors = f"{citation.authors[0]}, et al."
            elif len(citation.authors) == 2:
                authors = f"{citation.authors[0]} & {citation.authors[1]}"
            else:
                authors = citation.authors[0]

            return f"{authors} ({citation.publication_year}). {citation.title}. {citation.source}."

        if style == CitationStyle.MLA:
            # MLA format: Author, First Name. "Title." Source, Year.
            if len(citation.authors) > 2:
                authors = f"{citation.authors[0]}, et al."
            else:
                authors = ", ".join(citation.authors)

            return f'{authors}. "{citation.title}." {citation.source}, {citation.publication_year}.'

        if style == CitationStyle.CHICAGO:
            # Chicago format: Author. Title. Source, Year.
            authors = ", ".join(citation.authors)
            if len(citation.authors) > 1:
                authors = authors.replace(
                    ", " + citation.authors[-1], " & " + citation.authors[-1]
                )

            return f"{authors}. {citation.title}. {citation.source}, {citation.publication_year}."

        if style == CitationStyle.IEEE:
            # IEEE format: [1] A. Author, "Title," Source, Year.
            # Simplified - would use reference numbers in practice
            authors = (
                citation.authors[0].split()[-1]
                + citation.authors[0].split()[0][0]
                + "."
            )
            return f'{authors}, "{citation.title}," {citation.source}, {citation.publication_year}.'

        # Default format
        return f"{', '.join(citation.authors)} ({citation.publication_year}). {citation.title}. {citation.source}."

    async def create_methodology_document(
        self,
        assessment_name: str,
        description: str,
        sample_size: int,
        methodology_details: dict[str, Any],
    ) -> MethodologyDocument:
        """Create comprehensive research methodology documentation"""

        # Generate standard methodology sections
        abstract = f"This study utilized the {assessment_name} assessment to evaluate psychological characteristics among a sample of {sample_size} participants. {description}"

        introduction = await self._generate_introduction(
            assessment_name, methodology_details
        )

        methodology = await self._generate_methodology_section(methodology_details)

        participants = await self._generate_participants_section(
            sample_size, methodology_details
        )

        materials = await self._generate_materials_section(
            assessment_name, methodology_details
        )

        procedure = await self._generate_procedure_section(methodology_details)

        data_analysis = await self._generate_data_analysis_section(methodology_details)

        results = await self._generate_results_section(methodology_details)

        discussion = await self._generate_discussion_section(
            assessment_name, methodology_details
        )

        conclusion = await self._generate_conclusion_section(
            assessment_name, methodology_details
        )

        references = await self._generate_references(assessment_name)

        appendices = await self._generate_appendices(
            assessment_name, methodology_details
        )

        return MethodologyDocument(
            title=f"Methodology Report: {assessment_name}",
            abstract=abstract,
            introduction=introduction,
            methodology=methodology,
            participants=participants,
            materials=materials,
            procedure=procedure,
            data_analysis=data_analysis,
            results=results,
            discussion=discussion,
            conclusion=conclusion,
            references=references,
            appendices=appendices,
        )

    async def _generate_introduction(
        self, assessment_name: str, details: dict[str, Any]
    ) -> str:
        """Generate introduction section"""
        return f"""
Introduction

The {assessment_name} represents a significant advancement in psychological assessment methodology.
This comprehensive tool provides researchers with reliable and validated measures for evaluating
key psychological constructs. The instrument has been developed using rigorous psychometric
methodologies and has undergone extensive validation studies to ensure its appropriateness for
research applications.

The current study aims to demonstrate the utility of the {assessment_name} in both research
and clinical settings, providing valuable insights into psychological assessment practices.
"""

    async def _generate_methodology_section(self, details: dict[str, Any]) -> str:
        """Generate methodology section"""
        return """
Methodology

Research Design
This study employed a [cross-sectional/longitudinal/experimental] design to examine the
psychometric properties and applications of the assessment instrument.

Data Collection
Data was collected using the PsychSync digital platform, ensuring standardized administration
conditions and high-quality data capture.

Ethical Considerations
All procedures received approval from the Institutional Review Board. Participants provided
informed consent prior to participation, and all data was handled in accordance with ethical
guidelines for psychological research.
"""

    async def _generate_participants_section(
        self, sample_size: int, details: dict[str, Any]
    ) -> str:
        """Generate participants section"""
        return f"""
Participants

A total of {sample_size} participants completed the assessment procedures. The sample
demographics included:

- Age range: [Specify age range]
- Gender distribution: [Specify distribution]
- Educational background: [Specify background]
- Geographic distribution: [Specify distribution]

Participants were recruited through [recruitment method] and provided informed consent
in accordance with ethical guidelines.

Inclusion and Exclusion Criteria
- Inclusion: [Specify inclusion criteria]
- Exclusion: [Specify exclusion criteria]
"""

    async def _generate_materials_section(
        self, assessment_name: str, details: dict[str, Any]
    ) -> str:
        """Generate materials section"""
        return f"""
Materials and Instruments

Primary Assessment Tool
- {assessment_name}
- Developed by: [Developer information]
- Version: [Version number]
- Administration time: [Time required]
- Format: [Digital/Paper]

Additional Measures
[Describe any additional assessment instruments used]

Technical Equipment
- PsychSync digital platform
- [Other technical equipment used]
"""

    async def _generate_procedure_section(self, details: dict[str, Any]) -> str:
        """Generate procedure section"""
        return """
Procedure

Pre-Assessment Preparation
1. Participant recruitment and screening
2. Informed consent procedures
3. Demographic data collection

Assessment Administration
1. Standardized instructions provided
2. Assessment completion under supervised conditions
3. Quality checks for data completeness

Post-Assessment
1. Debriefing procedures
2. Compensation for participation (if applicable)
3. Data processing and quality assurance
"""

    async def _generate_data_analysis_section(self, details: dict[str, Any]) -> str:
        """Generate data analysis section"""
        return """
Data Analysis

Statistical analyses were conducted using [statistical software] with alpha set at 0.05 for
all significance tests.

Descriptive Statistics
- Central tendency measures
- Variability measures
- Distribution characteristics

Reliability Analysis
- Internal consistency (Cronbach's alpha)
- Test-retest reliability
- Inter-rater reliability (if applicable)

Validity Analysis
- Construct validity
- Criterion-related validity
- Content validity

Inferential Statistics
[Specify statistical tests used based on research questions]
"""

    async def _generate_results_section(self, details: dict[str, Any]) -> str:
        """Generate results section"""
        return """
Results

Preliminary analyses revealed [summarize key findings]. The assessment demonstrated
excellent psychometric properties:

Reliability
- Cronbach's alpha: [value]
- Test-retest reliability: [value]
- [Other reliability measures]

Validity
- Convergent validity: [findings]
- Discriminant validity: [findings]
- [Other validity measures]

Descriptive Statistics
- Mean: [value]
- Standard deviation: [value]
- Range: [value]

[Additional results based on specific analyses]
"""

    async def _generate_discussion_section(
        self, assessment_name: str, details: dict[str, Any]
    ) -> str:
        """Generate discussion section"""
        return f"""
Discussion

The findings of this study demonstrate that the {assessment_name} is a robust and reliable
assessment tool for [specific applications]. The observed psychometric properties indicate
that the instrument meets professional standards for research use.

Interpretation of Findings
The excellent reliability coefficients suggest that the {assessment_name} provides
consistent measurements across time and administrations. The validity evidence supports
the construct validity of the instrument.

Implications for Research
These findings have important implications for psychological research, providing researchers
with a validated tool for [specific applications].

Limitations
Several limitations should be considered when interpreting these results:
[Specify limitations]

Future Directions
Future research should focus on [future research directions]
"""

    async def _generate_conclusion_section(
        self, assessment_name: str, details: dict[str, Any]
    ) -> str:
        """Generate conclusion section"""
        return f"""
Conclusion

This study provides strong evidence for the reliability and validity of the {assessment_name}
as a research tool. The instrument demonstrated excellent psychometric properties and showed
promise for various research applications.

The {assessment_name} represents a valuable addition to the researcher's toolkit, offering
reliable and valid measurement of [target constructs]. Continued use and validation of this
instrument will contribute to the advancement of psychological assessment practices.

Future validation studies in diverse populations and settings will further establish the
utility of this assessment tool across different research contexts.
"""

    async def _generate_references(self, assessment_name: str) -> list[str]:
        """Generate reference list"""
        return [
            f"PsychSync Assessment Platform. (2024). {assessment_name} [Assessment instrument]. "
            f"PsychSync Inc. https://psychsync.com",
            "American Educational Research Association, American Psychological Association, & "
            "National Council on Measurement in Education. (2014). Standards for educational and "
            "psychological testing. American Educational Research Association.",
            "Cohen, J. (1988). Statistical power analysis for the behavioral sciences (2nd ed.). "
            "Lawrence Erlbaum Associates.",
            "DeVellis, R. F. (2017). Scale development: Theory and applications (4th ed.). "
            "SAGE Publications.",
            "Nunnally, J. C., & Bernstein, I. H. (1994). Psychometric theory (3rd ed.). "
            "McGraw-Hill.",
        ]

    async def _generate_appendices(
        self, assessment_name: str, details: dict[str, Any]
    ) -> list[str]:
        """Generate appendix list"""
        return [
            f"Appendix A: {assessment_name} Complete Instrument",
            "Appendix B: Demographic Questionnaire",
            "Appendix C: Statistical Analysis Code",
            "Appendix D: Raw Data Tables",
            "Appendix E: Informed Consent Form",
        ]

    async def export_complete_research_package(
        self,
        assessment_name: str,
        data: list[dict[str, Any]],
        metadata: ExportMetadata,
        export_formats: list[ExportFormat] = None,
    ) -> str:
        """Create complete research package with multiple export formats"""
        if export_formats is None:
            export_formats = [
                ExportFormat.SPSS_SAV,
                ExportFormat.R_CSV,
                ExportFormat.R_JSON,
            ]

        logger.info(f"Creating complete research package for {assessment_name}")

        # Create ZIP file in memory
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Add metadata
            metadata_json = json.dumps(
                {
                    "title": metadata.title,
                    "description": metadata.description,
                    "authors": metadata.authors,
                    "institution": metadata.institution,
                    "study_date": metadata.study_date.isoformat(),
                    "sample_size": metadata.sample_size,
                    "variables_count": metadata.variables_count,
                    "ethics_approval": metadata.ethics_approval,
                    "doi": metadata.doi,
                    "version": metadata.version,
                },
                indent=2,
            )

            zip_file.writestr("metadata.json", metadata_json)

            # Add data exports in multiple formats
            for format_type in export_formats:
                try:
                    if format_type in [ExportFormat.SPSS_SAV, ExportFormat.SPSS_POR]:
                        export_result = await self.export_to_spss(
                            data, metadata, format_type
                        )
                    elif format_type in [
                        ExportFormat.R_CSV,
                        ExportFormat.R_RDS,
                        ExportFormat.R_JSON,
                    ]:
                        export_result = await self.export_to_r(
                            data, metadata, format_type
                        )
                    else:
                        continue

                    zip_file.writestr(
                        f"data/{export_result.filename}", export_result.file_content
                    )

                except Exception as e:
                    logger.error(f"Error creating {format_type.value} export: {e!s}")

            # Add methodology document
            methodology_doc = await self.create_methodology_document(
                assessment_name,
                metadata.description,
                metadata.sample_size,
                {"export_formats": [f.value for f in export_formats]},
            )

            # Convert methodology document to text
            methodology_content = f"""
{methodology_doc.title}

{methodology_doc.abstract}

{methodology_doc.introduction}

{methodology_doc.methodology}

{methodology_doc.participants}

{methodology_doc.materials}

{methodology_doc.procedure}

{methodology_doc.data_analysis}

{methodology_doc.results}

{methodology_doc.discussion}

{methodology_doc.conclusion}

References:
{chr(10).join(f"- {ref}" for ref in methodology_doc.references)}

Appendices:
{chr(10).join(f"- {app}" for app in methodology_doc.appendices)}
"""

            zip_file.writestr("methodology/report.txt", methodology_content)

            # Add README file
            readme_content = f"""
# Research Data Package - {assessment_name}

This package contains all materials needed for academic research using the {assessment_name} assessment.

## Contents:

### Data Files:
{chr(10).join(f"- data/{f.value.replace('_', '.').replace('spss.', 'spss_')} file" for f in export_formats)}

### Documentation:
- metadata.json: Complete metadata about the dataset
- methodology/report.txt: Comprehensive methodology documentation

## Citation:
{await self.generate_citation(assessment_name, metadata.authors, metadata.study_date.year)}

## Data Usage:
This data is provided for academic research purposes only. Please cite appropriately and
adhere to ethical guidelines for data use.

## Contact:
For questions about this data package, contact the researchers listed in the metadata.
"""

            zip_file.writestr("README.txt", readme_content)

        zip_buffer.seek(0)
        return zip_buffer.getvalue()


# Initialize the academic export service
academic_export_service = AcademicExportService()
