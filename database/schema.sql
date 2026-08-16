CREATE TABLE `f_bd77265a__saved_items` (
  `id` CHAR(36) NOT NULL,
  `user_id` CHAR(36) NOT NULL,
  `item_name` VARCHAR(500) NOT NULL,
  `price` DECIMAL(10,2) NOT NULL,
  `product_link` VARCHAR(2048) NOT NULL,
  `created_at` TIMESTAMP NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE f_ed5144db__cooling_periods (
  id CHAR(36) NOT NULL,
  saved_item_id CHAR(36) NOT NULL,
  period_days INT NOT NULL,
  started_at TIMESTAMP NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP NOT NULL,
  PRIMARY KEY (id),
  CHECK (period_days IN (1, 3, 7))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- No database tables are required for feature: capability_countdown_timer_df84298e


CREATE TABLE `f_fd8968f7__scheduled_notifications` (
  `id` CHAR(36) NOT NULL,
  `item_id` CHAR(36) NOT NULL,
  `user_id` CHAR(36) NOT NULL,
  `scheduled_for` TIMESTAMP NOT NULL,
  `status` VARCHAR(20) NOT NULL,
  `sent_at` TIMESTAMP NULL,
  `notification_title` VARCHAR(100) NOT NULL,
  `notification_body` VARCHAR(200) NOT NULL,
  `deep_link_target` VARCHAR(500) NOT NULL,
  `created_at` TIMESTAMP NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE `f_c984506c__item_decisions` (
  `id` CHAR(36) NOT NULL,
  `item_id` CHAR(36) NOT NULL,
  `user_id` CHAR(36) NOT NULL,
  `decision_type` VARCHAR(4) NOT NULL,
  `item_price` DECIMAL(10,2) NOT NULL,
  `decided_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_item_decisions_user_savings` FOREIGN KEY (`user_id`) REFERENCES `f_c984506c__user_savings`(`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `f_c984506c__user_savings` (
  `id` CHAR(36) NOT NULL,
  `user_id` CHAR(36) NOT NULL,
  `total_saved` DECIMAL(12,2) NOT NULL,
  `updated_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE `f_66579af4__savings_records` (
  `id` CHAR(36) NOT NULL,
  `user_id` CHAR(36) NOT NULL,
  `item_id` CHAR(36) NOT NULL,
  `saved_amount` DECIMAL(10,2) NOT NULL,
  `skipped_at` TIMESTAMP NOT NULL,
  `created_at` TIMESTAMP NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_savings_records_user` FOREIGN KEY (`user_id`) REFERENCES `f_66579af4__user_savings_totals`(`user_id`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `f_66579af4__user_savings_totals` (
  `user_id` CHAR(36) NOT NULL,
  `total_saved` DECIMAL(10,2) NOT NULL,
  `updated_at` TIMESTAMP NOT NULL,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;