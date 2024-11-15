import numpy as np
import logging
import pandas as pd

STORE_COLUMN = 'store_id'
DATE_COLUMN = 'created_at'
DELIVERY_COLUMN = 'actual_delivery_time'
STORE_COLUMNS = 'store_id'
ORDER_PLACE_DURATION_COLUMN = 'estimated_order_place_duration'
STORE_CLIENT_DURATION_COLUMN = 'estimated_store_to_consumer_driving_duration'
SUBTOTAL_COLUMN = 'subtotal'
TOTAL_DASHERS_COLUMN = 'total_onshift_dashers'
BUSY_DASHERS_COLUMN = 'total_busy_dashers'
AVAILABLE_DASHERS_COLUMN = 'availabe_dashers_onshift'
TOTAL_ORDERS = 'total_outstanding_orders'
class DataCleaner:
    @staticmethod
    def add_temporal_variables(data: pd.DataFrame):
        """
        From a date column, extract the weekday, hour, time_of_day and weekend
        """
        # temporal variables
        data['weekday'] = data[DATE_COLUMN].dt.weekday
        data["weekend"] = (data['weekday'] > 4).astype(int)
        data['hour'] = data[DATE_COLUMN].dt.hour

        def categorize_time_of_day(hour):
            if 5 < hour < 12:
                return 'Morning'
            elif hour < 17:
                return 'Afternoon'
            elif hour < 21:
                return 'Evening'
            else:  # Above 21 or below 5
                return 'Night'

        data['time_of_day'] = data.apply(lambda row: categorize_time_of_day(row['hour']), axis=1)
        return data

    @staticmethod
    def add_target_variables(data: pd.DataFrame, delivery_threshold=3):
        """
        From a date column, extract the weekday, hour, time_of_day and weekedn
        """
        data['estimated_delivery_time'] = data['estimated_order_place_duration'] + data[STORE_CLIENT_DURATION_COLUMN]
        data['delivery_time'] = (data[DELIVERY_COLUMN] - data[DATE_COLUMN]) / pd.Timedelta(seconds=1)
        data['delivery_time_hours'] = data['delivery_time']/3600.0
        data = data.loc[data['delivery_time_hours'].le(delivery_threshold)]
        return data

    @staticmethod
    def remove_negative_values(data: pd.DataFrame):
        """
        From a date column, extract the weekday, hour, time_of_day and weekedn
        """
        data[AVAILABLE_DASHERS_COLUMN] = (data[TOTAL_DASHERS_COLUMN] - data[BUSY_DASHERS_COLUMN]).clip(lower=0)
        numeric_columns = [SUBTOTAL_COLUMN, TOTAL_DASHERS_COLUMN, BUSY_DASHERS_COLUMN, TOTAL_ORDERS]
        data = data.loc[~(data[numeric_columns] < 0).any(axis=1)]
        data = data.drop(BUSY_DASHERS_COLUMN, axis=1)
        return data


    @staticmethod
    def clean_conflict_category(
            data: pd.DataFrame,
            columns_to_be_corrected=['market_id', 'store_primary_category']
    ):
        """
        From a date column, extract the weekday, hour, time_of_day and weekedn
        """
        for column in columns_to_be_corrected:
            group_data = data \
                .groupby([column, STORE_COLUMN], as_index=False) \
                .agg(first_date=(DATE_COLUMN, 'min'), n_rows=(DATE_COLUMN, 'count'))
            group_data_max_count = group_data.groupby(STORE_COLUMN, as_index=False).agg({'n_rows': 'max'})
            group_data_filtered = group_data.merge(group_data_max_count, how='inner', on=[STORE_COLUMN, 'n_rows'])
            group_data_min_date = group_data_filtered.groupby(STORE_COLUMN, as_index=False).agg({'first_date': 'min'})
            group_data_unique = \
                group_data_filtered.merge(group_data_min_date, how='inner', on=[STORE_COLUMN, 'first_date'])
            data = data.drop(column, axis=1)
            data = data.merge(group_data_unique[[STORE_COLUMN, column]], how='left', on=[STORE_COLUMN])
        return data
