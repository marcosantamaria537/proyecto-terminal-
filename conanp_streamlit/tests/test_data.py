import unittest

import pandas as pd

from src.analytics import calculate_kpis
from src.data import filter_events, standardize_dataframe


class DashboardDataTests(unittest.TestCase):
    def test_aliases_and_kpis(self):
        raw = pd.DataFrame(
            {
                "FECHA_SUPERVICION": ["01/01/2026", "02/01/2026"],
                "TIPO_FALTA": ["Sin falta", "Pesca dentro ANP"],
                "POLIGONO": ["Punta Nizuc", "Punta Nizuc"],
                "ID_RECORRIDO": [1, 2],
                "KM_RECORRIDOS": [10, 15],
            }
        )
        data = standardize_dataframe(raw)
        self.assertTrue(data["fecha"].notna().all())
        self.assertEqual(calculate_kpis(data), {
            "faltas": 1,
            "recorridos": 2,
            "porcentaje_con_falta": 50.0,
            "kilometros": 25.0,
        })

    def test_filters_apply_to_all_rows(self):
        raw = pd.DataFrame(
            {
                "fecha": ["2026-01-01", "2026-02-01"],
                "tipo_falta": ["A", "B"],
                "poligono": ["Norte", "Sur"],
            }
        )
        data = standardize_dataframe(raw)
        result = filter_events(
            data,
            pd.Timestamp("2026-01-01").date(),
            pd.Timestamp("2026-01-31").date(),
            ["Norte"],
            ["A"],
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["poligono"], "Norte")


if __name__ == "__main__":
    unittest.main()
