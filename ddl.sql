CREATE DATABASE IF NOT EXISTS pizza311bot /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_uca1400_ai_ci */;;

CREATE TABLE `users` (
  `telegram_id` int(10) unsigned NOT NULL DEFAULT 0,
  `username` varchar(100) NOT NULL,
  `is_admin` int(10) unsigned NOT NULL DEFAULT 0,
  `is_enabled` int(10) unsigned NOT NULL DEFAULT 0,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`telegram_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `riders` (
  `telegram_id` int(10) unsigned NOT NULL DEFAULT 0,
  `rider_description` text NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`telegram_id`),
  CONSTRAINT `riders_users_FK` FOREIGN KEY (`telegram_id`) REFERENCES `users` (`telegram_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `places` (
  `place_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `phone_number` varchar(100) NOT NULL,
  `address` varchar(100) NOT NULL,
  `link_pdf` varchar(1024) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`place_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `orders` (
  `order_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `total` decimal(10,2) NOT NULL DEFAULT 0.00,
  `rider_id` int(10) unsigned NOT NULL DEFAULT 0,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`order_id`),
  CONSTRAINT `orders_riders_FK` FOREIGN KEY (`rider_id`) REFERENCES `riders` (`telegram_id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `items` (
  `item_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `order_id` int(10) unsigned NOT NULL,
  `ordered_by` int(10) unsigned NOT NULL DEFAULT 0,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`item_id`),
  CONSTRAINT `items_orders_FK` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`),
  CONSTRAINT `items_users_FK` FOREIGN KEY (`ordered_by`) REFERENCES `users` (`telegram_id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- DEFAULT ADMINS
INSERT INTO users (telegram_id, username, is_admin, is_enabled) VALUES (121527971, 'Alessandro Marchioro', 1, 1);
INSERT INTO users (telegram_id, username, is_admin, is_enabled) VALUES (51194667, 'Filippo Peretti', 1, 1)