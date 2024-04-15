-- Creates a table out of the onet data that adds title and description embeddings to
-- the onet data. This is done by joining the onet data with the embeddings table on the
-- index column.
CREATE OR REPLACE TABLE onet_with_embeddings AS
SELECT
    data.index AS ONET_INDEX,
    data.titles AS ONET_TITLES,
    data.onetsoc_code AS ONET_ONETSOC_CODE,
    data.descriptions AS ONET_DESCRIPTIONS,
    data.median_salary AS MEDIAN_SALARY,
    data.titles_embeddings AS TITLE_EMBEDDINGS,
    data.descriptions_embeddings AS DESCRIPTION_EMBEDDINGS,
	$model_version AS MODEL_VERSION
FROM data

