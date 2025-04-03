CREATE DATABASE IF NOT EXISTS pizza311bot /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_uca1400_ai_ci */;;

CREATE TABLE `users` (
  `id` int(10) unsigned NOT NULL DEFAULT 0,
  `username` varchar(100) NOT NULL,
  `is_admin` int(10) unsigned NOT NULL DEFAULT 0,
  `is_enabled` int(10) unsigned NOT NULL DEFAULT 0,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `riders` (
  `telegram_id` int(10) unsigned NOT NULL DEFAULT 0,
  `rider_description` text NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`telegram_id`),
  CONSTRAINT `riders_users_FK` FOREIGN KEY (`telegram_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `places` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `phone_number` varchar(100) NOT NULL,
  `address` varchar(100) NOT NULL,
  `link_pdf` varchar(1024) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `orders` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `rider_id` int(10) unsigned DEFAULT NULL,
  `event_date` datetime NOT NULL DEFAULT current_timestamp(),
  `completed` int(10) unsigned NOT NULL DEFAULT 0,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  CONSTRAINT `orders_riders_FK` FOREIGN KEY (`rider_id`) REFERENCES `riders` (`telegram_id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `items` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `order_id` int(10) unsigned NOT NULL,
  `telegram_id` int(10) unsigned NOT NULL DEFAULT 0,
  `name` varchar(100) NOT NULL,
  `price` decimal(10,2) unsigned NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  CONSTRAINT `items_orders_FK` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`),
  CONSTRAINT `items_users_FK` FOREIGN KEY (`telegram_id`) REFERENCES `users` (`id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- DEFAULT ADMINS
INSERT INTO users (id, username, is_admin, is_enabled) VALUES (121527971, 'Alessandro Marchioro', 1, 1);
INSERT INTO users (id, username, is_admin, is_enabled) VALUES (51194667, 'Filippo Peretti', 1, 1);
INSERT INTO users (id, username, is_admin, is_enabled) VALUES (19121995, 'Davide Bianchi', 1, 1);

-- INSERTING ORDER DAYS
DELIMITER //

CREATE PROCEDURE InsertThursdays()
BEGIN
    DECLARE start_date DATETIME DEFAULT '2025-01-01 19:30:00';
    DECLARE end_date DATETIME DEFAULT '2030-12-31 19:30:00';
    
    -- Find the first Thursday of 2025
    WHILE WEEKDAY(start_date) != 3 DO
        SET start_date = DATE_ADD(start_date, INTERVAL 1 DAY);
    END WHILE;
    
    -- Insert orders for each Thursday until the end of 2030
    WHILE start_date <= end_date DO
        INSERT INTO orders (event_date) VALUES (start_date);
        SET start_date = DATE_ADD(start_date, INTERVAL 7 DAY);
    END WHILE;
END //
DELIMITER ;

-- Call the procedure to perform the insertions
CALL InsertThursdays();
