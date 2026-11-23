CREATE DATABASE IF NOT EXISTS campus_market DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE campus_market;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS favorites;
DROP TABLE IF EXISTS product_images;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS users;
CREATE TABLE users (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, username VARCHAR(20) NOT NULL UNIQUE,
 password VARCHAR(255) NOT NULL, nickname VARCHAR(30) NOT NULL,
 phone VARCHAR(20) NOT NULL DEFAULT '', created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
CREATE TABLE categories (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(30) NOT NULL UNIQUE, sort INT NOT NULL DEFAULT 0
) ENGINE=InnoDB;
CREATE TABLE products (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, seller_id BIGINT NOT NULL, category_id BIGINT NOT NULL,
 title VARCHAR(100) NOT NULL, description VARCHAR(1000) NOT NULL, price DECIMAL(10,2) NOT NULL,
 status ENUM('on_sale','sold','offline') NOT NULL DEFAULT 'on_sale',
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT fk_product_seller FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE,
 CONSTRAINT fk_product_category FOREIGN KEY (category_id) REFERENCES categories(id),
 INDEX idx_product_category_status (category_id,status), INDEX idx_product_created (created_at)
) ENGINE=InnoDB;
CREATE TABLE product_images (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, product_id BIGINT NOT NULL,
 path VARCHAR(255) NOT NULL, sort INT NOT NULL DEFAULT 0,
 CONSTRAINT fk_image_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;
CREATE TABLE favorites (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, user_id BIGINT NOT NULL, product_id BIGINT NOT NULL,
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT fk_favorite_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
 CONSTRAINT fk_favorite_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
 UNIQUE KEY uk_favorite_user_product (user_id,product_id)
) ENGINE=InnoDB;
CREATE TABLE messages (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, product_id BIGINT NOT NULL, user_id BIGINT NOT NULL,
 parent_id BIGINT NULL, content VARCHAR(500) NOT NULL,
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT fk_message_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
 CONSTRAINT fk_message_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
 CONSTRAINT fk_message_parent FOREIGN KEY (parent_id) REFERENCES messages(id) ON DELETE CASCADE,
 INDEX idx_message_product_created (product_id,created_at)
) ENGINE=InnoDB;
INSERT INTO categories(id,name,sort) VALUES
(1,'教材书籍',1),(2,'电子数码',2),(3,'生活用品',3),(4,'运动户外',4),(5,'美妆个护',5);
