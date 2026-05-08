-- SQL script to create a read-only DBRE agent user
-- Run this on your MySQL server to create the agent user

-- Create the user (adjust host as needed: '%' for remote, 'localhost' for local)
CREATE USER IF NOT EXISTS 'dbre_agent'@'%' IDENTIFIED BY 'your_secure_password_here';

-- Grant read-only privileges on information_schema (for processlist, variables, etc.)
GRANT SELECT ON information_schema.* TO 'dbre_agent'@'%';

-- Grant read-only privileges on performance_schema (for thread stats, metrics)
GRANT SELECT ON performance_schema.* TO 'dbre_agent'@'%';

-- Grant SHOW privileges for status, variables, replication, etc.
GRANT SHOW VIEW ON *.* TO 'dbre_agent'@'%';

-- Grant REPLICATION CLIENT for SHOW SLAVE/REPLICA STATUS
GRANT REPLICATION CLIENT ON *.* TO 'dbre_agent'@'%';

-- Grant REPLICATION SLAVE for replication monitoring
GRANT REPLICATION SLAVE ON *.* TO 'dbre_agent'@'%';

-- Grant PROCESS for SHOW PROCESSLIST
GRANT PROCESS ON *.* TO 'dbre_agent'@'%';

-- Grant usage for basic connection
GRANT USAGE ON *.* TO 'dbre_agent'@'%';

-- Apply changes
FLUSH PRIVILEGES;

-- Verify the grants
SHOW GRANTS FOR 'dbre_agent'@'%';

-- Note: This user can ONLY:
-- - SELECT from information_schema and performance_schema
-- - SHOW GLOBAL STATUS, SHOW GLOBAL VARIABLES
-- - SHOW PROCESSLIST
-- - SHOW REPLICA/SLAVE STATUS
-- - SHOW REPLICA/SLAVE HOSTS
-- - SHOW ENGINE INNODB STATUS
--
-- This user CANNOT:
-- - SELECT/UPDATE/DELETE/INSERT from user databases (unless explicitly granted)
-- - DROP any tables or databases
-- - ALTER any tables
-- - Execute any write operations
