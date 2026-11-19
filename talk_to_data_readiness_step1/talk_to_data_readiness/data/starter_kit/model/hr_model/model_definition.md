# Semantic model: "Workforce_Analytics_Model"

## Tables and columns (as named in the source)

| Table | Columns |
|---|---|
| F_ATTENDANCE | ATTENDANCE_ID, EMPLOYEE_ID, DATE_KEY, HOURS_WORKED, OVERTIME_HOURS, STATUS_CD |
| D_EMPLOYEE | EMPLOYEE_ID, EMPLOYEE_NAME, DEPARTMENT_ID, MANAGER_ID, HIRE_DATE, EMPLOYMENT_TYPE, SALARY, EMAIL |
| D_DEPARTMENT | DEPARTMENT_ID, DEPARTMENT_NAME, BUSINESS_UNIT, LOCATION |
| D_DATE | DATE_KEY, FULL_DATE, YEAR, QUARTER, MONTH, MONTH_NAME, YEAR_MONTH |
| F_RECRUITMENT | CANDIDATE_ID, DEPARTMENT_ID, RECRUITER_ID, APPLIED_DATE_KEY, HIRED_DATE_KEY, STATUS_CD, TIME_TO_HIRE |

No table or column has a description. All columns are visible. Numeric columns keep default "Sum" summarization, including identifiers and YEAR.

## Relationships

| From | To | Cardinality | Active | Cross-filter |
|---|---|---|---|---|
| F_ATTENDANCE[EMPLOYEE_ID] | D_EMPLOYEE[EMPLOYEE_ID] | many-to-one | Yes | Single |
| F_ATTENDANCE[DATE_KEY] | D_DATE[DATE_KEY] | many-to-one | Yes | Single |
| D_EMPLOYEE[DEPARTMENT_ID] | D_DEPARTMENT[DEPARTMENT_ID] | many-to-one | Yes | Both |
| F_RECRUITMENT[DEPARTMENT_ID] | D_DEPARTMENT[DEPARTMENT_ID] | many-to-one | Yes | Single |
| F_RECRUITMENT[APPLIED_DATE_KEY] | D_DATE[DATE_KEY] | many-to-one | Yes | Single |
| F_RECRUITMENT[HIRED_DATE_KEY] | D_DATE[DATE_KEY] | many-to-one | No | Single |

D_DATE is not marked as a date table. MONTH_NAME is not sorted by MONTH.

## Measures (in table F_ATTENDANCE)

```dax
Total Employees = DISTINCTCOUNT ( D_EMPLOYEE[EMPLOYEE_ID] )
Attendance Hours = SUM ( F_ATTENDANCE[HOURS_WORKED] )
Overtime Hours = SUM ( F_ATTENDANCE[OVERTIME_HOURS] )
Average Working Hours = AVERAGE ( F_ATTENDANCE[HOURS_WORKED] )
Absent Count = COUNTROWS ( FILTER ( F_ATTENDANCE, F_ATTENDANCE[STATUS_CD] = "A" ) )
Attrition Rate = DIVIDE ( [Exited Employees], [Total Employees] )
Exited Employees = DISTINCTCOUNT ( D_EMPLOYEE[EMPLOYEE_ID] )
Average Time to Hire = AVERAGE ( F_RECRUITMENT[TIME_TO_HIRE] )
```

## What the codes mean

- F_ATTENDANCE[STATUS_CD]: P = Present, A = Absent, L = Leave.
- F_RECRUITMENT[STATUS_CD]: A = Applied, S = Screening, I = Interview, O = Offered, H = Hired, R = Rejected.
- D_EMPLOYEE[EMPLOYMENT_TYPE]: F = Full-time, C = Contract, I = Intern.
- D_DEPARTMENT[BUSINESS_UNIT]: T = Technology, F = Finance, S = Sales, O = Operations.

## Business context

The model supports workforce attendance, employee information, departmental analysis, and recruitment reporting. Employee salary and email are sensitive employee attributes and should not be exposed indiscriminately in natural-language analytics.

The data covers the reporting period from January 2025 to December 2026.