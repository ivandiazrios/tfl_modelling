import numpy as np
import os.path
import json
import difflib

__nature_list = [
    "Single Carriageway", "Traffic Island Link", "Dual Carriageway",
    "Roundabout", "Traffic Island Link At Junction", "Slip Road"
]

__weekday_list = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']

__SIMILARITY_THRESHOLD = 0.7

_data_directory = os.path.join((os.path.dirname(__file__)), 'road_data')

_MPH_TO_KPH = 1.60934
_MPH_TO_MPS = 0.44704

def __get_best_nature_approximation(nature):

    similarity_measure = lambda n: difflib.SequenceMatcher(None, nature, n).ratio()
    nature_similarity = map(similarity_measure, __nature_list)

    max_similarity = max(nature_similarity)

    if max_similarity >= __SIMILARITY_THRESHOLD:
        max_index = nature_similarity.index(max_similarity)
        return __nature_list[max_index]
    else:
        return None

def __check_dow_input(dow):
    if type(dow) == int:
        if dow >= len(__weekday_list) or dow < 0:
            raise ValueError("Day of the week has to be between (inclusive) 0-6")

    elif type(dow) == str:
        dow = dow.lower()

        try:
            dow = __weekday_list.index(dow)
        except ValueError:
            raise ValueError("%s is not a valid day of the week string" % dow)

    else:
        raise TypeError("Day of the week must be an int or string")

    return dow

def __check_hour_input(hour):
    if type(hour) == int:
        if hour >= 24 or hour < 0:
            raise ValueError("Hour must be int between 0-23 (inclusive")
    else:
        raise TypeError("Hour must be an int")

    return hour

def __get_road_speed(road, nature, hour, dow, depth):
    road_data = __get_road_data(road)

    dow = __check_dow_input(dow)
    hour = __check_hour_input(hour)

    nature = __get_best_nature_approximation(nature)

    if not road_data:
        raise ValueError('Road does not exist, please validate beforehand')
    else:
        nature_data = road_data.get("nature_results", {}).get(nature, {})

        if not nature_data:
            raise ValueError("Road does not contain this nature, use get_natures_for_road "
                             "to find the natures contained for a given road")

        if "best_function" in nature_data:
            function = _func_list[nature_data["best_function"]]
            parameters = nature_data["parameters"]
            return function(parameters, depth, __days_to_binary(dow), hour)
        else:
            return float(nature_data["avg_speed"])

def __days_to_binary(day):
    if day == 0 or day == 6:
        return 0
    return 1

def __plot_func0(params, rainfall_depth, day, hour):
  p0, e0, p1, e1, p2, e2, c = params
  return p0 * rainfall_depth ** e0 + p1 * day ** e1 + p2 * hour ** e2 + c

def __plot_func1(params, rainfall_depth, day, hour):
  p0, p1, e1, p2, e2, p3, e3, c = params
  return p0 * np.exp(p1 * rainfall_depth ** e1 + p2 * hour ** e2) + p3 * day ** e3 + c

def __plot_func2(params, rainfall_depth, day, hour):
  p0, e0, p1, e1, p2, p3, p4, p5, c = params
  return p0 * rainfall_depth ** e0 + p1 * day ** e1 + p2 * hour ** 4  + p3 * hour ** 3 + p4 * hour ** 2 + p5 * hour + c

_func_list = [__plot_func0, __plot_func1, __plot_func2]

def __get_road_data(road):
    """
    :param road: string
    :return: dictionary of data for road, return empty dictionary if road not found
    """

    road = road.upper()

    file_name = os.path.join(_data_directory, road + ".json")

    if os.path.isfile(file_name):
        with open(file_name) as data_file:
            try:
                data = json.load(data_file)
            except:
                data = {}

            return data

    else:
        return {}

def validate_road(road):
    """
    Check if a road is contained in the model

    Args:
        road (string): Name of road to investigate

    Returns:
        bool: Is given road modelled
    """
    return any(__get_road_data(road))

def get_natures_for_road(road):
    """
    Returns a list of all natures in model for a given road
    """
    road_data = __get_road_data(road)

    if road_data:
        return [str(a) for a in road_data['nature_results'].keys()]
    else:
        return []

def get_available_roads():
    """
    Returns list of all roads contained in the model
    """
    directory_items = os.listdir(_data_directory)
    tail_len = len('.json')

    return [f[:-tail_len] for f in directory_items if not f.startswith('.')]

def get_speed_without_rainfall_mph(road, nature, hour, dow):
    """
    Get predicted speed in mph when rainfall is not present

    Args:
        road (string): Name of road to investigate
        nature (string): Name of nature to investigate
        hour (int): Time of day to investigate.
            Inputted as a number from 0-23
        dow (int): Day of week.
            Integer with Sunday = 0 through to Saturday = 6
        depth (float): Depth of rainfall in 15 minute period
            given in millimeters

    Returns:
        float: The predicted speed of a given road and nature in mph,
            at the time and day of week specified.
    """
    return __get_road_speed(road, nature, hour, dow, 0.0)

