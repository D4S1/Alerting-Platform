SELECT-- List all tables in the database
.tables

-- Show schema for each table
.schema services
.schema admins
.schema service_admins
.schema incidents
.schema contact_attempts


-- Preview data from each table
SELECT * FROM services;
SELECT * FROM admins;
SELECT * FROM service_admins;
SELECT * FROM incidents;
SELECT * FROM contact_attempts;