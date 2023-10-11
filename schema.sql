DROP DATABASE IF EXISTS `balance`;
CREATE DATABASE `balance`;
USE `balance`;

CREATE TABLE `Positions` (
    `positions_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `position_name` varchar(300) NOT NULL,
    `hourly_rate` int NOT NULL,
    PRIMARY KEY (
        `positions_id`
    ),
    CONSTRAINT `max_rate` CHECK (hourly_rate <= 100)
);

CREATE TABLE `Employees` (
    `employee_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `employee_name` varchar(100) NOT NULL ,
    `positions_id` int UNSIGNED NOT NULL ,
    PRIMARY KEY (
        `employee_id`
    ),
    FOREIGN KEY(`positions_id`) REFERENCES `Positions` (`positions_id`)
);

CREATE TABLE `Tasks` (
    `task_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `task_name` varchar(300) NOT NULL ,
    PRIMARY KEY (
        `task_id`
    )
);

CREATE TABLE `Timesheet` (
    `timesheet_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `employee_id` int UNSIGNED NOT NULL ,
    `task_id` int UNSIGNED NOT NULL ,
    `start_time` datetime NOT NULL ,
    `end_time` datetime NOT NULL ,
    PRIMARY KEY (
        `timesheet_id`
    ),
    FOREIGN KEY(`employee_id`) REFERENCES `Employees` (`employee_id`),
    FOREIGN KEY(`task_id`) REFERENCES `Tasks` (`task_id`) ON DELETE CASCADE
);

DELIMITER //
CREATE TRIGGER check_timesheet_overlap
BEFORE INSERT ON Timesheet FOR EACH ROW
BEGIN
  DECLARE timesheet_overlap_count INT;

  SELECT COUNT(1)
  INTO timesheet_overlap_count
  FROM Timesheet
  WHERE employee_id = NEW.employee_id
    AND (
      (NEW.start_time BETWEEN start_time AND end_time)
      OR (NEW.end_time BETWEEN start_time AND end_time)
      OR (start_time BETWEEN NEW.start_time AND NEW.end_time)
    );

  IF (timesheet_overlap_count > 0) THEN
    SIGNAL SQLSTATE '45003'
    SET MESSAGE_TEXT = 'The new timesheet entry overlaps with an existing timesheet entry for this employee.';
  END IF;

END;//
DELIMITER ;

DELIMITER //
CREATE TRIGGER check_timesheet_overlap_update
BEFORE UPDATE ON Timesheet FOR EACH ROW
BEGIN
  DECLARE timesheet_overlap_count INT;

  SELECT COUNT(1)
  INTO timesheet_overlap_count
  FROM Timesheet
  WHERE employee_id = NEW.employee_id
    AND timesheet_id <> OLD.timesheet_id
    AND (
      (NEW.start_time BETWEEN start_time AND end_time)
      OR (NEW.end_time BETWEEN start_time AND end_time)
      OR (start_time BETWEEN NEW.start_time AND NEW.end_time)
    );

  IF (timesheet_overlap_count > 0) THEN
    SIGNAL SQLSTATE '45003'
    SET MESSAGE_TEXT = 'The updated timesheet entry overlaps with an existing timesheet entry for this employee.';
  END IF;

END;//
DELIMITER ;
