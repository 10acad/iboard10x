count_mdl_log = 'SELECT COUNT(*) FROM MDL_LOG'
count_mdl_course = 'SELECT COUNT(*) FROM MDL_COURSE'
list_db_tables = """
SELECT table_schema,table_name
FROM information_schema.tables
ORDER BY table_schema,table_name;
"""

quiz_submission_by_hrday = """
-- from https://tjhunt.blogspot.com/2010/03/when-do-students-submit-their-online.html
-- Number of quiz submissions by hour of day
SELECT 
    DATE_PART('hour', TIMESTAMP WITH TIME ZONE 'epoch' + timefinish * INTERVAL '1 second') AS hour,
    COUNT(1)

FROM mdl_quiz_attempts qa

WHERE
    qa.preview = 0 AND
    qa.timefinish <> 0

GROUP BY
    DATE_PART('hour', TIMESTAMP WITH TIME ZONE 'epoch' + timefinish * INTERVAL '1 second')

ORDER BY
    hour
"""

quiz_submission_before_deadline="""
-- from https://tjhunt.blogspot.com/2010/03/when-do-students-submit-their-online.html
-- Number of quiz submissions by hour before deadline
SELECT 
    (quiz.timeclose - qa.timefinish) / 3600 AS hoursbefore,
    COUNT(1)

FROM mdl_quiz_attempts qa
JOIN mdl_quiz quiz ON quiz.id = qa.quiz

WHERE
    qa.preview = 0 AND
    quiz.timeclose <> 0 AND
    qa.timefinish <> 0

GROUP BY
    (quiz.timeclose - qa.timefinish) / 3600

HAVING (quiz.timeclose - qa.timefinish) / 3600 < 24 * 7
"""

moodle_usage_summary = """
SELECT
(SELECT COUNT(id) FROM prefix_course) - 1 AS courses,
(SELECT COUNT(id) FROM prefix_user WHERE deleted = 0 AND confirmed = 1) AS users,
(SELECT COUNT(DISTINCT ra.userid)
 FROM prefix_role_capabilities rc
 JOIN prefix_role_assignments ra ON ra.roleid = rc.roleid
 WHERE rc.capability IN ('moodle/course:upd' || 'ate', 'moodle/site:doanything')) AS teachers,
(SELECT COUNT(id) FROM prefix_role_assignments) AS enrolments,
(SELECT COUNT(id) FROM prefix_forum_posts) AS forum_posts,
(SELECT COUNT(id) FROM prefix_resource) AS resources,
(SELECT COUNT(id) FROM prefix_question) AS questions
"""

monthly_usage_stat =  """
-- from https://docs.moodle.org/36/en/Custom_SQL_queries_report
SELECT 
EXTRACT(MONTH FROM to_timestamp(prefix_stats_user_monthly.timeend)) AS calendar_month,
EXTRACT(YEAR FROM to_timestamp(prefix_stats_user_monthly.timeend)) AS calendar_year,
prefix_role.name AS user_role,
COUNT(DISTINCT prefix_stats_user_monthly.userid) AS total_users
FROM
prefix_stats_user_monthly
INNER JOIN prefix_role_assignments ON prefix_stats_user_monthly.userid = prefix_role_assignments.userid
INNER JOIN prefix_context ON prefix_role_assignments.contextid = prefix_context.id
INNER JOIN prefix_role ON prefix_role_assignments.roleid = prefix_role.id
WHERE prefix_context.contextlevel = 50
AND prefix_stats_user_monthly.stattype = 'activity'
AND prefix_stats_user_monthly.courseid <>1
GROUP BY EXTRACT(MONTH FROM to_timestamp(prefix_stats_user_monthly.timeend)),
EXTRACT(YEAR FROM to_timestamp(prefix_stats_user_monthly.timeend)),
prefix_stats_user_monthly.stattype,
prefix_role.name
ORDER BY 
EXTRACT(YEAR FROM to_timestamp(prefix_stats_user_monthly.timeend)), EXTRACT(MONTH FROM to_timestamp(prefix_stats_user_monthly.timeend)),
prefix_role.name
"""
