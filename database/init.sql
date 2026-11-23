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

USE campus_market;

INSERT INTO users(id,username,password,nickname,phone) VALUES
(1,'demo','pbkdf2:sha256:1000000$oXyduBJyHqZapGia$d2482de4ba7cfdee1e86bf484718c2e9de09e2af34a9a2cc5d12f62418c457db','林同学','13800138000'),
(2,'buyer','pbkdf2:sha256:1000000$oXyduBJyHqZapGia$d2482de4ba7cfdee1e86bf484718c2e9de09e2af34a9a2cc5d12f62418c457db','周同学','13900139000');

INSERT INTO products(id,seller_id,category_id,title,description,price,status,created_at) VALUES
(1,1,1,'高等数学教材 第七版','上下册齐全，少量笔记，不影响阅读。',28.00,'on_sale','2026-11-23 11:00:00'),
(2,2,1,'O''Reilly Python 编程书','经典教材，书角轻微磨损，内页干净。',45.00,'on_sale','2026-11-22 12:00:00'),
(3,1,1,'100%全新 大学英语四级真题','买重复了，塑封未拆。',18.00,'on_sale','2026-11-21 13:00:00'),
(4,2,2,'九成新机械键盘','青轴，功能正常，送键帽和拔键器。',128.00,'on_sale','2026-11-20 14:00:00'),
(5,1,2,'小米蓝牙音箱','音质不错，续航正常，配原装充电线。',79.00,'on_sale','2026-11-19 15:00:00'),
(6,2,2,'27寸显示器','2K分辨率，轻微使用痕迹，仅限校内自提。',499.00,'sold','2026-11-18 16:00:00'),
(7,1,3,'护眼台灯','三档调光，适合宿舍学习。',35.00,'on_sale','2026-11-17 17:00:00'),
(8,2,3,'宿舍小风扇','静音款，可夹床头，毕业低价出。',22.00,'on_sale','2026-11-16 10:00:00'),
(9,1,3,'折叠收纳箱','容量大，无破损，两个一起出。',25.00,'on_sale','2026-11-15 11:00:00'),
(10,2,4,'篮球 7号','几乎没用过，室外场地适用。',58.00,'on_sale','2026-11-14 12:00:00'),
(11,1,4,'羽毛球拍一对','轻量碳素，送三个羽毛球。',65.00,'on_sale','2026-11-13 13:00:00'),
(12,2,4,'瑜伽垫','加厚防滑，使用两次。',30.00,'on_sale','2026-11-12 14:00:00'),
(13,1,5,'洗发水套装','全新未拆封，日期新鲜。',48.00,'on_sale','2026-11-11 15:00:00'),
(14,2,5,'防晒霜','专柜购入，只用过一次。',55.00,'on_sale','2026-11-10 16:00:00'),
(15,1,1,'计算机组成原理','重点章节有标注，适合复习。',20.00,'on_sale','2026-11-09 17:00:00'),
(16,2,2,'无线鼠标','静音按键，接收器齐全。',39.00,'on_sale','2026-11-08 10:00:00'),
(17,1,3,'桌面书架','可折叠，承重好，适合宿舍。',32.00,'on_sale','2026-11-07 11:00:00'),
(18,2,4,'跳绳','计数款，送收纳袋。',15.00,'on_sale','2026-11-06 12:00:00'),
(19,1,5,'唇釉两支','色号不适合，仅试色。',26.00,'offline','2026-11-05 13:00:00'),
(20,2,1,'数据结构教材','配套习题册，一起出售。',36.00,'on_sale','2026-11-04 14:00:00'),
(21,1,2,'平板电脑支架','铝合金材质，可调节角度。',29.00,'on_sale','2026-11-23 15:00:00'),
(22,2,3,'保温杯','500ml，保温正常，杯身有贴纸。',24.00,'on_sale','2026-11-22 16:00:00'),
(23,1,4,'足球','5号球，脚感好，毕业出。',45.00,'on_sale','2026-11-21 17:00:00'),
(24,2,5,'化妆刷套装','清洗后收纳，刷毛完好。',40.00,'on_sale','2026-11-20 10:00:00');

INSERT INTO product_images(product_id,path,sort) VALUES
(1,'seed/p01.png',0),
(2,'seed/p02.png',0),
(3,'seed/p03.png',0),
(4,'seed/p04.png',0),
(5,'seed/p05.png',0),
(5,'seed/p05.png',1),
(6,'seed/p06.png',0),
(7,'seed/p07.png',0),
(8,'seed/p08.png',0),
(9,'seed/p09.png',0),
(10,'seed/p10.png',0),
(10,'seed/p10.png',1),
(11,'seed/p11.png',0),
(12,'seed/p12.png',0),
(13,'seed/p01.png',0),
(14,'seed/p02.png',0),
(15,'seed/p03.png',0),
(15,'seed/p03.png',1),
(16,'seed/p04.png',0),
(17,'seed/p05.png',0),
(18,'seed/p06.png',0),
(19,'seed/p07.png',0),
(20,'seed/p08.png',0),
(20,'seed/p08.png',1),
(21,'seed/p09.png',0),
(22,'seed/p10.png',0),
(23,'seed/p11.png',0),
(24,'seed/p12.png',0);

INSERT INTO favorites(user_id,product_id) VALUES (2,1),(2,4),(1,8);

INSERT INTO messages(id,product_id,user_id,parent_id,content,created_at) VALUES
(1,1,2,NULL,'教材还有吗？可以便宜一点吗？','2026-11-22 15:20:00'),
(2,1,1,1,'还在的，两本一起可以再少 3 元。','2026-11-22 15:30:00'),
(3,4,2,NULL,'键盘可以带到东区门口吗？','2026-11-23 09:10:00');