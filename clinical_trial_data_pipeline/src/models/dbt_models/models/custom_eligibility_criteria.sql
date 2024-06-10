WITH base AS (
    SELECT
        nct_id,brief_title,
        CONCAT(
            'Gender applicable is ', sex, 
            ',minimum age is ', minimum_age, 
            ',maximum age is ', maximum_age, 
            ',and with eligibility criteria of', eligibility_criteria
        ) AS custom_criteria
    FROM {{ source('clinical_trial_data', 'studies') }}
)

SELECT * FROM base