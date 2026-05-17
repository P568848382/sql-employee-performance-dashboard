--Data Validation
select * from employee_performance limit 15;
select employeestatus ,count(*) as headcount
from employee_performance
group by employeestatus;
--o/p:-
/*
"employeestatus"			"headcount"
"Voluntarily Terminated"	321
"Future Start"				69
"Active"					2458
"Terminated for Cause"		66
"Leave of Absence"			86 
*/
select column_name,data_type
from information_schema.columns
where table_name='employee_performance';
/*
column_name							data_type
"performance_score_num"				"smallint"
"dob"								"date"
"current_employee_rating"			"smallint"
"start_date"						"date"
"exit_date"							"date"
"tenure_months"						"integer"
"tenure_years"						"numeric"
"age"								"smallint"
"monthly_salary"					"integer"
"annual_salary"						"integer"
"is_terminated"						"smallint"
"payzone"							"character varying"
"employeeclassificationtype"		"character varying"
"terminationtype"					"character varying"
"terminationdescription"	"character varying"
"departmenttype"	"character varying"
"division"	"character varying"
"empid"	"character varying"
"state"	"character varying"
"jobfunctiondescription"	"character varying"
"gendercode"	"character varying"
"locationcode"	"character varying"
"racedesc"	"character varying"
"maritaldesc"	"character varying"
"performance_score"	"character varying"
"firstname"	"character varying"
"lastname"	"character varying"
"startdate"	"character varying"
"exitdate"	"character varying"
"title"	"character varying"
"supervisor"	"character varying"
"ademail"	"character varying"
"businessunit"	"character varying"
"employeestatus"	"character varying"
"employeetype"	"character varying"
*/
--Shape Check
select count(*) as total_employees from employee_performance;

--Status Distribution
select employeestatus,count(*) 
from employee_performance
group by employeestatus;

---- Pay zone + salary sanity check
select payzone,
	   count(*) as headcount,
	   round(min(monthly_salary),0) as min_salary,
	   round(max(monthly_salary),0)  as max_salary,
	   round(avg(monthly_salary),0) as avg_salary
from employee_performance
group by payzone
order by payzone;

-- Performance score distribution
select performance_score,
	  count(*) as headcount
from employee_performance
group by performance_score
order by headcount desc;

---- Termination type breakdown
select terminationtype,
       count(*) as headcount
from employee_performance
group by terminationtype;

---- Department types
select departmenttype,
		count(*)
from employee_performance
group by departmenttype
order by count(*) desc;
