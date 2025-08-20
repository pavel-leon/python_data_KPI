# python_data_KPI
 learning project

The Incident Report System (IRS) is a data analytics utility designed to process exports from an ITSM platform. The ITSM platform is used to manage incidents (service disruptions) reported by clients.

IRS provides comprehensive analysis capabilities, supporting the following report types:
	1.	KPI Reports
	2.	Analytical Reports


KPI Reports

KPI reports in IRS offer the following functionality:

• Reaction Time KPI – Measures how quickly support teams acknowledge and take ownership of incoming incidents. This is a key performance indicator in incident management, helping assess the responsiveness and operational efficiency of support groups. This metric is calculated within IRS. Report shows top 10 groups with the lowest KPI's. 

• Reassignments KPI – Tracks the number of times incidents are reassigned between support groups before resolution. Frequent reassignments can delay overall resolution times, so understanding both the number and necessity of such reassignments is critical. This metric is calculated within IRS. Report shows top 10 groups with the lowest KPI's.  
• SLA KPI – Shows the percentage of incidents resolved in compliance with the Service Level Agreements (SLA) defined and automated in the ITSM platform. This metric is based on exported ITSM data. Report shows top 10 groups with the lowest KPI's. 


**Analytical Reports**

Analytical reports in IRS currently include:
• Dependency: Incidents vs. Categories (Chi²) – Automatically detects whether there is a statistical correlation between the occurrence of critical incidents and specific system categories. If a dependency is identified, further investigation into system availability, stability, and compliance with the functional requirements outlined in the technical specification is recommended. This analysis is performed within IRS.