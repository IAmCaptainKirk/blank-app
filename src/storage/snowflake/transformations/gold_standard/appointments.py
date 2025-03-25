import pandas as pd
import numpy as np

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

class GoldStandardAppointmentsTransformation:
    def __init__(self, session):
        self.session = session

    def get_data(self):
        appointments_query = """
            SELECT 
                created_at, 
                id, 
                IFNULL(tbl_master_opportunities.area, fm_area) area, 
                sets AS GOALS, 
                NULL AS PROFILE_PICTURE 
            FROM analytics.reporting.tbl_master_opportunities 
            LEFT JOIN operational.enrichment.vw_area_goals 
                ON tbl_master_opportunities.area = vw_area_goals.area
            WHERE CREATED_AT >= DATEADD("day", -30, CURRENT_DATE) 
            AND IFNULL(tbl_master_opportunities.area, fm_area) IN (
                'Salem', 'North Portland', 'Des Moines', 'Minneapolis', 'Portland',
                'Pasco', 'Medford', 'Bozeman', 'Cincinnati', 'Helena', 
                'Cedar Rapids', 'Missoula', 'Puget Sound', 'Spokane', 'Bend',
                'Billings', 'Utah'
            )
            AND lead_generator IS NOT NULL
        """
        return self.session.sql(appointments_query).to_pandas()

    def transform(self, start_date, end_date):
        df = self.get_data()

        df['CREATED_AT'] = pd.to_datetime(df['CREATED_AT']).dt.date

        date_range = pd.date_range(start=start_date, end=end_date)

        # 4. Build a dictionary of daily goals from the first value we see in Snowflake's GOALS
        #    (If your Snowflake data truly has different daily goals by date, adjust accordingly.)
        daily_goals_dict = (
            df.groupby('AREA', as_index=False)
            .agg({'GOALS': 'first'})
            .set_index('AREA')['GOALS']
            .to_dict()
        )

        # 5. Default profile picture URL
        default_profile_picture = 'https://res.cloudinary.com/dwuzrptk6/image/upload/v1730865202/Group_1127_zhbvez.png'

        # 6. Build a "goals_df" with one row per (area, date), 
        #    setting weekend goals to 0 exactly as the original code did.
        all_areas = df['AREA'].unique().tolist()
        goals_df = pd.DataFrame(
            [
                (
                    area,
                    daily_goals_dict.get(area, 0) if single_date.weekday() < 5 else 0,
                    single_date.date(),
                    profile_pictures.get(area, default_profile_picture)
                )
                for area in all_areas
                for single_date in date_range
            ],
            columns=['AREA', 'GOALS', 'CREATED_AT', 'PROFILE_PICTURE']
        )

        # 7. Convert CREATED_AT to date in goals_df
        goals_df['CREATED_AT'] = pd.to_datetime(goals_df['CREATED_AT']).dt.date

        # 8. Drop 'GOALS' and 'PROFILE_PICTURE' from the original df to avoid conflicts
        df = df.drop(columns=['GOALS', 'PROFILE_PICTURE'])

        # 9. Merge appointments data with our artificial daily goals data
        df = df.merge(goals_df, on=['AREA', 'CREATED_AT'], how='outer')

        # 10. Filter for the selected date range
        df = df[(df['CREATED_AT'] >= start_date) & (df['CREATED_AT'] <= end_date)]

        # 11. Group by AREA, CREATED_AT to get daily totals
        daily_df = df.groupby(['AREA', 'CREATED_AT']).agg({
            'ID': 'count',
            'GOALS': 'first',  # same daily goal per area & day
            'PROFILE_PICTURE': 'first'
        }).reset_index()

        # 12. Sum over the date range per AREA
        df_groupby = daily_df.groupby('AREA').agg({
            'ID': 'sum',
            'GOALS': 'sum',
            'PROFILE_PICTURE': 'first'
        }).reset_index()

        # 13. Fill NaNs in GOALS before casting
        df_groupby['GOALS'] = df_groupby['GOALS'].fillna(0).astype(int)

        # 14. Clean up PROFILE_PICTURE
        df_groupby['PROFILE_PICTURE'].replace('', np.nan, inplace=True)
        df_groupby['PROFILE_PICTURE'] = df_groupby['PROFILE_PICTURE'].fillna(default_profile_picture)

        # 15. Convert ID to int
        df_groupby['ID'] = pd.to_numeric(df_groupby['ID'], errors='coerce').fillna(0).astype(int)

        # 16. Calculate Percent of Total (ID / GOALS)
        df_groupby['Percent of Total'] = np.where(
            df_groupby['GOALS'] != 0,
            (df_groupby['ID'] / df_groupby['GOALS']).round(2),
            0
        )

        # 17. Sort final data by AREA
        df_groupby = df_groupby.sort_values(by='AREA')

        return df_groupby