def get_speed_without_rainfall_kph(road, nature, hour, dow):
    """
    Get predicted speed in kph when rainfall is not present

    Args:
        road (string): Name of road to investigate
        nature (string): Name of nature to investigate
        hour (int): Time of day to investigate.
            Inputted as a number from 0-23
        dow (int): Day of week.
            Integer with Sunday = 0 through to Saturday = 6
        depth (float): Depth of rainfall in 15 minute period
            given in millimeters

    Returns:
        float: The predicted speed of a given road and nature in kph,
            at the time and day of week specified.
    """
    return __get_road_speed(road, nature, hour, dow, 0.0) * _MPH_TO_KPH

def get_speed_without_rainfall_ms(road, nature, hour, dow):
    """
    Get predicted speed in ms when rainfall is not present

    Args:
        road (string): Name of road to investigate
        nature (string): Name of nature to investigate
        hour (int): Time of day to investigate.
            Inputted as a number from 0-23
        dow (int): Day of week.
            Integer with Sunday = 0 through to Saturday = 6
        depth (float): Depth of rainfall in 15 minute period
            given in millimeters

    Returns:
        float: The predicted speed of a given road and nature in ms,
            at the time and day of week specified.
    """
    return __get_road_speed(road, nature, hour, dow, 0.0) * _MPH_TO_MPS

def get_speed_with_rainfall_mph(road, nature, hour, dow, depth):
    """
    Get predicted speed in mph when rainfall is present

    Args:
        road (string): Name of road to investigate
        nature (string): Name of nature to investigate
        hour (int): Time of day to investigate.
            Inputted as a number from 0-23
        dow (int): Day of week.
            Integer with Sunday = 0 through to Saturday = 6
        depth (float): Depth of rainfall in 15 minute period
            given in millimeters

    Returns:
        float: The predicted speed of a given road and nature in mph,
            at the time and day of week specified.
    """
    speed_no_rainfall = __get_road_speed(road, nature, hour, dow, 0.0)
    speed_rainfall = __get_road_speed(road, nature, hour, dow, depth)

    if speed_no_rainfall < speed_rainfall:
        # Model is increasing
        return speed_no_rainfall
    else:
        return speed_rainfall

def get_speed_with_rainfall_kph(road, nature, hour, dow, depth):
    """
    Get predicted speed in kph when rainfall is present

    Args:
        road (string): Name of road to investigate
        nature (string): Name of nature to investigate
        hour (int): Time of day to investigate.
            Inputted as a number from 0-23
        dow (int): Day of week.
            Integer with Sunday = 0 through to Saturday = 6
        depth (float): Depth of rainfall in 15 minute period
            given in millimeters

    Returns:
        float: The predicted speed of a given road and nature in kph,
            at the time and day of week specified.
    """
    speed_no_rainfall = __get_road_speed(road, nature, hour, dow, 0.0)
    speed_rainfall = __get_road_speed(road, nature, hour, dow, depth)

    if speed_no_rainfall < speed_rainfall:
        # Model is increasing
        return speed_no_rainfall * _MPH_TO_KPH
    else:
        return speed_rainfall * _MPH_TO_KPH

def get_speed_with_rainfall_ms(road, nature, hour, dow, depth):
    """
    Get predicted speed in ms when rainfall is present

    Args:
        road (string): Name of road to investigate
        nature (string): Name of nature to investigate
        hour (int): Time of day to investigate.
            Inputted as a number from 0-23
        dow (int): Day of week.
            Integer with Sunday = 0 through to Saturday = 6
        depth (float): Depth of rainfall in 15 minute period
            given in millimeters

    Returns:
        float: The predicted speed of a given road and nature in ms,
            at the time and day of week specified.
    """
    speed_no_rainfall = __get_road_speed(road, nature, hour, dow, 0.0)
    speed_rainfall = __get_road_speed(road, nature, hour, dow, depth)

    if speed_no_rainfall < speed_rainfall:
        # Model is increasing
        return speed_no_rainfall * _MPH_TO_MPS
    else:
        return speed_rainfall * _MPH_TO_MPS

def get_percentage_slowdown(road, nature, hour, dow, depth):
    """
    Get percentage slowdown caused by rainfall

    Args:
        road (string): Name of road to investigate
        nature (string): Name of nature to investigate
        hour (int): Time of day to investigate.
            Inputted as a number from 0-23
        dow (int): Day of week.
            Integer with Sunday = 0 through to Saturday = 6
        depth (float): Depth of rainfall in 15 minute period
            given in millimeters

    Returns:
        float: The percentage slowdown of the road attributed to rainfall.
    """
    speed_no_rainfall = get_speed_without_rainfall_mph(road, nature, hour, dow)
    speed_rainfall = get_speed_with_rainfall_mph(road, nature, hour, dow, depth)

    return (1.0 - (speed_rainfall / speed_no_rainfall)) * 100.0
