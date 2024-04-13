-- Reads in the occupation data from the ONET database and
-- joins it with the median salary data from the government database
WITH onet AS (
    SELECT
        replace(replace(occ.onetsoc_code, '-', ''), '.', '') AS onetsoc_code,
        occ.title AS titles,
        occ.description AS descriptions,
        roles.median_salary
    FROM rds_dev.onet.occupation_data occ
    INNER JOIN rds_dev.government_data.onet_roles roles
        ON roles.onetsoc_code = replace(replace(occ.onetsoc_code, '-', ''), '.', '')
)
SELECT
    onet.*,
    ROW_NUMBER() OVER (ORDER BY onet.titles DESC) AS index
FROM onet
LIMIT $lmt
;
