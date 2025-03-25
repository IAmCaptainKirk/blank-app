import pandas as pd
import numpy as np
from datetime import datetime

profile_pictures = {
    'Salem': 'https://res.cloudinary.com/dwuzrptk6/image/upload/v1730863720/salem_eckoe1.png',
    'Portland North': 'https://res.cloudinary.com/dwuzrptk6/image/upload/v1730865202/Group_1127_zhbvez.png',
    'Des Moines': 'https://res.cloudinary.com/dwuzrptk6/image/upload/v1730863717/des_moines_mcwvbz.png',
    'Minneapolis': 'https://res.cloudinary.com/dwuzrptk6/image/upload/v1730863713/minneapolis_jlnpqw.png',
    'Portland': 'https://res.cloudinary.com/dwuzrptk6/image/upload/v1730863714/portland_iwid9m.png',
    'Pasco': 'https://res.cloudinary.com/dwuzrptk6/image/upload/v1730863718/pasco_fxdzsg.png',
    'Medford': 'https://res.cloudinary.com/dwuzrptk6/image/upload/v1730863720/medford_ks5ol1.png',
    'Bozeman': 'https://res.cloudinary.com/dwuzrptk6/image/upload/v1730863714/bozeman_z1dcyw.png',
    'Cincinnati': 'https://res.cloudinary.com/dwuzrptk6/image/upload/v1733779348/Cincinnati_2-Photoroom_rxg5dz.png',
    'Helena': 'https://res.cloudinary.com/dwuzrptk6/image/upload/v1730863713/helena_b0lpfy.png',
    'Cedar Rapids': 'https://res.cloudinary.com/dwuzrptk6/image/upload/v1730865480/Group_1128_bckfag.png',
    'Missoula': 'https://res.cloudinary.com/dwuzrptk6/image/upload/v1730863715/missoulda_lmfros.png',
    'Puget Sound': 'https://res.cloudinary.com/dwuzrptk6/image/upload/v1733779404/PugetSound-Photoroom_wmj5k7.png',
    'Spokane': 'https://res.cloudinary.com/dwuzrptk6/image/upload/v1730863715/spokane_i8tixp.png',
    'Bend': 'https://res.cloudinary.com/dwuzrptk6/image/upload/v1730863714/bend_dvre85.png',
    'Billings': 'https://res.cloudinary.com/dwuzrptk6/image/upload/v1730863716/billings_hezzk6.png',
    'Utah': 'https://res.cloudinary.com/dwuzrptk6/image/upload/v1733790161/Asset_2_zfodre.png'
}

