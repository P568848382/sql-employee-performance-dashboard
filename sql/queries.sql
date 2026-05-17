--The 8 Business Queries
--columns are:-
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
"terminationdescription"			"character varying"
"departmenttype"					"character varying"
"division"							"character varying"
"empid"								"character varying"
"state"								"character varying"
"jobfunctiondescription"			"character varying"
"gendercode"						"character varying"
"locationcode"						"character varying"
"racedesc"							"character varying"
"maritaldesc"						"character varying"
"performance_score"					"character varying"
"firstname"							"character varying"
"lastname"							"character varying"
"startdate"							"character varying"
"exitdate"							"character varying"
"title"								"character varying"
"supervisor"						"character varying"
"ademail"							"character varying"
"businessunit"						"character varying"
"employeestatus"					"character varying"
"employeetype"						"character varying"
*/


--1.Rank Employees Within Each Department by Salary
-- ============================================================
-- Query 1: Salary Ranking Within Each Department
-- Demonstrates: RANK(), DENSE_RANK(), ROW_NUMBER()
-- Business Question: Who are the top earners per department?
-- ============================================================
select empid,
	   firstname ||' '||lastname employee_name,
	   departmenttype,
	   title,
	   payzone,
	   monthly_salary,
	   performance_score,
	   dense_rank()over(partition by departmenttype order by monthly_salary desc) as d_rnk_in_dept,
	   rank()over(partition by departmenttype order by monthly_salary desc) as rnk_in_dept,
	   row_number()over(partition by departmenttype order by monthly_salary desc) as row_num_in_dept,
	   count(*)over(partition by departmenttype) as dept_headcount
from employee_performance
where is_terminated=0
order by departmenttype,rnk_in_dept;
	   
-- 2.Employee Salary vs Department Average
-- ============================================================
-- Query 2: Individual Salary vs Department Average
-- Demonstrates: AVG() OVER(PARTITION BY)
-- Business Question: Which employees are outliers in their dept?
-- ============================================================
with dept_comparison as(
select  empid,
		firstname||' '||lastname as employee_name,
		departmenttype,
		businessunit,
		title,
	    payzone,
		monthly_salary,
		performance_score,
		round(avg(monthly_salary)over(partition by departmenttype),2) as dept_avg_salary,
		round(max(monthly_salary)over(partition by departmenttype),2) as dept_max_salary,
		round(min(monthly_salary)over(partition by departmenttype),2) as dept_min_salary
from employee_performance
where is_terminated=0
)
select empid,
       employee_name,
	   departmenttype,
	   title,
	   payzone,
	   monthly_salary,
	   dept_avg_salary,
	   round(monthly_salary - dept_avg_salary,2) as diff_from_dept_avg,
	   round(
			(monthly_salary - dept_avg_salary)*100.0
			/dept_avg_salary,2
	   )  as pct_vs_dept_avg,
	   case
	   		when monthly_salary > dept_avg_salary*1.20 then 'Significantly Above'
			when monthly_salary > dept_avg_salary then 'Above Average'
			when monthly_salary < dept_avg_salary*0.8 then 'Significantly Below'
			when monthly_salary < dept_avg_salary  then 'Below Average'
			else 'At Average'
		end   as salary_position
from dept_comparison
order by departmenttype,pct_vs_dept_avg desc;

-- 3.Top 10% Earners Company-Wide
-- ============================================================
-- Query 3: Top 10% Earners Across Entire Company
-- Demonstrates: NTILE(10), PERCENT_RANK()
-- ============================================================
with salary_percentile as(
select empid,
	   firstname||' '||lastname as employee_name,
	   departmenttype,
	   title,
	   payzone,
	   monthly_salary,
	   annual_salary,
	   performance_score,
	   state,
	   ntile(10)over(order by monthly_salary desc) as income_decile,
	   
		percent_rank()over(order by monthly_salary)*100
	    as percent_rank_pct
from employee_performance
where is_terminated=0
)
select empid,
	   employee_name,
	   departmenttype,
	   title,
	   payzone,
	   monthly_salary,
	   annual_salary,
	   income_decile,
	   percent_rank_pct,
	   case 
	   		when income_decile = 1 then 'TOP 10%'
			when income_decile <=3 then 'TOP 30%'
			when income_decile <=5 then 'TOP 50%'
			else 'Bottom 50%'
		end as income_tier
from salary_percentile
order by monthly_salary desc;

--4.Termination Rate by Department and Termination Type.
-- ============================================================
-- Query 4: Termination Analysis by Department + Type
-- This dataset has Termination Type (Resignation, Layoff,
-- Retirement) — much richer than a simple attrition flag.
-- Business Question: How and why are employees leaving?
-- ============================================================
select departmenttype,
	   terminationtype,
	   count(*) as terminated_count,
	   round(avg(tenure_years),2) as avg_tenure_at_exit,
	   round(avg(monthly_salary),2) as avg_monthly_salary_at_exit,
	   round(avg(age),2) as avg_age_at_exit,
	   round(count(*)*100.0
	   		 /sum(count(*))over(),2) as pct_of_all_terminations
from employee_performance
where employeestatus in('Voluntarily Terminated','Terminated for Cause')
	  and terminationtype is not null  
group by departmenttype,
	   	 terminationtype
order by terminated_count desc;

