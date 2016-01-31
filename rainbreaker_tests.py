import rainbreaker as rb
import os
import numpy
import pytest

class TestRainbreaker():

    def setup_class(self):
        # Change api data directory to mock one
        rb._data_directory = os.path.join((os.path.dirname(__file__)), 'test_road_data')

        func0 = lambda (c,), rainfall_depth, day, hour: 1 / (rainfall_depth + 1) + day + hour + c
        func1 = lambda (c,), rainfall_depth, day, hour: rainfall_depth + c * day * hour

        # Change api function list to two simple ones
        rb._func_list = [func0, func1]

    def check_list_equal(self, l1, l2):
        return len(l1) == len(l2) and sorted(l1) == sorted(l2)

    def test_get_available_roads(self):
        assert self.check_list_equal(rb.get_available_roads(), ['TEST_STREET1', 'TEST_STREET2', 'TEST_STREET3', 'TEST_STREET4', 'TEST_STREET5'])

    def test_get_natures_for_road(self):
        assert self.check_list_equal(rb.get_natures_for_road('TEST_STREET1'), ["Traffic Island Link At Junction", "Single Carriageway", "Dual Carriageway"])
        assert self.check_list_equal(rb.get_natures_for_road('TEST_STREET2'), ["Single Carriageway"])
        assert self.check_list_equal(rb.get_natures_for_road('TEST_STREET3'), ["Traffic Island Link At Junction", "Single Carriageway", "Dual Carriageway"])
        assert self.check_list_equal(rb.get_natures_for_road('TEST_STREET4'), ["Single Carriageway", "Slip Road"])
        assert self.check_list_equal(rb.get_natures_for_road('TEST_STREET5'), ["Single Carriageway", "Slip Road", "Traffic Island Link At Junction", "Dual Carriageway", "Roundabout"])

    def test_get_natures_for_unexistent_road(self):
        assert rb.get_natures_for_road('UNEXISTENT ROAD') == []

    def test_validate_road(self):
        assert rb.validate_road('TEST_STREET1')
        assert rb.validate_road('TEST_STREET2')
        assert rb.validate_road('TEST_STREET3')
        assert rb.validate_road('TEST_STREET4')
        assert rb.validate_road('TEST_STREET5')

    def test_validate_unexistent_road(self):
        assert not rb.validate_road('UNEXISTENT ROAD')

    def test_get_speed_with_rainfall_mph(self):
        # Test the calculations are working correctly
        assert numpy.isclose(rb.get_speed_with_rainfall_mph("TEST_STREET3", "Single Carriageway", 5, "Monday", 0.1), 11.709)

    def test_get_speed_with_rainfall_mph_avg_speed_always_constant(self):
        assert numpy.isclose(rb.get_speed_with_rainfall_mph("TEST_STREET3", "Dual Carriageway", 5, "Monday", 0.1), 35.9989)
        assert numpy.isclose(rb.get_speed_with_rainfall_mph("TEST_STREET3", "Dual Carriageway", 16, "Monday", 0.8), 35.9989)

    def test_get_speed_no_rainfall_same_as_0_depth(self):
        assert rb.get_speed_with_rainfall_mph("TEST_STREET5", "Single Carriageway", 5, "Monday", 0) == \
               rb.get_speed_without_rainfall_mph("TEST_STREET5", "Single Carriageway", 5, "Monday")

    def test_throws_value_error_when_road_does_not_contain_inputted_nature(self):
        with pytest.raises(ValueError):
            assert rb.get_speed_with_rainfall_mph("TEST_STREET2", "Dual Carriageway", 5, "Monday", 0)

    def test_api_catches_increasing_model_and_return_0_depth_instead(self):
        assert rb.get_speed_with_rainfall_mph("TEST_STREET2", "Single Carriageway", 5, "Monday", 0.1) == \
               rb.get_speed_without_rainfall_mph("TEST_STREET2", "Single Carriageway", 5, "Monday")

    def test_speed_comparison_mph_to_kph(self):
        assert rb.get_speed_with_rainfall_mph("TEST_STREET5", "Single Carriageway", 5, "Monday", 0.3) * rb._MPH_TO_KPH == \
               rb.get_speed_with_rainfall_kph("TEST_STREET5", "Single Carriageway", 5, "Monday", 0.3)

    def test_speed_comparison_mph_to_ms(self):
        assert rb.get_speed_with_rainfall_mph("TEST_STREET5", "Single Carriageway", 5, "Monday", 0.3) * rb._MPH_TO_MPS == \
               rb.get_speed_with_rainfall_ms("TEST_STREET5", "Single Carriageway", 5, "Monday", 0.3)

    def test_speed_comparison_kph_to_ms(self):
        assert rb.get_speed_with_rainfall_kph("TEST_STREET5", "Single Carriageway", 5, "Monday", 0.3) * (1.0 / rb._MPH_TO_KPH) * rb._MPH_TO_MPS == \
               rb.get_speed_with_rainfall_ms("TEST_STREET5", "Single Carriageway", 5, "Monday", 0.3)

    def test_catches_out_of_range_hour_input(self):
        with pytest.raises(ValueError):
            rb.get_speed_with_rainfall_kph("TEST_STREET5", "Single Carriageway", -1, "Monday", 0.3)
        with pytest.raises(ValueError):
            rb.get_speed_with_rainfall_kph("TEST_STREET5", "Single Carriageway", 24, "Monday", 0.3)

    def test_catches_invalid_hour_type_input(self):
        with pytest.raises(TypeError):
            rb.get_speed_with_rainfall_kph("TEST_STREET5", "Single Carriageway", "1", "Monday", 0.3)

    def test_nature_approximation(self):
        assert rb.get_speed_with_rainfall_mph("TEST_STREET5", "Single Carriageway", 5, "Monday", 0.3) == \
            rb.get_speed_with_rainfall_mph("TEST_STREET5", "SinGllle Carriagewway", 5, "Monday", 0.3)
        assert rb.get_speed_with_rainfall_mph("TEST_STREET1", "Dual Carriageway", 5, "Monday", 0) == \
            rb.get_speed_with_rainfall_mph("TEST_STREET1", "Dual Cawy", 5, "Monday", 0)

    def test_road_uppercase_or_lower_case_irrelevant(self):
        assert rb.get_speed_with_rainfall_mph("TEST_STREET1", "Dual Carriageway", 5, "Monday", 0) == \
            rb.get_speed_with_rainfall_mph("test_street1", "Dual Carriageway", 5, "Monday", 0)

    def test_day_of_week_int_or_string(self):
        assert rb.get_speed_with_rainfall_mph("test_street1", "Dual Carriageway", 5, "Monday", 0) == \
               rb.get_speed_with_rainfall_mph("test_street1", "Dual Carriageway", 5, 1, 0)

    def test_catches_out_of_range_int_day_input(self):
        with pytest.raises(ValueError):
            rb.get_speed_with_rainfall_kph("TEST_STREET5", "Single Carriageway", 0, -1, 0.3)
        with pytest.raises(ValueError):
            rb.get_speed_with_rainfall_kph("TEST_STREET5", "Single Carriageway", 0, 7, 0.3)

    def test_throws_type_error_wrong_day_of_week_input(self):
        with pytest.raises(TypeError):
            rb.get_speed_with_rainfall_kph("TEST_STREET5", "Single Carriageway", 0, 5., 0.3)

    def test_case_of_dow_irrelevant(self):
        assert rb.get_speed_with_rainfall_kph("TEST_STREET5", "Single Carriageway", 0, "MoNDaY", 0.3) == \
            rb.get_speed_with_rainfall_kph("TEST_STREET5", "Single Carriageway", 0, "mOndAy", 0.3)

    def test_throws_value_error_invalid_dow_string(self):
        with pytest.raises(ValueError):
            rb.get_speed_with_rainfall_kph("TEST_STREET5", "Single Carriageway", 0, "Yaladay", 0.3)
