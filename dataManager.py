import psycopg2
import pandas as pd
from collections import defaultdict

class DataManager(object):

    def __init__(self):
        self.__conn = psycopg2.connect(database="tfl", user="tfl", password="tfl", host="127.0.0.1", port=9999)
        self.__cur = self.__conn.cursor()

    def __get_toids(self, filters, natures):

        column_values = defaultdict(list)
        for k,v in filters:
            column_values[k].append(v)

        filter_condition = " OR ".join([column + " " + self.__get_condition(values) for column, values in column_values.iteritems()])
        conditions = filter_condition + " AND nature %s" % self.__get_condition(natures)

        query = "SELECT toid, length, nature, street, classification " \
                "FROM itn_link WHERE %s" % conditions

        self.__cur.execute(query)
        result = self.__cur.fetchall()

        toid_info = {row[0]:(row[1], row[2], row[3] if row[3] else row[4]) for row in result}

        return toid_info

    def __get_time_depth(self, traffic_table, rainfall_table, toids, hours, days):
        """
        :param toids: list of toids
        :param hours: list of hours
        :param weekdays: list of days
        :return: list of tuples -> (toid, journey_time, depth)
        """

        hours_condition = self.__get_condition(hours)
        days_condition = self.__get_condition(days)
        toid_condition = self.__get_condition(toids)

        query = """
            SELECT traffic.toid, traffic.journey_time, SUM(COALESCE(rainfall.depth, 0)) as depth,
                   EXTRACT(HOUR FROM lower(traffic.period)) as hour,
                   EXTRACT(DOW FROM lower(traffic.period)) as dow
            FROM
                   %s as traffic JOIN link_grid ON traffic.toid = link_grid.toid
                   LEFT JOIN %s as rainfall ON rainfall.os_grid = link_grid.box
                   AND traffic.period @> rainfall.period
                   WHERE traffic.toid %s
                   AND EXTRACT(HOUR FROM lower(traffic.period)) %s
                   AND EXTRACT(DOW FROM lower(traffic.period)) %s
                   GROUP BY traffic.toid, traffic.period, traffic.journey_time;
        """ % (traffic_table, rainfall_table, toid_condition, hours_condition, days_condition)

        self.__cur.execute(query)
        toid_time_depth = self.__cur.fetchall()

        return toid_time_depth

    def __get_condition(self, values):

        if len(values) == 1:
            v = values[0]

            if type(v) == str:
                return "= '%s'" % v
            else:
                return "= %s" % v

        if type(values[0]) == int:
            minimum = min(values)
            maximum = max(values)
            compare_tuple = tuple(range(minimum, maximum + 1))

            if compare_tuple == values:
                return "BETWEEN %s AND %s" % (minimum, maximum)

        return "IN %s" % str(tuple(values))

    def __get_data(self, traffic_table, rainfall_table, roads, natures, hours, days):
        """
        :param roads: list of (column, column_value) eg (street, "OXFORD STREET")
        :param natures: list of natures
        :param hours: tuple of hours
        :param weekdays: tuple of weekdays
        :return: dataframe with columns depth, speed, nature, identifier
        """
        toid_info = self.__get_toids(roads, natures)
        toid_time_depth = self.__get_time_depth(traffic_table, rainfall_table, toid_info.keys(), hours, days)

        pd_data = []

        for toid, time, depth, hour, dow in toid_time_depth:
            length, nature, identifier = toid_info[toid]
            pd_data.append(((2.23694 * (length) / (float(time) / 100)), float(depth), nature, identifier, hour, dow))

        if not len(pd_data):
            speed, depth, natures, identifiers, hours, dows = [], [], [], [], [], []
        else:
            speed, depth, natures, identifiers, hours, dows = zip(*pd_data)

        df = pd.DataFrame({'depth':depth, 'speed':speed, 'nature':natures, 'identifier':identifiers, 'hour':hours, 'dow':dows})

        return df

    def get_data(self, traffic_table, rainfall_table,  roads, natures, hours, days):

        return self.__get_data(traffic_table, rainfall_table, roads, natures, hours, days)
