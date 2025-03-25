class GoldStandardTeamMemberRepository:
    def __init__(self, session):
        self.session = session

    def find_all(self):
        query = """
SELECT 
    MAX(
        IFNULL("opportunities.current_month_sales_calc", 0) + 
        IFNULL("opportunities.current_month_assists", 0)
    ) AS current_month_sales_and_assists,

    MAX(
        IFNULL("opportunities.previous_month_sales_calc", 0) + 
        IFNULL("opportunities.previous_month_assists", 0)
    ) AS previous_month_sales_and_assists,

    "user.name" AS name,
    "team_members.effective_date" AS date,

    IFNULL(
        "user.picture_link", 
        'https://res.cloudinary.com/dwuzrptk6/image/upload/v1730865202/Group_1127_zhbvez.png'
    ) AS picture_link,

    8 AS GOAL

FROM analytics.reporting.tbl_team_members

WHERE "user.name" IN (
     'Adam Ayase'
    , 'Adam Kalous'
    , 'Alesi Radnovich'
    , 'Austin Lowe'
    , 'Anthony Rivero'
    , 'Anthony Tang'
    , 'Bryan Bodnar'
    , 'Benjamin Toala'
    , 'Brooks Haas'
    , 'Brady Reinwald'
    , 'Brandon Thornton'
    , 'Caleb Phillips'
    , 'Barson Beus'
    , 'Chris Bouchard'
    , 'Chris Nelson'
    , 'Daniel Blankenship'
    , 'Devon Fish'
    , 'Donovan Lewis'
    , 'Dylan Garcia'
    , 'Enzo Couillens'
    , 'Eric Feldman'
    , 'Jack McCoy'
    , 'Jordan Nesbitt'
    , 'Justic Brewton'
    , 'Justin Smith'
    , 'Kevin Judd'
    , 'Kyle Giffen'
    , 'Lex Minniear'
    , 'Lily Meadows'
    , 'Madison Leonelli'
    , 'Marco Ayase'
    , 'Mariana Flores'
    , 'Michael Browne'
    , 'Nicholas Sowers'
    , 'Nicholas Ventura'
    , 'Orlando Sanchez'
    , 'Rian Wright'
    , 'Ryan Reeves'
    , 'Sean Mcfatridge'
    , 'Seth Groth'
    , 'Tareq Butler'
    , 'Thomas Rodemeyer'
    , 'Trevor Thornton'
    , 'Wendy Radnovich'
)

GROUP BY ALL

QUALIFY ROW_NUMBER() OVER (
    PARTITION BY "user.name"
    ORDER BY "team_members.effective_date" DESC
) = 1;
        """
        return self.session.sql(query).to_pandas()