class GoldStandardSalesTransformation:
    def __init__(self, session):
        self.session = session

    def get_data(self, month, year):
        query = """
            SELECT 
                sale_date,
                id,
                tbl_master_opportunities.area,
                min_goal,
                max_goal,
                DAYOFMONTH(CURRENT_DATE) as day_of_month,
                RIGHT(LAST_DAY(CURRENT_DATE()),2) as days_in_month,
                1 - ROUND(DAYOFMONTH(CURRENT_DATE()) / RIGHT(LAST_DAY(CURRENT_DATE()),2),2) as percent_of_month_left,
                SUM(CASE WHEN sale_date >= DATEADD("day", -30, CURRENT_DATE()) THEN 1 ELSE 0 END) OVER(PARTITION BY tbl_master_opportunities.area) as last_30_day_sales,
                SUM(CASE WHEN YEAR(sale_date) = YEAR(CURRENT_DATE()) AND MONTH(sale_date) = MONTH(CURRENT_DATE()) THEN 1 ELSE 0 END) OVER(PARTITION BY tbl_master_opportunities.area) as current_month_sales,
                FLOOR((last_30_day_sales * percent_of_month_left) + current_month_sales) as pace
            FROM 
                analytics.reporting.tbl_master_opportunities
            LEFT JOIN operational.enrichment.vw_area_goals 
                ON tbl_master_opportunities.area = vw_area_goals.area
            WHERE sale_date >= DATEADD("month", -6, CURRENT_DATE())
            AND grand_total > 0
            AND tbl_master_opportunities.area IN (
                'Salem', 'North Portland', 'Des Moines', 'Minneapolis', 'Portland',
                'Pasco', 'Medford', 'Bozeman', 'Cincinnati', 'Helena', 
                'Cedar Rapids', 'Missoula', 'Puget Sound', 'Spokane', 'Bend',
                'Billings', 'Utah'
            )
        """
        return self.session.sql(query).to_pandas()

    def transform(self, month, year):
        # 1. Fetch sales data for the selected month and year
        df = self.get_data(month, year)

        if df.empty:
            return pd.DataFrame()

        # 2. Convert 'SALE_DATE' to date in df
        df['SALE_DATE'] = pd.to_datetime(df['SALE_DATE']).dt.date

        # 3. Grab the 'PACE' value by area (as you already do)
        pace_df = df.groupby('AREA').agg({'PACE': 'first'}).reset_index()

        # 4. Define the start/end dates for the selected month/year
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - pd.Timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - pd.Timedelta(days=1)
        
        # 5. Create a date range for the selected month
        date_range = pd.date_range(start=start_date, end=end_date)
        
        # 6. Create a cross-join (area × day) so we have rows for days with no sales
        all_areas = df['AREA'].unique().tolist()
        cross_join_list = []
        default_profile_picture = 'https://res.cloudinary.com/dwuzrptk6/image/upload/v1730865202/Group_1127_zhbvez.png'

        for area in all_areas:
            for single_date in date_range:
                cross_join_list.append({
                    'AREA': area,
                    'SALE_DATE': single_date.date(),
                    'PROFILE_PICTURE': profile_pictures.get(area, default_profile_picture)
                })
        
        cross_df = pd.DataFrame(cross_join_list)

        # 7. Merge sales data with cross-join to fill missing days
        #    This brings in min_goal and max_goal from your Snowflake query where they exist.
        df = df.merge(cross_df, on=['AREA', 'SALE_DATE'], how='right')

        # 8. Filter for the selected date range
        df = df[(df['SALE_DATE'] >= start_date) & (df['SALE_DATE'] <= end_date)]

        # 9. Group by area & sale_date to get daily totals
        #    - We use 'first' for MIN_GOAL/MAX_GOAL. If your data actually has daily variations,
        #      switch to something like sum, max, or an average as needed.
        daily_df = df.groupby(['AREA', 'SALE_DATE'], as_index=False).agg({
            'ID': 'count',
            'MIN_GOAL': 'first',
            'MAX_GOAL': 'first',
            'PROFILE_PICTURE': 'first'
        })

        # 10. Sum over the date range per AREA
        df_groupby = daily_df.groupby('AREA', as_index=False).agg({
            'ID': 'sum',
            'MIN_GOAL': 'first',  # If the same goal is repeated daily, 'first' is fine
            'MAX_GOAL': 'first',
            'PROFILE_PICTURE': 'first'
        })

        # 11. Merge pace info
        df_groupby = df_groupby.merge(pace_df, on='AREA', how='left')
        df_groupby['PACE'] = df_groupby['PACE'].fillna(0).astype(int)

        # 12. Clean up data types and missing values
        df_groupby['MIN_GOAL'] = pd.to_numeric(df_groupby['MIN_GOAL'], errors='coerce').fillna(0).astype(int)
        df_groupby['MAX_GOAL'] = pd.to_numeric(df_groupby['MAX_GOAL'], errors='coerce').fillna(0).astype(int)
        df_groupby['ID'] = pd.to_numeric(df_groupby['ID'], errors='coerce').fillna(0).astype(int)
        df_groupby['PROFILE_PICTURE'].replace('', np.nan, inplace=True)
        df_groupby['PROFILE_PICTURE'] = df_groupby['PROFILE_PICTURE'].fillna(default_profile_picture)

        # 13. Calculate percentages vs. min_goal and max_goal
        df_groupby['PERCENT_OF_MIN_TOTAL'] = np.where(
            df_groupby['MIN_GOAL'] != 0,
            (df_groupby['ID'] / df_groupby['MIN_GOAL']).round(2),
            0
        )
        df_groupby['PERCENT_OF_MAX_TOTAL'] = np.where(
            df_groupby['MAX_GOAL'] != 0,
            (df_groupby['ID'] / df_groupby['MAX_GOAL']).round(2),
            0
        )

        # 14. Sort by AREA and return
        df_groupby = df_groupby.sort_values(by='AREA').reset_index(drop=True)
        return df_groupby