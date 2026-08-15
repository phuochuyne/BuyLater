CREATE TABLE `users` (
  `id` CHAR(36) NOT NULL,
  `email` VARCHAR(320) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `f_bd77265a__saved_items` (
  `id` CHAR(36) NOT NULL,
  `user_id` CHAR(36) NOT NULL,
  `item_name` VARCHAR(500) NOT NULL,
  `price` DECIMAL(10,2) NOT NULL,
  `product_link` VARCHAR(2048) NOT NULL,
  `created_at` TIMESTAMP NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_saved_items_user_created` (`user_id`, `created_at`),
  CONSTRAINT `fk_saved_items_user` FOREIGN KEY (`user_id`)
    REFERENCES `users` (`id`) ON DELETE CASCADE,
  CHECK (`price` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `f_ed5144db__cooling_periods` (
  `id` CHAR(36) NOT NULL,
  `saved_item_id` CHAR(36) NOT NULL,
  `period_days` INT NOT NULL,
  `started_at` TIMESTAMP NOT NULL,
  `expires_at` TIMESTAMP NOT NULL,
  `created_at` TIMESTAMP NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_cooling_period_saved_item` (`saved_item_id`),
  KEY `ix_cooling_period_expires` (`expires_at`),
  CONSTRAINT `fk_cooling_period_saved_item` FOREIGN KEY (`saved_item_id`)
    REFERENCES `f_bd77265a__saved_items` (`id`) ON DELETE CASCADE,
  CHECK (`period_days` IN (1, 3, 7)),
  CHECK (`expires_at` > `started_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
  PRIMARY KEY (`id`),
  KEY `ix_notifications_due` (`status`, `scheduled_for`),
  KEY `ix_notifications_user` (`user_id`),
  CONSTRAINT `fk_notifications_item` FOREIGN KEY (`item_id`)
    REFERENCES `f_bd77265a__saved_items` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_notifications_user` FOREIGN KEY (`user_id`)
    REFERENCES `users` (`id`) ON DELETE CASCADE,
  CHECK (`status` IN ('pending', 'sent', 'failed', 'cancelled'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `f_c984506c__user_savings` (
  `id` CHAR(36) NOT NULL,
  `user_id` CHAR(36) NOT NULL,
  `total_saved` DECIMAL(12,2) NOT NULL,
  `updated_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_decision_savings_user` (`user_id`),
  CONSTRAINT `fk_decision_savings_user` FOREIGN KEY (`user_id`)
    REFERENCES `users` (`id`) ON DELETE CASCADE,
  CHECK (`total_saved` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `f_c984506c__item_decisions` (
  `id` CHAR(36) NOT NULL,
  `item_id` CHAR(36) NOT NULL,
  `user_id` CHAR(36) NOT NULL,
  `decision_type` VARCHAR(4) NOT NULL,
  `item_price` DECIMAL(10,2) NOT NULL,
  `decided_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_item_decision_user_item` (`user_id`, `item_id`),
  CONSTRAINT `fk_item_decision_item` FOREIGN KEY (`item_id`)
    REFERENCES `f_bd77265a__saved_items` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_item_decision_user` FOREIGN KEY (`user_id`)
    REFERENCES `users` (`id`) ON DELETE CASCADE,
  CHECK (`decision_type` IN ('buy', 'skip')),
  CHECK (`item_price` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `f_66579af4__user_savings_totals` (
  `user_id` CHAR(36) NOT NULL,
  `total_saved` DECIMAL(10,2) NOT NULL,
  `updated_at` TIMESTAMP NOT NULL,
  PRIMARY KEY (`user_id`),
  CONSTRAINT `fk_savings_totals_user` FOREIGN KEY (`user_id`)
    REFERENCES `users` (`id`) ON DELETE CASCADE,
  CHECK (`total_saved` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `f_66579af4__savings_records` (
  `id` CHAR(36) NOT NULL,
  `user_id` CHAR(36) NOT NULL,
  `item_id` CHAR(36) NOT NULL,
  `saved_amount` DECIMAL(10,2) NOT NULL,
  `skipped_at` TIMESTAMP NOT NULL,
  `created_at` TIMESTAMP NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_savings_record_user_item` (`user_id`, `item_id`),
  KEY `ix_savings_records_user_skipped` (`user_id`, `skipped_at`),
  CONSTRAINT `fk_savings_records_user` FOREIGN KEY (`user_id`)
    REFERENCES `f_66579af4__user_savings_totals` (`user_id`)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT `fk_savings_records_item` FOREIGN KEY (`item_id`)
    REFERENCES `f_bd77265a__saved_items` (`id`) ON DELETE CASCADE,
  CHECK (`saved_amount` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
