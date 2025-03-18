from django import test

from argus.htmx.incident.customization import IncidentTableColumn, get_incident_table_columns


class TestGetIncidentTableColumns(test.TestCase):
    @test.override_settings(INCIDENT_TABLE_COLUMNS=["status"])
    def test_it_should_return_correct_builtin_columns_based_on_name(self):
        columns = get_incident_table_columns()
        assert columns[0].name == "status"

    @test.override_settings(INCIDENT_TABLE_COLUMNS=["not_real"])
    def test_it_should_raise_exception_if_settings_contain_name_for_nonexisting_builtin(self):
        with self.assertRaises(ValueError):
            get_incident_table_columns()

    @test.override_settings(
        INCIDENT_TABLE_COLUMNS=[
            IncidentTableColumn(
                "custom_column",
                label="Custom Column",
                cell_template="htmx/incidents/_custom_template.html",
            ),
        ],
    )
    def test_it_should_return_custom_column(self):
        columns = get_incident_table_columns()
        assert columns[0].name == "custom_column"
