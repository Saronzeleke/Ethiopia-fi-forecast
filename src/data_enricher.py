# src/data_enricher.py
import pandas as pd
from typing import List


class DataEnricher:
    """
    Enrich financial inclusion dataset with additional OBSERVATIONS only.
    No events. No causal assumptions.
    """

    def __init__(self, base_data: pd.DataFrame):
        self.base_data = base_data.copy()
        self.new_records: List[dict] = []

    # ---------------------------------------------------
    # FINDEX MICRODATA
    # ---------------------------------------------------
    def add_findex_microdata(self) -> None:
        data = {
            "indicator": "Account ownership, female (% age 15+)",
            "indicator_code": "FINDEX_ACCOUNT_FEMALE",
            "values": {
                2011: 11.2,
                2014: 18.5,
                2017: 31.8,
                2021: 42.1,
                2024: 45.3,
            },
            "source": "World Bank Global Findex",
            "source_url": "https://www.worldbank.org/globalfindex",
            "confidence": "high",
        }

        for year, value in data["values"].items():
            self.new_records.append({
                "record_type": "observation",
                "pillar": "access",
                "indicator": data["indicator"],
                "indicator_code": data["indicator_code"],
                "value_numeric": value,
                "observation_date": f"{year}-12-31",
                "source_name": data["source"],
                "source_url": data["source_url"],
                "confidence": data["confidence"],
                "notes": "Gender-disaggregated Findex data",
            })

    # ---------------------------------------------------
    # NBE INFRASTRUCTURE DATA
    # ---------------------------------------------------
    def add_nbe_infrastructure_data(self) -> None:
        indicators = {
            "INFRA_ATM_DENSITY": {
                "name": "ATMs per 100,000 adults",
                "values": {2021: 7.8, 2022: 8.2, 2023: 8.5},
            },
            "INFRA_BRANCH_DENSITY": {
                "name": "Bank branches per 100,000 adults",
                "values": {2021: 6.1, 2022: 6.3, 2023: 6.4},
            },
        }

        for code, meta in indicators.items():
            for year, value in meta["values"].items():
                self.new_records.append({
                    "record_type": "observation",
                    "pillar": "infrastructure",
                    "indicator": meta["name"],
                    "indicator_code": code,
                    "value_numeric": value,
                    "observation_date": f"{year}-12-31",
                    "source_name": "National Bank of Ethiopia",
                    "source_url": "https://nbe.gov.et",
                    "confidence": "high",
                    "notes": "NBE annual report",
                })

    # ---------------------------------------------------
    # GSMA MOBILE DATA
    # ---------------------------------------------------
    def add_gsma_mobile_data(self) -> None:
        indicators = {
            "GSMA_MOBILE_PENETRATION": {
                "name": "Mobile penetration (% population)",
                "values": {2021: 44, 2022: 48, 2023: 52, 2024: 55},
            },
            "GSMA_4G_COVERAGE": {
                "name": "4G coverage (% population)",
                "values": {2021: 35, 2022: 42, 2023: 50, 2024: 58},
            },
        }

        for code, meta in indicators.items():
            for year, value in meta["values"].items():
                self.new_records.append({
                    "record_type": "observation",
                    "pillar": "infrastructure",
                    "indicator": meta["name"],
                    "indicator_code": code,
                    "value_numeric": value,
                    "observation_date": f"{year}-12-31",
                    "source_name": "GSMA",
                    "source_url": "https://www.gsma.com",
                    "confidence": "medium",
                    "notes": "GSMA Mobile Economy",
                })

    # ---------------------------------------------------
    # FINAL MERGE
    # ---------------------------------------------------
    def get_enriched_data(self) -> pd.DataFrame:
        new_df = pd.DataFrame(self.new_records)

        # Ensure required schema
        required_cols = [
            "record_type", "pillar", "indicator", "indicator_code",
            "value_numeric", "observation_date",
            "source_name", "source_url", "confidence", "notes"
        ]

        for col in required_cols:
            if col not in new_df.columns:
                new_df[col] = None
            if col not in self.base_data.columns:
                self.base_data[col] = None

        enriched = pd.concat([self.base_data, new_df], ignore_index=True)
        return enriched
