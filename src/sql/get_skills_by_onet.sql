WITH dwas AS (
  SELECT * FROM read_csv('data/dwas.txt', delim='\t')
),
task_to_dwas AS (
  SELECT * FROM read_csv('data/task_to_dwa.txt', delim='\t')
),
filtered_task_to_dwas AS (
  SELECT *
  FROM task_to_dwas
  WHERE replace(replace("O*NET-SOC Code", '-', ''), '.', '') IN (
    SELECT UNNEST($ONET_CODE)
  )
)
SELECT DISTINCT dwas."DWA Title" AS "Associated Skills"
FROM dwas
INNER JOIN filtered_task_to_dwas ON dwas."DWA ID" = filtered_task_to_dwas."DWA ID";
